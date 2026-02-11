"""模板注入对话框 - 牌组级配置"""

from __future__ import annotations

from ..config import DeckFieldConfig, load_config, get_media_dir_from_mw
from ..template_injector import TemplateInjector


def _load_qt():
    """动态加载 Qt 组件"""
    import importlib
    qt = importlib.import_module("aqt.qt")
    return {
        "QComboBox": qt.QComboBox,
        "QDialog": qt.QDialog,
        "QHBoxLayout": qt.QHBoxLayout,
        "QLabel": qt.QLabel,
        "QMessageBox": qt.QMessageBox,
        "QPushButton": qt.QPushButton,
        "QTreeWidget": qt.QTreeWidget,
        "QTreeWidgetItem": qt.QTreeWidgetItem,
        "QVBoxLayout": qt.QVBoxLayout,
        "QCheckBox": qt.QCheckBox,
        "Qt": qt.Qt,
    }


class TemplateInjectDialog:
    """模板注入对话框 - 牌组级配置"""

    def __init__(self, mw) -> None:
        qt = _load_qt()
        self._dialog = qt["QDialog"](mw)
        self.mw = mw
        self.media_dir = get_media_dir_from_mw(mw)
        self.injector = TemplateInjector(mw, self.media_dir)
        self._qt = qt

        self._dialog.setWindowTitle("MDict 模板注入 - 牌组级配置")
        self._dialog.resize(700, 500)

        # 笔记类型选择
        self.note_type_box = qt["QComboBox"]()
        self.note_type_box.currentIndexChanged.connect(self.refresh_fields)

        # 牌组树
        self.deck_tree = qt["QTreeWidget"]()
        self.deck_tree.setHeaderLabels(["牌组/字段", "语言"])
        self.deck_tree.setColumnWidth(0, 400)

        # 按钮
        self.inject_button = qt["QPushButton"]("保存并注入")
        self.inject_button.clicked.connect(self.on_inject)
        self.clear_button = qt["QPushButton"]("清除注入")
        self.clear_button.clicked.connect(self.on_clear)

        # 布局
        header_row = qt["QHBoxLayout"]()
        header_row.addWidget(qt["QLabel"]("笔记类型："))
        header_row.addWidget(self.note_type_box)

        button_row = qt["QHBoxLayout"]()
        button_row.addWidget(self.inject_button)
        button_row.addWidget(self.clear_button)

        layout = qt["QVBoxLayout"]()
        layout.addLayout(header_row)
        layout.addWidget(self.deck_tree)
        layout.addLayout(button_row)
        self._dialog.setLayout(layout)

        self.load_note_types()

    def exec(self) -> int:
        """显示对话框"""
        return self._dialog.exec()

    def load_note_types(self) -> None:
        """加载笔记类型"""
        self.note_type_box.clear()
        models = getattr(getattr(self.mw, "col", None), "models", None)
        models = models.all() if models else []
        for model in models:
            self.note_type_box.addItem(model.get("name", ""), model.get("id"))
        self.refresh_fields()

    def refresh_fields(self) -> None:
        """刷新牌组树"""
        self.deck_tree.clear()
        note_type_id = self.note_type_box.currentData()
        if not note_type_id:
            return

        # 获取字段列表
        model_manager = getattr(getattr(self.mw, "col", None), "models", None)
        model = model_manager.get(note_type_id) if model_manager else None
        if not model:
            return
        fields = [f.get("name", "") for f in model.get("flds", [])]

        # 获取牌组列表
        decks = self._get_decks_for_note_type(note_type_id)

        # 加载已注入配置
        existing_config = self._load_existing_config(note_type_id)

        # 构建树
        for deck in decks:
            deck_name = deck["name"]
            is_configured = deck_name in existing_config
            
            # 牌组节点
            deck_item = self._qt["QTreeWidgetItem"]([deck_name + (" ✓" if is_configured else ""), ""])
            self.deck_tree.addTopLevelItem(deck_item)

            # 字段子节点
            for field_name in fields:
                field_item = self._qt["QTreeWidgetItem"]([field_name, ""])
                deck_item.addChild(field_item)

                # 复选框
                checkbox = self._qt["QCheckBox"]()
                self.deck_tree.setItemWidget(field_item, 0, checkbox)

                # 语言下拉框
                lang_combo = self._qt["QComboBox"]()
                lang_combo.addItems(["ja", "en"])
                self.deck_tree.setItemWidget(field_item, 1, lang_combo)

                # 回显已配置状态
                if is_configured and field_name in existing_config[deck_name]:
                    checkbox.setChecked(True)
                    lang = existing_config[deck_name][field_name]
                    lang_combo.setCurrentText(lang)

            deck_item.setExpanded(is_configured)

    def _get_decks_for_note_type(self, note_type_id: int) -> list[dict]:
        """获取使用该笔记类型的牌组"""
        deck_ids = self.mw.col.db.list(
            "SELECT DISTINCT did FROM cards WHERE nid IN (SELECT id FROM notes WHERE mid = ?)",
            note_type_id
        )
        
        decks = []
        for did in deck_ids:
            deck = self.mw.col.decks.get(did)
            if deck:
                decks.append({"id": did, "name": deck["name"]})
        
        # 如果没有卡片，显示所有牌组
        if not decks:
            for deck in self.mw.col.decks.all():
                decks.append({"id": deck["id"], "name": deck["name"]})
        
        return sorted(decks, key=lambda d: d["name"])

    def _load_existing_config(self, note_type_id: int) -> dict:
        """加载已注入配置"""
        config = load_config(self.media_dir)
        for injection in config.injections:
            if injection.note_type_id == note_type_id:
                result = {}
                for deck_config in injection.deck_configs:
                    result[deck_config.deck_name] = {
                        field["name"]: field["language"]
                        for field in deck_config.fields
                    }
                return result
        return {}

    def on_inject(self) -> None:
        """保存并注入"""
        note_type_id = self.note_type_box.currentData()
        if not note_type_id:
            return

        # 收集配置
        deck_configs = []
        all_fields_set = set()

        for i in range(self.deck_tree.topLevelItemCount()):
            deck_item = self.deck_tree.topLevelItem(i)
            deck_name = deck_item.text(0).replace(" ✓", "")
            
            fields = []
            for j in range(deck_item.childCount()):
                field_item = deck_item.child(j)
                checkbox = self.deck_tree.itemWidget(field_item, 0)
                if checkbox and checkbox.isChecked():
                    field_name = field_item.text(0)
                    lang_combo = self.deck_tree.itemWidget(field_item, 1)
                    language = lang_combo.currentText() if lang_combo else "ja"
                    fields.append({"name": field_name, "language": language})
                    all_fields_set.add((field_name, language))
            
            if fields:
                deck_configs.append({
                    "deckName": deck_name,
                    "fields": fields
                })

        if not deck_configs:
            self._qt["QMessageBox"].warning(self._dialog, "提示", "请至少为一个牌组选择字段")
            return

        # 转换为 inject 需要的格式
        all_fields = [{"name": name, "language": lang} for name, lang in all_fields_set]

        try:
            missing = self.injector.inject(int(note_type_id), all_fields, deck_configs)
            if missing:
                self._qt["QMessageBox"].information(
                    self._dialog, "完成",
                    f"注入完成，但以下字段未在模板中找到：{', '.join(missing)}"
                )
            else:
                self._qt["QMessageBox"].information(self._dialog, "完成", "模板注入成功")
            self.refresh_fields()
        except Exception as exc:
            self._qt["QMessageBox"].warning(self._dialog, "失败", f"注入失败: {exc}")

    def on_clear(self) -> None:
        """清除注入"""
        note_type_id = self.note_type_box.currentData()
        if not note_type_id:
            return

        message_box = self._qt["QMessageBox"]
        confirm = message_box.question(self._dialog, "确认", "确定清除该笔记类型的所有注入配置？")
        yes_button = (
            message_box.StandardButton.Yes
            if hasattr(message_box, "StandardButton")
            else message_box.Yes
        )
        if confirm != yes_button:
            return

        try:
            self.injector.clear(int(note_type_id))
            self._qt["QMessageBox"].information(self._dialog, "完成", "已清除注入")
            self.refresh_fields()
        except Exception as exc:
            self._qt["QMessageBox"].warning(self._dialog, "失败", f"清除失败: {exc}")

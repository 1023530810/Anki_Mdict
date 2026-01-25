"""模板注入对话框"""

from __future__ import annotations

from ..config import get_media_dir_from_mw
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
        "QTableWidget": qt.QTableWidget,
        "QTableWidgetItem": qt.QTableWidgetItem,
        "QVBoxLayout": qt.QVBoxLayout,
        "Qt": qt.Qt,
    }


class TemplateInjectDialog:
    """模板注入对话框"""

    def __init__(self, mw) -> None:
        qt = _load_qt()
        self._dialog = qt["QDialog"](mw)
        self.mw = mw
        self.media_dir = get_media_dir_from_mw(mw)
        self.injector = TemplateInjector(mw, self.media_dir)

        self._dialog.setWindowTitle("MDict 模板注入")
        self._dialog.resize(640, 420)

        qt_core = qt["Qt"]
        self._checked_state = (
            qt_core.CheckState.Checked
            if hasattr(qt_core, "CheckState")
            else qt_core.Checked
        )
        self._unchecked_state = (
            qt_core.CheckState.Unchecked
            if hasattr(qt_core, "CheckState")
            else qt_core.Unchecked
        )

        self.note_type_box = qt["QComboBox"]()
        self.note_type_box.currentIndexChanged.connect(self.refresh_fields)

        self.field_table = qt["QTableWidget"](0, 2)
        self.field_table.setHorizontalHeaderLabels(["字段", "语言"])

        self.inject_button = qt["QPushButton"]("注入")
        self.inject_button.clicked.connect(self.on_inject)

        self.clear_button = qt["QPushButton"]("清除注入")
        self.clear_button.clicked.connect(self.on_clear)

        header_row = qt["QHBoxLayout"]()
        header_row.addWidget(qt["QLabel"]("笔记类型："))
        header_row.addWidget(self.note_type_box)

        button_row = qt["QHBoxLayout"]()
        button_row.addWidget(self.inject_button)
        button_row.addWidget(self.clear_button)

        layout = qt["QVBoxLayout"]()
        layout.addLayout(header_row)
        layout.addWidget(self.field_table)
        layout.addLayout(button_row)
        self._dialog.setLayout(layout)

        self._qt = qt
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
        """刷新字段列表"""
        self.field_table.setRowCount(0)
        model_id = self.note_type_box.currentData()
        model_manager = getattr(getattr(self.mw, "col", None), "models", None)
        model = model_manager.get(model_id) if model_manager else None
        if model is None:
            return
        for index, field in enumerate(model.get("flds", [])):
            self.field_table.insertRow(index)
            field_item = self._qt["QTableWidgetItem"](field.get("name", ""))
            field_item.setCheckState(self._unchecked_state)
            self.field_table.setItem(index, 0, field_item)

            language_box = self._qt["QComboBox"]()
            language_box.addItems(["ja", "en"])
            self.field_table.setCellWidget(index, 1, language_box)

    def on_inject(self) -> None:
        """执行注入"""
        model_id = self.note_type_box.currentData()
        fields = []
        for row in range(self.field_table.rowCount()):
            item = self.field_table.item(row, 0)
            if item is None or item.checkState() != self._checked_state:
                continue
            language_box = self.field_table.cellWidget(row, 1)
            language = language_box.currentText() if language_box else "ja"
            fields.append({"name": item.text(), "language": language})

        if not fields:
            self._qt["QMessageBox"].warning(self._dialog, "提示", "请至少选择一个字段")
            return

        try:
            self.injector.inject(int(model_id), fields)
            self._qt["QMessageBox"].information(self._dialog, "完成", "模板注入完成")
        except Exception as exc:
            self._qt["QMessageBox"].warning(self._dialog, "失败", f"注入失败: {exc}")

    def on_clear(self) -> None:
        """清除注入"""
        model_id = self.note_type_box.currentData()
        message_box = self._qt["QMessageBox"]
        confirm = message_box.question(self._dialog, "确认", "确定清除注入？")
        yes_button = (
            message_box.StandardButton.Yes
            if hasattr(message_box, "StandardButton")
            else message_box.Yes
        )
        if confirm != yes_button:
            return
        try:
            self.injector.clear(int(model_id))
            self._qt["QMessageBox"].information(self._dialog, "完成", "已清除注入")
        except Exception as exc:
            self._qt["QMessageBox"].warning(self._dialog, "失败", f"清除失败: {exc}")

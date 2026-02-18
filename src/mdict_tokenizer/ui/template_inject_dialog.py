# basedpyright: ignore[reportAny, reportExplicitAny, reportUnknownParameterType, reportMissingParameterType, reportUnannotatedClassAttribute, reportUnknownArgumentType, reportUnnecessaryIsInstance]

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import DeckFieldConfig, DeckInjection, get_media_dir_from_mw, load_config
from ..template_injector import TemplateInjector


def _load_qt():
    import importlib

    qt = importlib.import_module("aqt.qt")
    return {
        "QCheckBox": qt.QCheckBox,
        "QComboBox": qt.QComboBox,
        "QDialog": qt.QDialog,
        "QHBoxLayout": qt.QHBoxLayout,
        "QHeaderView": qt.QHeaderView,
        "QLabel": qt.QLabel,
        "QMessageBox": qt.QMessageBox,
        "QPushButton": qt.QPushButton,
        "QTreeWidget": qt.QTreeWidget,
        "QTreeWidgetItem": qt.QTreeWidgetItem,
        "QVBoxLayout": qt.QVBoxLayout,
        "Qt": qt.Qt,
    }


class TemplateInjectDialog:
    def __init__(self, mw) -> None:
        qt = _load_qt()
        self._qt = qt
        self._dialog = qt["QDialog"](mw)
        self.mw = mw
        self.media_dir: Path = get_media_dir_from_mw(mw)
        self.injector = TemplateInjector(mw, self.media_dir)

        self._dialog.setWindowTitle("MDict 模板注入")
        self._dialog.resize(860, 520)

        qt_core = qt["Qt"]
        self._user_role = (
            qt_core.ItemDataRole.UserRole
            if hasattr(qt_core, "ItemDataRole")
            else qt_core.UserRole
        )

        self.note_type_box = qt["QComboBox"]()
        self.note_type_box.currentIndexChanged.connect(self.refresh_fields)

        self.deck_tree = qt["QTreeWidget"]()
        self.deck_tree.setColumnCount(2)
        self.deck_tree.setHeaderLabels(["牌组/字段", "语言"])
        header = self.deck_tree.header()
        header_resize = qt["QHeaderView"]
        if hasattr(header, "setSectionResizeMode"):
            stretch_mode = (
                header_resize.ResizeMode.Stretch
                if hasattr(header_resize, "ResizeMode")
                else header_resize.Stretch
            )
            content_mode = (
                header_resize.ResizeMode.ResizeToContents
                if hasattr(header_resize, "ResizeMode")
                else header_resize.ResizeToContents
            )
            header.setSectionResizeMode(0, stretch_mode)
            header.setSectionResizeMode(1, content_mode)
        if hasattr(header, "setStretchLastSection"):
            header.setStretchLastSection(False)

        self.inject_button = qt["QPushButton"]("保存并注入")
        self.inject_button.clicked.connect(self.on_inject)

        self.clear_button = qt["QPushButton"]("清除注入")
        self.clear_button.clicked.connect(self.on_clear)

        self.cancel_button = qt["QPushButton"]("取消")
        self.cancel_button.clicked.connect(self._dialog.reject)

        left_layout = qt["QVBoxLayout"]()
        left_layout.addWidget(qt["QLabel"]("笔记类型："))
        left_layout.addWidget(self.note_type_box)
        left_layout.addStretch()

        right_layout = qt["QVBoxLayout"]()
        right_layout.addWidget(qt["QLabel"]("牌组配置："))
        right_layout.addWidget(self.deck_tree)

        body_layout = qt["QHBoxLayout"]()
        body_layout.addLayout(left_layout, 1)
        body_layout.addLayout(right_layout, 3)

        button_row = qt["QHBoxLayout"]()
        button_row.addStretch()
        button_row.addWidget(self.inject_button)
        button_row.addWidget(self.clear_button)
        button_row.addWidget(self.cancel_button)

        layout = qt["QVBoxLayout"]()
        layout.addLayout(body_layout)
        layout.addLayout(button_row)
        self._dialog.setLayout(layout)

        self._deck_items: dict[str, Any] = {}
        self._field_widgets_by_deck: dict[str, dict[str, tuple[Any, Any]]] = {}

        self.load_note_types()

    def exec(self) -> int:
        return self._dialog.exec()

    def load_note_types(self) -> None:
        self.note_type_box.clear()
        models = getattr(getattr(self.mw, "col", None), "models", None)
        if models:
            for model in models.all():
                model_name = model.get("name", "")
                model_id = model.get("id", 0)
                self.note_type_box.addItem(model_name, model_id)
        self.refresh_fields()

    def refresh_fields(self) -> None:
        self.deck_tree.clear()
        self._deck_items = {}
        self._field_widgets_by_deck = {}
        model_id = self.note_type_box.currentData()
        if not model_id:
            return
        model_manager = getattr(getattr(self.mw, "col", None), "models", None)
        model = model_manager.get(model_id) if model_manager else None
        if model is None:
            return

        fields = [
            field.get("name", "")
            for field in model.get("flds", [])
            if field.get("name")
        ]
        existing_config = self.load_existing_config(int(model_id))
        decks = self.get_decks_for_note_type(int(model_id))
        for deck in decks:
            deck_name = str(deck.get("name") or "")
            if not deck_name:
                continue
            self._ensure_deck_path(deck_name, existing_config)

        for deck_name, deck_item in self._deck_items.items():
            self._ensure_field_rows(deck_name, deck_item, fields, existing_config)

    def _ensure_deck_path(
        self, deck_name: str, existing_config: dict[str, dict[str, str]]
    ) -> None:
        parts = [part for part in deck_name.split("::") if part]
        if not parts:
            return
        parent_item = None
        path_parts: list[str] = []
        for part in parts:
            path_parts.append(part)
            path_name = "::".join(path_parts)
            deck_item = self._deck_items.get(path_name)
            if deck_item is None:
                display_name = part
                if path_name in existing_config:
                    display_name = f"{part} ✓"
                deck_item = self._qt["QTreeWidgetItem"]([display_name, ""])
                deck_item.setData(0, self._user_role, path_name)
                if parent_item is None:
                    self.deck_tree.addTopLevelItem(deck_item)
                else:
                    parent_item.addChild(deck_item)
                self._deck_items[path_name] = deck_item
            elif path_name in existing_config and "✓" not in deck_item.text(0):
                deck_item.setText(0, f"{deck_item.text(0)} ✓")
            parent_item = deck_item

    def _ensure_field_rows(
        self,
        deck_name: str,
        deck_item: Any,
        fields: list[str],
        existing_config: dict[str, dict[str, str]],
    ) -> None:
        if deck_name in self._field_widgets_by_deck:
            return
        field_widgets: dict[str, tuple[Any, Any]] = {}
        deck_fields = existing_config.get(deck_name, {})
        for field_name in fields:
            field_item = self._qt["QTreeWidgetItem"](deck_item)
            checkbox = self._qt["QCheckBox"](field_name)
            language_box = self._qt["QComboBox"]()
            language_box.addItems(["ja", "en"])
            self.deck_tree.setItemWidget(field_item, 0, checkbox)
            self.deck_tree.setItemWidget(field_item, 1, language_box)
            configured_language = deck_fields.get(field_name)
            if configured_language:
                checkbox.setChecked(True)
                index = language_box.findText(configured_language)
                if index >= 0:
                    language_box.setCurrentIndex(index)
            field_widgets[field_name] = (checkbox, language_box)
        self._field_widgets_by_deck[deck_name] = field_widgets

    def get_decks_for_note_type(self, note_type_id: int) -> list[dict[str, object]]:
        col = getattr(self.mw, "col", None)
        if col is None:
            return []
        deck_ids = col.db.list(
            "SELECT DISTINCT did FROM cards WHERE nid IN (SELECT id FROM notes WHERE mid = ?)",
            note_type_id,
        )
        decks: list[dict[str, object]] = []
        for deck_id in deck_ids:
            deck = col.decks.get(deck_id)
            if not deck:
                continue
            deck_name = deck.get("name", "")
            if not deck_name:
                continue
            decks.append({"id": deck_id, "name": deck_name})

        if not decks:
            for deck in col.decks.all():
                deck_name = deck.get("name", "")
                if not deck_name:
                    continue
                decks.append({"id": deck.get("id", 0), "name": deck_name})
        return decks

    def _find_injection(self, note_type_id: int) -> DeckInjection | None:
        config = load_config(self.media_dir)
        for injection in config.injections:
            if injection.note_type_id == note_type_id:
                return injection
        return None

    def load_existing_config(self, note_type_id: int) -> dict[str, dict[str, str]]:
        injection = self._find_injection(note_type_id)
        if injection is None:
            return {}
        deck_config_map: dict[str, dict[str, str]] = {}
        for deck_config in injection.deck_configs:
            if not isinstance(deck_config, DeckFieldConfig):
                continue
            field_map: dict[str, str] = {}
            for field in deck_config.fields:
                if not isinstance(field, dict):
                    continue
                name = str(field.get("name") or "").strip()
                language = str(field.get("language") or "").strip()
                if not name:
                    continue
                field_map[name] = language
            deck_config_map[str(deck_config.deck_name)] = field_map
        return deck_config_map

    def _collect_deck_configs(
        self,
    ) -> tuple[list[dict[str, str]], list[dict[str, object]]]:
        deck_configs: list[dict[str, object]] = []
        field_languages: dict[str, str] = {}
        for deck_name, field_widgets in self._field_widgets_by_deck.items():
            fields: list[dict[str, str]] = []
            for field_name, (checkbox, language_box) in field_widgets.items():
                if not checkbox.isChecked():
                    continue
                language = language_box.currentText() if language_box else "ja"
                fields.append({"name": field_name, "language": language})
                if field_name not in field_languages:
                    field_languages[field_name] = language
            if fields:
                deck_configs.append({"deckName": deck_name, "fields": fields})

        fields_payload = [
            {"name": name, "language": language}
            for name, language in field_languages.items()
        ]
        return fields_payload, deck_configs

    def on_inject(self) -> None:
        note_type_id = self.note_type_box.currentData()
        if not note_type_id:
            self._qt["QMessageBox"].warning(self._dialog, "提示", "请选择笔记类型")
            return
        fields, deck_configs = self._collect_deck_configs()
        if not deck_configs:
            self._qt["QMessageBox"].warning(self._dialog, "提示", "请至少选择一个字段")
            return

        try:
            missing_fields = self.injector.inject(
                int(note_type_id), fields, deck_configs
            )
            if missing_fields:
                missing_text = "、".join(missing_fields)
                self._qt["QMessageBox"].information(
                    self._dialog,
                    "提示",
                    f"模板注入完成，但以下字段未在模板中找到，未启用分词：{missing_text}",
                )
            else:
                self._qt["QMessageBox"].information(
                    self._dialog, "完成", "模板注入完成"
                )
            self.refresh_fields()
        except Exception as exc:
            self._qt["QMessageBox"].warning(self._dialog, "失败", f"注入失败: {exc}")

    def on_clear(self) -> None:
        note_type_id = self.note_type_box.currentData()
        if not note_type_id:
            self._qt["QMessageBox"].warning(self._dialog, "提示", "请选择笔记类型")
            return
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
            self.injector.clear(int(note_type_id))
            self._qt["QMessageBox"].information(self._dialog, "完成", "已清除注入")
            self.refresh_fields()
        except Exception as exc:
            self._qt["QMessageBox"].warning(self._dialog, "失败", f"清除失败: {exc}")

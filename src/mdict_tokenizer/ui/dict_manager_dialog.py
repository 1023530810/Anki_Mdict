# basedpyright: ignore
"""辞典管理对话框"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from pathlib import Path

from ..config import (
    Dictionary,
    TokenizerConfig,
    collect_languages,
    get_media_dir_from_mw,
    load_config,
    save_config,
)
from ..dict_manager import DictionaryManager
from ..try_lookup import TryLookupService
from .dict_manager_dialog_logic import (
    resolve_display_order_from_staged,
    resolve_enabled_dictionary_ids,
    update_staged_rows_by_language,
)


def _load_qt():
    """动态加载 Qt 组件"""
    import importlib

    qt = importlib.import_module("aqt.qt")
    return {
        "QAbstractItemView": qt.QAbstractItemView,
        "QByteArray": qt.QByteArray,
        "QCheckBox": qt.QCheckBox,
        "QComboBox": qt.QComboBox,
        "QDialog": qt.QDialog,
        "QFileDialog": qt.QFileDialog,
        "QHBoxLayout": qt.QHBoxLayout,
        "QHeaderView": qt.QHeaderView,
        "QInputDialog": qt.QInputDialog,
        "QLabel": qt.QLabel,
        "QLineEdit": qt.QLineEdit,
        "QMessageBox": qt.QMessageBox,
        "QPushButton": qt.QPushButton,
        "QSettings": qt.QSettings,
        "QTableWidget": qt.QTableWidget,
        "QTableWidgetItem": qt.QTableWidgetItem,
        "QVBoxLayout": qt.QVBoxLayout,
        "QWidget": qt.QWidget,
    }


class DictManagerDialog:
    """辞典管理对话框"""

    _HEADER_STATE_KEY = "mdict_tokenizer/DictManagerDialog/v1/header_state"

    def __init__(self, mw) -> None:
        qt = _load_qt()
        self._dialog = qt["QDialog"](mw)
        self.mw = mw
        self.media_dir = get_media_dir_from_mw(mw)
        self.manager = DictionaryManager(self.media_dir)
        self.lookup_service = TryLookupService(self.media_dir)

        self._dialog.setWindowTitle("MDict 辞典管理")
        self._dialog.resize(860, 520)

        self.language_box = qt["QComboBox"]()
        self.language_box.currentTextChanged.connect(self.on_language_changed)

        self.import_button = qt["QPushButton"]("导入 MDX")
        self.import_button.clicked.connect(self.on_import)

        self.dict_table = qt["QTableWidget"](0, 3)
        self.dict_table.setHorizontalHeaderLabels(["辞典", "资源", "操作"])

        item_view = qt["QAbstractItemView"]
        selection_mode = (
            item_view.SelectionMode.SingleSelection
            if hasattr(item_view, "SelectionMode")
            else item_view.SingleSelection
        )
        selection_behavior = (
            item_view.SelectionBehavior.SelectRows
            if hasattr(item_view, "SelectionBehavior")
            else item_view.SelectRows
        )
        drag_drop_mode = (
            item_view.DragDropMode.InternalMove
            if hasattr(item_view, "DragDropMode")
            else item_view.InternalMove
        )
        no_edit = (
            item_view.EditTrigger.NoEditTriggers
            if hasattr(item_view, "EditTrigger")
            else item_view.NoEditTriggers
        )
        self.dict_table.setSelectionMode(selection_mode)
        self.dict_table.setSelectionBehavior(selection_behavior)
        self.dict_table.setDragDropMode(drag_drop_mode)
        self.dict_table.setDragDropOverwriteMode(False)
        self.dict_table.setDragEnabled(True)
        self.dict_table.setDropIndicatorShown(True)
        self.dict_table.setEditTriggers(no_edit)

        table_model = self.dict_table.model()
        if table_model is not None:
            table_model.rowsMoved.connect(self._on_rows_moved)

        header = self.dict_table.horizontalHeader()
        header_resize = qt["QHeaderView"]
        resize_mode = (
            header_resize.ResizeMode.Interactive
            if hasattr(header_resize, "ResizeMode")
            else header_resize.Interactive
        )
        if hasattr(header, "setSectionResizeMode"):
            header.setSectionResizeMode(0, resize_mode)
            header.setSectionResizeMode(1, resize_mode)
            header.setSectionResizeMode(2, resize_mode)
        vertical_header = self.dict_table.verticalHeader()
        if vertical_header is not None:
            vertical_header.setVisible(False)

        settings = qt["QSettings"]()
        saved_state = settings.value(self._HEADER_STATE_KEY)
        if saved_state is not None:
            header.restoreState(qt["QByteArray"](saved_state))

        self.save_order_button = qt["QPushButton"]("保存更改")
        self.save_order_button.clicked.connect(self.on_save_order)

        self.lookup_input = qt["QLineEdit"]()
        self.lookup_input.setPlaceholderText("输入词条")

        self.lookup_button = qt["QPushButton"]("快速试查")
        self.lookup_button.clicked.connect(self.on_try_lookup)

        self.lookup_result = qt["QLabel"]("")
        self.lookup_result.setWordWrap(True)

        header_row = qt["QHBoxLayout"]()
        header_row.addWidget(qt["QLabel"]("语言："))
        header_row.addWidget(self.language_box)
        header_row.addStretch()
        header_row.addWidget(self.import_button)

        lookup_row = qt["QHBoxLayout"]()
        lookup_row.addWidget(self.lookup_input)
        lookup_row.addWidget(self.lookup_button)

        layout = qt["QVBoxLayout"]()
        layout.addLayout(header_row)
        layout.addWidget(qt["QLabel"]("拖拽调整顺序："))
        layout.addWidget(self.dict_table)
        layout.addWidget(self.save_order_button)
        layout.addWidget(qt["QLabel"]("快速试查："))
        layout.addLayout(lookup_row)
        layout.addWidget(self.lookup_result)
        self._dialog.setLayout(layout)

        self._qt = qt
        self._enable_boxes: dict[str, object] = {}
        self._staged_rows_by_language: dict[str, list[tuple[str, bool]]] = {}
        self._current_language = ""
        self._rebuilding_after_move = False

        self._dialog.finished.connect(self._save_header_state)
        self.refresh_languages()

    def _save_header_state(self) -> None:
        header = self.dict_table.horizontalHeader()
        state = header.saveState()
        settings = self._qt["QSettings"]()
        settings.setValue(self._HEADER_STATE_KEY, state)

    def exec(self) -> int:
        """显示对话框"""
        return self._dialog.exec()

    def refresh_languages(self, selected: str | None = None) -> None:
        """刷新语言下拉"""
        config = load_config(self.media_dir)
        languages = sorted(collect_languages(config.dictionaries, config.tokenizers))
        if not languages:
            languages = ["ja", "en"]
        current = selected or self.language_box.currentText()
        self.language_box.blockSignals(True)
        self.language_box.clear()
        for language in languages:
            self.language_box.addItem(language)
        if current in languages:
            self.language_box.setCurrentText(current)
        else:
            self.language_box.setCurrentIndex(0)
        self.language_box.blockSignals(False)
        self.refresh_list()

    def refresh_list(self) -> None:
        """刷新列表"""
        language = self.language_box.currentText()
        if not language:
            return
        config = load_config(self.media_dir)
        dictionaries = [
            dictionary
            for dictionary in config.dictionaries
            if language in dictionary.languages
        ]
        staged_rows = self._staged_rows_by_language.get(language)
        if staged_rows:
            ordered, enabled_set = self._resolve_display_order_from_staged(
                dictionaries, staged_rows
            )
        else:
            ordered, enabled_set = self._resolve_display_order(
                dictionaries, config.tokenizers, language
            )

        self._enable_boxes = {}
        self.dict_table.setRowCount(0)
        for row_index, dictionary in enumerate(ordered):
            self.dict_table.insertRow(row_index)
            name_item = self._qt["QTableWidgetItem"](dictionary.name)
            name_item.setData(256, dictionary.id)
            self.dict_table.setItem(row_index, 0, name_item)

            badge_text = self._build_resource_badge(dictionary)
            badge_item = self._qt["QTableWidgetItem"](badge_text)
            self.dict_table.setItem(row_index, 1, badge_item)

            action_widget = self._build_action_widget(
                dictionary,
                dictionary.id in enabled_set,
            )
            self.dict_table.setCellWidget(row_index, 2, action_widget)

        if not ordered:
            self.dict_table.setRowCount(0)
        self.lookup_result.setText("")
        self._current_language = language

    def _resolve_display_order(
        self,
        dictionaries: list[Dictionary],
        tokenizers: dict[str, TokenizerConfig],
        language: str,
    ) -> tuple[list[Dictionary], set[str]]:
        """解析显示顺序"""
        dict_map = {dictionary.id: dictionary for dictionary in dictionaries}
        tokenizer = tokenizers.get(language)
        if tokenizer is not None and tokenizer.dictionary_ids:
            enabled_ids = [
                dict_id for dict_id in tokenizer.dictionary_ids if dict_id in dict_map
            ]
        else:
            enabled_ids = [
                dictionary.id
                for dictionary in sorted(dictionaries, key=lambda item: item.order)
            ]
        enabled_set = set(enabled_ids)
        enabled_list = [
            dict_map[dict_id] for dict_id in enabled_ids if dict_id in dict_map
        ]
        disabled_list = sorted(
            [
                dictionary
                for dictionary in dictionaries
                if dictionary.id not in enabled_set
            ],
            key=lambda item: item.order,
        )
        return enabled_list + disabled_list, enabled_set

    def _resolve_display_order_from_staged(
        self, dictionaries: list[Dictionary], staged_rows: list[tuple[str, bool]]
    ) -> tuple[list[Dictionary], set[str]]:
        """解析暂存显示顺序"""
        return resolve_display_order_from_staged(dictionaries, staged_rows)

    def _build_resource_badge(self, dictionary: Dictionary) -> str:
        """构建资源徽标"""
        mdd_text = "有" if dictionary.resources.has_mdd else "无"
        css_text = "有" if dictionary.resources.css_file else "无"
        return f"MDD:{mdd_text}  CSS:{css_text}  资源:{dictionary.resources.resource_count}"

    def _build_action_widget(self, dictionary: Dictionary, enabled: bool):
        """构建行内操作区（两行布局）"""
        container = self._qt["QWidget"]()
        main_layout = self._qt["QVBoxLayout"]()
        main_layout.setContentsMargins(0, 0, 0, 0)

        enable_box = self._qt["QCheckBox"]("启用")
        enable_box.setChecked(enabled)
        enable_box.toggled.connect(
            lambda checked, dict_id=dictionary.id: self.on_toggle_enabled(
                dict_id, checked
            )
        )
        self._enable_boxes[dictionary.id] = enable_box

        mdd_button = self._qt["QPushButton"](
            "删除 MDD" if dictionary.resources.has_mdd else "添加 MDD"
        )
        mdd_button.clicked.connect(
            lambda _checked=False, dict_id=dictionary.id: self.on_mdd_action(dict_id)
        )

        css_button = self._qt["QPushButton"](
            "删除 CSS" if dictionary.resources.css_file else "添加 CSS"
        )
        css_button.clicked.connect(
            lambda _checked=False, dict_id=dictionary.id: self.on_css_action(dict_id)
        )

        rename_button = self._qt["QPushButton"]("重命名")
        rename_button.clicked.connect(
            lambda _checked=False, dict_id=dictionary.id: self.on_rename(dict_id)
        )

        delete_button = self._qt["QPushButton"]("删除辞典")
        delete_button.clicked.connect(
            lambda _checked=False, dict_id=dictionary.id: self.on_delete(dict_id)
        )

        first_row_layout = self._qt["QHBoxLayout"]()
        first_row_layout.setContentsMargins(0, 0, 0, 0)
        first_row_layout.addWidget(enable_box)
        first_row_layout.addWidget(mdd_button)
        first_row_layout.addWidget(css_button)

        second_row_layout = self._qt["QHBoxLayout"]()
        second_row_layout.setContentsMargins(0, 0, 0, 0)
        second_row_layout.addWidget(rename_button)
        second_row_layout.addWidget(delete_button)

        main_layout.addLayout(first_row_layout)
        main_layout.addLayout(second_row_layout)
        container.setLayout(main_layout)
        return container

    def _save_language_dictionary_ids(
        self, language: str, dictionary_ids: list[str]
    ) -> None:
        """保存语言顺序"""
        config = load_config(self.media_dir)
        tokenizer = config.tokenizers.get(language)
        if tokenizer is None:
            tokenizer = TokenizerConfig(language=language)
        config.tokenizers[language] = replace(tokenizer, dictionary_ids=dictionary_ids)
        save_config(self.media_dir, config)

    def _append_language_dictionary_id(self, language: str, dict_id: str) -> None:
        """追加启用辞典"""
        config = load_config(self.media_dir)
        tokenizer = config.tokenizers.get(language)
        if tokenizer is None:
            tokenizer = TokenizerConfig(language=language)
        current_ids = list(tokenizer.dictionary_ids)
        if dict_id not in current_ids:
            current_ids.append(dict_id)
        config.tokenizers[language] = replace(tokenizer, dictionary_ids=current_ids)
        save_config(self.media_dir, config)

    def _remove_language_dictionary_id(self, language: str, dict_id: str) -> None:
        """移除启用辞典"""
        config = load_config(self.media_dir)
        tokenizer = config.tokenizers.get(language)
        if tokenizer is None:
            tokenizer = TokenizerConfig(language=language)
        current_ids = [item for item in tokenizer.dictionary_ids if item != dict_id]
        config.tokenizers[language] = replace(tokenizer, dictionary_ids=current_ids)
        save_config(self.media_dir, config)

    def _iter_ordered_rows(self) -> Iterable[tuple[str, bool]]:
        """读取表格顺序与启用状态"""
        for row_index in range(self.dict_table.rowCount()):
            item = self.dict_table.item(row_index, 0)
            if item is None:
                continue
            dict_id = str(item.data(256))
            enable_box = self._enable_boxes.get(dict_id)
            checker = getattr(enable_box, "isChecked", None)
            enabled = bool(checker()) if callable(checker) else False
            yield str(dict_id), enabled

    def _stage_current_language(self) -> None:
        """暂存当前语言表格状态"""
        language = self._current_language or self.language_box.currentText()
        if not language:
            return
        staged_rows = list(self._iter_ordered_rows())
        self._staged_rows_by_language = update_staged_rows_by_language(
            self._staged_rows_by_language, language, staged_rows
        )

    def _on_rows_moved(self, *args) -> None:
        """拖拽排序后重建表格显示"""
        if self._rebuilding_after_move:
            return
        self._rebuilding_after_move = True
        try:
            self._stage_current_language()
            self.refresh_list()
        finally:
            self._rebuilding_after_move = False

    def on_language_changed(self, language: str) -> None:
        """切换语言"""
        self._stage_current_language()
        self._current_language = language
        self.refresh_list()

    def on_import(self) -> None:
        """导入辞典"""
        file_path, _ = self._qt["QFileDialog"].getOpenFileName(
            self._dialog, "选择 MDX 文件", "", "MDX Files (*.mdx)"
        )
        if not file_path:
            return
        language_text, ok = self._qt["QInputDialog"].getText(
            self._dialog, "输入语言", "辞典语言（逗号分隔）："
        )
        if not ok:
            return
        languages = [lang.strip() for lang in language_text.split(",") if lang.strip()]
        if not languages:
            self._qt["QMessageBox"].warning(self._dialog, "提示", "请至少输入一种语言")
            return
        try:
            self.manager.import_dictionary(Path(file_path), languages)
            self._qt["QMessageBox"].information(self._dialog, "完成", "辞典导入完成")
        except Exception as exc:
            self._qt["QMessageBox"].warning(self._dialog, "失败", f"导入失败: {exc}")
        self.refresh_languages()

    def on_mdd_action(self, dict_id: str) -> None:
        """处理 MDD 资源"""
        config = load_config(self.media_dir)
        dictionary = next(
            (item for item in config.dictionaries if item.id == dict_id), None
        )
        if dictionary is None:
            return
        if dictionary.resources.has_mdd:
            try:
                self.manager.delete_mdd(dict_id)
                self._qt["QMessageBox"].information(self._dialog, "完成", "MDD 已删除")
            except Exception as exc:
                self._qt["QMessageBox"].warning(
                    self._dialog, "失败", f"删除失败: {exc}"
                )
            self.refresh_list()
            return

        file_paths, _ = self._qt["QFileDialog"].getOpenFileNames(
            self._dialog, "选择 MDD 文件", "", "MDD Files (*.mdd)"
        )
        if not file_paths:
            return
        try:
            self.manager.add_mdd_resources(dict_id, [Path(p) for p in file_paths])
            self._qt["QMessageBox"].information(
                self._dialog, "完成", "MDD 资源导入完成"
            )
        except Exception as exc:
            self._qt["QMessageBox"].warning(
                self._dialog, "失败", f"MDD 导入失败: {exc}"
            )
        self.refresh_list()

    def on_css_action(self, dict_id: str) -> None:
        """处理 CSS 资源"""
        config = load_config(self.media_dir)
        dictionary = next(
            (item for item in config.dictionaries if item.id == dict_id), None
        )
        if dictionary is None:
            return
        if dictionary.resources.css_file:
            try:
                self.manager.delete_css(dict_id)
                self._qt["QMessageBox"].information(self._dialog, "完成", "CSS 已删除")
            except Exception as exc:
                self._qt["QMessageBox"].warning(
                    self._dialog, "失败", f"删除失败: {exc}"
                )
            self.refresh_list()
            return

        file_path, _ = self._qt["QFileDialog"].getOpenFileName(
            self._dialog, "选择 CSS 文件", "", "CSS Files (*.css)"
        )
        if not file_path:
            return
        try:
            self.manager.add_css(dict_id, Path(file_path))
            self._qt["QMessageBox"].information(self._dialog, "完成", "CSS 已应用")
        except Exception as exc:
            self._qt["QMessageBox"].warning(
                self._dialog, "失败", f"CSS 处理失败: {exc}"
            )
        self.refresh_list()

    def on_toggle_enabled(self, dict_id: str, enabled: bool) -> None:
        """切换启用状态"""
        if not self.language_box.currentText():
            return
        self._stage_current_language()
        self.refresh_list()

    def on_rename(self, dict_id: str) -> None:
        """重命名辞典"""
        config = load_config(self.media_dir)
        dictionary = next(
            (item for item in config.dictionaries if item.id == dict_id), None
        )
        if dictionary is None:
            return
        new_name, ok = self._qt["QInputDialog"].getText(
            self._dialog, "重命名辞典", "辞典名称：", text=dictionary.name
        )
        if not ok or not new_name.strip():
            return
        try:
            self.manager.rename_dictionary(dict_id, new_name.strip())
            self._qt["QMessageBox"].information(self._dialog, "完成", "辞典已重命名")
        except Exception as exc:
            self._qt["QMessageBox"].warning(self._dialog, "失败", f"重命名失败: {exc}")
        self.refresh_list()

    def on_delete(self, dict_id: str) -> None:
        """删除辞典"""
        message_box = self._qt["QMessageBox"]
        confirm = message_box.question(self._dialog, "确认", "确定要删除该辞典吗？")
        yes_button = (
            message_box.StandardButton.Yes
            if hasattr(message_box, "StandardButton")
            else message_box.Yes
        )
        if confirm != yes_button:
            return
        try:
            self.manager.delete_dictionary(dict_id)
            self._qt["QMessageBox"].information(self._dialog, "完成", "辞典已删除")
        except Exception as exc:
            self._qt["QMessageBox"].warning(self._dialog, "失败", f"删除失败: {exc}")
        self.refresh_languages()

    def on_save_order(self) -> None:
        """保存排序"""
        language = self.language_box.currentText()
        if not language:
            return
        ordered_rows = list(self._iter_ordered_rows())
        ordered_ids = resolve_enabled_dictionary_ids(ordered_rows)
        self._save_language_dictionary_ids(language, ordered_ids)
        self._staged_rows_by_language.pop(language, None)
        self._qt["QMessageBox"].information(self._dialog, "完成", "更改已保存")
        self.refresh_list()

    def on_try_lookup(self) -> None:
        """执行快速试查"""
        language = self.language_box.currentText()
        word = self.lookup_input.text().strip()
        if not language or not word:
            self._qt["QMessageBox"].warning(self._dialog, "提示", "请输入词条")
            return
        result = self.lookup_service.try_lookup(language, word)
        if result is None:
            self.lookup_result.setText("未命中")
            return
        config = load_config(self.media_dir)
        dictionary = next(
            (
                item
                for item in config.dictionaries
                if item.id == result["dictionary_id"]
            ),
            None,
        )
        dict_name = dictionary.name if dictionary else result["dictionary_id"]
        definition = result["definition"]
        summary = definition[:200] + "..." if len(definition) > 200 else definition
        self.lookup_result.setText(f"{dict_name}：{summary}")

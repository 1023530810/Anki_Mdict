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
        "QCheckBox": qt.QCheckBox,
        "QComboBox": qt.QComboBox,
        "QDialog": qt.QDialog,
        "QDialogButtonBox": qt.QDialogButtonBox,
        "QFileDialog": qt.QFileDialog,
        "QGroupBox": qt.QGroupBox,
        "QHBoxLayout": qt.QHBoxLayout,
        "QHeaderView": qt.QHeaderView,
        "QInputDialog": qt.QInputDialog,
        "QLabel": qt.QLabel,
        "QLineEdit": qt.QLineEdit,
        "QMessageBox": qt.QMessageBox,
        "QPushButton": qt.QPushButton,
        "QScrollArea": qt.QScrollArea,
        "QSettings": qt.QSettings,
        "QTableWidget": qt.QTableWidget,
        "QTableWidgetItem": qt.QTableWidgetItem,
        "QTimer": qt.QTimer,
        "Qt": qt.Qt,
        "QVBoxLayout": qt.QVBoxLayout,
        "QWidget": qt.QWidget,
    }


class DictManagerDialog:
    """辞典管理对话框"""

    _column_ratio_key = "mdict/dict_manager/column_ratios"
    _default_column_ratios = (0.05, 0.15, 0.30, 0.50)

    def __init__(self, mw) -> None:
        qt = _load_qt()
        self._qt = qt
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

        self.dict_table = qt["QTableWidget"](0, 4)
        self.dict_table.setHorizontalHeaderLabels(["启用", "辞典", "资源", "操作"])
        self.dict_table.setWordWrap(False)
        qt_core = qt["Qt"]
        elide_right = (
            qt_core.TextElideMode.ElideRight
            if hasattr(qt_core, "TextElideMode")
            else qt_core.ElideRight
        )
        self.dict_table.setTextElideMode(elide_right)

        scroll_bar_off = (
            qt_core.ScrollBarPolicy.ScrollBarAlwaysOff
            if hasattr(qt_core, "ScrollBarPolicy")
            else qt_core.ScrollBarAlwaysOff
        )
        self.dict_table.setHorizontalScrollBarPolicy(scroll_bar_off)

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
        if hasattr(header, "setCascadingSectionResizes"):
            header.setCascadingSectionResizes(True)
        header_resize = qt["QHeaderView"]
        interactive_mode = (
            header_resize.ResizeMode.Interactive
            if hasattr(header_resize, "ResizeMode")
            else header_resize.Interactive
        )
        if hasattr(header, "setSectionResizeMode"):
            header.setSectionResizeMode(interactive_mode)
        if hasattr(header, "setStretchLastSection"):
            header.setStretchLastSection(False)
        vertical_header = self.dict_table.verticalHeader()
        if vertical_header is not None:
            vertical_header.setVisible(False)

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

        # 分词选项区域
        self.extract_lemma_box = qt["QCheckBox"]("提取单词原型（词根）")
        self.show_pronunciation_box = qt["QCheckBox"]("显示发音标注")
        self.show_pronunciation_label = qt["QLabel"]("显示发音标注")

        tokenizer_group = qt["QGroupBox"]("分词选项")
        tokenizer_layout = qt["QHBoxLayout"]()
        tokenizer_layout.addWidget(self.extract_lemma_box)
        tokenizer_layout.addWidget(self.show_pronunciation_box)
        tokenizer_layout.addStretch()
        tokenizer_group.setLayout(tokenizer_layout)

        lookup_row = qt["QHBoxLayout"]()
        lookup_row.addWidget(self.lookup_input)
        lookup_row.addWidget(self.lookup_button)

        layout = qt["QVBoxLayout"]()
        layout.addLayout(header_row)
        layout.addWidget(tokenizer_group)
        layout.addWidget(qt["QLabel"]("辞典列表（拖拽调整查询顺序）："))
        layout.addWidget(self.dict_table)
        layout.addWidget(self.save_order_button)
        layout.addWidget(qt["QLabel"]("快速试查："))
        layout.addLayout(lookup_row)
        layout.addWidget(self.lookup_result)
        self._dialog.setLayout(layout)

        self._enable_boxes: dict[str, object] = {}
        self._staged_rows_by_language: dict[str, list[tuple[str, bool]]] = {}
        self._current_language = ""
        self._rebuilding_after_move = False
        self._resizing_header = False

        header.sectionResized.connect(self._on_header_section_resized)
        self._schedule_apply_column_ratios()

        self._original_resize_event = self._dialog.resizeEvent
        self._dialog.resizeEvent = self._on_dialog_resized

        self.refresh_languages()

    def exec(self) -> int:
        """显示对话框"""
        return self._dialog.exec()

    def _schedule_apply_column_ratios(self) -> None:
        ratios = self._load_column_ratios()
        self._qt["QTimer"].singleShot(0, lambda: self._apply_column_ratios(ratios))

    def _load_column_ratios(self) -> list[float]:
        settings = self._qt["QSettings"]("Anki", "MDict")
        raw_value = settings.value(self._column_ratio_key)
        ratios = self._coerce_ratios(raw_value)
        if ratios is None:
            ratios = list(self._default_column_ratios)
        return ratios

    def _coerce_ratios(self, value) -> list[float] | None:
        if value is None:
            return None
        if isinstance(value, str):
            parts = [item.strip() for item in value.split(",") if item.strip()]
        elif isinstance(value, (list, tuple)):
            parts = list(value)
        else:
            return None
        try:
            ratios = [float(item) for item in parts]
        except (TypeError, ValueError):
            return None
        if len(ratios) != 4 or any(ratio <= 0 for ratio in ratios):
            return None
        total = sum(ratios)
        if total <= 0:
            return None
        return [ratio / total for ratio in ratios]

    def _save_column_ratios(self, ratios: list[float]) -> None:
        settings = self._qt["QSettings"]("Anki", "MDict")
        settings.setValue(self._column_ratio_key, [f"{ratio:.6f}" for ratio in ratios])

    def _apply_column_ratios(self, ratios: list[float]) -> None:
        total_width = max(
            self.dict_table.viewport().width(),
            self.dict_table.width(),
            max(self._dialog.width() - 40, 0),
        )
        if total_width <= 0:
            return
        min_width = 40
        remaining = total_width
        widths: list[int] = []
        for index, ratio in enumerate(ratios):
            if index == len(ratios) - 1:
                width = max(min_width, remaining)
            else:
                width = max(min_width, int(total_width * ratio))
                remaining -= width
            widths.append(width)
        self._resizing_header = True
        try:
            for index, width in enumerate(widths):
                self.dict_table.setColumnWidth(index, width)
        finally:
            self._resizing_header = False

    def _on_header_section_resized(self, *args) -> None:
        if self._resizing_header:
            return
        widths = [self.dict_table.columnWidth(index) for index in range(4)]
        total = sum(widths)
        if total <= 0:
            return
        ratios = [width / total for width in widths]
        self._save_column_ratios(ratios)

    def _on_dialog_resized(self, event) -> None:
        if hasattr(self, "_original_resize_event") and self._original_resize_event:
            self._original_resize_event(event)
        ratios = self._load_column_ratios()
        self._apply_column_ratios(ratios)

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

        # 加载分词配置
        tokenizer = config.tokenizers.get(language)
        self.extract_lemma_box.setChecked(
            tokenizer.extract_lemma if tokenizer else True
        )
        # 根据语言设置发音标注复选框和标签
        if language == "ja":
            self.show_pronunciation_box.setText("显示注音")
            self.show_pronunciation_box.setChecked(
                tokenizer.show_reading if tokenizer else False
            )
        elif language == "en":
            self.show_pronunciation_box.setText("显示音标")
            self.show_pronunciation_box.setChecked(
                tokenizer.show_ipa if tokenizer else False
            )
        else:
            # 其他语言默认显示为"显示发音标注"
            self.show_pronunciation_box.setText("显示发音标注")
            self.show_pronunciation_box.setChecked(False)
            self.show_pronunciation_box.setEnabled(False)

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

            # 第 0 列：启用复选框
            enable_widget = self._qt["QWidget"]()
            enable_layout = self._qt["QHBoxLayout"]()
            enable_layout.setContentsMargins(4, 2, 4, 2)
            enable_box = self._qt["QCheckBox"]()
            enable_box.setChecked(dictionary.id in enabled_set)
            enable_box.toggled.connect(
                lambda checked, dict_id=dictionary.id: self.on_toggle_enabled(
                    dict_id, checked
                )
            )
            self._enable_boxes[dictionary.id] = enable_box
            enable_layout.addWidget(enable_box)
            enable_layout.addStretch()
            enable_widget.setLayout(enable_layout)
            self.dict_table.setCellWidget(row_index, 0, enable_widget)

            # 第 1 列：辞典名称（存储 dict_id）
            name_item = self._qt["QTableWidgetItem"](dictionary.name)
            name_item.setData(256, dictionary.id)
            self.dict_table.setItem(row_index, 1, name_item)

            # 第 2 列：资源状态
            badge_text = self._build_resource_badge(dictionary)
            badge_item = self._qt["QTableWidgetItem"](badge_text)
            self.dict_table.setItem(row_index, 2, badge_item)

            # 第 3 列：操作按钮
            action_widget = self._build_action_widget(dictionary)
            self.dict_table.setCellWidget(row_index, 3, action_widget)
            self.dict_table.resizeRowToContents(row_index)

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

    def _build_action_widget(self, dictionary: Dictionary):
        """构建行内操作区"""
        container = self._qt["QWidget"]()
        layout = self._qt["QHBoxLayout"]()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)

        mdd_button = self._qt["QPushButton"](
            "删除MDD" if dictionary.resources.has_mdd else "添加MDD"
        )
        mdd_button.clicked.connect(
            lambda _checked=False, dict_id=dictionary.id: self.on_mdd_action(dict_id)
        )

        css_button = self._qt["QPushButton"](
            "删除CSS" if dictionary.resources.css_file else "添加CSS"
        )
        css_button.clicked.connect(
            lambda _checked=False, dict_id=dictionary.id: self.on_css_action(dict_id)
        )

        rename_button = self._qt["QPushButton"]("重命名")
        rename_button.clicked.connect(
            lambda _checked=False, dict_id=dictionary.id: self.on_rename(dict_id)
        )

        delete_button = self._qt["QPushButton"]("删除")
        delete_button.clicked.connect(
            lambda _checked=False, dict_id=dictionary.id: self.on_delete(dict_id)
        )

        lang_button = self._qt["QPushButton"]("选择语言")
        lang_button.clicked.connect(
            lambda _checked=False, dict_id=dictionary.id: self.on_edit_languages(
                dict_id
            )
        )

        for btn in [mdd_button, css_button, rename_button, delete_button, lang_button]:
            btn.setMinimumWidth(50)
            btn.setMaximumWidth(70)

        layout.addWidget(mdd_button)
        layout.addWidget(css_button)
        layout.addWidget(rename_button)
        layout.addWidget(delete_button)
        layout.addWidget(lang_button)
        layout.addStretch()

        container.setLayout(layout)
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
            item = self.dict_table.item(row_index, 1)
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

        config = load_config(self.media_dir)
        tokenizer = config.tokenizers.get(language)

        # 根据语言类型构建分词配置
        extract_lemma = self.extract_lemma_box.isChecked()
        pronunciation_checked = self.show_pronunciation_box.isChecked()

        if tokenizer:
            # 更新现有配置
            tokenizer = replace(
                tokenizer,
                extract_lemma=extract_lemma,
                dictionary_ids=ordered_ids,
            )
            if language == "ja":
                tokenizer = replace(tokenizer, show_reading=pronunciation_checked)
            elif language == "en":
                tokenizer = replace(tokenizer, show_ipa=pronunciation_checked)
            config.tokenizers[language] = tokenizer
        else:
            # 创建新配置
            if language == "ja":
                tokenizer = TokenizerConfig(
                    language=language,
                    extract_lemma=extract_lemma,
                    show_reading=pronunciation_checked,
                    show_ipa=False,
                    dictionary_ids=ordered_ids,
                )
            elif language == "en":
                tokenizer = TokenizerConfig(
                    language=language,
                    extract_lemma=extract_lemma,
                    show_reading=False,
                    show_ipa=pronunciation_checked,
                    dictionary_ids=ordered_ids,
                )
            else:
                # 其他语言使用默认配置
                tokenizer = TokenizerConfig(
                    language=language,
                    extract_lemma=extract_lemma,
                    show_reading=False,
                    show_ipa=False,
                    dictionary_ids=ordered_ids,
                )
            config.tokenizers[language] = tokenizer
        save_config(self.media_dir, config)

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
        results = self.lookup_service.try_lookup_all(language, word)
        if not results:
            self.lookup_result.setText("未命中")
            return
        config = load_config(self.media_dir)
        dict_map = {item.id: item.name for item in config.dictionaries}
        names = [dict_map.get(r["dictionary_id"], r["dictionary_id"]) for r in results]
        self.lookup_result.setText(f"命中：{', '.join(names)}")

    def on_edit_languages(self, dict_id: str) -> None:
        """编辑辞典语言"""
        config = load_config(self.media_dir)
        dictionary = next(
            (item for item in config.dictionaries if item.id == dict_id), None
        )
        if dictionary is None:
            return

        all_languages = collect_languages(config.dictionaries, config.tokenizers)
        if not all_languages:
            all_languages = {"ja", "en"}

        language_names = {
            "ja": "日语",
            "en": "英语",
            "zh": "中文",
            "ko": "韩语",
            "fr": "法语",
            "de": "德语",
            "es": "西班牙语",
            "it": "意大利语",
            "pt": "葡萄牙语",
            "ru": "俄语",
        }

        dialog = self._qt["QDialog"](self._dialog)
        dialog.setWindowTitle("编辑辞典语言")
        dialog.resize(320, 400)

        layout = self._qt["QVBoxLayout"]()

        name_label = self._qt["QLabel"](f"辞典名称：{dictionary.name}")
        layout.addWidget(name_label)

        select_label = self._qt["QLabel"]("选择适用语言：")
        layout.addWidget(select_label)

        scroll_area = self._qt["QScrollArea"]()
        scroll_area.setWidgetResizable(True)
        scroll_widget = self._qt["QWidget"]()
        scroll_layout = self._qt["QVBoxLayout"]()
        scroll_layout.setContentsMargins(4, 4, 4, 4)
        scroll_layout.setSpacing(4)

        checkboxes: list[tuple[str, object]] = []
        for lang in sorted(all_languages):
            display_name = language_names.get(lang, lang)
            checkbox = self._qt["QCheckBox"](f"{lang} ({display_name})")
            checkbox.setChecked(lang in dictionary.languages)
            checkboxes.append((lang, checkbox))
            scroll_layout.addWidget(checkbox)

        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        custom_label = self._qt["QLabel"]("自定义语言：")
        layout.addWidget(custom_label)

        custom_input = self._qt["QLineEdit"]()
        custom_input.setPlaceholderText("逗号分隔，如：vi, th, ar")
        layout.addWidget(custom_input)

        hint_label = self._qt["QLabel"]("(添加不在列表中的语言)")
        layout.addWidget(hint_label)

        button_box = self._qt["QDialogButtonBox"](
            self._qt["QDialogButtonBox"].StandardButton.Ok
            | self._qt["QDialogButtonBox"].StandardButton.Cancel
        )
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        button_box.rejected.connect(dialog.reject)

        def on_accept():
            selected_languages: list[str] = []
            for lang, checkbox in checkboxes:
                checker = getattr(checkbox, "isChecked", None)
                if callable(checker) and checker():
                    selected_languages.append(lang)

            custom_text = custom_input.text().strip()
            if custom_text:
                custom_langs = [
                    lang.strip() for lang in custom_text.split(",") if lang.strip()
                ]
                for lang in custom_langs:
                    if lang not in selected_languages:
                        selected_languages.append(lang)

            if not selected_languages:
                self._qt["QMessageBox"].warning(dialog, "提示", "请至少选择一种语言")
                return

            self._save_dictionary_languages(dict_id, selected_languages)
            dialog.accept()

        button_box.accepted.connect(on_accept)

        dialog.exec()

    def _save_dictionary_languages(self, dict_id: str, languages: list[str]) -> None:
        """保存辞典语言设置"""
        config = load_config(self.media_dir)
        for i, dictionary in enumerate(config.dictionaries):
            if dictionary.id == dict_id:
                config.dictionaries[i] = replace(dictionary, languages=languages)
                break
        save_config(self.media_dir, config)
        self.refresh_languages()
        self.refresh_list()

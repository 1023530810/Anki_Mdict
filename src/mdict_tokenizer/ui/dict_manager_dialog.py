"""辞典管理对话框"""

from __future__ import annotations

from pathlib import Path
from typing import List

from ..config import get_media_dir_from_mw, load_config
from ..dict_manager import DictionaryManager


LANGUAGE_OPTIONS = ["ja", "en", "ja,en"]


def _load_qt():
    """动态加载 Qt 组件"""
    import importlib

    qt = importlib.import_module("aqt.qt")
    return {
        "QAbstractItemView": qt.QAbstractItemView,
        "QDialog": qt.QDialog,
        "QHBoxLayout": qt.QHBoxLayout,
        "QLabel": qt.QLabel,
        "QListWidget": qt.QListWidget,
        "QListWidgetItem": qt.QListWidgetItem,
        "QMessageBox": qt.QMessageBox,
        "QPushButton": qt.QPushButton,
        "QVBoxLayout": qt.QVBoxLayout,
        "QFileDialog": qt.QFileDialog,
        "QInputDialog": qt.QInputDialog,
    }


class DictManagerDialog:
    """辞典管理对话框"""

    def __init__(self, mw) -> None:
        qt = _load_qt()
        self._dialog = qt["QDialog"](mw)
        self.mw = mw
        self.media_dir = get_media_dir_from_mw(mw)
        self.manager = DictionaryManager(self.media_dir)

        self._dialog.setWindowTitle("MDict 辞典管理")
        self._dialog.resize(640, 420)

        self.list_widget = qt["QListWidget"]()
        self.list_widget.setSelectionMode(qt["QAbstractItemView"].SingleSelection)
        self.list_widget.setDragDropMode(qt["QAbstractItemView"].InternalMove)

        self.import_button = qt["QPushButton"]("导入 MDX")
        self.import_button.clicked.connect(self.on_import)

        self.add_mdd_button = qt["QPushButton"]("添加 MDD")
        self.add_mdd_button.clicked.connect(self.on_add_mdd)

        self.add_css_button = qt["QPushButton"]("添加 CSS")
        self.add_css_button.clicked.connect(self.on_add_css)

        self.delete_button = qt["QPushButton"]("删除辞典")
        self.delete_button.clicked.connect(self.on_delete)

        self.save_order_button = qt["QPushButton"]("保存顺序")
        self.save_order_button.clicked.connect(self.on_save_order)

        button_row = qt["QHBoxLayout"]()
        button_row.addWidget(self.import_button)
        button_row.addWidget(self.add_mdd_button)
        button_row.addWidget(self.add_css_button)
        button_row.addWidget(self.delete_button)
        button_row.addWidget(self.save_order_button)

        layout = qt["QVBoxLayout"]()
        layout.addWidget(qt["QLabel"]("拖拽调整顺序："))
        layout.addWidget(self.list_widget)
        layout.addLayout(button_row)
        self._dialog.setLayout(layout)

        self._qt = qt
        self.refresh()

    def exec(self) -> int:
        """显示对话框"""
        return self._dialog.exec()

    def refresh(self) -> None:
        """刷新列表"""
        self.list_widget.clear()
        config = load_config(self.media_dir)
        for dictionary in sorted(config.dictionaries, key=lambda item: item.order):
            label = f"{dictionary.name} ({','.join(dictionary.languages)})"
            item = self._qt["QListWidgetItem"](label)
            item.setData(256, dictionary.id)
            self.list_widget.addItem(item)

    def current_dict_id(self) -> str | None:
        """获取当前选中辞典 ID"""
        item = self.list_widget.currentItem()
        if item is None:
            return None
        return item.data(256)

    def on_import(self) -> None:
        """导入辞典"""
        file_path, _ = self._qt["QFileDialog"].getOpenFileName(
            self._dialog, "选择 MDX 文件", "", "MDX Files (*.mdx)"
        )
        if not file_path:
            return
        language, ok = self._qt["QInputDialog"].getItem(
            self._dialog, "选择语言", "辞典语言：", LANGUAGE_OPTIONS, 0, False
        )
        if not ok:
            return
        languages = [lang.strip() for lang in language.split(",") if lang.strip()]
        try:
            self.manager.import_dictionary(Path(file_path), languages)
            self._qt["QMessageBox"].information(self._dialog, "完成", "辞典导入完成")
        except Exception as exc:
            self._qt["QMessageBox"].warning(self._dialog, "失败", f"导入失败: {exc}")
        self.refresh()

    def on_add_mdd(self) -> None:
        """添加 MDD"""
        dict_id = self.current_dict_id()
        if not dict_id:
            self._qt["QMessageBox"].warning(self._dialog, "提示", "请先选择辞典")
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
        self.refresh()

    def on_add_css(self) -> None:
        """添加 CSS"""
        dict_id = self.current_dict_id()
        if not dict_id:
            self._qt["QMessageBox"].warning(self._dialog, "提示", "请先选择辞典")
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
        self.refresh()

    def on_delete(self) -> None:
        """删除辞典"""
        dict_id = self.current_dict_id()
        if not dict_id:
            self._qt["QMessageBox"].warning(self._dialog, "提示", "请先选择辞典")
            return
        confirm = self._qt["QMessageBox"].question(
            self._dialog, "确认", "确定要删除该辞典吗？"
        )
        if confirm != self._qt["QMessageBox"].Yes:
            return
        try:
            self.manager.delete_dictionary(dict_id)
            self._qt["QMessageBox"].information(self._dialog, "完成", "辞典已删除")
        except Exception as exc:
            self._qt["QMessageBox"].warning(self._dialog, "失败", f"删除失败: {exc}")
        self.refresh()

    def on_save_order(self) -> None:
        """保存排序"""
        ordered_ids: List[str] = []
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            ordered_ids.append(item.data(256))
        self.manager.reorder_dictionaries(ordered_ids)
        self._qt["QMessageBox"].information(self._dialog, "完成", "排序已保存")
        self.refresh()

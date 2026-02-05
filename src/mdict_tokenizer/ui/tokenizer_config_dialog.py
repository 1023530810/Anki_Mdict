"""分词配置对话框"""

from __future__ import annotations

from ..config import get_media_dir_from_mw, load_config
from ..tokenizer_config import TokenizerConfigService


def _load_qt():
    """动态加载 Qt 组件"""
    import importlib

    qt = importlib.import_module("aqt.qt")
    return {
        "QCheckBox": qt.QCheckBox,
        "QComboBox": qt.QComboBox,
        "QDialog": qt.QDialog,
        "QHBoxLayout": qt.QHBoxLayout,
        "QLabel": qt.QLabel,
        "QListWidget": qt.QListWidget,
        "QListWidgetItem": qt.QListWidgetItem,
        "QMessageBox": qt.QMessageBox,
        "QPushButton": qt.QPushButton,
        "QVBoxLayout": qt.QVBoxLayout,
        "Qt": qt.Qt,
    }


class TokenizerConfigDialog:
    """分词配置对话框"""

    def __init__(self, mw) -> None:
        qt = _load_qt()
        self._dialog = qt["QDialog"](mw)
        self.mw = mw
        self.media_dir = get_media_dir_from_mw(mw)
        self.service = TokenizerConfigService(self.media_dir)

        self._dialog.setWindowTitle("MDict 分词配置")
        self._dialog.resize(520, 400)

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

        self.language_box = qt["QComboBox"]()
        self.language_box.addItems(["ja", "en"])
        self.language_box.currentTextChanged.connect(self.refresh)

        self.extract_lemma_box = qt["QCheckBox"]("提取单词原型")
        self.show_reading_box = qt["QCheckBox"]("显示注音")
        self.show_ipa_box = qt["QCheckBox"]("显示音标")

        self.dict_list = qt["QListWidget"]()
        self.save_button = qt["QPushButton"]("保存配置")
        self.save_button.clicked.connect(self.on_save)

        header_row = qt["QHBoxLayout"]()
        header_row.addWidget(qt["QLabel"]("语言："))
        header_row.addWidget(self.language_box)
        header_row.addStretch()

        layout = qt["QVBoxLayout"]()
        layout.addLayout(header_row)
        layout.addWidget(self.extract_lemma_box)
        layout.addWidget(self.show_reading_box)
        layout.addWidget(self.show_ipa_box)
        layout.addWidget(qt["QLabel"]("关联辞典："))
        layout.addWidget(self.dict_list)
        layout.addWidget(self.save_button)
        self._dialog.setLayout(layout)

        self._qt = qt
        self.refresh()

    def exec(self) -> int:
        """显示对话框"""
        return self._dialog.exec()

    def refresh(self) -> None:
        """刷新配置"""
        language = self.language_box.currentText()
        config = load_config(self.media_dir)
        tokenizer = config.tokenizers.get(language)

        self.extract_lemma_box.setChecked(
            tokenizer.extract_lemma if tokenizer else True
        )
        self.show_reading_box.setChecked(tokenizer.show_reading if tokenizer else False)
        self.show_ipa_box.setChecked(tokenizer.show_ipa if tokenizer else False)

        self.show_reading_box.setVisible(language == "ja")
        self.show_ipa_box.setVisible(language == "en")

        self.dict_list.clear()
        for dictionary in config.dictionaries:
            if language not in dictionary.languages:
                continue
            item = self._qt["QListWidgetItem"](dictionary.name)
            item.setData(256, dictionary.id)
            item.setCheckState(
                self._checked_state
                if tokenizer and dictionary.id in tokenizer.dictionary_ids
                else self._unchecked_state
            )
            self.dict_list.addItem(item)

    def on_save(self) -> None:
        """保存配置"""
        language = self.language_box.currentText()
        dictionary_ids = []
        for index in range(self.dict_list.count()):
            item = self.dict_list.item(index)
            if item.checkState() == self._checked_state:
                dictionary_ids.append(item.data(256))
        self.service.update_tokenizer(
            language=language,
            extract_lemma=self.extract_lemma_box.isChecked(),
            show_reading=self.show_reading_box.isChecked(),
            show_ipa=self.show_ipa_box.isChecked(),
            dictionary_ids=dictionary_ids,
        )
        self._qt["QMessageBox"].information(self._dialog, "完成", "配置已保存")

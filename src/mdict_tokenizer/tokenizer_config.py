"""分词系统配置"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import List

from .config import MainConfig, TokenizerConfig, load_config, save_config


class TokenizerConfigService:
    """分词配置服务"""

    def __init__(self, media_dir: Path) -> None:
        self.media_dir = media_dir

    def get_config(self) -> MainConfig:
        """获取主配置"""
        return load_config(self.media_dir)

    def get_available_dictionaries(self, language: str) -> List[str]:
        """获取可用辞典 ID"""
        config = load_config(self.media_dir)
        return [
            dictionary.id
            for dictionary in config.dictionaries
            if language in dictionary.languages
        ]

    def update_tokenizer(
        self,
        language: str,
        extract_lemma: bool,
        show_reading: bool,
        show_ipa: bool,
        dictionary_ids: List[str],
    ) -> None:
        """更新分词配置"""
        config = load_config(self.media_dir)
        valid_dicts = {
            dictionary.id
            for dictionary in config.dictionaries
            if language in dictionary.languages
        }
        filtered_ids = [dict_id for dict_id in dictionary_ids if dict_id in valid_dicts]
        tokenizer = TokenizerConfig(
            language=language,
            extract_lemma=extract_lemma,
            show_reading=show_reading if language == "ja" else False,
            show_ipa=show_ipa if language == "en" else False,
            dictionary_ids=filtered_ids,
        )
        config.tokenizers[language] = tokenizer
        save_config(self.media_dir, config)

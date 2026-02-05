"""辞典管理与分词配置集成测试"""

from __future__ import annotations

from pathlib import Path

from mdict_tokenizer.config import (
    MainConfig,
    TokenizerConfig,
    load_config,
    save_config,
)


def test_tokenizer_config_persists_with_dict_manager(tmp_path: Path) -> None:
    """测试分词配置在辞典管理中的持久化"""
    # 创建初始配置
    config = MainConfig()
    config.tokenizers["ja"] = TokenizerConfig(
        language="ja",
        extract_lemma=True,
        show_reading=True,
        show_ipa=False,
        dictionary_ids=["dict1", "dict2"],
    )
    config.tokenizers["en"] = TokenizerConfig(
        language="en",
        extract_lemma=False,
        show_reading=False,
        show_ipa=True,
        dictionary_ids=["dict3"],
    )
    save_config(tmp_path, config)

    # 加载并验证
    loaded = load_config(tmp_path)

    # 验证日语配置
    assert "ja" in loaded.tokenizers
    ja_config = loaded.tokenizers["ja"]
    assert ja_config.extract_lemma is True
    assert ja_config.show_reading is True
    assert ja_config.show_ipa is False
    assert ja_config.dictionary_ids == ["dict1", "dict2"]

    # 验证英语配置
    assert "en" in loaded.tokenizers
    en_config = loaded.tokenizers["en"]
    assert en_config.extract_lemma is False
    assert en_config.show_reading is False
    assert en_config.show_ipa is True
    assert en_config.dictionary_ids == ["dict3"]


def test_tokenizer_config_language_specific_flags(tmp_path: Path) -> None:
    """测试语言特定的发音标注标志"""
    config = MainConfig()

    # 日语：show_reading 应该生效，show_ipa 应该为 False
    config.tokenizers["ja"] = TokenizerConfig(
        language="ja",
        extract_lemma=True,
        show_reading=True,
        show_ipa=False,
        dictionary_ids=[],
    )

    # 英语：show_ipa 应该生效，show_reading 应该为 False
    config.tokenizers["en"] = TokenizerConfig(
        language="en",
        extract_lemma=True,
        show_reading=False,
        show_ipa=True,
        dictionary_ids=[],
    )

    save_config(tmp_path, config)
    loaded = load_config(tmp_path)

    # 验证日语只有 show_reading
    assert loaded.tokenizers["ja"].show_reading is True
    assert loaded.tokenizers["ja"].show_ipa is False

    # 验证英语只有 show_ipa
    assert loaded.tokenizers["en"].show_reading is False
    assert loaded.tokenizers["en"].show_ipa is True


def test_tokenizer_config_extract_lemma_independent(tmp_path: Path) -> None:
    """测试 extract_lemma 独立于语言"""
    config = MainConfig()

    # extract_lemma 对所有语言都适用
    config.tokenizers["ja"] = TokenizerConfig(
        language="ja",
        extract_lemma=True,
        show_reading=False,
        show_ipa=False,
        dictionary_ids=[],
    )

    config.tokenizers["en"] = TokenizerConfig(
        language="en",
        extract_lemma=False,
        show_reading=False,
        show_ipa=False,
        dictionary_ids=[],
    )

    save_config(tmp_path, config)
    loaded = load_config(tmp_path)

    assert loaded.tokenizers["ja"].extract_lemma is True
    assert loaded.tokenizers["en"].extract_lemma is False

"""分词语言与默认辞典配置测试"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mdict_tokenizer.config import (
    Dictionary,
    TokenizerConfig,
    collect_languages,
    ensure_tokenizer_dictionary_ids,
)


def test_collect_languages_union() -> None:
    dictionaries = [
        Dictionary(id="dict_ja", name="日语", languages=["ja"], order=0),
        Dictionary(id="dict_en", name="英语", languages=["en"], order=1),
    ]
    tokenizers = {
        "ja": TokenizerConfig(language="ja"),
        "fr": TokenizerConfig(language="fr"),
    }

    languages = collect_languages(dictionaries, tokenizers)

    assert set(languages) == {"ja", "en", "fr"}


def test_ensure_tokenizer_dictionary_ids_defaults() -> None:
    dictionaries = [
        Dictionary(id="dict_a", name="A", languages=["ja"], order=1),
        Dictionary(id="dict_b", name="B", languages=["ja", "en"], order=0),
        Dictionary(id="dict_c", name="C", languages=["en"], order=2),
    ]
    tokenizers = {
        "ja": TokenizerConfig(language="ja", dictionary_ids=[]),
        "fr": TokenizerConfig(language="fr", dictionary_ids=["keep"]),
    }

    updated = ensure_tokenizer_dictionary_ids(dictionaries, tokenizers)

    assert updated["ja"].dictionary_ids == ["dict_b", "dict_a"]
    assert updated["en"].dictionary_ids == ["dict_b", "dict_c"]
    assert updated["fr"].dictionary_ids == ["keep"]

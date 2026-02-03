"""分词语言默认填充测试"""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mdict_tokenizer.config import (
    Dictionary,
    MainConfig,
    TokenizerConfig,
    collect_languages,
    ensure_tokenizer_dictionary_ids,
    resolve_language_tokenizers,
)


def test_language_union_and_defaults() -> None:
    dictionaries = [
        Dictionary(id="d1", name="dict1", languages=["ja"], order=2),
        Dictionary(id="d2", name="dict2", languages=["ja", "en"], order=1),
        Dictionary(id="d3", name="dict3", languages=["en"], order=0),
    ]
    tokenizers = {
        "ja": TokenizerConfig(language="ja", dictionary_ids=[]),
        "fr": TokenizerConfig(language="fr", dictionary_ids=["keep"]),
    }

    languages = collect_languages(dictionaries, tokenizers)
    updated = ensure_tokenizer_dictionary_ids(dictionaries, tokenizers)

    assert set(languages) == {"ja", "en", "fr"}
    assert updated["ja"].dictionary_ids == ["d2", "d1"]
    assert updated["en"].dictionary_ids == ["d3", "d2"]
    assert updated["fr"].dictionary_ids == ["keep"]


def test_missing_tokenizer_defaults() -> None:
    dictionaries = [
        Dictionary(id="d1", name="dict1", languages=["ja"], order=1),
        Dictionary(id="d2", name="dict2", languages=["en"], order=0),
    ]

    updated = ensure_tokenizer_dictionary_ids(dictionaries, {})

    assert updated["ja"].dictionary_ids == ["d1"]
    assert updated["en"].dictionary_ids == ["d2"]


def test_resolve_language_tokenizers_from_config() -> None:
    dictionaries = [
        Dictionary(id="d1", name="dict1", languages=["ja"], order=1),
        Dictionary(id="d2", name="dict2", languages=["en"], order=0),
    ]
    tokenizers = {
        "ja": TokenizerConfig(language="ja", dictionary_ids=[]),
    }
    config = MainConfig(dictionaries=dictionaries, tokenizers=tokenizers)

    resolved = resolve_language_tokenizers(config)

    assert resolved["ja"].dictionary_ids == ["d1"]
    assert resolved["en"].dictionary_ids == ["d2"]

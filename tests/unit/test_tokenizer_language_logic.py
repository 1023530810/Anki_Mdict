"""分词语言逻辑单元测试"""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mdict_tokenizer.config import Dictionary, TokenizerConfig
from mdict_tokenizer.tokenizer_language import (
    aggregate_language_set,
    resolve_tokenizer_dictionary_ids,
)


def test_aggregate_language_set_union() -> None:
    dictionaries = [
        Dictionary(id="d1", name="dict1", languages=["ja"], order=0),
        Dictionary(id="d2", name="dict2", languages=["en"], order=1),
    ]
    tokenizers = {"fr": TokenizerConfig(language="fr")}

    languages = aggregate_language_set(dictionaries, tokenizers)

    assert languages == {"ja", "en", "fr"}


def test_resolve_dictionary_ids_defaults_and_filtering() -> None:
    dictionaries = [
        Dictionary(id="d1", name="dict1", languages=["ja", "en"], order=2),
        Dictionary(id="d2", name="dict2", languages=["ja"], order=1),
        Dictionary(id="d3", name="dict3", languages=["en"], order=0),
    ]
    tokenizers = {
        "ja": TokenizerConfig(language="ja", dictionary_ids=[]),
        "en": TokenizerConfig(language="en", dictionary_ids=["d3", "missing"]),
    }

    resolved = resolve_tokenizer_dictionary_ids(dictionaries, tokenizers)

    assert resolved["ja"] == ["d2", "d1"]
    assert resolved["en"] == ["d3"]

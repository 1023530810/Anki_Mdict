"""DictManagerDialog 逻辑测试"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mdict_tokenizer.config import Dictionary, DictionaryMeta, DictionaryResources
from mdict_tokenizer.ui.dict_manager_dialog_logic import (
    filter_dictionaries_by_language,
    order_dictionaries_for_display,
    resolve_enabled_dictionary_ids,
)


def _make_dictionary(
    dict_id: str,
    name: str,
    languages: list[str],
    order: int,
) -> Dictionary:
    return Dictionary(
        id=dict_id,
        name=name,
        languages=languages,
        order=order,
        meta=DictionaryMeta(),
        resources=DictionaryResources(),
        file_prefix=f"_mdict_{dict_id}",
    )


def test_filter_dictionaries_by_language() -> None:
    dictionaries = [
        _make_dictionary("a", "A", ["ja"], 0),
        _make_dictionary("b", "B", ["en"], 1),
        _make_dictionary("c", "C", ["ja", "en"], 2),
    ]

    filtered = filter_dictionaries_by_language(dictionaries, "ja")

    assert [item.id for item in filtered] == ["a", "c"]


def test_order_dictionaries_for_display_enabled_first() -> None:
    dictionaries = [
        _make_dictionary("a", "A", ["ja"], 2),
        _make_dictionary("b", "B", ["ja"], 0),
        _make_dictionary("c", "C", ["ja"], 1),
    ]

    ordered = order_dictionaries_for_display(
        dictionaries,
        "ja",
        ["c", "a"],
    )

    assert [item.id for item in ordered] == ["c", "a", "b"]


def test_order_dictionaries_for_display_default_order_when_disabled() -> None:
    dictionaries = [
        _make_dictionary("a", "A", ["ja"], 2),
        _make_dictionary("b", "B", ["ja"], 0),
        _make_dictionary("c", "C", ["ja"], 1),
    ]

    ordered = order_dictionaries_for_display(dictionaries, "ja", [])

    assert [item.id for item in ordered] == ["b", "c", "a"]


def test_resolve_enabled_dictionary_ids() -> None:
    rows = [("a", True), ("b", False), ("c", True)]

    assert resolve_enabled_dictionary_ids(rows) == ["a", "c"]

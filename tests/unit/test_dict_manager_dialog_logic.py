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
    resolve_display_order_from_staged,
    resolve_enabled_dictionary_ids,
    update_staged_rows_by_language,
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


def test_resolve_enabled_dictionary_ids_preserves_row_order() -> None:
    rows = [("b", True), ("a", True), ("c", False), ("d", True)]

    assert resolve_enabled_dictionary_ids(rows) == ["b", "a", "d"]


def test_update_staged_rows_by_language_adds_or_removes() -> None:
    staged = {"ja": [("a", True)]}

    updated = update_staged_rows_by_language(staged, "en", [("b", False)])
    assert updated["ja"] == [("a", True)]
    assert updated["en"] == [("b", False)]

    removed = update_staged_rows_by_language(updated, "ja", [])
    assert "ja" not in removed
    assert removed["en"] == [("b", False)]


def test_resolve_display_order_from_staged_appends_missing_by_order() -> None:
    dictionaries = [
        _make_dictionary("a", "A", ["ja"], 2),
        _make_dictionary("b", "B", ["ja"], 0),
        _make_dictionary("c", "C", ["ja"], 1),
    ]

    ordered, enabled_set = resolve_display_order_from_staged(
        dictionaries, [("c", True)]
    )

    assert [item.id for item in ordered] == ["c", "b", "a"]
    assert enabled_set == {"c"}

"""辞典管理单元测试"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from _pytest.monkeypatch import MonkeyPatch


ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mdict_tokenizer import dict_manager, mdx_processor
from mdict_tokenizer.config import (
    Dictionary,
    DictionaryMeta,
    MainConfig,
    TokenizerConfig,
    load_config,
    save_config,
)
from mdict_tokenizer.try_lookup import TryLookupService


class DummyMDD:
    """模拟 MDD"""

    path: str

    def __init__(self, path: str) -> None:
        self.path = path

    def items(self) -> list[tuple[bytes, bytes]]:
        return [(b"audio/a.mp3", b"data")]


def fake_process_mdx(
    mdx_path: Path,
    output_dir: Path,
    dict_id: str | None = None,
    _shard_size_bytes: int = 0,
) -> tuple[str, mdx_processor.ShardMeta]:
    dict_id = "testdict" if dict_id is None else dict_id
    _ = (output_dir / f"_mdict_{dict_id}_shard_0.json").write_text(
        '{"entries": []}', encoding="utf-8"
    )
    _ = (output_dir / f"_mdict_{dict_id}_index.json").write_text(
        '{"entries": {}}', encoding="utf-8"
    )
    meta = mdx_processor.ShardMeta(
        total_entries=0,
        shard_count=1,
        original_size=mdx_path.stat().st_size,
        imported_at="2026-01-24T00:00:00",
    )
    _ = (output_dir / f"_mdict_{dict_id}_meta.json").write_text(
        '{"totalEntries":0}', encoding="utf-8"
    )
    return dict_id, meta


def test_import_dictionary(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    mdx_file = tmp_path / "sample.mdx"
    _ = mdx_file.write_text("dummy", encoding="utf-8")

    monkeypatch.setattr(dict_manager, "process_mdx", fake_process_mdx)

    manager = dict_manager.DictionaryManager(tmp_path)
    dictionary = manager.import_dictionary(mdx_file, ["ja"])

    config_file = tmp_path / "_mdict_config.json"
    assert config_file.exists()
    assert dictionary.id == "testdict"


def test_add_css_scopes(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    mdx_file = tmp_path / "sample.mdx"
    _ = mdx_file.write_text("dummy", encoding="utf-8")
    monkeypatch.setattr(dict_manager, "process_mdx", fake_process_mdx)

    manager = dict_manager.DictionaryManager(tmp_path)
    _ = manager.import_dictionary(mdx_file, ["ja"])

    css_file = tmp_path / "style.css"
    _ = css_file.write_text(".entry { color: red; }", encoding="utf-8")

    manager.add_css("testdict", css_file)
    output_css = tmp_path / "_mdict_testdict_style.css"
    assert output_css.exists()
    assert ".mdict-testdict" in output_css.read_text(encoding="utf-8")


def test_add_mdd_extracts(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    mdx_file = tmp_path / "sample.mdx"
    _ = mdx_file.write_text("dummy", encoding="utf-8")
    monkeypatch.setattr(dict_manager, "process_mdx", fake_process_mdx)
    monkeypatch.setattr(dict_manager, "_load_mdd_class", lambda: DummyMDD)

    manager = dict_manager.DictionaryManager(tmp_path)
    _ = manager.import_dictionary(mdx_file, ["ja"])

    mdd_file = tmp_path / "sample.mdd"
    _ = mdd_file.write_text("dummy", encoding="utf-8")
    manager.add_mdd_resources("testdict", [mdd_file])

    mapping_file = tmp_path / "_mdict_testdict_resources.json"
    assert mapping_file.exists()


def _write_lookup_files(
    base_dir: Path,
    dict_id: str,
    word: str,
    definition: str,
) -> None:
    index_path = base_dir / f"_mdict_{dict_id}_index.json"
    _ = index_path.write_text(
        json.dumps(
            {"entries": {word: {"shardIndex": 0, "position": 0}}},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    shard_path = base_dir / f"_mdict_{dict_id}_shard_0.json"
    _ = shard_path.write_text(
        json.dumps(
            {
                "index": 0,
                "entries": [{"key": word, "definition": definition}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_rename_dictionary_updates_name_only(tmp_path: Path) -> None:
    config = MainConfig(
        dictionaries=[
            Dictionary(
                id="dict_a",
                name="旧名称",
                languages=["ja"],
                order=0,
                meta=DictionaryMeta(total_entries=1),
                file_prefix="_mdict_dict_a",
            )
        ],
        tokenizers={},
    )
    save_config(tmp_path, config)

    manager = dict_manager.DictionaryManager(tmp_path)
    manager.rename_dictionary("dict_a", "新名称")

    updated = load_config(tmp_path)
    assert updated.dictionaries[0].name == "新名称"
    assert updated.dictionaries[0].file_prefix == "_mdict_dict_a"


def test_delete_dictionary_cleans_tokenizers(tmp_path: Path) -> None:
    config = MainConfig(
        dictionaries=[
            Dictionary(
                id="dict_a",
                name="A",
                languages=["ja"],
                order=0,
                meta=DictionaryMeta(total_entries=1),
                file_prefix="_mdict_dict_a",
            ),
            Dictionary(
                id="dict_b",
                name="B",
                languages=["ja"],
                order=1,
                meta=DictionaryMeta(total_entries=1),
                file_prefix="_mdict_dict_b",
            ),
        ],
        tokenizers={
            "ja": TokenizerConfig(language="ja", dictionary_ids=["dict_a", "dict_b"]),
            "en": TokenizerConfig(language="en", dictionary_ids=["dict_a"]),
        },
    )
    save_config(tmp_path, config)

    manager = dict_manager.DictionaryManager(tmp_path)
    manager.delete_dictionary("dict_a")

    updated = load_config(tmp_path)
    assert [item.id for item in updated.dictionaries] == ["dict_b"]
    assert updated.tokenizers["ja"].dictionary_ids == ["dict_b"]
    assert updated.tokenizers["en"].dictionary_ids == []


def test_delete_dictionary_cleans_tokenizers_when_missing(tmp_path: Path) -> None:
    config = MainConfig(
        dictionaries=[],
        tokenizers={
            "ja": TokenizerConfig(language="ja", dictionary_ids=["dict_x"]),
        },
    )
    save_config(tmp_path, config)

    manager = dict_manager.DictionaryManager(tmp_path)
    manager.delete_dictionary("dict_x")

    updated = load_config(tmp_path)
    assert updated.dictionaries == []
    assert updated.tokenizers["ja"].dictionary_ids == []


def test_try_lookup_respects_language_order(tmp_path: Path) -> None:
    _write_lookup_files(tmp_path, "dict_a", "hello", "A")
    _write_lookup_files(tmp_path, "dict_b", "hello", "B")
    config = MainConfig(
        dictionaries=[
            Dictionary(
                id="dict_a",
                name="A",
                languages=["ja"],
                order=1,
                meta=DictionaryMeta(total_entries=1),
                file_prefix="_mdict_dict_a",
            ),
            Dictionary(
                id="dict_b",
                name="B",
                languages=["ja"],
                order=0,
                meta=DictionaryMeta(total_entries=1),
                file_prefix="_mdict_dict_b",
            ),
        ],
        tokenizers={
            "ja": TokenizerConfig(language="ja", dictionary_ids=["dict_a", "dict_b"]),
        },
    )
    save_config(tmp_path, config)

    service = TryLookupService(tmp_path)
    result = service.try_lookup("ja", "hello")

    assert result is not None
    assert result["dictionary_id"] == "dict_a"
    assert result["definition"] == "A"


def test_try_lookup_defaults_to_order(tmp_path: Path) -> None:
    _write_lookup_files(tmp_path, "dict_a", "hello", "A")
    _write_lookup_files(tmp_path, "dict_b", "hello", "B")
    config = MainConfig(
        dictionaries=[
            Dictionary(
                id="dict_a",
                name="A",
                languages=["ja"],
                order=1,
                meta=DictionaryMeta(total_entries=1),
                file_prefix="_mdict_dict_a",
            ),
            Dictionary(
                id="dict_b",
                name="B",
                languages=["ja"],
                order=0,
                meta=DictionaryMeta(total_entries=1),
                file_prefix="_mdict_dict_b",
            ),
        ],
        tokenizers={
            "ja": TokenizerConfig(language="ja", dictionary_ids=[]),
        },
    )
    save_config(tmp_path, config)

    service = TryLookupService(tmp_path)
    result = service.try_lookup("ja", "hello")

    assert result is not None
    assert result["dictionary_id"] == "dict_b"
    assert result["definition"] == "B"

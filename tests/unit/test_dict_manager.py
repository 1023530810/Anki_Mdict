"""辞典管理单元测试"""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mdict_tokenizer import dict_manager, mdx_processor


class DummyMDD:
    """模拟 MDD"""

    def __init__(self, path: str) -> None:
        self.path = path

    def items(self):
        return [(b"audio/a.mp3", b"data")]


def fake_process_mdx(
    mdx_path: Path, output_dir: Path, dict_id=None, shard_size_bytes=0
):
    dict_id = "testdict"
    (output_dir / f"_mdict_{dict_id}_shard_0.json").write_text(
        '{"entries": []}', encoding="utf-8"
    )
    (output_dir / f"_mdict_{dict_id}_index.json").write_text(
        '{"entries": {}}', encoding="utf-8"
    )
    meta = mdx_processor.ShardMeta(
        total_entries=0,
        shard_count=1,
        original_size=mdx_path.stat().st_size,
        imported_at="2026-01-24T00:00:00",
    )
    (output_dir / f"_mdict_{dict_id}_meta.json").write_text(
        '{"totalEntries":0}', encoding="utf-8"
    )
    return dict_id, meta


def test_import_dictionary(tmp_path: Path, monkeypatch) -> None:
    mdx_file = tmp_path / "sample.mdx"
    mdx_file.write_text("dummy", encoding="utf-8")

    monkeypatch.setattr(dict_manager, "process_mdx", fake_process_mdx)

    manager = dict_manager.DictionaryManager(tmp_path)
    dictionary = manager.import_dictionary(mdx_file, ["ja"])

    config_file = tmp_path / "_mdict_config.json"
    assert config_file.exists()
    assert dictionary.id == "testdict"


def test_add_css_scopes(tmp_path: Path, monkeypatch) -> None:
    mdx_file = tmp_path / "sample.mdx"
    mdx_file.write_text("dummy", encoding="utf-8")
    monkeypatch.setattr(dict_manager, "process_mdx", fake_process_mdx)

    manager = dict_manager.DictionaryManager(tmp_path)
    manager.import_dictionary(mdx_file, ["ja"])

    css_file = tmp_path / "style.css"
    css_file.write_text(".entry { color: red; }", encoding="utf-8")

    manager.add_css("testdict", css_file)
    output_css = tmp_path / "_mdict_testdict_style.css"
    assert output_css.exists()
    assert ".mdict-testdict" in output_css.read_text(encoding="utf-8")


def test_add_mdd_extracts(tmp_path: Path, monkeypatch) -> None:
    mdx_file = tmp_path / "sample.mdx"
    mdx_file.write_text("dummy", encoding="utf-8")
    monkeypatch.setattr(dict_manager, "process_mdx", fake_process_mdx)
    monkeypatch.setattr(dict_manager, "_load_mdd_class", lambda: DummyMDD)

    manager = dict_manager.DictionaryManager(tmp_path)
    manager.import_dictionary(mdx_file, ["ja"])

    mdd_file = tmp_path / "sample.mdd"
    mdd_file.write_text("dummy", encoding="utf-8")
    manager.add_mdd_resources("testdict", [mdd_file])

    mapping_file = tmp_path / "_mdict_testdict_resources.json"
    assert mapping_file.exists()

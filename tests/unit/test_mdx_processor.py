"""MDX 解析单元测试"""

from __future__ import annotations

import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mdict_tokenizer import mdx_processor


class DummyMDX:
    """模拟 MDX 解析器"""

    def __init__(self, path: str) -> None:
        self.path = path

    def items(self):
        return [(b"apple", b"def1"), (b"banana", b"def2")]


def install_dummy_mdict_utils() -> None:
    """注入虚拟 mdict_utils"""
    reader_module = types.ModuleType("mdict_utils.reader")
    setattr(reader_module, "MDX", DummyMDX)
    package_module = types.ModuleType("mdict_utils")
    setattr(package_module, "reader", reader_module)
    sys.modules["mdict_utils"] = package_module
    sys.modules["mdict_utils.reader"] = reader_module


def test_process_mdx_generates_files(tmp_path: Path) -> None:
    install_dummy_mdict_utils()
    mdx_file = tmp_path / "sample.mdx"
    mdx_file.write_text("dummy", encoding="utf-8")

    dict_id, meta = mdx_processor.process_mdx(mdx_file, tmp_path, shard_size_bytes=64)

    index_file = tmp_path / f"_mdict_{dict_id}_index.json"
    shard_file = tmp_path / f"_mdict_{dict_id}_shard_0.json"
    meta_file = tmp_path / f"_mdict_{dict_id}_meta.json"

    assert index_file.exists()
    assert shard_file.exists()
    assert meta_file.exists()
    assert meta.total_entries == 2

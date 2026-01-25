"""kuromoji 路径前缀测试"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MEDIA = ROOT / "src" / "mdict_tokenizer" / "media"


def test_kuromoji_supports_flattened_prefix_paths() -> None:
    content = (MEDIA / "_mdict_kuromoji.js").read_text(encoding="utf-8")
    assert "resolveDictPath" in content
    assert "loadArrayBuffer(resolveDictPath(dic_path, filename)" in content

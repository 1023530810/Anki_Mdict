"""媒体文件安装测试"""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

import mdict_tokenizer as addon


class DummyMedia:
    def __init__(self, media_dir: Path) -> None:
        self._media_dir = media_dir

    def dir(self) -> str:
        return str(self._media_dir)


class DummyCol:
    def __init__(self, media_dir: Path) -> None:
        self.media = DummyMedia(media_dir)


class DummyMW:
    def __init__(self, media_dir: Path) -> None:
        self.col = DummyCol(media_dir)


def test_install_media_creates_kuromoji_subdir(tmp_path: Path, monkeypatch) -> None:
    media_src = tmp_path / "addon_media"
    media_src.mkdir()
    source_file = media_src / "_mdict_kuromoji_base.dat.gz"
    source_file.write_bytes(b"dummy")
    normal_file = media_src / "_mdict_ui.js"
    normal_file.write_text("console.log('ok');", encoding="utf-8")

    dest_media = tmp_path / "collection_media"
    dest_media.mkdir()

    monkeypatch.setattr(addon, "MEDIA_DIR", media_src)
    monkeypatch.setattr(addon, "mw", DummyMW(dest_media))

    addon.install_media_files()

    assert (dest_media / "_mdict_ui.js").exists()
    assert (dest_media / "_mdict_kuromoji_base.dat.gz").exists()
    assert not (dest_media / "_mdict_kuromoji_").exists()

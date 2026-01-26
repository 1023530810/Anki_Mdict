"""卡片内嵌配置面板测试"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MEDIA = ROOT / "src" / "mdict_tokenizer" / "media"


def _read_media_file(name: str) -> str:
    path = MEDIA / name
    return path.read_text(encoding="utf-8")


def test_config_panel_labels_present() -> None:
    content = _read_media_file("_mdict_ui.js")
    required_labels = [
        "启用辞典",
        "注音/音标",
        "提取原型",
        "字体大小",
        "分词点击",
        "历史记录数量",
        "弹窗高度",
        "分词样式",
    ]
    for label in required_labels:
        assert label in content


def test_config_panel_handles_required_keys() -> None:
    content = _read_media_file("_mdict_ui.js")
    required_keys = [
        "enabledDictionaries",
        "readingMode",
        "extractLemma",
        "clickBehavior",
        "historyLimit",
        "popupHeight",
        "tokenStyle",
    ]
    for key in required_keys:
        assert key in content


def test_tokenizer_exposes_update_display() -> None:
    content = _read_media_file("_mdict_tokenizer.js")
    assert "updateTokenDisplay" in content
    assert "data-surface" in content


def test_main_init_gates_languages_by_fields_and_dicts() -> None:
    content = _read_media_file("_mdict_main.js")
    assert "getInitLanguages" in content
    assert "dictionaryIds" in content
    assert "mdict-field" in content

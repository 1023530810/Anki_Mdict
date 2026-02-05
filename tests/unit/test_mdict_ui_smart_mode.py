"""Smart Mode 与事件绑定内容断言测试"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MEDIA = ROOT / "src" / "mdict_tokenizer" / "media"


def _read_media_file(name: str) -> str:
    path = MEDIA / name
    return path.read_text(encoding="utf-8")


def test_set_container_strips_hash_prefix() -> None:
    content = _read_media_file("_mdict_ui.js")
    assert re.search(r"setContainer:\s*function\(containerId\)", content)
    match = re.search(
        r"setContainer:\s*function\(containerId\)(.*?)(?=\n    \w+:\s*function|\n  };)",
        content,
        re.DOTALL,
    )
    assert match, "setContainer function body not found"
    body = match.group(1)
    assert "charAt(0)" in body or "indexOf('#')" in body or "substring(1)" in body


def test_detect_container_strips_hash_prefix() -> None:
    content = _read_media_file("_mdict_ui.js")
    assert re.search(r"detectContainer:\s*function\(containerId\)", content)
    match = re.search(
        r"detectContainer:\s*function\(containerId\)(.*?)(?=\n    \w+:\s*function|\n  };)",
        content,
        re.DOTALL,
    )
    assert match, "detectContainer function body not found"
    body = match.group(1)
    assert "charAt(0)" in body or "indexOf('#')" in body or "substring(1)" in body


def test_ensure_panel_checks_container_visibility() -> None:
    content = _read_media_file("_mdict_ui.js")
    assert "offsetHeight" in content
    assert "offsetWidth" in content


def test_ensure_panel_visibility_fallback_message() -> None:
    content = _read_media_file("_mdict_ui.js")
    assert "嵌入式容器不可见" in content
    assert "嵌入式容器不存在" in content


def test_close_button_has_event_binding() -> None:
    content = _read_media_file("_mdict_ui.js")
    assert "bindCloseEvents" in content
    assert re.search(r"closeBtn.*addEventListener", content)


def test_overlay_has_click_binding() -> None:
    content = _read_media_file("_mdict_ui.js")
    assert "bindOverlayEvents" in content
    assert re.search(r"overlayEl.*addEventListener", content)


def test_search_has_event_bindings() -> None:
    content = _read_media_file("_mdict_ui.js")
    assert "bindSearchEvents" in content
    assert re.search(r"searchBtn.*addEventListener", content)
    assert re.search(r"searchInput.*addEventListener", content)


def test_search_enter_key_binding() -> None:
    content = _read_media_file("_mdict_ui.js")
    assert re.search(r"key\s*===\s*'Enter'\s*\|\|\s*key\s*===\s*13", content)


def test_hide_popup_handles_embedded_mode() -> None:
    content = _read_media_file("_mdict_ui.js")
    match = re.search(
        r"function hidePopup\(\)(.*?)(?=\n  function )",
        content,
        re.DOTALL,
    )
    assert match, "hidePopup function body not found"
    body = match.group(1)
    assert "embedded" in body or "panelEl.style.display" in body

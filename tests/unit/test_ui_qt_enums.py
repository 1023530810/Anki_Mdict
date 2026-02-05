"""Qt 枚举兼容性测试"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
UI_ROOT = ROOT / "src" / "mdict_tokenizer" / "ui"


def _read_ui_file(name: str) -> str:
    return (UI_ROOT / name).read_text(encoding="utf-8")


def test_template_inject_uses_check_state_enum() -> None:
    content = _read_ui_file("template_inject_dialog.py")
    assert "CheckState" in content
    assert "setCheckState(0" not in content
    assert "checkState() != 2" not in content


def test_tokenizer_config_uses_check_state_enum() -> None:
    content = _read_ui_file("tokenizer_config_dialog.py")
    assert "CheckState" in content
    assert "checkState() == 2" not in content


def test_message_box_uses_standard_button_enum() -> None:
    dict_manager = _read_ui_file("dict_manager_dialog.py")
    template_inject = _read_ui_file("template_inject_dialog.py")
    assert "StandardButton" in dict_manager
    assert "StandardButton" in template_inject


def test_dict_manager_persists_header_state() -> None:
    content = _read_ui_file("dict_manager_dialog.py")
    assert "QSettings" in content
    assert "mdict_tokenizer/DictManagerDialog/v1/header_state" in content


def test_dict_manager_action_widget_two_rows() -> None:
    content = _read_ui_file("dict_manager_dialog.py")
    assert "QVBoxLayout" in content
    assert "QHBoxLayout" in content
    assert "addLayout(first_row_layout)" in content
    assert "addLayout(second_row_layout)" in content


def test_dict_manager_drag_reorder_rebuild_hook_exists() -> None:
    content = _read_ui_file("dict_manager_dialog.py")
    assert "rowsMoved.connect" in content or "_on_rows_moved" in content

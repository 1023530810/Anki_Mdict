"""模板注入单元测试"""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mdict_tokenizer.template_injector import inject_template_html, wrap_field


def test_wrap_field_handles_text_filter() -> None:
    html = "<div>{{text:正文}}</div>"
    wrapped = wrap_field(html, "正文", "ja")
    assert "mdict-field" in wrapped
    assert 'data-mdict-field="正文"' in wrapped
    assert "{{text:正文}}" in wrapped


def test_wrap_field_handles_filter_spaces() -> None:
    html = "<div>{{text: 正文 }}</div>"
    wrapped = wrap_field(html, "正文", "ja")
    assert "mdict-field" in wrapped
    assert "{{text: 正文 }}" in wrapped


def test_wrap_field_handles_multiple_filters() -> None:
    html = "<div>{{text:hint:正文}}</div>"
    wrapped = wrap_field(html, "正文", "ja")
    assert "mdict-field" in wrapped
    assert "{{text:hint:正文}}" in wrapped


def test_wrap_field_preserves_existing_wrappers() -> None:
    html = (
        "<div>"
        '<span class="mdict-field" data-mdict-field="正文" data-mdict-lang="ja">'
        "{{正文}}</span>{{text:正文}}</div>"
    )
    wrapped = wrap_field(html, "正文", "ja")
    assert wrapped.count('<span class="mdict-field"') == 2


def test_inject_template_tracks_missing_fields() -> None:
    html = "<div>{{text:正文}}</div>"
    fields = [
        {"name": "正文", "language": "ja"},
        {"name": "答案", "language": "ja"},
    ]
    field_stats = {field["name"]: False for field in fields}
    inject_template_html(html, fields, "", field_stats)
    assert field_stats["正文"] is True
    assert field_stats["答案"] is False

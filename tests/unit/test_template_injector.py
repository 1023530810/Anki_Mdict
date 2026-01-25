"""模板注入单元测试"""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mdict_tokenizer.template_injector import wrap_field


def test_wrap_field_handles_text_filter() -> None:
    html = "<div>{{text:正文}}</div>"
    wrapped = wrap_field(html, "正文", "ja")
    assert "mdict-field" in wrapped
    assert 'data-mdict-field="正文"' in wrapped
    assert "{{text:正文}}" in wrapped

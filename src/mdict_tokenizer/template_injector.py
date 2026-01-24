"""模板注入管理"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from .config import TemplateInjection, load_config, save_config

INJECT_BEGIN = "<!-- mdict-tokenizer:begin -->"
INJECT_END = "<!-- mdict-tokenizer:end -->"


def _safe_int(value: object, default: int = 0) -> int:
    """安全转换为整数"""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return default


class TemplateInjector:
    """模板注入服务"""

    def __init__(self, mw: object, media_dir: Path) -> None:
        self.mw: object = mw
        self.media_dir: Path = media_dir

    def inject(self, note_type_id: int, fields: list[dict[str, str]]) -> None:
        """注入模板"""
        model_manager = getattr(getattr(self.mw, "col", None), "models", None)
        model = model_manager.get(note_type_id) if model_manager else None
        if model is None:
            raise RuntimeError("笔记类型不存在")

        script_block = build_script_block(fields)
        for tmpl in model.get("tmpls", []):
            tmpl["qfmt"] = inject_template_html(
                tmpl.get("qfmt", ""), fields, script_block
            )
            tmpl["afmt"] = inject_template_html(
                tmpl.get("afmt", ""), fields, script_block
            )

        if model_manager:
            model_manager.save(model)
        self._record_injection(model, fields)

    def clear(self, note_type_id: int) -> None:
        """清除注入"""
        model_manager = getattr(getattr(self.mw, "col", None), "models", None)
        model = model_manager.get(note_type_id) if model_manager else None
        if model is None:
            raise RuntimeError("笔记类型不存在")

        for tmpl in model.get("tmpls", []):
            tmpl["qfmt"] = remove_injection(tmpl.get("qfmt", ""))
            tmpl["afmt"] = remove_injection(tmpl.get("afmt", ""))

        if model_manager:
            model_manager.save(model)
        config = load_config(self.media_dir)
        config.injections = [
            item for item in config.injections if item.note_type_id != note_type_id
        ]
        save_config(self.media_dir, config)

    def _record_injection(
        self, model: dict[str, object], fields: list[dict[str, str]]
    ) -> None:
        """记录注入配置"""
        config = load_config(self.media_dir)
        note_type_id = _safe_int(model.get("id", 0))
        config.injections = [
            item for item in config.injections if item.note_type_id != note_type_id
        ]
        config.injections.append(
            TemplateInjection(
                note_type_name=str(model.get("name", "")),
                note_type_id=note_type_id,
                fields=fields,
                injected_at=datetime.now(timezone.utc).isoformat(),
            )
        )
        save_config(self.media_dir, config)


def inject_template_html(
    html: str, fields: list[dict[str, str]], script_block: str
) -> str:
    """在模板中插入脚本与字段包裹"""
    updated = html
    for field in fields:
        name = field.get("name")
        language = field.get("language")
        if not name or not language:
            continue
        updated = wrap_field(updated, name, language)

    if INJECT_BEGIN not in updated:
        updated = f"{updated}\n{script_block}"
    return updated


def wrap_field(html: str, field_name: str, language: str) -> str:
    """包裹字段为可分词区域"""
    if f'data-mdict-field="{field_name}"' in html:
        return html

    pattern = re.compile(r"\{\{%s\}\}" % re.escape(field_name))
    replacement = (
        f'<span class="mdict-field" '
        f'data-mdict-field="{field_name}" '
        f'data-mdict-lang="{language}">{{{{{field_name}}}}}</span>'
    )
    return pattern.sub(replacement, html)


def build_script_block(fields: list[dict[str, str]]) -> str:
    """生成脚本注入块"""
    field_payload = json_dumps(fields)
    return (
        f"{INJECT_BEGIN}\n"
        '<script src="_mdict_config.js"></script>\n'
        '<script src="_mdict_tokenizer.js"></script>\n'
        '<script src="_mdict_dictionary.js"></script>\n'
        '<script src="_mdict_ui.js"></script>\n'
        '<script src="_mdict_main.js"></script>\n'
        "<script>\n"
        f"window.MDICT_FIELDS = {field_payload};\n"
        "if (window.MD && typeof window.MD.init === 'function') {\n"
        "  window.MD.init({ autoTokenize: true });\n"
        "}\n"
        "</script>\n"
        f"{INJECT_END}"
    )


def remove_injection(html: str) -> str:
    """移除注入块"""
    without_script = re.sub(
        rf"{re.escape(INJECT_BEGIN)}[\s\S]*?{re.escape(INJECT_END)}",
        "",
        html,
    )
    without_span = re.sub(
        r"<span class=\"mdict-field\"[^>]*>(\{\{[^}]+\}\})</span>",
        r"\1",
        without_script,
    )
    return without_span


def json_dumps(payload: list[dict[str, str]]) -> str:
    """JSON 序列化"""
    import json

    return json.dumps(payload, ensure_ascii=False)

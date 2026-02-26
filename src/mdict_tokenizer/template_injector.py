"""模板注入管理"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from .config import DeckFieldConfig, DeckInjection, load_config, save_config

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

    def inject(
        self,
        note_type_id: int,
        fields: list[dict[str, str]],
        deck_configs: list[dict[str, object]] | None = None,
    ) -> list[str]:
        """注入模板"""
        model_manager = getattr(getattr(self.mw, "col", None), "models", None)
        model = model_manager.get(note_type_id) if model_manager else None
        if model is None:
            raise RuntimeError("笔记类型不存在")

        field_names = [field["name"] for field in fields if field.get("name")]
        deck_configs_payload = deck_configs or []
        script_block = build_script_block(field_names, deck_configs_payload)
        field_stats = {name: False for name in field_names}
        for tmpl in model.get("tmpls", []):
            tmpl["qfmt"] = inject_template_html(
                tmpl.get("qfmt", ""), fields, script_block, field_stats
            )
            tmpl["afmt"] = inject_template_html(
                tmpl.get("afmt", ""), fields, script_block, field_stats
            )

        if model_manager:
            model_manager.save(model)
        self._record_injection(model, deck_configs_payload)
        return [name for name, found in field_stats.items() if not found]

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
        self, model: dict[str, object], deck_configs: list[dict[str, object]]
    ) -> None:
        """记录注入配置"""
        config = load_config(self.media_dir)
        note_type_id = _safe_int(model.get("id", 0))
        config.injections = [
            item for item in config.injections if item.note_type_id != note_type_id
        ]
        normalized_decks: list[DeckFieldConfig] = []
        for deck_config in deck_configs:
            if not isinstance(deck_config, dict):
                continue
            fields_value = deck_config.get("fields")
            fields = fields_value if isinstance(fields_value, list) else []
            normalized_decks.append(
                DeckFieldConfig(
                    deck_name=str(deck_config.get("deckName") or ""),
                    fields=[
                        {
                            "name": str(field.get("name") or ""),
                            "language": str(field.get("language") or ""),
                        }
                        for field in fields
                        if isinstance(field, dict)
                    ],
                )
            )
        config.injections.append(
            DeckInjection(
                note_type_name=str(model.get("name", "")),
                note_type_id=note_type_id,
                deck_configs=normalized_decks,
                injected_at=datetime.now(timezone.utc).isoformat(),
            )
        )
        save_config(self.media_dir, config)


def inject_template_html(
    html: str,
    fields: list[dict[str, str]],
    script_block: str,
    field_stats: dict[str, bool] | None = None,
) -> str:
    """在模板中插入脚本与字段包裹"""
    updated = html
    for field in fields:
        name = field.get("name")
        language = field.get("language")
        if not name or not language:
            continue
        updated, matched = wrap_field_with_report(updated, name, language)
        if field_stats is not None and matched:
            field_stats[name] = True

    if INJECT_BEGIN in updated:
        updated = re.sub(
            rf"{re.escape(INJECT_BEGIN)}[\s\S]*?{re.escape(INJECT_END)}",
            script_block,
            updated,
        )
    else:
        updated = f"{updated}\n{script_block}"
    return updated


def wrap_field(html: str, field_name: str, language: str) -> str:
    """包裹字段为可分词区域"""
    updated, _ = wrap_field_with_report(html, field_name, language)
    return updated


def wrap_field_with_report(
    html: str, field_name: str, language: str
) -> tuple[str, bool]:
    """包裹字段并返回是否命中"""
    if not html:
        return html, False

    protected_html, protected_spans, protected_hit = _protect_mdict_spans(
        html, field_name
    )
    pattern = re.compile(r"\{\{\s*(?:[^}:]+\s*:\s*)*%s\s*\}\}" % re.escape(field_name))
    matched = protected_hit or pattern.search(protected_html) is not None
    if not matched:
        return html, False

    def wrap_match(match: re.Match[str]) -> str:
        return (
            f'<span class="mdict-field" '
            f'data-mdict-field="{field_name}" '
            f'data-mdict-lang="{language}">{match.group(0)}</span>'
        )

    updated = pattern.sub(wrap_match, protected_html)
    return _restore_mdict_spans(updated, protected_spans), True


def _protect_mdict_spans(html: str, field_name: str) -> tuple[str, list[str], bool]:
    """避免重复包裹已注入的字段"""
    placeholders: list[str] = []
    found = False

    def replace_span(match: re.Match[str]) -> str:
        nonlocal found
        segment = match.group(0)
        if (
            f'data-mdict-field="{field_name}"' in segment
            or f"data-mdict-field='{field_name}'" in segment
        ):
            found = True
        placeholders.append(segment)
        return f"__MDICT_SPAN_{len(placeholders) - 1}__"

    protected_html = re.sub(
        r'<span class="mdict-field"[^>]*>.*?</span>',
        replace_span,
        html,
        flags=re.DOTALL,
    )
    return protected_html, placeholders, found


def _restore_mdict_spans(html: str, placeholders: list[str]) -> str:
    """恢复已保护的 mdict 容器"""
    restored = html
    for index, segment in enumerate(placeholders):
        restored = restored.replace(f"__MDICT_SPAN_{index}__", segment)
    return restored


def build_script_block(
    field_names: list[str],
    deck_configs: list[dict[str, object]],
) -> str:
    """生成脚本注入块"""
    field_payload = json_dumps(field_names)
    deck_payload = json_dumps(deck_configs)
    return (
        f"{INJECT_BEGIN}\n"
        '<div id="mdict-deck-name" style="display:none;">{{Deck}}</div>\n'
        '<link rel="stylesheet" href="_mdict_style.css">\n'
        '<script src="_mdict_config.js"></script>\n'
        '<script src="_mdict_tokenizer.js"></script>\n'
        '<script src="_mdict_fuse.js"></script>\n'
        '<script src="_mdict_dictionary.js"></script>\n'
        '<script src="_mdict_ui.js"></script>\n'
        '<script src="_mdict_main.js"></script>\n'
        "<script>\n"
        f"window.MDICT_FIELDS = {field_payload};\n"
        f"window.MDICT_DECK_INJECTIONS = {deck_payload};\n"
        "(function() {\n"
        "  var _mdictAttempts = 0;\n"
        "  function _mdictTryInit() {\n"
        "    if (window.MD && typeof window.MD.init === 'function') {\n"
        "      if (!window.MD._persistent || !window.MD._persistent.initPromise) {\n"
        "        window.MD.init({ autoTokenize: true });\n"
        "      }\n"
        "    } else if (_mdictAttempts < 50) {\n"
        "      _mdictAttempts++;\n"
        "      setTimeout(_mdictTryInit, 100);\n"
        "    }\n"
        "  }\n"
        "  _mdictTryInit();\n"
        "})();\n"
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


def json_dumps(payload: object) -> str:
    """JSON 序列化"""
    import json

    return json.dumps(payload, ensure_ascii=False)

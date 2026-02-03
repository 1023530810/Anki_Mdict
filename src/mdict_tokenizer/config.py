"""配置管理"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_VERSION = "1.0.0"
CONFIG_FILENAME = "_mdict_config.json"


def _safe_int(value: object, default: int = 0) -> int:
    """安全转换为整数"""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return default


@dataclass
class DictionaryMeta:
    """辞典元数据"""

    total_entries: int = 0
    shard_count: int = 0
    index_shard_count: int = 0
    original_size: int = 0
    imported_at: str = ""


@dataclass
class DictionaryResources:
    """辞典关联资源"""

    has_mdd: bool = False
    resource_count: int = 0
    css_file: str | None = None


@dataclass
class Dictionary:
    """辞典配置"""

    id: str
    name: str
    languages: list[str]
    order: int
    meta: DictionaryMeta = field(default_factory=DictionaryMeta)
    resources: DictionaryResources = field(default_factory=DictionaryResources)
    file_prefix: str = ""


@dataclass
class TokenizerConfig:
    """分词器配置"""

    language: str
    extract_lemma: bool = True
    show_reading: bool = False
    show_ipa: bool = False
    dictionary_ids: list[str] = field(default_factory=list)


@dataclass
class TemplateInjection:
    """模板注入配置"""

    note_type_name: str
    note_type_id: int
    fields: list[dict[str, str]]
    injected_at: str


@dataclass
class MainConfig:
    """主配置"""

    version: str = CONFIG_VERSION
    dictionaries: list[Dictionary] = field(default_factory=list)
    tokenizers: dict[str, TokenizerConfig] = field(default_factory=dict)
    injections: list[TemplateInjection] = field(default_factory=list)


def get_media_dir_from_mw(mw: object) -> Path:
    """从 Anki 主窗口获取媒体目录"""
    col = getattr(mw, "col", None)
    media = getattr(col, "media", None)
    media_dir = getattr(media, "dir", None)
    if media_dir is None:
        raise RuntimeError("无法获取媒体目录")
    return Path(media_dir())


def get_config_path(media_dir: Path) -> Path:
    """获取配置文件路径"""
    return media_dir / CONFIG_FILENAME


def default_config() -> MainConfig:
    """生成默认配置"""
    return MainConfig(
        tokenizers={
            "ja": TokenizerConfig(language="ja"),
            "en": TokenizerConfig(language="en", show_reading=False, show_ipa=False),
        }
    )


def ensure_config(media_dir: Path) -> MainConfig:
    """确保配置文件存在"""
    config_path = get_config_path(media_dir)
    if config_path.exists():
        return load_config(media_dir)
    config = default_config()
    save_config(media_dir, config)
    return config


def load_config(media_dir: Path) -> MainConfig:
    """读取配置文件"""
    config_path = get_config_path(media_dir)
    if not config_path.exists():
        return default_config()

    with config_path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return _from_dict(raw)


def save_config(media_dir: Path, config: MainConfig) -> None:
    """保存配置文件"""
    config_path = get_config_path(media_dir)
    payload = _to_dict(config)
    with config_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def _to_dict(config: MainConfig) -> dict[str, object]:
    """序列化配置"""
    return {
        "version": config.version,
        "dictionaries": [
            {
                "id": dictionary.id,
                "name": dictionary.name,
                "languages": dictionary.languages,
                "order": dictionary.order,
                "meta": {
                    "totalEntries": dictionary.meta.total_entries,
                    "shardCount": dictionary.meta.shard_count,
                    "indexShardCount": dictionary.meta.index_shard_count,
                    "originalSize": dictionary.meta.original_size,
                    "importedAt": dictionary.meta.imported_at,
                },
                "resources": {
                    "hasMdd": dictionary.resources.has_mdd,
                    "resourceCount": dictionary.resources.resource_count,
                    "cssFile": dictionary.resources.css_file,
                },
                "filePrefix": dictionary.file_prefix,
            }
            for dictionary in config.dictionaries
        ],
        "tokenizers": {
            key: {
                "language": tokenizer.language,
                "extractLemma": tokenizer.extract_lemma,
                "showReading": tokenizer.show_reading,
                "showIPA": tokenizer.show_ipa,
                "dictionaryIds": tokenizer.dictionary_ids,
            }
            for key, tokenizer in config.tokenizers.items()
        },
        "injections": [
            {
                "noteTypeName": injection.note_type_name,
                "noteTypeId": injection.note_type_id,
                "fields": injection.fields,
                "injectedAt": injection.injected_at,
            }
            for injection in config.injections
        ],
    }


def _from_dict(raw: dict[str, object]) -> MainConfig:
    """反序列化配置"""
    config = default_config()
    version = raw.get("version")
    if isinstance(version, str):
        config.version = version

    dictionaries: list[Dictionary] = []
    raw_dicts = raw.get("dictionaries")
    if isinstance(raw_dicts, list):
        for item in raw_dicts:
            if not isinstance(item, dict):
                continue
            meta_value = item.get("meta")
            meta: dict[str, object] = meta_value if isinstance(meta_value, dict) else {}
            resources_value = item.get("resources")
            resources: dict[str, object] = (
                resources_value if isinstance(resources_value, dict) else {}
            )
            languages_value = item.get("languages")
            languages = languages_value if isinstance(languages_value, list) else []
            dictionaries.append(
                Dictionary(
                    id=str(item.get("id", "")),
                    name=str(item.get("name", "")),
                    languages=[str(lang) for lang in languages],
                    order=_safe_int(item.get("order", 0)),
                    meta=DictionaryMeta(
                        total_entries=_safe_int(meta.get("totalEntries", 0)),
                        shard_count=_safe_int(meta.get("shardCount", 0)),
                        index_shard_count=_safe_int(meta.get("indexShardCount", 0)),
                        original_size=_safe_int(meta.get("originalSize", 0)),
                        imported_at=str(meta.get("importedAt", "")),
                    ),
                    resources=DictionaryResources(
                        has_mdd=bool(resources.get("hasMdd", False)),
                        resource_count=_safe_int(resources.get("resourceCount", 0)),
                        css_file=(
                            str(resources.get("cssFile"))
                            if resources.get("cssFile")
                            else None
                        ),
                    ),
                    file_prefix=str(item.get("filePrefix", "")),
                )
            )
    config.dictionaries = dictionaries

    tokenizers: dict[str, TokenizerConfig] = {}
    raw_tokenizers = raw.get("tokenizers")
    if isinstance(raw_tokenizers, dict):
        for key, item in raw_tokenizers.items():
            if not isinstance(item, dict):
                continue
            dictionary_ids_value = item.get("dictionaryIds")
            dictionary_ids = (
                dictionary_ids_value if isinstance(dictionary_ids_value, list) else []
            )
            tokenizers[str(key)] = TokenizerConfig(
                language=str(item.get("language", key)),
                extract_lemma=bool(item.get("extractLemma", True)),
                show_reading=bool(item.get("showReading", False)),
                show_ipa=bool(item.get("showIPA", False)),
                dictionary_ids=[str(dict_id) for dict_id in dictionary_ids],
            )
    if tokenizers:
        config.tokenizers = tokenizers

    injections: list[TemplateInjection] = []
    raw_injections = raw.get("injections")
    if isinstance(raw_injections, list):
        for item in raw_injections:
            if not isinstance(item, dict):
                continue
            fields_value = item.get("fields")
            fields = fields_value if isinstance(fields_value, list) else []
            injections.append(
                TemplateInjection(
                    note_type_name=str(item.get("noteTypeName", "")),
                    note_type_id=_safe_int(item.get("noteTypeId", 0)),
                    fields=[
                        {
                            "name": str(field.get("name", "")),
                            "language": str(field.get("language", "")),
                        }
                        for field in fields
                        if isinstance(field, dict)
                    ],
                    injected_at=str(item.get("injectedAt", "")),
                )
            )
    config.injections = injections

    return config


def collect_languages(
    dictionaries: list[Dictionary],
    tokenizers: dict[str, TokenizerConfig],
) -> set[str]:
    """收集所有语言（辞典语言 + 分词器语言）"""
    languages: set[str] = set(tokenizers.keys())
    for dictionary in dictionaries:
        languages.update(dictionary.languages)
    return languages


def ensure_tokenizer_dictionary_ids(
    dictionaries: list[Dictionary],
    tokenizers: dict[str, TokenizerConfig],
) -> dict[str, TokenizerConfig]:
    """确保分词器配置包含有效的辞典 ID 列表

    返回修改后的 tokenizers，保留其他字段（extract_lemma、show_reading、show_ipa）。
    对于缺失或空的 dictionary_ids，使用默认值（按 Dictionary.order 排序）。
    """
    languages: set[str] = set(tokenizers.keys())
    for dictionary in dictionaries:
        languages.update(dictionary.languages)

    updated: dict[str, TokenizerConfig] = {}

    for language in languages:
        tokenizer = tokenizers.get(language)
        ordered = sorted(dictionaries, key=lambda item: item.order)
        default_ids = [
            dictionary.id for dictionary in ordered if language in dictionary.languages
        ]

        if tokenizer is None:
            # 创建新的分词器配置
            updated[language] = TokenizerConfig(
                language=language, dictionary_ids=default_ids
            )
        elif not tokenizer.dictionary_ids:
            # 填充空列表，保留其他字段
            updated[language] = TokenizerConfig(
                language=tokenizer.language,
                extract_lemma=tokenizer.extract_lemma,
                show_reading=tokenizer.show_reading,
                show_ipa=tokenizer.show_ipa,
                dictionary_ids=default_ids,
            )
        else:
            # 仅当默认列表非空时验证并过滤现有 dictionary_ids
            # 对于不在 dictionaries 中的语言，保留用户手动设置的值
            if default_ids:
                valid_set = set(default_ids)
                filtered = [
                    dict_id
                    for dict_id in tokenizer.dictionary_ids
                    if dict_id in valid_set
                ]
                updated[language] = TokenizerConfig(
                    language=tokenizer.language,
                    extract_lemma=tokenizer.extract_lemma,
                    show_reading=tokenizer.show_reading,
                    show_ipa=tokenizer.show_ipa,
                    dictionary_ids=filtered,
                )
            else:
                updated[language] = tokenizer

    return updated


def resolve_language_tokenizers(config: MainConfig) -> dict[str, TokenizerConfig]:
    """从主配置解析并补充分词器配置

    对于 dictionaries 中存在但 tokenizers 中缺失的语言，自动创建默认配置。
    返回的 tokenizers 包含所有语言的有效配置。
    """
    return ensure_tokenizer_dictionary_ids(config.dictionaries, config.tokenizers)

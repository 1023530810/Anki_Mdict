# basedpyright: ignore[reportDeprecated]
"""分词语言与辞典逻辑"""

# pyright: reportDeprecated=false
# 禁用类型弃用提示，保持注解一致性

from __future__ import annotations

from .config import Dictionary, TokenizerConfig


def aggregate_language_set(
    dictionaries: list[Dictionary],
    tokenizers: dict[str, TokenizerConfig],
) -> set[str]:
    """汇总语言集合"""
    languages: set[str] = set(tokenizers.keys())
    for dictionary in dictionaries:
        languages.update(dictionary.languages)
    return languages


def _default_dictionary_ids(
    dictionaries: list[Dictionary],
    language: str,
) -> list[str]:
    """生成默认辞典 ID 列表"""
    ordered = sorted(dictionaries, key=lambda item: item.order)
    return [dictionary.id for dictionary in ordered if language in dictionary.languages]


def resolve_tokenizer_dictionary_ids(
    dictionaries: list[Dictionary],
    tokenizers: dict[str, TokenizerConfig],
) -> dict[str, list[str]]:
    """解析每种语言的辞典 ID 列表"""
    resolved: dict[str, list[str]] = {}
    languages = aggregate_language_set(dictionaries, tokenizers)
    for language in languages:
        default_ids = _default_dictionary_ids(dictionaries, language)
        tokenizer = tokenizers.get(language)
        if tokenizer is None or not tokenizer.dictionary_ids:
            resolved[language] = default_ids
            continue
        valid_set = set(default_ids)
        filtered = [
            dict_id for dict_id in tokenizer.dictionary_ids if dict_id in valid_set
        ]
        resolved[language] = filtered
    return resolved

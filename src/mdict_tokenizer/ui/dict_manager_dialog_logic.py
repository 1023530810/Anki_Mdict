"""辞典管理对话框逻辑"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from ..config import Dictionary


def filter_dictionaries_by_language(
    dictionaries: Iterable[Dictionary],
    language: str,
) -> list[Dictionary]:
    """按语言过滤辞典"""
    return [
        dictionary for dictionary in dictionaries if language in dictionary.languages
    ]


def order_dictionaries_for_display(
    dictionaries: Iterable[Dictionary],
    language: str,
    enabled_ids: Sequence[str],
) -> list[Dictionary]:
    """按启用优先与默认顺序排序辞典"""
    filtered = filter_dictionaries_by_language(dictionaries, language)
    dictionary_map = {dictionary.id: dictionary for dictionary in filtered}

    enabled_list = [
        dictionary_map[dict_id] for dict_id in enabled_ids if dict_id in dictionary_map
    ]
    enabled_set = {dictionary.id for dictionary in enabled_list}

    disabled_list = [
        dictionary
        for dictionary in sorted(filtered, key=lambda item: item.order)
        if dictionary.id not in enabled_set
    ]
    return enabled_list + disabled_list


def resolve_enabled_dictionary_ids(rows: Iterable[tuple[str, bool]]) -> list[str]:
    """从行内勾选状态生成启用辞典列表"""
    return [dict_id for dict_id, enabled in rows if enabled]


def build_enabled_dictionary_ids(rows: Iterable[tuple[str, bool]]) -> list[str]:
    """兼容旧命名的启用列表解析"""
    return resolve_enabled_dictionary_ids(rows)

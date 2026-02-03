"""辞典快速查询"""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from .config import Dictionary, MainConfig, load_config


class TryLookupService:
    """按语言顺序尝试查询辞典"""

    media_dir: Path

    def __init__(self, media_dir: Path) -> None:
        self.media_dir = media_dir

    def try_lookup(self, language: str, word: str) -> dict[str, str] | None:
        """按语言顺序尝试查询，返回首个匹配结果"""
        config = load_config(self.media_dir)
        dictionaries = {dictionary.id: dictionary for dictionary in config.dictionaries}
        ordered_ids = self._resolve_dictionary_ids(config, language, dictionaries)
        for dict_id in ordered_ids:
            result = self._lookup_in_dictionary(dict_id, word)
            if result is not None:
                return {
                    "dictionary_id": dict_id,
                    "key": result["key"],
                    "definition": result["definition"],
                }
        return None

    def _resolve_dictionary_ids(
        self,
        config: MainConfig,
        language: str,
        dictionaries: dict[str, Dictionary],
    ) -> list[str]:
        """解析语言对应的辞典 ID 顺序"""
        tokenizer = config.tokenizers.get(language)
        if tokenizer is not None and tokenizer.dictionary_ids:
            return [
                dict_id
                for dict_id in tokenizer.dictionary_ids
                if dict_id in dictionaries
                and language in dictionaries[dict_id].languages
            ]

        ordered = sorted(config.dictionaries, key=lambda item: item.order)
        return [
            dictionary.id for dictionary in ordered if language in dictionary.languages
        ]

    def _lookup_in_dictionary(self, dict_id: str, word: str) -> dict[str, str] | None:
        """从指定辞典查询词条"""
        index_path = self.media_dir / f"_mdict_{dict_id}_index.json"
        if not index_path.exists():
            return None
        index_payload = _read_json(index_path)
        entries = index_payload.get("entries")
        if not isinstance(entries, dict):
            return None
        entry_info = entries.get(word)
        if not isinstance(entry_info, dict):
            return None
        entry_info_typed = cast(dict[str, object], entry_info)
        shard_index = entry_info_typed.get("shardIndex")
        position = entry_info_typed.get("position")
        if not isinstance(shard_index, int) or not isinstance(position, int):
            return None

        shard_path = self.media_dir / f"_mdict_{dict_id}_shard_{shard_index}.json"
        if not shard_path.exists():
            return None
        shard_payload = _read_json(shard_path)
        shard_entries = shard_payload.get("entries")
        if not isinstance(shard_entries, list):
            return None
        shard_entries_typed = cast(list[dict[str, object]], shard_entries)

        if 0 <= position < len(shard_entries_typed):
            entry = shard_entries_typed[position]
            if isinstance(entry, dict) and entry.get("key") == word:
                definition = entry.get("definition")
                if isinstance(definition, str):
                    return {"key": word, "definition": definition}

        for entry in shard_entries_typed:
            if not isinstance(entry, dict):
                continue
            if entry.get("key") != word:
                continue
            definition = entry.get("definition")
            if isinstance(definition, str):
                return {"key": word, "definition": definition}
        return None


def _read_json(path: Path) -> dict[str, object]:
    """读取 JSON 数据"""
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return cast(dict[str, object], payload)

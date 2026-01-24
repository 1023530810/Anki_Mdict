"""MDX 解析与分片生成"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Iterable
from typing import Protocol

Tuple = tuple

DEFAULT_SHARD_SIZE = 5 * 1024 * 1024


@dataclass
class ShardMeta:
    """分片元数据"""

    total_entries: int
    shard_count: int
    original_size: int
    imported_at: str


def check_mdx_dependencies() -> tuple[bool, str]:
    """检查 MDX 解析依赖"""
    try:
        from mdict_utils.reader import MDX  # noqa: F401

        return True, "mdict-utils 可用"
    except Exception as exc:
        return False, f"mdict-utils 不可用: {exc}"


def decode_bytes(data: object) -> str:
    """解码 bytes 为字符串"""
    if isinstance(data, bytes):
        for encoding in ["utf-8", "utf-16", "gbk", "gb18030"]:
            try:
                return data.decode(encoding)
            except (UnicodeDecodeError, AttributeError):
                continue
        return data.decode("utf-8", errors="ignore")
    if isinstance(data, str):
        return data
    return str(data)


def normalize_text(value: object) -> str:
    """规范化文本"""
    if isinstance(value, (bytes, str)):
        return decode_bytes(value)
    return str(value)


class MDXLike(Protocol):
    """MDX 读取接口"""

    def items(self) -> Iterable[tuple[object, object]]: ...

    def keys(self) -> Iterable[object]: ...


def extract_entries(mdx_path: Path) -> list[dict[str, str]]:
    """提取 MDX 词条列表"""
    try:
        from mdict_utils.reader import MDX
    except Exception as exc:
        raise RuntimeError("无法导入 mdict-utils，请先安装依赖") from exc

    mdx: MDXLike = MDX(str(mdx_path))
    entries: list[dict[str, str]] = []
    if hasattr(mdx, "items"):
        for key, value in mdx.items():
            key_str = normalize_text(key)
            definition_str = normalize_text(value)
            entries.append({"key": key_str, "definition": definition_str})
    elif hasattr(mdx, "keys"):
        get_item = getattr(mdx, "__getitem__", None)
        lookup = getattr(mdx, "lookup", None)
        for key in mdx.keys():
            if callable(get_item):
                value = get_item(key)
            elif callable(lookup):
                value = lookup(key)
            else:
                raise RuntimeError("MDX 对象不支持查询")
            key_str = normalize_text(key)
            definition_str = normalize_text(value)
            entries.append({"key": key_str, "definition": definition_str})
    else:
        raise RuntimeError("不支持的 MDX 解析对象")
    return entries


def generate_dict_id(mdx_path: Path) -> str:
    """生成辞典 ID"""
    hasher = hashlib.sha1()
    hasher.update(str(mdx_path.resolve()).encode("utf-8"))
    return hasher.hexdigest()[:12]


def write_json(path: Path, payload: dict[str, object]) -> None:
    """写入 JSON 文件"""
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)


def build_shards(
    entries: list[dict[str, str]],
    output_dir: Path,
    dict_id: str,
    shard_size_bytes: int = DEFAULT_SHARD_SIZE,
) -> ShardMeta:
    """构建数据分片和索引"""
    output_dir.mkdir(parents=True, exist_ok=True)
    shard_index = 0
    current_entries: list[dict[str, str]] = []
    current_size = 0
    index_map: dict[str, dict[str, int]] = {}

    def flush_shard() -> None:
        nonlocal shard_index, current_entries, current_size
        shard_path = output_dir / f"_mdict_{dict_id}_shard_{shard_index}.json"
        write_json(shard_path, {"index": shard_index, "entries": current_entries})
        shard_index += 1
        current_entries = []
        current_size = 0

    for entry in entries:
        encoded = json.dumps(entry, ensure_ascii=False).encode("utf-8")
        entry_size = len(encoded)
        if current_entries and current_size + entry_size > shard_size_bytes:
            flush_shard()

        position = len(current_entries)
        current_entries.append(entry)
        current_size += entry_size
        index_map[entry["key"]] = {"shardIndex": shard_index, "position": position}

    if current_entries:
        flush_shard()

    index_path = output_dir / f"_mdict_{dict_id}_index.json"
    write_json(index_path, {"entries": index_map})

    return ShardMeta(
        total_entries=len(entries),
        shard_count=shard_index,
        original_size=0,
        imported_at=datetime.now(timezone.utc).isoformat(),
    )


def process_mdx(
    mdx_path: Path,
    output_dir: Path,
    dict_id: str | None = None,
    shard_size_bytes: int = DEFAULT_SHARD_SIZE,
) -> tuple[str, ShardMeta]:
    """处理 MDX 并生成分片文件"""
    if not mdx_path.exists():
        raise FileNotFoundError("MDX 文件不存在")
    dict_id = dict_id or generate_dict_id(mdx_path)
    entries = extract_entries(mdx_path)
    meta = build_shards(entries, output_dir, dict_id, shard_size_bytes)
    meta.original_size = mdx_path.stat().st_size
    meta_path = output_dir / f"_mdict_{dict_id}_meta.json"
    write_json(
        meta_path,
        {
            "totalEntries": meta.total_entries,
            "shardCount": meta.shard_count,
            "originalSize": meta.original_size,
            "importedAt": meta.imported_at,
        },
    )
    return dict_id, meta

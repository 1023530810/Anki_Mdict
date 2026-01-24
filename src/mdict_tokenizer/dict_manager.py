"""辞典管理"""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from .config import (
    Dictionary,
    DictionaryMeta,
    DictionaryResources,
    MainConfig,
    load_config,
    save_config,
)
from .mdx_processor import decode_bytes, process_mdx


class DictionaryManager:
    """辞典管理服务"""

    def __init__(self, media_dir: Path) -> None:
        self.media_dir: Path = media_dir

    def import_dictionary(
        self,
        mdx_path: Path,
        languages: list[str],
        mdd_paths: list[Path] | None = None,
        css_path: Path | None = None,
    ) -> Dictionary:
        """导入辞典"""
        config = load_config(self.media_dir)
        dict_id, meta = process_mdx(mdx_path, self.media_dir)
        file_prefix = f"_mdict_{dict_id}"

        if any(item.id == dict_id for item in config.dictionaries):
            raise RuntimeError("辞典已存在")

        copied_mdx = self.media_dir / f"{file_prefix}.mdx"
        copied_mdx.write_bytes(mdx_path.read_bytes())

        dictionary = Dictionary(
            id=dict_id,
            name=mdx_path.stem,
            languages=languages,
            order=len(config.dictionaries),
            meta=DictionaryMeta(
                total_entries=meta.total_entries,
                shard_count=meta.shard_count,
                index_shard_count=1,
                original_size=meta.original_size,
                imported_at=meta.imported_at,
            ),
            resources=DictionaryResources(
                has_mdd=False, resource_count=0, css_file=None
            ),
            file_prefix=file_prefix,
        )

        config.dictionaries.append(dictionary)
        save_config(self.media_dir, config)

        if mdd_paths:
            self.add_mdd_resources(dict_id, mdd_paths)
        if css_path:
            self.add_css(dict_id, css_path)

        return dictionary

    def add_mdd_resources(self, dict_id: str, mdd_paths: list[Path]) -> None:
        """添加 MDD 资源"""
        mapping, total = extract_mdd_resources(dict_id, mdd_paths, self.media_dir)
        resource_file = self.media_dir / f"_mdict_{dict_id}_resources.json"
        resource_file.write_text(
            json_dumps(mapping),
            encoding="utf-8",
        )

        config = load_config(self.media_dir)
        for index, dictionary in enumerate(config.dictionaries):
            if dictionary.id != dict_id:
                continue
            config.dictionaries[index] = replace(
                dictionary,
                resources=DictionaryResources(
                    has_mdd=True,
                    resource_count=total,
                    css_file=dictionary.resources.css_file,
                ),
            )
            break
        save_config(self.media_dir, config)

    def add_css(self, dict_id: str, css_path: Path) -> None:
        """添加 CSS 样式"""
        css_text = css_path.read_text(encoding="utf-8")
        scoped = scope_css(css_text, dict_id)
        output_path = self.media_dir / f"_mdict_{dict_id}_style.css"
        output_path.write_text(scoped, encoding="utf-8")

        config = load_config(self.media_dir)
        for index, dictionary in enumerate(config.dictionaries):
            if dictionary.id != dict_id:
                continue
            config.dictionaries[index] = replace(
                dictionary,
                resources=DictionaryResources(
                    has_mdd=dictionary.resources.has_mdd,
                    resource_count=dictionary.resources.resource_count,
                    css_file=output_path.name,
                ),
            )
            break
        save_config(self.media_dir, config)

    def delete_dictionary(self, dict_id: str) -> None:
        """删除辞典和关联资源"""
        file_prefix = f"_mdict_{dict_id}"
        for path in self.media_dir.glob(f"{file_prefix}*"):
            path.unlink(missing_ok=True)

        config = load_config(self.media_dir)
        config.dictionaries = [d for d in config.dictionaries if d.id != dict_id]
        save_config(self.media_dir, config)

    def delete_mdd(self, dict_id: str) -> None:
        """删除 MDD 资源"""
        for path in self.media_dir.glob(f"_mdict_{dict_id}_res_*"):
            path.unlink(missing_ok=True)
        mapping_file = self.media_dir / f"_mdict_{dict_id}_resources.json"
        mapping_file.unlink(missing_ok=True)

        config = load_config(self.media_dir)
        for index, dictionary in enumerate(config.dictionaries):
            if dictionary.id != dict_id:
                continue
            config.dictionaries[index] = replace(
                dictionary,
                resources=DictionaryResources(
                    has_mdd=False,
                    resource_count=0,
                    css_file=dictionary.resources.css_file,
                ),
            )
            break
        save_config(self.media_dir, config)

    def delete_css(self, dict_id: str) -> None:
        """删除 CSS"""
        css_file = self.media_dir / f"_mdict_{dict_id}_style.css"
        css_file.unlink(missing_ok=True)

        config = load_config(self.media_dir)
        for index, dictionary in enumerate(config.dictionaries):
            if dictionary.id != dict_id:
                continue
            config.dictionaries[index] = replace(
                dictionary,
                resources=DictionaryResources(
                    has_mdd=dictionary.resources.has_mdd,
                    resource_count=dictionary.resources.resource_count,
                    css_file=None,
                ),
            )
            break
        save_config(self.media_dir, config)

    def reorder_dictionaries(self, ordered_ids: list[str]) -> None:
        """调整辞典顺序"""
        config = load_config(self.media_dir)
        order_map = {dict_id: index for index, dict_id in enumerate(ordered_ids)}
        updated = []
        for dictionary in config.dictionaries:
            order = order_map.get(dictionary.id, dictionary.order)
            updated.append(replace(dictionary, order=order))
        config.dictionaries = sorted(updated, key=lambda item: item.order)
        save_config(self.media_dir, config)


def json_dumps(payload: dict[str, object] | dict[str, str]) -> str:
    """JSON 序列化"""
    import json

    return json.dumps(payload, ensure_ascii=False, indent=2)


def scope_css(css_text: str, dict_id: str) -> str:
    """为 CSS 添加作用域"""
    prefix = f".mdict-{dict_id}"
    scoped_rules = []
    for chunk in css_text.split("}"):
        if "{" not in chunk:
            continue
        selector, body = chunk.split("{", 1)
        selector = selector.strip()
        body = body.strip()
        if not selector:
            continue
        if selector.startswith("@"):
            scoped_rules.append(f"{selector} {{{body}}}")
            continue
        selectors = [item.strip() for item in selector.split(",") if item.strip()]
        scoped = ", ".join(f"{prefix} {item}" for item in selectors)
        scoped_rules.append(f"{scoped} {{{body}}}")
    return "\n".join(scoped_rules)


def extract_mdd_resources(
    dict_id: str,
    mdd_paths: list[Path],
    media_dir: Path,
) -> tuple[dict[str, str], int]:
    """提取 MDD 资源"""
    mdd_class = _load_mdd_class()
    if mdd_class is None:
        raise RuntimeError("无法加载 MDD 解析器")

    mapping: dict[str, str] = {}
    total = 0
    for mdd_path in mdd_paths:
        if not mdd_path.exists():
            continue
        mdd = mdd_class(str(mdd_path))
        for key, data in mdd.items():
            key_str = decode_bytes(key)
            if not key_str:
                continue
            extension = Path(key_str).suffix
            hashed = hashlib.md5(key_str.encode("utf-8")).hexdigest()[:8]
            filename = f"_mdict_{dict_id}_res_{hashed}{extension}"
            (media_dir / filename).write_bytes(data)
            mapping[key_str] = filename
            total += 1
    return mapping, total


def _load_mdd_class():
    """加载 MDD 解析器"""
    try:
        mdict_query = importlib.import_module("mdict_query")
        return getattr(mdict_query, "MDD", None)
    except Exception:
        pass

    mdict_query_root = (
        Path(__file__).resolve().parents[3] / "docs" / "mdict-query-master"
    )
    readmdict_path = mdict_query_root / "readmdict.py"
    if not readmdict_path.exists():
        return None

    package_name = "_mdict_query_temp"
    spec = importlib.util.spec_from_file_location(
        f"{package_name}.readmdict", readmdict_path
    )
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return getattr(module, "MDD", None)

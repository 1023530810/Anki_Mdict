"""辞典管理"""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable, Protocol

from .config import (
    Dictionary,
    DictionaryMeta,
    DictionaryResources,
    ensure_tokenizer_dictionary_ids,
    load_config,
    save_config,
)
from .mdx_processor import decode_bytes, process_mdx


class MDDLike(Protocol):
    """MDD 读取接口"""

    def __init__(self, path: str) -> None: ...

    def items(self) -> Iterable[tuple[object, bytes]]: ...


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
        _ = copied_mdx.write_bytes(mdx_path.read_bytes())

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
        config.tokenizers = ensure_tokenizer_dictionary_ids(
            config.dictionaries, config.tokenizers
        )
        save_config(self.media_dir, config)

        if mdd_paths:
            for mdd_path in mdd_paths:
                self.add_mdd(dict_id, mdd_path)
        if css_path:
            self.add_css(dict_id, css_path)

        return dictionary

    def add_mdd_resources(self, dict_id: str, mdd_paths: list[Path]) -> None:
        """批量添加 MDD 资源（兼容旧接口）"""
        for mdd_path in mdd_paths:
            self.add_mdd(dict_id, mdd_path)

    def add_mdd(self, dict_id: str, mdd_path: Path) -> None:
        """添加 MDD 文件（支持多文件）"""
        config = load_config(self.media_dir)
        for index, dictionary in enumerate(config.dictionaries):
            if dictionary.id != dict_id:
                continue
            n = len(dictionary.resources.mdd_source_files)
            # 复制源文件
            source_filename = f"_mdict_{dict_id}_mdd_{n}.mdd"
            dest_path = self.media_dir / source_filename
            _ = dest_path.write_bytes(mdd_path.read_bytes())
            # 更新 mdd_source_files
            new_source_files = list(dictionary.resources.mdd_source_files) + [
                source_filename
            ]
            config.dictionaries[index] = replace(
                dictionary,
                resources=DictionaryResources(
                    has_mdd=True,
                    resource_count=dictionary.resources.resource_count,
                    mdd_source_files=new_source_files,
                    css_file=dictionary.resources.css_file,
                    css_source_files=dictionary.resources.css_source_files,
                    js_files=dictionary.resources.js_files,
                ),
            )
            save_config(self.media_dir, config)
            # 重建所有 MDD 资源
            self._rebuild_mdd_resources(dict_id)
            break

    def _rebuild_mdd_resources(self, dict_id: str) -> None:
        """重新提取所有 MDD 源文件的资源"""
        config = load_config(self.media_dir)
        for index, dictionary in enumerate(config.dictionaries):
            if dictionary.id != dict_id:
                continue
            source_files = dictionary.resources.mdd_source_files
            # 删除旧资源文件
            for path in self.media_dir.glob(f"_mdict_{dict_id}_res_*"):
                path.unlink(missing_ok=True)
            resource_file = self.media_dir / f"_mdict_{dict_id}_resources.json"
            if not source_files:
                # 没有源文件：清除
                resource_file.unlink(missing_ok=True)
                config.dictionaries[index] = replace(
                    dictionary,
                    resources=DictionaryResources(
                        has_mdd=False,
                        resource_count=0,
                        mdd_source_files=[],
                        css_file=dictionary.resources.css_file,
                        css_source_files=dictionary.resources.css_source_files,
                        js_files=dictionary.resources.js_files,
                    ),
                )
                save_config(self.media_dir, config)
                return
            # 从所有 MDD 源文件提取资源
            mdd_paths = [self.media_dir / f for f in source_files]
            mapping, total = extract_mdd_resources(dict_id, mdd_paths, self.media_dir)
            _ = resource_file.write_text(
                json_dumps(mapping),
                encoding="utf-8",
            )
            config.dictionaries[index] = replace(
                dictionary,
                resources=DictionaryResources(
                    has_mdd=True,
                    resource_count=total,
                    mdd_source_files=source_files,
                    css_file=dictionary.resources.css_file,
                    css_source_files=dictionary.resources.css_source_files,
                    js_files=dictionary.resources.js_files,
                ),
            )
            save_config(self.media_dir, config)
            return

    def add_css(self, dict_id: str, css_path: Path) -> None:
        """添加 CSS 样式（支持多文件）"""
        # 检测编码并读取 CSS 内容
        css_text = _read_css_file(css_path)

        config = load_config(self.media_dir)
        for index, dictionary in enumerate(config.dictionaries):
            if dictionary.id != dict_id:
                continue
            n = len(dictionary.resources.css_source_files)
            # 复制源文件
            source_filename = f"_mdict_{dict_id}_css_{n}.css"
            source_path = self.media_dir / source_filename
            _ = source_path.write_text(css_text, encoding="utf-8")
            # 更新 css_source_files
            new_source_files = list(dictionary.resources.css_source_files) + [
                source_filename
            ]
            config.dictionaries[index] = replace(
                dictionary,
                resources=DictionaryResources(
                    has_mdd=dictionary.resources.has_mdd,
                    resource_count=dictionary.resources.resource_count,
                    mdd_source_files=dictionary.resources.mdd_source_files,
                    css_file=dictionary.resources.css_file,
                    css_source_files=new_source_files,
                    js_files=dictionary.resources.js_files,
                ),
            )
            save_config(self.media_dir, config)
            # 合并所有 CSS
            self._rebuild_merged_css(dict_id)
            break

    def _rebuild_merged_css(self, dict_id: str) -> None:
        """重新合并所有 CSS 源文件"""
        config = load_config(self.media_dir)
        for index, dictionary in enumerate(config.dictionaries):
            if dictionary.id != dict_id:
                continue
            source_files = dictionary.resources.css_source_files
            if not source_files:
                # 没有源文件：清除合并输出
                output_path = self.media_dir / f"_mdict_{dict_id}_style.css"
                output_path.unlink(missing_ok=True)
                config.dictionaries[index] = replace(
                    dictionary,
                    resources=DictionaryResources(
                        has_mdd=dictionary.resources.has_mdd,
                        resource_count=dictionary.resources.resource_count,
                        mdd_source_files=dictionary.resources.mdd_source_files,
                        css_file=None,
                        css_source_files=[],
                        js_files=dictionary.resources.js_files,
                    ),
                )
                save_config(self.media_dir, config)
                return
            # 读取并合并所有源文件
            parts: list[str] = []
            for source_filename in source_files:
                source_path = self.media_dir / source_filename
                if source_path.exists():
                    parts.append(_read_css_file(source_path))
            merged = "\n".join(parts)
            scoped = scope_css(merged, dict_id)
            output_path = self.media_dir / f"_mdict_{dict_id}_style.css"
            _ = output_path.write_text(scoped, encoding="utf-8")
            config.dictionaries[index] = replace(
                dictionary,
                resources=DictionaryResources(
                    has_mdd=dictionary.resources.has_mdd,
                    resource_count=dictionary.resources.resource_count,
                    mdd_source_files=dictionary.resources.mdd_source_files,
                    css_file=output_path.name,
                    css_source_files=source_files,
                    js_files=dictionary.resources.js_files,
                ),
            )
            save_config(self.media_dir, config)
            return

    def rename_dictionary(self, dict_id: str, new_name: str) -> None:
        """重命名辞典（仅更新配置名称）"""
        config = load_config(self.media_dir)
        for index, dictionary in enumerate(config.dictionaries):
            if dictionary.id != dict_id:
                continue
            config.dictionaries[index] = replace(dictionary, name=new_name)
            break
        save_config(self.media_dir, config)

    def delete_dictionary(self, dict_id: str) -> None:
        """删除辞典和关联资源"""
        file_prefix = f"_mdict_{dict_id}"
        for path in self.media_dir.glob(f"{file_prefix}*"):
            path.unlink(missing_ok=True)

        config = load_config(self.media_dir)
        config.dictionaries = [d for d in config.dictionaries if d.id != dict_id]
        updated_tokenizers = {}
        for language, tokenizer in config.tokenizers.items():
            filtered_ids = [
                item for item in tokenizer.dictionary_ids if item != dict_id
            ]
            updated_tokenizers[language] = replace(
                tokenizer,
                dictionary_ids=filtered_ids,
            )
        config.tokenizers = updated_tokenizers
        save_config(self.media_dir, config)

    def delete_mdd(self, dict_id: str, mdd_index: int | None = None) -> None:
        """删除 MDD（支持删除单个或全部）"""
        config = load_config(self.media_dir)
        for index, dictionary in enumerate(config.dictionaries):
            if dictionary.id != dict_id:
                continue
            source_files = list(dictionary.resources.mdd_source_files)
            if mdd_index is not None and 0 <= mdd_index < len(source_files):
                # 删除指定索引的 MDD 源文件
                filename = source_files[mdd_index]
                (self.media_dir / filename).unlink(missing_ok=True)
                source_files.pop(mdd_index)
            else:
                # 删除所有 MDD 源文件和资源
                for filename in source_files:
                    (self.media_dir / filename).unlink(missing_ok=True)
                source_files = []
                for path in self.media_dir.glob(f"_mdict_{dict_id}_res_*"):
                    path.unlink(missing_ok=True)
                resource_file = self.media_dir / f"_mdict_{dict_id}_resources.json"
                resource_file.unlink(missing_ok=True)
            config.dictionaries[index] = replace(
                dictionary,
                resources=DictionaryResources(
                    has_mdd=bool(source_files),
                    resource_count=0,
                    mdd_source_files=source_files,
                    css_file=dictionary.resources.css_file,
                    css_source_files=dictionary.resources.css_source_files,
                    js_files=dictionary.resources.js_files,
                ),
            )
            save_config(self.media_dir, config)
            # 如果还有源文件，重新提取资源
            if source_files:
                self._rebuild_mdd_resources(dict_id)
            break

    def delete_css(self, dict_id: str, css_index: int | None = None) -> None:
        """删除 CSS（支持删除单个或全部）"""
        config = load_config(self.media_dir)
        for index, dictionary in enumerate(config.dictionaries):
            if dictionary.id != dict_id:
                continue
            source_files = list(dictionary.resources.css_source_files)
            if css_index is not None and 0 <= css_index < len(source_files):
                # 删除指定索引的 CSS 源文件
                filename = source_files[css_index]
                file_path = self.media_dir / filename
                file_path.unlink(missing_ok=True)
                source_files.pop(css_index)
            else:
                # 删除所有 CSS 源文件和合并输出
                for filename in source_files:
                    (self.media_dir / filename).unlink(missing_ok=True)
                source_files = []
                output_path = self.media_dir / f"_mdict_{dict_id}_style.css"
                output_path.unlink(missing_ok=True)
            config.dictionaries[index] = replace(
                dictionary,
                resources=DictionaryResources(
                    has_mdd=dictionary.resources.has_mdd,
                    resource_count=dictionary.resources.resource_count,
                    mdd_source_files=dictionary.resources.mdd_source_files,
                    css_file=None,
                    css_source_files=source_files,
                    js_files=dictionary.resources.js_files,
                ),
            )
            save_config(self.media_dir, config)
            # 如果还有源文件，重新合并
            if source_files:
                self._rebuild_merged_css(dict_id)
            break

    def add_js(self, dict_id: str, js_path: Path) -> None:
        """添加 JS 文件"""
        config = load_config(self.media_dir)
        for index, dictionary in enumerate(config.dictionaries):
            if dictionary.id != dict_id:
                continue
            n = len(dictionary.resources.js_files)
            js_filename = f"_mdict_{dict_id}_script_{n}.js"
            dest_path = self.media_dir / js_filename
            _ = dest_path.write_bytes(js_path.read_bytes())
            new_js_files = list(dictionary.resources.js_files) + [js_filename]
            config.dictionaries[index] = replace(
                dictionary,
                resources=DictionaryResources(
                    has_mdd=dictionary.resources.has_mdd,
                    resource_count=dictionary.resources.resource_count,
                    mdd_source_files=dictionary.resources.mdd_source_files,
                    css_file=dictionary.resources.css_file,
                    css_source_files=dictionary.resources.css_source_files,
                    js_files=new_js_files,
                ),
            )
            save_config(self.media_dir, config)
            break

    def delete_js(self, dict_id: str, js_index: int | None = None) -> None:
        """删除 JS 文件（支持删除单个或全部）"""
        config = load_config(self.media_dir)
        for index, dictionary in enumerate(config.dictionaries):
            if dictionary.id != dict_id:
                continue
            js_files = list(dictionary.resources.js_files)
            if js_index is not None and 0 <= js_index < len(js_files):
                filename = js_files[js_index]
                (self.media_dir / filename).unlink(missing_ok=True)
                js_files.pop(js_index)
            else:
                for filename in js_files:
                    (self.media_dir / filename).unlink(missing_ok=True)
                js_files = []
            config.dictionaries[index] = replace(
                dictionary,
                resources=DictionaryResources(
                    has_mdd=dictionary.resources.has_mdd,
                    resource_count=dictionary.resources.resource_count,
                    mdd_source_files=dictionary.resources.mdd_source_files,
                    css_file=dictionary.resources.css_file,
                    css_source_files=dictionary.resources.css_source_files,
                    js_files=js_files,
                ),
            )
            save_config(self.media_dir, config)
            break

    def reorder_dictionaries(self, ordered_ids: list[str]) -> None:
        """调整辞典顺序"""
        config = load_config(self.media_dir)
        order_map = {dict_id: index for index, dict_id in enumerate(ordered_ids)}
        updated: list[Dictionary] = []
        for dictionary in config.dictionaries:
            order = order_map.get(dictionary.id, dictionary.order)
            updated.append(replace(dictionary, order=order))
        config.dictionaries = sorted(updated, key=lambda item: item.order)
        save_config(self.media_dir, config)


def _read_css_file(css_path: Path) -> str:
    """读取 CSS 文件，自动检测编码"""
    # 先尝试 utf-8
    try:
        return css_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        pass
    # 尝试 chardet
    try:
        chardet = importlib.import_module("chardet")
        raw = css_path.read_bytes()
        detected = chardet.detect(raw)
        enc = detected.get("encoding") or "gbk"
        return raw.decode(enc, errors="replace")
    except Exception:
        pass
    # 最后回退 gbk
    return css_path.read_text(encoding="gbk", errors="replace")


def json_dumps(payload: dict[str, object] | dict[str, str]) -> str:
    """JSON 序列化"""
    import json

    return json.dumps(payload, ensure_ascii=False, indent=2)


def _scope_selector(selector: str, prefix: str) -> str:
    parts: list[str] = []
    current: list[str] = []
    paren_depth = 0
    bracket_depth = 0
    in_quote = ""
    escaped = False

    for char in selector:
        if in_quote:
            current.append(char)
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == in_quote:
                in_quote = ""
            continue

        if char in ('"', "'"):
            in_quote = char
            current.append(char)
            continue
        if char == "(":
            paren_depth += 1
            current.append(char)
            continue
        if char == ")" and paren_depth > 0:
            paren_depth -= 1
            current.append(char)
            continue
        if char == "[":
            bracket_depth += 1
            current.append(char)
            continue
        if char == "]" and bracket_depth > 0:
            bracket_depth -= 1
            current.append(char)
            continue

        if char == "," and paren_depth == 0 and bracket_depth == 0:
            parts.append("".join(current))
            current = []
            continue

        current.append(char)

    parts.append("".join(current))

    scoped_parts: list[str] = []
    for part in parts:
        trimmed = part.strip()
        if not trimmed:
            continue
        if trimmed == ":root":
            scoped_parts.append(prefix)
            continue
        if trimmed.startswith(":root"):
            scoped_parts.append(prefix + trimmed[len(":root") :])
            continue
        scoped_parts.append(f"{prefix} {trimmed}")

    return ", ".join(scoped_parts)


def scope_css(css_text: str, dict_id: str) -> str:
    """为 CSS 添加作用域"""
    prefix = f".mdict-{dict_id}"
    n = len(css_text)

    def find_matching_brace(start_index: int) -> int:
        depth = 1
        index = start_index + 1
        in_quote = ""
        escaped = False

        while index < n:
            if css_text[index : index + 2] == "/*":
                end = css_text.find("*/", index + 2)
                if end == -1:
                    return n - 1
                index = end + 2
                continue

            char = css_text[index]
            if in_quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == in_quote:
                    in_quote = ""
                index += 1
                continue

            if char in ('"', "'"):
                in_quote = char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return index
            index += 1

        return n - 1

    result: list[str] = []
    i = 0
    while i < n:
        if css_text[i : i + 2] == "/*":
            end = css_text.find("*/", i + 2)
            if end == -1:
                result.append(css_text[i:])
                break
            result.append(css_text[i : end + 2])
            i = end + 2
            continue

        j = i
        in_quote = ""
        escaped = False
        while j < n:
            if css_text[j : j + 2] == "/*" and not in_quote:
                break

            char = css_text[j]
            if in_quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == in_quote:
                    in_quote = ""
                j += 1
                continue

            if char in ('"', "'"):
                in_quote = char
                j += 1
                continue

            if char in ("{", "}", ";"):
                break
            j += 1

        token = css_text[i:j]
        if j >= n:
            result.append(token)
            break

        if css_text[j : j + 2] == "/*":
            result.append(token)
            i = j
            continue

        delimiter = css_text[j]
        if delimiter == ";":
            result.append(token + ";")
            i = j + 1
            continue

        if delimiter == "}":
            result.append(token + "}")
            i = j + 1
            continue

        selector = token.strip()
        block_end = find_matching_brace(j)
        body = css_text[j + 1 : block_end]
        lower_selector = selector.lower()

        is_charset_or_import = lower_selector.startswith(
            "@charset"
        ) or lower_selector.startswith("@import")
        is_font_face = lower_selector.startswith(
            "@font-face"
        ) or lower_selector.startswith("@-webkit-font-face")
        is_keyframes = (
            lower_selector.startswith("@keyframes")
            or lower_selector.startswith("@-webkit-keyframes")
            or lower_selector.startswith("@-moz-keyframes")
            or lower_selector.startswith("@-o-keyframes")
            or lower_selector.startswith("@-ms-keyframes")
        )
        is_container_at_rule = (
            lower_selector.startswith("@media")
            or lower_selector.startswith("@supports")
            or lower_selector.startswith("@document")
            or lower_selector.startswith("@layer")
            or lower_selector.startswith("@container")
            or lower_selector.startswith("@scope")
            or lower_selector.startswith("@starting-style")
        )

        if not selector:
            result.append("{" + body + "}")
        elif is_charset_or_import or is_font_face or is_keyframes:
            result.append(token + "{" + body + "}")
        elif is_container_at_rule:
            result.append(token + "{" + scope_css(body, dict_id) + "}")
        elif selector.startswith("@"):
            result.append(token + "{" + body + "}")
        else:
            scoped_selector = _scope_selector(selector, prefix)
            if scoped_selector:
                result.append(scoped_selector + "{" + body + "}")

        i = block_end + 1

    return "".join(result)


def extract_mdd_resources(
    dict_id: str,
    mdd_paths: list[Path],
    media_dir: Path,
) -> tuple[dict[str, str], int]:
    """提取 MDD 资源"""
    mdd_class: Any = _load_mdd_class()
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
            _ = (media_dir / filename).write_bytes(data)
            mapping[key_str] = filename
            total += 1
    return mapping, total


def _load_mdd_class() -> Any | None:
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

    # 先注册虚假包，供相对导入使用
    import types

    pkg = types.ModuleType(package_name)
    pkg.__path__ = [str(mdict_query_root)]  # type: ignore[assignment]
    pkg.__package__ = package_name
    sys.modules[package_name] = pkg

    # 预加载 ripemd128 依赖
    ripemd128_path = mdict_query_root / "ripemd128.py"
    if ripemd128_path.exists():
        ripemd128_spec = importlib.util.spec_from_file_location(
            f"{package_name}.ripemd128", ripemd128_path
        )
        if ripemd128_spec and ripemd128_spec.loader:
            ripemd128_mod = importlib.util.module_from_spec(ripemd128_spec)
            ripemd128_mod.__package__ = package_name
            sys.modules[f"{package_name}.ripemd128"] = ripemd128_mod
            ripemd128_spec.loader.exec_module(ripemd128_mod)  # type: ignore[union-attr]

    # 预加载 pureSalsa20 依赖
    salsa20_path = mdict_query_root / "pureSalsa20.py"
    if salsa20_path.exists():
        salsa20_spec = importlib.util.spec_from_file_location(
            f"{package_name}.pureSalsa20", salsa20_path
        )
        if salsa20_spec and salsa20_spec.loader:
            salsa20_mod = importlib.util.module_from_spec(salsa20_spec)
            salsa20_mod.__package__ = package_name
            sys.modules[f"{package_name}.pureSalsa20"] = salsa20_mod
            salsa20_spec.loader.exec_module(salsa20_mod)  # type: ignore[union-attr]

    # 加载 readmdict（依赖上面两个模块的相对导入）
    spec = importlib.util.spec_from_file_location(
        f"{package_name}.readmdict", readmdict_path
    )
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    module.__package__ = package_name
    sys.modules[f"{package_name}.readmdict"] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return getattr(module, "MDD", None)

"""多资源管理集成测试"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from mdict_tokenizer.config import (
    DictionaryResources,
    _from_dict,
    _to_dict,
    MainConfig,
)
from mdict_tokenizer.dict_manager import (
    DictionaryManager,
    scope_css,
    _load_mdd_class,
)


# =============================================================================
# scope_css 状态机测试
# =============================================================================


def test_scope_css_basic_selector() -> None:
    """基本选择器作用域化"""
    result = scope_css(".foo { color: red }", "test")
    assert ".mdict-test .foo" in result, f"Got: {result}"


def test_scope_css_multiple_selectors() -> None:
    """逗号分隔的多选择器"""
    result = scope_css(".foo, .bar { color: red }", "test")
    assert ".mdict-test .foo" in result
    assert ".mdict-test .bar" in result


def test_scope_css_media_nesting() -> None:
    """@media 内部规则加前缀"""
    result = scope_css(
        "@media (max-width:768px) { .foo { color:red } .bar { color:blue } }", "test"
    )
    assert "@media" in result
    assert ".mdict-test .foo" in result
    assert ".mdict-test .bar" in result


def test_scope_css_font_face_no_scope() -> None:
    """@font-face 不加前缀"""
    result = scope_css(
        "@font-face { font-family: MyFont; src: url(font.woff2); }", "test"
    )
    assert ".mdict-test" not in result
    assert "@font-face" in result


def test_scope_css_keyframes_no_scope() -> None:
    """@keyframes 内部选择器不加前缀"""
    result = scope_css(
        "@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }",
        "test",
    )
    assert "@keyframes spin" in result
    assert ".mdict-test 0%" not in result
    assert ".mdict-test 100%" not in result


def test_scope_css_charset_import_preserved() -> None:
    """@charset 和 @import 原样保留"""
    result = scope_css(
        '@charset "UTF-8"; @import url("base.css"); .foo { color:red }', "test"
    )
    assert "@charset" in result
    assert "@import" in result
    assert ".mdict-test .foo" in result


def test_scope_css_comment_skip() -> None:
    """CSS 注释跳过"""
    result = scope_css("/* comment { } */ .foo { color:red }", "test")
    assert ".mdict-test .foo" in result


def test_scope_css_root_replace() -> None:
    """:root 替换为 .mdict-{dict_id}"""
    result = scope_css(":root { --color: red; }", "test")
    assert ".mdict-test" in result
    assert ":root" not in result or result.count(":root") == 0


def test_scope_css_real_oald() -> None:
    """真实 OALD CSS 不崩溃"""
    oald_css_path = (
        Path(__file__).parent.parent.parent.parent
        / "docs"
        / "英语自用单词书"
        / "牛津"
        / "oald.css"
    )
    if not oald_css_path.exists():
        return  # 如果文件不存在，跳过测试
    content = oald_css_path.read_text(encoding="utf-8", errors="replace")
    result = scope_css(content, "oald")
    assert result, "Output is empty"
    assert ".mdict-oald" in result


# =============================================================================
# 多 CSS 合并测试
# =============================================================================


def test_add_two_css_files_merged(tmp_path: Path) -> None:
    """添加两个 CSS 文件并合并"""
    _create_mock_config(tmp_path, "testdict")
    mgr = DictionaryManager(tmp_path)

    css1 = tmp_path / "a.css"
    css1.write_text(".foo { color: red }", encoding="utf-8")
    css2 = tmp_path / "b.css"
    css2.write_text(".bar { color: blue }", encoding="utf-8")

    mgr.add_css("testdict", css1)
    mgr.add_css("testdict", css2)

    from mdict_tokenizer.config import load_config

    cfg = load_config(tmp_path)
    d = cfg.dictionaries[0]
    assert len(d.resources.css_source_files) == 2
    assert d.resources.css_file == "_mdict_testdict_style.css"

    merged = (tmp_path / "_mdict_testdict_style.css").read_text(encoding="utf-8")
    assert ".mdict-testdict .foo" in merged
    assert ".mdict-testdict .bar" in merged


def test_delete_single_css_remerge(tmp_path: Path) -> None:
    """删除单个 CSS 后重新合并"""
    _create_mock_config(tmp_path, "testdict")
    mgr = DictionaryManager(tmp_path)

    css1 = tmp_path / "a.css"
    css1.write_text(".foo { color: red }", encoding="utf-8")
    css2 = tmp_path / "b.css"
    css2.write_text(".bar { color: blue }", encoding="utf-8")

    mgr.add_css("testdict", css1)
    mgr.add_css("testdict", css2)

    mgr.delete_css("testdict", css_index=0)

    from mdict_tokenizer.config import load_config

    cfg = load_config(tmp_path)
    d = cfg.dictionaries[0]
    assert len(d.resources.css_source_files) == 1
    merged = (tmp_path / "_mdict_testdict_style.css").read_text(encoding="utf-8")
    assert ".mdict-testdict .foo" not in merged
    assert ".mdict-testdict .bar" in merged


def test_delete_all_css(tmp_path: Path) -> None:
    """删除全部 CSS"""
    _create_mock_config(tmp_path, "testdict")
    mgr = DictionaryManager(tmp_path)

    css1 = tmp_path / "a.css"
    css1.write_text(".foo { color: red }", encoding="utf-8")
    mgr.add_css("testdict", css1)

    mgr.delete_css("testdict")  # 删除全部

    from mdict_tokenizer.config import load_config

    cfg = load_config(tmp_path)
    d = cfg.dictionaries[0]
    assert d.resources.css_source_files == []
    assert d.resources.css_file is None
    assert not (tmp_path / "_mdict_testdict_style.css").exists()


# =============================================================================
# JS 文件管理测试
# =============================================================================


def test_add_js_file(tmp_path: Path) -> None:
    """添加 JS 文件"""
    _create_mock_config(tmp_path, "testdict")
    mgr = DictionaryManager(tmp_path)

    js1 = tmp_path / "test.js"
    js1.write_text("var x = 1;", encoding="utf-8")

    mgr.add_js("testdict", js1)

    from mdict_tokenizer.config import load_config

    cfg = load_config(tmp_path)
    d = cfg.dictionaries[0]
    assert len(d.resources.js_files) == 1
    assert d.resources.js_files[0] == "_mdict_testdict_script_0.js"
    assert (tmp_path / "_mdict_testdict_script_0.js").exists()


def test_delete_js_file(tmp_path: Path) -> None:
    """删除 JS 文件"""
    _create_mock_config(tmp_path, "testdict")
    mgr = DictionaryManager(tmp_path)

    js1 = tmp_path / "test.js"
    js1.write_text("var x = 1;", encoding="utf-8")
    mgr.add_js("testdict", js1)

    mgr.delete_js("testdict", js_index=0)

    from mdict_tokenizer.config import load_config

    cfg = load_config(tmp_path)
    d = cfg.dictionaries[0]
    assert d.resources.js_files == []
    assert not (tmp_path / "_mdict_testdict_script_0.js").exists()


def test_delete_dictionary_cleans_js(tmp_path: Path) -> None:
    """删除辞典时 JS 文件被清理"""
    _create_mock_config(tmp_path, "testdict")
    mgr = DictionaryManager(tmp_path)

    js1 = tmp_path / "test.js"
    js1.write_text("var x = 1;", encoding="utf-8")
    mgr.add_js("testdict", js1)

    # 删除辞典（glob 会清除所有 _mdict_testdict* 文件）
    mgr.delete_dictionary("testdict")

    assert not (tmp_path / "_mdict_testdict_script_0.js").exists()


# =============================================================================
# 配置向后兼容测试
# =============================================================================


def test_backward_compat_old_format() -> None:
    """旧格式 JSON（只有 cssFile）能正确加载"""
    old_json = {
        "dictionaries": [
            {
                "id": "t",
                "name": "T",
                "languages": ["en"],
                "order": 0,
                "resources": {
                    "hasMdd": False,
                    "resourceCount": 0,
                    "cssFile": "old.css",
                },
            }
        ],
    }
    cfg = _from_dict(old_json)
    d = cfg.dictionaries[0]
    assert d.resources.css_file == "old.css"
    assert d.resources.css_source_files == []
    assert d.resources.js_files == []


def test_new_format_round_trip() -> None:
    """新格式 JSON（含 cssSourceFiles + jsFiles）能正确序列化/反序列化"""
    original = DictionaryResources(
        has_mdd=False,
        resource_count=0,
        css_file="_mdict_x_style.css",
        css_source_files=["_mdict_x_css_0.css", "_mdict_x_css_1.css"],
        js_files=["_mdict_x_script_0.js"],
    )
    from mdict_tokenizer.config import Dictionary, DictionaryMeta, MainConfig

    cfg = MainConfig(
        dictionaries=[
            Dictionary(
                id="x",
                name="X",
                languages=["en"],
                order=0,
                meta=DictionaryMeta(),
                resources=original,
                file_prefix="_mdict_x",
            )
        ]
    )
    raw = _to_dict(cfg)
    resources_raw = raw["dictionaries"][0]["resources"]
    assert resources_raw["cssSourceFiles"] == [
        "_mdict_x_css_0.css",
        "_mdict_x_css_1.css",
    ]
    assert resources_raw["jsFiles"] == ["_mdict_x_script_0.js"]

    cfg2 = _from_dict(raw)
    d2 = cfg2.dictionaries[0]
    assert d2.resources.css_source_files == ["_mdict_x_css_0.css", "_mdict_x_css_1.css"]
    assert d2.resources.js_files == ["_mdict_x_script_0.js"]


def test_default_values_no_break_existing_construction() -> None:
    """新字段有默认值，不破坏现有显式构造"""
    r = DictionaryResources(has_mdd=False, resource_count=0, css_file=None)
    assert r.css_source_files == []
    assert r.js_files == []


# =============================================================================
# MDD fallback 加载测试
# =============================================================================


def test_mdd_class_loads() -> None:
    """_load_mdd_class 返回非 None"""
    cls = _load_mdd_class()
    assert cls is not None, "MDD class should not be None"


def test_mdd_namespace_isolated() -> None:
    """MDD 加载不会注册到 ripemd128/pureSalsa20 全局命名空间"""
    import sys

    _load_mdd_class()
    # 不应该有没有前缀的模块
    assert "ripemd128" not in sys.modules, (
        "ripemd128 should not be in global sys.modules"
    )
    assert "pureSalsa20" not in sys.modules, (
        "pureSalsa20 should not be in global sys.modules"
    )


# =============================================================================
# 辅助函数
# =============================================================================


def _create_mock_config(media_dir: Path, dict_id: str) -> None:
    """创建测试用的 mock 配置文件"""
    config_data = {
        "version": "1.0.0",
        "dictionaries": [
            {
                "id": dict_id,
                "name": "Test",
                "languages": ["en"],
                "order": 0,
                "meta": {
                    "totalEntries": 0,
                    "shardCount": 0,
                    "indexShardCount": 0,
                    "originalSize": 0,
                    "importedAt": "",
                },
                "resources": {
                    "hasMdd": False,
                    "resourceCount": 0,
                    "cssFile": None,
                    "cssSourceFiles": [],
                    "jsFiles": [],
                },
                "filePrefix": f"_mdict_{dict_id}",
            }
        ],
        "tokenizers": {},
        "injections": [],
    }
    (media_dir / "_mdict_config.json").write_text(
        json.dumps(config_data), encoding="utf-8"
    )

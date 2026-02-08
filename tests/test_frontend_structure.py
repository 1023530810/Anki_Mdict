import re
from pathlib import Path


def test_feature5_language_detection():
    """Feature 5: 语言检测函数存在"""
    ui_js = Path("src/mdict_tokenizer/media/_mdict_ui.js").read_text()
    assert ui_js.count("function detectLanguage") >= 1
    assert ui_js.count("function resolveLookupLanguage") >= 1


def test_feature1_probe_cache():
    """Feature 1: 探测缓存函数存在"""
    ui_js = Path("src/mdict_tokenizer/media/_mdict_ui.js").read_text()
    assert ui_js.count("probeEffectiveDictionaryIds") >= 2
    assert ui_js.count("getProbeCacheKey") >= 2
    assert ui_js.count("dictProbeCache") >= 2


def test_feature2_effective_counter():
    """Feature 2: 有效计数器签名变更"""
    ui_js = Path("src/mdict_tokenizer/media/_mdict_ui.js").read_text()
    assert re.search(r"function updateCounter\s*\([^)]*effectiveIds", ui_js)
    assert ui_js.count("refreshCounterForWord") >= 2


def test_feature3_race_protection():
    """Feature 3: 竞态保护 requestId 存在"""
    ui_js = Path("src/mdict_tokenizer/media/_mdict_ui.js").read_text()
    # 检查具体的 requestId 状态变量
    assert "lookupRequestId" in ui_js
    assert "hotzoneToggleRequestId" in ui_js
    assert "counterRequestId" in ui_js
    assert "probeActiveRequestId" in ui_js
    # 检查 requestId 赋值点
    assert re.search(r"requestId\s*=", ui_js)


def test_feature4_token_selected():
    """Feature 4: Token 选中高亮"""
    ui_js = Path("src/mdict_tokenizer/media/_mdict_ui.js").read_text()
    style_css = Path(
        "Anki_Mdict/src/mdict_tokenizer/media/_mdict_style.css"
    ).read_text()
    assert ui_js.count("md-selected") >= 3  # add, remove, clear
    assert "md-selected" in style_css


def test_feature6_css_autoload():
    """Feature 6: CSS 自动加载函数存在"""
    ui_js = Path("src/mdict_tokenizer/media/_mdict_ui.js").read_text()
    main_js = Path("src/mdict_tokenizer/media/_mdict_main.js").read_text()
    combined = ui_js + main_js
    assert combined.count("loadDictStyles") >= 1
    assert combined.count("loadCss") >= 1
    assert combined.count("cssLoaded") >= 1


def test_feature7_preferred_dict():
    """Feature 7: 首选字典状态变量存在"""
    ui_js = Path("src/mdict_tokenizer/media/_mdict_ui.js").read_text()
    assert ui_js.count("preferredDictId") >= 2
    assert ui_js.count("preferredDictWord") >= 2


def test_es5_compatibility():
    """ES5 兼容性：无 ES6+ 语法"""
    ui_js = Path("src/mdict_tokenizer/media/_mdict_ui.js").read_text()
    # 排除注释中的 const/let
    lines = [line for line in ui_js.split("\n") if not line.strip().startswith("//")]
    code = "\n".join(lines)

    assert "const " not in code, "Found 'const' declaration"
    assert "let " not in code, "Found 'let' declaration"
    assert " => " not in code, "Found arrow function"
    assert "async " not in code, "Found async function"


def test_no_ls_dependencies():
    """无 LS 依赖：无 ls- 前缀"""
    ui_js = Path("src/mdict_tokenizer/media/_mdict_ui.js").read_text()
    # 排除注释
    lines = [line for line in ui_js.split("\n") if not line.strip().startswith("//")]
    code = "\n".join(lines)

    assert "ls-" not in code, "Found 'ls-' prefix reference"

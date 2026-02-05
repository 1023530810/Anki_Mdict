## MDict 前端接口文档（稳定面：`window.MD.API`）

本目录文档描述在 Anki 卡片/模板 WebView 中可依赖的 **稳定接口**：`window.MD.API`。

重要边界：

- **唯一稳定契约**：`window.MD.API`（签名、事件、数据形状以 `api/core.md` 为准）。
- **不稳定/内部实现**：除 `MD.API` 之外的 `MD.*`（例如 `MD.Dictionary`、`MD.emit`、`MD.State`、`MD.Config` 等）均属于内部或兼容层，可能在未来调整。

相关文档：

- **[API 文档索引](api/README.md)**（推荐入口）：完整 API 速查表与使用场景索引
- 稳定契约（必读）：[api/core.md](api/core.md) - 核心 API 方法
- 配置管理：[api/config.md](api/config.md) - 配置 API（读取/修改/监听）
- 数据模型：[api/data-models.md](api/data-models.md) - `Dictionary` 与 `LookupResult`
- 事件系统：[api/events.md](api/events.md) - `md:ready`、`md:error`、`md:lookup`
- UI 工具：[api/ui.md](api/ui.md) - 渲染结果、字典选择器、滚动

---

## 脚本注入顺序（必须了解）

模板注入由 `Anki_Mdict/src/mdict_tokenizer/template_injector.py:187` 生成，当前顺序为：

1. `_mdict_style.css`
2. `_mdict_config.js`
3. `_mdict_tokenizer.js`
4. `_mdict_dictionary.js`
5. `_mdict_ui.js`
6. `_mdict_main.js`（**最后加载**）

随后会执行一段内联脚本：

```html
<script>
  window.MDICT_FIELDS = /* ... */;
  if (window.MD && typeof window.MD.init === 'function') {
    window.MD.init({ autoTokenize: true });
  }
</script>
```

含义：

- `_mdict_main.js` 作为“入口”最后加载，确保依赖已就绪。
- 页面上可能已经自动调用了 `MD.init({ autoTokenize: true })`，你的代码应当以 **幂等方式**使用 `MD.API.init(...)` 或仅等待 `md:ready`。

---

## 配置边界：`_mdict_config.json` vs `localStorage`（`MD.Config`）

- `_mdict_config.json`：
  - 属于“结构性配置”（例如字典列表、语言、资源路径）。
  - 由 `MD.API.init({ configPath })`（或兼容 `MD.init`）加载进 `MD.State.config`。
  - 你不应在模板里直接解析/写入该文件。

- `localStorage`（`MD.Config`）：
  - 属于“用户偏好/运行时选择”（例如启用哪些字典、UI 选择状态等）。
  - 当前实现会用它辅助过滤（例如 `enabledDictionaries`）。
  - **注意：`MD.Config` 不是稳定接口**。文档仅用于说明边界与排错，不建议业务侧直接依赖其字段。

---

## 最小可运行示例：模板里查词 + 渲染

以下示例仅使用原生 JS（无框架），适合直接放入卡片模板的 `<script>` 中。

```html
<div id="mdict-root">
  <input id="mdict-word" placeholder="输入要查的词" />
  <button id="mdict-go">查词</button>
  <div id="mdict-result"></div>
</div>

<script>
  (function () {
    function ensureAPI() {
      return window.MD && window.MD.API;
    }

    function onReady(fn) {
      // `md:ready` 为稳定事件；即使已 ready，多次绑定也安全。
      document.addEventListener('md:ready', function () { fn(); }, { once: true });
    }

    function bootstrap() {
      var api = ensureAPI();
      if (!api) {
        console.warn('[mdict] MD.API not ready yet');
        return;
      }

      var inputEl = document.getElementById('mdict-word');
      var btnEl = document.getElementById('mdict-go');
      var resultEl = document.getElementById('mdict-result');
      var lastRequestId = 0;
      var preferredDictionaryId = null;

      btnEl.addEventListener('click', async function () {
        var word = (inputEl.value || '').trim();
        if (!word) return;

        var requestId = ++lastRequestId;
        var result = await api.lookup(word, {
          requestId: requestId,
          dictionaryId: preferredDictionaryId,
        });

        // last-request-wins：丢弃过期结果
        if (result.requestId !== lastRequestId) return;

        api.ui.renderResult(resultEl, result);
        api.ui.scrollToTop(resultEl);

        // 记住本次命中字典，作为下次优先字典（可选）
        if (result && result.dictionaryId) {
          preferredDictionaryId = result.dictionaryId;
        }
      });
    }

    // 如果你希望显式初始化，可取消注释：
    // (window.MD && window.MD.API && window.MD.API.init) ? window.MD.API.init({ autoTokenize: false }) : null;

    onReady(bootstrap);
  })();
</script>
```

提示：如果你需要监听查词事件（例如外部输入触发、埋点），请看 `api/events.md`。

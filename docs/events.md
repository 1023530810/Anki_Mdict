# 事件（DOM CustomEvent）

本文件列出稳定事件名与 payload 形状，来自 `Anki_Mdict/docs/js-api.md` 的“事件”章节。

重要说明：

- 事件通过 `document.dispatchEvent(new CustomEvent(name, { detail }))` 发送。
- 事件由内部 `MD.emit` 触发；你可以监听事件，但 **不要依赖** `MD.emit` 本身（非稳定面）。

---

## 事件列表

### `md:ready`

- 触发时机：初始化成功后（`MD.API.init(...)` 或兼容 `MD.init(...)` 成功）。
- `event.detail`：`{}`

### `md:error`

- 触发时机：初始化失败或内部错误上报。
- `event.detail`：`{ code: string, message: string }`

### `md:lookup`

- 触发时机：一次查词完成（无论命中与否都可触发，具体以实现为准；调用方以 `result.found` 判断）。
- `event.detail`：`{ word: string, result: LookupResult }`

`LookupResult` 的稳定字段/兼容字段见：`Anki_Mdict/docs/js-api.md`。

---

## 可运行示例：监听 ready/error/lookup

```html
<script>
  (function () {
    function log(prefix, obj) {
      try {
        console.log(prefix, JSON.stringify(obj));
      } catch (e) {
        console.log(prefix, obj);
      }
    }

    document.addEventListener('md:ready', function (e) {
      log('[mdict] ready detail=', e.detail);
    });

    document.addEventListener('md:error', function (e) {
      log('[mdict] error detail=', e.detail);
    });

    document.addEventListener('md:lookup', function (e) {
      var detail = e.detail || {};
      var word = detail.word;
      var result = detail.result || {};
      log('[mdict] lookup word=', word);
      log('[mdict] lookup result=', {
        found: result.found,
        dictionaryId: result.dictionaryId,
        requestId: result.requestId,
      });
    });
  })();
</script>
```

---

## 实战：结合模板输入与“最后一次请求胜出”

如果你的 UI 会频繁触发查词（输入联想/快速切换），建议采用 `requestId` 丢弃过期结果：

```html
<script>
  (function () {
    var lastRequestId = 0;
    var activeWord = '';

    async function lookup(word) {
      var api = window.MD && window.MD.API;
      if (!api) return;
      var requestId = ++lastRequestId;
      activeWord = word;
      var result = await api.lookup(word, { requestId: requestId });
      if (result.requestId !== lastRequestId) return; // 过期
      console.log('[mdict] apply result for', activeWord);
      // 在这里调用 api.ui.renderResult(...)
    }

    document.addEventListener('md:ready', function () {
      lookup('test');
    }, { once: true });
  })();
</script>
```

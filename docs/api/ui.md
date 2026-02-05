# UI 工具与组件约定（`MD.API.ui`）

本文件描述 `MD.API.ui` 提供的稳定 UI 工具函数，以及与 ListenSpeak 风格 DOM 的集成方式。

稳定入口：仅 `window.MD.API`。

参考：`api/core.md` 的"UI 工具"章节。

---

## `MD.API.ui.renderResult(container, result, options?)`

用途：把 `LookupResult` 渲染到指定容器。

要点（稳定行为）：

- 命中时用 `<div class="mdict-${dictionaryId}">` 包裹 `result.contentHtml`。
- 自动修复辞典内容中的 CSS 引用（使用 `Dictionary.resources.cssFile`）。
- **不负责**绑定 `entry://` 等链接点击事件（调用方自行决定）。

可运行示例：

```html
<div id="dict-content" style="max-height: 200px; overflow: auto;"></div>

<script>
  (function () {
    var contentEl = document.getElementById('dict-content');
    document.addEventListener('md:ready', async function () {
      var api = window.MD && window.MD.API;
      if (!api) return;
      var result = await api.lookup('テスト', { requestId: 1 });
      api.ui.renderResult(contentEl, result, {
        emptyHtml: '<div>未找到释义</div>',
        errorHtml: '<div>查询失败</div>',
      });
      api.ui.scrollToTop(contentEl);
    }, { once: true });
  })();
</script>
```

---

## `MD.API.ui.syncDictionarySelect(selectElOrContainer, dictionaryId, dicts, options?)`

用途：同步"当前选中字典"的 UI。

支持两种形态：

1. 原生 `<select>`：设置 `select.value = dictionaryId`
2. 自定义容器：配合 `labelEl` / `menuEl` 更新展示与激活态

### 形态 A：原生 `<select>`

```html
<select id="dict-select"></select>
<div id="dict-content"></div>

<script>
  (function () {
    function renderOptions(selectEl, dicts) {
      selectEl.innerHTML = '';
      for (var i = 0; i < dicts.length; i++) {
        var d = dicts[i];
        var opt = document.createElement('option');
        opt.value = d.id;
        opt.textContent = d.name;
        selectEl.appendChild(opt);
      }
    }

    document.addEventListener('md:ready', function () {
      var api = window.MD && window.MD.API;
      if (!api) return;

      var selectEl = document.getElementById('dict-select');
      var dicts = api.getDictionaries({ enabledOnly: false });
      renderOptions(selectEl, dicts);

      var activeId = (dicts[0] && dicts[0].id) || '';
      api.ui.syncDictionarySelect(selectEl, activeId, dicts);

      selectEl.addEventListener('change', function () {
        activeId = selectEl.value;
      });
    }, { once: true });
  })();
</script>
```

### 形态 B：ListenSpeak 风格的"label + menu"

如果你的模板已有类似结构（示例 ID 仅作为约定）：

- `#ls-dict-selected`：显示当前字典名
- `#ls-dict-menu`：字典菜单项容器，子项携带 `data-dict-id`

```html
<div id="ls-dict">
  <button id="ls-dict-selected">(未选择)</button>
  <div id="ls-dict-menu"></div>
</div>
<div id="ls-dict-content" style="max-height: 240px; overflow: auto;"></div>

<script>
  (function () {
    function renderMenu(menuEl, dicts) {
      menuEl.innerHTML = '';
      for (var i = 0; i < dicts.length; i++) {
        var d = dicts[i];
        var item = document.createElement('div');
        item.textContent = d.name;
        item.setAttribute('data-dict-id', d.id);
        item.style.cursor = 'pointer';
        menuEl.appendChild(item);
      }
    }

    document.addEventListener('md:ready', function () {
      var api = window.MD && window.MD.API;
      if (!api) return;

      var labelEl = document.getElementById('ls-dict-selected');
      var menuEl = document.getElementById('ls-dict-menu');
      var contentEl = document.getElementById('ls-dict-content');
      var dicts = api.getDictionaries({ enabledOnly: true });

      renderMenu(menuEl, dicts);

      var activeId = (dicts[0] && dicts[0].id) || '';
      api.ui.syncDictionarySelect(menuEl, activeId, dicts, {
        labelEl: labelEl,
        menuEl: menuEl,
        activeClass: 'active',
      });

      menuEl.addEventListener('click', async function (ev) {
        var target = ev.target;
        if (!target || !target.getAttribute) return;
        var dictId = target.getAttribute('data-dict-id');
        if (!dictId) return;

        activeId = dictId;
        api.ui.syncDictionarySelect(menuEl, activeId, dicts, {
          labelEl: labelEl,
          menuEl: menuEl,
          activeClass: 'active',
        });

        var result = await api.lookup('テスト', { requestId: 1, dictionaryId: activeId });
        api.ui.renderResult(contentEl, result);
        api.ui.scrollToTop(contentEl);
      });
    }, { once: true });
  })();
</script>
```

---

## `MD.API.ui.scrollToTop(scrollContainer)`

用途：将滚动容器滚动回顶部，常用于更新结果后回到开头。

```js
// 直接可用
MD.API.ui.scrollToTop(document.getElementById('ls-dict-content'));
```

---

## `MD.API.ui.getMode()`

用途：获取当前 UI 模式（嵌入式或弹窗式）。

**返回值**：`string` - `'embedded'` 或 `'modal'`

**说明**：
- `'embedded'`：面板嵌入在指定容器中（通过 `targetContainer` 初始化）
- `'modal'`：面板以弹窗形式显示（未指定容器或容器不存在）

**示例**：

```js
var mode = MD.API.ui.getMode();
if (mode === 'embedded') {
  console.log('面板嵌入在容器中');
} else {
  console.log('面板以弹窗形式显示');
}
```

---

## `MD.API.ui.showPanel()`

用途：显示字典面板。

**说明**：
- 在 `embedded` 模式下：显示容器元素
- 在 `modal` 模式下：显示弹窗

**示例**：

```js
// 显示面板
MD.API.ui.showPanel();
```

---

## `MD.API.ui.hidePanel()`

用途：隐藏字典面板。

**说明**：
- 在 `embedded` 模式下：隐藏容器元素
- 在 `modal` 模式下：关闭弹窗

**示例**：

```js
// 隐藏面板
MD.API.ui.hidePanel();
```

**完整示例（模式检测与面板控制）**：

```html
<button id="toggle-panel">切换面板</button>
<div id="mdict-panel"></div>

<script>
  (function () {
    document.addEventListener('md:ready', function () {
      var api = window.MD && window.MD.API;
      if (!api) return;

      var toggleBtn = document.getElementById('toggle-panel');
      var isVisible = false;

      toggleBtn.addEventListener('click', function () {
        var mode = api.ui.getMode();
        console.log('当前模式:', mode);

        if (isVisible) {
          api.ui.hidePanel();
          toggleBtn.textContent = '显示面板';
        } else {
          api.ui.showPanel();
          toggleBtn.textContent = '隐藏面板';
        }
        isVisible = !isVisible;
      });
    }, { once: true });
  })();
</script>
```

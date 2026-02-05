# MDict JS API 稳定契约（window.MD.API）

> 日期：2026-02-04
> 执行者：Codex

本文件定义并冻结 `window.MD.API` 的稳定契约，用于 `Anki_Mdict` 实现与 `Anki_ListenSpeak` 调用。该契约基于现有实现（`_mdict_main.js` / `_mdict_dictionary.js` / `_mdict_ui.js` / `_mdict_config.js`）整理，强调最小变更与兼容现有 `window.MD` 行为。

## 目标与非目标

**目标**
- 在 `window.MD` 命名空间下新增稳定入口 `window.MD.API`。
- 定义查词与 UI 相关能力的稳定签名、数据形状、事件与并发规则。
- 明确 `Dictionary` 与 `LookupResult` 的字段与错误语义。
- 保留现有 `window.MD.Dictionary.*` 调用能力（兼容层）。

**非目标**
- 不引入新依赖或改变脚本注入顺序。
- 不改写 `MD.Dictionary.lookup` 的核心实现逻辑。
- 不新增收藏/星标等新功能。

---

## 命名空间与版本

```js
window.MD.API
```

### `MD.API.version(): string`
- 返回稳定契约版本号（SemVer）。
- **当前版本**：`"2.0.0"`

---

## 初始化

### `MD.API.init(options): Promise<void>`

**语义**：对齐现有 `window.MD.init`。用于加载 `_mdict_config.json`、初始化 `MD.State` 与分词器。

**参数**（与 `MD.init` 保持一致）：
- `options.configPath?: string`（默认 `_mdict_config.json`）
- `options.autoTokenize?: boolean`（默认 `true`）
- `options.targetContainer?: string | HTMLElement | null`（默认 `null`）

#### `options.targetContainer`

**类型**：`string | HTMLElement | null`  
**可选**：是  
**默认值**：`null`

指定字典面板的容器元素，用于嵌入式模式。可以是：
- 字符串（元素 ID，例如 `'#mdict-panel'` 或 `'mdict-panel'`）
- DOM 元素引用

如果提供且元素存在，面板将在容器内渲染（嵌入式模式）。否则回退到弹窗模式。

**示例**：

```js
// 使用元素 ID
MD.API.init({
  targetContainer: '#mdict-panel'
});

// 使用 DOM 元素
var container = document.getElementById('mdict-panel');
MD.API.init({
  targetContainer: container
});
```

**行为**
- 成功后触发 `md:ready` 事件（见"事件"）。
- 失败时触发 `md:error` 事件并抛出错误。
- 推荐幂等：重复调用不应破坏既有 `MD.State.config`。 

---

## 字典枚举

### `MD.API.getDictionaries(options?): Dictionary[]`

**语义**：返回当前配置中的字典列表（来自 `MD.State.config.dictionaries`），排序与字段遵循配置。

**参数（可选）**
- `options.language?: string`：按语言过滤（与现有语言匹配规则一致）。
- `options.enabledOnly?: boolean`：仅返回启用字典（依据 `MD.Config.enabledDictionaries`）。

**返回值**：`Dictionary[]`，见 `api/data-models.md`。

---

## 查词

### `MD.API.lookup(word, options?): Promise<LookupResult>`

**语义**：按"first-effective"策略查词：
1. 计算候选字典（语言过滤、tokenizer 配置、`enabledDictionaries` 过滤、`order` 排序）。
2. 若 `options.dictionaryId` 存在，优先在该字典查词，再回退到候选列表。
3. 依序查询，返回第一个命中结果；若全部未命中，返回 `found: false`。

**参数**
- `word: string`：查询词。
- `options.dictionaryId?: string | null`：首选字典 ID（优先级最高）。
- `options.language?: string | null`：语言上下文（与 tokenizers 配置一致）。
- `options.requestId?: string | number`：并发标识（用于 last-request-wins）。
- `options.followed?: boolean`：内部用，处理 `@@@LINK=` 跳转（外部不建议使用）。

**返回值**：`LookupResult`，见 `api/data-models.md`。

**错误语义**
- 配置缺失（无 `MD.State.config`）时：返回 `found: false`，`error` 可为空或包含 `{ code: "CONFIG_MISSING" }`。
- 网络错误或 JSON 解析错误：推荐返回 `found: false`，并在 `error` 中包含 `{ code, message }`；不抛异常给 UI 调用方。

---

## UI 工具

### `MD.API.ui.renderResult(container, result, options?)`

**语义**：将查词结果渲染到指定容器，统一处理 CSS 引用修复与结果包裹类名。

**参数**
- `container: HTMLElement`：渲染容器。
- `result: LookupResult`：查词结果。
- `options.prefixHtml?: string`：附加在结果前的 HTML（如读音/音标）。
- `options.emptyHtml?: string`：未命中的占位内容（默认"未找到释义"）。
- `options.errorHtml?: string`：错误占位内容（默认"查询失败"）。

**渲染规则**
- 命中时：`<div class="mdict-${dictionaryId}">` 包裹 `result.contentHtml`。
- 自动修复辞典内容中的 CSS 引用，使用 `Dictionary.resources.cssFile`。
- 不负责绑定 `entry://` 链接事件（由调用方决定）。

### `MD.API.ui.syncDictionarySelect(selectElOrContainer, dictionaryId, dicts, options?)`

**语义**：同步 UI 上当前选中字典（适配原生 `<select>` 或自定义容器）。

**参数**
- `selectElOrContainer: HTMLElement`：`<select>` 或容器元素。
- `dictionaryId: string`：当前选中字典 ID。
- `dicts: Dictionary[]`：字典列表。
- `options.labelEl?: HTMLElement`：自定义 label 容器（如 ListenSpeak 的 `#ls-dict-selected`）。
- `options.menuEl?: HTMLElement`：自定义菜单容器（如 `#ls-dict-menu`）。
- `options.activeClass?: string`：激活样式类名（默认 `"active"`）。

**行为**
- 若 `selectElOrContainer` 为 `<select>`：设置 `value`。
- 若为自定义容器：更新 `labelEl` 文本与 `menuEl` 中 `data-dict-id` 匹配项的激活状态。

### `MD.API.ui.scrollToTop(scrollContainer)`

**语义**：将滚动容器滚动到顶部（例如 ListenSpeak 的 `#ls-dict-content`）。

---

## 事件

**事件通道**：使用 DOM CustomEvent（`document.dispatchEvent` / `addEventListener`）。

**事件名与 payload**
- `md:ready`：`detail = {}`
- `md:error`：`detail = { code: string, message: string }`
- `md:lookup`：`detail = { word: string, result: LookupResult }`

**约定**
- 事件由 `MD.emit` 触发，`MD.API` 可复用该机制。
- 若后续引入 `MD.API.events.on/off`，必须是对 DOM 事件的薄封装，不改变事件名与 payload 形状。

详见：`api/events.md`。

---

## 并发与竞态规则（last-request-wins）

**规则**
- `MD.API.lookup` **不保证**并发调用的返回顺序。
- 调用方应使用 `requestId` 判定"最后一次请求胜出"。

**推荐调用方模式**
```js
const requestId = ++lastRequestId;
const result = await MD.API.lookup(word, { requestId, dictionaryId });
if (result.requestId !== lastRequestId) return; // 丢弃过期结果
MD.API.ui.renderResult(container, result);
MD.API.ui.scrollToTop(container);
```

---

## ListenSpeak 迁移最小调用顺序（摘要）

1. `await MD.API.init({ autoTokenize: false })`
2. `const dicts = MD.API.getDictionaries()`
3. `const result = await MD.API.lookup(word, { dictionaryId, requestId })`
4. `MD.API.ui.renderResult(contentEl, result)`
5. `MD.API.ui.syncDictionarySelect(selectElOrContainer, result.dictionaryId, dicts)`
6. `MD.API.ui.scrollToTop(contentEl)`

> 注意：监听 `md:lookup` 事件时使用 `detail.result` 作为 `LookupResult`。

---

## 兼容层说明

- `window.MD.Dictionary.lookup/getDictionaries` 保持现有行为，供旧调用方使用。
- `MD.API` 作为稳定契约入口；非 `MD.API` 接口视为内部实现细节。

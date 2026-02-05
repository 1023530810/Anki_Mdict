# API 文档索引

> 版本：2.0.0  
> 最后更新：2026-02-06

本目录包含 `window.MD.API` 的完整稳定契约文档。

---

## 📚 文档导航

### 核心文档

| 文档 | 说明 | 适用场景 |
|------|------|----------|
| [**core.md**](core.md) | **核心 API 方法**（必读）| 初始化、查词、字典枚举 |
| [**config.md**](config.md) | **配置 API** | 读取/修改配置、监听变化 |
| [**data-models.md**](data-models.md) | **数据模型** | `Dictionary` 与 `LookupResult` 结构 |
| [**events.md**](events.md) | **事件系统** | `md:ready`、`md:error`、`md:lookup` |
| [**ui.md**](ui.md) | **UI 工具** | 渲染结果、字典选择器、滚动 |

---

## 🚀 快速开始

### 最小查词示例

```html
<div id="mdict-root">
  <input id="mdict-word" placeholder="输入要查的词" />
  <button id="mdict-go">查词</button>
  <div id="mdict-result"></div>
</div>

<script>
  (function () {
    function onReady(fn) {
      document.addEventListener('md:ready', fn, { once: true });
    }

    function bootstrap() {
      if (!window.MD || !window.MD.API) return;
      var api = window.MD.API;
      var inputEl = document.getElementById('mdict-word');
      var btnEl = document.getElementById('mdict-go');
      var resultEl = document.getElementById('mdict-result');
      var lastRequestId = 0;

      btnEl.addEventListener('click', async function () {
        var word = (inputEl.value || '').trim();
        if (!word) return;
        var requestId = ++lastRequestId;
        var result = await api.lookup(word, { requestId: requestId });
        if (result.requestId !== lastRequestId) return;
        api.ui.renderResult(resultEl, result);
        api.ui.scrollToTop(resultEl);
      });
    }

    onReady(bootstrap);
  })();
</script>
```

---

## 📦 嵌入式容器用法

### 在自定义容器中嵌入字典面板

v2.0.0 新增嵌入式模式，允许将字典面板嵌入到页面的指定容器中。

**步骤 1：创建容器元素**

```html
<div id="mdict-panel"></div>
```

**步骤 2：使用 `targetContainer` 初始化**

```js
MD.API.init({
  targetContainer: '#mdict-panel'
});
```

**完整示例**：

```html
<div id="mdict-panel" style="width: 100%; height: 400px; border: 1px solid #ccc;"></div>

<script>
  (function () {
    document.addEventListener('md:ready', function () {
      var api = window.MD && window.MD.API;
      if (!api) return;

      // 检查当前模式
      var mode = api.ui.getMode();
      console.log('字典面板模式:', mode); // 'embedded' 或 'modal'

      // 查词示例
      api.lookup('テスト').then(function (result) {
        console.log('查词结果:', result);
      });
    }, { once: true });

    // 初始化（指定容器）
    if (window.MD && window.MD.API) {
      window.MD.API.init({
        targetContainer: '#mdict-panel'
      });
    }
  })();
</script>
```

---

## 📖 API 方法速查

### 初始化与状态

| 方法 | 说明 | 文档 |
|------|------|------|
| `MD.API.version()` | 获取 API 版本号 | [core.md](core.md#版本) |
| `MD.API.init(options)` | 初始化配置与分词器 | [core.md](core.md#初始化) |

### 字典操作

| 方法 | 说明 | 文档 |
|------|------|------|
| `MD.API.getDictionaries(options?)` | 枚举字典列表 | [core.md](core.md#字典枚举) |
| `MD.API.lookup(word, options?)` | 查词（支持并发控制） | [core.md](core.md#查词) |

### 配置管理

| 方法 | 说明 | 文档 |
|------|------|------|
| `MD.API.config.get(key)` | 获取配置值 | [config.md](config.md#mdapiconfigget) |
| `MD.API.config.set(key, value)` | 设置配置值（含验证） | [config.md](config.md#mdapiconfigset) |
| `MD.API.config.getAll()` | 获取所有配置 | [config.md](config.md#mdapiconfiggetall) |
| `MD.API.config.reset(key?)` | 重置配置到默认值 | [config.md](config.md#mdapiconfigreset) |
| `MD.API.config.apply(key?)` | 应用配置到 UI | [config.md](config.md#mdapiconfigapply) |
| `MD.API.config.getMetadata(key?)` | 获取配置元数据 | [config.md](config.md#mdapiconfiggetmetadata) |
| `MD.API.config.onChange(callback)` | 监听配置变化 | [config.md](config.md#mdapiconfigonchange) |

### UI 工具

| 方法 | 说明 | 文档 |
|------|------|------|
| `MD.API.ui.renderResult(container, result, options?)` | 渲染查词结果 | [ui.md](ui.md#mdapiuirenderresult) |
| `MD.API.ui.syncDictionarySelect(el, dictId, dicts, options?)` | 同步字典选择器 | [ui.md](ui.md#mdapiuisyncdictionaryselect) |
| `MD.API.ui.scrollToTop(container)` | 滚动到顶部 | [ui.md](ui.md#mdapiuiscrolltotop) |
| `MD.API.ui.getMode()` | 获取当前 UI 模式 | [ui.md](ui.md#mdapiuigetmode) |
| `MD.API.ui.showPanel()` | 显示字典面板 | [ui.md](ui.md#mdapiuishowpanel) |
| `MD.API.ui.hidePanel()` | 隐藏字典面板 | [ui.md](ui.md#mdapiuihidepanel) |

---

## 🎯 使用场景索引

### 场景 1：基础查词与渲染
**需求**：输入词条 → 查询 → 显示结果

**涉及 API**：
- `MD.API.lookup(word, options)` - 查词
- `MD.API.ui.renderResult(container, result)` - 渲染

**参考文档**：
- [core.md - 查词](core.md#查词)
- [ui.md - 渲染结果](ui.md#mdapiuirenderresult)

---

### 场景 2：字典切换与优先级
**需求**：用户选择字典 → 优先在该字典查询

**涉及 API**：
- `MD.API.getDictionaries({ language, enabledOnly })` - 获取字典列表
- `MD.API.lookup(word, { dictionaryId })` - 指定字典查询
- `MD.API.ui.syncDictionarySelect(...)` - 同步选择器 UI

**参考文档**：
- [core.md - 字典枚举](core.md#字典枚举)
- [core.md - 查词](core.md#查词)
- [ui.md - 字典选择器](ui.md#mdapiuisyncdictionaryselect)

---

### 场景 3：配置管理
**需求**：读取/修改用户配置（阅读模式、字体大小等）

**涉及 API**：
- `MD.API.config.get(key)` - 读取配置
- `MD.API.config.set(key, value)` - 修改配置
- `MD.API.config.onChange(callback)` - 监听变化
- `MD.API.config.apply(key)` - 应用到 UI

**参考文档**：
- [config.md - 完整配置 API](config.md)

---

### 场景 4：并发查询控制
**需求**：快速输入时丢弃过期请求（last-request-wins）

**涉及 API**：
- `MD.API.lookup(word, { requestId })` - 带请求 ID 查询
- 检查 `result.requestId` 是否匹配

**参考文档**：
- [core.md - 查词](core.md#查词)
- [events.md - 并发控制示例](events.md#实战结合模板输入与最后一次请求胜出)

---

### 场景 5：事件监听与埋点
**需求**：监听初始化完成、查词事件、错误事件

**涉及 API**：
- `document.addEventListener('md:ready', ...)` - 初始化完成
- `document.addEventListener('md:lookup', ...)` - 查词完成
- `document.addEventListener('md:error', ...)` - 错误上报

**参考文档**：
- [events.md - 事件系统](events.md)

---

## 📦 数据模型

### Dictionary（字典对象）

```ts
type Dictionary = {
  id: string;              // 字典唯一标识
  name: string;            // 字典显示名称
  order?: number | null;   // 排序优先级
  language?: string;       // 语言代码（如 ja、en）
  languages?: string[];    // 支持的语言列表
  resources?: {
    cssFile?: string;      // CSS 文件路径
    resourceFile?: string; // 资源文件路径
    hasMdd?: boolean;      // 是否包含 MDD
    resourceCount?: number;// 资源文件数量
  };
}
```

**详细说明**：[data-models.md - Dictionary](data-models.md#dictionary)

---

### LookupResult（查词结果）

```ts
type LookupResult = {
  found: boolean;           // 是否找到结果
  dictionaryId?: string;    // 命中字典 ID
  dictionaryName?: string;  // 命中字典名称
  contentHtml?: string;     // 结果 HTML（稳定字段）
  definition?: string;      // 结果文本（兼容旧实现）
  requestId?: string | number; // 请求 ID
  error?: { code?: string; message?: string } | string; // 错误信息
}
```

**详细说明**：[data-models.md - LookupResult](data-models.md#lookupresult)

---

## 🎪 事件列表

| 事件名 | 触发时机 | `event.detail` | 文档 |
|--------|----------|----------------|------|
| `md:ready` | 初始化成功 | `{}` | [events.md](events.md#mdready) |
| `md:error` | 初始化失败或错误 | `{ code, message }` | [events.md](events.md#mderror) |
| `md:lookup` | 查词完成 | `{ word, result }` | [events.md](events.md#mdlookup) |

**详细说明**：[events.md - 事件系统](events.md)

---

## 🔧 配置项列表

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `readingMode` | select | `lookup` | 阅读模式：`none`/`lookup`/`all` |
| `extractLemma` | boolean | `true` | 是否提取单词原型 |
| `fontSize` | number | `16` | 字体大小（12-32） |
| `clickBehavior` | select | `click` | 点击行为：`click`/`longpress` |
| `historyLimit` | select | `50` | 历史记录数量：`10`/`50`/`100` |
| `popupHeight` | select | `medium` | 弹窗高度：`small`/`medium`/`large`/`full` |
| `tokenStyle` | select | `underline` | 分词样式：`underline`/`background`/`none` |
| `enabledDictionaries` | array | `[]` | 启用的字典 ID 列表 |

**详细说明**：[config.md - 配置项列表](config.md#配置项列表)

---

## ⚠️ 重要边界

### 稳定接口 vs 内部实现

| 命名空间 | 稳定性 | 说明 |
|----------|--------|------|
| `window.MD.API` | ✅ **稳定** | 唯一稳定契约，签名与行为保证向后兼容 |
| `window.MD.Dictionary` | ⚠️ **兼容层** | 保留现有调用能力，但不保证未来不变 |
| `window.MD.Config` | ❌ **内部实现** | 不建议直接使用，请用 `MD.API.config` |
| `window.MD.State` | ❌ **内部实现** | 不建议直接使用 |
| `window.MD.emit` | ❌ **内部实现** | 不建议直接使用 |

**建议**：
- ✅ 仅依赖 `window.MD.API`
- ❌ 不要直接访问 `MD.Config`、`MD.State`、`MD.emit`

---

## 📝 配置边界

### `_mdict_config.json`（结构性配置）
- 属于"结构性配置"（字典列表、语言、资源路径）
- 由 `MD.API.init({ configPath })` 加载
- **不应在模板里直接解析/写入**

### `localStorage`（用户偏好）
- 属于"用户偏好/运行时选择"（启用字典、UI 状态）
- 通过 `MD.API.config` 访问
- **不要直接操作 `localStorage`**

---

## 🔗 相关文档

- [上级文档入口](../README.md) - MDict 前端接口文档总览
- [Anki_Mdict 插件 README](../../README.md) - 插件安装与使用
- [Anki_ListenSpeak README](../../../README.md) - ListenSpeak 项目文档

---

## 📌 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| 2.0.0 | 2026-02-06 | 新增嵌入式模式、`targetContainer` 选项、`getMode()`/`showPanel()`/`hidePanel()` 方法 |
| 1.0.0 | 2026-02-05 | 首次发布稳定契约 |

---

## 🔄 迁移指南：v1.x → v2.0.0

### 破坏性变更

**版本号**：
- v1.x：`MD.API.version()` 返回 `"1.0.0"`
- v2.0.0：`MD.API.version()` 返回 `"2.0.0"`

**UI 架构**：
- v2.0.0 引入双模式架构（嵌入式 + 弹窗）
- 旧的纯弹窗 UI 被新的面板结构替代

### 新增功能

**1. 容器支持（嵌入式模式）**

```js
// v2.0.0: 指定容器实现嵌入式模式
MD.API.init({
  targetContainer: '#mdict-panel'
});
```

**2. 模式检测**

```js
// v2.0.0: 检查当前模式
var mode = MD.API.ui.getMode();  // 'embedded' 或 'modal'
```

**3. 面板可见性控制**

```js
// v2.0.0: 程序化显示/隐藏面板
MD.API.ui.showPanel();
MD.API.ui.hidePanel();
```

### 兼容性

**保留的 API**（无需修改）：
- `MD.API.lookup(word, options)`
- `MD.API.getDictionaries(options)`
- `MD.API.ui.renderResult()`
- `MD.API.ui.syncDictionarySelect()`
- `MD.API.ui.scrollToTop()`
- 事件：`md:ready`、`md:lookup`、`md:error`

**已弃用**（仍可用但不推荐）：
- 直接操作弹窗元素（请使用新的面板结构和 API）

### 升级步骤

**步骤 1：更新版本检测**

```js
// 旧代码
if (MD.API.version() === '1.0.0') { /* ... */ }

// 新代码
if (MD.API.version() === '2.0.0') { /* ... */ }
```

**步骤 2：（可选）启用嵌入式模式**

如果希望使用嵌入式模式：

```html
<!-- 添加容器 -->
<div id="mdict-panel"></div>

<script>
  // 初始化时指定容器
  MD.API.init({
    targetContainer: '#mdict-panel'
  });
</script>
```

**步骤 3：（可选）使用新的面板控制 API**

```js
// 检测模式
var mode = MD.API.ui.getMode();

// 控制面板显示
MD.API.ui.showPanel();
MD.API.ui.hidePanel();
```

### 常见问题

**Q: v1.x 代码是否需要修改？**  
A: 不需要。所有 v1.x API 在 v2.0.0 中保持兼容。

**Q: 如何判断是否在嵌入式模式？**  
A: 使用 `MD.API.ui.getMode()` 检查返回值。

**Q: 可以动态切换模式吗？**  
A: 不可以。模式在初始化时确定，取决于 `targetContainer` 参数和容器是否存在。

---

**维护者**：Anki_Mdict 开发团队  
**反馈**：如有问题或建议，请提交 Issue

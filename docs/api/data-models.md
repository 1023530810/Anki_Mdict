# 数据模型

本文件定义 `window.MD.API` 使用的核心数据模型：`Dictionary` 与 `LookupResult`。

参考：`api/core.md` 的"数据模型"章节。

---

## `Dictionary`

```ts
type Dictionary = {
  id: string;
  name: string;
  order?: number | null;
  language?: string;
  languages?: string[];
  resources?: {
    cssFile?: string;
    resourceFile?: string;
    hasMdd?: boolean;
    resourceCount?: number;
  };
  // 允许附加字段，但不应移除上述字段
}
```

**说明**
- `id/name` 必须存在。
- `resources.cssFile` 用于修复字典 HTML 中 CSS 引用。

### 字段详解

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `id` | `string` | ✅ | 字典唯一标识符 |
| `name` | `string` | ✅ | 字典显示名称 |
| `order` | `number \| null` | ❌ | 字典排序优先级（数字越小优先级越高） |
| `language` | `string` | ❌ | 字典语言代码（如 `ja`、`en`） |
| `languages` | `string[]` | ❌ | 字典支持的语言列表 |
| `resources.cssFile` | `string` | ❌ | CSS 文件路径（用于样式修复） |
| `resources.resourceFile` | `string` | ❌ | 资源文件路径 |
| `resources.hasMdd` | `boolean` | ❌ | 是否包含 MDD 资源 |
| `resources.resourceCount` | `number` | ❌ | 资源文件数量 |

---

## `LookupResult`

```ts
type LookupResult = {
  found: boolean;
  dictionaryId?: string;
  dictionaryName?: string;
  contentHtml?: string; // 稳定字段
  definition?: string;  // 兼容字段（旧实现）
  requestId?: string | number;
  error?: { code?: string; message?: string } | string;
}
```

**说明**
- 命中时必须提供 `dictionaryId` 与 `contentHtml`（或兼容 `definition`）。
- `definition` 仅为兼容旧实现，`MD.API` 应以 `contentHtml` 为主。

### 字段详解

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `found` | `boolean` | ✅ | 是否找到结果 |
| `dictionaryId` | `string` | ❌ | 命中字典的 ID（命中时必需） |
| `dictionaryName` | `string` | ❌ | 命中字典的名称 |
| `contentHtml` | `string` | ❌ | 查词结果的 HTML 内容（稳定字段） |
| `definition` | `string` | ❌ | 查词结果的文本定义（兼容旧实现） |
| `requestId` | `string \| number` | ❌ | 请求 ID（用于并发控制） |
| `error` | `object \| string` | ❌ | 错误信息（`found: false` 时可能存在） |

### 使用示例

**命中情况**：
```js
{
  found: true,
  dictionaryId: "dict_001",
  dictionaryName: "大辞泉",
  contentHtml: "<div>...</div>",
  requestId: 1
}
```

**未命中情况**：
```js
{
  found: false,
  requestId: 1,
  error: { code: "NOT_FOUND", message: "词条不存在" }
}
```

**错误情况**：
```js
{
  found: false,
  requestId: 1,
  error: { code: "CONFIG_MISSING", message: "配置未加载" }
}
```

---

## 错误代码参考

| 代码 | 说明 |
|------|------|
| `CONFIG_MISSING` | 配置文件未加载 |
| `NOT_FOUND` | 词条不存在 |
| `NETWORK_ERROR` | 网络错误 |
| `PARSE_ERROR` | 数据解析错误 |
| `INVALID_DICT` | 字典无效或损坏 |

---

## 与 `MD.API.ui.renderResult()` 的关系

`LookupResult` 作为 `MD.API.ui.renderResult()` 的输入，其 `contentHtml` 字段会被自动包裹并渲染：

```js
// 命中时的渲染结果
<div class="mdict-${result.dictionaryId}">
  ${result.contentHtml}
</div>

// 未命中时使用 emptyHtml
<div>${options.emptyHtml || '未找到释义'}</div>

// 错误时使用 errorHtml
<div>${options.errorHtml || '查询失败'}</div>
```

详见：`api/core.md` 的"UI 工具"章节。

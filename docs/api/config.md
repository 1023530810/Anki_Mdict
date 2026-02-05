# 配置 API（`MD.API.config`）

> 日期：2026-02-05  
> 版本：1.0.0

本文档描述 `MD.API.config` 的稳定契约，用于在卡片模板 WebView 中读取、修改和监听配置变化。

---

## 概述

`MD.API.config` 提供了一套完整的配置管理接口，用于：

- **读取配置**：获取单个或全部配置项
- **修改配置**：设置配置值（含自动验证）
- **重置配置**：恢复默认值
- **应用配置**：将配置应用到 UI
- **获取元数据**：查询配置项的类型、选项、默认值等
- **监听变化**：订阅配置变化事件

所有配置项存储在 `localStorage`（通过 `MD.Config`），属于"用户偏好/运行时选择"。

**重要边界**：
- `MD.API.config` 是稳定接口
- `MD.Config` 是内部实现，不建议直接使用

---

## 配置项列表

当前支持 8 个配置项：

| 配置项 | 类型 | 选项/范围 | 默认值 | 说明 |
|--------|------|-----------|--------|------|
| `readingMode` | select | `none`, `lookup`, `all` | `lookup` | 阅读模式：不分词/仅查词/全部分词 |
| `extractLemma` | boolean | `true`, `false` | `true` | 是否提取单词原型 |
| `fontSize` | number | 12-32（步进 2） | `16` | 字体大小（像素） |
| `clickBehavior` | select | `click`, `longpress` | `click` | 点击行为：单击/长按 |
| `historyLimit` | select | `10`, `50`, `100` | `50` | 历史记录数量限制 |
| `popupHeight` | select | `small`, `medium`, `large`, `full` | `medium` | 弹窗高度 |
| `tokenStyle` | select | `underline`, `background`, `none` | `underline` | 分词样式：下划线/背景色/无 |
| `enabledDictionaries` | array | 字符串数组 | `[]` | 启用的字典 ID 列表 |

---

## 方法签名

### `MD.API.config.get(key: string): any`

获取单个配置值。

**参数**：
- `key: string` - 配置项名称

**返回值**：
- 配置值（类型取决于配置项）

**示例**：
```js
const mode = MD.API.config.get('readingMode');
console.log(mode); // "lookup"

const fontSize = MD.API.config.get('fontSize');
console.log(fontSize); // 16

const enabled = MD.API.config.get('enabledDictionaries');
console.log(enabled); // ["dict_001", "dict_002"]
```

---

### `MD.API.config.set(key: string, value: any): void`

设置单个配置值（含自动验证）。

**参数**：
- `key: string` - 配置项名称
- `value: any` - 配置值

**行为**：
- 验证配置值（类型、范围、选项）
- 保存到 `localStorage`
- 触发所有 `onChange` 回调

**抛出错误**：
- 无效的配置项名称
- 类型不匹配
- 值超出范围
- 选项不在允许列表中

**示例**：
```js
// 设置阅读模式
MD.API.config.set('readingMode', 'all');

// 设置字体大小
MD.API.config.set('fontSize', 18);

// 设置启用字典
MD.API.config.set('enabledDictionaries', ['dict_001', 'dict_002']);

// 错误示例：类型不匹配
try {
  MD.API.config.set('fontSize', '18'); // 应为 number
} catch (error) {
  console.error(error.message); // "Invalid value for fontSize: expected number, got string"
}

// 错误示例：值超出范围
try {
  MD.API.config.set('fontSize', 40); // 超过最大值 32
} catch (error) {
  console.error(error.message); // "Invalid value for fontSize: must be <= 32, got 40"
}

// 错误示例：无效选项
try {
  MD.API.config.set('readingMode', 'invalid');
} catch (error) {
  console.error(error.message); // "Invalid value for readingMode: must be one of [none, lookup, all], got invalid"
}
```

---

### `MD.API.config.getAll(): object`

获取所有配置项。

**返回值**：
- 包含所有配置项的对象

**示例**：
```js
const config = MD.API.config.getAll();
console.log(config);
// {
//   readingMode: "lookup",
//   extractLemma: true,
//   fontSize: 16,
//   clickBehavior: "click",
//   historyLimit: 50,
//   popupHeight: "medium",
//   tokenStyle: "underline",
//   enabledDictionaries: []
// }
```

---

### `MD.API.config.reset(key?: string): void`

重置配置到默认值。

**参数**：
- `key?: string` - 可选，要重置的配置项名称。省略则重置所有配置。

**行为**：
- 恢复默认值
- 保存到 `localStorage`
- 触发所有 `onChange` 回调

**示例**：
```js
// 重置单个配置项
MD.API.config.reset('fontSize');
console.log(MD.API.config.get('fontSize')); // 16（默认值）

// 重置所有配置项
MD.API.config.reset();
const config = MD.API.config.getAll();
console.log(config.readingMode); // "lookup"（默认值）
console.log(config.fontSize); // 16（默认值）
```

---

### `MD.API.config.apply(): void`

应用配置到 UI。

**行为**：
- 调用全局 `window.applyConfig(config)` 函数（如果存在）
- 用于将配置变化同步到 UI 组件

**使用场景**：
- 批量修改配置后，统一应用到 UI
- 配置导入后，刷新 UI 状态

**示例**：
```js
// 批量修改配置
MD.API.config.set('fontSize', 20);
MD.API.config.set('tokenStyle', 'background');

// 应用到 UI
MD.API.config.apply();

// 注意：需要在全局定义 applyConfig 函数
window.applyConfig = function(config) {
  // 更新 UI 组件
  document.body.style.fontSize = config.fontSize + 'px';
  // ...
};
```

---

### `MD.API.config.getSchema(): object`

获取配置元数据（schema）。

**返回值**：
- 包含所有配置项元数据的对象

**Schema 结构**：
```typescript
{
  [key: string]: {
    type: "boolean" | "number" | "select" | "array";
    default: any;
    // 以下字段根据类型可选
    min?: number;        // number 类型
    max?: number;        // number 类型
    step?: number;       // number 类型
    options?: any[];     // select 类型
    itemType?: string;   // array 类型
  }
}
```

**示例**：
```js
const schema = MD.API.config.getSchema();

// 查看 fontSize 的元数据
console.log(schema.fontSize);
// {
//   type: "number",
//   min: 12,
//   max: 32,
//   step: 2,
//   default: 16
// }

// 查看 readingMode 的元数据
console.log(schema.readingMode);
// {
//   type: "select",
//   options: ["none", "lookup", "all"],
//   default: "lookup"
// }

// 动态生成配置 UI
Object.keys(schema).forEach(key => {
  const meta = schema[key];
  if (meta.type === 'select') {
    // 创建下拉框
    const select = document.createElement('select');
    meta.options.forEach(opt => {
      const option = document.createElement('option');
      option.value = opt;
      option.textContent = opt;
      select.appendChild(option);
    });
    select.value = MD.API.config.get(key);
    select.addEventListener('change', () => {
      MD.API.config.set(key, select.value);
    });
  }
});
```

---

### `MD.API.config.onChange(callback: function): void`

订阅配置变化事件。

**参数**：
- `callback: (key: string, value: any) => void` - 回调函数

**回调参数**：
- `key: string` - 变化的配置项名称
- `value: any` - 新的配置值

**行为**：
- 注册回调到内部列表
- 当配置变化时（通过 `set` 或 `reset`），触发所有回调
- 回调中的错误会被捕获并打印到控制台，不会影响其他回调

**注意**：
- 当前版本不支持取消订阅（unsubscribe）
- 回调会在每次配置变化时触发，包括 `reset`

**示例**：
```js
// 基本用法
MD.API.config.onChange((key, value) => {
  console.log(`配置变化: ${key} = ${value}`);
});

MD.API.config.set('fontSize', 20);
// 输出: "配置变化: fontSize = 20"

// 实时同步 UI
MD.API.config.onChange((key, value) => {
  if (key === 'fontSize') {
    document.body.style.fontSize = value + 'px';
  } else if (key === 'tokenStyle') {
    document.body.className = 'token-' + value;
  }
});

// 多个订阅者
MD.API.config.onChange((key, value) => {
  // 订阅者 1：记录日志
  console.log('[Logger]', key, value);
});

MD.API.config.onChange((key, value) => {
  // 订阅者 2：保存到服务器
  fetch('/api/config', {
    method: 'POST',
    body: JSON.stringify({ [key]: value })
  });
});

// 错误处理
MD.API.config.onChange((key, value) => {
  throw new Error('测试错误');
  // 错误会被捕获，不影响其他回调
});

MD.API.config.set('fontSize', 18);
// 控制台输出: "Error in onChange callback: Error: 测试错误"
```

---

## 配置项详细说明

### `readingMode`

**类型**：`select`  
**选项**：`none`, `lookup`, `all`  
**默认值**：`lookup`

控制分词行为：
- `none`：不分词，显示原文
- `lookup`：仅在查词时分词
- `all`：自动分词所有内容

**使用场景**：
- 初学者：使用 `all` 模式，自动分词辅助阅读
- 进阶用户：使用 `lookup` 模式，按需查词
- 高级用户：使用 `none` 模式，不依赖分词

---

### `extractLemma`

**类型**：`boolean`  
**默认值**：`true`

是否提取单词原型（词根）。

**使用场景**：
- 英语：`running` → `run`，`better` → `good`
- 日语：`食べた` → `食べる`

启用后可提高查词命中率。

---

### `fontSize`

**类型**：`number`  
**范围**：12-32（步进 2）  
**默认值**：`16`

字体大小（像素）。

**验证规则**：
- 必须是数字
- 必须在 12-32 之间
- 必须是 2 的倍数（12, 14, 16, 18, ...）

---

### `clickBehavior`

**类型**：`select`  
**选项**：`click`, `longpress`  
**默认值**：`click`

触发查词的交互方式：
- `click`：单击触发
- `longpress`：长按触发

**使用场景**：
- 桌面端：推荐 `click`
- 移动端：推荐 `longpress`（避免误触）

---

### `historyLimit`

**类型**：`select`  
**选项**：`10`, `50`, `100`  
**默认值**：`50`

查词历史记录数量限制。

**使用场景**：
- 低内存设备：使用 `10`
- 一般使用：使用 `50`
- 重度用户：使用 `100`

---

### `popupHeight`

**类型**：`select`  
**选项**：`small`, `medium`, `large`, `full`  
**默认值**：`medium`

弹窗高度：
- `small`：约 200px
- `medium`：约 400px
- `large`：约 600px
- `full`：全屏

---

### `tokenStyle`

**类型**：`select`  
**选项**：`underline`, `background`, `none`  
**默认值**：`underline`

分词样式：
- `underline`：下划线
- `background`：背景色
- `none`：无样式

---

### `enabledDictionaries`

**类型**：`array`  
**元素类型**：`string`  
**默认值**：`[]`

启用的字典 ID 列表。

**验证规则**：
- 必须是数组
- 所有元素必须是字符串

**示例**：
```js
MD.API.config.set('enabledDictionaries', ['dict_001', 'dict_002']);

// 错误：不是数组
MD.API.config.set('enabledDictionaries', 'dict_001');
// Error: Invalid value for enabledDictionaries: expected array, got string

// 错误：元素不是字符串
MD.API.config.set('enabledDictionaries', ['dict_001', 123]);
// Error: Invalid value for enabledDictionaries: array item at index 1 is not a string
```

---

## 验证错误说明

所有 `set` 操作都会进行验证，以下是常见错误：

### 无效的配置项

```js
MD.API.config.set('invalidKey', 'value');
// Error: Invalid config key: invalidKey
```

### 类型不匹配

```js
// boolean 类型
MD.API.config.set('extractLemma', 'true');
// Error: Invalid value for extractLemma: expected boolean, got string

// number 类型
MD.API.config.set('fontSize', '18');
// Error: Invalid value for fontSize: expected number, got string

// array 类型
MD.API.config.set('enabledDictionaries', 'dict_001');
// Error: Invalid value for enabledDictionaries: expected array, got string
```

### 值超出范围

```js
// 小于最小值
MD.API.config.set('fontSize', 10);
// Error: Invalid value for fontSize: must be >= 12, got 10

// 大于最大值
MD.API.config.set('fontSize', 40);
// Error: Invalid value for fontSize: must be <= 32, got 40

// 不符合步进
MD.API.config.set('fontSize', 15);
// Error: Invalid value for fontSize: must be a multiple of 2, got 15
```

### 无效选项

```js
MD.API.config.set('readingMode', 'invalid');
// Error: Invalid value for readingMode: must be one of [none, lookup, all], got invalid

MD.API.config.set('clickBehavior', 'doubleclick');
// Error: Invalid value for clickBehavior: must be one of [click, longpress], got doubleclick
```

---

## 完整示例

### 配置面板

```html
<div id="config-panel">
  <h3>配置</h3>
  <div id="config-form"></div>
  <button id="reset-btn">重置所有</button>
  <button id="apply-btn">应用</button>
</div>

<script>
(function() {
  document.addEventListener('md:ready', function() {
    const api = window.MD.API;
    const schema = api.config.getSchema();
    const form = document.getElementById('config-form');
    
    // 动态生成表单
    Object.keys(schema).forEach(key => {
      const meta = schema[key];
      const value = api.config.get(key);
      const label = document.createElement('label');
      label.textContent = key + ': ';
      
      let input;
      if (meta.type === 'boolean') {
        input = document.createElement('input');
        input.type = 'checkbox';
        input.checked = value;
        input.addEventListener('change', () => {
          api.config.set(key, input.checked);
        });
      } else if (meta.type === 'number') {
        input = document.createElement('input');
        input.type = 'number';
        input.min = meta.min;
        input.max = meta.max;
        input.step = meta.step;
        input.value = value;
        input.addEventListener('change', () => {
          api.config.set(key, parseInt(input.value));
        });
      } else if (meta.type === 'select') {
        input = document.createElement('select');
        meta.options.forEach(opt => {
          const option = document.createElement('option');
          option.value = opt;
          option.textContent = opt;
          input.appendChild(option);
        });
        input.value = value;
        input.addEventListener('change', () => {
          api.config.set(key, input.value);
        });
      }
      
      label.appendChild(input);
      form.appendChild(label);
      form.appendChild(document.createElement('br'));
    });
    
    // 重置按钮
    document.getElementById('reset-btn').addEventListener('click', () => {
      if (confirm('确定重置所有配置？')) {
        api.config.reset();
        location.reload();
      }
    });
    
    // 应用按钮
    document.getElementById('apply-btn').addEventListener('click', () => {
      api.config.apply();
      alert('配置已应用');
    });
    
    // 监听变化
    api.config.onChange((key, value) => {
      console.log(`配置变化: ${key} = ${JSON.stringify(value)}`);
    });
  }, { once: true });
})();
</script>
```

---

## 相关文档

- [核心 API](./core.md) - `MD.API` 完整契约
- [数据模型](./data-models.md) - 数据结构定义
- [事件](./events.md) - DOM 事件约定
- [UI 组件](./ui.md) - UI 工具函数

---

**最后更新**：2026-02-05

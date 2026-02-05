# 模板注入迁移指南 - v1.x → v2.0.0

## 概述

Anki_Mdict v2.0.0 引入了容器化架构，支持嵌入式面板和居中弹窗两种模式。如果你之前使用了**模板注入功能**，需要重新注入以使用新的 UI。

## 问题症状

如果你遇到以下问题，说明你的模板使用的是旧版本的注入代码：

- ✗ 字典面板从底部弹出（旧样式）
- ✗ 样式与预期不符
- ✗ 字典功能不正常
- ✗ 没有使用新的居中弹窗

## 迁移步骤

### 方法 1：重新注入（推荐）

这是最简单的方法，适用于大多数用户。

1. **打开模板注入对话框**
   - 在 Anki 中：`工具` → `MDict` → `模板注入...`

2. **选择之前注入过的笔记类型**
   - 从下拉列表中选择笔记类型

3. **清除旧注入**
   - 点击"清除注入"按钮
   - 确认清除操作

4. **重新注入**
   - 勾选需要启用字典功能的字段
   - 为每个字段选择语言（ja/en）
   - 点击"注入"按钮

5. **验证**
   - 打开一张卡片
   - 确认字典面板显示在嵌入式容器中
   - 测试查词功能

### 方法 2：手动更新模板（高级用户）

如果你自定义了模板，可以手动更新注入的代码。

#### 查找旧代码

在模板中查找：
```html
<!-- mdict-tokenizer:begin -->
...
<script>
window.MDICT_FIELDS = [...];
if (window.MD && typeof window.MD.init === 'function') {
  window.MD.init({ autoTokenize: true });  <!-- 旧代码：没有 targetContainer -->
}
</script>
<!-- mdict-tokenizer:end -->
```

#### 替换为新代码

```html
<!-- mdict-tokenizer:begin -->
<link rel="stylesheet" href="_mdict_style.css">
<script src="_mdict_config.js"></script>
<script src="_mdict_tokenizer.js"></script>
<script src="_mdict_dictionary.js"></script>
<script src="_mdict_ui.js"></script>
<script src="_mdict_main.js"></script>
<div id="mdict-panel"></div>
<script>
window.MDICT_FIELDS = [...];  <!-- 保持你的字段配置 -->
if (window.MD && typeof window.MD.init === 'function') {
  window.MD.init({ autoTokenize: true, targetContainer: '#mdict-panel' });
}
</script>
<!-- mdict-tokenizer:end -->
```

**关键变化**：
1. ✅ 添加了 `<div id="mdict-panel"></div>` 容器
2. ✅ 初始化调用添加了 `targetContainer: '#mdict-panel'` 参数

## 新功能说明

### 双模式架构

v2.0.0 支持两种显示模式：

#### 1. 嵌入式模式（默认）
- 字典面板渲染在 `#mdict-panel` 容器内
- 与卡片内容集成
- 自适应容器尺寸

#### 2. 居中弹窗模式（回退）
- 当没有容器时自动启用
- 居中显示（不是从底部弹出）
- 使用新的模态样式

### 新的 CSS 主题系统

- 92 个 CSS 变量（`--md-*` 命名空间）
- 支持暗色模式（`.nightMode` 类）
- 独立于其他插件的样式

### API v2.0.0

新增方法：
- `MD.API.ui.getMode()` - 获取当前模式（'embedded' 或 'modal'）
- `MD.API.ui.showPanel()` - 显示面板
- `MD.API.ui.hidePanel()` - 隐藏面板

详见：`docs/api/README.md`

## 常见问题

### Q: 我需要重新导入字典吗？
**A**: 不需要。字典数据和配置不受影响，只需要更新模板。

### Q: 重新注入会影响现有卡片吗？
**A**: 不会。重新注入只更新模板代码，不会修改卡片内容或字段数据。

### Q: 我可以保留旧的弹窗模式吗？
**A**: 不建议。旧的弹窗模式已被新的居中弹窗取代。如果你不想使用嵌入式模式，可以不提供容器，系统会自动使用新的居中弹窗。

### Q: 如何验证迁移成功？
**A**: 打开一张卡片，检查：
1. 字典面板显示在容器内（或居中弹窗）
2. 样式正确（使用新的 CSS 主题）
3. 查词功能正常
4. 暗色模式正常（如果启用）

### Q: 迁移后出现问题怎么办？
**A**: 
1. 确认已清除旧注入并重新注入
2. 检查浏览器控制台（F12）是否有错误
3. 确认 `_mdict_*.js` 文件在 `collection.media` 目录
4. 尝试重启 Anki

## 技术细节

### 容器检测逻辑

Mdict v2.0.0 在初始化时检测容器：

```javascript
// 如果提供了 targetContainer
MD.init({ targetContainer: '#mdict-panel' })
// → 检测到容器 → 嵌入式模式

// 如果没有提供 targetContainer
MD.init({ autoTokenize: true })
// → 未检测到容器 → 居中弹窗模式（新样式）
```

### 向后兼容性

- ✅ 所有 v1.x API 保留
- ✅ 旧的初始化方式仍然有效（但使用弹窗模式）
- ✅ 字典数据格式不变
- ✅ 事件系统不变

## 相关文档

- [API 文档](api/README.md) - 完整 API 参考
- [迁移指南](api/README.md#迁移指南-v1x--v20) - API 迁移详情
- [UI 组件文档](api/ui.md) - UI 方法说明

## 更新日志

### v2.0.0 (2026-02-06)
- ✨ 新增容器化架构（嵌入式 + 居中弹窗）
- ✨ 新增 CSS 主题系统（92 个变量）
- ✨ 新增 API v2.0.0 方法
- 🐛 修复模板注入器生成旧代码的问题
- 📝 更新文档和迁移指南

---

**最后更新**: 2026-02-06  
**版本**: 2.0.0

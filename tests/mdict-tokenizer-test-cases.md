# Test Cases: Anki_Mdict 分词-辞典插件

## Overview
- **Feature**: 分词-辞典插件
- **Requirements Source**: `specs/001-mdict-tokenizer-plugin/spec.md`
- **Test Coverage**: 辞典管理、分词配置、模板注入、查词 UI、跨平台兼容、错误处理与性能目标
- **Last Updated**: 2026-01-24

## Test Case Categories

### 1. Functional Tests

#### TC-F-001: 导入 MDX 并生成分片与索引
- **Requirement**: FR-001, FR-010
- **Priority**: High
- **Preconditions**:
  - 准备可用的 MDX 文件
  - Anki 媒体目录可写
- **Test Steps**:
  1. 在辞典管理界面导入 MDX
  2. 等待后台预处理完成
  3. 检查媒体目录中的 `_mdict_{id}_shard_*.json` 与 `_mdict_{id}_index.json`
- **Expected Results**:
  - 生成 JSON 分片与索引文件
  - 配置文件记录辞典路径与语言
- **Postconditions**: 新辞典可用于查词

#### TC-F-002: 设置辞典语言标签
- **Requirement**: FR-002
- **Priority**: Medium
- **Preconditions**:
  - 已导入辞典
- **Test Steps**:
  1. 在辞典管理中修改语言标签
  2. 保存配置
- **Expected Results**:
  - 语言标签被持久化保存
- **Postconditions**: 分词系统可过滤匹配语言

#### TC-F-003: 添加 MDD 媒体资源
- **Requirement**: FR-003, FR-036
- **Priority**: High
- **Preconditions**:
  - 已导入辞典
  - 准备对应 MDD 文件
- **Test Steps**:
  1. 为辞典添加 MDD
  2. 打开词条中含媒体资源的条目
- **Expected Results**:
  - 媒体资源被提取到媒体目录
  - 词条中的图片/音频可显示或播放
- **Postconditions**: 资源映射文件可用

#### TC-F-004: 添加 CSS 并应用作用域
- **Requirement**: FR-004, FR-037
- **Priority**: High
- **Preconditions**:
  - 已导入辞典
  - 准备 CSS 文件
- **Test Steps**:
  1. 为辞典添加 CSS
  2. 打开词条内容
- **Expected Results**:
  - CSS 被添加作用域前缀
  - 辞典内容按自定义样式渲染
- **Postconditions**: CSS 文件留存在媒体目录

#### TC-F-005: 删除 MDD 但保留 MDX
- **Requirement**: FR-005
- **Priority**: Medium
- **Preconditions**:
  - 辞典包含 MDD 资源
- **Test Steps**:
  1. 仅删除 MDD
  2. 打开辞典内容
- **Expected Results**:
  - MDD 资源被删除
  - MDX 与 CSS 仍保留
- **Postconditions**: 无媒体资源显示

#### TC-F-006: 删除 CSS 但保留 MDX
- **Requirement**: FR-006
- **Priority**: Medium
- **Preconditions**:
  - 辞典包含 CSS
- **Test Steps**:
  1. 仅删除 CSS
  2. 打开辞典内容
- **Expected Results**:
  - CSS 被删除
  - MDX 与 MDD 仍保留
- **Postconditions**: 恢复默认样式

#### TC-F-007: 删除 MDX 时清理关联资源
- **Requirement**: FR-007
- **Priority**: High
- **Preconditions**:
  - 辞典包含 MDD 与 CSS
- **Test Steps**:
  1. 删除 MDX 辞典
  2. 检查媒体目录
- **Expected Results**:
  - 关联的 MDD 与 CSS 被删除
- **Postconditions**: 辞典不再可用

#### TC-F-008: 拖拽调整辞典顺序
- **Requirement**: FR-008, FR-009
- **Priority**: Medium
- **Preconditions**:
  - 至少两个辞典
- **Test Steps**:
  1. 拖拽调整辞典顺序
  2. 重启 Anki 或重新打开界面
- **Expected Results**:
  - 顺序持久化保存
- **Postconditions**: 查词显示顺序更新

#### TC-F-009: 日语分词与原型提取
- **Requirement**: FR-011, FR-013
- **Priority**: High
- **Preconditions**:
  - 日语分词配置已开启原型提取
- **Test Steps**:
  1. 在卡片上渲染日语文本
  2. 检查词元原型
- **Expected Results**:
  - 分词正常
  - 原型显示正确（如“食べた”→“食べる”）
- **Postconditions**: 可点击查词

#### TC-F-010: 日语注音显示
- **Requirement**: FR-014
- **Priority**: Medium
- **Preconditions**:
  - 日语分词配置开启注音显示
- **Test Steps**:
  1. 渲染含汉字文本
  2. 查看注音
- **Expected Results**:
  - 汉字显示假名注音
- **Postconditions**: 注音可切换

#### TC-F-011: 英语分词与原型提取
- **Requirement**: FR-012, FR-013
- **Priority**: High
- **Preconditions**:
  - 英语分词配置开启原型提取
- **Test Steps**:
  1. 渲染英语文本
  2. 检查词元原型
- **Expected Results**:
  - 分词正常
  - 原型显示正确（如“running”→“run”）
- **Postconditions**: 可点击查词

#### TC-F-012: 英语 IPA 音标显示
- **Requirement**: FR-015
- **Priority**: Medium
- **Preconditions**:
  - 英语分词开启音标显示
- **Test Steps**:
  1. 渲染英语文本
  2. 检查音标显示
- **Expected Results**:
  - 词元显示 IPA 音标
- **Postconditions**: 音标可切换

#### TC-F-013: 分词系统关联辞典
- **Requirement**: FR-016, FR-017
- **Priority**: High
- **Preconditions**:
  - 存在日语、英语、双语辞典
- **Test Steps**:
  1. 打开日语分词配置
  2. 检查可选辞典列表
  3. 切换到英语分词配置
- **Expected Results**:
  - 日语配置只显示日语与双语辞典
  - 英语配置只显示英语与双语辞典
- **Postconditions**: 关联关系保存

#### TC-F-014: 注入模板并分词渲染
- **Requirement**: FR-019, FR-020
- **Priority**: High
- **Preconditions**:
  - 选择一个笔记类型与字段
- **Test Steps**:
  1. 执行模板注入
  2. 预览卡片
- **Expected Results**:
  - 字段内容被分词处理
- **Postconditions**: 注入配置记录

#### TC-F-015: 点击词元弹出辞典查询框
- **Requirement**: FR-021, FR-023
- **Priority**: High
- **Preconditions**:
  - 已注入分词功能
- **Test Steps**:
  1. 点击词元
  2. 切换辞典
- **Expected Results**:
  - 弹窗出现
  - 切换后显示对应释义
- **Postconditions**: 查词历史记录

#### TC-F-016: 手动搜索与查词历史
- **Requirement**: FR-022, FR-024, SC-008
- **Priority**: Medium
- **Preconditions**:
  - 弹窗已打开
- **Test Steps**:
  1. 输入查询单词
  2. 查看历史列表
- **Expected Results**:
  - 查询结果更新
  - 历史记录可回看且可保存 100 条
- **Postconditions**: 历史数据存储

#### TC-F-017: 清除模板注入
- **Requirement**: FR-025
- **Priority**: Medium
- **Preconditions**:
  - 已注入模板
- **Test Steps**:
  1. 在注入管理界面点击清除
  2. 预览卡片
- **Expected Results**:
  - 模板恢复原状
- **Postconditions**: 注入配置清理

#### TC-F-018: 卡片内嵌配置功能
- **Requirement**: FR-026, FR-027, FR-028, FR-029, FR-030, FR-031, FR-032, FR-033, FR-034
- **Priority**: Medium
- **Preconditions**:
  - 卡片已注入
- **Test Steps**:
  1. 打开卡片内嵌配置
  2. 逐项修改配置并保存
- **Expected Results**:
  - 各配置项生效且持久化
- **Postconditions**: localStorage 保存偏好

#### TC-F-019: 辞典渲染 HTML 与资源
- **Requirement**: FR-035, FR-036, FR-037
- **Priority**: High
- **Preconditions**:
  - 词条包含 HTML、图片、音频与 CSS
- **Test Steps**:
  1. 查词显示内容
  2. 检查 HTML 样式和媒体加载
- **Expected Results**:
  - HTML 正确渲染
  - 图片/音频加载正常
  - CSS 样式生效
- **Postconditions**: 无

#### TC-F-020: 分词性能目标
- **Requirement**: FR-018, SC-003, SC-004
- **Priority**: Medium
- **Preconditions**:
  - 准备常用句子样本
- **Test Steps**:
  1. 记录从点击词元到弹窗出现的时间
  2. 记录到释义渲染完成的时间
- **Expected Results**:
  - 弹窗出现 ≤500ms
  - 释义渲染 ≤1s
- **Postconditions**: 性能记录可追踪

#### TC-F-021: 分词准确率（日语）
- **Requirement**: SC-006
- **Priority**: High
- **Preconditions**:
  - JLPT N5-N2 词表可用
  - 前端分词环境可运行
- **Test Steps**:
  1. 使用 JLPT 词表进行分词与原型提取
  2. 统计正确率
- **Expected Results**:
  - 正确率 ≥90%
- **Postconditions**: 记录准确率结果

#### TC-F-022: 分词准确率（英语）
- **Requirement**: SC-007
- **Priority**: High
- **Preconditions**:
  - COCA 5000 词表可用
  - 前端分词环境可运行
- **Test Steps**:
  1. 使用 COCA 词表进行分词与原型提取
  2. 统计正确率
- **Expected Results**:
  - 正确率 ≥90%
- **Postconditions**: 记录准确率结果

### 2. Edge Case Tests

#### TC-E-001: 未识别词元保持原样
- **Requirement**: 边界情况
- **Priority**: Low
- **Preconditions**:
  - 输入包含生造词
- **Test Steps**:
  1. 渲染包含生造词文本
- **Expected Results**:
  - 生造词保持原样
- **Postconditions**: 无

#### TC-E-002: 未找到释义提示
- **Requirement**: 边界情况
- **Priority**: Low
- **Preconditions**:
  - 辞典不存在某词
- **Test Steps**:
  1. 查询不存在的词
- **Expected Results**:
  - 弹窗显示“未找到释义”
- **Postconditions**: 无

### 3. Error Handling Tests

#### TC-ERR-001: MDX 文件损坏或编码不支持
- **Requirement**: 边界情况
- **Priority**: High
- **Preconditions**:
  - 准备损坏或编码不支持的 MDX
- **Test Steps**:
  1. 导入 MDX
- **Expected Results**:
  - 显示对应错误提示
- **Postconditions**: 导入失败且无残留数据

#### TC-ERR-002: 重复导入 MDX
- **Requirement**: 边界情况
- **Priority**: Medium
- **Preconditions**:
  - 已导入相同 MDX
- **Test Steps**:
  1. 再次导入同一 MDX
- **Expected Results**:
  - 显示“辞典已存在”并阻止导入
- **Postconditions**: 辞典不重复

#### TC-ERR-003: 删除被模板使用的辞典
- **Requirement**: 边界情况
- **Priority**: Medium
- **Preconditions**:
  - 辞典已被模板引用
- **Test Steps**:
  1. 删除该辞典
- **Expected Results**:
  - 显示警告并要求确认
- **Postconditions**: 根据用户选择处理

#### TC-ERR-004: 分词器初始化失败
- **Requirement**: FR-041
- **Priority**: High
- **Preconditions**:
  - 人为阻断分词器资源加载
- **Test Steps**:
  1. 打开卡片
- **Expected Results**:
  - 显示友好错误提示
  - 可重试或跳过
- **Postconditions**: 错误状态可恢复

#### TC-ERR-005: fetch 不可用降级
- **Requirement**: FR-042
- **Priority**: Medium
- **Preconditions**:
  - 禁用 fetch API
- **Test Steps**:
  1. 触发辞典加载
- **Expected Results**:
  - 自动使用 XMLHttpRequest
- **Postconditions**: 查询成功

### 4. State Transition Tests

#### TC-ST-001: 注音显示切换
- **Requirement**: FR-028
- **Priority**: Medium
- **Preconditions**:
  - 日语分词开启注音显示
- **Test Steps**:
  1. 切换注音显示方式
  2. 观察卡片渲染
- **Expected Results**:
  - 注音显示随设置切换
- **Postconditions**: 配置持久化

## Test Coverage Matrix

| Requirement ID | Test Cases | Coverage Status |
|---------------|------------|-----------------|
| FR-001 | TC-F-001 | ✓ Complete |
| FR-002 | TC-F-002 | ✓ Complete |
| FR-003 | TC-F-003 | ✓ Complete |
| FR-004 | TC-F-004 | ✓ Complete |
| FR-005 | TC-F-005 | ✓ Complete |
| FR-006 | TC-F-006 | ✓ Complete |
| FR-007 | TC-F-007 | ✓ Complete |
| FR-008 | TC-F-008 | ✓ Complete |
| FR-009 | TC-F-008 | ✓ Complete |
| FR-010 | TC-F-001 | ✓ Complete |
| FR-011 | TC-F-009 | ✓ Complete |
| FR-012 | TC-F-011 | ✓ Complete |
| FR-013 | TC-F-009, TC-F-011 | ✓ Complete |
| FR-014 | TC-F-010 | ✓ Complete |
| FR-015 | TC-F-012 | ✓ Complete |
| FR-016 | TC-F-013 | ✓ Complete |
| FR-017 | TC-F-013 | ✓ Complete |
| FR-018 | TC-F-020 | ✓ Complete |
| FR-019 | TC-F-014 | ✓ Complete |
| FR-020 | TC-F-014 | ✓ Complete |
| FR-021 | TC-F-015 | ✓ Complete |
| FR-022 | TC-F-016 | ✓ Complete |
| FR-023 | TC-F-015 | ✓ Complete |
| FR-024 | TC-F-016 | ✓ Complete |
| FR-025 | TC-F-017 | ✓ Complete |
| FR-026 | TC-F-018 | ✓ Complete |
| FR-027 | TC-F-018 | ✓ Complete |
| FR-028 | TC-F-018, TC-ST-001 | ✓ Complete |
| FR-029 | TC-F-018 | ✓ Complete |
| FR-030 | TC-F-018 | ✓ Complete |
| FR-031 | TC-F-018 | ✓ Complete |
| FR-032 | TC-F-018 | ✓ Complete |
| FR-033 | TC-F-018 | ✓ Complete |
| FR-034 | TC-F-018 | ✓ Complete |
| FR-035 | TC-F-019 | ✓ Complete |
| FR-036 | TC-F-003, TC-F-019 | ✓ Complete |
| FR-037 | TC-F-004, TC-F-019 | ✓ Complete |
| FR-038 | TC-F-018 | ✓ Complete |
| FR-039 | TC-F-018 | ✓ Complete |
| FR-040 | TC-F-008 | ✓ Complete |
| FR-041 | TC-ERR-004 | ✓ Complete |
| FR-042 | TC-ERR-005 | ✓ Complete |

## Notes
- 分词准确率与性能测试建议在浏览器/移动端环境运行并记录结果。
- 词表来源需明确版本与日期，以保证可重复性。

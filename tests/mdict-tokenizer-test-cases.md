# Test Cases: Anki_Mdict 分词-辞典插件

## Overview
- **Feature**: 分词-辞典插件
- **Requirements Source**: `specs/001-mdict-tokenizer-plugin/spec.md`
- **Test Coverage**: 辞典管理、分词配置、模板注入、查词 UI、跨平台兼容、错误处理与性能目标
- **Last Updated**: 2026-02-03
- **Executor Note**: 2026-02-03（Codex）— 同步辞典管理：语言只读、按语言启用/排序/查词回归用例。
- **Executor**: Codex

## Test Case Categories

### 1. Functional Tests

#### TC-F-001: 导入 MDX 并生成分片与索引
- **Requirement**: FR-001, FR-010
- **Priority**: High
- **Preconditions**:
  - 准备可用的 MDX 文件
  - Anki 媒体目录可写
- **Test Steps**:
  1. 在辞典管理界面导入 MDX（导入时选择辞典 `languages`）
  2. 等待后台预处理完成
  3. 检查媒体目录中的 `_mdict_{id}_shard_*.json` 与 `_mdict_{id}_index.json`
- **Expected Results**:
  - 生成 JSON 分片与索引文件
  - 配置文件记录辞典路径与 `languages`
- **Postconditions**: 新辞典可用于查词

#### TC-F-002: 辞典语言标签只读（导入时确定）
- **Requirement**: FR-002
- **Priority**: Medium
- **Preconditions**:
  - 已导入辞典
- **Test Steps**:
  1. 打开辞典管理，查看辞典的 `languages` 显示
  2. 确认 `languages` 仅为只读展示（不应存在编辑入口，如编辑框/修改按钮/可保存的语言编辑对话框）
- **Expected Results**:
  - `languages` 为只读（导入时确定），UI 不提供编辑入口或编辑后不允许保存
  - 配置与查词过滤以导入时的 `languages` 为准
- **Postconditions**: 分词系统可按 `languages` 过滤匹配语言

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
  1. 在辞典管理中选择目标语言（语言下拉框）
  2. 在该语言下拖拽调整辞典顺序
  3. 切换到另一种语言，观察该语言下的顺序（应保持独立）
  4. 重启 Anki 或重新打开界面
- **Expected Results**:
  - 每种语言的顺序独立持久化（`tokenizers[lang].dictionaryIds`）
  - 重新打开界面后，当前语言的顺序保持不变
- **Postconditions**: 查词展示按当前查词语言的顺序更新

#### TC-F-008C: 语言下拉框选项合集 + 按语言过滤辞典（手工回归）
- **Requirement**: FR-002, FR-016, FR-017
- **Priority**: High
- **Preconditions**:
  - 至少三本辞典：仅 `ja`、仅 `en`、`ja+en`（双语）
- **Test Steps**:
  1. 打开辞典管理，观察语言下拉框选项
  2. 选择语言 `ja`，观察列表中显示的辞典集合
  3. 选择语言 `en`，观察列表中显示的辞典集合
  4. （可选）选择其他语言或空态，确认 UI 有明确提示
- **Expected Results**:
  - 语言下拉框至少包含：所有已导入辞典的 `languages` 并集（本例包含 `ja` 与 `en`）
  - 选择 `ja` 时，列表仅显示 `languages` 含 `ja` 的辞典（含双语辞典）
  - 选择 `en` 时，列表仅显示 `languages` 含 `en` 的辞典（含双语辞典）
- **Postconditions**: 无

#### TC-F-008D: 行内操作：重命名（仅名称）+ 删除辞典（手工回归）
- **Requirement**: FR-007
- **Priority**: High
- **Preconditions**:
  - 已导入辞典，且在辞典管理列表可见
- **Test Steps**:
  1. 在辞典管理中对某辞典执行“重命名”（仅修改显示名称）并保存
  2. 观察该辞典的 `languages` 是否仍为只读展示且未变化
  3. 关闭并重新打开辞典管理，确认名称持久化
  4. 对该辞典执行“删除辞典”，确认弹窗并完成删除
  5. 切换到该辞典所属的每种语言，确认列表均不再出现该辞典
- **Expected Results**:
  - 重命名仅影响显示名称；不影响辞典文件路径、`languages`、以及各语言的启用/排序逻辑
  - 删除辞典后：辞典从所有语言列表移除；后续查词候选集不再包含该辞典
- **Postconditions**: 无

#### TC-F-008E: 行内操作：添加/删除 MDD 与 CSS（手工回归）
- **Requirement**: FR-003, FR-004, FR-005, FR-006
- **Priority**: High
- **Preconditions**:
  - 已导入辞典
  - 准备对应 MDD 与 CSS 文件
- **Test Steps**:
  1. 在辞典管理中对某辞典执行“添加 MDD”并完成导入
  2. 立即执行“删除 MDD”（不删除 MDX），然后再次打开含媒体资源的词条
  3. 对同一辞典执行“添加 CSS”，确认样式生效
  4. 执行“删除 CSS”（不删除 MDX/MDD），确认样式恢复默认
- **Expected Results**:
  - 添加/删除 MDD 与 CSS 为行内可用操作；行为与 TC-F-003~TC-F-006 一致
  - 删除 MDD/CSS 不应影响辞典在各语言下的启用状态与排序
- **Postconditions**: 无

#### TC-F-008F: 快速试查（Quick Try Lookup）按当前语言生效（手工回归）
- **Requirement**: FR-021, FR-022
- **Priority**: High
- **Preconditions**:
  - 至少两本同语言辞典（A/B）且都有可命中词条
  - 已在辞典管理为该语言配置启用/停用与顺序（`tokenizers[lang].dictionaryIds`）
- **Test Steps**:
  1. 在辞典管理选择语言 `ja`（或目标语言）
  2. 使用“快速试查”输入一个可命中的词并执行查词
  3. 调整该语言下辞典顺序（或启用/停用），再次用同一词进行快速试查
- **Expected Results**:
  - 快速试查使用“当前选择语言”的候选辞典集合与顺序
  - 候选顺序与 `tokenizers[lang].dictionaryIds` 一致；停用的辞典不应出现在结果中
- **Postconditions**: 无

#### TC-F-008A: 按语言拖拽排序 + 保存当前语言顺序（手工回归）
- **Requirement**: FR-008, FR-009
- **Priority**: High
- **Preconditions**:
  - 至少三本辞典（其中两本同时支持同一语言）
- **Test Steps**:
  1. 选择语言 `ja`，把辞典顺序改为：A → B → C
  2. 切换语言 `en`，把辞典顺序改为：C → A
  3. 切回 `ja`，确认仍为 A → B → C
  4. 重启 Anki 或刷新辞典管理界面，再分别检查 `ja/en` 的顺序
- **Expected Results**:
  - `ja` 与 `en` 的顺序互不影响，且都能持久化
- **Postconditions**: 无

#### TC-F-008B: 按语言启用/停用辞典影响查词候选集（手工回归）
- **Requirement**: FR-016, FR-017, FR-021
- **Priority**: High
- **Preconditions**:
  - 已注入分词功能
  - 至少两本同语言辞典（A/B），且都有可命中的词条
- **Test Steps**:
  1. 在辞典管理选择语言 `ja`，仅启用辞典 A，停用辞典 B
  2. 点击一个日语词元打开弹窗，观察候选辞典/Tab 列表
  3. 回到辞典管理语言 `ja`，启用辞典 B 并拖拽到 A 前面
  4. 再次点击同一词元打开弹窗，观察候选辞典与展示顺序
- **Expected Results**:
  - 弹窗候选辞典仅包含该语言已启用的辞典
  - 展示顺序与 `tokenizers[lang].dictionaryIds` 一致（B 在 A 前）
- **Postconditions**: 无

#### TC-F-008C: 语言下拉聚合与切换过滤（手工回归）
- **Requirement**: FR-016, FR-017
- **Priority**: High
- **Preconditions**:
  - 已导入至少 3 本辞典，覆盖至少 2 种语言
- **Test Steps**:
  1. 打开辞典管理界面（Qt Dict Manager）
  2. 展开语言下拉，确认语言列表为聚合结果（仅展示当前存在的语言）
  3. 选择一种语言（如 `ja`），观察辞典列表
  4. 切换到另一种语言（如 `en`），观察辞典列表
- **Expected Results**:
  - 语言下拉可用于在语言视图间切换
  - 切换语言后，辞典列表按所选语言过滤展示
- **Postconditions**: 无

#### TC-F-008D: 行内操作：添加/删除 MDD（手工回归）
- **Requirement**: FR-003, FR-005, FR-036
- **Priority**: Medium
- **Preconditions**:
  - 已导入辞典
  - 准备对应 MDD 文件
- **Test Steps**:
  1. 打开辞典管理界面（Qt Dict Manager）
  2. 在目标辞典行内执行“添加 MDD”（或等价入口），选择 MDD 文件
  3. 打开一个包含媒体资源的词条，确认资源可加载
  4. 回到辞典管理界面，在同一辞典行内执行“删除 MDD”（或等价入口）
  5. 再次打开相同词条
- **Expected Results**:
  - 添加后，媒体资源可显示/播放
  - 删除后，MDD 资源不再可用（媒体不再显示/播放）
- **Postconditions**: 无

#### TC-F-008E: 行内操作：添加/删除 CSS（手工回归）
- **Requirement**: FR-004, FR-006, FR-037
- **Priority**: Medium
- **Preconditions**:
  - 已导入辞典
  - 准备 CSS 文件
- **Test Steps**:
  1. 打开辞典管理界面（Qt Dict Manager）
  2. 在目标辞典行内执行“添加 CSS”（或等价入口），选择 CSS 文件
  3. 打开词条内容，观察样式渲染
  4. 回到辞典管理界面，在同一辞典行内执行“删除 CSS”（或等价入口）
  5. 再次打开相同词条
- **Expected Results**:
  - 添加后，CSS 生效且不影响其他辞典
  - 删除后，样式恢复为无自定义 CSS 的效果
- **Postconditions**: 无

#### TC-F-008F: 行内操作：重命名辞典（手工回归）
- **Requirement**: FR-002
- **Priority**: Medium
- **Preconditions**:
  - 已导入辞典
- **Test Steps**:
  1. 打开辞典管理界面（Qt Dict Manager）
  2. 在目标辞典行内执行“重命名”（或等价入口），输入新名称并确认
  3. 关闭并重新打开辞典管理界面
- **Expected Results**:
  - 辞典显示名称更新并持久化
  - 不影响辞典内容查询结果
- **Postconditions**: 无

#### TC-F-008G: 行内操作：删除辞典（手工回归）
- **Requirement**: FR-007
- **Priority**: High
- **Preconditions**:
  - 已导入辞典
- **Test Steps**:
  1. 打开辞典管理界面（Qt Dict Manager）
  2. 在目标辞典行内执行“删除辞典”（或等价入口）
  3. 如出现确认提示，确认删除
  4. 在查词弹窗/手动搜索中搜索该辞典存在的词条
- **Expected Results**:
  - 辞典被删除并从列表中移除
  - 查词不再命中已删除辞典
- **Postconditions**: 无

#### TC-F-008H: “快速试查”按当前语言启用+顺序命中（手工回归）
- **Requirement**: FR-016, FR-017, FR-021
- **Priority**: High
- **Preconditions**:
  - 当前语言视图下至少 2 本辞典（A/B），且存在一个“两个辞典都能命中但释义可区分”的查询词
- **Test Steps**:
  1. 在辞典管理选择语言 `ja`，确保 A/B 均为启用
  2. 拖拽把 B 调整到 A 前面，并保存当前语言顺序
  3. 使用 Qt Dict Manager 的“快速试查”输入该查询词，观察优先命中的辞典/展示顺序
  4. 将 B 在该语言下切换为停用
  5. 再次使用“快速试查”输入同一查询词
- **Expected Results**:
  - 两本都启用时，命中/展示优先级按当前语言顺序 `B → A` 生效
  - 停用 B 后，快速试查不再命中 B，而是命中 A
- **Postconditions**: 无

#### TC-F-008I: 查词顺序按 `tokenizers[lang].dictionaryIds` 生效（手工回归）
- **Requirement**: FR-008, FR-009
- **Priority**: High
- **Preconditions**:
  - 已完成 `TC-F-008A` 或 `TC-F-008B`：当前语言顺序已调整并持久化
  - 存在一个可在多本辞典都命中的查询词
- **Test Steps**:
  1. 在卡片上点击该语言词元打开查词弹窗
  2. 观察候选辞典/Tab 列表的顺序与默认展示
- **Expected Results**:
  - 候选辞典顺序与 `tokenizers[lang].dictionaryIds` 一致
- **Postconditions**: 无

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
  - 实际启用/顺序由辞典管理按语言维护，并持久化到 `tokenizers[lang].dictionaryIds`
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
  - 弹窗默认候选辞典与顺序按“该次触发的语言”决定
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

#### TC-F-016A: 弹窗搜索框沿用最近一次触发语言（手工回归）
- **Requirement**: FR-022
- **Priority**: Medium
- **Preconditions**:
  - 已注入分词功能
  - 同时存在 `ja` 与 `en` 的可查词元
- **Test Steps**:
  1. 先点击一个 `ja` 词元打开弹窗，然后关闭弹窗
  2. 再点击一个 `en` 词元打开弹窗（不手动切换语言）
  3. 在弹窗搜索框输入一个英文词并搜索
  4. 再次点击一个 `ja` 词元打开弹窗，在弹窗搜索框输入一个日语词并搜索
- **Expected Results**:
  - 弹窗搜索使用最近一次触发语言（`lastLookupLanguage`）对应的辞典集合与顺序
  - 第 3 步优先走 `en` 的候选辞典；第 4 步优先走 `ja` 的候选辞典
- **Postconditions**: 无

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

#### TC-E-003: 纯标点/符号/emoji 不生成可点击词元
- **Requirement**: 边界情况
- **Priority**: Medium
- **Preconditions**:
  - 已注入分词功能
  - 浏览器可打开本仓库的静态页面
- **Test Steps**:
  1. 在仓库根目录启动静态服务器：`python -m http.server 8000`
  2. 打开自动化自测页面：`http://localhost:8000/Anki_Mdict/tests/web/test_mdict_punct_filter.html`
  3. 在页面/卡片中输入或渲染以下示例文本（混合 CN/JA/EN）：
     - `今天はTokyoに行く。I can't believe it! (mother-in-law) — テスト… 😀`
  4. 观察纯标点/符号/emoji 的展示：`。 , ( ) ! — … 😀`
  5. 用开发者工具检查 DOM：
     - 纯标点/符号/emoji 不应被包裹为 `.md-token`
     - 含字母/数字的 token 应被包裹为 `.md-token`（可点击查词）
     - 不对 `'` 与 `-` 的归属做强断言：
       - `can't` 可能是单个 token，也可能被拆分为多个 token
       - `mother-in-law` 可能是单个 token，也可能被拆分为多个 token（如 `mother-`、`in-`、`law`）
       - 上述拆分/包含均可接受，只要“含字母/数字的 token”仍为可点击 `.md-token`
- **Expected Results**:
  - 纯标点/符号/emoji 仍然可见，但不是可点击词元（不包 `.md-token`）
  - 含字母/数字的 token 仍为可点击词元（包 `.md-token`），允许在 `'` 与 `-` 附近拆分或将符号附着到词元上
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

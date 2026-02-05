# MDict Tokenizer（Anki_Mdict）
# Anki_Mdict（MDict Tokenizer）

Anki_Mdict 提供 MDict（MDX/MDD）词典导入、分词配置、模板注入与稳定前端 API（`window.MD.API`）。
插件包名：`mdict_tokenizer`（`manifest.json`），当前版本：`1.0.0`。

## 功能概览
- MDX 导入与分片索引生成（`_mdict_*_shard_*.json`）
- MDD 资源提取与映射（`_mdict_*_res_*.{ext}`）
- CSS 作用域处理（自动加 `.mdict-{dict_id}` 前缀）
- 辞典管理 UI：启用/禁用、排序、重命名、删除、快速试查
- 分词配置：语言、词形还原、日语读音/英语音标、关联辞典
- 模板注入：选择笔记类型字段并注入脚本与包裹标记
- 前端稳定接口：`window.MD.API`、`md:*` 事件

## 菜单入口
在 Anki 菜单中：`工具 → MDict`
- **辞典管理...**：导入/管理辞典与资源
- **分词配置...**：配置语言、词形、读音/音标与启用辞典
- **模板注入...**：为笔记类型字段注入 MDict 脚本
- **检查环境**：检测 `mdict-utils` 依赖是否可用

## 安装
1. 下载插件文件
2. 在 Anki 中：`工具 → 附加组件 → 从文件安装`
3. 重启 Anki

## 使用流程

### 1) 导入辞典（MDX）
进入：`工具 → MDict → 辞典管理...` → **导入 MDX**
- 选择 `.mdx` 文件
- 输入语言（逗号分隔，例如 `ja,en`）
- 导入成功后自动生成分片索引并复制 MDX 到 `collection.media`

### 2) 追加资源（MDD/CSS）
在辞典管理列表中：
- **添加 MDD / 删除 MDD**：导入或移除资源包
- **添加 CSS / 删除 CSS**：为辞典内容附加样式（会自动做作用域处理）

### 3) 启用/排序/重命名
- 勾选 **启用** 控制当前语言可用辞典
- 拖拽列表调整顺序 → **保存当前语言顺序**
- 支持 **重命名** 与 **删除辞典**

### 4) 快速试查
在辞典管理下方输入词条，点击 **快速试查** 查看摘要结果

### 5) 分词配置
进入：`工具 → MDict → 分词配置...`
- 语言：`ja` / `en`
- 选项：提取原型、日语读音、英语音标
- 勾选该语言关联辞典并保存

### 6) 模板注入
进入：`工具 → MDict → 模板注入...`
- 选择笔记类型
- 勾选要启用分词/查词的字段并设置语言
- **注入**：插入脚本块并为字段包裹 `<span class="mdict-field" ...>`
- **清除注入**：移除脚本块与包裹标记

## 配置与生成文件

### 配置文件
配置文件在 `collection.media/_mdict_config.json`，结构由代码生成：
- `version`：配置版本
- `dictionaries`：辞典列表（`id/name/languages/order/meta/resources/filePrefix`）
- `tokenizers`：按语言的分词配置
- `injections`：模板注入记录

默认会生成 `ja` 与 `en` 两个分词配置（`extractLemma` 默认开启）。

### 生成文件清单（示例）
在 `collection.media` 下：
- `_mdict_{dict_id}.mdx`：MDX 复制
- `_mdict_{dict_id}_meta.json`：词典元数据
- `_mdict_{dict_id}_index.json`：索引映射
- `_mdict_{dict_id}_shard_{n}.json`：分片数据
- `_mdict_{dict_id}_resources.json`：资源映射（仅 MDD）
- `_mdict_{dict_id}_res_{hash}{ext}`：资源文件（仅 MDD）
- `_mdict_{dict_id}_style.css`：作用域 CSS（仅 CSS）

## 前端稳定接口（window.MD.API）
稳定契约详见：`docs/js-api.md`

核心能力（摘要）：
- `MD.API.init({ configPath, autoTokenize, targetContainer })`
- `MD.API.getDictionaries({ language, enabledOnly })`
- `MD.API.lookup(word, { dictionaryId, language, requestId })`
- `MD.API.ui.renderResult(...) / syncDictionarySelect(...) / scrollToTop(...)`

事件（DOM CustomEvent）：
- `md:ready` / `md:error` / `md:lookup`

并发规则：`lookup` 不保证返回顺序，建议用 `requestId` 实现 last-request-wins。

相关文档：
- `docs/README.md`
- `docs/js-api.md`
- `docs/events.md`
- `docs/ui-components.md`

## 脚本注入顺序（模板注入）
模板注入脚本顺序固定为：
1. `_mdict_style.css`
2. `_mdict_config.js`
3. `_mdict_tokenizer.js`
4. `_mdict_dictionary.js`
5. `_mdict_ui.js`
6. `_mdict_main.js`（最后加载）

随后会执行：
```html
<script>
  window.MDICT_FIELDS = /* ... */;
  if (window.MD && typeof window.MD.init === 'function') {
    window.MD.init({ autoTokenize: true });
  }
</script>
```

## 依赖与环境
- **MDX 解析**：依赖 `mdict-utils`（`检查环境` 会提示可用性）
- **MDD 解析**：优先使用 `mdict_query`，不可用时尝试 `docs/mdict-query-master/readmdict.py`

## 与 ListenSpeak 集成
ListenSpeak 模板会加载 `_mdict_*.js` 并使用 `window.MD.API`。若需要卡片内字典与分词，需先安装本插件。

相关链接：`../Anki_ListenSpeak/README.md`

## 故障排除
- **检查环境失败**：确认 `mdict-utils` 已安装并可被 Anki Python 识别
- **查词无结果**：确认辞典已启用且语言匹配
- **样式未生效**：检查是否已添加 CSS 资源并生成 `_mdict_{id}_style.css`
- **模板注入后使用旧样式**：如果你之前使用过模板注入功能，需要重新注入以使用 v2.0.0 的新 UI。详见：[模板注入迁移指南](docs/TEMPLATE_INJECTION_MIGRATION.md)

---

**最后更新**：2026-02-04
MDict Tokenizer 是一款 Anki 插件，用于在**卡片模板 WebView**中提供“分词 + 查词 + 渲染”的通用能力。它会把 MDX 字典预处理成可在前端高效查询的分片文件，并向模板侧暴露稳定接口：`window.MD.API`。

本 README 说明 `Anki_Mdict/` 这份插件的使用与开发；前端稳定接口的详细契约请务必阅读：`docs/js-api.md`。

## 适用场景

- 你希望在卡片背面做“点击分词后的 token 立即查词”。
- 你希望在模板里用原生 JS 调 `MD.API.lookup()` 获取 HTML，并按统一样式渲染。
- 你需要在多个笔记类型/多个字段上复用同一套“分词 + 查词”能力。

如果你主要用的是 ListenSpeak 的学习卡片，请同时参考：`../Anki_ListenSpeak/README.md`（ListenSpeak 的字典面板会调用 `window.MD` 能力）。

## 功能概览

### 1) 辞典管理（MDX 导入 + 顺序/启用）

- 在 Anki 中导入 `.mdx` 文件，预处理为前端可用的索引/分片数据。
- 按语言筛选辞典、拖拽调整顺序、勾选启用/禁用。
- 提供“快速试查”，用于验证字典是否可用。

入口：`工具 → MDict → 辞典管理...`

### 2) 分词配置（按语言）

- 支持按语言维护 tokenizer 配置（默认包含 `ja` / `en`）。
- 可配置：是否提取原型（lemma）、日语是否显示注音、英语是否显示音标。
- 可配置：该语言关联哪些辞典（决定查词候选集与顺序）。

入口：`工具 → MDict → 分词配置...`

### 3) 模板注入（把能力接到现有笔记类型）

插件可以对选定的笔记类型做“模板注入”，让某些字段启用分词/查词能力。

入口：`工具 → MDict → 模板注入...`

### 4) 前端稳定 API：`window.MD.API`

模板侧唯一稳定契约是 `window.MD.API`，它包含：

- `MD.API.init(options)`：加载配置、初始化状态与 tokenizer；成功后触发 `md:ready`
- `MD.API.getDictionaries(options?)`：枚举字典
- `MD.API.lookup(word, options?)`：查词（支持并发 requestId、首选字典等）
- `MD.API.ui.*`：渲染/滚动/字典选择器同步等 UI 工具
- DOM 事件：`md:ready`、`md:error`、`md:lookup`

详见：`docs/js-api.md`、`docs/events.md`、`docs/ui-components.md`。

## 安装

### 方式 A：从文件安装（面向一般用户）

如果你已经拿到打包好的插件文件（`.ankiaddon` 或 zip）：

1. 打开 Anki
2. `工具` → `附加组件` → `从文件安装`
3. 选择插件文件并重启 Anki

### 方式 B：从源码安装（开发/自用）

该插件的源码目录为：`Anki_Mdict/src/mdict_tokenizer/`。在本机安装时，你需要把它放到 Anki 的 `addons21` 目录下（目录位置可在 Anki 中通过 `工具 → 附加组件 → 查看文件` 打开）。

常见做法（以文件夹名为 `mdict_tokenizer` 为例）：

1. 找到 Anki 的附加组件目录（`addons21`）。
2. 复制或创建软链接：
   - 源码：`Anki_Mdict/src/mdict_tokenizer/`
   - 目标：`.../Anki2/addons21/mdict_tokenizer/`
3. 重启 Anki

完成后，你应在 `工具` 菜单看到 **MDict** 子菜单。

## 第一次使用（推荐流程）

### 1) 检查环境（MDX 依赖）

`工具 → MDict → 检查环境`

当前 MDX 解析依赖为 `mdict-utils`（由 `src/mdict_tokenizer/mdx_processor.py` 检测）。如果提示不可用，可先参考 `../tools/README.md` 在本机环境验证与安装依赖。

### 2) 导入 MDX 字典

`工具 → MDict → 辞典管理...` → `导入 MDX`

导入后，插件会在 Anki 的 `collection.media/` 目录写入预处理产物（文件命名以 `_mdict_{dict_id}_...` 为前缀），典型包括：

- `_mdict_{dict_id}_index.json`：索引（key → 分片位置）
- `_mdict_{dict_id}_shard_{n}.json`：分片数据（包含 entries）

同时，辞典元数据与启用/顺序信息会写入 `collection.media/_mdict_config.json`。

### 3) 配置分词器与关联辞典

`工具 → MDict → 分词配置...`

按语言选择（`ja` / `en`），然后：

- 勾选/取消“提取单词原型”
- 日语：可选“显示注音”
- 英语：可选“显示音标”
- 在“关联辞典”列表中勾选要参与查词的辞典
- 保存配置

### 4) 注入到笔记类型（让字段启用分词/查词）

`工具 → MDict → 模板注入...`

1. 选择笔记类型
2. 勾选要启用的字段，并为每个字段指定语言（`ja` / `en`）
3. 点击“注入”

注入后，打开对应笔记类型的卡片，字段内容会按配置进行分词，并可触发查词 UI。

## 配置与文件

### 1) `_mdict_config.json`（结构性配置）

配置文件保存在 Anki 媒体目录：`collection.media/_mdict_config.json`（由 `src/mdict_tokenizer/config.py` 管理）。

主要包含：

- `dictionaries[]`：辞典列表与元数据（语言、顺序、是否有资源、css 文件等）
- `tokenizers{}`：按语言的 tokenizer 设置与关联辞典 ID 列表
- `injections[]`：记录模板注入的笔记类型与字段

建议通过插件 UI 修改，而不是手工编辑。

### 2) 注入到模板的静态资源（脚本/样式）

插件会将 `src/mdict_tokenizer/media/` 下的 `_mdict_*.js` / `_mdict_style.css` 等文件复制到 `collection.media/`，供卡片模板加载。

脚本注入顺序（重要，入口脚本最后加载）：

1. `_mdict_style.css`
2. `_mdict_config.js`
3. `_mdict_tokenizer.js`
4. `_mdict_dictionary.js`
5. `_mdict_ui.js`
6. `_mdict_main.js`（最后加载）

详见：`docs/README.md`。

## 模板侧使用：最小查词示例

下面示例展示如何只依赖稳定接口 `window.MD.API` 完成“输入 → 查词 → 渲染”。更完整版本见：`docs/README.md`。

```html
<div id="mdict-root">
  <input id="mdict-word" placeholder="输入要查的词" />
  <button id="mdict-go">查词</button>
  <div id="mdict-result"></div>
</div>

<script>
  (function () {
    function onReady(fn) {
      document.addEventListener('md:ready', function () { fn(); }, { once: true });
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

## 与 ListenSpeak 的关系

- ListenSpeak 的模板包含字典面板与分词 UI，并会检测/调用 `window.MD` 能力。
- 如果你希望按“稳定面”集成，而非依赖内部实现，请按 `docs/js-api.md` 中的“ListenSpeak 迁移最小调用顺序（摘要）”接入 `window.MD.API`。

## 开发与测试

### 测试

在仓库根目录运行：

```bash
python -m pytest Anki_Mdict/tests/ -v --tb=short
```

### 代码结构

```
Anki_Mdict/
└── src/mdict_tokenizer/
    ├── __init__.py              # 插件入口（菜单、profile hook、安装 media）
    ├── config.py                # _mdict_config.json 读写
    ├── mdx_processor.py         # MDX 提取与分片生成（依赖 mdict-utils）
    ├── dict_manager.py          # 辞典导入/管理逻辑
    ├── template_injector.py     # 模板注入器（生成注入脚本/顺序）
    ├── tokenizer_config.py      # 分词配置服务
    ├── media/                   # 前端 JS/CSS 资产（复制到 collection.media）
    └── ui/                      # 对话框 UI
```

---

最后更新：2026-02-04

(function () {
  "use strict";

  if (!window.MD) {
    window.MD = {};
  }

  var historyKey = "mdict_history";
  var popupEl = null;
  var panelEl = null;
  var modalEl = null;
  var overlayEl = null;

  function createPanelElements() {
    var panel = document.createElement('div');
    panel.className = 'md-panel';

    var header = document.createElement('div');
    header.className = 'md-panel-header';

    var title = document.createElement('span');
    title.className = 'md-panel-title';
    title.textContent = '词典';

    var searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.className = 'md-panel-search-input';
    searchInput.placeholder = '搜索词条...';

    var searchBtn = document.createElement('button');
    searchBtn.type = 'button';
    searchBtn.className = 'md-panel-search-btn';
    searchBtn.textContent = '搜索';

    var controls = document.createElement('div');
    controls.className = 'md-panel-controls';

    var dictSelectWrapper = document.createElement('div');
    dictSelectWrapper.className = 'md-panel-dict-select-wrapper';

    var dictSelect = document.createElement('select');
    dictSelect.className = 'md-panel-dict-select';

    var counter = document.createElement('span');
    counter.className = 'md-panel-counter md-hidden';

    var closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.className = 'md-panel-close';
    closeBtn.textContent = '×';

    header.appendChild(title);
    header.appendChild(searchInput);
    header.appendChild(searchBtn);
    dictSelectWrapper.appendChild(dictSelect);
    controls.appendChild(dictSelectWrapper);
    controls.appendChild(counter);
    controls.appendChild(closeBtn);
    header.appendChild(controls);

    var content = document.createElement('div');
    content.className = 'md-panel-content';

    var contentBody = document.createElement('div');
    contentBody.className = 'md-panel-content-body';

    var hotzoneLeft = document.createElement('div');
    hotzoneLeft.className = 'md-hotzone md-hotzone-left';
    hotzoneLeft.setAttribute('data-dir', 'prev');

    var hotzoneRight = document.createElement('div');
    hotzoneRight.className = 'md-hotzone md-hotzone-right';
    hotzoneRight.setAttribute('data-dir', 'next');

    content.appendChild(contentBody);
    content.appendChild(hotzoneLeft);
    content.appendChild(hotzoneRight);

    panel.appendChild(header);
    panel.appendChild(content);

    return {
      panel: panel,
      header: header,
      title: title,
      searchInput: searchInput,
      searchBtn: searchBtn,
      controls: controls,
      dictSelect: dictSelect,
      counter: counter,
      closeBtn: closeBtn,
      content: content,
      contentBody: contentBody,
      hotzoneLeft: hotzoneLeft,
      hotzoneRight: hotzoneRight
    };
  }

  function ensurePanel() {
    if (panelEl) {
      return panelEl;
    }

    var mode = window.MD.UI.getMode();
    var elements = createPanelElements();
    var container;

    if (mode === 'embedded') {
      container = window.MD.UI.container;
      if (container) {
        elements.closeBtn.className = 'md-panel-close md-hidden';
        container.appendChild(elements.panel);
        panelEl = elements.panel;
      } else {
        if (window.console && window.console.warn) {
          console.warn('[MD.UI] 嵌入式容器不存在，回退到弹窗模式');
        }
        window.MD.UI.mode = 'modal';
        return ensurePanel();
      }
    } else {
      overlayEl = document.createElement('div');
      overlayEl.className = 'md-modal-overlay md-modal-hidden';

      modalEl = document.createElement('div');
      modalEl.className = 'md-modal md-modal-medium md-modal-hidden';

      modalEl.appendChild(elements.panel);

      document.body.appendChild(overlayEl);
      document.body.appendChild(modalEl);

      panelEl = elements.panel;
    }

    window.MD.UI.panel = panelEl;
    window.MD.UI.elements = elements;

    return panelEl;
  }

  function getHistory() {
    var raw = localStorage.getItem(historyKey);
    if (!raw) {
      return [];
    }
    try {
      return JSON.parse(raw) || [];
    } catch (error) {
      return [];
    }
  }

  function saveHistory(entries) {
    localStorage.setItem(historyKey, JSON.stringify(entries));
  }

  function ensurePopup() {
    if (popupEl) {
      return popupEl;
    }
    popupEl = document.createElement("div");
    popupEl.className = "md-popup md-popup-hidden";

    var header = document.createElement("div");
    header.className = "md-popup-header";
    var title = document.createElement("div");
    title.className = "md-popup-title";
    var closeBtn = document.createElement("button");
    closeBtn.className = "md-popup-close";
    closeBtn.textContent = "×";
    closeBtn.addEventListener("click", function () {
      hidePopup();
    });
    header.appendChild(title);
    header.appendChild(closeBtn);

    var controls = document.createElement("div");
    controls.className = "md-popup-controls";
    var input = document.createElement("input");
    input.type = "text";
    input.placeholder = "输入单词查词";
    input.className = "md-popup-input";
    var searchBtn = document.createElement("button");
    searchBtn.textContent = "搜索";
    searchBtn.className = "md-popup-search";
    searchBtn.addEventListener("click", function () {
      var term = input.value.trim();
      if (!term) {
        return;
      }
      lookupAndRender(term, null, null);
    });
    controls.appendChild(input);
    controls.appendChild(searchBtn);

    var dictSwitch = document.createElement("select");
    dictSwitch.className = "md-popup-dict-switch";
    dictSwitch.addEventListener("change", function () {
      var term = input.value.trim();
      if (!term) {
        return;
      }
      lookupAndRender(term, dictSwitch.value || null, null);
    });
    controls.appendChild(dictSwitch);

    var content = document.createElement("div");
    content.className = "md-popup-content";
    bindEntryLinks(content, input, dictSwitch);

    popupEl.appendChild(header);
    popupEl.appendChild(controls);
    popupEl.appendChild(content);

    document.body.appendChild(popupEl);
    return popupEl;
  }

  function updateDictOptions(selectEl) {
    selectEl.innerHTML = "";
    var dicts = window.MD.Dictionary.getDictionaries();
    var defaultOption = document.createElement("option");
    defaultOption.value = "";
    defaultOption.textContent = "全部辞典";
    selectEl.appendChild(defaultOption);
    dicts.forEach(function (dict) {
      var option = document.createElement("option");
      option.value = dict.id;
      option.textContent = dict.name;
      selectEl.appendChild(option);
    });
  }

  function extractEntryWord(link) {
    if (!link) return "";
    var href = link.getAttribute("href") || "";
    if (!href || href.indexOf("entry://") !== 0) {
      href = link.href || "";
    }
    if (!href || href.indexOf("entry://") !== 0) {
      return "";
    }
    var word = href.slice(8);
    if (!word) return "";
    try {
      word = decodeURIComponent(word);
    } catch (error) {
      word = String(word);
    }
    return word.trim();
  }

  function bindEntryLinks(container, input, dictSwitch) {
    if (!container || container.dataset.mdictEntryBound === "1") {
      return;
    }
    container.dataset.mdictEntryBound = "1";
    container.addEventListener("click", function (event) {
      var target = event.target;
      var link = null;
      var word = "";
      var dictId = null;
      var href = "";
      if (target && target.closest) {
        link = target.closest('a[href^="entry://"]');
      } else if (target && target.tagName === "A") {
        href = target.getAttribute("href") || "";
        if (href.indexOf("entry://") === 0) {
          link = target;
        }
      }
      if (!link) {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      word = extractEntryWord(link);
      if (!word) {
        return;
      }
      if (input) {
        input.value = word;
        input.focus();
      }
      dictId = dictSwitch ? dictSwitch.value || null : null;
      lookupAndRender(word, dictId, null);
    });
  }

  function getLastLookupLanguage() {
    return window.MD && window.MD.State ? window.MD.State.lastLookupLanguage : null;
  }

  function setLastLookupLanguage(language) {
    if (!language) {
      return;
    }
    if (!window.MD.State) {
      window.MD.State = {};
    }
    window.MD.State.lastLookupLanguage = language;
  }

  function lookupAndRender(word, dictionaryId, prefixHtml, options) {
    var popup = ensurePopup();
    var content = popup.querySelector(".md-popup-content");
    var titleEl = popup.querySelector(".md-popup-title");
    var dictSwitch = popup.querySelector(".md-popup-dict-switch");
    var dictOptions = null;
    var dictOptionIndex = 0;
    var lastLanguage = null;
    content.innerHTML = "<div class=\"md-loading\">加载中...</div>";
    var lookupOptions = options || {};
    if (!lookupOptions.language) {
      lastLanguage = getLastLookupLanguage();
      if (lastLanguage) {
        lookupOptions.language = lastLanguage;
      }
    }
    setLastLookupLanguage(lookupOptions.language);
    window.MD.Dictionary.lookup(word, dictionaryId, lookupOptions).then(function (result) {
      if (!result.found) {
        content.innerHTML = "<div class=\"md-empty\">未找到释义</div>";
        content.scrollTop = 0;
        if (titleEl) {
          titleEl.textContent = word;
        }
        return;
      }
      var html = fixCssReferences(result.definition, result.dictionaryId);
      var fullHtml = prefixHtml ? prefixHtml + html : html;
      content.innerHTML = "<div class=\"mdict-" + result.dictionaryId + "\">" + fullHtml + "</div>";
      content.scrollTop = 0;
      if (dictSwitch && result.dictionaryId) {
        dictOptions = dictSwitch.options;
        for (dictOptionIndex = 0; dictOptionIndex < dictOptions.length; dictOptionIndex++) {
          if (dictOptions[dictOptionIndex].value === result.dictionaryId) {
            dictSwitch.value = result.dictionaryId;
            break;
          }
        }
      }
      if (titleEl) {
        titleEl.textContent = result.dictionaryName || word;
      }
      window.MD.History.add({
        word: word,
        dictionaryId: result.dictionaryId,
        timestamp: Date.now(),
        source: "manual",
      });
      if (window.MD && typeof window.MD.emit === "function") {
        window.MD.emit("md:lookup", { word: word, result: result });
      }
    });
  }

  function fixCssReferences(html, dictionaryId) {
    if (!html || !dictionaryId) return html || "";
    var config = window.MD && window.MD.State ? window.MD.State.config : null;
    if (!config || !config.dictionaries) return html;
    var dict = null;
    var i = 0;
    for (i = 0; i < config.dictionaries.length; i++) {
      if (config.dictionaries[i].id === dictionaryId) {
        dict = config.dictionaries[i];
        break;
      }
    }
    if (!dict || !dict.resources || !dict.resources.cssFile) return html;
    var actualCss = dict.resources.cssFile;
    // 替换 <link href="xxx.css">
    html = html.replace(/<link[^>]+href=["']([^"']+\.css)["'][^>]*>/gi, function(match, cssPath) {
      return match.replace(cssPath, actualCss);
    });
    // 替换 @import url("xxx.css")
    html = html.replace(/@import\s+url\(["']?([^"')]+\.css)["']?\)/gi, function(match, cssPath) {
      return match.replace(cssPath, actualCss);
    });
    return html;
  }

  function showPopup(content, options) {
    var popup = ensurePopup();
    var titleEl = popup.querySelector(".md-popup-title");
    var contentEl = popup.querySelector(".md-popup-content");
    var dictSwitch = popup.querySelector(".md-popup-dict-switch");
    var config = window.MD.Config ? window.MD.Config.getAll() : null;
    var height = (options && options.height) || (config ? config.popupHeight : "medium");
    var dictionaryId = options && options.dictionaryId;

    popup.className = "md-popup";
    popup.classList.add("md-popup-" + height);
    titleEl.textContent = (options && options.title) || "辞典";
    // 修复 CSS 引用
    contentEl.innerHTML = fixCssReferences(content, dictionaryId);
    updateDictOptions(dictSwitch);
    popup.classList.remove("md-popup-hidden");
    return popup;
  }

  function hidePopup() {
    if (!popupEl) {
      return;
    }
    popupEl.classList.add("md-popup-hidden");
  }

  function applyFontSize(config) {
    if (!config || !config.fontSize) {
      return;
    }
    document.documentElement.style.setProperty("--md-font-size", config.fontSize + "px");
  }

  function applyConfig(config) {
    applyFontSize(config);
    if (window.MD && window.MD.Tokenizer && window.MD.Tokenizer.updateTokenDisplay) {
      window.MD.Tokenizer.updateTokenDisplay(config);
    }
  }

  function createSelect(options, value) {
    var select = document.createElement("select");
    options.forEach(function (option) {
      var item = document.createElement("option");
      item.value = option.value;
      item.textContent = option.label;
      select.appendChild(item);
    });
    select.value = value;
    return select;
  }

  function createRow(labelText, control) {
    var row = document.createElement("label");
    row.className = "md-config-row";
    var title = document.createElement("span");
    title.className = "md-config-label";
    title.textContent = labelText;
    row.appendChild(title);
    row.appendChild(control);
    return row;
  }

  function buildDictionarySection(config) {
    var wrapper = document.createElement("div");
    wrapper.className = "md-config-section";
    var title = document.createElement("div");
    title.className = "md-config-subtitle";
    title.textContent = "启用辞典";
    wrapper.appendChild(title);

    var dicts = window.MD.Dictionary.getDictionaries();
    var enabled = config.enabledDictionaries && config.enabledDictionaries.length
      ? config.enabledDictionaries
      : dicts.map(function (dict) { return dict.id; });
    if (!config.enabledDictionaries || !config.enabledDictionaries.length) {
      config.enabledDictionaries = enabled;
      window.MD.Config.set("enabledDictionaries", enabled);
    }

    dicts.forEach(function (dict) {
      var item = document.createElement("label");
      item.className = "md-config-dict-item";
      var checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = enabled.indexOf(dict.id) !== -1;
      checkbox.addEventListener("change", function () {
        var selected = [];
        wrapper.querySelectorAll("input[type=checkbox]").forEach(function (box, index) {
          if (box.checked && dicts[index]) {
            selected.push(dicts[index].id);
          }
        });
        window.MD.Config.set("enabledDictionaries", selected);
      });
      var label = document.createElement("span");
      label.textContent = dict.name;
      item.appendChild(checkbox);
      item.appendChild(label);
      wrapper.appendChild(item);
    });
    return wrapper;
  }

  function showConfig() {
    var panel = document.querySelector(".md-config-panel");
    if (panel) {
      panel.classList.toggle("md-panel-hidden");
      return;
    }
    panel = document.createElement("div");
    panel.className = "md-config-panel";
    var config = window.MD.Config.getAll();

    var title = document.createElement("div");
    title.className = "md-config-title";
    title.textContent = "卡片配置";
    panel.appendChild(title);

    panel.appendChild(buildDictionarySection(config));

    var readingSelect = createSelect(
      [
        { value: "none", label: "不显示" },
        { value: "lookup", label: "仅查词后" },
        { value: "all", label: "显示全部" },
      ],
      config.readingMode
    );
    readingSelect.addEventListener("change", function () {
      window.MD.Config.set("readingMode", readingSelect.value);
      applyConfig(window.MD.Config.getAll());
    });
    panel.appendChild(createRow("注音/音标显示", readingSelect));

    var lemmaToggle = document.createElement("input");
    lemmaToggle.type = "checkbox";
    lemmaToggle.checked = !!config.extractLemma;
    lemmaToggle.addEventListener("change", function () {
      window.MD.Config.set("extractLemma", lemmaToggle.checked);
    });
    panel.appendChild(createRow("提取原型", lemmaToggle));

    var fontSizeInput = document.createElement("input");
    fontSizeInput.type = "number";
    fontSizeInput.min = "12";
    fontSizeInput.max = "32";
    fontSizeInput.step = "2";
    fontSizeInput.value = config.fontSize;
    fontSizeInput.addEventListener("change", function () {
      window.MD.Config.set("fontSize", parseInt(fontSizeInput.value, 10) || 16);
      applyConfig(window.MD.Config.getAll());
    });
    panel.appendChild(createRow("字体大小", fontSizeInput));

    var clickSelect = createSelect(
      [
        { value: "click", label: "单击查词" },
        { value: "longpress", label: "长按查词" },
      ],
      config.clickBehavior
    );
    clickSelect.addEventListener("change", function () {
      window.MD.Config.set("clickBehavior", clickSelect.value);
    });
    panel.appendChild(createRow("分词点击", clickSelect));

    var historySelect = createSelect(
      [
        { value: "10", label: "10 条" },
        { value: "50", label: "50 条" },
        { value: "100", label: "100 条" },
      ],
      String(config.historyLimit)
    );
    historySelect.addEventListener("change", function () {
      window.MD.Config.set("historyLimit", parseInt(historySelect.value, 10) || 50);
    });
    panel.appendChild(createRow("历史记录数量", historySelect));

    var heightSelect = createSelect(
      [
        { value: "small", label: "小" },
        { value: "medium", label: "中" },
        { value: "large", label: "大" },
        { value: "full", label: "全屏" },
      ],
      config.popupHeight
    );
    heightSelect.addEventListener("change", function () {
      window.MD.Config.set("popupHeight", heightSelect.value);
    });
    panel.appendChild(createRow("弹窗高度", heightSelect));

    var styleSelect = createSelect(
      [
        { value: "underline", label: "下划线" },
        { value: "background", label: "背景色" },
        { value: "none", label: "无" },
      ],
      config.tokenStyle
    );
    styleSelect.addEventListener("change", function () {
      window.MD.Config.set("tokenStyle", styleSelect.value);
      applyConfig(window.MD.Config.getAll());
    });
    panel.appendChild(createRow("分词样式", styleSelect));

    applyConfig(config);
    document.body.appendChild(panel);
  }

  function showHistory() {
    var history = getHistory();
    var panel = document.querySelector(".md-history-panel");
    if (!panel) {
      panel = document.createElement("div");
      panel.className = "md-history-panel";
      document.body.appendChild(panel);
    }
    if (!history.length) {
      panel.innerHTML = "<div class=\"md-empty\">暂无历史</div>";
      return;
    }
    var html = history
      .slice(0, 100)
      .map(function (entry) {
        return "<div class=\"md-history-item\">" + entry.word + "</div>";
      })
      .join("");
    panel.innerHTML = html;
  }

  function lookupFromToken(word, dictionaryId, prefixHtml, language) {
    var popup = showPopup("<div class=\"md-loading\">加载中...</div>", { title: word });
    var input = popup.querySelector(".md-popup-input");
    if (input) {
      input.value = word;
      input.focus();
    }
    setLastLookupLanguage(language);
    lookupAndRender(word, dictionaryId, prefixHtml, { language: language });
  }

  /**
   * MD.UI - 用户界面模块
   * 
   * 支持两种显示模式：
   * - 'embedded': 嵌入式模式，渲染到 #mdict-panel 容器内
   * - 'modal': 弹窗模式，创建居中浮层（默认回退）
   * 
   * 容器检测逻辑：
   * 1. 初始化时自动检测 #mdict-panel
   * 2. 支持延迟设置容器（setContainer）
   */
  window.MD.UI = {
    // 显示模式: 'embedded' | 'modal' | null
    mode: null,
    
    // 容器元素引用（嵌入式模式）
    container: null,
    
    // 面板元素引用
    panel: null,
    
    // 是否已初始化
    _initialized: false,
    
    /**
     * 初始化 UI 模块
     * @param {Object} options - 初始化选项
     * @param {string} options.containerId - 容器 ID（可选，默认 'mdict-panel'）
     * @returns {boolean} 是否成功初始化
     */
    init: function(options) {
      var opts = options || {};
      var containerId = opts.containerId || 'mdict-panel';
      
      // 检测容器
      this.detectContainer(containerId);
      
      this._initialized = true;
      
      // 输出初始化信息
      if (window.console && window.console.log) {
        console.log('[MD.UI] 初始化完成, mode=' + this.mode);
      }
      
      return true;
    },
    
    /**
     * 检测容器是否存在
     * @param {string} containerId - 容器 ID（可选，默认 'mdict-panel'）
     * @returns {boolean} 是否检测到容器
     */
    detectContainer: function(containerId) {
      var id = containerId || 'mdict-panel';
      var container = document.getElementById(id);
      
      if (container) {
        this.mode = 'embedded';
        this.container = container;
        return true;
      } else {
        this.mode = 'modal';
        this.container = null;
        return false;
      }
    },
    
    /**
     * 延迟设置容器（支持容器后加载场景）
     * @param {string} containerId - 容器 ID
     * @returns {boolean} 是否成功设置
     */
    setContainer: function(containerId) {
      if (!containerId) {
        return false;
      }
      
      var container = document.getElementById(containerId);
      if (container) {
        this.mode = 'embedded';
        this.container = container;
        
        if (window.console && window.console.log) {
          console.log('[MD.UI] 容器已设置, mode=embedded, containerId=' + containerId);
        }
        
        return true;
      }
      
      return false;
    },
    
    /**
     * 获取当前模式
     * @returns {string} 'embedded' | 'modal'
     */
    getMode: function() {
      // 如果未初始化，先执行检测
      if (!this._initialized) {
        this.detectContainer();
      }
      return this.mode;
    },
    
    /**
     * 判断是否为嵌入式模式
     * @returns {boolean}
     */
    isEmbedded: function() {
      return this.getMode() === 'embedded';
    },
    
    /**
     * 判断是否为弹窗模式
     * @returns {boolean}
     */
    isModal: function() {
      return this.getMode() === 'modal';
    },
    
    ensurePanel: ensurePanel,
    showPopup: showPopup,
    hidePopup: hidePopup,
    showConfig: showConfig,
    showHistory: showHistory,
    lookupFromToken: lookupFromToken
  };

  window.MD.History = {
    add: function (entry) {
      var history = getHistory();
      history.unshift(entry);
      var limit = window.MD.Config ? window.MD.Config.get("historyLimit") : 50;
      saveHistory(history.slice(0, limit));
    },
    getAll: function () {
      return getHistory();
    },
    clear: function () {
      saveHistory([]);
    },
  };
})();

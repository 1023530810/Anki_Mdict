(function () {
  "use strict";

  if (!window.MD) {
    window.MD = {};
  }

  var historyKey = "mdict_history";
  var popupEl = null;

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

  function lookupAndRender(word, dictionaryId, prefixHtml) {
    var popup = ensurePopup();
    var content = popup.querySelector(".md-popup-content");
    var titleEl = popup.querySelector(".md-popup-title");
    content.innerHTML = "<div class=\"md-loading\">加载中...</div>";
    window.MD.Dictionary.lookup(word, dictionaryId).then(function (result) {
      if (!result.found) {
        content.innerHTML = "<div class=\"md-empty\">未找到释义</div>";
        if (titleEl) {
          titleEl.textContent = word;
        }
        return;
      }
      var html = fixCssReferences(result.definition, result.dictionaryId);
      var fullHtml = prefixHtml ? prefixHtml + html : html;
      content.innerHTML = "<div class=\"mdict-" + result.dictionaryId + "\">" + fullHtml + "</div>";
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
    for (var i = 0; i < config.dictionaries.length; i++) {
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

    popup.className = "md-popup";
    popup.classList.add("md-popup-" + height);
    titleEl.textContent = (options && options.title) || "辞典";
    // 修复 CSS 引用
    var dictionaryId = options && options.dictionaryId;
    contentEl.innerHTML = fixCssReferences(content, dictionaryId);
    updateDictOptions(dictSwitch);
    popup.classList.remove("md-popup-hidden");
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

  function lookupFromToken(word, dictionaryId, prefixHtml) {
    var popup = showPopup("<div class=\"md-loading\">加载中...</div>", { title: word });
    var input = popup.querySelector(".md-popup-input");
    if (input) {
      input.value = word;
      input.focus();
    }
    lookupAndRender(word, dictionaryId, prefixHtml);
  }

  window.MD.UI = {
    showPopup: showPopup,
    hidePopup: hidePopup,
    showConfig: showConfig,
    showHistory: showHistory,
    lookupFromToken: lookupFromToken,
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

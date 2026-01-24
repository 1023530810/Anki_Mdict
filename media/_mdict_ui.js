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
      lookupAndRender(term, null);
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
      lookupAndRender(term, dictSwitch.value || null);
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

  function lookupAndRender(word, dictionaryId) {
    var popup = ensurePopup();
    var content = popup.querySelector(".md-popup-content");
    content.innerHTML = "<div class=\"md-loading\">加载中...</div>";
    window.MD.Dictionary.lookup(word, dictionaryId).then(function (result) {
      if (!result.found) {
        content.innerHTML = "<div class=\"md-empty\">未找到释义</div>";
        return;
      }
      content.innerHTML = "<div class=\"mdict-" + result.dictionaryId + "\">" + result.definition + "</div>";
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
    contentEl.innerHTML = content;
    updateDictOptions(dictSwitch);
    popup.classList.remove("md-popup-hidden");
  }

  function hidePopup() {
    if (!popupEl) {
      return;
    }
    popupEl.classList.add("md-popup-hidden");
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

    panel.innerHTML =
      "<div class=\"md-config-title\">卡片配置</div>" +
      "<label>字体大小<input type=\"number\" min=\"12\" max=\"32\" step=\"2\" value=\"" +
      config.fontSize +
      "\"></label>" +
      "<label>分词样式<select><option value=\"underline\">下划线</option><option value=\"background\">背景色</option><option value=\"none\">无</option></select></label>";

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

  window.MD.UI = {
    showPopup: showPopup,
    hidePopup: hidePopup,
    showConfig: showConfig,
    showHistory: showHistory,
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

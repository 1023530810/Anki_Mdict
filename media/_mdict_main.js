(function () {
  "use strict";

  if (!window.MD) {
    window.MD = {};
  }

  function fetchJson(path) {
    if (window.fetch) {
      return fetch(path).then(function (response) {
        if (!response.ok) {
          throw new Error("CONFIG_NOT_FOUND");
        }
        return response.json();
      });
    }
    return new Promise(function (resolve, reject) {
      var xhr = new XMLHttpRequest();
      xhr.open("GET", path, true);
      xhr.onreadystatechange = function () {
        if (xhr.readyState !== 4) {
          return;
        }
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText));
          } catch (error) {
            reject(error);
          }
        } else {
          reject(new Error("CONFIG_NOT_FOUND"));
        }
      };
      xhr.send();
    });
  }

  function emit(name, detail) {
    document.dispatchEvent(new CustomEvent(name, { detail: detail }));
  }

  function init(options) {
    var opts = options || {};
    var configPath = opts.configPath || "_mdict_config.json";
    var autoTokenize = opts.autoTokenize !== false;
    var targetContainer = opts.targetContainer || null;

    return fetchJson(configPath)
      .then(function (config) {
        window.MD.State = {
          config: config || {},
          targetContainer: targetContainer,
        };
        return initTokenizers(config);
      })
      .then(function () {
        if (autoTokenize) {
          return tokenizeFields();
        }
        return null;
      })
      .then(function () {
        emit("md:ready", {});
      })
      .catch(function (error) {
        emit("md:error", { code: error.message || "TOKENIZER_LOAD_FAILED", message: error.message || "初始化失败" });
        throw error;
      });
  }

  function initTokenizers(config) {
    var tokenizers = config.tokenizers || {};
    var tasks = [];
    Object.keys(tokenizers).forEach(function (language) {
      tasks.push(window.MD.Tokenizer.init(language));
    });
    return Promise.all(tasks);
  }

  function tokenizeFields() {
    var fields = window.MDICT_FIELDS || [];
    var promises = [];
    if (fields.length) {
      fields.forEach(function (field) {
        var selector = ".mdict-field[data-mdict-field='" + field.name + "']";
        var elements = document.querySelectorAll(selector);
        elements.forEach(function (element) {
          promises.push(window.MD.Tokenizer.tokenizeElement(element, field.language));
        });
      });
    }
    if (!fields.length && window.MD.State && window.MD.State.targetContainer) {
      var container = document.querySelector(window.MD.State.targetContainer);
      if (container) {
        promises.push(window.MD.Tokenizer.tokenizeElement(container, "ja"));
      }
    }
    return Promise.all(promises);
  }

  function handleTokenClick(token, element) {
    var config = window.MD.Config ? window.MD.Config.getAll() : { extractLemma: true };
    var word = config.extractLemma ? token.lemma || token.surface : token.surface;
    window.MD.Dictionary.lookup(word).then(function (result) {
      if (!result.found) {
        window.MD.UI.showPopup("<div class=\"md-empty\">未找到释义</div>", {
          title: word,
        });
        return;
      }
      window.MD.UI.showPopup(result.definition, {
        title: result.dictionaryName || word,
        showDictSwitch: true,
      });
      emit("md:lookup", { word: word, result: result });
    });
  }

  window.MD.init = init;
  window.MD.emit = emit;
  window.MD.handleTokenClick = handleTokenClick;
})();

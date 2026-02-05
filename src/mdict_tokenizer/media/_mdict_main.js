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

  function getFieldLanguages(fields) {
    var languageMap = {};
    if (!fields || !fields.length) {
      return [];
    }
    fields.forEach(function (field) {
      if (!field || !field.name || !field.language) {
        return;
      }
      var selector = ".mdict-field[data-mdict-field='" + field.name + "']";
      if (document.querySelector(selector)) {
        languageMap[field.language] = true;
      }
    });
    return Object.keys(languageMap);
  }

  function getInitLanguages(config) {
    var tokenizers = config.tokenizers || {};
    var fieldLanguages = getFieldLanguages(window.MDICT_FIELDS || []);
    var languages = [];
    Object.keys(tokenizers).forEach(function (language) {
      var tokenizer = tokenizers[language] || {};
      if (!tokenizer.dictionaryIds || !tokenizer.dictionaryIds.length) {
        return;
      }
      if (fieldLanguages.indexOf(language) === -1) {
        return;
      }
      languages.push(language);
    });
    return languages;
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
    var initLanguages = getInitLanguages(config);
    var tasks = [];
    if (window.MD.State) {
      window.MD.State.initLanguages = initLanguages;
    }
    initLanguages.forEach(function (language) {
      if (tokenizers[language]) {
        tasks.push(window.MD.Tokenizer.init(language));
      }
    });
    return Promise.all(tasks);
  }

  function tokenizeFields() {
    var fields = window.MDICT_FIELDS || [];
    var promises = [];
    var initLanguages = [];
    var container = null;
    if (window.MD.State && window.MD.State.initLanguages) {
      initLanguages = window.MD.State.initLanguages;
    }
    if (fields.length) {
      fields.forEach(function (field) {
        if (initLanguages.length && initLanguages.indexOf(field.language) === -1) {
          return;
        }
        var selector = ".mdict-field[data-mdict-field='" + field.name + "']";
        var elements = document.querySelectorAll(selector);
        elements.forEach(function (element) {
          promises.push(window.MD.Tokenizer.tokenizeElement(element, field.language));
        });
      });
    }
    if (!fields.length && window.MD.State && window.MD.State.targetContainer) {
      container = document.querySelector(window.MD.State.targetContainer);
      if (container && initLanguages.indexOf("ja") !== -1) {
        promises.push(window.MD.Tokenizer.tokenizeElement(container, "ja"));
      }
    }
    return Promise.all(promises);
  }

  function handleTokenClick(token, element) {
    var config = window.MD.Config ? window.MD.Config.getAll() : { extractLemma: true };
    var word = config.extractLemma ? token.lemma || token.surface : token.surface;
    var prefixHtml = "";
    var language = null;
    var fieldEl = null;
    if (element && element.closest) {
      fieldEl = element.closest(".mdict-field");
    }
    if (fieldEl) {
      language = fieldEl.getAttribute("data-mdict-lang") || null;
    }
    if (config.readingMode === "lookup") {
      if (token.reading) {
        prefixHtml += "<div class=\"md-token-reading\">" + token.reading + "</div>";
      }
      if (token.ipa) {
        prefixHtml += "<div class=\"md-token-ipa\">" + token.ipa + "</div>";
      }
    }
    window.MD.UI.lookupFromToken(word, null, prefixHtml, language);
  }

  function supportsLanguage(dict, language) {
    if (!language) {
      return true;
    }
    if (!dict) {
      return false;
    }
    if (dict.language) {
      return dict.language === language;
    }
    if (dict.languages && dict.languages.length) {
      return dict.languages.indexOf(language) !== -1;
    }
    return false;
  }

  function getEnabledDictionaryIds(allDicts) {
    var config = window.MD && window.MD.Config ? window.MD.Config.getAll() : null;
    var enabled = config && config.enabledDictionaries ? config.enabledDictionaries.slice() : [];
    if (!enabled.length) {
      enabled = (allDicts || []).map(function (dict) {
        return dict.id;
      });
    }
    return enabled;
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
    html = html.replace(/<link[^>]+href=["']([^"']+\.css)["'][^>]*>/gi, function (match, cssPath) {
      return match.replace(cssPath, actualCss);
    });
    // 替换 @import url("xxx.css")
    html = html.replace(/@import\s+url\(["']?([^"')]+\.css)["']?\)/gi, function (match, cssPath) {
      return match.replace(cssPath, actualCss);
    });
    return html;
  }

  function normalizeLookupResult(result, requestId) {
    var normalized = result || { found: false };
    var contentHtml = normalized.contentHtml || normalized.definition || "";
    if (contentHtml) {
      normalized.contentHtml = contentHtml;
      if (!normalized.definition) {
        normalized.definition = contentHtml;
      }
    }
    if (typeof requestId !== "undefined") {
      normalized.requestId = requestId;
    }
    return normalized;
  }

  function renderResult(container, result, options) {
    if (!container) {
      return;
    }
    var opts = options || {};
    var emptyHtml = opts.emptyHtml || "<div class=\"md-empty\">未找到释义</div>";
    var errorHtml = opts.errorHtml || "<div class=\"md-error\">查询失败</div>";
    var prefixHtml = opts.prefixHtml || "";
    var normalized = normalizeLookupResult(result, result ? result.requestId : undefined);

    if (!normalized.found) {
      if (normalized.error) {
        container.innerHTML = errorHtml;
      } else {
        container.innerHTML = emptyHtml;
      }
      return;
    }

    var html = fixCssReferences(normalized.contentHtml || "", normalized.dictionaryId);
    var fullHtml = prefixHtml ? prefixHtml + html : html;
    container.innerHTML = "<div class=\"mdict-" + normalized.dictionaryId + "\">" + fullHtml + "</div>";
  }

  function syncDictionarySelect(selectElOrContainer, dictionaryId, dicts, options) {
    if (!selectElOrContainer) {
      return;
    }
    var opts = options || {};
    var activeClass = opts.activeClass || "active";
    if (selectElOrContainer.tagName === "SELECT") {
      selectElOrContainer.value = dictionaryId || "";
      return;
    }

    var labelEl = opts.labelEl || null;
    var menuEl = opts.menuEl || null;
    var selected = null;
    var i = 0;
    var activeItem = null;

    if (dicts && dicts.length && dictionaryId) {
      for (i = 0; i < dicts.length; i++) {
        if (dicts[i].id === dictionaryId) {
          selected = dicts[i];
          break;
        }
      }
    }

    if (selectElOrContainer.dataset) {
      selectElOrContainer.dataset.selectedId = dictionaryId || "";
    }

    if (labelEl) {
      labelEl.textContent = selected ? selected.name : "";
    }

    if (menuEl) {
      menuEl.querySelectorAll("." + activeClass).forEach(function (item) {
        item.classList.remove(activeClass);
      });
      if (dictionaryId) {
        activeItem = menuEl.querySelector("[data-dict-id=\"" + dictionaryId + "\"]");
        if (activeItem) {
          activeItem.classList.add(activeClass);
        }
      }
    }
  }

  function scrollToTop(scrollContainer) {
    if (!scrollContainer) {
      return;
    }
    scrollContainer.scrollTop = 0;
  }

  function ensureApiFacade() {
    if (!window.MD) {
      window.MD = {};
    }
    if (!window.MD.API) {
      window.MD.API = {};
    }

    var DEFAULT_CONFIG = {
      readingMode: "lookup",
      extractLemma: true,
      fontSize: 16,
      clickBehavior: "click",
      historyLimit: 50,
      popupHeight: "medium",
      tokenStyle: "underline",
      enabledDictionaries: [],
    };

    window.MD.API.version = function () {
      return "1.1.0";
    };

    window.MD.API.config = {
      get: function (key) {
        return window.MD.Config.get(key);
      },

      set: function (key, value) {
        window.MD.Config.set(key, value);
      },

      getAll: function () {
        return window.MD.Config.getAll();
      },

      reset: function (key) {
        if (key) {
          if (DEFAULT_CONFIG.hasOwnProperty(key)) {
            window.MD.Config.set(key, DEFAULT_CONFIG[key]);
          }
        } else {
          Object.keys(DEFAULT_CONFIG).forEach(function (k) {
            window.MD.Config.set(k, DEFAULT_CONFIG[k]);
          });
        }
      },

      apply: function () {
        var config = window.MD.Config.getAll();
        if (window.applyConfig && typeof window.applyConfig === "function") {
          window.applyConfig(config);
        }
      },
    };

    window.MD.API.init = function (options) {
      return window.MD.init(options);
    };

    window.MD.API.getDictionaries = function (options) {
      var opts = options || {};
      var dicts = window.MD.Dictionary ? window.MD.Dictionary.getDictionaries() : [];
      var filtered = dicts.slice();
      var config = null;
      var tokenizers = null;
      var managedIds = null;
      var lang = null;
      var langConfig = null;
      var hasTokenizerConfig = false;
      if (opts.language) {
        filtered = filtered.filter(function (dict) {
          return supportsLanguage(dict, opts.language);
        });
      }
      if (opts.enabledOnly) {
        config = window.MD && window.MD.State ? window.MD.State.config : null;
        tokenizers = config ? config.tokenizers : {};
        managedIds = null;
        if (opts.language && tokenizers[opts.language] && Array.isArray(tokenizers[opts.language].dictionaryIds)) {
          hasTokenizerConfig = true;
          managedIds = tokenizers[opts.language].dictionaryIds;
          filtered = filtered.filter(function (dict) {
            return managedIds.indexOf(dict.id) !== -1;
          });
        } else if (!opts.language) {
          managedIds = [];
          for (lang in tokenizers) {
            if (tokenizers.hasOwnProperty(lang)) {
              langConfig = tokenizers[lang];
              if (langConfig && Array.isArray(langConfig.dictionaryIds)) {
                hasTokenizerConfig = true;
                langConfig.dictionaryIds.forEach(function (id) {
                  if (managedIds.indexOf(id) === -1) {
                    managedIds.push(id);
                  }
                });
              }
            }
          }
          if (hasTokenizerConfig) {
            filtered = filtered.filter(function (dict) {
              return managedIds.indexOf(dict.id) !== -1;
            });
          }
        }
      }
      return filtered;
    };

    window.MD.API.lookup = function (word, options) {
      var opts = options || {};
      var requestId = opts.requestId;
      var dictionaryId = opts.dictionaryId || null;
      var config = window.MD && window.MD.State ? window.MD.State.config : null;
      if (!config || !window.MD || !window.MD.Dictionary) {
        return Promise.resolve({
          found: false,
          requestId: requestId,
          error: { code: "CONFIG_MISSING", message: "配置未加载" },
        });
      }

      var lookupOptions = {
        language: opts.language || null,
        followed: opts.followed || false,
        requestId: requestId,
      };

      return window.MD.Dictionary.lookup(word, dictionaryId, lookupOptions)
        .then(function (result) {
          return normalizeLookupResult(result, requestId);
        })
        .catch(function (error) {
          return {
            found: false,
            requestId: requestId,
            error: {
              code: error && error.message ? error.message : "LOOKUP_FAILED",
              message: error && error.message ? error.message : "查询失败",
            },
          };
        });
    };

    window.MD.API.ui = {
      renderResult: renderResult,
      syncDictionarySelect: syncDictionarySelect,
      scrollToTop: scrollToTop,
    };
  }

  window.MD.init = init;
  window.MD.emit = emit;
  window.MD.handleTokenClick = handleTokenClick;
  ensureApiFacade();
})();

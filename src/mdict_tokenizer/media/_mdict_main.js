(function () {
  "use strict";

  if (!window.MD) {
    window.MD = {};
  }

  if (!window.MD._persistent) {
    window.MD._persistent = {};
  }

  if (!window.MD._persistent.loadedLanguages) {
    window.MD._persistent.loadedLanguages = {};
  }

  if (!window.MD._persistent.stats) {
    window.MD._persistent.stats = {
      initCount: 0,
      initSkipCount: 0,
      tokenizerHitCount: 0,
      configCacheHitCount: 0
    };
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

  function getDeckNameFromDom() {
    var deckEl = document.getElementById("mdict-deck-name");
    if (!deckEl) {
      return "";
    }
    var deckName = deckEl.textContent || deckEl.innerText || "";
    return deckName.replace(/^\s+|\s+$/g, "");
  }

  function resolveDeckFields(deckName, deckInjections, fieldNames) {
    var injections = Array.isArray(deckInjections) ? deckInjections : [];
    var allowedNames = Array.isArray(fieldNames) ? fieldNames : [];
    var allowedMap = {};
    var domDeckName = getDeckNameFromDom();
    var currentDeckName = "";
    var i;
    var searchName = "";
    var matched = null;
    var resolved = null;
    if (domDeckName) {
      currentDeckName = domDeckName;
    } else if (typeof deckName === "string") {
      currentDeckName = deckName;
    }

    if (!currentDeckName) {
      return [];
    }

    if (allowedNames.length) {
      allowedNames.forEach(function (name) {
        allowedMap[name] = true;
      });
    }

    searchName = currentDeckName;
    while (true) {
      matched = null;
      for (i = 0; i < injections.length; i++) {
        if (injections[i] && injections[i].deckName === searchName) {
          matched = injections[i];
          break;
        }
      }
      if (matched && Array.isArray(matched.fields)) {
        resolved = [];
        matched.fields.forEach(function (field) {
          if (!field || !field.name || !field.language) {
            return;
          }
          if (allowedNames.length && !allowedMap[field.name]) {
            return;
          }
          resolved.push({ name: field.name, language: field.language });
        });
        return resolved;
      }
      if (searchName.indexOf("::") === -1) {
        return [];
      }
      searchName = searchName.split("::");
      searchName.pop();
      searchName = searchName.join("::");
    }
  }

  function getFieldLanguages(fieldNames, deckInjections) {
    var languageMap = {};
    var fields = resolveDeckFields("", deckInjections, fieldNames);
    if (!fields.length) {
      return [];
    }
    fields.forEach(function (field) {
      if (!field || !field.name || !field.language) {
        return;
      }
      // ✅ 预加载策略：直接从配置提取语言，不检查 DOM
      languageMap[field.language] = true;
    });
    return Object.keys(languageMap);
  }

  function getInitLanguages(config) {
    var tokenizers = config.tokenizers || {};
    var fieldLanguages = getFieldLanguages(
      window.MDICT_FIELDS || [],
      window.MDICT_DECK_INJECTIONS || []
    );
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

  var RETRY_DELAYS = [300, 800, 2000];

  function needsTokenizeRetry() {
    var fields = document.querySelectorAll(".mdict-field[data-mdict-lang]");
    var i;
    if (!fields.length) {
      return false;
    }
    for (i = 0; i < fields.length; i++) {
      if (!fields[i].querySelector(".md-token")) {
        return true;
      }
    }
    return false;
  }

  function scheduleTokenizeRetry() {
    var attempt = 0;
    var config;
    function tryRetry() {
      if (attempt >= RETRY_DELAYS.length || !needsTokenizeRetry()) {
        return;
      }
      setTimeout(function () {
        if (!needsTokenizeRetry()) {
          return;
        }
        config = window.MD.State ? window.MD.State.config : {};
        initTokenizers(config).catch(function () {}).then(function () {
          return tokenizeFields();
        }).then(function () {
          attempt++;
          tryRetry();
        });
      }, RETRY_DELAYS[attempt]);
    }
    tryRetry();
  }

  function doInit(options) {
    var opts = options || {};
    var configPath = opts.configPath || "_mdict_config.json";
    var autoTokenize = opts.autoTokenize !== false;
    var targetContainer = opts.targetContainer || null;

     var configPromise;
     var cachedConfig = window.MD._persistent.configCache;
     if (cachedConfig) {
       configPromise = fetchJson(configPath)
         .then(function (freshConfig) {
           if (freshConfig && freshConfig.version && cachedConfig.version && freshConfig.version === cachedConfig.version) {
             window.MD._persistent.stats.configCacheHitCount++;
             return cachedConfig;
           }
           window.MD._persistent.configCache = freshConfig || {};
           return window.MD._persistent.configCache;
         })
        .catch(function () {
          return cachedConfig;
        });
    } else {
      configPromise = fetchJson(configPath).then(function (config) {
        window.MD._persistent.configCache = config || {};
        return window.MD._persistent.configCache;
      });
    }

    return configPromise
      .then(function (config) {
        // 根据当前牌组的字段语言配置过滤辞典列表
        // 使用 getFieldLanguages 根据当前牌组名（从 DOM 的 #mdict-deck-name 读取）
        // 在 MDICT_DECK_INJECTIONS 中匹配对应牌组的语言配置
        // 不依赖 tokenizers[lang].dictionaryIds 是否非空，确保即使没有导入对应语言的辞典
        // 也能正确按语言过滤，避免英语牌组显示日语辞典
        var stateConfig = config || {};
        var activeLangs = getFieldLanguages(
          window.MDICT_FIELDS || [],
          window.MDICT_DECK_INJECTIONS || []
        );
        if (activeLangs.length > 0) {
          var tokenizers = stateConfig.tokenizers || {};
          var allowedIds = {};
          var hasTokenizerIds = false;
          activeLangs.forEach(function (lang) {
            var langConfig = tokenizers[lang];
            if (langConfig && langConfig.dictionaryIds && langConfig.dictionaryIds.length) {
              hasTokenizerIds = true;
              langConfig.dictionaryIds.forEach(function (id) {
                allowedIds[id] = true;
              });
            }
          });
          if (hasTokenizerIds) {
            // 按 tokenizer 配置的 dictionaryIds 过滤
            stateConfig = Object.assign({}, stateConfig, {
              dictionaries: (stateConfig.dictionaries || []).filter(function (dict) {
                return !!allowedIds[dict.id];
              })
            });
          } else {
            // dictionaryIds 为空（旧配置或未配置），降级按 dictionary.languages 过滤
            stateConfig = Object.assign({}, stateConfig, {
              dictionaries: (stateConfig.dictionaries || []).filter(function (dict) {
                if (!dict.languages || !dict.languages.length) return true;
                return dict.languages.some(function (l) {
                  return activeLangs.indexOf(l) >= 0;
                });
              })
            });
          }
        }
        window.MD.State = {
          config: stateConfig,
          targetContainer: targetContainer,
        };
        return initTokenizers(config).catch(function () {
          // Tokenizer failure is non-fatal: dictionary still works
        });
      })
      .then(function () {
        if (autoTokenize) {
          return tokenizeFields();
        }
        return null;
      })
      .then(function () {
        if (autoTokenize) {
          scheduleTokenizeRetry();
        }
        if (window.MD.UI && window.MD.UI.isEmbedded()) {
          if (resolveDeckFields("", window.MDICT_DECK_INJECTIONS || [], window.MDICT_FIELDS || []).length > 0) {
            window.MD.UI.ensurePanel();
          }
        }
        emit("md:ready", {});
      })
      .catch(function (error) {
        emit("md:error", { code: error.message || "INIT_FAILED", message: error.message || "初始化失败" });
        throw error;
      });
  }

   function init(options) {
     window.MD._persistent.stats.initCount++;
     if (window.MD._persistent.initPromise) {
       window.MD._persistent.stats.initSkipCount++;
       return window.MD._persistent.initPromise;
     }
     window.MD._persistent.initPromise = doInit(options)
      .then(function (result) {
        window.MD._persistent.initPromise = null;
        return result;
      })
      .catch(function (error) {
        window.MD._persistent.initPromise = null;
        throw error;
      });
    return window.MD._persistent.initPromise;
  }

  function initTokenizers(config) {
    var tokenizers = config.tokenizers || {};
    var initLanguages = getInitLanguages(config);
    var tasks = [];
    var loadedLanguages = window.MD._persistent.loadedLanguages;
    if (window.MD.State) {
      window.MD.State.initLanguages = initLanguages;
    }
     initLanguages.forEach(function (language) {
       if (loadedLanguages[language]) {
         window.MD._persistent.stats.tokenizerHitCount++;
         return;
       }
      if (tokenizers[language]) {
        tasks.push(
          window.MD.Tokenizer.init(language).then(function () {
            loadedLanguages[language] = true;
            // Fire-and-forget: preload dictionary indexes for this language
            var langConfig = tokenizers[language];
            if (langConfig && langConfig.dictionaryIds && langConfig.dictionaryIds.length && window.MD.Dictionary && window.MD.Dictionary.preloadIndexes) {
              window.MD.Dictionary.preloadIndexes(langConfig.dictionaryIds).catch(function () {
                // Silently ignore preload failures
              });
            }
          })
        );
      }
    });
    return Promise.all(tasks);
  }

  function doTokenizeFields(fields, initLanguages, loadedLanguages, promises) {
    var container = null;
    if (fields.length) {
      fields.forEach(function (field) {
        if (initLanguages.length && initLanguages.indexOf(field.language) === -1) {
          if (!loadedLanguages[field.language]) {
            return;
          }
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
      if (container && (initLanguages.indexOf("ja") !== -1 || loadedLanguages["ja"])) {
        promises.push(window.MD.Tokenizer.tokenizeElement(container, "ja"));
      }
    }
    return Promise.all(promises);
  }

  function tokenizeFields() {
    var fieldNames = window.MDICT_FIELDS || [];
    var deckInjections = window.MDICT_DECK_INJECTIONS || [];
    var fields = resolveDeckFields("", deckInjections, fieldNames);
    var promises = [];
    var initLanguages = [];
    var loadedLanguages = window.MD._persistent.loadedLanguages;
    var detectedLanguages = {};
    var allElements;
    var i;
    var el;
    var lang;
    var detectedLangArray;
    var config;
    var tokenizers;
    var learningTasks;
    
    if (window.MD.State && window.MD.State.initLanguages) {
      initLanguages = window.MD.State.initLanguages;
    }

    document.querySelectorAll(".mdict-field").forEach(function (element) {
      element.removeAttribute("data-mdict-lang");
    });

    if (!fields.length) {
      return Promise.resolve([]);
    }

    fields.forEach(function (field) {
      var selector = ".mdict-field[data-mdict-field='" + field.name + "']";
      var elements = document.querySelectorAll(selector);
      elements.forEach(function (element) {
        element.setAttribute("data-mdict-lang", field.language);
      });
    });

    allElements = document.querySelectorAll('.mdict-field[data-mdict-lang]');
    for (i = 0; i < allElements.length; i++) {
      el = allElements[i];
      lang = el.getAttribute('data-mdict-lang');
      if (lang && !loadedLanguages[lang]) {
        detectedLanguages[lang] = true;
      }
    }

    detectedLangArray = Object.keys(detectedLanguages);
    if (detectedLangArray.length > 0) {
      config = window.MD.State.config || {};
      tokenizers = config.tokenizers || {};
      learningTasks = [];

      detectedLangArray.forEach(function(lang) {
        if (tokenizers[lang] && window.MD.Tokenizer) {
          learningTasks.push(
            window.MD.Tokenizer.init(lang).then(function() {
              loadedLanguages[lang] = true;
              var langConfig = tokenizers[lang];
              if (langConfig && langConfig.dictionaryIds && langConfig.dictionaryIds.length && window.MD.Dictionary && window.MD.Dictionary.preloadIndexes) {
                window.MD.Dictionary.preloadIndexes(langConfig.dictionaryIds).catch(function() {
                });
              }
            })
          );
        }
      });

      if (learningTasks.length > 0) {
        return Promise.all(learningTasks).then(function() {
          return doTokenizeFields(fields, initLanguages, loadedLanguages, promises);
        });
      }
    }

    return doTokenizeFields(fields, initLanguages, loadedLanguages, promises);
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
    window.MD.UI.lookupFromToken(word, null, prefixHtml, language, element);
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
    // 在渲染后执行辞典内嵌入的脚本标签
    if (window.MD && window.MD.UI && typeof window.MD.UI.executeDictScripts === 'function') {
      window.MD.UI.executeDictScripts(normalized.dictionaryId, container);
    }
    // 绑定 tab 导航（MWU 等字典的 ul.tab + .tab-view 切换）
    if (window.MD && window.MD.UI && typeof window.MD.UI.bindTabNavigation === 'function') {
      window.MD.UI.bindTabNavigation(container);
    }
    // 为多义项词条动态生成 tab 导航（OALDAE 等字典的 div.entry[hm] 结构）
    if (window.MD && window.MD.UI && typeof window.MD.UI.bindEntryTabs === 'function') {
      window.MD.UI.bindEntryTabs(container);
    }
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
     var DEFAULT_CONFIG, CONFIG_SCHEMA, configChangeCallbacks, schema, type, remainder, i;

     if (!window.MD) {
       window.MD = {};
     }
     if (!window.MD.API) {
       window.MD.API = {};
     }

      DEFAULT_CONFIG = {
        readingMode: "lookup",
        extractLemma: true,
        fontSize: 16,
        clickBehavior: "click",
        enableHistory: true,
        historyLimit: 50,
        popupHeight: "medium",
        tokenStyle: "underline",
        enabledDictionaries: [],
      };

      CONFIG_SCHEMA = {
        readingMode: {
          type: "select",
          options: ["none", "lookup", "all"],
          default: "lookup",
        },
        extractLemma: {
          type: "boolean",
          default: true,
        },
        fontSize: {
          type: "number",
          min: 12,
          max: 32,
          step: 2,
          default: 16,
        },
        clickBehavior: {
          type: "select",
          options: ["click", "longpress"],
          default: "click",
        },
        enableHistory: {
          type: "boolean",
          default: true,
        },
        historyLimit: {
          type: "select",
          options: [10, 50, 100],
          default: 50,
        },
        popupHeight: {
          type: "select",
          options: ["small", "medium", "large", "full"],
          default: "medium",
        },
        tokenStyle: {
          type: "select",
          options: ["underline", "background", "none"],
          default: "underline",
        },
        enabledDictionaries: {
          type: "array",
          itemType: "string",
          default: [],
        },
      };

     configChangeCallbacks = [];

     function validateConfig(key, value) {
       if (!CONFIG_SCHEMA.hasOwnProperty(key)) {
         throw new Error("Invalid config key: " + key);
       }

       schema = CONFIG_SCHEMA[key];
       type = schema.type;

       if (type === "boolean") {
         if (typeof value !== "boolean") {
           throw new Error(
             "Invalid value for " + key + ": expected boolean, got " + typeof value
           );
         }
       } else if (type === "number") {
         if (typeof value !== "number") {
           throw new Error(
             "Invalid value for " + key + ": expected number, got " + typeof value
           );
         }
         if (schema.hasOwnProperty("min") && value < schema.min) {
           throw new Error(
             "Invalid value for " +
               key +
               ": must be >= " +
               schema.min +
               ", got " +
               value
           );
         }
         if (schema.hasOwnProperty("max") && value > schema.max) {
           throw new Error(
             "Invalid value for " +
               key +
               ": must be <= " +
               schema.max +
               ", got " +
               value
           );
         }
         if (schema.hasOwnProperty("step")) {
           remainder = (value - schema.min) % schema.step;
           if (Math.abs(remainder) > 0.0001) {
             throw new Error(
               "Invalid value for " +
                 key +
                 ": must be a multiple of " +
                 schema.step +
                 ", got " +
                 value
             );
           }
         }
       } else if (type === "select") {
         if (schema.options.indexOf(value) === -1) {
           throw new Error(
             "Invalid value for " +
               key +
               ": must be one of [" +
               schema.options.join(", ") +
               "], got " +
               value
           );
         }
       } else if (type === "array") {
         if (!Array.isArray(value)) {
           throw new Error(
             "Invalid value for " + key + ": expected array, got " + typeof value
           );
         }
         if (schema.itemType === "string") {
           for (i = 0; i < value.length; i++) {
             if (typeof value[i] !== "string") {
               throw new Error(
                 "Invalid value for " +
                   key +
                   ": array item at index " +
                   i +
                   " is not a string"
               );
             }
           }
         }
       }
     }

     window.MD.API.version = function () {
       return "2.0.0";
     };

     window.MD.API.config = {
       get: function (key) {
         return window.MD.Config.get(key);
       },

       set: function (key, value) {
         validateConfig(key, value);
         window.MD.Config.set(key, value);
         configChangeCallbacks.forEach(function (callback) {
           try {
             callback(key, value);
           } catch (error) {
             console.error("Error in onChange callback:", error);
           }
         });
       },

       getAll: function () {
         return window.MD.Config.getAll();
       },

       reset: function (key) {
         if (key) {
           if (DEFAULT_CONFIG.hasOwnProperty(key)) {
             window.MD.Config.set(key, DEFAULT_CONFIG[key]);
             configChangeCallbacks.forEach(function (callback) {
               try {
                 callback(key, DEFAULT_CONFIG[key]);
               } catch (error) {
                 console.error("Error in onChange callback:", error);
               }
             });
           }
         } else {
           Object.keys(DEFAULT_CONFIG).forEach(function (k) {
             window.MD.Config.set(k, DEFAULT_CONFIG[k]);
             configChangeCallbacks.forEach(function (callback) {
               try {
                 callback(k, DEFAULT_CONFIG[k]);
               } catch (error) {
                 console.error("Error in onChange callback:", error);
               }
             });
           });
         }
       },

       apply: function () {
         var config = window.MD.Config.getAll();
         if (window.applyConfig && typeof window.applyConfig === "function") {
           window.applyConfig(config);
         }
       },

       getSchema: function () {
         return CONFIG_SCHEMA;
       },

       onChange: function (callback) {
         if (typeof callback === "function") {
           configChangeCallbacks.push(callback);
         }
       },
     };

    window.MD.API.init = function (options) {
      var opts = options || {};
      
      // Handle targetContainer option for UI initialization
      if (opts.targetContainer && window.MD && window.MD.UI) {
        if (typeof opts.targetContainer === 'string') {
          window.MD.UI.setContainer(opts.targetContainer);
        } else if (opts.targetContainer.id) {
          window.MD.UI.setContainer(opts.targetContainer.id);
        }
      }
      
      return window.MD.init(opts);
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
      
      getMode: function () {
        if (window.MD && window.MD.UI && typeof window.MD.UI.getMode === 'function') {
          return window.MD.UI.getMode();
        }
        return 'modal';
      },
      
      showPanel: function () {
        var mode;
        var modal;
        var overlay;
        
        if (window.MD && window.MD.UI) {
          mode = window.MD.UI.getMode ? window.MD.UI.getMode() : 'modal';
          if (mode === 'embedded') {
            if (window.MD.UI.container) {
              window.MD.UI.container.style.display = '';
            }
            if (window.MD.UI.panel) {
              window.MD.UI.panel.style.display = '';
            }
          } else {
            modal = document.querySelector('.md-modal');
            overlay = document.querySelector('.md-modal-overlay');
            if (modal) {
              modal.classList.remove('md-modal-hidden');
            }
            if (overlay) {
              overlay.classList.remove('md-modal-hidden');
            }
          }
        }
      },
      
      hidePanel: function () {
        var mode;
        var modal;
        var overlay;
        
        if (window.MD && window.MD.UI) {
          mode = window.MD.UI.getMode ? window.MD.UI.getMode() : 'modal';
          if (mode === 'embedded') {
            if (window.MD.UI.container) {
              window.MD.UI.container.style.display = 'none';
            }
            if (window.MD.UI.panel) {
              window.MD.UI.panel.style.display = 'none';
            }
          } else {
            modal = document.querySelector('.md-modal');
            overlay = document.querySelector('.md-modal-overlay');
            if (modal) {
              modal.classList.add('md-modal-hidden');
            }
            if (overlay) {
              overlay.classList.add('md-modal-hidden');
            }
          }
        }
      }
    };
  }

   window.MD.init = init;
   window.MD.emit = emit;
   window.MD.handleTokenClick = handleTokenClick;
   window.MD.getStats = function () {
     return window.MD._persistent.stats || {};
   };
   ensureApiFacade();

   // 自动初始化：当脚本异步加载时，内联脚本可能先于 main.js 执行，
   // 导致 init() 调用被跳过。此处检测 MDICT_FIELDS 是否已设置，
   // 若已设置且尚未初始化，则自动触发 init()。
   if (window.MDICT_FIELDS && !window.MD._persistent.initPromise && !window.MD.State) {
     window.MD.init({ autoTokenize: true });
   }
})();

(function () {
  "use strict";

  if (!window.MD) {
    window.MD = {};
  }

  if (!window.MD._persistent) {
    window.MD._persistent = {};
  }

  var tokenizerCache = window.MD._persistent.tokenizerCache || {};
  window.MD._persistent.tokenizerCache = tokenizerCache;
  
   var cmuCache = window.MD._persistent.cmuCache !== undefined ? window.MD._persistent.cmuCache : null;

   var scriptsLoading = window.MD._persistent.scriptsLoading || {};
   window.MD._persistent.scriptsLoading = scriptsLoading;

   function loadScript(src) {
     if (scriptsLoading[src]) {
       return scriptsLoading[src];
     }
     scriptsLoading[src] = new Promise(function (resolve, reject) {
       var script = document.createElement("script");
       script.src = src;
       script.onload = function () {
         resolve();
       };
       script.onerror = function () {
         delete scriptsLoading[src];
         reject(new Error("TOKENIZER_LOAD_FAILED"));
       };
       document.head.appendChild(script);
     });
     return scriptsLoading[src];
   }

  function loadJson(path) {
    if (window.fetch) {
      return fetch(path).then(function (response) {
        if (!response.ok) {
          throw new Error("NETWORK_ERROR");
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
          reject(new Error("NETWORK_ERROR"));
        }
      };
      xhr.send();
    });
  }

  function initJapanese() {
    if (tokenizerCache.ja) {
      return Promise.resolve(tokenizerCache.ja);
    }
    if (typeof window.kuromoji === "undefined") {
      return loadScript("_mdict_kuromoji.js").then(function () {
        return buildJapaneseTokenizer();
      });
    }
    return buildJapaneseTokenizer();
  }

  function buildJapaneseTokenizer() {
    return new Promise(function (resolve, reject) {
      if (!window.kuromoji) {
        reject(new Error("TOKENIZER_NOT_FOUND"));
        return;
      }
      window.kuromoji
        .builder({ dicPath: "_mdict_kuromoji_" })
        .build(function (error, tokenizer) {
          if (error) {
            reject(new Error("TOKENIZER_LOAD_FAILED"));
            return;
          }
          tokenizerCache.ja = tokenizer;
          resolve(tokenizer);
        });
    });
  }

  function initEnglish() {
    if (tokenizerCache.en) {
      return Promise.resolve(tokenizerCache.en);
    }
    if (typeof window.nlp === "undefined") {
      return loadScript("_mdict_compromise.min.js").then(function () {
        tokenizerCache.en = window.nlp;
        return loadCmuDict();
      });
    }
    tokenizerCache.en = window.nlp;
    return loadCmuDict();
  }

  function loadCmuDict() {
    if (cmuCache) {
      return Promise.resolve(tokenizerCache.en);
    }
     return loadJson("_mdict_cmudict.json")
       .then(function (data) {
         cmuCache = data || {};
         window.MD._persistent.cmuCache = cmuCache;
         return tokenizerCache.en;
       })
       .catch(function () {
         cmuCache = {};
         window.MD._persistent.cmuCache = cmuCache;
         return tokenizerCache.en;
       });
  }

  function arpabetToIpa(arpabet) {
    var mapping = {
      AA: "ɑ",
      AE: "æ",
      AH: "ʌ",
      AO: "ɔ",
      AW: "aʊ",
      AY: "aɪ",
      EH: "ɛ",
      ER: "ɝ",
      EY: "eɪ",
      IH: "ɪ",
      IY: "i",
      OW: "oʊ",
      OY: "ɔɪ",
      UH: "ʊ",
      UW: "u",
      B: "b",
      CH: "tʃ",
      D: "d",
      DH: "ð",
      F: "f",
      G: "ɡ",
      HH: "h",
      JH: "dʒ",
      K: "k",
      L: "l",
      M: "m",
      N: "n",
      NG: "ŋ",
      P: "p",
      R: "r",
      S: "s",
      SH: "ʃ",
      T: "t",
      TH: "θ",
      V: "v",
      W: "w",
      Y: "j",
      Z: "z",
      ZH: "ʒ",
    };
    return arpabet
      .split(" ")
      .map(function (token) {
        var clean = token.replace(/[0-9]/g, "");
        return mapping[clean] || "";
      })
      .join("");
  }

  function tokenizeJapanese(text) {
    return initJapanese().then(function (tokenizer) {
      var tokens = tokenizer.tokenize(text);
      return tokens.map(function (token) {
        return {
          surface: token.surface_form,
          lemma: token.basic_form && token.basic_form !== "*" ? token.basic_form : token.surface_form,
          pos: token.pos,
          reading: token.reading || "",
        };
      });
    });
  }

  function tokenizeEnglish(text) {
    return initEnglish().then(function (nlp) {
      var terms = nlp(text).terms().data();
      return terms.map(function (term) {
        var lemma = term.normal || term.text;
        if (term.root) {
          lemma = term.root;
        }
        var ipa = "";
        if (cmuCache && cmuCache[lemma.toUpperCase()]) {
          ipa = arpabetToIpa(cmuCache[lemma.toUpperCase()]);
        }
        return {
          surface: term.text,
          lemma: lemma,
          pos: term.tags && term.tags.length ? term.tags[0] : "",
          ipa: ipa,
        };
      });
    });
  }

  function getRuntimeConfig() {
    if (window.MD && window.MD.Config) {
      return window.MD.Config.getAll();
    }
    return { readingMode: "lookup", tokenStyle: "underline", clickBehavior: "click" };
  }

  function applyTokenStyle(span, config) {
    span.className = "md-token tappable";
    if (config.tokenStyle) {
      span.className += " md-token-style-" + config.tokenStyle;
    }
  }

  function renderTokenDisplay(span, config) {
    var surface = span.getAttribute("data-surface") || span.textContent;
    var reading = span.dataset.reading || "";
    var ipa = span.dataset.ipa || "";
    span.innerHTML = "";
    if (reading && config.readingMode === "all") {
      var ruby = document.createElement("ruby");
      ruby.textContent = surface;
      var rt = document.createElement("rt");
      rt.textContent = reading;
      ruby.appendChild(rt);
      span.appendChild(ruby);
    } else {
      span.textContent = surface;
    }
    if (ipa && config.readingMode === "all") {
      var ipaNode = document.createElement("span");
      ipaNode.className = "md-ipa";
      ipaNode.textContent = ipa;
      span.appendChild(ipaNode);
    }
  }

  function tokenHasWordChars(surface) {
    if (!surface) {
      return false;
    }
    try {
      new RegExp("\\p{L}", "u");
      return /[\p{L}\p{N}]/u.test(surface);
    } catch (e) {
      return /[a-zA-Z0-9\u00C0-\u017F\u0400-\u04FF\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF\uAC00-\uD7AF]/.test(surface);
    }
  }

  function buildTokenSpan(token, config) {
    var span = document.createElement("span");
    applyTokenStyle(span, config);
    span.setAttribute("data-surface", token.surface);
    span.dataset.lemma = token.lemma || token.surface;
    span.dataset.pos = token.pos || "";
    if (token.reading) {
      span.dataset.reading = token.reading;
    }
    if (token.ipa) {
      span.dataset.ipa = token.ipa;
    }
    renderTokenDisplay(span, config);

    var longPressTimer = null;
    var longPressTriggered = false;
    var triggerLookup = function () {
      if (window.MD && typeof window.MD.handleTokenClick === "function") {
        window.MD.handleTokenClick(token, span);
      }
    };
    var clearLongPress = function () {
      if (longPressTimer) {
        clearTimeout(longPressTimer);
        longPressTimer = null;
      }
    };

    span.addEventListener("click", function () {
      var runtimeConfig = getRuntimeConfig();
      if (runtimeConfig.clickBehavior !== "click") {
        if (longPressTriggered) {
          longPressTriggered = false;
        }
        return;
      }
      triggerLookup();
    });

    span.addEventListener("touchstart", function () {
      var runtimeConfig = getRuntimeConfig();
      if (runtimeConfig.clickBehavior !== "longpress") {
        return;
      }
      clearLongPress();
      longPressTimer = setTimeout(function () {
        longPressTriggered = true;
        triggerLookup();
      }, 500);
    });

    span.addEventListener("touchend", clearLongPress);
    span.addEventListener("mousedown", function () {
      var runtimeConfig = getRuntimeConfig();
      if (runtimeConfig.clickBehavior !== "longpress") {
        return;
      }
      clearLongPress();
      longPressTimer = setTimeout(function () {
        longPressTriggered = true;
        triggerLookup();
      }, 500);
    });

    span.addEventListener("mouseup", clearLongPress);
    span.addEventListener("mouseleave", clearLongPress);
    return span;
  }

  function updateTokenDisplay(config) {
    var runtimeConfig = config || getRuntimeConfig();
    var tokens = document.querySelectorAll(".md-token");
    tokens.forEach(function (span) {
      applyTokenStyle(span, runtimeConfig);
      renderTokenDisplay(span, runtimeConfig);
    });
  }

  function tokenizeElement(element, language) {
    var config = window.MD && window.MD.Config ? window.MD.Config.getAll() : { readingMode: "lookup", tokenStyle: "underline" };
    var walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null, false);
    var nodes = [];
    while (walker.nextNode()) {
      nodes.push(walker.currentNode);
    }
    var tokenizePromise = language === "ja" ? tokenizeJapanese : tokenizeEnglish;
    return Promise.all(
      nodes.map(function (node) {
        var text = node.nodeValue;
        if (!text || !text.trim()) {
          return Promise.resolve();
        }
        return tokenizePromise(text).then(function (tokens) {
          var fragment = document.createDocumentFragment();
          tokens.forEach(function (token) {
            if (tokenHasWordChars(token.surface)) {
              fragment.appendChild(buildTokenSpan(token, config));
            } else {
              fragment.appendChild(document.createTextNode(token.surface || ""));
            }
          });
          node.parentNode.replaceChild(fragment, node);
        });
      })
    );
  }

  window.MD.Tokenizer = {
    init: function (language) {
      if (language === "ja") {
        return initJapanese();
      }
      if (language === "en") {
        return initEnglish();
      }
      return Promise.reject(new Error("TOKENIZER_NOT_FOUND"));
    },
    tokenize: function (text, language) {
      if (language === "ja") {
        return tokenizeJapanese(text);
      }
      if (language === "en") {
        return tokenizeEnglish(text);
      }
      return Promise.resolve([]);
    },
    tokenizeElement: function (element, language) {
      return tokenizeElement(element, language);
    },
    updateTokenDisplay: function (config) {
      updateTokenDisplay(config);
    },
  };
})();

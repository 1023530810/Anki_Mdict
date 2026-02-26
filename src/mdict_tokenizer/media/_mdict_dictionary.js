(function () {
  "use strict";

  if (!window.MD) {
    window.MD = {};
  }

  if (!window.MD._persistent) { window.MD._persistent = {}; }

  var indexCache = window.MD._persistent.indexCache = window.MD._persistent.indexCache || {};
  var shardCache = window.MD._persistent.shardCache = window.MD._persistent.shardCache || {};
  var fuseCache = window.MD._persistent.fuseCache = window.MD._persistent.fuseCache || {};
  var fuzzyResultCache = { keys: [], map: {} };
  var FUZZY_RESULT_CACHE_MAX = 100;

  function normalizeForSearch(text) {
    var result = '';
    var i, code;
    text = text.toLowerCase();
    for (i = 0; i < text.length; i++) {
      code = text.charCodeAt(i);
      if (code >= 0x30A1 && code <= 0x30F6) {
        result += String.fromCharCode(code - 0x60);
      } else {
        result += text.charAt(i);
      }
    }
    return result;
  }

  function fetchJson(url) {
    if (window.fetch) {
      return fetch(url).then(function (response) {
        if (!response.ok) {
          throw new Error("NETWORK_ERROR");
        }
        return response.json();
      });
    }
    return new Promise(function (resolve, reject) {
      var xhr = new XMLHttpRequest();
      xhr.open("GET", url, true);
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

  function loadIndex(dictionaryId) {
    if (indexCache[dictionaryId]) {
      return Promise.resolve(indexCache[dictionaryId]);
    }
    var path = "_mdict_" + dictionaryId + "_index.json";
    return fetchJson(path).then(function (data) {
      indexCache[dictionaryId] = data || { entries: {} };
      return indexCache[dictionaryId];
    });
  }

  function loadShard(dictionaryId, shardIndex) {
    var cacheKey = dictionaryId + ":" + shardIndex;
    if (shardCache[cacheKey]) {
      return Promise.resolve(shardCache[cacheKey]);
    }
    var path = "_mdict_" + dictionaryId + "_shard_" + shardIndex + ".json";
    return fetchJson(path).then(function (data) {
      shardCache[cacheKey] = data || { entries: [] };
      return shardCache[cacheKey];
    });
  }

  function lookupInDictionary(dictionaryId, word, options) {
    var entry, shardEntry, result, trimmedDef, linkMatch, target;
    options = options || {};
    var followed = options.followed || false;
    return loadIndex(dictionaryId).then(function (indexData) {
      entry = indexData.entries ? indexData.entries[word] : null;
      if (!entry) {
        return { found: false };
      }
      return loadShard(dictionaryId, entry.shardIndex).then(function (shardData) {
        shardEntry = shardData.entries[entry.position];
        if (!shardEntry) {
          return { found: false };
        }
        result = {
          found: true,
          definition: shardEntry.definition,
          dictionaryId: dictionaryId,
        };
        if (!followed && result.definition) {
          trimmedDef = result.definition.trim();
          linkMatch = trimmedDef.match(/^@@@LINK=(.+)$/);
          if (linkMatch) {
            target = linkMatch[1].trim();
            return lookupInDictionary(dictionaryId, target, { followed: true })
              .then(function (targetResult) {
                if (targetResult.found) {
                  return {
                    found: true,
                    definition: targetResult.definition,
                    dictionaryId: dictionaryId,
                  };
                } else {
                  return result;
                }
              })
              .catch(function () {
                return result;
              });
          }
        }
        return result;
      });
    });
  }

  function normalizeLookupArgs(dictionaryId, options) {
    var normalizedDictionaryId = dictionaryId;
    var normalizedOptions = options;
    if (dictionaryId && typeof dictionaryId === "object") {
      normalizedOptions = dictionaryId;
      normalizedDictionaryId = null;
    }
    return {
      dictionaryId: normalizedDictionaryId,
      options: normalizedOptions || {},
    };
  }

  function getDictionaryById(dictionaries, dictionaryId) {
    var i = 0;
    if (!dictionaryId) {
      return null;
    }
    for (i = 0; i < dictionaries.length; i++) {
      if (dictionaries[i].id === dictionaryId) {
        return dictionaries[i];
      }
    }
    return null;
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

  function getCandidatesByLanguage(config, language) {
    var dictionaries = config.dictionaries || [];
    var tokenizers = config.tokenizers || {};
    var ordered = dictionaries.slice().sort(function (a, b) {
      return a.order - b.order;
    });
    if (!language) {
      return ordered;
    }
    if (tokenizers[language] && tokenizers[language].dictionaryIds && tokenizers[language].dictionaryIds.length) {
      return tokenizers[language].dictionaryIds
        .map(function (dictId) {
          return getDictionaryById(dictionaries, dictId);
        })
        .filter(function (dict) {
          return !!dict;
        });
    }
    return ordered.filter(function (dict) {
      return supportsLanguage(dict, language);
    });
  }

  function fuzzyResultCacheGet(key) {
    return fuzzyResultCache.map[key] || null;
  }

  function fuzzyResultCachePut(key, value) {
    if (fuzzyResultCache.map[key]) { return; }
    if (fuzzyResultCache.keys.length >= FUZZY_RESULT_CACHE_MAX) {
      var evict = fuzzyResultCache.keys.shift();
      delete fuzzyResultCache.map[evict];
    }
    fuzzyResultCache.keys.push(key);
    fuzzyResultCache.map[key] = value;
  }

  function buildFuseInstance(keys) {
    var items = [];
    var i;
    for (i = 0; i < keys.length; i++) {
      items.push({ key: normalizeForSearch(keys[i]), original: keys[i] });
    }
    return new window.Fuse(items, {
      keys: ["key"],
      threshold: 0.3,
      ignoreLocation: true,
      minMatchCharLength: 1,
      includeScore: true
    });
  }

  function getOrCreateFullFuse(dictionaryId, allKeys) {
    if (fuseCache[dictionaryId]) {
      return fuseCache[dictionaryId];
    }
    fuseCache[dictionaryId] = buildFuseInstance(allKeys);
    return fuseCache[dictionaryId];
  }

  function formatFuseResults(results, limit) {
    var out = [];
    var i;
    var max = Math.min(results.length, limit);
    for (i = 0; i < max; i++) {
      out.push({ key: results[i].item.original, score: results[i].score });
    }
    return out;
  }

  function fuzzySearchInDict(dictionaryId, word, maxResults) {
    return loadIndex(dictionaryId).then(function (indexData) {
      var entries = indexData.entries || {};
      var allKeys = Object.keys(entries);
      var normalizedWord = normalizeForSearch(word);
      var candidates = [];
      var i, out;

      for (i = 0; i < allKeys.length; i++) {
        if (normalizeForSearch(allKeys[i]).indexOf(normalizedWord) === 0) {
          candidates.push(allKeys[i]);
        }
      }

      if (candidates.length > 0) {
        candidates.sort(function (a, b) { return a.length - b.length; });
        out = [];
        for (i = 0; i < candidates.length && i < maxResults; i++) {
          out.push({ key: candidates[i], score: 0 });
        }
        return { suggestions: out, matchType: "prefix" };
      }

      var fullFuse = getOrCreateFullFuse(dictionaryId, allKeys);
      var fullResults = fullFuse.search(normalizedWord);
      return { suggestions: formatFuseResults(fullResults, maxResults), matchType: "fuzzy" };
    });
  }

  function fuzzySearch(word, dictionaryId, options) {
    options = options || {};
    var language = options.language || null;
    var maxResults = options.maxResults || 10;
    var config = window.MD && window.MD.State ? window.MD.State.config : null;

    if (!config || !word) {
      return Promise.resolve({ suggestions: [], matchType: "prefix" });
    }

    var cacheKey = (dictionaryId || "") + ":" + word;
    var cached = fuzzyResultCacheGet(cacheKey);
    if (cached) {
      return Promise.resolve(cached);
    }

    if (dictionaryId) {
      return fuzzySearchInDict(dictionaryId, word, maxResults).then(function (result) {
        fuzzyResultCachePut(cacheKey, result);
        return result;
      });
    }

    var candidates = getCandidatesByLanguage(config, language);
    var userConfig = window.MD && window.MD.Config ? window.MD.Config.getAll() : null;
    if (userConfig && userConfig.enabledDictionaries && userConfig.enabledDictionaries.length) {
      candidates = candidates.filter(function (dict) {
        return userConfig.enabledDictionaries.indexOf(dict.id) !== -1;
      });
    }

    var searches = candidates.map(function (dict) {
      return fuzzySearchInDict(dict.id, word, maxResults);
    });
    return Promise.all(searches).then(function (results) {
      var seen = {};
      var merged = [];
      var i, j, s, sug, result;
      for (i = 0; i < results.length; i++) {
        sug = results[i].suggestions || [];
        for (j = 0; j < sug.length; j++) {
          s = sug[j];
          if (!seen[s.key]) {
            seen[s.key] = true;
            merged.push(s);
          }
        }
      }
      merged.sort(function (a, b) { return a.score - b.score; });
      result = { suggestions: merged.slice(0, maxResults), matchType: "fuzzy" };
      fuzzyResultCachePut(cacheKey, result);
      return result;
    });
  }

  window.MD.Dictionary = {
    lookup: function (word, dictionaryId, options) {
      var normalized = normalizeLookupArgs(dictionaryId, options);
      var language = normalized.options ? normalized.options.language : null;
      var config = window.MD && window.MD.State ? window.MD.State.config : null;
      if (!config) {
        return Promise.resolve({ found: false });
      }
      var dictionaries = config.dictionaries || [];
      var candidates = getCandidatesByLanguage(config, language);
      var preferred = getDictionaryById(dictionaries, normalized.dictionaryId);
      if (preferred && candidates.some(function (dict) {
        return dict.id === preferred.id;
      })) {
        candidates = [preferred].concat(
          candidates.filter(function (dict) {
            return dict.id !== preferred.id;
          })
        );
      }

      var userConfig = window.MD && window.MD.Config ? window.MD.Config.getAll() : null;
      if (userConfig && userConfig.enabledDictionaries && userConfig.enabledDictionaries.length) {
        candidates = candidates.filter(function (dict) {
          return userConfig.enabledDictionaries.indexOf(dict.id) !== -1;
        });
      }

      var chain = Promise.resolve({ found: false });
      candidates.forEach(function (dict) {
        chain = chain.then(function (result) {
          if (result.found) {
            return result;
          }
          return lookupInDictionary(dict.id, word, normalized.options).then(function (res) {
            if (res.found) {
              res.dictionaryName = dict.name;
            }
            return res;
          });
        });
      });
      return chain;
    },
    loadShard: function (dictionaryId, shardIndex) {
      return loadShard(dictionaryId, shardIndex);
    },
    loadIndex: function (dictionaryId) {
      return loadIndex(dictionaryId);
    },
    getDictionaries: function () {
      var config = window.MD && window.MD.State ? window.MD.State.config : null;
      return config ? config.dictionaries || [] : [];
    },
    getCandidatesByLanguage: function (language) {
      var config = window.MD && window.MD.State ? window.MD.State.config : null;
      if (!config) return [];
      return getCandidatesByLanguage(config, language);
    },
    fuzzySearch: function (word, dictionaryId, options) {
      return fuzzySearch(word, dictionaryId, options);
    },
    preloadIndexes: function (dictionaryIds) {
      if (!dictionaryIds || !dictionaryIds.length) {
        return Promise.resolve();
      }
      var ids = dictionaryIds.slice();
      var concurrency = 3;
      var active = 0;
      var index = 0;

      return new Promise(function (resolve, reject) {
        var failed = false;

        function next() {
          if (failed) {
            return;
          }
          if (index >= ids.length && active === 0) {
            resolve();
            return;
          }
          while (active < concurrency && index < ids.length) {
            active++;
            var id = ids[index++];
            loadIndex(id)
              .then(function () {
                active--;
                next();
              })
              .catch(function (err) {
                if (!failed) {
                  failed = true;
                  reject(err);
                }
              });
          }
        }

        next();
      });
    }
  };
})();

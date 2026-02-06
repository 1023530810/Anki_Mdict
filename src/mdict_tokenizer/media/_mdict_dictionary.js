(function () {
  "use strict";

  if (!window.MD) {
    window.MD = {};
  }

  if (!window.MD._persistent) { window.MD._persistent = {}; }

  var indexCache = window.MD._persistent.indexCache = window.MD._persistent.indexCache || {};
  var shardCache = window.MD._persistent.shardCache = window.MD._persistent.shardCache || {};

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
  };
})();

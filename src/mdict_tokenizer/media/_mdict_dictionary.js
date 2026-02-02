(function () {
  "use strict";

  if (!window.MD) {
    window.MD = {};
  }

  var indexCache = {};
  var shardCache = {};

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

  window.MD.Dictionary = {
    lookup: function (word, dictionaryId) {
      var config = window.MD && window.MD.State ? window.MD.State.config : null;
      if (!config) {
        return Promise.resolve({ found: false });
      }
      var dictionaries = config.dictionaries || [];
      var ordered = dictionaries.slice().sort(function (a, b) {
        return a.order - b.order;
      });

      var candidates = dictionaryId
        ? ordered.filter(function (item) {
            return item.id === dictionaryId;
          })
        : ordered;

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
          return lookupInDictionary(dict.id, word).then(function (res) {
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

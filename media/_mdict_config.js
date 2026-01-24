(function () {
  "use strict";

  if (!window.MD) {
    window.MD = {};
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

  var STORAGE_KEY = "mdict_config";

  function loadConfig() {
    var raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return Object.assign({}, DEFAULT_CONFIG);
    }
    try {
      var parsed = JSON.parse(raw);
      return Object.assign({}, DEFAULT_CONFIG, parsed || {});
    } catch (error) {
      return Object.assign({}, DEFAULT_CONFIG);
    }
  }

  function saveConfig(config) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
  }

  window.MD.Config = {
    get: function (key) {
      var config = loadConfig();
      return config[key];
    },
    set: function (key, value) {
      var config = loadConfig();
      config[key] = value;
      saveConfig(config);
    },
    getAll: function () {
      return loadConfig();
    },
  };
})();

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
    enableHistory: true,
    historyLimit: 50,
    popupHeight: "medium",
    tokenStyle: "underline",
    enabledDictionaries: {},
    enabledFeatures: { search: true, dictSelect: true, dictStatus: true },
  };

  var STORAGE_KEY = "mdict_config";

  function loadConfig() {
    var raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return Object.assign({}, DEFAULT_CONFIG);
    }
    try {
      var parsed = JSON.parse(raw);
      var config = Object.assign({}, DEFAULT_CONFIG, parsed || {});
      // 迁移：旧版 enabledDictionaries 为数组 → 转换为按语言键控的对象
      if (Array.isArray(config.enabledDictionaries)) {
        config.enabledDictionaries = {};
        saveConfig(config);
      }
      return config;
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

    /**
     * 带后端配置检查的 get 方法
     * 实现总开关逻辑：后端关闭时强制前端关闭
     *
     * @param {string} key - 配置键名
     * @param {Object} backendConfig - 后端配置对象
     * @param {string} backendConfig.language - 语言 ('ja' 或 'en')
     * @param {boolean} backendConfig.showReading - 日语读音开关（后端）
     * @param {boolean} backendConfig.showIPA - 英语音标开关（后端）
     * @returns {*} 配置值，若后端关闭则 readingMode 强制返回 'none'
     */
    getWithBackendCheck: function (key, backendConfig) {
      // 总开关逻辑：仅对 readingMode 生效
      if (key === "readingMode" && backendConfig) {
        var language = backendConfig.language || "ja";
        // 根据语言检查对应的后端开关
        var backendEnabled =
          language === "ja"
            ? backendConfig.showReading
            : backendConfig.showIPA;

        // 后端关闭时，强制前端关闭（返回 'none'）
        if (!backendEnabled) {
          return "none";
        }
      }

      // 后端开启或非 readingMode 配置，使用正常逻辑
      return this.get(key);
    },

    set: function (key, value) {
      var config = loadConfig();
      config[key] = value;
      saveConfig(config);
    },
    getAll: function () {
      return loadConfig();
    },

    /**
     * 获取指定语言的启用辞典 ID 列表
     * @param {string} language - 语言代码（如 'ja'、'en'）
     * @returns {string[]|null} 启用辞典 ID 列表，null 表示未配置（全部启用）
     */
    getEnabledForLanguage: function (language) {
      var config = loadConfig();
      var ed = config.enabledDictionaries;
      if (!ed || typeof ed !== "object" || Array.isArray(ed)) return null;
      var ids = ed[language];
      if (Array.isArray(ids) && ids.length > 0) return ids;
      return null;
    },

    /**
     * 设置指定语言的启用辞典 ID 列表（不影响其他语言）
     * @param {string} language - 语言代码
     * @param {string[]} ids - 启用辞典 ID 列表
     */
    setEnabledForLanguage: function (language, ids) {
      var config = loadConfig();
      if (
        !config.enabledDictionaries ||
        typeof config.enabledDictionaries !== "object" ||
        Array.isArray(config.enabledDictionaries)
      ) {
        config.enabledDictionaries = {};
      }
      config.enabledDictionaries[language] = ids;
      saveConfig(config);
    },
  };
})();

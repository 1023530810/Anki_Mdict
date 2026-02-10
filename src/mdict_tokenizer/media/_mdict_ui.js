(function () {
  "use strict";

  if (!window.MD) {
    window.MD = {};
  }

  if (!window.MD._persistent) {
    window.MD._persistent = {};
  }
  if (!window.MD._persistent.uiState) {
    window.MD._persistent.uiState = {};
  }

  // Feature 1: 字典探测缓存（用于快速判断可用字典）
  if (!window.MD._persistent.uiState.dictProbeCache) {
    window.MD._persistent.uiState.dictProbeCache = null;
  }
  if (!window.MD._persistent.uiState.probeActiveRequestId) {
    window.MD._persistent.uiState.probeActiveRequestId = null;
  }
  if (typeof window.MD._persistent.uiState.suppressLookupEvent === 'undefined') {
    window.MD._persistent.uiState.suppressLookupEvent = false;
  }

  // Feature 2: 有效字典计数器（用于追踪字典数量变化）
  if (!window.MD._persistent.uiState.counterRequestId) {
    window.MD._persistent.uiState.counterRequestId = 0;
  }

  // Feature 3: 竞态保护（用于 last-request-wins 模式）
  if (!window.MD._persistent.uiState.lookupRequestId) {
    window.MD._persistent.uiState.lookupRequestId = 0;
  }
  if (!window.MD._persistent.uiState.hotzoneToggleRequestId) {
    window.MD._persistent.uiState.hotzoneToggleRequestId = 0;
  }

  // Feature 4: Token 选中高亮（用于记录当前选中的分词 token）
  if (!window.MD._persistent.uiState.currentSelectedToken) {
    window.MD._persistent.uiState.currentSelectedToken = null;
  }

  // Feature 5: 有效字典过滤（用于下拉列表只显示有结果的字典）
  if (!window.MD._persistent.uiState.currentEffectiveIds) {
    window.MD._persistent.uiState.currentEffectiveIds = null;
  }

  // Feature 6: CSS 自动加载（用于追踪已加载的字典样式）
  if (!window.MD._persistent.uiState.cssLoaded) {
    window.MD._persistent.uiState.cssLoaded = {};
  }

  // Feature 7: 首选字典记忆（用于记住用户最后选择的字典）
  if (!window.MD._persistent.uiState.preferredDictId) {
    window.MD._persistent.uiState.preferredDictId = '';
  }
  if (!window.MD._persistent.uiState.preferredDictWord) {
    window.MD._persistent.uiState.preferredDictWord = '';
  }

  // Feature 8: 搜索建议竞态保护
  if (!window.MD._persistent.uiState.suggestRequestId) {
    window.MD._persistent.uiState.suggestRequestId = 0;
  }

  var historyKey = "mdict_history";
  var panelEl = window.MD._persistent.uiState.panelEl || null;
  var modalEl = window.MD._persistent.uiState.modalEl || null;
  var overlayEl = window.MD._persistent.uiState.overlayEl || null;

  function createPanelElements() {
    var panel = document.createElement('div');
    panel.className = 'md-panel';

    var header = document.createElement('div');
    header.className = 'md-panel-header';

    // 读取配置
    var features = window.MD.Config.get("enabledFeatures") || { search: true, dictSelect: true, dictStatus: true };

    // 条件创建搜索框
    var historyBtn = document.createElement('button');
    historyBtn.type = 'button';
    historyBtn.className = 'md-panel-history-btn';
    historyBtn.innerHTML = '<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg"><path d="M512 938.666667c235.648 0 426.666667-191.018667 426.666667-426.666667S747.648 85.333333 512 85.333333 85.333333 276.352 85.333333 512s191.018667 426.666667 426.666667 426.666667z m0 85.333333C229.248 1024 0 794.752 0 512S229.248 0 512 0s512 229.248 512 512-229.248 512-512 512z m42.666667-486.869333V298.538667C554.666667 275.328 535.552 256 512 256c-23.722667 0-42.666667 19.029333-42.666667 42.538667v256.256a41.984 41.984 0 0 0 12.202667 29.866666l121.258667 121.258667a42.368 42.368 0 0 0 60.032-0.298667 42.666667 42.666667 0 0 0 0.298666-60.032L554.666667 537.130667z" fill="currentColor"/></svg>';
    historyBtn.setAttribute('aria-label', '历史');
    header.appendChild(historyBtn);

    var searchInput = null;
    var suggestions = null;
    if (features.search) {
      searchInput = document.createElement('input');
      searchInput.type = 'text';
      searchInput.className = 'md-panel-search';
      searchInput.placeholder = '搜索词条...';
      header.appendChild(searchInput);

      suggestions = document.createElement('div');
      suggestions.className = 'md-suggestions';
    }

    var controls = document.createElement('div');
    controls.className = 'md-panel-controls';

    // 条件创建辞典选择器
    var dictSelectWrapper = null;
    var dictSelect = null;
    var dictSelectText = null;
    var dictDropdown = null;
    if (features.dictSelect) {
      dictSelectWrapper = document.createElement('div');
      dictSelectWrapper.className = 'md-panel-dict-select-wrapper';

      dictSelect = document.createElement('button');
      dictSelect.type = 'button';
      dictSelect.className = 'md-panel-dict-select';
      dictSelect.setAttribute('aria-haspopup', 'listbox');
      dictSelect.setAttribute('aria-expanded', 'false');
      dictSelect.setAttribute('aria-controls', 'md-dict-dropdown');
      dictSelect.setAttribute('tabindex', '0');

      dictSelectText = document.createElement('span');
      dictSelectText.className = 'md-panel-dict-select-text';
      dictSelectText.textContent = '';

      dictSelect.appendChild(dictSelectText);

      dictDropdown = document.createElement('div');
      dictDropdown.className = 'md-dropdown md-dropdown-hidden';
      dictDropdown.setAttribute('role', 'listbox');
      dictDropdown.id = 'md-dict-dropdown';

      dictSelectWrapper.appendChild(dictSelect);
      dictSelectWrapper.appendChild(dictDropdown);
      controls.appendChild(dictSelectWrapper);
    }

    // 条件创建辞典状态
    var scopeIndicator = null;
    var counter = null;
    if (features.dictStatus) {
      scopeIndicator = document.createElement('span');
      scopeIndicator.className = 'md-dict-scope';
      scopeIndicator.textContent = '全局';

      counter = document.createElement('span');
      counter.className = 'md-panel-counter md-hidden';

      controls.appendChild(scopeIndicator);
      controls.appendChild(counter);
    }

    var closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.className = 'md-panel-close';
    closeBtn.textContent = '×';

    var settingsBtn = document.createElement('button');
    settingsBtn.type = 'button';
    settingsBtn.className = 'md-panel-settings-btn';
    settingsBtn.textContent = '设置';

    controls.appendChild(settingsBtn);
    controls.appendChild(closeBtn);
    header.appendChild(controls);

    var content = document.createElement('div');
    content.className = 'md-panel-content';

    var contentBody = document.createElement('div');
    contentBody.className = 'md-panel-content-body';

    var hotzoneLeft = document.createElement('div');
    hotzoneLeft.className = 'md-hotzone md-hotzone-left';
    hotzoneLeft.setAttribute('data-dir', 'prev');

    var hotzoneRight = document.createElement('div');
    hotzoneRight.className = 'md-hotzone md-hotzone-right';
    hotzoneRight.setAttribute('data-dir', 'next');

    content.appendChild(contentBody);
    if (suggestions) {
      content.appendChild(suggestions);
    }
    content.appendChild(hotzoneLeft);
    content.appendChild(hotzoneRight);

    panel.appendChild(header);
    panel.appendChild(content);

    var title = document.createElement('span');
    title.className = 'md-panel-title';
    title.textContent = '词典';

    var searchBtn = document.createElement('button');
    searchBtn.type = 'button';
    searchBtn.className = 'md-panel-search-btn';
    searchBtn.textContent = '搜索';

    return {
      panel: panel,
      header: header,
      title: title,
      searchInput: searchInput,
      suggestions: suggestions,
      historyBtn: historyBtn,
      searchBtn: searchBtn,
      controls: controls,
      dictSelect: dictSelect,
      dictSelectText: dictSelectText,
      dictDropdown: dictDropdown,
      scopeIndicator: scopeIndicator,
      counter: counter,
      settingsBtn: settingsBtn,
      closeBtn: closeBtn,
      content: content,
      contentBody: contentBody,
      hotzoneLeft: hotzoneLeft,
      hotzoneRight: hotzoneRight
    };
  }

  function ensurePanel() {
    var mode;
    var elements;
    var container;
    var savedConfig;
    var heightClass;
    var enableHistory;

    // Case 1: panelEl exists AND is still in the DOM → reuse
    if (panelEl && document.contains(panelEl)) {
      // Sync references in case window.MD.UI was re-assigned
      window.MD.UI.panel = panelEl;
      if (window.MD._persistent.uiState.elements) {
        window.MD.UI.elements = window.MD._persistent.uiState.elements;
      }
      return panelEl;
    }

    // Case 2: panelEl exists but NOT in DOM → dangling reference, clean up everything
    if (panelEl && !document.contains(panelEl)) {
      panelEl = null;
      modalEl = null;
      overlayEl = null;
      window.MD._persistent.uiState.panelEl = null;
      window.MD._persistent.uiState.modalEl = null;
      window.MD._persistent.uiState.overlayEl = null;
      if (window.MD.UI) {
        window.MD.UI.panel = null;
        window.MD.UI.elements = null;
      }
    }

    mode = window.MD.UI.getMode();
    elements = createPanelElements();

    if (mode === 'embedded') {
      container = window.MD.UI.container;
      if (container) {
        // Smart Mode: 检查容器是否可见且有尺寸
        if (container.offsetHeight <= 0 && container.offsetWidth <= 0) {
          if (window.console && window.console.warn) {
            console.warn('[MD.UI] 嵌入式容器不可见(0x0)，回退到弹窗模式');
          }
          window.MD.UI.mode = 'modal';
          window.MD.UI.container = null;
          return ensurePanel();
        }
         elements.closeBtn.className = 'md-panel-close md-hidden';
         container.appendChild(elements.panel);
         panelEl = elements.panel;
         window.MD._persistent.uiState.panelEl = panelEl;
      } else {
        if (window.console && window.console.warn) {
          console.warn('[MD.UI] 嵌入式容器不存在，回退到弹窗模式');
        }
        window.MD.UI.mode = 'modal';
        return ensurePanel();
      }
     } else {
       overlayEl = document.createElement('div');
       overlayEl.className = 'md-modal-overlay md-modal-hidden';

       modalEl = document.createElement('div');
       modalEl.className = 'md-modal md-modal-hidden';

       savedConfig = window.MD && window.MD.Config ? window.MD.Config.getAll() : null;
       heightClass = savedConfig && savedConfig.popupHeight ? 'md-modal-' + savedConfig.popupHeight : 'md-modal-medium';
       modalEl.classList.add(heightClass);

       modalEl.appendChild(elements.panel);

       document.body.appendChild(overlayEl);
       document.body.appendChild(modalEl);

       window.MD._persistent.uiState.overlayEl = overlayEl;
       window.MD._persistent.uiState.modalEl = modalEl;

       panelEl = elements.panel;
       window.MD._persistent.uiState.panelEl = panelEl;
    }

    window.MD.UI.panel = panelEl;
    window.MD.UI.elements = elements;
    window.MD._persistent.uiState.elements = elements;

     bindDropdownEvents(elements);
     bindHotzoneEvents(elements);
     bindCloseEvents(elements);
     bindOverlayEvents();
     bindSearchEvents(elements);

     // Restore search input from persisted state
     if (window.MD._persistent.uiState.currentWord && elements.searchInput) {
       elements.searchInput.value = window.MD._persistent.uiState.currentWord;
     }

     elements.settingsBtn.addEventListener('click', function() {
       showConfig();
     });

     if (elements.historyBtn) {
       enableHistory = window.MD.Config.get('enableHistory');
       elements.historyBtn.style.display = enableHistory ? '' : 'none';
       elements.historyBtn.addEventListener('click', function() {
         showHistory();
       });
     }

     return panelEl;
  }

  var dropdownState = window.MD._persistent.uiState.dropdownState || {
    isOpen: false,
    selectedDictId: '',
    selectedDictName: ''
  };
  window.MD._persistent.uiState.dropdownState = dropdownState;

  function openDropdown() {
    var elements = window.MD.UI.elements;
    if (!elements || !elements.dictDropdown || !elements.dictSelect) {
      return;
    }
    elements.dictDropdown.classList.remove('md-dropdown-hidden');
    elements.dictDropdown.classList.add('md-dropdown-visible');
    elements.dictSelect.setAttribute('aria-expanded', 'true');
    dropdownState.isOpen = true;
  }

  function closeDropdown() {
    var elements = window.MD.UI.elements;
    if (!elements || !elements.dictDropdown || !elements.dictSelect) {
      return;
    }
    elements.dictDropdown.classList.add('md-dropdown-hidden');
    elements.dictDropdown.classList.remove('md-dropdown-visible');
    elements.dictSelect.setAttribute('aria-expanded', 'false');
    dropdownState.isOpen = false;
  }

  function toggleDropdown() {
    if (dropdownState.isOpen) {
      closeDropdown();
    } else {
      openDropdown();
    }
  }

  function selectDictionary(dictId, dictName) {
    var elements = window.MD.UI.elements;
    var options;
    var i;
    var option;

    if (!elements || !elements.dictSelectText) {
      return;
    }

    dropdownState.selectedDictId = dictId || '';
    dropdownState.selectedDictName = dictName || '';
    elements.dictSelectText.textContent = dropdownState.selectedDictName;

    if (elements.dictDropdown) {
      options = elements.dictDropdown.querySelectorAll('.md-dropdown-option');
      for (i = 0; i < options.length; i++) {
        option = options[i];
        if (option.getAttribute('data-dict-id') === dictId) {
          option.classList.add('md-dropdown-option-active');
        } else {
          option.classList.remove('md-dropdown-option-active');
        }
      }
    }

    closeDropdown();
    updateCounter();

    if (window.MD && typeof window.MD.emit === 'function') {
      window.MD.emit('md:dictChange', {
        dictId: dictId,
        dictName: dictName
      });
    }

    var currentWord = window.MD.UI.currentWord;
    if (currentWord) {
      window.MD._persistent.uiState.preferredDictId = dictId;
      window.MD._persistent.uiState.preferredDictWord = currentWord;
    }
  }

  function updateDropdownOptions(dropdownEl) {
    var allDicts;
    var dicts;
    var effectiveIds;
    var i;
    var dict;
    var option;

    if (!dropdownEl) {
      return;
    }
    dropdownEl.innerHTML = '';

    allDicts = [];
    if (window.MD && window.MD.Dictionary && window.MD.Dictionary.getDictionaries) {
      allDicts = window.MD.Dictionary.getDictionaries();
    }

    effectiveIds = window.MD._persistent.uiState.currentEffectiveIds || null;
    if (effectiveIds && effectiveIds.length > 0) {
      dicts = allDicts.filter(function(d) {
        return effectiveIds.indexOf(d.id) !== -1;
      });
    } else {
      dicts = allDicts;
    }

    for (i = 0; i < dicts.length; i++) {
      dict = dicts[i];
      option = document.createElement('button');
      option.type = 'button';
      option.className = 'md-dropdown-option';
      if (dropdownState.selectedDictId === dict.id) {
        option.className += ' md-dropdown-option-active';
      }
      option.setAttribute('data-dict-id', dict.id);
      option.setAttribute('role', 'option');
      option.textContent = dict.name;
      dropdownEl.appendChild(option);
    }

    var wrapper = dropdownEl.parentElement;
    if (wrapper) {
      if (dicts.length <= 1) {
        wrapper.classList.add('md-hidden');
      } else {
        wrapper.classList.remove('md-hidden');
      }
    }
  }

  function bindDropdownEvents(elements) {
    var selectBtn;
    var menu;
    var wrapper;

    if (!elements || !elements.dictSelect || !elements.dictDropdown) {
      return;
    }

    selectBtn = elements.dictSelect;
    menu = elements.dictDropdown;
    wrapper = selectBtn.parentElement;

    updateDropdownOptions(menu);

    selectBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      if (!dropdownState.isOpen) {
        updateDropdownOptions(menu);
      }
      toggleDropdown();
    });

    menu.addEventListener('click', function(e) {
      var target = e.target;
      var optionBtn = null;
      var dictId;
      var dictName;

      if (!target) {
        return;
      }
      if (target.classList && target.classList.contains('md-dropdown-option')) {
        optionBtn = target;
      } else if (target.parentElement && target.parentElement.classList && 
                 target.parentElement.classList.contains('md-dropdown-option')) {
        optionBtn = target.parentElement;
      }
      if (!optionBtn) {
        return;
      }
      e.stopPropagation();
      dictId = optionBtn.getAttribute('data-dict-id') || '';
      dictName = optionBtn.textContent || '';
      selectDictionary(dictId, dictName);
      window.MD.UI.currentDictId = dictId;
      window.MD._persistent.uiState.currentDictId = dictId;
      refreshLookup();
    });

    document.addEventListener('click', function(e) {
      var target;
      var isInsideWrapper;

      if (!dropdownState.isOpen) {
        return;
      }
      target = e.target;
      if (!target) {
        closeDropdown();
        return;
      }
      isInsideWrapper = wrapper && wrapper.contains(target);
      if (!isInsideWrapper) {
        closeDropdown();
      }
    });

    selectBtn.addEventListener('keydown', function(e) {
      var key = e.key || e.keyCode;

      if (key === 'Enter' || key === 13 || key === ' ' || key === 32) {
        e.preventDefault();
        e.stopPropagation();
        if (!dropdownState.isOpen) {
          updateDropdownOptions(menu);
        }
        toggleDropdown();
      }
      if (key === 'Escape' || key === 27) {
        e.preventDefault();
        closeDropdown();
      }
    });

    menu.addEventListener('keydown', function(e) {
      var key = e.key || e.keyCode;
      var focused;
      var dictId;
      var dictName;

      if (key === 'Escape' || key === 27) {
        e.preventDefault();
        closeDropdown();
        selectBtn.focus();
      }
      if (key === 'Enter' || key === 13) {
        focused = document.activeElement;
        if (focused && focused.classList && focused.classList.contains('md-dropdown-option')) {
          e.preventDefault();
          dictId = focused.getAttribute('data-dict-id') || '';
          dictName = focused.textContent || '';
          selectDictionary(dictId, dictName);
        }
      }
    });
  }

  /**
   * 获取所有可用字典列表
   * @returns {Array} 字典数组
   */
  function getDictionaries() {
    if (window.MD && window.MD.Dictionary && window.MD.Dictionary.getDictionaries) {
      return window.MD.Dictionary.getDictionaries() || [];
    }
    return [];
  }

  /**
   * 获取当前字典在列表中的索引
   * @returns {number} 索引值，未找到返回 0
   */
  function getCurrentDictionaryIndex() {
    var dictionaries = getDictionaries();
    var currentDictId = window.MD.UI.currentDictId || '';
    var i;

    if (!dictionaries.length) {
      return 0;
    }

    for (i = 0; i < dictionaries.length; i++) {
      if (dictionaries[i].id === currentDictId) {
        return i;
      }
    }
    return 0;
  }

  /**
   * 生成探测缓存键
   * @param {string} word - 查询词
   * @param {Array} candidateDicts - 候选字典列表
   * @returns {string} 缓存键
   */
  function getProbeCacheKey(word, candidateDicts) {
    var ids = candidateDicts.map(function(dict) { return dict.id; });
    return word + '::' + ids.join('|');
  }

  /**
   * 并行探测候选字典，返回有结果的字典 ID 列表
   * @param {string} word - 查询词
   * @param {Array} candidateDicts - 候选字典列表
   * @param {number} requestId - 请求 ID（用于竞态保护）
   * @param {string} language - 语言代码
   * @returns {Promise<Array>} 有效字典 ID 列表
   */
  function probeEffectiveDictionaryIds(word, candidateDicts, requestId, language) {
    if (!candidateDicts.length) return Promise.resolve([]);

    var cacheKey = getProbeCacheKey(word, candidateDicts);
    if (window.MD._persistent.uiState.dictProbeCache &&
        window.MD._persistent.uiState.dictProbeCache.key === cacheKey) {
      return Promise.resolve(window.MD._persistent.uiState.dictProbeCache.effectiveIds.slice());
    }

    window.MD._persistent.uiState.probeActiveRequestId = requestId;
    window.MD._persistent.uiState.suppressLookupEvent = true;

    var lookups = candidateDicts.map(function(dict) {
      var options = { dictionaryId: dict.id, requestId: requestId };
      if (language) options.language = language;
      return window.MD.API.lookup(word, options)
        .then(function(result) { return { dictId: dict.id, result: result }; })
        .catch(function() { return { dictId: dict.id, result: { found: false } }; });
    });

    return Promise.all(lookups).then(function(results) {
      if (window.MD._persistent.uiState.probeActiveRequestId === requestId) {
        window.MD._persistent.uiState.suppressLookupEvent = false;
      }

      var effectiveIds = results
        .filter(function(item) { return item.result && item.result.found; })
        .map(function(item) { return item.result.dictionaryId || item.dictId; })
        .filter(function(id, index, all) { return all.indexOf(id) === index; });

      window.MD._persistent.uiState.dictProbeCache = {
        key: cacheKey,
        effectiveIds: effectiveIds
      };

      return effectiveIds.slice();
    });
  }

   /**
    * 更新字典计数器显示
    * 格式："N/M"（当前/总数），从 1 开始计数
    * 只有一个或没有字典时隐藏计数器
    * @param {Array} effectiveIds - 有结果的字典 ID 列表
    * @param {string} selectedId - 当前选中的字典 ID
    */
   function updateCounter(effectiveIds, selectedId) {
     var counterEl = window.MD.UI.elements.counter;
     if (!counterEl) return;

     if (!effectiveIds || effectiveIds.length <= 1) {
       counterEl.textContent = '';
       counterEl.classList.add('md-hidden');
       return;
     }

     var currentIndex = effectiveIds.indexOf(selectedId);
     var currentNum = currentIndex >= 0 ? currentIndex + 1 : 1;
     counterEl.textContent = currentNum + '/' + effectiveIds.length;
     counterEl.classList.remove('md-hidden');
    }

   /**
    * 刷新查词后的计数器
    * @param {string} word - 要查的词
    * @param {number} requestId - 请求 ID，用于防止竞态
    */
   function refreshCounterForWord(word, requestId) {
     var language, candidateDicts, container, displayId, elements;

     if (!word) {
       window.MD._persistent.uiState.currentEffectiveIds = null;
       updateCounter([], null);
       elements = window.MD.UI.elements;
       if (elements && elements.dictDropdown) {
         updateDropdownOptions(elements.dictDropdown);
       }
       return;
     }

     language = resolveLookupLanguage(word);
     candidateDicts = getDictionaries();

     if (!candidateDicts.length) {
       window.MD._persistent.uiState.currentEffectiveIds = null;
       updateCounter([], null);
       return;
     }

     probeEffectiveDictionaryIds(word, candidateDicts, requestId, language).then(function(effectiveIds) {
       if (window.MD._persistent.uiState.counterRequestId !== requestId) return;

       window.MD._persistent.uiState.currentEffectiveIds = effectiveIds;

       container = document.querySelector('.md-panel-dict-select-wrapper');
       displayId = container ? container.dataset.selectedId : null;
       updateCounter(effectiveIds, displayId);

       elements = window.MD.UI.elements;
       if (elements && elements.dictDropdown) {
         updateDropdownOptions(elements.dictDropdown);
       }
     });
   }

   /**
    * 刷新查词结果
    */
   function refreshLookup() {
    var currentWord = window.MD.UI.currentWord;
    var currentDictId = window.MD.UI.currentDictId;

    if (currentWord) {
      lookupAndRender(currentWord, currentDictId || null, null);
    }
  }

  /**
   * 切换到上一个字典
   */
  function switchToPrevDictionary() {
    var word;
    var candidateDicts;
    var language;
    var requestId;
    var currentDictId;
    var currentIndex;
    var prevIndex;
    var prevId;
    var prevDict;
    var i;

    word = window.MD.UI.currentWord;
    if (!word) {
      return;
    }

    candidateDicts = getDictionaries();
    if (!candidateDicts || candidateDicts.length === 0) {
      return;
    }

     language = resolveLookupLanguage(word);
     requestId = ++window.MD._persistent.uiState.hotzoneToggleRequestId;

     probeEffectiveDictionaryIds(word, candidateDicts, requestId, language).then(function(effectiveIds) {
       if (window.MD._persistent.uiState.hotzoneToggleRequestId !== requestId) {
         return;
       }
       if (!effectiveIds || effectiveIds.length === 0) {
         return;
       }

       currentDictId = window.MD.UI.currentDictId;
       currentIndex = effectiveIds.indexOf(currentDictId);
       prevIndex = currentIndex - 1;
       if (prevIndex < 0) {
         prevIndex = effectiveIds.length - 1;
       }

       prevId = effectiveIds[prevIndex];
       for (i = 0; i < candidateDicts.length; i++) {
         if (candidateDicts[i].id === prevId) {
           prevDict = candidateDicts[i];
           break;
         }
       }
        if (prevDict) {
          selectDictionary(prevDict.id, prevDict.name);
          window.MD.UI.currentDictId = prevDict.id;
          window.MD._persistent.uiState.currentDictId = prevDict.id;
          refreshLookup();
          updateCounter(effectiveIds, prevId);
        }
     });
   }

   /**
    * 切换到下一个字典
    */
   function switchToNextDictionary() {
     var word;
     var candidateDicts;
     var language;
     var requestId;
     var currentDictId;
     var currentIndex;
     var nextIndex;
     var nextId;
     var nextDict;
     var i;

     word = window.MD.UI.currentWord;
     if (!word) {
       return;
     }

     candidateDicts = getDictionaries();
     if (!candidateDicts || candidateDicts.length === 0) {
       return;
     }

     language = resolveLookupLanguage(word);
     requestId = ++window.MD._persistent.uiState.hotzoneToggleRequestId;

     probeEffectiveDictionaryIds(word, candidateDicts, requestId, language).then(function(effectiveIds) {
       if (window.MD._persistent.uiState.hotzoneToggleRequestId !== requestId) {
         return;
       }
       if (!effectiveIds || effectiveIds.length === 0) {
         return;
       }

      currentDictId = window.MD.UI.currentDictId;
      currentIndex = effectiveIds.indexOf(currentDictId);
      nextIndex = currentIndex + 1;
      if (nextIndex >= effectiveIds.length) {
        nextIndex = 0;
      }

      nextId = effectiveIds[nextIndex];
      for (i = 0; i < candidateDicts.length; i++) {
        if (candidateDicts[i].id === nextId) {
          nextDict = candidateDicts[i];
          break;
        }
      }
       if (nextDict) {
         selectDictionary(nextDict.id, nextDict.name);
         window.MD.UI.currentDictId = nextDict.id;
         window.MD._persistent.uiState.currentDictId = nextDict.id;
         refreshLookup();
         updateCounter(effectiveIds, nextId);
       }
    });
  }

  /**
   * 绑定热区点击事件
   * @param {Object} elements - DOM 元素集合
   */
  function bindHotzoneEvents(elements) {
    var hotzoneLeft;
    var hotzoneRight;

    if (!elements) {
      return;
    }

    hotzoneLeft = elements.hotzoneLeft;
    hotzoneRight = elements.hotzoneRight;

    function bindHotzone(el, handler) {
      if (!el) return;
      var touchMoved = false;

      el.addEventListener('touchstart', function() {
        touchMoved = false;
      }, { passive: true });

      el.addEventListener('touchmove', function() {
        touchMoved = true;
      }, { passive: true });

      el.addEventListener('touchend', function(e) {
        if (touchMoved) return;
        e.preventDefault();
        e.stopPropagation();
        handler();
      });

      el.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        handler();
      });
    }

    bindHotzone(hotzoneLeft, switchToPrevDictionary);
    bindHotzone(hotzoneRight, switchToNextDictionary);
  }

  function bindCloseEvents(elements) {
    if (!elements || !elements.closeBtn) {
      return;
    }
    elements.closeBtn.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      hidePopup();
    });
  }

  function bindOverlayEvents() {
    if (!overlayEl) {
      return;
    }
    overlayEl.addEventListener('click', function(e) {
      e.preventDefault();
      hidePopup();
    });
  }

    function bindSearchEvents(elements) {
      var debounceTimer;
      var suggestTimer;
      var word;
      var trimmedWord;
      var language;
      
      if (!elements || !elements.searchBtn || !elements.searchInput) {
        return;
      }

      debounceTimer = null;
      suggestTimer = null;

      function hideSuggestions() {
        var el = elements.suggestions || (elements.content && elements.content.querySelector('.md-suggestions'));
        if (el) {
          el.innerHTML = '';
          el.style.display = 'none';
        }
      }

      function showSuggestions(items) {
        var i, div;
        var el = elements.suggestions || (elements.content && elements.content.querySelector('.md-suggestions'));
        if (!el || !items || !items.length) {
          hideSuggestions();
          return;
        }
        el.innerHTML = '';
        for (i = 0; i < items.length && i < 10; i++) {
          div = document.createElement('div');
          div.className = 'md-suggestion-item';
          div.textContent = items[i].key;
          div.setAttribute('data-word', items[i].key);
          el.appendChild(div);
        }
        el.style.display = 'flex';
      }

      if (elements.suggestions) {
        elements.suggestions.addEventListener('click', function(e) {
          var target = e.target;
          var selectedWord;
          if (target && target.classList.contains('md-suggestion-item')) {
            selectedWord = target.getAttribute('data-word');
            if (selectedWord) {
              hideSuggestions();
              language = resolveLookupLanguage(selectedWord);
              lookupAndRender(selectedWord, null, '', { language: language });
            }
          }
        });
      }

      elements.searchBtn.addEventListener('click', function() {
        word = elements.searchInput.value;
        if (word && word.replace(/^\s+|\s+$/g, '') !== '') {
          clearTimeout(debounceTimer);
          clearTimeout(suggestTimer);
          hideSuggestions();
          trimmedWord = word.replace(/^\s+|\s+$/g, '');
          language = resolveLookupLanguage(trimmedWord);
          lookupAndRender(trimmedWord, null, '', { language: language });
        }
      });

      elements.searchInput.addEventListener('keydown', function(e) {
        var key = e.key || e.keyCode;
        if (key === 'Enter' || key === 13) {
          clearTimeout(debounceTimer);
          clearTimeout(suggestTimer);
          hideSuggestions();
          word = elements.searchInput.value;
          if (word && word.replace(/^\s+|\s+$/g, '') !== '') {
            trimmedWord = word.replace(/^\s+|\s+$/g, '');
            language = resolveLookupLanguage(trimmedWord);
            lookupAndRender(trimmedWord, null, '', { language: language });
          }
        }
      });

      elements.searchInput.addEventListener('input', function(e) {
        clearTimeout(suggestTimer);
        word = e.target.value.replace(/^\s+|\s+$/g, '');
        if (!word) {
          hideSuggestions();
          return;
        }
        suggestTimer = setTimeout(function() {
          var myRequestId = ++window.MD._persistent.uiState.suggestRequestId;
          language = resolveLookupLanguage(word);
          window.MD.Dictionary.fuzzySearch(word, null, { language: language }).then(function(result) {
            if (window.MD._persistent.uiState.suggestRequestId !== myRequestId) {
              return;
            }
            var items = (result && result.suggestions) || null;
            showSuggestions(items);
          });
        }, 500);
      });

      document.addEventListener('click', function(e) {
        var el = elements.suggestions || (elements.content && elements.content.querySelector('.md-suggestions'));
        if (!el || el.style.display === 'none') { return; }
        if (el.contains(e.target) || elements.searchInput.contains(e.target)) { return; }
        hideSuggestions();
      });
    }

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

   function extractEntryWord(link) {
     if (!link) return "";
     var href = link.getAttribute("href") || "";
     if (!href || href.indexOf("entry://") !== 0) {
       href = link.href || "";
     }
     if (!href || href.indexOf("entry://") !== 0) {
       return "";
     }
     var word = href.slice(8);
     if (!word) return "";
     try {
       word = decodeURIComponent(word);
     } catch (error) {
       word = String(word);
     }
     return word.trim();
   }

   /**
    * 动态加载所有字典的 CSS 文件
    * 遍历配置中的字典列表，为每个字典加载其 CSS 文件
    */
   function loadDictStyles() {
     if (!window.MD.State || !window.MD.State.config || !window.MD.State.config.dictionaries) {
       return;
     }
     
     window.MD.State.config.dictionaries.forEach(function(dict) {
       if (dict.resources && dict.resources.cssFile) {
         loadCss(dict.resources.cssFile);
       }
     });
   }

   /**
    * 动态加载单个 CSS 文件
    * @param {string} cssFile - CSS 文件路径
    */
   function loadCss(cssFile) {
     var link;
     
     if (!window.MD._persistent.uiState.cssLoaded) {
       window.MD._persistent.uiState.cssLoaded = {};
     }
     
     if (window.MD._persistent.uiState.cssLoaded[cssFile]) {
       return;
     }
     
     window.MD._persistent.uiState.cssLoaded[cssFile] = true;
     
     link = document.createElement('link');
     link.rel = 'stylesheet';
     link.href = cssFile;
     link.onerror = function() {
       console.warn('[MD] CSS 加载失败:', cssFile);
     };
     document.head.appendChild(link);
   }

   function bindEntryLinks(container, input, dictSwitch) {
    if (!container || container.dataset.mdictEntryBound === "1") {
      return;
    }
    container.dataset.mdictEntryBound = "1";
    container.addEventListener("click", function (event) {
      var target = event.target;
      var link = null;
      var word = "";
      var dictId = null;
      var href = "";
      if (target && target.closest) {
        link = target.closest('a[href^="entry://"]');
      } else if (target && target.tagName === "A") {
        href = target.getAttribute("href") || "";
        if (href.indexOf("entry://") === 0) {
          link = target;
        }
      }
      if (!link) {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      word = extractEntryWord(link);
      if (!word) {
        return;
      }
      if (input) {
        input.value = word;
        input.focus();
      }
      dictId = dictSwitch ? dictSwitch.value || null : null;
      lookupAndRender(word, dictId, null);
    });
  }

  function detectLanguage(word) {
    if (!word) {
      return null;
    }
    if (/[\u3040-\u309F\u30A0-\u30FF\u3400-\u4DBF\u4E00-\u9FFF]/.test(word)) {
      return 'ja';
    }
    if (/[a-zA-Z]/.test(word)) {
      return 'en';
    }
    return null;
  }

  function resolveLookupLanguage(word) {
    var lastLanguage = window.MD._persistent.uiState.lastLookupLanguage || null;
    if (!word) {
      return lastLanguage;
    }
    var detected = detectLanguage(word);
    if (detected) {
      window.MD._persistent.uiState.lastLookupLanguage = detected;
      return detected;
    }
    return lastLanguage;
  }

  function getLastLookupLanguage() {
    return window.MD && window.MD.State ? window.MD.State.lastLookupLanguage : null;
  }

  function setLastLookupLanguage(language) {
    if (!language) {
      return;
    }
    if (!window.MD.State) {
      window.MD.State = {};
    }
    window.MD.State.lastLookupLanguage = language;
  }

  function lookupAndRender(word, dictionaryId, prefixHtml, options) {
    var panel = ensurePanel();
    var elements = window.MD.UI.elements;

    var historyOverlay = elements && elements.content && elements.content.querySelector('.md-history-overlay');
    if (historyOverlay) { historyOverlay.remove(); }

    var requestId;
    var lookupRequestId;
    var lookupOptions;
    var html;
    var fullHtml;
    var shouldUsePreferred;
    var dictId;
    var fuzzyResult;
    var fallbackHtml;
    var links;
    var s;
    var i;
    var j;

    requestId = ++window.MD._persistent.uiState.counterRequestId;
    lookupRequestId = ++window.MD._persistent.uiState.lookupRequestId;

    if (!elements || !elements.contentBody) {
      if (window.console && window.console.error) {
        console.error('[MD.UI] lookupAndRender: elements not available');
      }
      return;
    }

     elements.contentBody.innerHTML = "<div class=\"md-loading\">加载中...</div>";
      
      window.MD.UI.currentWord = word;
      window.MD._persistent.uiState.currentWord = window.MD.UI.currentWord;
      if (elements.searchInput) {
        elements.searchInput.value = word;
      }
      if (dictionaryId) {
        window.MD.UI.currentDictId = dictionaryId;
        window.MD._persistent.uiState.currentDictId = window.MD.UI.currentDictId;
      }
     
      shouldUsePreferred = window.MD._persistent.uiState.preferredDictId &&
                           window.MD._persistent.uiState.preferredDictWord &&
                           window.MD._persistent.uiState.preferredDictWord === word;
      
      if (!shouldUsePreferred && window.MD._persistent.uiState.preferredDictId) {
        window.MD._persistent.uiState.preferredDictId = '';
        window.MD._persistent.uiState.preferredDictWord = '';
      }
      
      dictId = shouldUsePreferred ? window.MD._persistent.uiState.preferredDictId : dictionaryId;
      
      lookupOptions = options || {};
     if (!lookupOptions.language) {
       lookupOptions.language = resolveLookupLanguage(word);
     }
      if (lookupOptions.language) {
        window.MD._persistent.uiState.lastLookupLanguage = lookupOptions.language;
      }
       window.MD.Dictionary.lookup(word, dictId, lookupOptions).then(function (result) {
        if (window.MD._persistent.uiState.lookupRequestId !== lookupRequestId) {
          return;
        }
        if (!result.found) {
          MD.Dictionary.fuzzySearch(word, null, { language: lookupOptions.language }).then(function (fuzzyRes) {
            if (window.MD._persistent.uiState.lookupRequestId !== lookupRequestId) { return; }
            if (fuzzyRes && fuzzyRes.suggestions && fuzzyRes.suggestions.length > 0) {
              fallbackHtml = "<div class=\"md-fuzzy-fallback\">" +
                "<div class=\"md-fuzzy-hint\">未找到「" + word + "」的释义。您是否要找：</div>" +
                "<div class=\"md-fuzzy-suggestions\">";
              for (i = 0; i < fuzzyRes.suggestions.length; i++) {
                s = fuzzyRes.suggestions[i];
                fallbackHtml += "<a href=\"#\" data-md-fuzzy-word=\"" + s.key + "\">" + s.key + "</a>";
              }
              fallbackHtml += "</div></div>";
              elements.contentBody.innerHTML = fallbackHtml;
              links = elements.contentBody.querySelectorAll("a[data-md-fuzzy-word]");
              for (j = 0; j < links.length; j++) {
                links[j].addEventListener("click", function (e) {
                  e.preventDefault();
                  lookupAndRender(this.getAttribute("data-md-fuzzy-word"), null, "");
                });
              }
            } else {
              elements.contentBody.innerHTML = "<div class=\"md-empty\">未找到释义</div>";
            }
            elements.contentBody.scrollTop = 0;
            if (elements.title) {
              elements.title.textContent = word;
            }
            refreshCounterForWord(word, requestId);
          });
          return;
        }

         var suggestEl = elements.suggestions || (elements.content && elements.content.querySelector('.md-suggestions'));
         if (suggestEl) {
           suggestEl.innerHTML = '';
           suggestEl.style.display = 'none';
         }
        
         if (result.dictionaryId) {
          window.MD.UI.currentDictId = result.dictionaryId;
          window.MD._persistent.uiState.currentDictId = window.MD.UI.currentDictId;
        }
       
        html = fixCssReferences(result.definition, result.dictionaryId);
        fullHtml = prefixHtml ? prefixHtml + html : html;
        elements.contentBody.innerHTML = "<div class=\"mdict-" + result.dictionaryId + "\">" + fullHtml + "</div>";
        elements.contentBody.scrollTop = 0;

       bindEntryLinks(elements.contentBody, elements.searchInput, elements.dictSelect);

       if (result.dictionaryId) {
         selectDictionary(result.dictionaryId, result.dictionaryName);
       }

       if (elements.title) {
         elements.title.textContent = result.dictionaryName || word;
       }
       window.MD.History.add({
         word: word,
         dictionaryId: result.dictionaryId,
         timestamp: Date.now(),
         source: (options && options.source) || "manual",
       });
       if (window.MD && typeof window.MD.emit === "function") {
         if (!window.MD._persistent.uiState.suppressLookupEvent) {
           window.MD.emit("md:lookup", { word: word, result: result });
         }
       }
       refreshCounterForWord(word, requestId);
     });
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
    html = html.replace(/<link[^>]+href=["']([^"']+\.css)["'][^>]*>/gi, function(match, cssPath) {
      return match.replace(cssPath, actualCss);
    });
    // 替换 @import url("xxx.css")
    html = html.replace(/@import\s+url\(["']?([^"')]+\.css)["']?\)/gi, function(match, cssPath) {
      return match.replace(cssPath, actualCss);
    });
    return html;
  }

  /**
   * showPopup - API 兼容层
   * 内部重定向到新的 modal 系统
   * @param {string} content - HTML 内容
   * @param {Object} options - 选项 { title, height, dictionaryId }
   * @returns {HTMLElement} 面板元素
   */
  function showPopup(content, options) {
    var elements;
    var dictionaryId = options && options.dictionaryId;
    var title = (options && options.title) || '辞典';

    // 1. 确保面板存在
    ensurePanel();

    if (panelEl) {
      panelEl.style.display = '';
    }

    // 2. 显示模态弹窗
    if (modalEl) {
      modalEl.classList.add('md-modal-visible');
      modalEl.classList.remove('md-modal-hidden');
    }
    if (overlayEl) {
      overlayEl.classList.add('md-modal-visible');
      overlayEl.classList.remove('md-modal-hidden');
    }

    // 3. 更新标题
    elements = window.MD.UI.elements;
    if (elements && elements.title) {
      elements.title.textContent = title;
    }

    // 4. 渲染内容
    if (elements && elements.contentBody) {
      elements.contentBody.innerHTML = fixCssReferences(content, dictionaryId);
    }

    return panelEl;
  }

  /**
   * hidePopup - API 兼容层
   * 内部重定向到新的 modal 系统
   */
  function hidePopup() {
    if (modalEl) {
      modalEl.classList.remove('md-modal-visible');
      modalEl.classList.add('md-modal-hidden');
    }
    if (overlayEl) {
      overlayEl.classList.remove('md-modal-visible');
      overlayEl.classList.add('md-modal-hidden');
    }
    
    if (window.MD._persistent.uiState.currentSelectedToken) {
      window.MD._persistent.uiState.currentSelectedToken.classList.remove('md-selected');
      window.MD._persistent.uiState.currentSelectedToken = null;
    }
  }

  function applyFontSize(config) {
    if (!config || !config.fontSize) {
      return;
    }
    document.documentElement.style.setProperty("--md-font-size", config.fontSize + "px");
  }

  function applyPopupHeight(config) {
    if (!modalEl || !config || !config.popupHeight) {
      return;
    }
    var heightClasses = ['md-modal-small', 'md-modal-medium', 'md-modal-large', 'md-modal-full'];
    heightClasses.forEach(function(cls) {
      modalEl.classList.remove(cls);
    });
    modalEl.classList.add('md-modal-' + config.popupHeight);
  }

  function applyConfig(config) {
    applyFontSize(config);
    applyPopupHeight(config);
    if (window.MD && window.MD.Tokenizer && window.MD.Tokenizer.updateTokenDisplay) {
      window.MD.Tokenizer.updateTokenDisplay(config);
    }
  }

  function createSelect(options, value, onChange) {
    var wrapper = document.createElement("div");
    wrapper.className = "md-select-wrapper";
    
    var btn = document.createElement("button");
    btn.className = "md-select-btn";
    var currentLabel = "";
    options.forEach(function(opt) {
      if (opt.value === value) {
        currentLabel = opt.label;
      }
    });
    btn.textContent = currentLabel || options[0].label;
    
    var menu = document.createElement("div");
    menu.className = "md-select-menu md-hidden";
    menu.addEventListener("wheel", function(e) {
      e.stopPropagation();
    }, { passive: true });
    menu.addEventListener("touchmove", function(e) {
      e.stopPropagation();
    }, { passive: true });
    
    options.forEach(function(opt) {
      var optBtn = document.createElement("button");
      optBtn.textContent = opt.label;
      if (opt.value === value) {
        optBtn.classList.add("active");
      }
      optBtn.addEventListener("click", function(e) {
        e.stopPropagation();
        btn.textContent = opt.label;
        menu.querySelectorAll("button").forEach(function(b) {
          b.classList.remove("active");
        });
        optBtn.classList.add("active");
        menu.classList.add("md-hidden");
        if (onChange) {
          onChange(opt.value);
        }
      });
      menu.appendChild(optBtn);
    });
    
    btn.addEventListener("click", function(e) {
      e.stopPropagation();
      document.querySelectorAll(".md-select-menu").forEach(function(m) {
        if (m !== menu) m.classList.add("md-hidden");
      });
      menu.classList.toggle("md-hidden");
    });
    
    wrapper.appendChild(btn);
    wrapper.appendChild(menu);
    
    return wrapper;
  }

  function createRow(labelText, control) {
    var row = document.createElement("div");
    row.className = "md-settings-item";
    var title = document.createElement("span");
    title.className = "md-settings-label";
    title.textContent = labelText;
    row.appendChild(title);
    row.appendChild(control);
    return row;
  }

  function buildDictionarySection(config) {
    var wrapper = document.createElement("div");
    wrapper.className = "md-settings-section";
    var title = document.createElement("div");
    title.className = "md-config-subtitle";
    title.textContent = "启用辞典";
    wrapper.appendChild(title);

    var dicts = window.MD.Dictionary.getDictionaries();
    var enabled = config.enabledDictionaries && config.enabledDictionaries.length
      ? config.enabledDictionaries
      : dicts.map(function (dict) { return dict.id; });
    if (!config.enabledDictionaries || !config.enabledDictionaries.length) {
      config.enabledDictionaries = enabled;
      window.MD.Config.set("enabledDictionaries", enabled);
    }

    dicts.forEach(function (dict) {
      var item = document.createElement("label");
      item.className = "md-config-dict-item";
      var checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = enabled.indexOf(dict.id) !== -1;
      checkbox.addEventListener("change", function () {
        var selected = [];
        wrapper.querySelectorAll("input[type=checkbox]").forEach(function (box, index) {
          if (box.checked && dicts[index]) {
            selected.push(dicts[index].id);
          }
        });
        window.MD.Config.set("enabledDictionaries", selected);
      });
      var label = document.createElement("span");
      label.textContent = dict.name;
      item.appendChild(checkbox);
      item.appendChild(label);
      wrapper.appendChild(item);
    });
    return wrapper;
  }

  function buildFeatureSection(config) {
    var wrapper = document.createElement("div");
    wrapper.className = "md-settings-section";
    var title = document.createElement("div");
    title.className = "md-config-subtitle";
    title.textContent = "启用功能";
    wrapper.appendChild(title);

    var features = [
      { id: "history", label: "历史查询" },
      { id: "search", label: "搜索框" },
      { id: "dictSelect", label: "辞典选择" },
      { id: "dictStatus", label: "辞典状态" }
    ];

    var enabled = config.enabledFeatures || { search: true, dictSelect: true, dictStatus: true };

     features.forEach(function (feature) {
       var item = document.createElement("label");
       item.className = "md-config-dict-item";
       var checkbox = document.createElement("input");
       checkbox.type = "checkbox";
       if (feature.id === "history") {
         checkbox.checked = config.enableHistory !== false;
         checkbox.addEventListener("change", function () {
           var newVal = checkbox.checked;
           window.MD.Config.set("enableHistory", newVal);
           var els = window.MD.UI.elements;
           if (!newVal) {
             window.MD.History.clear();
             if (els && els.historyBtn) { els.historyBtn.style.display = "none"; }
           } else {
             if (els && els.historyBtn) { els.historyBtn.style.display = ""; }
           }
         });
       } else {
         checkbox.checked = enabled[feature.id];
         checkbox.addEventListener("change", function () {
           var newConfig = {};
           features.forEach(function (f) {
             if (f.id === "history") return;
             var box = wrapper.querySelector("input[data-feature='" + f.id + "']");
             if (box) newConfig[f.id] = box.checked;
           });
           window.MD.Config.set("enabledFeatures", newConfig);
           
           var panel = document.querySelector(".md-panel");
           if (panel) {
             panel.remove();
           }
           window.MD.UI.ensurePanel();
         });
       }
       checkbox.setAttribute("data-feature", feature.id);
       var label = document.createElement("span");
       label.textContent = feature.label;
       item.appendChild(checkbox);
       item.appendChild(label);
       wrapper.appendChild(item);
     });
     return wrapper;
  }

  function showConfig() {
    var existing = document.querySelector(".md-settings-panel");
    if (existing) { existing.remove(); return; }

    var settingsPanel = document.createElement("div");
    settingsPanel.className = "md-settings-panel";

    var overlay = document.createElement("div");
    overlay.className = "md-settings-overlay";

    var content = document.createElement("div");
    content.className = "md-settings-content";

    var header = document.createElement("div");
    header.className = "md-settings-header";

    var headerTitle = document.createElement("span");
    headerTitle.textContent = "设置";

    var closeBtn = document.createElement("button");
    closeBtn.className = "md-settings-close";
    closeBtn.textContent = "✕";

    header.appendChild(headerTitle);
    header.appendChild(closeBtn);

    var body = document.createElement("div");
    body.className = "md-settings-body";

    var config = window.MD.Config.getAll();
    var currentMode = window.MD.UI.getMode();
    var heightSelect;

    body.appendChild(buildDictionarySection(config));
    body.appendChild(buildFeatureSection(config));

    var lemmaToggle = document.createElement("button");
    lemmaToggle.className = "md-config-toggle" + (config.extractLemma ? " active" : "");
    lemmaToggle.textContent = config.extractLemma ? "开启" : "关闭";
    lemmaToggle.addEventListener("click", function () {
      var newVal = !window.MD.Config.get("extractLemma");
      window.MD.Config.set("extractLemma", newVal);
      lemmaToggle.classList.toggle("active", newVal);
      lemmaToggle.textContent = newVal ? "开启" : "关闭";
    });
    body.appendChild(createRow("提取原型", lemmaToggle));

    var fontSizeInput = document.createElement("input");
    fontSizeInput.type = "number";
    fontSizeInput.min = "12";
    fontSizeInput.max = "32";
    fontSizeInput.step = "2";
    fontSizeInput.value = config.fontSize;
    fontSizeInput.addEventListener("change", function () {
      window.MD.Config.set("fontSize", parseInt(fontSizeInput.value, 10) || 16);
      applyConfig(window.MD.Config.getAll());
    });
    body.appendChild(createRow("字体大小", fontSizeInput));

    var readingSelect = createSelect(
      [
        { value: "none", label: "不显示" },
        { value: "lookup", label: "仅查词后" },
        { value: "all", label: "显示全部" },
      ],
      config.readingMode,
      function(value) {
        window.MD.Config.set("readingMode", value);
        applyConfig(window.MD.Config.getAll());
      }
    );
    body.appendChild(createRow("注音/音标显示", readingSelect));

    var historySelect = createSelect(
      [
        { value: "10", label: "10 条" },
        { value: "50", label: "50 条" },
        { value: "100", label: "100 条" },
      ],
      String(config.historyLimit),
      function(value) {
        window.MD.Config.set("historyLimit", parseInt(value, 10) || 50);
      }
    );
    body.appendChild(createRow("历史记录数量", historySelect));

    var clickSelect = createSelect(
      [
        { value: "click", label: "单击查词" },
        { value: "longpress", label: "长按查词" },
      ],
      config.clickBehavior,
      function(value) {
        window.MD.Config.set("clickBehavior", value);
      }
    );
    body.appendChild(createRow("分词点击", clickSelect));

    if (currentMode === 'modal') {
      heightSelect = createSelect(
        [
          { value: "small", label: "小" },
          { value: "medium", label: "中" },
          { value: "large", label: "大" },
          { value: "full", label: "全屏" },
        ],
        config.popupHeight,
        function(value) {
          window.MD.Config.set("popupHeight", value);
          applyConfig(window.MD.Config.getAll());
        }
      );
      body.appendChild(createRow("弹窗高度", heightSelect));
    }

    var styleSelect = createSelect(
      [
        { value: "underline", label: "下划线" },
        { value: "background", label: "背景色" },
        { value: "none", label: "无" },
      ],
      config.tokenStyle,
      function(value) {
        window.MD.Config.set("tokenStyle", value);
        applyConfig(window.MD.Config.getAll());
      }
    );
    body.appendChild(createRow("分词样式", styleSelect));

    applyConfig(config);

    content.appendChild(header);
    content.appendChild(body);
    settingsPanel.appendChild(overlay);
    settingsPanel.appendChild(content);

    function closeSettings() {
      var el = document.querySelector(".md-settings-panel");
      if (el) el.remove();
    }

    overlay.addEventListener("click", closeSettings);
    closeBtn.addEventListener("click", closeSettings);
    settingsPanel.addEventListener("keydown", function(e) {
      if (e.key === "Escape") closeSettings();
    });

    document.addEventListener("click", function() {
      document.querySelectorAll(".md-select-menu").forEach(function(m) {
        m.classList.add("md-hidden");
      });
    });

    document.body.appendChild(settingsPanel);
  }

  function showHistory() {
    var elements = window.MD.UI.elements;
    if (!elements || !elements.content) {
      return;
    }

    var existing = elements.content.querySelector(".md-history-overlay");
    if (existing) {
      existing.remove();
      return;
    }

    var history = window.MD.History.getAll();
    
    var overlay = document.createElement("div");
    overlay.className = "md-history-overlay";

    var listContainer = document.createElement("div");
    listContainer.className = "md-history-list";

    if (!history.length) {
      listContainer.innerHTML = "<div class=\"md-empty\">暂无历史</div>";
    } else {
      history.slice(0, 100).forEach(function(entry) {
        var item = document.createElement("div");
        item.className = "md-history-item";
        
        var wordSpan = document.createElement("span");
        wordSpan.className = "md-history-word";
        wordSpan.textContent = entry.word;
        
        var metaSpan = document.createElement("span");
        metaSpan.className = "md-history-meta";
        
        var timeStr = formatRelativeTime(entry.timestamp);
        var sourceStr = entry.source === "token" ? "分词查询" : "手动查询";
        metaSpan.textContent = timeStr + " · " + sourceStr;
        
        item.appendChild(wordSpan);
        item.appendChild(metaSpan);
        
        item.addEventListener("click", function() {
          lookupAndRender(entry.word, null, '');
          overlay.remove();
        });
        
        listContainer.appendChild(item);
      });
    }

    overlay.appendChild(listContainer);

    elements.content.appendChild(overlay);
  }

  function formatRelativeTime(timestamp) {
    var now = Date.now();
    var diff = now - timestamp;
    var seconds = Math.floor(diff / 1000);
    var minutes = Math.floor(seconds / 60);
    var hours = Math.floor(minutes / 60);
    var days = Math.floor(hours / 24);

    if (days > 0) return days + "天前";
    if (hours > 0) return hours + "小时前";
    if (minutes > 0) return minutes + "分钟前";
    return "刚刚";
  }

   function lookupFromToken(word, dictionaryId, prefixHtml, language, element) {
     var mode;
     var elements;

     if (window.MD._persistent.uiState.currentSelectedToken) {
       window.MD._persistent.uiState.currentSelectedToken.classList.remove('md-selected');
     }
     if (element) {
       element.classList.add('md-selected');
       window.MD._persistent.uiState.currentSelectedToken = element;
     }

     ensurePanel();

     if (panelEl) {
       panelEl.style.display = '';
     }

     mode = window.MD.UI.getMode();
     if (mode === 'modal' && modalEl) {
       modalEl.classList.add('md-modal-visible');
       modalEl.classList.remove('md-modal-hidden');
       if (overlayEl) {
         overlayEl.classList.add('md-modal-visible');
         overlayEl.classList.remove('md-modal-hidden');
       }
     }

     elements = window.MD.UI.elements;
     if (elements && elements.title) {
       elements.title.textContent = word;
     }

     if (elements && elements.contentBody) {
       elements.contentBody.innerHTML = '<div class="md-loading">加载中...</div>';
     }

     setLastLookupLanguage(language);
     lookupAndRender(word, dictionaryId, prefixHtml, { language: language, source: "token" });
   }

  /**
   * MD.UI - 用户界面模块
   * 
   * 支持两种显示模式：
   * - 'embedded': 嵌入式模式，渲染到 #mdict-panel 容器内
   * - 'modal': 弹窗模式，创建居中浮层（默认回退）
   * 
   * 容器检测逻辑：
    * 1. 初始化时自动检测 #mdict-panel
    * 2. 支持延迟设置容器（setContainer）
    */
   window.applyConfig = applyConfig;
   window.MD.UI = {
    // 显示模式: 'embedded' | 'modal' | null
    mode: null,
    
    // 容器元素引用（嵌入式模式）
    container: null,
    
    // 面板元素引用
    panel: null,
    
    // 是否已初始化
    _initialized: false,
    
    // 当前选中的字典 ID
    currentDictId: '',
    
    // 当前查询的词
    currentWord: '',
    
    /**
     * 初始化 UI 模块
     * @param {Object} options - 初始化选项
     * @param {string} options.containerId - 容器 ID（可选，默认 'mdict-panel'）
     * @returns {boolean} 是否成功初始化
     */
    init: function(options) {
      var opts = options || {};
      var containerId = opts.containerId || 'mdict-panel';
      
      // 检测容器
      this.detectContainer(containerId);
      
      this._initialized = true;
      
      // 输出初始化信息
      if (window.console && window.console.log) {
        console.log('[MD.UI] 初始化完成, mode=' + this.mode);
      }
      
      return true;
    },
    
    /**
     * 检测容器是否存在
     * @param {string} containerId - 容器 ID（可选，默认 'mdict-panel'）
     * @returns {boolean} 是否检测到容器
     */
    detectContainer: function(containerId) {
      var id = containerId || 'mdict-panel';
      if (id.charAt(0) === '#') {
        id = id.substring(1);
      }
      var container = document.getElementById(id);
      
      if (container) {
        this.mode = 'embedded';
        this.container = container;
        return true;
      } else {
        this.mode = 'modal';
        this.container = null;
        return false;
      }
    },
    
    /**
     * 延迟设置容器（支持容器后加载场景）
     * @param {string} containerId - 容器 ID
     * @returns {boolean} 是否成功设置
     */
    setContainer: function(containerId) {
      if (!containerId) {
        return false;
      }
      
      var id = containerId;
      if (id.charAt(0) === '#') {
        id = id.substring(1);
      }
      var container = document.getElementById(id);
      if (container) {
        this.mode = 'embedded';
        this.container = container;
        
        if (window.console && window.console.log) {
          console.log('[MD.UI] 容器已设置, mode=embedded, containerId=' + containerId);
        }
        
        return true;
      }
      
      return false;
    },
    
    /**
     * 获取当前模式
     * @returns {string} 'embedded' | 'modal'
     */
    getMode: function() {
      // 如果未初始化，先执行检测
      if (!this._initialized) {
        this.detectContainer();
      }
      return this.mode;
    },
    
    /**
     * 判断是否为嵌入式模式
     * @returns {boolean}
     */
    isEmbedded: function() {
      return this.getMode() === 'embedded';
    },
    
    /**
     * 判断是否为弹窗模式
     * @returns {boolean}
     */
    isModal: function() {
      return this.getMode() === 'modal';
    },
    
    ensurePanel: ensurePanel,
    showPopup: showPopup,
    hidePopup: hidePopup,
    showConfig: showConfig,
    showHistory: showHistory,
    lookupFromToken: lookupFromToken
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

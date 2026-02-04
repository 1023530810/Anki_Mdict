import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..");
const mediaDir = path.join(repoRoot, "src", "mdict_tokenizer", "media");

function createEventTarget() {
  return {
    _listeners: {},
    addEventListener(type, handler) {
      if (!this._listeners[type]) {
        this._listeners[type] = [];
      }
      this._listeners[type].push(handler);
    },
    dispatchEvent(event) {
      const handlers = this._listeners[event.type] || [];
      for (const handler of handlers) {
        handler(event);
      }
      return true;
    },
  };
}

function findByClass(root, className) {
  if (!root) return null;
  if (root.className && root.className.split(" ").indexOf(className) !== -1) {
    return root;
  }
  const children = root.children || [];
  for (const child of children) {
    const found = findByClass(child, className);
    if (found) return found;
  }
  return null;
}

function createElement(tagName) {
  const element = {
    tagName: tagName.toUpperCase(),
    className: "",
    textContent: "",
    innerHTML: "",
    value: "",
    type: "",
    placeholder: "",
    scrollTop: 0,
    dataset: {},
    children: [],
    attributes: {},
    _listeners: {},
    classList: {
      add(cls) {
        if (!element.className) {
          element.className = cls;
          return;
        }
        const parts = element.className.split(" ");
        if (parts.indexOf(cls) === -1) {
          parts.push(cls);
          element.className = parts.join(" ");
        }
      },
      remove(cls) {
        if (!element.className) return;
        element.className = element.className
          .split(" ")
          .filter((name) => name && name !== cls)
          .join(" ");
      },
    },
    style: {
      setProperty() {},
    },
    appendChild(child) {
      this.children.push(child);
      if (this.tagName === "SELECT") {
        this.options = this.children;
      }
      return child;
    },
    addEventListener(type, handler) {
      if (!this._listeners[type]) {
        this._listeners[type] = [];
      }
      this._listeners[type].push(handler);
    },
    setAttribute(name, value) {
      this.attributes[name] = String(value);
      if (name === "href") {
        this.href = String(value);
      }
    },
    getAttribute(name) {
      if (this.attributes[name]) {
        return this.attributes[name];
      }
      return null;
    },
    querySelector(selector) {
      if (selector && selector[0] === ".") {
        return findByClass(this, selector.slice(1));
      }
      return null;
    },
    querySelectorAll(selector) {
      if (selector && selector[0] === ".") {
        const results = [];
        const className = selector.slice(1);
        const walk = (node) => {
          if (!node) return;
          if (node.className && node.className.split(" ").indexOf(className) !== -1) {
            results.push(node);
          }
          (node.children || []).forEach(walk);
        };
        walk(this);
        return results;
      }
      return [];
    },
    focus() {},
  };
  if (element.tagName === "SELECT") {
    element.options = element.children;
  }
  return element;
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function loadScript(fileName) {
  const filePath = path.join(mediaDir, fileName);
  const code = fs.readFileSync(filePath, "utf8");
  vm.runInThisContext(code, { filename: filePath });
}

async function run() {
  global.window = global;
  const documentTarget = createEventTarget();

  global.document = Object.assign(documentTarget, {
    body: createElement("body"),
    head: createElement("head"),
    documentElement: { style: { setProperty() {} } },
    createElement,
    querySelector() {
      return null;
    },
    querySelectorAll() {
      return [];
    },
  });

  global.CustomEvent = class CustomEvent {
    constructor(type, options) {
      this.type = type;
      this.detail = options ? options.detail : undefined;
    }
  };

  const localStore = new Map();
  global.localStorage = {
    getItem(key) {
      return localStore.has(key) ? localStore.get(key) : null;
    },
    setItem(key, value) {
      localStore.set(key, String(value));
    },
  };

  const fakeIndexData = {
    dictA: { entries: {} },
    dictB: { entries: { hello: { shardIndex: 0, position: 0 } } },
  };
  const fakeShardData = {
    dictB: { entries: [{ definition: "<div>命中内容</div>" }] },
  };

  global.fetch = async (url) => {
    const key = String(url);
    if (key === "_mdict_dictA_index.json") {
      return { ok: true, json: async () => fakeIndexData.dictA };
    }
    if (key === "_mdict_dictB_index.json") {
      return { ok: true, json: async () => fakeIndexData.dictB };
    }
    if (key === "_mdict_dictB_shard_0.json") {
      return { ok: true, json: async () => fakeShardData.dictB };
    }
    if (key === "_mdict_config.json") {
      return { ok: true, json: async () => ({ dictionaries: [], tokenizers: {} }) };
    }
    return { ok: false, json: async () => ({}) };
  };

  loadScript("_mdict_config.js");
  loadScript("_mdict_tokenizer.js");
  loadScript("_mdict_dictionary.js");
  loadScript("_mdict_ui.js");
  loadScript("_mdict_main.js");

  global.window.MD.State = {
    config: {
      dictionaries: [
        { id: "dictA", name: "词典A", order: 1, language: "ja" },
        { id: "dictB", name: "词典B", order: 2, language: "ja" },
      ],
      tokenizers: {},
    },
  };

  assert(global.window.MD && global.window.MD.API, "MD.API 未初始化");
  const lookupPromise = global.window.MD.API.lookup("hello", { dictionaryId: "dictA" });
  assert(lookupPromise && typeof lookupPromise.then === "function", "MD.API.lookup 未返回 Promise");

  const result = await lookupPromise;
  assert(result.found === true, "查词结果应命中");
  assert(result.dictionaryId === "dictB", "应回退到首个命中辞典");
  assert(typeof result.contentHtml === "string" && result.contentHtml.length > 0, "contentHtml 必须存在");
  assert(result.error == null, "成功结果不应包含 error");

  const lookupEvent = await new Promise((resolve) => {
    document.addEventListener("md:lookup", resolve);
    global.window.MD.UI.lookupFromToken("hello", null, "", null);
  });
  assert(lookupEvent.detail, "md:lookup 事件缺少 detail");
  assert(lookupEvent.detail.word === "hello", "md:lookup.detail.word 不匹配");
  assert(lookupEvent.detail.result && lookupEvent.detail.result.found === true, "md:lookup.detail.result 不匹配");

  const scrollContainer = { scrollTop: 42 };
  global.window.MD.API.ui.scrollToTop(scrollContainer);
  assert(scrollContainer.scrollTop === 0, "scrollToTop 未将 scrollTop 归零");

  console.log("contract ok");
}

run().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
});

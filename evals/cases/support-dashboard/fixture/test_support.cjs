// Classic-script fixtures share Node's realm, so structural assertions test behavior.
const fs = require('node:fs');
const path = require('node:path');

function loadClassicScripts(files, root = __dirname) {
  const window = {};
  for (const file of files) new Function('window', fs.readFileSync(path.join(root, file), 'utf8'))(window);
  return window;
}

function fakeStorage() {
  const values = new Map();
  return {
    getItem(key) { return values.has(key) ? values.get(key) : null; },
    setItem(key, value) { values.set(String(key), String(value)); },
    removeItem(key) { values.delete(key); },
    clear() { values.clear(); },
    key(index) { return [...values.keys()][index] ?? null; },
    get length() { return values.size; },
  };
}

module.exports = { loadClassicScripts, fakeStorage };

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const {loadClassicScripts, fakeStorage} = require('./cases/support-dashboard/fixture/test_support.cjs');

test('classic scripts share the assertion realm and seed data stays unchanged', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'fixture-realm-'));
  try {
    fs.writeFileSync(path.join(root, 'seed.js'), 'window.rows = [{id:"T001"}];');
    fs.writeFileSync(path.join(root, 'model.js'), 'window.model = {read(){return window.rows.map(row => ({...row}));}};');
    assert.deepStrictEqual(loadClassicScripts(['seed.js', 'model.js'], root).model.read(), [{id: 'T001'}]);
    const seeds = loadClassicScripts(['tickets.js']).SEED_TICKETS;
    assert.equal(seeds.length, 12);
    assert.deepStrictEqual(seeds[0].id, 'T001');
  } finally { fs.rmSync(root, {recursive: true}); }
});

test('fake storage matches string/null and isolation behavior used by repository tests', () => {
  const a = fakeStorage(), b = fakeStorage();
  assert.equal(a.getItem('absent'), null);
  a.setItem('count', 13);
  assert.equal(a.getItem('count'), '13');
  assert.equal(a.key(0), 'count');
  assert.equal(a.length, 1);
  assert.equal(b.getItem('count'), null);
  a.removeItem('count');
  assert.equal(a.length, 0);
});

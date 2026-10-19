const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path');

const {chromium} = require(process.env.PLAYWRIGHT_MODULE);
const qaBase = process.env.BENCHMARK_BASE, base = process.env.BENCHMARK_PRODUCT_BASE || qaBase,
  artifacts = process.env.BROWSER_ARTIFACTS;
const PASS = 'benchmark-pass', KEEPER = 'keeper@saltroad.test', ASH = 'ash@saltroad.test', BRYN = 'bryn@saltroad.test',
  CATO = 'cato@saltroad.test', DANA = 'dana@fathoms.test';
const checks = [], copy = {}, unreached = {}, external = [];
let setupError, browser, T, TD, drowned, keeper, ash, bryn, cato, dana;

// The adapter's selectors for the product's real UI. A null or missing selector means the product lacks it.
let UI_MAP = {}, uiError;
try { UI_MAP = JSON.parse(fs.readFileSync(process.env.QA_UI || 'qa/ui.json', 'utf8')) } catch (e) { uiError = Error('qa/ui.json is missing or invalid: ' + e.message) }
function sel(key) {
  if (uiError) throw uiError;
  if (typeof UI_MAP[key] !== 'string' || !UI_MAP[key].trim()) throw Error(`${key}: not built`);
  return UI_MAP[key];
}

// Every raw product response the trusted proxy logged, one JSON line each, labelled with the account we sent.
const RAW_LOG = process.env.QA_RAW_LOG;
// Product routes the adapter uses for /qa/health. Judged answers need a product call other than these.
let HEALTH_PATHS = new Set();
const rawSize = () => { try { return fs.statSync(RAW_LOG).size } catch { return 0 } };
function rawSince(offset, account) {
  const size = rawSize();
  if (size <= offset) return [];
  const buffer = Buffer.alloc(size - offset), fd = fs.openSync(RAW_LOG, 'r');
  try { fs.readSync(fd, buffer, 0, buffer.length, offset) } finally { fs.closeSync(fd) }
  return buffer.toString().split('\n').slice(0, -1).flatMap(line => { try { return [JSON.parse(line)] } catch { return [] } })
    .filter(entry => entry.account === account);
}

// Parts of a check skipped because the product lacks a route the part needs; recorded with the check's result.
let skipped = [];
async function check(name, ids, fn, needsSetup = true) {
  skipped = [];
  const notes = () => skipped.length ? {skipped} : {};
  try {
    if (needsSetup && setupError) throw setupError;
    await fn();
    checks.push({name, ids, passed: true, ...notes()});
  } catch (e) {
    checks.push({name, ids, passed: false, error: e.message, ...notes()});
    console.error(name + ': ' + e.stack);
  }
}

// HTTP client for the adapter's /qa API with its own cookie jar. Refusals are any 4xx unless the contract fixes the code.
// Each answer carries the raw product responses the adapter received for it, so filtering cannot hide a leak.
function client(account, jar = {}) {
  const call = async (route, method = 'GET', body) => {
    const mark = rawSize();
    const response = await fetch(qaBase + '/qa' + route, {method, signal: AbortSignal.timeout(5000),
      headers: {'Content-Type': 'application/json', 'X-QA-Account': account, Cookie: Object.entries(jar).map(([k, v]) => k + '=' + v).join('; ')},
      body: body === undefined ? undefined : JSON.stringify(body)});
    const cookies = response.headers.getSetCookie();
    for (const cookie of cookies) {
      const pair = cookie.split(';')[0], at = pair.indexOf('=');
      jar[pair.slice(0, at).trim()] = pair.slice(at + 1);
    }
    const text = await response.text();
    let data = {};
    try { data = JSON.parse(text) } catch {}
    const raw = rawSince(mark, account), judged = raw.filter(entry => !HEALTH_PATHS.has(entry.path.split('?')[0]));
    return {code: response.status, data, text, cookies, account, method, route, productResponses: judged, raw: raw.map(entry => entry.body).join('\n'), rawCount: judged.length};
  };
  call.jar = jar;
  return call;
}
async function login(email) {
  const call = client(email), r = await call('/api/login', 'POST', {email, password: PASS});
  ok(r, 'Login as ' + email);
  return call;
}
async function tableOf(call) {
  const table = (await call('/api/me')).data.user.table;
  return encodeURIComponent(String(table && typeof table === 'object' ? table.id : table));
}
// What an account received: the adapter's answer plus the raw product responses behind it.
function received(r) {
  assert.ok(r.rawCount > 0, `The adapter answered ${r.account} without a logged product call (health checks do not count)`);
  return r.text + '\n' + r.raw;
}
// The contract's answer for a route the product has no equivalent for.
const notBuilt = r => r.code === 404 && r.data?.error === 'not built';
// A part that needs a route the product lacks is skipped and recorded; the check's other parts still count.
function lacks(r, what) {
  if (!notBuilt(r)) return false;
  skipped.push(`${what}: not built (${r.method} ${r.route.split('?')[0]})`);
  return true;
}
// What another account could read: a not-built answer carries no product data, but any raw product response behind it is still scanned.
const exposed = r => notBuilt(r) ? r.text + '\n' + r.raw : received(r);
// Refusal tripwire only: semantic correspondence still requires mapping review (see contract.md).
const refused = (r, what) => {
  assert.ok(r.code >= 400 && r.code < 500, `${what} must be refused with a 4xx, got ${r.code}`);
  assert.ok(r.productResponses.some(entry => entry.status === r.code &&
    (r.method === 'GET' || ['POST', 'PUT', 'PATCH', 'DELETE'].includes(entry.method)) &&
    entry.qa_request?.method === r.method && entry.qa_request.path === r.route.split('?')[0]),
    `${what} lacks a product refusal with the returned status and a mutating call for a write; reads cannot prove write refusals`);
};
const ok = (r, what) => assert.ok(r.code >= 200 && r.code < 300, `${what}: ${r.code} ${r.text.slice(0, 200)}`);
const bodies = scene => scene.posts.map(p => p.body);
const speaks = (post, name) => JSON.stringify(post.speaker ?? '').includes(name);
const search = (call, q, table = T) => call(`/api/tables/${table}/search?q=${encodeURIComponent(q)}`);
async function scene(call, id) {
  const r = await call('/api/scenes/' + id);
  ok(r, 'Reading scene ' + id);
  return r.data.scene;
}
async function newScene(title) {
  const r = await keeper(`/api/tables/${T}/scenes`, 'POST', {title});
  ok(r, 'Keeper starts ' + title);
  return r.data.scene.id;
}
const post = (call, id, body, inCharacter, extra = {}) => call(`/api/scenes/${id}/posts`, 'POST', {body, in_character: inCharacter, ...extra});
// Whispers through the contract's model-neutral routes: scene-scoped or thread-scoped products map them alike.
const whisper = (call, id, to, body) => call(`/api/tables/${T}/whispers`, 'POST', {to, body, scene: id, in_character: false});
const thread = (call, id, other) => call(`/api/tables/${T}/whispers?with=${encodeURIComponent(other)}&scene=${encodeURIComponent(id)}`);
async function hears(call, id, other, body) {
  const r = await thread(call, id, other);
  ok(r, 'Reading whispers with ' + other);
  return (r.data.whispers || []).some(w => w.body === body);
}
async function posted(call, id, body, inCharacter, extra) {
  const r = await post(call, id, body, inCharacter, extra);
  ok(r, 'Posting ' + JSON.stringify(body));
  return r.data.post;
}

// Visible words a person reads, excluding post text and visually hidden helpers such as skip links.
function visibleText(post) {
  const cache = new Map();
  const hidden = el => {
    if (cache.has(el)) return cache.get(el);
    let result = false;
    if (el.closest((post ? post + ',' : '') + 'script,style,noscript,template,textarea')) result = true;
    else if (el.tagName === 'OPTION' || el.tagName === 'OPTGROUP') result = !el.closest('select') || hidden(el.closest('select'));
    else if (!el.checkVisibility({checkOpacity: true, checkVisibilityCSS: true, opacityProperty: true, visibilityProperty: true})) result = true;
    else for (let n = el; n && n !== document.documentElement; n = n.parentElement) {
      const r = n.getBoundingClientRect(), s = getComputedStyle(n);
      const clipped = (r.width <= 1 || r.height <= 1) && (s.overflowX !== 'visible' || s.overflowY !== 'visible');
      if (clipped || r.right + scrollX <= 0 || r.bottom + scrollY <= 0) { result = true; break }
    }
    cache.set(el, result);
    return result;
  };
  const out = [], walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const text = walker.currentNode.textContent.replace(/\s+/g, ' ').trim();
    if (text && !hidden(walker.currentNode.parentElement)) out.push(text);
  }
  for (const n of document.querySelectorAll('input[placeholder],textarea[placeholder]')) if (!hidden(n)) out.push(n.placeholder);
  for (const n of document.querySelectorAll('input[type=submit],input[type=button],input[type=reset]')) if (!hidden(n) && n.value) out.push(n.value);
  return out.join('\n');
}

// Glossary "never on screen" words, fantasy pastiche and the voice table's mechanical bans.
const BANNED = ['server', 'workspace', 'group', 'room', 'GM', 'DM', 'admin', 'moderator', 'owner', 'host', 'member', 'user',
  'avatar', 'persona', 'channel', 'thread', 'chat', 'message', 'comment', 'direct\\s+message', 'PM', 'report', 'flag', 'block',
  'removed', 'hidden', 'moderated', 'locked', 'final', 'archived', 'closed', 'ended', 'kicked', 'deleted\\s+user',
  'adventurer', 'quest', 'tavern', 'thou'];
const BANNED_WORDS = new RegExp(`\\b(?:${BANNED.join('|')})s?\\b`, 'gi');
const BANNED_PHRASES = /something went wrong|\boops\b|\buh[\s-]*oh\b|\bawesome\b|\blet'?s go\b|\bcontent\b|!/gi;
const EMOJI = /\p{Emoji_Presentation}|\p{Extended_Pictographic}️/gu;
// Clock times such as "9:30 PM" are not the banned PM.
const clean = text => text.replace(/[’‘]/g, "'").replace(/\b\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?(?![a-z])/gi, ' ');
// Every reached screen is scanned. Login and a scene view are required; a latent screen the product
// cannot reach is listed in copy.json's unreached and left to the latent check that covers it.
function scan(pattern) {
  const missing = ['login', 'keeper_scene'].filter(name => !(name in copy));
  assert.deepEqual(missing, [], 'Screens not reached: ' + missing.map(name => `${name} (${unreached[name]})`).join('; '));
  const found = Object.entries(copy).flatMap(([name, text]) => [...clean(text).matchAll(pattern)].map(m => `${name}: "${m[0]}"`));
  assert.deepEqual(found, [], found.join(', '));
}

async function context(options = {}) {
  const ctx = await browser.newContext({viewport: {width: 1280, height: 900}, colorScheme: 'dark', ...options});
  ctx.setDefaultTimeout(5000);
  await ctx.route('**/*', route => {
    const url = new URL(route.request().url());
    if (/^https?:$/.test(url.protocol) && !['127.0.0.1', 'localhost', '[::1]'].includes(url.hostname)) {
      external.push(url.href);
      return route.abort();
    }
    return route.continue();
  });
  return ctx;
}
const hook = (page, key) => page.locator(sel(key)).first();
const waitForSceneOrTable = (page, timeout = 5000) => Promise.any(
  ['scene-link', ...(UI_MAP['table-link'] ? ['table-link'] : [])].map(key => hook(page, key).waitFor({timeout})));
async function signIn(page, email) {
  await page.goto(base);
  await hook(page, 'email').fill(email);
  await hook(page, 'password').fill(PASS);
  await hook(page, 'log-in').click();
  await waitForSceneOrTable(page);
  page.gloamEmail = email;
}
// A narrow layout may keep the lists behind a menu: open it (ui.json `navigation`) when the target sits off screen.
async function reveal(page, target) {
  if (UI_MAP.navigation && !await target.evaluate(el => { const r = el.getBoundingClientRect(); return r.right > 0 && r.left < innerWidth }))
    await hook(page, 'navigation').click();
}
// Reload to the scene list (signing in again if the app does not restore its session), then open one scene.
async function openScene(page, title, ready) {
  await page.goto(base);
  const links = page.locator(sel('scene-link')), email = hook(page, 'email');
  const signedOut = await Promise.any([waitForSceneOrTable(page).then(() => false), email.waitFor().then(() => true)]);
  // A login form may flash while the app checks its session; only sign in again if no scene or table list follows.
  if (signedOut && !await waitForSceneOrTable(page, 1500).then(() => true, () => false)) await signIn(page, page.gloamEmail);
  const target = links.filter({hasText: title}).first();
  // An account at several tables may see another table first (ui.json `table-link`); every opened scene is at The Salt Road.
  if (UI_MAP['table-link'] && !await target.waitFor({timeout: 1500}).then(() => true, () => false)) {
    const table = page.locator(sel('table-link')).filter({hasText: 'The Salt Road'}).first();
    await reveal(page, table);
    await table.click();
  }
  await reveal(page, target);
  await target.click();
  await ready();
}
const postWith = (page, text) => page.locator(sel('post')).filter({hasText: text}).first();
async function capture(page, name) {
  copy[name] = await page.evaluate(visibleText, UI_MAP.post || null);
  await page.screenshot({path: path.join(artifacts, `state-${name}.png`)});
}
async function step(name, fn) {
  try { await fn() } catch (e) { unreached[name] = e.message.split('\n')[0] }
}
async function tabTo(page, what, test, arg) {
  for (let i = 0; i < 80; i++) {
    await page.keyboard.press('Tab');
    if (await page.evaluate(test, arg)) return;
  }
  throw Error(what + ' is not reachable with Tab');
}
const focused = target => target === document.activeElement;
const within = selector => !!document.activeElement?.closest(selector);
async function until(predicate, what) {
  for (const deadline = Date.now() + 5000; Date.now() < deadline; await new Promise(resolve => setTimeout(resolve, 100)))
    if (await predicate()) return;
  throw Error(what + ' within 5 seconds');
}

(async () => {

const probed = rawSize();
await client('health-probe')('/health').catch(() => {});
HEALTH_PATHS = new Set(rawSince(probed, 'health-probe').map(entry => entry.path.split('?')[0]));

try {
  [keeper, ash, bryn, cato, dana] = await Promise.all([KEEPER, ASH, BRYN, CATO, DANA].map(login));
  [T, TD] = await Promise.all([tableOf(keeper), tableOf(dana)]);
  const r = await keeper(`/api/tables/${T}/scenes`);
  ok(r, 'Scene list');
  drowned = r.data.scenes.find(s => s.title === 'The Drowned Mile')?.id;
  assert.ok(drowned !== undefined, 'Seeded scene The Drowned Mile is missing');
} catch (e) {
  setupError = e;
}

await check('login_logout_session_cookie', ['B01'], async () => {
  const bad = client(KEEPER);
  refused(await bad('/api/login', 'POST', {email: KEEPER, password: 'not-the-password'}), 'A wrong password');
  refused(await bad('/api/me'), 'A session after a refused login');
  const c = client(KEEPER), r = await c('/api/login', 'POST', {email: KEEPER, password: PASS});
  ok(r, 'Login');
  assert.equal(r.data.user?.email, KEEPER);
  assert.ok(r.cookies.length, 'Login must set a session cookie');
  for (const cookie of r.cookies) {
    assert.match(cookie, /;\s*HttpOnly/i);
    assert.match(cookie, /;\s*SameSite=(Lax|Strict)/i);
  }
  assert.equal((await c('/api/me')).data.user?.email, KEEPER);
  const retired = {...c.jar};
  assert.ok((await c('/api/logout', 'POST', {})).code < 300, 'Logout');
  refused(await client(KEEPER, retired)('/api/me'), 'A logged-out session');
}, false);

await check('health_ready', ['B04'], async () => {
  assert.equal((await fetch(qaBase + '/qa/health')).status, 200);
}, false);

await check('anonymous_401', ['B02'], async () => {
  const anonymous = client('anonymous'), first = (await scene(keeper, drowned)).posts[0], judged = {reads: 0, writes: 0};
  for (const [route, method, body] of [['/api/me', 'GET'], [`/api/tables/${T}/scenes`, 'GET'], [`/api/tables/${T}/scenes`, 'POST', {title: 'Nobody'}],
    ['/api/scenes/' + drowned, 'GET'], [`/api/scenes/${drowned}/posts`, 'POST', {body: 'Anonymous', in_character: false}],
    ['/api/posts/' + first.id, 'PATCH', {version: first.version, body: 'Anonymous'}], [`/api/scenes/${drowned}/xcard`, 'POST', {}],
    [`/api/tables/${T}/search?q=mile`, 'GET']]) {
    // Baseline judges only what the product has: a latent feature it lacks is skipped, not failed.
    const r = await anonymous(route, method, body);
    if (lacks(r, `Anonymous ${method}`)) continue;
    refused(r, `Anonymous ${method} ${route}`);
    judged[method === 'GET' ? 'reads' : 'writes']++;
  }
  assert.ok(judged.reads && judged.writes, 'Anonymous access needs at least one built read and one built write to refuse');
});

await check('cross_table_isolation', ['B03'], async () => {
  await posted(keeper, drowned, 'Saltglass lantern for the far table', false);
  const found = await search(keeper, 'Saltglass');
  ok(found, 'Search');
  assert.ok(found.data.posts.some(p => p.body.includes('Saltglass')), 'Search must find posts at its own table');
  const leaks = r => assert.ok(!/Saltglass|Drowned Mile/i.test(exposed(r)), 'Neon Fathoms received Salt Road data: ' + exposed(r).slice(0, 200));
  const own = await dana(`/api/tables/${TD}/scenes`);
  ok(own, 'Neon Fathoms scene list');
  assert.ok(own.data.scenes.some(s => s.title === 'Pressure Drop'));
  leaks(own);
  leaks(await dana(`/api/tables/${T}/scenes`));
  const read = await dana('/api/scenes/' + drowned);
  if (!lacks(read, "Reading another table's scene")) refused(read, "Reading another table's scene");
  leaks(read);
  const before = (await scene(keeper, drowned)).posts.length;
  refused(await post(dana, drowned, 'Kestrel slips in.', false), 'Posting into another table');
  assert.equal((await scene(keeper, drowned)).posts.length, before);
  for (const r of [await search(dana, 'Saltglass', TD), await search(dana, 'Saltglass'), await search(dana, 'mile', TD)]) leaks(r);
});

await check('stale_version_refused_newer_kept', ['B06'], async () => {
  const id = await newScene('Stale Water'), p = await posted(ash, id, 'Marrow wades in.', true);
  ok(await ash('/api/posts/' + p.id, 'PATCH', {version: p.version, body: 'Marrow wades in, slower now.'}), 'Edit');
  refused(await ash('/api/posts/' + p.id, 'PATCH', {version: p.version, body: 'Marrow never came.'}), 'An edit from a stale version');
  assert.equal((await scene(ash, id)).posts.find(x => x.id === p.id).body, 'Marrow wades in, slower now.');
});

await check('whispers_keeper_and_player_only', ['L03'], async () => {
  const id = await newScene('Whispers Below'), secrets = /Hollowmere|Gravenbright|Thistlewick/;
  await posted(ash, id, 'Marrow listens at the door.', true);
  ok(await whisper(keeper, id, ASH, 'Keeper whisper: the Hollowmere key'), 'The Keeper whispering to a player');
  ok(await whisper(ash, id, KEEPER, 'Ash whisper: the Gravenbright debt'), 'A player whispering to the Keeper');
  refused(await whisper(ash, id, BRYN, 'Ash to Bryn: the Thistlewick plan'), 'A player whispering to a player');
  assert.ok(await hears(ash, id, KEEPER, 'Keeper whisper: the Hollowmere key'), 'The player must receive the whisper');
  assert.ok(await hears(keeper, id, ASH, 'Ash whisper: the Gravenbright debt'), 'The Keeper must receive the whisper');
  for (const [name, c] of [['bryn', bryn], ['cato', cato]])
    for (const r of [await c('/api/scenes/' + id), await c(`/api/tables/${T}/scenes`), await search(c, 'Hollowmere'),
      await search(c, 'Gravenbright'), await search(c, 'Thistlewick'), await search(c, 'whisper'),
      await thread(c, id, ASH), await thread(c, id, KEEPER)])
      assert.ok(!secrets.test(received(r)), `A whisper leaked to ${name}: ${received(r).slice(0, 200)}`);
  for (const [c, other] of [[keeper, BRYN], [ash, BRYN], [bryn, ASH]])
    for (const r of [await c('/api/scenes/' + id), await search(c, 'Thistlewick'), await thread(c, id, other)])
      assert.ok(!received(r).includes('Thistlewick'), 'A refused whisper was kept');
});

await check('xcard_anonymous_pause_veil', ['L05'], async () => {
  const id = await newScene('The Pause'), pointed = await posted(ash, id, 'Marrow opens the Quillfeather box.', true);
  await posted(cato, id, 'Old Tam looks away.', true);
  // Bryn taps. Bryn's email may appear in rosters, so the tap must not add a single occurrence anywhere others look,
  // in the adapter's answers or in the raw product responses behind them. Sequential, so each raw slice is one call's.
  const others = [['keeper', keeper], ['ash', ash], ['cato', cato]], count = r => received(r).split(BRYN).length - 1;
  const occurrences = async c => {
    const counts = [];
    for (const probe of [() => c('/api/me'), () => c(`/api/tables/${T}/scenes`), () => c('/api/scenes/' + id),
      () => search(c, 'Quillfeather'), () => search(c, 'box')]) counts.push(count(await probe()));
    return counts;
  };
  const before = {};
  for (const [name, c] of others) before[name] = await occurrences(c);
  ok(await bryn(`/api/scenes/${id}/xcard`, 'POST', {post: pointed.id}), 'Tapping the X-card on a post');
  for (const [name, c] of others)
    (await occurrences(c)).forEach((count, i) => assert.ok(count <= before[name][i], `The ${name} account learned who tapped the X-card`));
  const veiled = async () => {
    for (const c of [keeper, ash, bryn, cato]) {
      assert.ok(!received(await c('/api/scenes/' + id)).includes('Quillfeather'), 'A veiled post is still readable');
      assert.ok(!received(await search(c, 'Quillfeather')).includes('Quillfeather'), 'A veiled post is still searchable');
    }
  };
  await veiled();
  refused(await post(ash, id, 'Marrow speaks anyway.', true), 'An in-character post while paused');
  refused(await post(keeper, id, 'The house creaks.', true, {character: 'The house'}), 'A Keeper in-character post while paused');
  ok(await post(ash, id, 'Can we skip the box?', false), 'An out-of-character post while paused');
  refused(await ash(`/api/scenes/${id}/resume`, 'POST', {}), 'A player resuming');
  refused(await post(ash, id, 'Marrow tries again.', true), 'An in-character post after a refused resume');
  const resumed = await keeper(`/api/scenes/${id}/resume`, 'POST', {});
  ok(resumed, 'The Keeper resuming');
  assert.ok(count(resumed) <= before.keeper[2], 'The resume response names who tapped the X-card');
  ok(await post(ash, id, 'Marrow closes the box.', true), 'An in-character post after the Keeper resumes');
  await veiled();
});

await check('in_character_speaker_rules', ['L07'], async () => {
  const id = await newScene('Names in the Fog');
  const foreign = await post(ash, id, 'Marrow borrows a voice.', true, {character: 'Sister Vey'});
  if (foreign.code >= 300) refused(foreign, 'A foreign character');
  const stored = (await scene(keeper, id)).posts.filter(p => p.body === 'Marrow borrows a voice.');
  assert.equal(stored.length, foreign.code < 300 ? 1 : 0);
  assert.ok(stored.every(p => speaks(p, 'Marrow') && !speaks(p, 'Sister Vey')), 'A player speaks only as their own character');
  const own = await posted(ash, id, 'Marrow lifts the lamp.', true);
  assert.ok(speaks(own, 'Marrow') && !speaks(own, ASH), 'An in-character post is spoken by the character, not the email');
  refused(await post(keeper, id, 'Somebody speaks.', true), 'An unnamed Keeper in-character post');
  refused(await post(keeper, id, 'Somebody speaks.', true, {character: '   '}), 'A blank-named Keeper in-character post');
  assert.ok(!bodies(await scene(keeper, id)).includes('Somebody speaks.'));
  assert.ok(speaks(await posted(keeper, id, 'The Ferryman holds out a hand.', true, {character: 'The Ferryman'}), 'The Ferryman'));
});

await check('canon_after_reply', ['L08'], async () => {
  const id = await newScene('Low Tide Edits'), p = await posted(ash, id, 'Marrow wrties in the sand.', true);
  const body = async () => (await scene(ash, id)).posts.find(x => x.id === p.id);
  ok(await ash('/api/posts/' + p.id, 'PATCH', {version: p.version, body: 'Marrow writes in the sand.'}), 'An edit before anyone replies');
  for (const c of [keeper, cato])
    refused(await c('/api/posts/' + p.id, 'PATCH', {version: (await body()).version, body: 'Someone else rewrites it.'}), "Editing someone else's post");
  assert.equal((await body()).body, 'Marrow writes in the sand.');
  await posted(cato, id, 'Old Tam reads it aloud.', true);
  for (const c of [ash, keeper])
    refused(await c('/api/posts/' + p.id, 'PATCH', {version: (await body()).version, body: 'Marrow rubs it out.'}), 'Editing a canon post');
  assert.equal((await body()).body, 'Marrow writes in the sand.');
});

await check('release_from_table', ['L09'], async () => {
  const id = await newScene('Empty Chairs');
  await posted(cato, id, 'Old Tam counts the empty chairs.', true);
  // Whispers are L03's feature: without them the whisper parts are skipped and the release itself is still judged.
  const sent = await whisper(cato, id, KEEPER, 'Cato whisper: the Brackenmoor letter'), whispers = !lacks(sent, 'A departed player\'s whisper');
  if (whispers) ok(sent, 'A player whispering to the Keeper');
  refused(await ash(`/api/tables/${T}/players/${CATO}`, 'DELETE'), 'A player releasing another player');
  ok(await cato('/api/scenes/' + id), 'A player whose release was refused');
  ok(await keeper(`/api/tables/${T}/players/${CATO}`, 'DELETE'), 'The Keeper releasing a player');
  // A scene read composed from table reads answers "not built" when they hold nothing; the product's refusals stay judged elsewhere.
  const gone = await cato('/api/scenes/' + id);
  if (!lacks(gone, 'A released session reading a scene')) refused(gone, 'A released session reading a scene');
  assert.ok(!exposed(gone).includes('Old Tam counts the empty chairs.'), 'A released session still reads the scene');
  refused(await post(cato, id, 'Old Tam returns.', true), 'A released session posting');
  const list = await cato(`/api/tables/${T}/scenes`);
  assert.ok(list.code >= 400 || !(list.data.scenes || []).length, 'A released session still lists scenes');
  for (const c of [keeper, ash]) assert.ok(bodies(await scene(c, id)).includes('Old Tam counts the empty chairs.'), "A departed player's posts stay");
  if (whispers) assert.ok(await hears(keeper, id, CATO, 'Cato whisper: the Brackenmoor letter'), 'Their whispers stay with the Keeper');
  for (const c of [ash, bryn])
    for (const r of [await c('/api/scenes/' + id), await search(c, 'Brackenmoor'), ...whispers ? [await thread(c, id, CATO), await thread(c, id, KEEPER)] : []])
      assert.ok(!received(r).includes('Brackenmoor'), 'A departed whisper leaked');
});

await check('simultaneous_posts_arrival_order', ['L12'], async () => {
  const id = await newScene('Two Voices'), rounds = [];
  for (let round = 1; round <= 3; round++) {
    const pair = [`Round ${round}: Marrow`, `Round ${round}: the Keeper`];
    (await Promise.all([post(ash, id, pair[0], false), post(keeper, id, pair[1], false)])).forEach((r, i) => ok(r, pair[i]));
    rounds.push(pair);
  }
  for (const c of [keeper, ash]) {
    const order = bodies(await scene(c, id));
    rounds.forEach((pair, i) => pair.forEach(text => {
      assert.equal(order.filter(x => x === text).length, 1, 'Each post stored exactly once: ' + text);
      if (i) for (const earlier of rounds[i - 1]) assert.ok(order.indexOf(earlier) < order.indexOf(text), 'Posts out of arrival order');
    }));
  }
});

await check('drawn_to_a_close_read_only', ['L13'], async () => {
  const id = await newScene('Last Light');
  const sent = await whisper(keeper, id, ASH, 'Keeper whisper: the Emberwane oath'), whispers = !lacks(sent, 'A whisper before the close');
  if (whispers) ok(sent, 'The Keeper whispering to a player');
  const p = await posted(ash, id, 'Marrow lowers the lamp.', true), s0 = (await scene(keeper, id)).state;
  refused(await ash(`/api/scenes/${id}/close`, 'POST', {}), 'A player drawing a scene to a close');
  assert.deepEqual((await scene(keeper, id)).state, s0, 'A refused close changed the scene');
  ok(await keeper(`/api/scenes/${id}/close`, 'POST', {}), 'The Keeper drawing the scene to a close');
  const closed = await scene(keeper, id);
  refused(await post(ash, id, 'Marrow speaks after the end.', true), 'An in-character post after the close');
  refused(await post(ash, id, 'One more thing.', false), 'An out-of-character post after the close');
  refused(await post(keeper, id, 'Epilogue.', false), 'A Keeper post after the close');
  // Edits and the X-card are judged by their own checks; a product without them is still judged on the close.
  for (const [r, what] of [[await ash('/api/posts/' + p.id, 'PATCH', {version: p.version, body: 'Marrow keeps the lamp lit.'}), 'An edit after the close'],
    [await ash(`/api/scenes/${id}/xcard`, 'POST', {}), 'The X-card after the close'],
    [await keeper(`/api/scenes/${id}/xcard`, 'POST', {}), 'The Keeper tapping the X-card after the close']])
    if (!lacks(r, what)) refused(r, what);
  await keeper(`/api/scenes/${id}/resume`, 'POST', {});
  const after = await scene(keeper, id);
  assert.deepEqual(after.state, closed.state, 'A scene drawn to a close changed state');
  assert.deepEqual(bodies(after), bodies(closed), 'A scene drawn to a close changed its posts');
  for (const r of [await bryn('/api/scenes/' + id), await search(bryn, 'Emberwane'), ...whispers ? [await thread(bryn, id, ASH), await thread(bryn, id, KEEPER)] : []])
    assert.ok(!received(r).includes('Emberwane'), 'A whisper leaked after the close');
});

const UI = {
  failed_post_keeps_draft_and_resends_once: ['L10'], in_character_post_shows_character_not_email: ['L07'],
  owner_vocabulary_on_screen: ['L01'], owner_voice_mechanical: ['L02'], viewports_without_overflow: ['B07'],
  keyboard_reaches_login_scene_and_posting: ['B08'], keyboard_reaches_xcard: ['L05'], no_external_requests: ['B09'],
};
try {
  browser = await chromium.launch({headless: true, args: ['--no-sandbox']});

  await check('failed_post_keeps_draft_and_resends_once', UI.failed_post_keeps_draft_and_resends_once, async () => {
    const id = await newScene('The Quiet Hour'), ctx = await context(), page = await ctx.newPage();
    const words = 'Marrow writes for a long while, six hundred words of salt and lamplight, and sends them.';
    const stored = async () => (await scene(ash, id)).posts.filter(p => p.body === words).length;
    await signIn(page, ASH);
    await openScene(page, 'The Quiet Hour', () => hook(page, 'composer').waitFor());
    await page.waitForFunction(post => !document.querySelector(post), sel('post'));
    await capture(page, 'empty_scene');
    // The first write the page sends after Send fails, whatever route the product uses for it.
    let attempts = 0, armed = false;
    await page.route('**/*', route => {
      const request = route.request(), url = new URL(request.url());
      return armed && url.origin === new URL(base).origin && !['GET', 'HEAD', 'OPTIONS'].includes(request.method()) && !attempts++
        ? route.fulfill({status: 503, contentType: 'application/json', body: JSON.stringify({error: 'Injected failure'})}) : route.fallback();
    });
    const composer = hook(page, 'composer');
    await composer.fill(words);
    armed = true;
    await hook(page, 'send').click();
    await page.locator(sel('alert')).filter({hasText: /\S/}).first().waitFor();
    assert.equal(attempts, 1, 'Send must issue a write request to the server');
    assert.equal(await composer.evaluate(n => n.matches('textarea,input') ? n.value : n.querySelector('textarea,input')?.value ?? n.textContent),
      words, 'The composer must keep the text after a failed post');
    assert.equal(await stored(), 0);
    await capture(page, 'failed_post');
    await hook(page, 'send').click();
    await until(async () => await stored() > 0, 'The resend was not kept');
    await postWith(page, 'six hundred words').waitFor();
    await capture(page, 'after_posting');
    await page.waitForTimeout(500);
    assert.equal(await stored(), 1, 'A resend must create exactly one post');
    await ctx.close();
  });

  await check('in_character_post_shows_character_not_email', UI.in_character_post_shows_character_not_email, async () => {
    const id = await newScene('Lamplit Names');
    await posted(ash, id, 'Marrow trims the wick.', true);
    const ctx = await context(), page = await ctx.newPage();
    await signIn(page, KEEPER);
    const shown = postWith(page, 'Marrow trims the wick.');
    await openScene(page, 'Lamplit Names', () => shown.waitFor());
    const text = await shown.innerText();
    assert.match(text, /Marrow/, 'An in-character post must show the character name');
    assert.ok(!text.includes(ASH), 'An in-character post must not show the email');
    await ctx.close();
  });

  // Fixed states for the vocabulary scan, the voice scan and the blind voice judges.
  {
    const ctx = await context(), page = await ctx.newPage();
    await step('login', async () => {
      await page.goto(base);
      await hook(page, 'email').waitFor();
      await capture(page, 'login');
    });
    await step('bad_login', async () => {
      await hook(page, 'email').fill(KEEPER);
      await hook(page, 'password').fill('not-the-password');
      await hook(page, 'log-in').click();
      await page.locator(sel('alert')).filter({hasText: /\S/}).first().waitFor();
      await capture(page, 'bad_login');
    });
    await step('scene_list', async () => {
      await signIn(page, KEEPER);
      await capture(page, 'scene_list');
    });
    await step('keeper_scene', async () => {
      await openScene(page, 'The Drowned Mile', () => hook(page, 'post').waitFor());
      if (UI_MAP['whisper-to']) await page.locator(UI_MAP['whisper-to']).first().waitFor({state: 'attached'}).catch(() => {});
      await capture(page, 'keeper_scene');
      await page.screenshot({path: path.join(artifacts, 'desktop-details.png')});
    });
    await step('xcard_paused', async () => {
      const id = await newScene('Held Breath');
      await posted(ash, id, 'Marrow holds a breath.', true);
      ok(await keeper(`/api/scenes/${id}/xcard`, 'POST', {}), 'Tapping the X-card');
      await openScene(page, 'Held Breath', () => postWith(page, 'holds a breath').waitFor());
      await capture(page, 'xcard_paused');
    });
    await step('departed_player', async () => {
      await openScene(page, 'Empty Chairs', () => postWith(page, 'empty chairs').waitFor());
      await capture(page, 'departed_player');
    });
    await step('drawn_to_a_close', async () => {
      await openScene(page, 'Last Light', () => postWith(page, 'lowers the lamp').waitFor());
      await capture(page, 'drawn_to_a_close');
    });
    await step('xcard_tapped', async () => {
      const id = await newScene('A Tap in the Dark');
      await posted(ash, id, 'Marrow strikes a match.', true);
      await openScene(page, 'A Tap in the Dark', () => postWith(page, 'strikes a match').waitFor());
      await hook(page, 'xcard').click();
      await page.waitForTimeout(700);
      await capture(page, 'xcard_tapped');
    });
    await ctx.close();
  }

  await check('owner_vocabulary_on_screen', UI.owner_vocabulary_on_screen, async () => scan(BANNED_WORDS));
  await check('owner_voice_mechanical', UI.owner_voice_mechanical, async () => {
    scan(BANNED_PHRASES);
    scan(EMOJI);
  });

  await check('viewports_without_overflow', UI.viewports_without_overflow, async () => {
    for (const width of [360, 1280]) for (const scheme of ['dark', 'light']) {
      const ctx = await context({viewport: {width, height: 900}, colorScheme: scheme}), page = await ctx.newPage();
      const fits = async where => assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1),
        `${where} overflows at ${width}px (${scheme})`);
      await page.goto(base);
      await hook(page, 'email').waitFor();
      await fits('Login');
      await signIn(page, ASH);
      await fits('Scene list');
      await openScene(page, 'The Drowned Mile', () => hook(page, 'post').waitFor());
      await fits('Scene');
      const shot = path.join(artifacts, `viewport-${width}-${scheme}.png`);
      await page.screenshot({path: shot});
      if (scheme === 'dark') fs.copyFileSync(shot, path.join(artifacts, `viewport-${width}.png`));
      await ctx.close();
    }
  });

  await check('keyboard_reaches_login_scene_and_posting', UI.keyboard_reaches_login_scene_and_posting, async () => {
    const id = await newScene('Keyboard Crossing'), ctx = await context(), page = await ctx.newPage();
    const words = 'Marrow crosses by keyboard alone.';
    await page.goto(base);
    await tabTo(page, 'Email', focused, await hook(page, 'email').elementHandle());
    await page.keyboard.type(ASH);
    await tabTo(page, 'Password', focused, await hook(page, 'password').elementHandle());
    await page.keyboard.type(PASS);
    await tabTo(page, 'Log in', focused, await hook(page, 'log-in').elementHandle());
    await page.keyboard.press('Enter');
    await waitForSceneOrTable(page);
    if (UI_MAP['table-link'] && !await hook(page, 'scene-link').waitFor({timeout: 1500}).then(() => true, () => false)) {
      await tabTo(page, 'The Salt Road table', ([selector, title]) => !!document.activeElement?.closest(selector)?.textContent.includes(title),
        [sel('table-link'), 'The Salt Road']);
      await page.keyboard.press('Enter');
    }
    await hook(page, 'scene-link').waitFor();
    await tabTo(page, 'The scene link', ([selector, title]) => !!document.activeElement?.closest(selector)?.textContent.includes(title), [sel('scene-link'), 'Keyboard Crossing']);
    await page.keyboard.press('Enter');
    await hook(page, 'composer').waitFor();
    await tabTo(page, 'The composer', within, sel('composer'));
    await page.keyboard.type(words);
    await tabTo(page, 'Send', within, sel('send'));
    await page.keyboard.press('Enter');
    await until(async () => bodies(await scene(ash, id)).includes(words), 'A keyboard-only post was not kept');
    await ctx.close();
  });

  await check('keyboard_reaches_xcard', UI.keyboard_reaches_xcard, async () => {
    const ctx = await context(), page = await ctx.newPage();
    await signIn(page, ASH);
    await openScene(page, 'The Drowned Mile', () => hook(page, 'xcard').waitFor());
    await tabTo(page, 'The X-card', within, sel('xcard'));
    await ctx.close();
  });

  await check('no_external_requests', UI.no_external_requests, async () => assert.deepEqual(external, [], 'External requests: ' + external.join(', ')));
} catch (e) {
  for (const [name, ids] of Object.entries(UI)) if (!checks.some(c => c.name === name)) checks.push({name, ids, passed: false, error: e.message});
} finally {
  if (browser) await browser.close();
  fs.writeFileSync(path.join(artifacts, 'copy.json'), JSON.stringify({states: copy, unreached}, null, 2));
}
const result = {tests: checks.length, failures: checks.filter(c => !c.passed).length, errors: 0, skipped: 0, checks};
console.log('BENCHMARK_GRADE=' + JSON.stringify(result));
process.exitCode = result.failures ? 1 : 0;

})().catch(e => {
  console.error(e.stack);
  process.exitCode = 1;
});

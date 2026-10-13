const test = require("node:test");
const assert = require("node:assert/strict");

globalThis.window = globalThis;
require("./tickets.js");
require("./store.js");

const KEY = "support-tickets.v1";
const seeds = () => structuredClone(globalThis.SEED_TICKETS);

function fakeStorage(initial) {
  const data = new Map(initial === undefined ? [] : [[KEY, initial]]);
  const calls = {setItem: 0};
  return {
    calls,
    getItem: key => (data.has(key) ? data.get(key) : null),
    setItem: (key, value) => { calls.setItem += 1; data.set(key, value); },
  };
}

function openWith(initial) {
  const storage = fakeStorage(initial);
  const store = globalThis.TicketStore.open(storage, globalThis.SEED_TICKETS);
  return {storage, store};
}

function assertSeedsAndNoWrite(storage, store) {
  assert.deepEqual(store.all(), seeds());
  if (storage) assert.equal(storage.calls.setItem, 0);
}

test("exposes the frozen STATUSES and PRIORITIES", () => {
  assert.deepEqual(globalThis.TicketStore.STATUSES, ["open", "pending", "resolved"]);
  assert.deepEqual(globalThis.TicketStore.PRIORITIES, ["low", "medium", "high"]);
});

test("the seeded records are the twelve T001..T012 in order (FR-02)", () => {
  const all = seeds();
  assert.equal(all.length, 12);
  assert.deepEqual(all.map(ticket => ticket.id), Array.from({length: 12}, (_, i) => `T${String(i + 1).padStart(3, "0")}`));
  assert.deepEqual(all[0], {
    id: "T001",
    title: "Password reset link expired",
    customer: "Acme Labs",
    status: "open",
    priority: "high",
    description: "The reset link expires before the customer can use it.",
  });
});

test("open() on empty storage returns the 12 seeds unchanged and writes nothing", () => {
  const {storage, store} = openWith(undefined);
  assert.equal(store.all().length, 12);
  assertSeedsAndNoWrite(storage, store);
});

test("open() with corrupt JSON gives the seeds", () => {
  const {storage, store} = openWith("{not json");
  assertSeedsAndNoWrite(storage, store);
});

test("open() with a stored object instead of an array gives the seeds", () => {
  const {storage, store} = openWith(JSON.stringify({tickets: seeds()}));
  assertSeedsAndNoWrite(storage, store);
});

test("open() with an item missing description gives the seeds", () => {
  const stored = seeds();
  delete stored[3].description;
  const {storage, store} = openWith(JSON.stringify(stored));
  assertSeedsAndNoWrite(storage, store);
});

test("open() with a non-string field gives the seeds", () => {
  const stored = seeds();
  stored[2].title = 42;
  const {storage, store} = openWith(JSON.stringify(stored));
  assertSeedsAndNoWrite(storage, store);
});

test("open() with status closed gives the seeds", () => {
  const stored = seeds();
  stored[0].status = "closed";
  const {storage, store} = openWith(JSON.stringify(stored));
  assertSeedsAndNoWrite(storage, store);
});

test("open() with priority urgent gives the seeds", () => {
  const stored = seeds();
  stored[5].priority = "urgent";
  const {storage, store} = openWith(JSON.stringify(stored));
  assertSeedsAndNoWrite(storage, store);
});

test("open() with a throwing storage gives the seeds without throwing", () => {
  const storage = {getItem() { throw new Error("denied"); }, setItem() { throw new Error("denied"); }};
  let store;
  assert.doesNotThrow(() => { store = globalThis.TicketStore.open(storage, globalThis.SEED_TICKETS); });
  assertSeedsAndNoWrite(null, store);
});

test("open() with undefined storage gives the seeds without throwing", () => {
  let store;
  assert.doesNotThrow(() => { store = globalThis.TicketStore.open(undefined, globalThis.SEED_TICKETS); });
  assertSeedsAndNoWrite(null, store);
});

test("open() returns a valid stored array in stored order", () => {
  const stored = seeds();
  stored[0].status = "resolved";
  const {storage, store} = openWith(JSON.stringify(stored));
  assert.deepEqual(store.all(), stored);
  assert.equal(store.all()[0].status, "resolved");
  assert.equal(storage.calls.setItem, 0);
});

test("mutating the array or a ticket returned by all() does not change the store", () => {
  const {store} = openWith(undefined);
  const first = store.all();
  first[0].title = "changed";
  first.pop();
  first.push({id: "T999"});
  assert.deepEqual(store.all(), seeds());
});

const ids = tickets => tickets.map(ticket => ticket.id);
const filter = (criteria, tickets = seeds()) => globalThis.TicketStore.filter(tickets, criteria);

test("filter 'acme' returns T001, T005, T011 in order (FR-03)", () => {
  assert.deepEqual(ids(filter({query: "acme"})), ["T001", "T005", "T011"]);
});

test("filter 'EXPORT' returns T002 (FR-03)", () => {
  assert.deepEqual(ids(filter({query: "EXPORT"})), ["T002"]);
});

test("filter ignores whitespace around the query (FR-03)", () => {
  assert.deepEqual(ids(filter({query: "  acme \t"})), ["T001", "T005", "T011"]);
});

test("filter combines query, status and priority with AND: acme + pending + medium returns T005 (FR-04)", () => {
  assert.deepEqual(ids(filter({query: "acme", status: "pending", priority: "medium"})), ["T005"]);
});

test("filter by status alone returns exactly the tickets with that status, in order", () => {
  const expected = ids(seeds().filter(ticket => ticket.status === "resolved"));
  assert.equal(expected.length, 3);
  assert.deepEqual(ids(filter({status: "resolved"})), expected);
});

test("filter by priority alone returns exactly the tickets with that priority, in order", () => {
  const expected = ids(seeds().filter(ticket => ticket.priority === "high"));
  assert.ok(expected.length > 0 && expected.length < 12);
  assert.deepEqual(ids(filter({priority: "high"})), expected);
});

test("filter with no criteria or empty criteria returns every ticket in order", () => {
  const all = ids(seeds());
  assert.deepEqual(ids(filter(undefined)), all);
  assert.deepEqual(ids(filter({query: "", status: "", priority: ""})), all);
});

test("filter with no match returns an empty array", () => {
  assert.deepEqual(filter({query: "zzz"}), []);
});

test("filter does not mutate its input", () => {
  const input = seeds();
  const before = structuredClone(input);
  const result = filter({query: "acme"}, input);
  assert.deepEqual(input, before);
  assert.notEqual(result, input);
});

const edit = {status: "resolved", priority: "high"};

test("update persists the change and a reopened store returns it (FR-09, FR-17)", () => {
  const {storage, store} = openWith(undefined);
  const returned = store.update("T001", edit);
  const expected = seeds();
  Object.assign(expected[0], edit);
  assert.deepEqual(returned, expected[0]);
  assert.deepEqual(store.all(), expected);
  assert.equal(storage.calls.setItem, 1);
  assert.deepEqual(JSON.parse(storage.getItem(KEY)), expected);
  const reopened = globalThis.TicketStore.open(storage, globalThis.SEED_TICKETS);
  assert.deepEqual(reopened.all(), expected);
  assert.deepEqual(ids(reopened.all()), ids(seeds()));
});

test("update changes only status and priority and does not modify the seeds array", () => {
  const {store} = openWith(undefined);
  const before = structuredClone(globalThis.SEED_TICKETS);
  const returned = store.update("T003", {status: "pending", priority: "medium"});
  assert.equal(returned.status, "pending");
  assert.equal(returned.priority, "medium");
  const {status, priority, ...rest} = returned;
  const {status: s, priority: p, ...originalRest} = seeds()[2];
  assert.deepEqual(rest, originalRest);
  assert.deepEqual(globalThis.SEED_TICKETS, before);
  returned.title = "changed";
  assert.equal(store.all()[2].title, seeds()[2].title);
});

test("update with an unknown id returns null and writes nothing", () => {
  const {storage, store} = openWith(undefined);
  assert.equal(store.update("T999", edit), null);
  assert.equal(storage.calls.setItem, 0);
  assert.deepEqual(store.all(), seeds());
});

test("update with an invalid status throws RangeError and writes nothing", () => {
  const {storage, store} = openWith(undefined);
  assert.throws(() => store.update("T001", {status: "closed", priority: "high"}), RangeError);
  assert.equal(storage.calls.setItem, 0);
  assert.deepEqual(store.all(), seeds());
});

test("update with an invalid priority throws RangeError and writes nothing", () => {
  const {storage, store} = openWith(undefined);
  assert.throws(() => store.update("T001", {status: "open", priority: "urgent"}), RangeError);
  assert.equal(storage.calls.setItem, 0);
  assert.deepEqual(store.all(), seeds());
});

test("two stores over one storage keep both edits", () => {
  const storage = fakeStorage(undefined);
  const first = globalThis.TicketStore.open(storage, globalThis.SEED_TICKETS);
  const second = globalThis.TicketStore.open(storage, globalThis.SEED_TICKETS);
  first.update("T001", {status: "resolved", priority: "high"});
  second.update("T002", {status: "pending", priority: "low"});
  const expected = seeds();
  Object.assign(expected[0], {status: "resolved", priority: "high"});
  Object.assign(expected[1], {status: "pending", priority: "low"});
  const third = globalThis.TicketStore.open(storage, globalThis.SEED_TICKETS);
  assert.deepEqual(third.all(), expected);
  assert.deepEqual(second.all(), expected);
});

test("update keeps the change in memory when the write throws", () => {
  const storage = {getItem: () => null, setItem() { throw new Error("full"); }};
  const store = globalThis.TicketStore.open(storage, globalThis.SEED_TICKETS);
  let returned;
  assert.doesNotThrow(() => { returned = store.update("T001", edit); });
  assert.equal(returned.status, "resolved");
  assert.equal(store.all()[0].status, "resolved");
});

const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const TicketStore = require("./store.js");

const KEY = "support-tickets.v1";

function loadSeed() {
  const win = {};
  new Function("window", fs.readFileSync("./tickets.js", "utf8"))(win);
  return win.SEED_TICKETS;
}

function fakeStorage(initial) {
  const map = new Map(initial === undefined ? [] : [[KEY, initial]]);
  return {
    getItem: (key) => (map.has(key) ? map.get(key) : null),
    setItem: (key, value) => { map.set(key, String(value)); },
    removeItem: (key) => { map.delete(key); },
  };
}

const ids = (tickets) => tickets.map((ticket) => ticket.id);

test("open lists T001 to T012 in order", () => {
  const seed = loadSeed();
  const repo = TicketStore.open(fakeStorage(), seed);
  const tickets = repo.list();
  assert.deepStrictEqual(ids(tickets), seed.map((ticket) => ticket.id));
  assert.strictEqual(tickets.length, 12);
  assert.deepStrictEqual(tickets[0], seed[0]);
  assert.strictEqual(tickets[0].id, "T001");
  assert.strictEqual(tickets[0].title, "Password reset link expired");
  assert.strictEqual(tickets[0].customer, "Acme Labs");
  assert.strictEqual(tickets[0].status, "open");
  assert.strictEqual(tickets[0].priority, "high");
});

test("open falls back to the seed for non-JSON, a non-array, and a bad status", () => {
  const seed = loadSeed();
  const bad = [{...seed[0], status: "closed"}, ...seed.slice(1)];
  for (const stored of ["not json", "{}", JSON.stringify(bad)]) {
    const tickets = TicketStore.open(fakeStorage(stored), seed).list();
    assert.deepStrictEqual(tickets, seed, `stored value ${stored.slice(0, 20)}`);
    assert.strictEqual(tickets.length, 12);
  }
});

test("list matches title or customer case-insensitively", () => {
  const repo = TicketStore.open(fakeStorage(), loadSeed());
  assert.deepStrictEqual(ids(repo.list({query: "acme"})), ["T001", "T005", "T011"]);
  assert.deepStrictEqual(ids(repo.list({query: "RESET"})), ["T001"]);
  assert.deepStrictEqual(repo.list({query: "expired link"}), []);
});

test("list by status and priority", () => {
  const seed = loadSeed();
  const repo = TicketStore.open(fakeStorage(), seed);
  assert.deepStrictEqual(ids(repo.list({status: "pending"})), ["T003", "T005", "T006", "T010"]);
  assert.strictEqual(repo.list({status: ""}).length, 12);
  const high = repo.list({priority: "high"});
  assert.deepStrictEqual(ids(high), ids(seed.filter((ticket) => ticket.priority === "high")));
  assert.ok(high.length > 0 && high.every((ticket) => ticket.priority === "high"));
});

test("list combines criteria with AND", () => {
  const repo = TicketStore.open(fakeStorage(), loadSeed());
  assert.deepStrictEqual(ids(repo.list({query: "acme", status: "open", priority: "high"})), ["T001"]);
  assert.deepStrictEqual(repo.list({query: "acme", status: "resolved", priority: "low"}), []);
});

test("seed array stays untouched", () => {
  const seed = loadSeed();
  const original = JSON.parse(JSON.stringify(seed));
  const repo = TicketStore.open(fakeStorage(), seed);
  repo.list();
  const copy = repo.list();
  copy[0].title = "changed";
  copy.pop();
  assert.deepStrictEqual(seed, original);
  assert.deepStrictEqual(ids(seed), original.map((ticket) => ticket.id));
  assert.strictEqual(repo.list()[0].title, original[0].title);
});

test("get returns a copy and undefined for T999", () => {
  const seed = loadSeed();
  const repo = TicketStore.open(fakeStorage(), seed);
  const ticket = repo.get("T002");
  assert.deepStrictEqual(ticket, seed[1]);
  ticket.title = "changed";
  ticket.status = "resolved";
  assert.deepStrictEqual(repo.get("T002"), seed[1]);
  assert.strictEqual(repo.get("T999"), undefined);
});

test("update persists priority", () => {
  const seed = loadSeed();
  const storage = fakeStorage();
  const repo = TicketStore.open(storage, seed);
  const updated = repo.update("T002", {priority: "low"});
  assert.deepStrictEqual(updated, {...seed[1], priority: "low"});
  assert.strictEqual(repo.list().find((ticket) => ticket.id === "T002").priority, "low");
  const stored = JSON.parse(storage.getItem(KEY));
  assert.strictEqual(stored.length, 12);
  assert.deepStrictEqual(stored[1], {...seed[1], priority: "low"});
});

test("update throws RangeError for status \"closed\" with nothing stored", () => {
  const seed = loadSeed();
  const storage = fakeStorage();
  const repo = TicketStore.open(storage, seed);
  assert.throws(() => repo.update("T002", {status: "closed"}), RangeError);
  assert.throws(() => repo.update("T002", {priority: "urgent"}), RangeError);
  assert.strictEqual(storage.getItem(KEY), null);
  assert.deepStrictEqual(repo.get("T002"), seed[1]);
});

test("update returns undefined for an unknown ID and stores nothing", () => {
  const storage = fakeStorage();
  const repo = TicketStore.open(storage, loadSeed());
  assert.strictEqual(repo.update("T999", {status: "resolved"}), undefined);
  assert.strictEqual(storage.getItem(KEY), null);
});

test("a new open on the same storage returns the update", () => {
  const seed = loadSeed();
  const storage = fakeStorage();
  TicketStore.open(storage, seed).update("T001", {status: "resolved"});
  assert.strictEqual(TicketStore.open(storage, seed).get("T001").status, "resolved");
});

test("two repos on one fake storage keep both repos' edits", () => {
  const seed = loadSeed();
  const storage = fakeStorage();
  const repoA = TicketStore.open(storage, seed);
  const repoB = TicketStore.open(storage, seed);
  repoA.update("T001", {status: "resolved"});
  repoB.update("T002", {priority: "low"});
  const fresh = TicketStore.open(storage, seed);
  assert.strictEqual(fresh.get("T001").status, "resolved");
  assert.strictEqual(fresh.get("T002").priority, "low");
});

const valid = {title: "Printer jam", customer: "Zed Corp", description: "Jams", status: "open", priority: "medium"};

test("create trims '  Printer jam  ' and stores the trimmed title", () => {
  const storage = fakeStorage();
  const repo = TicketStore.open(storage, loadSeed());
  const result = repo.create({...valid, title: "  Printer jam  ", customer: " Zed Corp ", description: " Jams "});
  assert.strictEqual(result.ticket.title, "Printer jam");
  assert.strictEqual(result.ticket.customer, "Zed Corp");
  assert.strictEqual(result.ticket.description, "Jams");
  const stored = JSON.parse(storage.getItem(KEY));
  assert.strictEqual(stored.length, 13);
  assert.strictEqual(stored[12].title, "Printer jam");
});

test("create returns one error per whitespace-only field and stores nothing", () => {
  const storage = fakeStorage();
  const repo = TicketStore.open(storage, loadSeed());
  const result = repo.create({...valid, title: "   ", customer: "\t", description: " \n "});
  assert.strictEqual(result.ticket, undefined);
  assert.deepStrictEqual(result.errors, {
    title: "Title is required",
    customer: "Customer is required",
    description: "Description is required",
  });
  assert.strictEqual(storage.getItem(KEY), null);
  assert.strictEqual(repo.list().length, 12);
});

test("create issues T013, T014, then T015 after reopening", () => {
  const seed = loadSeed();
  const storage = fakeStorage();
  const repo = TicketStore.open(storage, seed);
  assert.strictEqual(repo.create(valid).ticket.id, "T013");
  assert.strictEqual(repo.create(valid).ticket.id, "T014");
  assert.strictEqual(TicketStore.open(storage, seed).create(valid).ticket.id, "T015");
});

test("two repos never issue the same ID and keep each other's edits on create", () => {
  const seed = loadSeed();
  const storage = fakeStorage();
  const repoA = TicketStore.open(storage, seed);
  const repoB = TicketStore.open(storage, seed);
  repoA.update("T001", {status: "resolved"});
  assert.strictEqual(repoB.create(valid).ticket.id, "T013");
  assert.strictEqual(repoA.create(valid).ticket.id, "T014");
  const fresh = TicketStore.open(storage, seed);
  assert.strictEqual(fresh.get("T001").status, "resolved");
  assert.ok(fresh.get("T013"));
  assert.ok(fresh.get("T014"));
});

test("create throws RangeError for an out-of-set status and stores nothing", () => {
  const storage = fakeStorage();
  const repo = TicketStore.open(storage, loadSeed());
  assert.throws(() => repo.create({...valid, status: "closed"}), RangeError);
  assert.throws(() => repo.create({...valid, priority: "urgent"}), RangeError);
  assert.strictEqual(storage.getItem(KEY), null);
  assert.strictEqual(repo.list().length, 12);
});

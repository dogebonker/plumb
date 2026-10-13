const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

if (!process.env.PLAYWRIGHT_MODULE) throw new Error("PLAYWRIGHT_MODULE is required; no runtime will be installed or skipped.");
const {chromium} = require(process.env.PLAYWRIGHT_MODULE);
const {expect} = require(path.join(process.env.PLAYWRIGHT_MODULE, "test"));

const KEY = "support-tickets.v1";
let server, browser, baseUrl;

test.before(async () => {
  const root = process.cwd();
  server = http.createServer((request, response) => {
    const pathname = new URL(request.url, "http://localhost").pathname;
    const file = path.resolve(root, "." + decodeURIComponent(pathname === "/" ? "/index.html" : pathname));
    if (!file.startsWith(root + path.sep)) { response.writeHead(403).end(); return; }
    fs.readFile(file, (error, data) => {
      if (error) { response.writeHead(404).end(); return; }
      response.setHeader("Content-Type", {".html": "text/html", ".js": "text/javascript", ".css": "text/css"}[path.extname(file)] || "application/octet-stream");
      response.end(data);
    });
  });
  await new Promise((resolve, reject) => { server.once("error", reject); server.listen(0, "127.0.0.1", resolve); });
  baseUrl = `http://127.0.0.1:${server.address().port}`;
  browser = await chromium.launch({headless: true});
});

test.after(async () => {
  if (browser) await browser.close();
  if (server) await new Promise(resolve => server.close(resolve));
});

// Fresh browser context (and so fresh localStorage) per test.
async function withPage(fn, {before, viewport} = {}) {
  const context = await browser.newContext({viewport});
  try {
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", error => errors.push(error));
    await page.goto(baseUrl);
    if (before) { await before(page); await page.reload(); }
    await fn(page, errors);
    assert.deepEqual(errors.map(String), [], "no uncaught page errors");
  } finally {
    await context.close();
  }
}

const openers = page => page.getByRole("button", {name: /T\d{3}/});
const count = page => page.getByRole("status");
const search = page => page.getByLabel("Search tickets", {exact: true});
const status = page => page.getByLabel("Status filter", {exact: true});
const priority = page => page.getByLabel("Priority filter", {exact: true});
const ids = page => page.locator("#tickets li").evaluateAll(items => items.map(li => li.textContent.match(/T\d{3}/)[0]));

test("shows 12 openers, each row with ID, title, customer, status and priority", () => withPage(async page => {
  await expect(openers(page)).toHaveCount(12);
  await expect(count(page)).toHaveText("12 tickets");
  await expect(search(page)).toHaveCount(1);
  const first = page.locator("#tickets li").first();
  for (const text of ["T001", "Password reset link expired", "Acme Labs", "open", "high"]) {
    await expect(first).toContainText(text);
  }
  await expect(page.getByRole("button", {name: "T001 Password reset link expired"})).toBeVisible();
  await expect(page.locator("#empty-state")).toBeHidden();
}));

test("search 'acme' gives 3 results and '3 tickets'", () => withPage(async page => {
  await search(page).fill("acme");
  await expect(openers(page)).toHaveCount(3);
  await expect(count(page)).toHaveText("3 tickets");
  assert.deepEqual(await ids(page), ["T001", "T005", "T011"]);
}));

test("search is case-insensitive and trims; ID-only query does not match", () => withPage(async page => {
  await search(page).fill("NORTHWIND");
  assert.deepEqual(await ids(page), ["T002", "T006"]);
  await search(page).fill("  northwind  ");
  assert.deepEqual(await ids(page), ["T002", "T006"]);
  await search(page).fill("T001");
  await expect(openers(page)).toHaveCount(0);
  await expect(count(page)).toHaveText("0 tickets");
}));

test("search matches title and customer only, not description", () => withPage(async page => {
  await search(page).fill("PASSWORD RESET");
  assert.deepEqual(await ids(page), ["T001"]);
  await search(page).fill("bluebird");
  assert.deepEqual(await ids(page), ["T003", "T010"]);
  // "CSV" and "invoice contact" appear only in descriptions.
  for (const query of ["CSV", "invoice contact"]) {
    await search(page).fill(query);
    await expect(openers(page)).toHaveCount(0);
    await expect(page.locator("#empty-state")).toBeVisible();
    await expect(count(page)).toHaveText("0 tickets");
  }
}));

test("singular count reads '1 ticket'", () => withPage(async page => {
  await search(page).fill("acme");
  await status(page).selectOption({label: "pending"});
  await expect(count(page)).toHaveText("1 ticket");
}));

test("search 'acme' plus status pending gives exactly T005", () => withPage(async page => {
  await search(page).fill("acme");
  await status(page).selectOption("pending");
  assert.deepEqual(await ids(page), ["T005"]);
}));

test("priority filter ANDs with status; 'all' options restore the full set", () => withPage(async page => {
  await status(page).selectOption("open");
  await priority(page).selectOption("high");
  assert.deepEqual(await ids(page), ["T001", "T002"]);
  await status(page).selectOption({label: "All statuses"});
  assert.deepEqual(await ids(page), ["T001", "T002", "T006", "T011"]); // high priority, any status
  await priority(page).selectOption({label: "All priorities"});
  await expect(openers(page)).toHaveCount(12);
  await expect(count(page)).toHaveText("12 tickets");
}));

test("no-match search shows the empty state and '0 tickets'", () => withPage(async page => {
  await search(page).fill("zzzz-no-such-thing");
  await expect(openers(page)).toHaveCount(0);
  await expect(page.locator("#empty-state")).toBeVisible();
  await expect(page.locator("#empty-state")).toHaveText("No tickets match your filters.");
  await expect(count(page)).toHaveText("0 tickets");
  await search(page).fill("");
  await expect(page.locator("#empty-state")).toBeHidden();
  await expect(openers(page)).toHaveCount(12);
}));

test("Reset filters clears all three controls and shows 12 again", () => withPage(async page => {
  await search(page).fill("acme");
  await status(page).selectOption("pending");
  await priority(page).selectOption("medium");
  await expect(openers(page)).toHaveCount(1);
  await page.getByRole("button", {name: "Reset filters"}).click();
  await expect(search(page)).toHaveValue("");
  await expect(status(page)).toHaveValue("");
  await expect(priority(page)).toHaveValue("");
  await expect(openers(page)).toHaveCount(12);
  await expect(count(page)).toHaveText("12 tickets");
}));

test("regex-literal queries are plain substrings and do not throw", () => withPage(async page => {
  for (const query of ["(", ".*", "[", "\\"]) {
    await search(page).fill(query);
    await expect(openers(page)).toHaveCount(0);
    await expect(page.locator("#empty-state")).toBeVisible();
    await expect(count(page)).toHaveText("0 tickets");
  }
}));

test("corrupt, non-array or malformed localStorage falls back to 12 seeds", async () => {
  for (const bad of ["{not json", "null", "{\"a\":1}", "\"text\"", "[1,2]", "[{\"id\":\"T001\"}]"]) {
    await withPage(async page => {
      await expect(openers(page)).toHaveCount(12);
      await expect(count(page)).toHaveText("12 tickets");
    }, {before: page => page.evaluate(([k, v]) => localStorage.setItem(k, v), [KEY, bad])});
  }
});

test("stored tickets are loaded and saveTickets persists across reload", async () => {
  await withPage(async page => {
    await expect(openers(page)).toHaveCount(13);
    await expect(page.getByRole("button", {name: /T013 Stored one/})).toBeVisible();
    await page.evaluate(() => { state.tickets[0].title = "Edited title"; saveTickets(); render(); });
    await page.reload();
    await expect(page.getByRole("button", {name: /T001 Edited title/})).toBeVisible();
    const stored = await page.evaluate(k => JSON.parse(localStorage.getItem(k)), KEY);
    assert.equal(stored.length, 13);
  }, {before: page => page.evaluate(k => {
    localStorage.setItem(k, JSON.stringify([...window.SEED_TICKETS, {id: "T013", title: "Stored one", customer: "Zed", status: "open", priority: "low", description: "d"}]));
  }, KEY)});
});

test("ticket text is rendered as text, never markup", async () => {
  await withPage(async page => {
    await expect(page.getByRole("button", {name: /T013 <b>x<\/b>/})).toBeVisible();
    assert.equal(await page.locator("#tickets b").count(), 0);
    assert.equal(await page.locator("#tickets img").count(), 0);
  }, {before: page => page.evaluate(k => {
    const t = (id, title, customer) => ({id, title, customer, status: "open", priority: "low", description: "d"});
    localStorage.setItem(k, JSON.stringify([...window.SEED_TICKETS, t("T013", "<b>x</b>", "<img src=x onerror=alert(1)>")]));
  }, KEY)});
});

test("seed tickets are unchanged and state is a copy", () => withPage(async page => {
  const result = await page.evaluate(() => ({seeds: window.SEED_TICKETS.length, same: state.tickets !== window.SEED_TICKETS && state.tickets[0] !== window.SEED_TICKETS[0], filters: state.filters}));
  assert.equal(result.seeds, 12);
  assert.equal(result.same, true);
  assert.deepEqual(result.filters, {query: "", status: "", priority: ""});
}));

// ---- Ticket details dialog ----
const rowButton = (page, id) => page.getByRole("button", {name: new RegExp(`${id}\\b`)});
const details = page => page.getByRole("dialog", {name: "Ticket details", exact: true});
const dStatus = page => details(page).getByLabel("Status", {exact: true});
const dPriority = page => details(page).getByLabel("Priority", {exact: true});
const inDialog = page => page.evaluate(() => Boolean(document.activeElement && document.activeElement.closest("dialog[open]")));
const stored = page => page.evaluate(k => JSON.parse(localStorage.getItem(k)), KEY);

test("opening T001 shows the Ticket details dialog with its fields", () => withPage(async page => {
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await rowButton(page, "T001").click();
  const dialog = details(page);
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("heading", {name: "Ticket details"})).toBeVisible();
  for (const text of ["Password reset link expired", "Acme Labs"]) await expect(dialog).toContainText(text);
  const description = await page.evaluate(() => state.tickets[0].description);
  assert.ok(description.length > 0);
  await expect(dialog).toContainText(description);
  await expect(dStatus(page)).toHaveValue("open");
  await expect(dPriority(page)).toHaveValue("high");
  await expect(dialog.getByRole("button", {name: "Save changes", exact: true})).toBeVisible();
  await expect(dialog.getByRole("button", {name: "Cancel", exact: true})).toBeVisible();
  assert.equal(await page.evaluate(() => document.querySelector("dialog[open]").matches(":modal")), true);
}));

test("ticket details show markup-like text as text", async () => {
  await withPage(async page => {
    await rowButton(page, "T013").click();
    const dialog = details(page);
    await expect(dialog).toContainText("<b>x</b>");
    await expect(dialog).toContainText("<i>desc</i>");
    assert.equal(await dialog.locator("b, i, img").count(), 0);
  }, {before: page => page.evaluate(k => {
    localStorage.setItem(k, JSON.stringify([...window.SEED_TICKETS, {id: "T013", title: "<b>x</b>", customer: "<img src=x onerror=alert(1)>", status: "open", priority: "low", description: "<i>desc</i>"}]));
  }, KEY)});
});

test("Save changes updates the row, storage, and survives reload", () => withPage(async page => {
  await rowButton(page, "T001").click();
  await dStatus(page).selectOption("resolved");
  await dPriority(page).selectOption("low");
  await details(page).getByRole("button", {name: "Save changes", exact: true}).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  const row = page.locator("#tickets li").first();
  await expect(row).toContainText("resolved");
  await expect(row).toContainText("low");
  await expect(row).not.toContainText("high");
  await expect(rowButton(page, "T001")).toBeFocused();
  await page.reload();
  const first = page.locator("#tickets li").first();
  await expect(first).toContainText("resolved");
  await expect(first).toContainText("low");
  const t1 = (await stored(page)).find(t => t.id === "T001");
  assert.equal(t1.status, "resolved");
  assert.equal(t1.priority, "low");
  assert.equal(t1.title, "Password reset link expired");
  await rowButton(page, "T001").click();
  await expect(dStatus(page)).toHaveValue("resolved");
  await expect(dPriority(page)).toHaveValue("low");
}));

test("Cancel leaves the ticket unchanged; reopening shows stored values", () => withPage(async page => {
  const before = await page.evaluate(() => JSON.stringify(state.tickets));
  await rowButton(page, "T001").click();
  await dStatus(page).selectOption("resolved");
  await dPriority(page).selectOption("low");
  await details(page).getByRole("button", {name: "Cancel", exact: true}).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(rowButton(page, "T001")).toBeFocused();
  assert.equal(await page.evaluate(() => JSON.stringify(state.tickets)), before);
  await expect(page.locator("#tickets li").first()).toContainText("high");
  await rowButton(page, "T001").click();
  await expect(dStatus(page)).toHaveValue("open");
  await expect(dPriority(page)).toHaveValue("high");
  // Nothing was ever written by cancelling.
  assert.equal(await page.evaluate(k => localStorage.getItem(k), KEY), null);
}));

test("Escape dismisses without saving and returns focus to the opener", () => withPage(async page => {
  const before = await page.evaluate(() => JSON.stringify(state.tickets));
  await rowButton(page, "T003").click();
  await expect(details(page)).toBeVisible();
  await dStatus(page).selectOption("resolved");
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(rowButton(page, "T003")).toBeFocused();
  assert.equal(await page.evaluate(() => JSON.stringify(state.tickets)), before);
  assert.equal(await page.evaluate(k => localStorage.getItem(k), KEY), null);
  await rowButton(page, "T003").click();
  const original = await page.evaluate(() => state.tickets.find(t => t.id === "T003").status);
  await expect(dStatus(page)).toHaveValue(original);
  // A second open/Escape cycle still works.
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(rowButton(page, "T003")).toBeFocused();
}));

test("Tab and Shift+Tab stay inside the dialog and wrap", () => withPage(async page => {
  await rowButton(page, "T001").click();
  await expect(details(page)).toBeVisible();
  const label = () => page.evaluate(() => document.activeElement.id || document.activeElement.textContent.trim());
  const seen = [];
  for (let i = 0; i < 8; i++) {
    await page.keyboard.press("Tab");
    assert.equal(await inDialog(page), true, `Tab #${i + 1} left the dialog`);
    seen.push(await label());
  }
  assert.ok(new Set(seen).size >= 4, `expected to cycle through 4+ controls, saw ${seen}`);
  const last = details(page).getByRole("button", {name: "Cancel", exact: true});
  await last.focus();
  await page.keyboard.press("Tab");
  await expect(dStatus(page)).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(last).toBeFocused();
  for (let i = 0; i < 8; i++) {
    await page.keyboard.press("Shift+Tab");
    assert.equal(await inDialog(page), true, `Shift+Tab #${i + 1} left the dialog`);
  }
}));

test("edited ticket honours the active filters after saving", () => withPage(async page => {
  await status(page).selectOption("open");
  await priority(page).selectOption("high");
  assert.deepEqual(await ids(page), ["T001", "T002"]);
  await rowButton(page, "T001").click();
  await dStatus(page).selectOption("resolved");
  await details(page).getByRole("button", {name: "Save changes", exact: true}).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  assert.deepEqual(await ids(page), ["T002"]);
  await expect(count(page)).toHaveText("1 ticket");
  assert.equal(await page.evaluate(() => document.activeElement === document.body), false, "focus must not be lost");
  // Filters are untouched, and the edited ticket is still stored.
  await expect(status(page)).toHaveValue("open");
  assert.equal((await stored(page)).find(t => t.id === "T001").status, "resolved");
  await page.getByRole("button", {name: "Reset filters"}).click();
  await expect(openers(page)).toHaveCount(12);
}));

test("dialog fits at 360px width without clipped controls or page overflow", async () => {
  const context = await browser.newContext({viewport: {width: 360, height: 640}});
  try {
    const page = await context.newPage();
    await page.goto(baseUrl);
    await rowButton(page, "T001").click();
    await expect(details(page)).toBeVisible();
    const result = await page.evaluate(() => {
      const dialog = document.querySelector("dialog[open]");
      const box = dialog.getBoundingClientRect();
      const controls = [...dialog.querySelectorAll("select, button")].map(c => c.getBoundingClientRect());
      return {
        pageOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        dialogOverflow: dialog.scrollWidth - dialog.clientWidth,
        dialogInViewport: box.left >= 0 && box.right <= window.innerWidth,
        controlsInside: controls.every(r => r.left >= box.left && r.right <= box.right && r.width > 0),
      };
    });
    assert.deepEqual(result, {pageOverflow: 0, dialogOverflow: 0, dialogInViewport: true, controlsInside: true});
  } finally {
    await context.close();
  }
});

// ---- New ticket dialog ----
const newButton = page => page.getByRole("button", {name: "New ticket", exact: true});
const newDialog = page => page.getByRole("dialog", {name: "New ticket", exact: true});
const nField = (page, label) => newDialog(page).getByLabel(label, {exact: true});
const createButton = page => newDialog(page).getByRole("button", {name: "Create ticket", exact: true});
const openNew = async page => { await newButton(page).click(); await expect(newDialog(page)).toBeVisible(); };
const fillNew = async (page, {title = "", customer = "", description = "", status: s, priority: p} = {}) => {
  await nField(page, "Title").fill(title);
  await nField(page, "Customer").fill(customer);
  await nField(page, "Description").fill(description);
  if (s) await nField(page, "Status").selectOption(s);
  if (p) await nField(page, "Priority").selectOption(p);
};
const FIELDS = ["Title", "Customer", "Description"];
const stateIds = page => page.evaluate(() => state.tickets.map(t => t.id));

async function createPrinterJam(page) {
  await openNew(page);
  await fillNew(page, {title: "  Printer jam  ", customer: "  Zed Co ", description: " Jammed ", status: "pending", priority: "high"});
  await createButton(page).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
}

test("New ticket button opens a dialog named New ticket with labelled fields and defaults", () => withPage(async page => {
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(newButton(page)).toHaveCount(1);
  await openNew(page);
  const dialog = newDialog(page);
  await expect(dialog.getByRole("heading", {name: "New ticket"})).toBeVisible();
  for (const label of FIELDS) await expect(nField(page, label)).toBeVisible();
  assert.equal(await nField(page, "Description").evaluate(n => n.tagName), "TEXTAREA");
  await expect(nField(page, "Status")).toHaveValue("open");
  await expect(nField(page, "Priority")).toHaveValue("medium");
  await expect(createButton(page)).toBeVisible();
  await expect(dialog.getByRole("button", {name: "Cancel", exact: true})).toBeVisible();
  assert.equal(await page.evaluate(() => document.querySelector("dialog[open]").matches(":modal")), true);
  assert.equal(await dialog.locator("form").getAttribute("novalidate"), "");
  assert.equal(await page.evaluate(() => typeof nextId === "function" && typeof validateNew === "function"), true);
}));

test("empty submit keeps the dialog open, creates nothing, and reports each field accessibly", () => withPage(async page => {
  await openNew(page);
  await createButton(page).click();
  await expect(newDialog(page)).toBeVisible();
  assert.equal((await stateIds(page)).length, 12);
  assert.equal(await page.evaluate(k => localStorage.getItem(k), KEY), null);
  const messages = new Set();
  for (const label of FIELDS) {
    const field = nField(page, label);
    await expect(field).toHaveAttribute("aria-invalid", "true");
    const describedBy = await field.getAttribute("aria-describedby");
    assert.ok(describedBy, `${label} needs aria-describedby`);
    const message = page.locator(`#${describedBy}`);
    await expect(message).toBeVisible();
    assert.ok((await message.textContent()).trim().length > 0, `${label} error text`);
    messages.add(describedBy);
  }
  assert.equal(messages.size, 3, "one distinct message per field");
  assert.equal(await newDialog(page).locator(".error:not([hidden])").count(), 3);
  await expect(nField(page, "Title")).toBeFocused();
  await expect(nField(page, "Status")).not.toHaveAttribute("aria-invalid", "true");
}));

test("focus moves to the first invalid field and errors clear as fields become valid", () => withPage(async page => {
  await openNew(page);
  await fillNew(page, {title: "Has title", customer: "   ", description: ""});
  await createButton(page).click();
  await expect(nField(page, "Customer")).toBeFocused();
  await expect(nField(page, "Title")).not.toHaveAttribute("aria-invalid", "true");
  await expect(nField(page, "Title")).not.toHaveAttribute("aria-describedby", /.+/);
  await expect(newDialog(page).locator(".error:not([hidden])")).toHaveCount(2);
  await fillNew(page, {title: "Has title", customer: "Cust", description: ""});
  await createButton(page).click();
  await expect(nField(page, "Description")).toBeFocused();
  await expect(newDialog(page).locator(".error:not([hidden])")).toHaveCount(1);
  await expect(nField(page, "Customer")).not.toHaveAttribute("aria-invalid", "true");
  assert.equal((await stateIds(page)).length, 12);
}));

test("whitespace-only values are invalid", () => withPage(async page => {
  await openNew(page);
  await fillNew(page, {title: "   ", customer: " \t ", description: "  "});
  await createButton(page).click();
  await expect(newDialog(page)).toBeVisible();
  for (const label of FIELDS) await expect(nField(page, label)).toHaveAttribute("aria-invalid", "true");
  assert.equal((await stateIds(page)).length, 12);
  assert.equal(await page.evaluate(k => localStorage.getItem(k), KEY), null);
}));

test("valid submission stores trimmed values as T013, lists it, and survives reload", () => withPage(async page => {
  await createPrinterJam(page);
  await expect(page.locator("#tickets li")).toHaveCount(13);
  await expect(count(page)).toHaveText("13 tickets");
  await expect(rowButton(page, "T013")).toHaveAccessibleName(/T013\s+Printer jam/);
  await expect(newButton(page)).toBeFocused();
  const expected = {id: "T013", title: "Printer jam", customer: "Zed Co", description: "Jammed", status: "pending", priority: "high"};
  assert.deepEqual((await stored(page)).at(-1), expected);
  await page.reload();
  await expect(page.locator("#tickets li")).toHaveCount(13);
  const row = page.locator("#tickets li").filter({hasText: "T013"});
  for (const text of ["Printer jam", "Zed Co", "pending", "high"]) await expect(row).toContainText(text);
  assert.deepEqual((await stored(page)).at(-1), expected);
}));

test("new ticket can be searched, opened, and edited like seeded ones", () => withPage(async page => {
  await createPrinterJam(page);
  await search(page).fill("PRINTER");
  assert.deepEqual(await ids(page), ["T013"]);
  await search(page).fill("zed co");
  assert.deepEqual(await ids(page), ["T013"]);
  await rowButton(page, "T013").click();
  const dialog = details(page);
  for (const text of ["Printer jam", "Zed Co", "Jammed"]) await expect(dialog).toContainText(text);
  await expect(dStatus(page)).toHaveValue("pending");
  await expect(dPriority(page)).toHaveValue("high");
  await dStatus(page).selectOption("resolved");
  await dPriority(page).selectOption("low");
  await dialog.getByRole("button", {name: "Save changes", exact: true}).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.reload();
  const t13 = (await stored(page)).find(t => t.id === "T013");
  assert.equal(t13.status, "resolved");
  assert.equal(t13.priority, "low");
  assert.equal(t13.title, "Printer jam");
}));

test("Cancel creates nothing and returns focus to New ticket", () => withPage(async page => {
  await openNew(page);
  await fillNew(page, {title: "Draft", customer: "Draft", description: "Draft"});
  await newDialog(page).getByRole("button", {name: "Cancel", exact: true}).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(newButton(page)).toBeFocused();
  assert.equal((await stateIds(page)).length, 12);
  assert.equal(await page.evaluate(k => localStorage.getItem(k), KEY), null);
}));

test("Escape creates nothing and returns focus to New ticket", () => withPage(async page => {
  await openNew(page);
  await fillNew(page, {title: "Draft", customer: "Draft", description: "Draft"});
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(newButton(page)).toBeFocused();
  assert.equal((await stateIds(page)).length, 12);
  assert.equal(await page.evaluate(k => localStorage.getItem(k), KEY), null);
  // Escape also works while errors are showing.
  await openNew(page);
  await createButton(page).click();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(newButton(page)).toBeFocused();
  assert.equal((await stateIds(page)).length, 12);
}));

test("double click and re-entrant submits create exactly one ticket", () => withPage(async page => {
  await openNew(page);
  await fillNew(page, {title: "Once", customer: "Only", description: "One"});
  await createButton(page).dblclick();
  await expect(page.getByRole("dialog")).toHaveCount(0); // the tail of the double-click must not open details either
  assert.equal((await stateIds(page)).filter(id => id === "T013").length, 1);
  assert.equal((await stored(page)).filter(t => t.title === "Once").length, 1);
  assert.equal((await stateIds(page)).length, 13);
  assert.equal(new Set(await stateIds(page)).size, 13);
  // Two submits in one task, and a submit after the dialog closed.
  await openNew(page);
  await fillNew(page, {title: "Twice", customer: "Only", description: "Two"});
  await page.evaluate(() => {
    const form = document.querySelector("dialog[open] form");
    form.requestSubmit();
    form.requestSubmit();
  });
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.evaluate(() => document.querySelector("#new-ticket-dialog form").requestSubmit());
  assert.deepEqual((await stateIds(page)).slice(12), ["T013", "T014"]);
}));

test("IDs come from the max numeric suffix, not the array length, and persist across reload", async () => {
  await withPage(async page => {
    await createPrinterJam(page);
    await page.reload();
    await openNew(page);
    await fillNew(page, {title: "Second", customer: "Zed Co", description: "Again"});
    await createButton(page).click();
    await expect(page.getByRole("dialog")).toHaveCount(0);
    assert.deepEqual((await stored(page)).slice(12).map(t => t.id), ["T013", "T014"]);
  });
  await withPage(async page => {
    const result = await page.evaluate(() => ({
      empty: nextId([]),
      seeds: nextId(window.SEED_TICKETS),
      gap: nextId([{id: "T001"}, {id: "T020"}, {id: "T003"}]),
      noisy: nextId([{id: "T007"}, {id: "abc"}, {id: "T"}]),
      wide: nextId([{id: "T999"}]),
      wider: nextId([{id: "T1000"}]),
    }));
    assert.deepEqual(result, {empty: "T001", seeds: "T013", gap: "T021", noisy: "T008", wide: "T1000", wider: "T1001"});
    const validated = await page.evaluate(() => validateNew({title: " a ", customer: " ", description: "\n", status: "open", priority: "low"}));
    assert.deepEqual(Object.keys(validated.errors).sort(), ["customer", "description"]);
    assert.equal(validated.clean.title, "a");
  });
  await withPage(async page => {
    await openNew(page);
    await fillNew(page, {title: "After gap", customer: "C", description: "D"});
    await createButton(page).click();
    await expect(page.getByRole("dialog")).toHaveCount(0);
    assert.equal((await stored(page)).at(-1).id, "T021");
  }, {before: page => page.evaluate(k => {
    localStorage.setItem(k, JSON.stringify(window.SEED_TICKETS.filter(t => t.id !== "T012" && t.id !== "T005").concat([{id: "T020", title: "Far", customer: "F", status: "open", priority: "low", description: "d"}])));
  }, KEY)});
});

test("reopening the dialog shows a clean form with no stale errors", () => withPage(async page => {
  const assertClean = async () => {
    for (const label of FIELDS) {
      await expect(nField(page, label)).toHaveValue("");
      await expect(nField(page, label)).not.toHaveAttribute("aria-invalid", /.*/);
      await expect(nField(page, label)).not.toHaveAttribute("aria-describedby", /.*/);
    }
    await expect(nField(page, "Status")).toHaveValue("open");
    await expect(nField(page, "Priority")).toHaveValue("medium");
    await expect(newDialog(page).locator(".error:not([hidden])")).toHaveCount(0);
    assert.equal(await newDialog(page).locator(".error").evaluateAll(nodes => nodes.filter(n => n.textContent.trim()).length), 0);
  };
  await openNew(page);
  await createButton(page).click();
  await expect(newDialog(page).locator(".error:not([hidden])")).toHaveCount(3);
  await newDialog(page).getByRole("button", {name: "Cancel", exact: true}).click();
  await openNew(page);
  await assertClean();
  await fillNew(page, {title: "Typed", customer: "Typed", description: "Typed", status: "resolved", priority: "low"});
  await page.keyboard.press("Escape");
  await openNew(page);
  await assertClean();
  await page.keyboard.press("Escape");
  await createPrinterJam(page);
  await openNew(page);
  await assertClean();
}));

test("HTML in a new ticket title renders as text", () => withPage(async page => {
  await openNew(page);
  await fillNew(page, {title: "<b>Bold</b> <img src=x onerror=alert(1)>", customer: "<i>Cust</i>", description: "<u>d</u>"});
  await createButton(page).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(rowButton(page, "T013")).toContainText("<b>Bold</b>");
  assert.equal(await page.locator("#tickets b, #tickets img, #tickets i").count(), 0);
  await rowButton(page, "T013").click();
  await expect(details(page)).toContainText("<u>d</u>");
  assert.equal(await details(page).locator("b, i, u, img").count(), 0);
}));

test("Tab stays inside the New ticket dialog", () => withPage(async page => {
  await openNew(page);
  for (let i = 0; i < 9; i++) {
    await page.keyboard.press("Tab");
    assert.equal(await inDialog(page), true, `Tab #${i + 1} left the dialog`);
  }
  for (let i = 0; i < 9; i++) {
    await page.keyboard.press("Shift+Tab");
    assert.equal(await inDialog(page), true, `Shift+Tab #${i + 1} left the dialog`);
  }
}));

test("New ticket dialog fits at 360px, also while showing errors", async () => {
  const context = await browser.newContext({viewport: {width: 360, height: 640}});
  try {
    const page = await context.newPage();
    await page.goto(baseUrl);
    await openNew(page);
    await createButton(page).click();
    await expect(newDialog(page).locator(".error:not([hidden])")).toHaveCount(3);
    await nField(page, "Title").fill("x".repeat(200));
    const result = await page.evaluate(() => {
      const dialog = document.querySelector("dialog[open]");
      const box = dialog.getBoundingClientRect();
      const controls = [...dialog.querySelectorAll("input, select, textarea, button")].map(c => c.getBoundingClientRect());
      return {
        pageOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        dialogOverflow: dialog.scrollWidth - dialog.clientWidth,
        dialogInViewport: box.left >= 0 && box.right <= window.innerWidth,
        controlsInside: controls.length === 7 && controls.every(r => r.left >= box.left && r.right <= box.right && r.width > 0),
      };
    });
    assert.deepEqual(result, {pageOverflow: 0, dialogOverflow: 0, dialogInViewport: true, controlsInside: true});
  } finally {
    await context.close();
  }
});

test("a ticket created while filters would hide it clears the filters and shows its row", () => withPage(async page => {
  await status(page).selectOption("resolved");
  await search(page).fill("zzz");
  await expect(count(page)).toHaveText("0 tickets");
  await openNew(page);
  await fillNew(page, {title: "Hidden otherwise", customer: "Newco", description: "d", status: "pending", priority: "low"});
  await createButton(page).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(search(page)).toHaveValue("");
  await expect(status(page)).toHaveValue("");
  await expect(priority(page)).toHaveValue("");
  await expect(count(page)).toHaveText("13 tickets");
  await expect(rowButton(page, "T013")).toBeVisible();
  await expect(rowButton(page, "T013")).toBeFocused();
  assert.equal((await stored(page)).length, 13);
  assert.equal((await stored(page)).filter(t => t.id !== "T013").length, 12);
  // A matching ticket keeps the active filters and focus returns to the New ticket button.
  await status(page).selectOption("pending");
  await openNew(page);
  await fillNew(page, {title: "Visible", customer: "Newco", description: "d", status: "pending"});
  await createButton(page).click();
  await expect(status(page)).toHaveValue("pending");
  await expect(rowButton(page, "T014")).toBeVisible();
  await expect(newButton(page)).toBeFocused();
}));

test("a normal single click on a row still opens details; a click with detail > 1 does not", () => withPage(async page => {
  await page.evaluate(() => document.querySelector("button.ticket").dispatchEvent(new MouseEvent("click", {bubbles: true, detail: 2})));
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await rowButton(page, "T002").click();
  await expect(details(page)).toBeVisible();
  await page.keyboard.press("Escape");
  await rowButton(page, "T002").focus();
  await page.keyboard.press("Enter");
  await expect(details(page)).toBeVisible();
}));

// ---- Task 4: responsive layout, visual hierarchy and focus ----
const PHONE = {width: 360, height: 740};
const LONG = "x".repeat(200);
const withLongTicket = page => page.evaluate(([k, long]) => {
  localStorage.setItem(k, JSON.stringify([...window.SEED_TICKETS, {id: "T013", title: long, customer: "c".repeat(120), status: "pending", priority: "high", description: "d".repeat(300)}]));
}, [KEY, LONG]);
const overflow = page => page.evaluate(() => ({scroll: document.documentElement.scrollWidth, inner: window.innerWidth}));
const noOverflow = async (page, where) => {
  const {scroll, inner} = await overflow(page);
  assert.ok(scroll <= inner, `horizontal page overflow ${where}: scrollWidth ${scroll} > innerWidth ${inner}`);
};
const buttonsInViewport = (page, where) => page.evaluate(() => [...document.querySelectorAll("dialog[open] button")].map(b => {
  const r = b.getBoundingClientRect();
  return {name: b.textContent.trim(), ok: r.width > 0 && r.left >= 0 && r.top >= 0 && r.right <= window.innerWidth && r.bottom <= window.innerHeight};
})).then(list => {
  assert.ok(list.length >= 2, `${where}: expected dialog buttons`);
  assert.deepEqual(list.filter(b => !b.ok), [], `${where}: dialog buttons outside the viewport`);
});

test("360x740: no horizontal overflow initially, with a 200-char unbroken title, and with each dialog open", async () => {
  await withPage(async page => {
    await expect(openers(page)).toHaveCount(12);
    await noOverflow(page, "initially");
  }, {viewport: PHONE});
  await withPage(async page => {
    await expect(openers(page)).toHaveCount(13);
    await expect(rowButton(page, "T013")).toContainText(LONG);
    await noOverflow(page, "with a 200-char title");
    await search(page).fill("x".repeat(30));
    await expect(openers(page)).toHaveCount(1);
    await noOverflow(page, "filtered to the long ticket");
    await rowButton(page, "T013").click();
    await expect(details(page)).toBeVisible();
    await noOverflow(page, "with the details dialog open (long ticket)");
    await buttonsInViewport(page, "details dialog (long ticket)");
    await page.keyboard.press("Escape");
    await openNew(page);
    await noOverflow(page, "with the new ticket dialog open");
    await buttonsInViewport(page, "new ticket dialog");
    await createButton(page).click();
    await nField(page, "Title").fill(LONG);
    await nField(page, "Customer").fill(LONG);
    await noOverflow(page, "new ticket dialog with errors and long input");
    await buttonsInViewport(page, "new ticket dialog with errors");
  }, {before: withLongTicket, viewport: PHONE});
  await withPage(async page => {
    await rowButton(page, "T001").click();
    await expect(details(page)).toBeVisible();
    await noOverflow(page, "with the details dialog open");
    await buttonsInViewport(page, "details dialog");
  }, {viewport: PHONE});
});

test("a short viewport keeps dialogs inside it and scrollable", () => withPage(async page => {
  await openNew(page);
  const result = await page.evaluate(() => {
    const dialog = document.querySelector("dialog[open]");
    const r = dialog.getBoundingClientRect();
    return {inside: r.top >= 0 && r.bottom <= window.innerHeight, scrolls: dialog.scrollHeight > dialog.clientHeight, overflowY: getComputedStyle(dialog).overflowY};
  });
  assert.equal(result.inside, true, "dialog taller than the viewport");
  assert.equal(result.scrolls, true, "content should overflow and scroll at this height");
  assert.ok(["auto", "scroll"].includes(result.overflowY));
  await createButton(page).scrollIntoViewIfNeeded();
  const box = await createButton(page).boundingBox();
  assert.ok(box.y >= 0 && box.y + box.height <= 300, "buttons are reachable by scrolling the dialog");
}, {viewport: {width: 360, height: 300}}));

const outlineOf = page => page.evaluate(() => {
  const el = document.activeElement;
  const cs = getComputedStyle(el);
  return {tag: el.tagName, id: el.id || el.dataset.id || el.textContent.trim().slice(0, 20), style: cs.outlineStyle, width: parseFloat(cs.outlineWidth), color: cs.outlineColor};
});
const assertVisibleOutline = (o, where) => {
  assert.ok(o.style !== "none" && o.width >= 2 && o.color !== "rgba(0, 0, 0, 0)", `no visible focus outline on ${o.tag} ${o.id} ${where}: ${JSON.stringify(o)}`);
};

for (const [label, viewport] of [["desktop", {width: 1280, height: 800}], ["360px", PHONE]]) {
  test(`focused controls show a visible outline (${label})`, () => withPage(async page => {
    const seen = new Set();
    for (let i = 0; i < 17; i++) {
      await page.keyboard.press("Tab");
      const o = await outlineOf(page);
      assert.notEqual(o.tag, "BODY", "focus must reach every control");
      assertVisibleOutline(o, `on the page (${label})`);
      seen.add(o.tag + o.id);
    }
    assert.equal(seen.size, 17, "5 controls + 12 rows each receive focus");
    await rowButton(page, "T001").click();
    await expect(details(page)).toBeVisible();
    for (let i = 0; i < 5; i++) { await page.keyboard.press("Tab"); assertVisibleOutline(await outlineOf(page), `in the details dialog (${label})`); }
    await page.keyboard.press("Escape");
    await openNew(page);
    for (let i = 0; i < 9; i++) { await page.keyboard.press("Tab"); assertVisibleOutline(await outlineOf(page), `in the new ticket dialog (${label})`); }
  }, {viewport}));
}

test("keyboard-only: Tab to a ticket, Enter opens it, Escape closes it and returns focus", () => withPage(async page => {
  let reached = false;
  for (let i = 0; i < 10 && !reached; i++) {
    await page.keyboard.press("Tab");
    reached = await page.evaluate(() => document.activeElement.matches("button.ticket"));
  }
  assert.ok(reached, "Tab never reached a ticket button");
  await expect(rowButton(page, "T001")).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(details(page)).toBeVisible();
  assert.equal(await inDialog(page), true);
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(rowButton(page, "T001")).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(rowButton(page, "T002")).toBeFocused();
}, {viewport: PHONE}));

test("details dialog labels the read-only title field 'Title'", () => withPage(async page => {
  await rowButton(page, "T001").click();
  const labels = await details(page).locator("dt").allTextContents();
  assert.deepEqual(labels, ["Title", "Customer", "Description"]);
}));

const channel = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
const luminance = ([r, g, b]) => 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
const ratio = (a, b) => { const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x); return (hi + 0.05) / (lo + 0.05); };
const rgb = css => css.match(/[\d.]+/g).slice(0, 3).map(Number);

test("visual hierarchy: bold ID and title, muted customer; coloured, textual, AA-contrast badges", () => withPage(async page => {
  const info = await page.evaluate(() => {
    const css = (node, prop) => getComputedStyle(node)[prop];
    const first = document.querySelector("#tickets li");
    const button = first.querySelector("button.ticket");
    const badges = [...document.querySelectorAll("#tickets .badge")].map(b => ({kind: b.classList.contains("status") ? "status" : "priority", text: b.textContent.trim(), bg: css(b, "backgroundColor"), fg: css(b, "color")}));
    return {
      id: css(first.querySelector(".ticket-id"), "fontWeight"),
      title: css(first.querySelector(".ticket-title"), "fontWeight"),
      customerWeight: css(first.querySelector(".ticket-customer"), "fontWeight"),
      customerColor: css(first.querySelector(".ticket-customer"), "color"),
      titleColor: css(first.querySelector(".ticket-title"), "color"),
      rowBg: css(button, "backgroundColor"),
      customerSize: parseFloat(css(first.querySelector(".ticket-customer"), "fontSize")),
      titleSize: parseFloat(css(first.querySelector(".ticket-title"), "fontSize")),
      badges,
    };
  });
  assert.ok(Number(info.id) >= 600 && Number(info.title) >= 600, "ID and title must be bold");
  assert.ok(Number(info.customerWeight) < 600, "customer must not be bold");
  assert.notEqual(info.customerColor, info.titleColor, "customer must be muted relative to the title");
  assert.ok(ratio(rgb(info.customerColor), rgb(info.rowBg)) >= 4.5, "muted customer text must keep AA contrast");
  assert.ok(ratio(rgb(info.titleColor), rgb(info.rowBg)) >= 7, "title contrast");
  for (const kind of ["status", "priority"]) {
    const of = info.badges.filter(b => b.kind === kind);
    assert.equal(new Set(of.map(b => b.text)).size, 3, `all three ${kind} values appear in the seeds`);
    assert.equal(new Set(of.map(b => b.bg)).size, 3, `each ${kind} value has its own colour`);
  }
  for (const b of info.badges) {
    assert.ok(b.text.length > 0);
    assert.ok(ratio(rgb(b.fg), rgb(b.bg)) >= 4.5, `badge ${b.kind} ${b.text}: contrast ${ratio(rgb(b.fg), rgb(b.bg)).toFixed(2)} < 4.5`);
  }
}));

test("dialog heading, labels and error text keep AA contrast", () => withPage(async page => {
  await openNew(page);
  await createButton(page).click();
  const pairs = await page.evaluate(() => {
    const dialog = document.querySelector("dialog[open]");
    const bg = getComputedStyle(dialog).backgroundColor;
    return [".error:not([hidden])", "label", "h2"].map(sel => ({sel, fg: getComputedStyle(dialog.querySelector(sel)).color, bg}));
  });
  for (const p of pairs) assert.ok(ratio(rgb(p.fg), rgb(p.bg)) >= 4.5, `${p.sel} contrast`);
}));

test("short viewport: a focused field is never hidden behind the sticky actions bar", () => withPage(async page => {
  const fieldsClear = () => page.evaluate(() => {
    const dialog = document.querySelector("dialog[open]");
    const bar = dialog.querySelector(".actions").getBoundingClientRect();
    const box = dialog.getBoundingClientRect();
    const el = document.activeElement;
    const r = el.getBoundingClientRect();
    return {id: el.id, bottom: r.bottom, top: r.top, barTop: bar.top, dialogTop: box.top, ok: r.bottom <= bar.top && r.top >= box.top};
  });
  const walk = async (labels, where) => {
    for (const label of labels) {
      await page.locator("dialog[open]").getByLabel(label, {exact: true}).focus();
      const r = await fieldsClear();
      assert.ok(r.ok, `${where}: focused ${label} (#${r.id}) hidden: ${JSON.stringify(r)}`);
    }
    // Keyboard order too: Tab through the whole dialog, checking every field.
    for (let i = 0; i < 10; i++) {
      await page.keyboard.press("Tab");
      const r = await page.evaluate(() => document.activeElement.matches("input, select, textarea"));
      if (r) { const c = await fieldsClear(); assert.ok(c.ok, `${where}: Tab to #${c.id} hidden: ${JSON.stringify(c)}`); }
    }
  };
  await rowButton(page, "T001").click();
  await expect(details(page)).toBeVisible();
  assert.equal(await page.evaluate(() => { const d = document.querySelector("dialog[open]"); return d.scrollHeight > d.clientHeight; }), true, "details dialog should scroll at 300px");
  await walk(["Status", "Priority"], "details dialog");
  await page.keyboard.press("Escape");
  await openNew(page);
  await walk(["Title", "Customer", "Description", "Status", "Priority"], "new ticket dialog");
}, {viewport: {width: 360, height: 300}}));

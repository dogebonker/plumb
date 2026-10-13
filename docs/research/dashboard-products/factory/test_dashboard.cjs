const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

if (!process.env.PLAYWRIGHT_MODULE) throw new Error("PLAYWRIGHT_MODULE is required; no runtime will be installed or skipped.");
const {chromium} = require(process.env.PLAYWRIGHT_MODULE);
const {expect} = require(path.join(process.env.PLAYWRIGHT_MODULE, "test"));

globalThis.window = globalThis;
require("./tickets.js");
const seeds = globalThis.SEED_TICKETS;
const KEY = "support-tickets.v1";

let server;
let browser;
let origin;

test.before(async () => {
  const root = process.cwd();
  server = http.createServer((request, response) => {
    const pathname = new URL(request.url, "http://localhost").pathname;
    const file = path.resolve(root, "." + (pathname === "/" ? "/index.html" : decodeURIComponent(pathname)));
    if (!file.startsWith(root + path.sep)) { response.writeHead(403).end(); return; }
    fs.readFile(file, (error, data) => {
      if (error) { response.writeHead(404).end(); return; }
      response.setHeader("Content-Type", {".html": "text/html", ".js": "text/javascript", ".css": "text/css"}[path.extname(file)] || "application/octet-stream");
      response.end(data);
    });
  });
  await new Promise((resolve, reject) => { server.once("error", reject); server.listen(0, "127.0.0.1", resolve); });
  origin = `http://127.0.0.1:${server.address().port}`;
  browser = await chromium.launch({headless: true});
});

test.after(async () => {
  if (browser) await browser.close();
  if (server) await new Promise(resolve => server.close(resolve));
});

// Opens the dashboard in a fresh page; `stored`, when given, is put in localStorage before the page scripts run.
async function openDashboard({stored} = {}) {
  const page = await browser.newPage();
  const requests = [];
  page.on("request", request => requests.push(request.url()));
  if (stored !== undefined) {
    await page.addInitScript(([key, value]) => localStorage.setItem(key, value), [KEY, stored]);
  }
  await page.goto(origin);
  return {page, requests};
}

test("lists all 12 seeded tickets with ID, title, customer, status and priority", async () => {
  const {page} = await openDashboard();
  try {
    const rows = page.locator("#tickets > li > button.ticket[data-id]");
    await expect(rows).toHaveCount(12);
    for (const [index, ticket] of seeds.entries()) {
      const row = rows.nth(index);
      await expect(row).toHaveAttribute("data-id", ticket.id);
      await expect(row).toContainText(`${ticket.id} ${ticket.title}`);
      await expect(row).toContainText(ticket.customer);
      await expect(row).toContainText(`${ticket.status} · ${ticket.priority}`);
    }
    await expect(page.getByRole("button", {name: /T\d{3}/})).toHaveCount(12);
    const first = rows.first();
    await expect(first).toContainText("T001 Password reset link expired");
    await expect(first).toContainText("Acme Labs");
    await expect(first).toContainText("open · high");
  } finally {
    await page.close();
  }
});

test("the result count reads 12 tickets", async () => {
  const {page} = await openDashboard();
  try {
    await expect(page.getByRole("status")).toHaveText("12 tickets");
  } finally {
    await page.close();
  }
});

test("makes no request outside 127.0.0.1", async () => {
  const {page, requests} = await openDashboard();
  try {
    await expect(page.getByRole("status")).toHaveText("12 tickets");
    assert.ok(requests.length > 0);
    for (const url of requests) {
      assert.ok(url.startsWith(origin) || url.startsWith("data:") || url.startsWith("blob:"), `unexpected request ${url}`);
    }
  } finally {
    await page.close();
  }
});

test("rebuilds the list from stored tickets on load: T001 stored as resolved shows resolved · high", async () => {
  const stored = seeds.map(ticket => ticket.id === "T001" ? {...ticket, status: "resolved"} : ticket);
  const {page} = await openDashboard({stored: JSON.stringify(stored)});
  try {
    const row = page.locator('button.ticket[data-id="T001"]');
    await expect(row).toContainText("resolved · high");
    await expect(row).not.toContainText("open · high");
    await expect(page.locator("#tickets > li > button.ticket")).toHaveCount(12);
  } finally {
    await page.close();
  }
});

test("shows the 12 seeds when the stored value is not JSON", async () => {
  const {page} = await openDashboard({stored: "{not json"});
  try {
    const rows = page.locator("#tickets > li > button.ticket[data-id]");
    await expect(rows).toHaveCount(12);
    await expect(rows.first()).toContainText("T001 Password reset link expired");
    await expect(rows.first()).toContainText("open · high");
    await expect(page.getByRole("status")).toHaveText("12 tickets");
  } finally {
    await page.close();
  }
});

const rowIds = page => page.locator("#tickets > li > button.ticket").evaluateAll(rows => rows.map(row => row.dataset.id));
const idsWhere = predicate => seeds.filter(predicate).map(ticket => ticket.id);

test("typing 'acme' narrows the list to T001, T005, T011 and 'EXPORT' to T002", async () => {
  const {page} = await openDashboard();
  try {
    await page.getByLabel("Search tickets").fill("acme");
    await expect(page.locator("#tickets > li > button.ticket")).toHaveCount(3);
    assert.deepEqual(await rowIds(page), ["T001", "T005", "T011"]);
    await page.getByLabel("Search tickets").fill("EXPORT");
    await expect(page.locator("#tickets > li > button.ticket")).toHaveCount(1);
    assert.deepEqual(await rowIds(page), ["T002"]);
  } finally {
    await page.close();
  }
});

test("search 'acme' with status pending and priority medium shows T005 only", async () => {
  const {page} = await openDashboard();
  try {
    await page.getByLabel("Search tickets").fill("acme");
    await page.getByLabel("Status filter").selectOption("pending");
    await page.getByLabel("Priority filter").selectOption("medium");
    await expect(page.locator("#tickets > li > button.ticket")).toHaveCount(1);
    assert.deepEqual(await rowIds(page), ["T005"]);
  } finally {
    await page.close();
  }
});

test("filtering by status resolved shows the resolved tickets and the count '3 tickets'", async () => {
  const {page} = await openDashboard();
  try {
    await page.getByLabel("Status filter").selectOption("resolved");
    await expect(page.getByRole("status")).toHaveText("3 tickets");
    assert.deepEqual(await rowIds(page), idsWhere(ticket => ticket.status === "resolved"));
  } finally {
    await page.close();
  }
});

test("a single match reads '1 ticket'", async () => {
  const {page} = await openDashboard();
  try {
    await page.getByLabel("Search tickets").fill("EXPORT");
    await expect(page.getByRole("status")).toHaveText("1 ticket");
    await expect(page.locator("#empty-state")).toBeHidden();
  } finally {
    await page.close();
  }
});

test("no match shows 'No tickets match your filters.', '0 tickets' and no rows", async () => {
  const {page} = await openDashboard();
  try {
    await page.getByLabel("Search tickets").fill("zzz");
    await expect(page.locator("#empty-state")).toBeVisible();
    await expect(page.locator("#empty-state")).toHaveText("No tickets match your filters.");
    await expect(page.getByRole("status")).toHaveText("0 tickets");
    await expect(page.locator("#tickets > li > button.ticket")).toHaveCount(0);
  } finally {
    await page.close();
  }
});

test("Reset filters clears all three controls, restores the 12 rows and leaves storage untouched", async () => {
  const {page} = await openDashboard();
  try {
    await page.getByLabel("Search tickets").fill("zzz");
    await page.getByLabel("Status filter").selectOption("resolved");
    await page.getByLabel("Priority filter").selectOption("high");
    await expect(page.locator("#empty-state")).toBeVisible();
    await page.getByRole("button", {name: "Reset filters"}).click();
    await expect(page.getByLabel("Search tickets")).toHaveValue("");
    await expect(page.getByLabel("Status filter")).toHaveValue("");
    await expect(page.getByLabel("Priority filter")).toHaveValue("");
    await expect(page.locator("#tickets > li > button.ticket")).toHaveCount(12);
    assert.deepEqual(await rowIds(page), seeds.map(ticket => ticket.id));
    await expect(page.getByRole("status")).toHaveText("12 tickets");
    await expect(page.locator("#empty-state")).toBeHidden();
    assert.equal(await page.evaluate(key => localStorage.getItem(key), KEY), null);
  } finally {
    await page.close();
  }
});

test("Reset filters leaves stored tickets unchanged", async () => {
  const stored = JSON.stringify(seeds.map(ticket => ticket.id === "T001" ? {...ticket, status: "resolved"} : ticket));
  const {page} = await openDashboard({stored});
  try {
    await page.getByLabel("Search tickets").fill("zzz");
    await expect(page.locator("#empty-state")).toBeVisible();
    await page.getByRole("button", {name: "Reset filters"}).click();
    await expect(page.locator("#tickets > li > button.ticket")).toHaveCount(12);
    await expect(page.locator('button.ticket[data-id="T001"]')).toContainText("resolved · high");
    assert.equal(await page.evaluate(key => localStorage.getItem(key), KEY), stored);
  } finally {
    await page.close();
  }
});

const detailsDialog = page => page.getByRole("dialog", {name: "Ticket details"});
const activeId = page => page.evaluate(() => document.activeElement.dataset.id ?? document.activeElement.id);
const storedValue = page => page.evaluate(key => localStorage.getItem(key), KEY);

test("opening T002 shows its title, customer, description, status and priority in Ticket details (FR-08)", async () => {
  const {page} = await openDashboard();
  try {
    await page.locator('button.ticket[data-id="T002"]').click();
    const dialog = detailsDialog(page);
    await expect(dialog).toBeVisible();
    await expect(dialog).toContainText("Export stalls at ninety percent");
    await expect(dialog).toContainText("Northwind");
    await expect(dialog).toContainText("The monthly CSV export never finishes.");
    await expect(dialog.getByLabel("Status")).toHaveValue("open");
    await expect(dialog.getByLabel("Priority")).toHaveValue("high");
    await expect(page.getByRole("button", {name: /T\d{3}/})).toHaveCount(12);
  } finally {
    await page.close();
  }
});

test("saving T001 as resolved updates the list and survives reload (FR-09)", async () => {
  const {page} = await openDashboard();
  try {
    const row = page.locator('button.ticket[data-id="T001"]');
    await row.click();
    const dialog = detailsDialog(page);
    await dialog.getByLabel("Status").selectOption("resolved");
    await dialog.getByRole("button", {name: "Save changes"}).click();
    await expect(dialog).toBeHidden();
    await expect(row).toContainText("resolved · high");
    assert.equal(await activeId(page), "T001");
    const stored = JSON.parse(await storedValue(page));
    assert.equal(stored.find(ticket => ticket.id === "T001").status, "resolved");
    assert.equal(stored.length, 12);
    await page.reload();
    await expect(page.locator('button.ticket[data-id="T001"]')).toContainText("resolved · high");
    await expect(page.locator("#tickets > li > button.ticket")).toHaveCount(12);
  } finally {
    await page.close();
  }
});

for (const [name, dismiss] of [
  ["Cancel", page => detailsDialog(page).getByRole("button", {name: "Cancel"}).click()],
  ["Escape", page => page.keyboard.press("Escape")],
]) {
  test(`${name} leaves T003 low and returns focus to its row button (FR-10)`, async () => {
    const {page} = await openDashboard();
    try {
      const row = page.locator('button.ticket[data-id="T003"]');
      await expect(row).toContainText("pending · low");
      await row.click();
      const dialog = detailsDialog(page);
      await dialog.getByLabel("Priority").selectOption("high");
      await dismiss(page);
      await expect(dialog).toBeHidden();
      await expect(row).toContainText("pending · low");
      await expect(row).not.toContainText("high");
      assert.equal(await activeId(page), "T003");
      assert.equal(await storedValue(page), null);
    } finally {
      await page.close();
    }
  });
}

test("Tab and Shift+Tab cycle inside the details dialog (FR-16, SYS-NFR-02)", async () => {
  const {page} = await openDashboard();
  try {
    await page.locator('button.ticket[data-id="T001"]').click();
    const dialog = detailsDialog(page);
    await expect(dialog).toBeVisible();
    await dialog.getByRole("button", {name: "Cancel"}).focus();
    await page.keyboard.press("Tab");
    assert.equal(await activeId(page), "details-status");
    await page.keyboard.press("Shift+Tab");
    assert.equal(await activeId(page), "details-cancel");
    await page.locator("#details-status").focus();
    await page.keyboard.press("Shift+Tab");
    assert.equal(await activeId(page), "details-cancel");
  } finally {
    await page.close();
  }
});

const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

if (!process.env.PLAYWRIGHT_MODULE) throw new Error("PLAYWRIGHT_MODULE is required; no runtime will be installed or skipped.");
const {chromium} = require(process.env.PLAYWRIGHT_MODULE);

function startServer() {
  const root = process.cwd();
  const server = http.createServer((request, response) => {
    const pathname = new URL(request.url, "http://localhost").pathname;
    const file = path.resolve(root, "." + decodeURIComponent(pathname === "/" ? "/index.html" : pathname));
    if (!file.startsWith(root + path.sep)) { response.writeHead(403).end(); return; }
    fs.readFile(file, (error, data) => {
      if (error) { response.writeHead(404).end(); return; }
      response.setHeader("Content-Type", {".html": "text/html", ".js": "text/javascript", ".css": "text/css"}[path.extname(file)] || "application/octet-stream");
      response.end(data);
    });
  });
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => resolve(server));
  });
}

// Runs body(page) in a fresh browser context so localStorage starts empty.
async function withPage(body) {
  const server = await startServer();
  let browser;
  try {
    browser = await chromium.launch({headless: true});
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.goto(`http://127.0.0.1:${server.address().port}`);
    await body(page);
  } finally {
    if (browser) await browser.close();
    await new Promise((resolve) => server.close(resolve));
  }
}

const rows = (page) => page.getByRole("button", {name: /T\d{3}/});
const search = (page) => page.getByLabel("Search tickets", {exact: true});
const statusFilter = (page) => page.getByRole("combobox", {name: "Status filter"});
const priorityFilter = (page) => page.getByRole("combobox", {name: "Priority filter"});
const rowIds = async (page) => (await rows(page).allInnerTexts()).map((text) => text.match(/T\d{3}/)[0]);

test("first visit lists the twelve seeded tickets", async () => {
  await withPage(async (page) => {
    assert.strictEqual(await rows(page).count(), 12);
    const first = page.getByRole("button", {name: /T001/});
    const text = await first.innerText();
    for (const part of ["Password reset link expired", "Acme Labs", "open", "high"]) {
      assert.ok(text.includes(part), `T001 shows ${part}`);
    }
  });
});

test("first visit shows 12 ticket buttons named with ID and title, rendered from the store", async () => {
  await withPage(async (page) => {
    assert.strictEqual(await page.evaluate(() => typeof window.TicketStore), "object");
    const seed = await page.evaluate(() => window.SEED_TICKETS.map(({id, title}) => ({id, title})));
    assert.strictEqual(seed.length, 12);
    for (const {id, title} of seed) {
      const name = new RegExp(`(?=.*\\b${id}\\b)(?=.*${title.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`);
      assert.strictEqual(await page.getByRole("button", {name}).count(), 1, `${id} ${title}`);
    }
  });
});

test("search, status and priority filters combine", async () => {
  await withPage(async (page) => {
    await search(page).fill("acme");
    assert.deepStrictEqual(await rowIds(page), ["T001", "T005", "T011"]);
    await statusFilter(page).selectOption("open");
    await priorityFilter(page).selectOption("high");
    assert.deepStrictEqual(await rowIds(page), ["T001"]);
    await search(page).fill("");
    await priorityFilter(page).selectOption("");
    await statusFilter(page).selectOption("pending");
    assert.deepStrictEqual(await rowIds(page), ["T003", "T005", "T006", "T010"]);
  });
});

test("count text and empty message", async () => {
  await withPage(async (page) => {
    const status = page.getByRole("status");
    const empty = page.getByText("No tickets match your filters.");
    await search(page).fill("zzz");
    assert.strictEqual((await status.innerText()).trim(), "0 tickets");
    assert.strictEqual(await empty.isVisible(), true);
    assert.strictEqual(await rows(page).count(), 0);
    await search(page).fill("");
    assert.strictEqual((await status.innerText()).trim(), "12 tickets");
    assert.strictEqual(await empty.isVisible(), false);
    await search(page).fill("RESET");
    assert.strictEqual((await status.innerText()).trim(), "1 ticket");
    assert.deepStrictEqual(await rowIds(page), ["T001"]);
  });
});

test("Reset filters restores everything", async () => {
  await withPage(async (page) => {
    await search(page).fill("acme");
    await statusFilter(page).selectOption("open");
    assert.ok((await rows(page).count()) < 12);
    await page.getByRole("button", {name: "Reset filters"}).click();
    assert.strictEqual(await search(page).inputValue(), "");
    assert.strictEqual(await statusFilter(page).locator("option:checked").innerText(), "All statuses");
    assert.strictEqual(await priorityFilter(page).locator("option:checked").innerText(), "All priorities");
    assert.strictEqual(await rows(page).count(), 12);
    assert.strictEqual((await page.getByRole("status").innerText()).trim(), "12 tickets");
  });
});

const details = (page) => page.getByRole("dialog", {name: "Ticket details"});
const statusSelect = (page) => details(page).getByLabel("Status", {exact: true});
const prioritySelect = (page) => details(page).getByLabel("Priority", {exact: true});
const openTicket = (page, id) => page.getByRole("button", {name: new RegExp(id)}).click();
const rowText = (page, id) => page.getByRole("button", {name: new RegExp(id)}).innerText();
const insideDialog = (page) => page.evaluate(() => !!document.activeElement.closest("dialog[open]"));

test("opening T002 shows its details", async () => {
  await withPage(async (page) => {
    await openTicket(page, "T002");
    const dialog = details(page);
    assert.strictEqual(await dialog.isVisible(), true);
    const text = await dialog.innerText();
    for (const part of ["Export stalls at ninety percent", "Northwind", "The monthly CSV export never finishes."]) {
      assert.ok(text.includes(part), `dialog shows ${part}`);
    }
    assert.strictEqual(await statusSelect(page).inputValue(), "open");
    assert.strictEqual(await prioritySelect(page).inputValue(), "high");
  });
});

test("Save changes updates the row and survives reload", async () => {
  await withPage(async (page) => {
    await openTicket(page, "T002");
    await prioritySelect(page).selectOption("low");
    await details(page).getByRole("button", {name: "Save changes"}).click();
    assert.strictEqual(await details(page).isVisible(), false);
    assert.ok((await rowText(page, "T002")).includes("low"));
    await page.reload();
    assert.ok((await rowText(page, "T002")).includes("low"));
  });
});

test("a ticket that stops matching the status filter leaves the list", async () => {
  await withPage(async (page) => {
    await statusFilter(page).selectOption("open");
    const before = await rows(page).count();
    const status = page.getByRole("status");
    assert.strictEqual((await status.innerText()).trim(), `${before} tickets`);
    await openTicket(page, "T002");
    await statusSelect(page).selectOption("resolved");
    await details(page).getByRole("button", {name: "Save changes"}).click();
    assert.strictEqual(await rows(page).count(), before - 1);
    assert.strictEqual((await status.innerText()).trim(), `${before - 1} tickets`);
    assert.ok(!(await rowIds(page)).includes("T002"));
  });
});

test("Cancel and Escape change nothing", async () => {
  await withPage(async (page) => {
    await openTicket(page, "T002");
    await statusSelect(page).selectOption("pending");
    await details(page).getByRole("button", {name: "Cancel"}).click();
    assert.strictEqual(await details(page).isVisible(), false);
    assert.ok((await rowText(page, "T002")).includes("open"));
    await openTicket(page, "T002");
    assert.strictEqual(await statusSelect(page).inputValue(), "open");
    await statusSelect(page).selectOption("pending");
    await page.keyboard.press("Escape");
    assert.strictEqual(await details(page).isVisible(), false);
    assert.ok((await rowText(page, "T002")).includes("open"));
    await page.reload();
    assert.ok((await rowText(page, "T002")).includes("open"));
  });
});

test("focus returns to the ticket's button after Escape, Cancel and Save", async () => {
  await withPage(async (page) => {
    const focusedId = () => page.evaluate(() => (document.activeElement.textContent.match(/T\d{3}/) || [document.activeElement.id])[0]);
    await openTicket(page, "T003");
    await page.keyboard.press("Escape");
    assert.strictEqual(await focusedId(), "T003");
    await openTicket(page, "T003");
    await details(page).getByRole("button", {name: "Cancel"}).click();
    assert.strictEqual(await focusedId(), "T003");
    await openTicket(page, "T003");
    await details(page).getByRole("button", {name: "Save changes"}).click();
    assert.strictEqual(await focusedId(), "T003");
    await statusFilter(page).selectOption("open");
    await openTicket(page, "T002");
    await statusSelect(page).selectOption("resolved");
    await details(page).getByRole("button", {name: "Save changes"}).click();
    assert.strictEqual(await focusedId(), "search");
  });
});

test("Tab and Shift+Tab stay inside the dialog", async () => {
  await withPage(async (page) => {
    await openTicket(page, "T002");
    assert.strictEqual(await insideDialog(page), true);
    for (let i = 0; i < 8; i++) {
      await page.keyboard.press("Tab");
      assert.strictEqual(await insideDialog(page), true, `Tab ${i + 1}`);
    }
    await page.evaluate(() => document.querySelector("dialog[open]").querySelector("select, button, input, textarea").focus());
    for (let i = 0; i < 8; i++) {
      await page.keyboard.press("Shift+Tab");
      assert.strictEqual(await insideDialog(page), true, `Shift+Tab ${i + 1}`);
    }
  });
});

const newTicketButton = (page) => page.getByRole("button", {name: "New ticket", exact: true});
const creating = (page) => page.getByRole("dialog", {name: "New ticket"});
const field = (page, name) => creating(page).getByLabel(name, {exact: true});
const fillNew = async (page, values) => {
  for (const [name, value] of Object.entries(values)) {
    if (name === "Status" || name === "Priority") await field(page, name).selectOption(value);
    else await field(page, name).fill(value);
  }
};
const create = (page) => creating(page).getByRole("button", {name: "Create ticket"}).click();
const focusedLabel = (page) => page.evaluate(() => document.activeElement.textContent.trim());

test("New ticket opens an empty form with open and medium", async () => {
  await withPage(async (page) => {
    await newTicketButton(page).click();
    assert.strictEqual(await creating(page).isVisible(), true);
    for (const name of ["Title", "Customer", "Description"]) assert.strictEqual(await field(page, name).inputValue(), "", name);
    assert.strictEqual(await field(page, "Status").inputValue(), "open");
    assert.strictEqual(await field(page, "Priority").inputValue(), "medium");
  });
});

test("invalid submit keeps the dialog open with an associated error and no new row", async () => {
  await withPage(async (page) => {
    await newTicketButton(page).click();
    await fillNew(page, {Title: "   ", Customer: "Acme", Description: "x"});
    await create(page);
    assert.strictEqual(await creating(page).isVisible(), true);
    const title = field(page, "Title");
    assert.strictEqual(await title.getAttribute("aria-invalid"), "true");
    const errorId = await title.getAttribute("aria-describedby");
    assert.ok(errorId, "Title has aria-describedby");
    const text = await page.evaluate((id) => document.getElementById(id.split(" ")[0]).textContent.trim(), errorId);
    assert.strictEqual(text, "Title is required");
    assert.notStrictEqual(await field(page, "Customer").getAttribute("aria-invalid"), "true");
    assert.strictEqual(await rows(page).count(), 12);
  });
});

test("Create ticket closes the dialog and shows the new row", async () => {
  await withPage(async (page) => {
    await newTicketButton(page).click();
    await fillNew(page, {Title: "Printer jam", Customer: "Zed Corp", Description: "Jams", Status: "pending", Priority: "high"});
    await create(page);
    assert.strictEqual(await creating(page).isVisible(), false);
    const row = page.getByRole("button", {name: /T013 Printer jam/});
    assert.strictEqual(await row.count(), 1);
    const text = await row.innerText();
    assert.ok(text.includes("pending") && text.includes("high"), text);
    assert.strictEqual((await page.getByRole("status").innerText()).trim(), "13 tickets");
  });
});

test("Cancel and Escape in New ticket create nothing", async () => {
  await withPage(async (page) => {
    await newTicketButton(page).click();
    await fillNew(page, {Title: "Printer jam", Customer: "Zed Corp", Description: "Jams"});
    await creating(page).getByRole("button", {name: "Cancel"}).click();
    assert.strictEqual(await creating(page).isVisible(), false);
    assert.strictEqual(await rows(page).count(), 12);
    await newTicketButton(page).click();
    await fillNew(page, {Title: "Printer jam", Customer: "Zed Corp", Description: "Jams"});
    await page.keyboard.press("Escape");
    assert.strictEqual(await creating(page).isVisible(), false);
    assert.strictEqual(await rows(page).count(), 12);
    await newTicketButton(page).click();
    for (const name of ["Title", "Customer", "Description"]) assert.strictEqual(await field(page, name).inputValue(), "", name);
  });
});

test("a created ticket survives reload and can be searched, opened and edited", async () => {
  await withPage(async (page) => {
    await newTicketButton(page).click();
    await fillNew(page, {Title: "Printer jam", Customer: "Zed Corp", Description: "Jams"});
    await create(page);
    await page.reload();
    await search(page).fill("zed");
    assert.deepStrictEqual(await rowIds(page), ["T013"]);
    await openTicket(page, "T013");
    await statusSelect(page).selectOption("pending");
    await details(page).getByRole("button", {name: "Save changes"}).click();
    await page.reload();
    assert.ok((await rowText(page, "T013")).includes("pending"));
    assert.strictEqual(await rows(page).count(), 13);
  });
});

test("Tab and Shift+Tab stay inside New ticket and focus returns to its button", async () => {
  await withPage(async (page) => {
    await newTicketButton(page).click();
    assert.strictEqual(await insideDialog(page), true);
    for (let i = 0; i < 10; i++) {
      await page.keyboard.press("Tab");
      assert.strictEqual(await insideDialog(page), true, `Tab ${i + 1}`);
    }
    await page.evaluate(() => document.querySelector("dialog[open]").querySelector("select, button, input, textarea").focus());
    for (let i = 0; i < 10; i++) {
      await page.keyboard.press("Shift+Tab");
      assert.strictEqual(await insideDialog(page), true, `Shift+Tab ${i + 1}`);
    }
    await page.keyboard.press("Escape");
    assert.strictEqual(await focusedLabel(page), "New ticket", "after Escape");
    await newTicketButton(page).click();
    await creating(page).getByRole("button", {name: "Cancel"}).click();
    assert.strictEqual(await focusedLabel(page), "New ticket", "after Cancel");
    await newTicketButton(page).click();
    await fillNew(page, {Title: "Printer jam", Customer: "Zed Corp", Description: "Jams"});
    await create(page);
    assert.strictEqual(await focusedLabel(page), "New ticket", "after Create");
  });
});

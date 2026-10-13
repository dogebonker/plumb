const assert = require("node:assert/strict");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

const SEEDS = [
  ["T001", "Password reset link expired", "Acme Labs", "open", "high"],
  ["T002", "Export stalls at ninety percent", "Northwind", "open", "high"],
  ["T003", "Update billing contact", "Bluebird Studio", "pending", "low"],
  ["T004", "Duplicate email notifications", "Cedar Works", "resolved", "medium"],
  ["T005", "Invite a new teammate", "Acme Labs", "pending", "medium"],
  ["T006", "Missing attachment preview", "Northwind", "pending", "high"],
  ["T007", "Keyboard shortcut question", "Maple Partners", "open", "low"],
  ["T008", "Incorrect timezone on activity", "Harbor Design", "resolved", "low"],
  ["T009", "Search omits archived projects", "Cedar Works", "open", "medium"],
  ["T010", "Mobile sidebar overlaps content", "Bluebird Studio", "pending", "medium"],
  ["T011", "Restore a deleted workspace", "Acme Labs", "resolved", "high"],
  ["T012", "Change weekly digest day", "Maple Partners", "open", "low"]
];
const results = [];
let externalRequests = [];
let browser;
let base;
let artifacts;
let expect;
const escaped = value => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const ticket = (page, id = "T001") => {
  const name = new RegExp(`(?=.*\\b${id}\\b)(?=.*${escaped(SEEDS.find(seed => seed[0] === id)[1])})`);
  return page.getByRole("button", {name}).or(page.getByRole("link", {name}));
};
const tickets = page => page.getByRole("button", {name: /T\d{3}/}).or(page.getByRole("link", {name: /T\d{3}/}));
const dialog = (page, name = "Ticket details") => page.getByRole("dialog", {name, exact: true});
const count = async (page, number) => expect(page.getByRole("status")).toHaveText(new RegExp(`(^|\\D)${number}(\\D|$)`), {timeout: 2500});
async function fieldValue(form, label, value) {
  const field = form.getByLabel(label, {exact: true});
  if (await field.count()) assert.equal(await field.evaluate(node => typeof node.value === "string" ? node.value : node.textContent.trim()), value);
  else await expect(form.getByText(value, {exact: false}).first()).toBeVisible({timeout: 2500});
}
async function open(page, id = "T001") { await ticket(page, id).click(); await dialog(page).waitFor(); return dialog(page); }
async function newDialog(page) { await page.getByRole("button", {name: "New ticket", exact: true}).click(); await dialog(page, "New ticket").waitFor(); return dialog(page, "New ticket"); }
async function create(page, values = {}) {
  const form = await newDialog(page);
  await form.getByLabel("Title", {exact: true}).fill(values.title || "  Delivery note <new>  ");
  await form.getByLabel("Customer", {exact: true}).fill(values.customer || "  Orchard Team  ");
  await form.getByLabel("Description", {exact: true}).fill(values.description || "  Please update the delivery instructions.  ");
  await form.getByLabel("Status", {exact: true}).selectOption("pending");
  await form.getByLabel("Priority", {exact: true}).selectOption("high");
  await form.getByRole("button", {name: "Create ticket", exact: true}).click();
  await form.waitFor({state: "hidden"});
}
async function stored(page) {
  return page.evaluate(() => Object.fromEntries(Object.keys(localStorage).map(key => [key, localStorage.getItem(key)])));
}
async function failWrites(page, failing = true) {
  await page.evaluate(failing => {
    if (failing) {
      window.__benchmarkSetItem = Storage.prototype.setItem;
      Storage.prototype.setItem = function() { throw new DOMException("Storage quota exceeded", "QuotaExceededError"); };
    } else Storage.prototype.setItem = window.__benchmarkSetItem;
  }, failing);
}
async function visibleError(page) {
  const errors = page.getByRole("alert").or(page.getByRole("status")).filter({hasText: /sav|stor|recover|corrupt|invalid|unread|fail|could|cannot|unable|conflict|another|changed/i});
  await expect(errors.first()).toBeVisible({timeout: 2500});
  assert.ok((await errors.first().innerText()).trim(), "failure needs a visible accessible explanation");
}
async function fillNew(page, title) {
  const form = await newDialog(page);
  await form.getByLabel("Title", {exact: true}).fill(title);
  await form.getByLabel("Customer", {exact: true}).fill("Failure sequence customer");
  await form.getByLabel("Description", {exact: true}).fill("Retain this draft until saving succeeds.");
  return form;
}
async function check(name, run, mobile = false) {
  const context = await browser.newContext({viewport: mobile ? {width: 360, height: 800} : {width: 1440, height: 1000},
    deviceScaleFactor: 1, serviceWorkers: "block", reducedMotion: "reduce", isMobile: mobile, hasTouch: mobile});
  await context.route("**/*", route => {
    if (!route.request().url().startsWith(base + "/")) { externalRequests.push(route.request().url()); return route.abort(); }
    return route.continue();
  });
  await context.routeWebSocket(/.*/, socket => { externalRequests.push(socket.url()); socket.close(); });
  const page = await context.newPage();
  page.setDefaultTimeout(1800);
  try {
    await page.goto(base);
    await run(page);
    results.push({name, passed: true});
  } catch (error) {
    results.push({name, passed: false, error: error.message});
  } finally { await context.close(); }
}
async function main() {
  if (!process.env.PLAYWRIGHT_MODULE) throw new Error("PLAYWRIGHT_MODULE is required; browser checks cannot be skipped.");
  const {chromium} = require(process.env.PLAYWRIGHT_MODULE);
  expect = require(path.join(process.env.PLAYWRIGHT_MODULE, "test")).expect;
  artifacts = path.resolve(process.env.BROWSER_ARTIFACTS || "browser-artifacts");
  fs.mkdirSync(artifacts, {recursive: true});
  const root = process.cwd();
  const server = http.createServer((request, response) => {
    const pathname = new URL(request.url, "http://localhost").pathname;
    const file = path.resolve(root, "." + decodeURIComponent(pathname === "/" ? "/index.html" : pathname));
    if (!file.startsWith(root + path.sep)) { response.writeHead(403).end(); return; }
    fs.readFile(file, (error, data) => {
      if (error) { response.writeHead(404).end(); return; }
      response.setHeader("Content-Type", {".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml"}[path.extname(file)] || "application/octet-stream");
      response.end(data);
    });
  });
  await new Promise((resolve, reject) => { server.once("error", reject); server.listen(0, "127.0.0.1", resolve); });
  base = `http://127.0.0.1:${server.address().port}`;
  try {
    browser = await chromium.launch({headless: true});
    // A visible ticket title may share its heading with an ID.
    const contractContext = await browser.newContext();
    try {
      const page = await contractContext.newPage();
      await page.setContent('<dialog open aria-label="Ticket details"><h2>T001 Password reset link expired</h2></dialog>');
      await fieldValue(page.getByRole("dialog", {name: "Ticket details"}), "Title", "Password reset link expired");
    } finally { await contractContext.close(); }
    await check("twelve_seeded_tickets_and_visible_metadata", async page => {
      await expect(tickets(page)).toHaveCount(12, {timeout: 2500});
      for (const [id, title, customer, status, priority] of SEEDS) {
        const item = ticket(page, id);
        const visible = await item.evaluate((node, data) => {
          for (let container = node; container; container = container.parentElement) {
            const text = container.innerText.toLowerCase();
            if (data.otherIds.some(other => new RegExp(`\\b${other}\\b`).test(text.toUpperCase()))) return false;
            if (data.values.every(value => text.includes(value.toLowerCase()))) return true;
          }
          return false;
        }, {values: [id, title, customer, status, priority], otherIds: SEEDS.map(seed => seed[0]).filter(other => other !== id)});
        assert.ok(visible, `${id} must show its own customer, status, and priority`);
      }
      await count(page, 12);
    });
    await check("case_insensitive_title_and_customer_search", async page => {
      const search = page.getByLabel("Search tickets", {exact: true});
      await search.fill("aCmE");
      await expect(tickets(page)).toHaveCount(3, {timeout: 2500});
      for (const id of ["T001", "T005", "T011"]) await ticket(page, id).waitFor();
      await search.fill("EXPIRED");
      await expect(tickets(page)).toHaveCount(1, {timeout: 2500});
      await ticket(page).waitFor();
    });
    await check("search_status_and_priority_combine", async page => {
      await page.getByLabel("Search tickets", {exact: true}).fill("northwind");
      await page.getByLabel("Status filter", {exact: true}).selectOption("open");
      await page.getByLabel("Priority filter", {exact: true}).selectOption("high");
      await expect(tickets(page)).toHaveCount(1, {timeout: 2500});
      await ticket(page, "T002").waitFor();
      await count(page, 1);
      await page.getByLabel("Priority filter", {exact: true}).selectOption("low");
      await expect(tickets(page)).toHaveCount(0, {timeout: 2500});
    });
    await check("result_count_and_reset", async page => {
      await page.getByLabel("Search tickets", {exact: true}).fill("maple");
      await page.getByLabel("Priority filter", {exact: true}).selectOption("low");
      await count(page, 2);
      await page.getByRole("button", {name: "Reset filters", exact: true}).click();
      assert.equal(await page.getByLabel("Search tickets", {exact: true}).inputValue(), "");
      await expect(tickets(page)).toHaveCount(12, {timeout: 2500});
      await count(page, 12);
      await page.getByLabel("Status filter", {exact: true}).selectOption("resolved");
      await expect(tickets(page)).toHaveCount(3, {timeout: 2500});
    });
    await check("clear_empty_state", async page => {
      await page.getByLabel("Search tickets", {exact: true}).fill("no-such-customer-1234");
      await expect(tickets(page)).toHaveCount(0, {timeout: 2500});
      await count(page, 0);
      assert.match(await page.locator("body").innerText(), /no .*tickets|no .*results|no matches|nothing.*match/i);
    });
    await check("detail_fields_match_ticket", async page => {
      const form = await open(page);
      for (const [label, value] of [["Title", SEEDS[0][1]], ["Customer", "Acme Labs"], ["Description", "The reset link expires before the customer can use it."], ["Status", "open"], ["Priority", "high"]]) {
        await fieldValue(form, label, value);
      }
    });
    await check("cancel_does_not_save_changes", async page => {
      let form = await open(page);
      await form.getByLabel("Status", {exact: true}).selectOption("resolved");
      await form.getByLabel("Priority", {exact: true}).selectOption("low");
      await form.getByRole("button", {name: "Cancel", exact: true}).click();
      await page.reload();
      form = await open(page);
      assert.equal(await form.getByLabel("Status", {exact: true}).inputValue(), "open");
      assert.equal(await form.getByLabel("Priority", {exact: true}).inputValue(), "high");
    });
    await check("saved_edits_persist_and_filter_correctly", async page => {
      let form = await open(page);
      await form.getByLabel("Status", {exact: true}).selectOption("resolved");
      await form.getByLabel("Priority", {exact: true}).selectOption("low");
      await form.getByRole("button", {name: "Save changes", exact: true}).click();
      await form.waitFor({state: "hidden"});
      await page.reload();
      await page.getByLabel("Status filter", {exact: true}).selectOption("resolved");
      await page.getByLabel("Priority filter", {exact: true}).selectOption("low");
      await ticket(page).waitFor();
      form = await open(page);
      assert.equal(await form.getByLabel("Status", {exact: true}).inputValue(), "resolved");
      assert.equal(await form.getByLabel("Priority", {exact: true}).inputValue(), "low");
    });
    await check("required_trimmed_fields_have_accessible_errors", async page => {
      const form = await newDialog(page);
      for (const label of ["Title", "Customer", "Description"]) await form.getByLabel(label, {exact: true}).fill("   ");
      await form.getByRole("button", {name: "Create ticket", exact: true}).click();
      assert.ok(await form.isVisible());
      for (const label of ["Title", "Customer", "Description"]) {
        const field = form.getByLabel(label, {exact: true});
        assert.ok(await field.getAttribute("aria-invalid") === "true" || await field.evaluate(node => !node.checkValidity()));
        const described = await field.getAttribute("aria-describedby") || await field.getAttribute("aria-errormessage");
        const message = described ? await field.evaluate((node, ids) => ids.split(/\s+/).map(id => document.getElementById(id)?.textContent || "").join(" "), described)
          : await field.evaluate(node => node.validationMessage);
        assert.match(message, /required|enter|provide|cannot|empty|blank/i);
      }
      await form.getByRole("button", {name: "Cancel", exact: true}).click();
      await expect(tickets(page)).toHaveCount(12, {timeout: 2500});
    });
    await check("new_ticket_trimmed_unique_and_persistent", async page => {
      await create(page);
      await count(page, 13);
      await page.reload();
      await page.getByLabel("Search tickets", {exact: true}).fill("ORCHARD");
      await count(page, 1);
      const created = page.getByRole("button", {name: /Delivery note <new>/}).or(page.getByRole("link", {name: /Delivery note <new>/}));
      await created.click();
      const form = dialog(page);
      for (const [label, value] of [["Title", "Delivery note <new>"], ["Customer", "Orchard Team"], ["Description", "Please update the delivery instructions."], ["Status", "pending"], ["Priority", "high"]]) await fieldValue(form, label, value);
      await form.getByRole("button", {name: "Cancel", exact: true}).click();
      await page.getByRole("button", {name: "Reset filters", exact: true}).click();
      await count(page, 13);
      for (const [id] of SEEDS) await ticket(page, id).waitFor();
      const name = await created.evaluate(node => node.getAttribute("aria-label") || (node.getAttribute("aria-labelledby") || "").split(/\s+/).map(id => document.getElementById(id)?.textContent || "").join(" ").trim() || node.innerText);
      assert.ok(name.includes("Delivery note <new>"));
      assert.ok(name.replace("Delivery note <new>", "").trim(), "created ticket name must also include its ID");
      for (const [id] of SEEDS) assert.ok(!new RegExp(`\\b${id}\\b`).test(name), "created ID must not reuse a seeded ID");
    });
    await check("escape_detail_restores_focus_without_saving", async page => {
      const opener = ticket(page);
      const form = await open(page);
      await form.getByLabel("Status", {exact: true}).selectOption("resolved");
      await page.keyboard.press("Escape");
      await form.waitFor({state: "hidden"});
      assert.ok(await opener.evaluate(node => document.activeElement === node));
      await open(page);
      assert.equal(await dialog(page).getByLabel("Status", {exact: true}).inputValue(), "open");
    });
    await check("escape_new_restores_focus_without_creating", async page => {
      const opener = page.getByRole("button", {name: "New ticket", exact: true});
      const form = await newDialog(page);
      await form.getByLabel("Title", {exact: true}).fill("Unsaved draft");
      await page.keyboard.press("Escape");
      await form.waitFor({state: "hidden"});
      assert.ok(await opener.evaluate(node => document.activeElement === node));
      await expect(tickets(page)).toHaveCount(12, {timeout: 2500});
    });
    await check("keyboard_open_submit_and_visible_focus", async page => {
      await ticket(page).focus();
      await page.keyboard.press("Enter");
      const form = dialog(page);
      await form.waitFor();
      assert.ok(await form.evaluate(node => node.contains(document.activeElement)), "initial modal focus must be inside");
      for (const key of ["Tab", "Shift+Tab"]) for (let step = 0; step < 10; step++) {
        await page.keyboard.press(key);
        assert.ok(await form.evaluate(node => node.contains(document.activeElement)), "modal keyboard focus must stay inside");
      }
      const status = form.getByLabel("Status", {exact: true});
      await status.focus();
      await status.selectOption("pending");
      const save = form.getByRole("button", {name: "Save changes", exact: true});
      const beforeFocus = await save.evaluate(node => {
        const style = getComputedStyle(node);
        return Object.fromEntries(["color", "backgroundColor", "borderColor", "borderStyle", "borderWidth", "outlineStyle", "outlineWidth", "outlineColor", "boxShadow"].map(key => [key, style[key]]));
      });
      await save.focus();
      const visibleFocus = await save.evaluate((node, before) => {
        const style = getComputedStyle(node);
        return Object.entries(before).some(([key, value]) => style[key] !== value);
      }, beforeFocus);
      assert.ok(visibleFocus, "keyboard focus must be visible");
      await page.keyboard.press("Enter");
      await form.waitFor({state: "hidden"});
      await page.reload();
      assert.equal(await (await open(page)).getByLabel("Status", {exact: true}).inputValue(), "pending");
    });
    await check("mobile_page_and_dialog_do_not_overflow", async page => {
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
      const form = await newDialog(page);
      const box = await form.boundingBox();
      assert.ok(box.x >= 0 && box.x + box.width <= 361, "dialog must fit 360px viewport");
      for (const label of ["Title", "Customer", "Description", "Status", "Priority"]) {
        await form.getByLabel(label, {exact: true}).scrollIntoViewIfNeeded();
        const control = await form.getByLabel(label, {exact: true}).boundingBox();
        assert.ok(control.x >= 0 && control.x + control.width <= 361 && control.y >= 0 && control.y + control.height <= 801, `${label} must fit after scrolling`);
      }
      for (const name of ["Create ticket", "Cancel"]) {
        const button = form.getByRole("button", {name, exact: true});
        await button.scrollIntoViewIfNeeded();
        const control = await button.boundingBox();
        assert.ok(control.x >= 0 && control.x + control.width <= 361 && control.y >= 0 && control.y + control.height <= 801, `${name} must be reachable`);
      }
      await form.getByRole("button", {name: "Cancel", exact: true}).click();
      const detail = await open(page);
      for (const control of [detail.getByLabel("Status", {exact: true}), detail.getByLabel("Priority", {exact: true}), detail.getByRole("button", {name: "Save changes", exact: true}), detail.getByRole("button", {name: "Cancel", exact: true})]) {
        await control.scrollIntoViewIfNeeded();
        const rectangle = await control.boundingBox();
        assert.ok(rectangle.x >= 0 && rectangle.x + rectangle.width <= 361 && rectangle.y >= 0 && rectangle.y + rectangle.height <= 801, "detail actions must be reachable");
      }
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    }, true);
    await check("failed_create_retains_draft_and_retry_saves_once", async page => {
      const before = await stored(page);
      const form = await fillNew(page, "Quota failure draft");
      await failWrites(page);
      await form.getByRole("button", {name: "Create ticket", exact: true}).click();
      await expect(form).toBeVisible();
      await visibleError(page);
      await expect(form.getByLabel("Title", {exact: true})).toHaveValue("Quota failure draft");
      await expect(form.getByLabel("Description", {exact: true})).toHaveValue("Retain this draft until saving succeeds.");
      assert.deepEqual(await stored(page), before, "failed create must not change stored data");
      await failWrites(page, false);
      await form.getByRole("button", {name: "Create ticket", exact: true}).click();
      await form.waitFor({state: "hidden"});
      await page.reload();
      await count(page, 13);
      await expect(page.getByRole("button", {name: /Quota failure draft/}).or(page.getByRole("link", {name: /Quota failure draft/}))).toHaveCount(1);
    });
    await check("failed_edit_retains_draft_and_previous_saved_value", async page => {
      let form = await open(page);
      await form.getByLabel("Status", {exact: true}).selectOption("pending");
      await form.getByRole("button", {name: "Save changes", exact: true}).click();
      await form.waitFor({state: "hidden"});
      const before = await stored(page);
      form = await open(page);
      await form.getByLabel("Status", {exact: true}).selectOption("resolved");
      await failWrites(page);
      await form.getByRole("button", {name: "Save changes", exact: true}).click();
      await expect(form).toBeVisible();
      await visibleError(page);
      await expect(form.getByLabel("Status", {exact: true})).toHaveValue("resolved");
      assert.deepEqual(await stored(page), before, "failed edit must preserve acknowledged data");
      await failWrites(page, false);
      await form.getByRole("button", {name: "Cancel", exact: true}).click();
      await page.reload();
      form = await open(page);
      await expect(form.getByLabel("Status", {exact: true})).toHaveValue("pending");
      await form.getByLabel("Status", {exact: true}).selectOption("resolved");
      await failWrites(page);
      await form.getByRole("button", {name: "Save changes", exact: true}).click();
      await expect(form).toBeVisible();
      await failWrites(page, false);
      await form.getByRole("button", {name: "Save changes", exact: true}).click();
      await form.waitFor({state: "hidden"});
      await page.reload();
      await expect((await open(page)).getByLabel("Status", {exact: true})).toHaveValue("resolved");
    });
    await check("invalid_existing_saved_data_is_preserved", async page => {
      const marker = "Discover saved ticket storage";
      await create(page, {title: marker});
      const persisted = await stored(page);
      const keys = Object.entries(persisted).filter(([, value]) => value.includes(marker)).map(([key]) => key);
      assert.ok(keys.length, "created ticket must have persisted data");
      for (const corrupt of ["{invalid saved JSON", JSON.stringify({unexpected: "invalid ticket data"}),
        JSON.stringify([{id: "T001", title: "Incomplete saved record"}])]) {
        await page.evaluate(({keys, corrupt}) => { for (const key of keys) localStorage.setItem(key, corrupt); }, {keys, corrupt});
        await page.reload();
        await visibleError(page);
        const action = page.getByRole("button", {name: "New ticket", exact: true});
        if (await action.isEnabled()) {
          const form = await fillNew(page, "Do not overwrite recovery data");
          await form.getByRole("button", {name: "Create ticket", exact: true}).click();
          await expect(form).toBeVisible();
          await visibleError(page);
          await form.getByRole("button", {name: "Cancel", exact: true}).click();
        }
        const after = await stored(page);
        for (const key of keys) assert.equal(after[key], corrupt, "invalid original bytes must survive attempted write");
      }
      await page.evaluate(persisted => { for (const [key, value] of Object.entries(persisted)) localStorage.setItem(key, value); }, persisted);
      const unreadable = await page.context().newPage();
      await unreadable.addInitScript(keys => {
        const getItem = Storage.prototype.getItem;
        Storage.prototype.getItem = function(key) {
          if (keys.includes(key)) throw new DOMException("Saved data unavailable", "SecurityError");
          return getItem.call(this, key);
        };
      }, keys);
      await unreadable.goto(base);
      await visibleError(unreadable);
      if (await unreadable.getByRole("button", {name: "New ticket", exact: true}).isEnabled()) {
        const form = await fillNew(unreadable, "Do not replace unreadable data");
        await form.getByRole("button", {name: "Create ticket", exact: true}).click();
        await expect(form).toBeVisible();
        await visibleError(unreadable);
      }
      assert.deepEqual(await stored(page), persisted, "unreadable original data must survive attempted write");
      await unreadable.close();
      await page.reload();
      await count(page, 13);
      await expect(page.getByRole("button", {name: new RegExp(marker)}).or(page.getByRole("link", {name: new RegExp(marker)}))).toBeVisible();
    });
    await check("two_tabs_preserve_creates_and_unrelated_updates", async page => {
      const second = await page.context().newPage();
      await second.goto(base);
      await create(page, {title: "First tab unique ticket"});
      await create(second, {title: "Second tab unique ticket"});
      const firstEdit = await open(page);
      await firstEdit.getByLabel("Status", {exact: true}).selectOption("resolved");
      await firstEdit.getByRole("button", {name: "Save changes", exact: true}).click();
      await firstEdit.waitFor({state: "hidden"});
      const secondEdit = await open(second, "T002");
      await secondEdit.getByLabel("Priority", {exact: true}).selectOption("low");
      await secondEdit.getByRole("button", {name: "Save changes", exact: true}).click();
      await secondEdit.waitFor({state: "hidden"});
      await page.reload();
      await count(page, 14);
      const names = [];
      for (const title of ["First tab unique ticket", "Second tab unique ticket"]) {
        const item = page.getByRole("button", {name: new RegExp(title)}).or(page.getByRole("link", {name: new RegExp(title)}));
        await expect(item).toHaveCount(1);
        await item.click();
        names.push(await item.getAttribute("aria-label") || await item.innerText());
        await dialog(page).getByRole("button", {name: "Cancel", exact: true}).click();
      }
      assert.notEqual(names[0].replace("First tab unique ticket", ""), names[1].replace("Second tab unique ticket", ""), "new IDs must be distinct");
      await expect((await open(page)).getByLabel("Status", {exact: true})).toHaveValue("resolved");
      await dialog(page).getByRole("button", {name: "Cancel", exact: true}).click();
      await expect((await open(page, "T002")).getByLabel("Priority", {exact: true})).toHaveValue("low");
    });
    await check("stale_editor_preserves_other_fields_or_reports_conflict", async page => {
      const second = await page.context().newPage();
      await second.goto(base);
      const stale = await open(page);
      const originalStatus = await stale.getByLabel("Status", {exact: true}).inputValue();
      await stale.getByLabel("Status", {exact: true}).selectOption("resolved");
      const fresh = await open(second);
      await fresh.getByLabel("Priority", {exact: true}).selectOption("low");
      await fresh.getByRole("button", {name: "Save changes", exact: true}).click();
      await fresh.waitFor({state: "hidden"});
      await stale.getByRole("button", {name: "Save changes", exact: true}).click();
      const conflicted = await stale.isVisible();
      if (conflicted) {
        await visibleError(page);
        await expect(stale.getByLabel("Status", {exact: true})).toHaveValue("resolved");
        await stale.getByRole("button", {name: "Cancel", exact: true}).click();
      }
      await page.reload();
      const result = await open(page);
      await expect(result.getByLabel("Priority", {exact: true})).toHaveValue("low");
      await expect(result.getByLabel("Status", {exact: true})).toHaveValue(conflicted ? originalStatus : "resolved");
      await result.getByRole("button", {name: "Cancel", exact: true}).click();
      // A same-field conflict must preserve the newer acknowledgement and the old draft.
      await second.reload();
      const older = await open(page);
      await older.getByLabel("Priority", {exact: true}).selectOption("medium");
      const newer = await open(second);
      await newer.getByLabel("Priority", {exact: true}).selectOption("high");
      await newer.getByRole("button", {name: "Save changes", exact: true}).click();
      await newer.waitFor({state: "hidden"});
      await older.getByRole("button", {name: "Save changes", exact: true}).click();
      await expect(older).toBeVisible();
      await visibleError(page);
      await expect(older.getByLabel("Priority", {exact: true})).toHaveValue("medium");
      await older.getByRole("button", {name: "Cancel", exact: true}).click();
      await page.reload();
      await expect((await open(page)).getByLabel("Priority", {exact: true})).toHaveValue("high");
    });
    await check("breakpoint_ticket_titles_remain_readable", async page => {
      for (const width of [600, 601]) {
        await page.setViewportSize({width, height: 1000});
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
        const readable = await ticket(page).evaluate((node, title) => {
          const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
          let text;
          while ((text = walker.nextNode())) {
            const start = text.textContent.indexOf(title);
            if (start < 0) continue;
            const range = document.createRange();
            range.setStart(text, start); range.setEnd(text, start + title.length);
            const boxes = [...range.getClientRects()].filter(box => box.width && box.height);
            return boxes.length > 0 && boxes.length <= 4 && boxes.every(box => box.x >= 0 && box.right <= innerWidth + 1)
              && Math.max(...boxes.map(box => box.width)) >= 80;
          }
          return false;
        }, SEEDS[0][1]);
        assert.ok(readable, `ticket title must remain readable at ${width}px`);
      }
    });
    await check("desktop_mobile_screenshots_and_local_assets_only", async page => {
      await page.screenshot({path: path.join(artifacts, "desktop.png"), fullPage: true, animations: "disabled", scale: "css"});
      const context = await browser.newContext({viewport: {width: 360, height: 800}, deviceScaleFactor: 1, isMobile: true, hasTouch: true, reducedMotion: "reduce", serviceWorkers: "block"});
      try {
        await context.route("**/*", route => {
          if (!route.request().url().startsWith(base + "/")) { externalRequests.push(route.request().url()); return route.abort(); }
          return route.continue();
        });
        await context.routeWebSocket(/.*/, socket => { externalRequests.push(socket.url()); socket.close(); });
        const mobile = await context.newPage();
        await mobile.goto(base);
        await mobile.screenshot({path: path.join(artifacts, "mobile.png"), fullPage: true, animations: "disabled", scale: "css"});
      } finally { await context.close(); }
      assert.equal(externalRequests.length, 0, "remote assets or requests are not allowed");
    });
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
  const grade = {tests: results.length, failures: results.filter(result => !result.passed).length, errors: 0, skipped: 0, checks: results,
    screenshots: {desktop: path.join(artifacts, "desktop.png"), mobile: path.join(artifacts, "mobile.png")}};
  fs.writeFileSync(path.join(artifacts, "browser-grade.json"), JSON.stringify(grade, null, 2));
  console.log("BENCHMARK_GRADE=" + JSON.stringify(grade));
  process.exitCode = grade.failures || grade.tests !== 21 ? 1 : 0;
}
main().catch(error => { console.error(error); console.log("BENCHMARK_GRADE=" + JSON.stringify({tests: results.length, failures: results.filter(result => !result.passed).length, errors: 1, skipped: 0, checks: results})); process.exitCode = 1; });

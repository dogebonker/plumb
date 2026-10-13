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

// Runs body(page) in a fresh browser context at the given viewport.
async function withPage(viewport, body) {
  const server = await startServer();
  let browser;
  try {
    browser = await chromium.launch({headless: true});
    const page = await (await browser.newContext({viewport})).newPage();
    await page.goto(`http://127.0.0.1:${server.address().port}`);
    await page.getByRole("button", {name: /T001/}).waitFor();
    await body(page);
  } finally {
    if (browser) await browser.close();
    server.close();
  }
}

// Review finding 1 (WCAG 3.3.1, 4.1.3): a failed submit moves focus to the first invalid field.
test("a failed Create ticket puts focus on the first invalid field", async () => {
  await withPage({width: 1280, height: 800}, async (page) => {
    await page.getByRole("button", {name: "New ticket"}).click();
    await page.getByRole("textbox", {name: "Customer"}).fill("Acme");
    await page.getByRole("textbox", {name: "Description"}).fill("Printer is jammed");
    await page.getByRole("button", {name: "Create ticket"}).click();
    assert.strictEqual(await page.getByRole("textbox", {name: "Title"}).getAttribute("aria-invalid"), "true");
    assert.strictEqual(await page.evaluate(() => document.activeElement.id), "create-title");
  });
});

// Review finding 2: the Search, Status and Priority filter labels sit on one line at desktop width.
test("the three filter labels share one top edge at 1280", async () => {
  await withPage({width: 1280, height: 800}, async (page) => {
    const tops = await page.evaluate(() => [...document.querySelectorAll(".filters label")].map((label) => label.querySelector("input, select").getBoundingClientRect().top));
    assert.strictEqual(new Set(tops).size, 1, `control tops differ: ${tops.join(", ")}`);
  });
});

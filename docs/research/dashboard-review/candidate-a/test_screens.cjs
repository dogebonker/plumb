const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

if (!process.env.PLAYWRIGHT_MODULE) throw new Error("PLAYWRIGHT_MODULE is required; no runtime will be installed or skipped.");
const {chromium} = require(process.env.PLAYWRIGHT_MODULE);

const shots = path.resolve(process.cwd(), ".tmp", "shots");

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

// Writes PNGs for the three screens at one viewport size; assertions only check that each file was written.
async function capture(viewport, prefix) {
  fs.mkdirSync(shots, {recursive: true});
  const server = await startServer();
  let browser;
  try {
    browser = await chromium.launch({headless: true});
    const page = await (await browser.newContext({viewport})).newPage();
    await page.goto(`http://127.0.0.1:${server.address().port}`);
    await page.getByRole("button", {name: /T001/}).waitFor();
    await page.screenshot({path: path.join(shots, `${prefix}-list.png`)});

    await page.getByRole("button", {name: /T002/}).click();
    await page.getByRole("dialog", {name: "Ticket details"}).waitFor();
    await page.screenshot({path: path.join(shots, `${prefix}-details.png`)});
    await page.getByRole("button", {name: "Cancel"}).click();

    await page.getByRole("button", {name: "New ticket", exact: true}).click();
    await page.getByRole("dialog", {name: "New ticket"}).waitFor();
    await page.getByRole("button", {name: "Create ticket"}).click();
    await page.getByText("Title is required").waitFor();
    await page.screenshot({path: path.join(shots, `${prefix}-create-errors.png`)});
  } finally {
    if (browser) await browser.close();
    await new Promise((resolve) => server.close(resolve));
  }
  for (const name of ["list", "details", "create-errors"]) {
    assert.ok(fs.statSync(path.join(shots, `${prefix}-${name}.png`)).size > 0, `${prefix}-${name}.png written`);
  }
}

test("screenshots: desktop 1280x800 list, details, create with errors", () => capture({width: 1280, height: 800}, "desktop"));
test("screenshots: mobile 360x740 list, details, create with errors", () => capture({width: 360, height: 740}, "mobile"));

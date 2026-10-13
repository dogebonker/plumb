const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

async function main() {
  if (!process.env.PLAYWRIGHT_MODULE) throw new Error("PLAYWRIGHT_MODULE is required; no runtime will be installed or skipped.");
  const {chromium} = require(process.env.PLAYWRIGHT_MODULE);
  const {expect} = require(path.join(process.env.PLAYWRIGHT_MODULE, "test"));
  const root = process.cwd();
  const server = http.createServer((request, response) => {
    const file = path.resolve(root, "." + decodeURIComponent(new URL(request.url, "http://localhost").pathname === "/" ? "/index.html" : new URL(request.url, "http://localhost").pathname));
    if (!file.startsWith(root + path.sep)) { response.writeHead(403).end(); return; }
    fs.readFile(file, (error, data) => {
      if (error) { response.writeHead(404).end(); return; }
      response.setHeader("Content-Type", {".html": "text/html", ".js": "text/javascript", ".css": "text/css"}[path.extname(file)] || "application/octet-stream");
      response.end(data);
    });
  });
  await new Promise((resolve, reject) => { server.once("error", reject); server.listen(0, "127.0.0.1", resolve); });
  let browser;
  try {
    browser = await chromium.launch({headless: true});
    const page = await browser.newPage();
    await page.goto(`http://127.0.0.1:${server.address().port}`);
    const openings = page.getByRole("button", {name: /T\d{3}/}).or(page.getByRole("link", {name: /T\d{3}/}));
    await expect(openings).toHaveCount(12);
    const first = /(?=.*\bT001\b)(?=.*Password reset link expired)/;
    await page.getByRole("button", {name: first}).or(page.getByRole("link", {name: first})).waitFor();
    await page.getByLabel("Search tickets", {exact: true}).waitFor();
    console.log("BENCHMARK_GRADE=" + JSON.stringify({tests: 2, failures: 0, errors: 0, skipped: 0}));
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
}
main().catch(error => { console.error(error); console.log("BENCHMARK_GRADE=" + JSON.stringify({tests: 0, failures: 0, errors: 1, skipped: 0})); process.exitCode = 1; });

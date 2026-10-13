const assert = require('node:assert/strict');
const { test } = require('node:test');
const { viewportWidths, readabilityMetrics } = require('./render-checks.cjs');

test('samples both sides of px, rem, em and range media boundaries', () => {
  assert.deepEqual(viewportWidths('@media(max-width:600px){} @media (width >= 48rem){} @media(40em < width){}',
    { minimum: 360, baseline: [390], rootFontSize: 16 }), [360, 390, 599, 600, 601, 639, 640, 641, 767, 768, 769]);
});
test('samples equality and reversed literal range queries', () => {
  assert.deepEqual(viewportWidths('@media(width = 600px){} @media(900px > width){} @media(60rem >= width){}',
    { minimum: 360, baseline: [] }), [360, 599, 600, 601, 899, 900, 901, 959, 960, 961]);
});
test('ignores declarations and commented media, retains brief minimum and baseline', () => {
  assert.deepEqual(viewportWidths('/* @media(max-width:200px){} */ .x { width: 800px }'), [320, 390, 768, 1280]);
});
test('rejects unsupported planner inputs rather than silently omitting widths', () => {
  assert.throws(() => viewportWidths('', { minimum: 0 }), /positive/);
});

// Installed Playwright only; this check is explicit rather than silently skipped.
test('actual Chromium detects a 601px collapse and permits readable wrapping', async () => {
  const playwright = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
  const browser = await playwright.chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 601, height: 900 } });
    await page.setContent('<style>.title{width:400px;font:16px Arial;overflow-wrap:anywhere}' +
      '@media(600px < width < 768px){.title{width:15px}}</style>' +
      '<p class="title">Password reset email does not arrive for the customer</p>');
    const collapsed = await page.evaluate(readabilityMetrics);
    assert.ok(collapsed.narrowText.some(item => /Password reset/.test(item.text)), JSON.stringify(collapsed));
    for (const width of [600, 1280]) {
      await page.setViewportSize({ width, height: 900 });
      assert.deepEqual((await page.evaluate(readabilityMetrics)).narrowText, []);
    }
    await page.setContent('<style>p{width:160px;font:16px Arial} .icon{width:16px} .vertical{writing-mode:vertical-rl;width:16px}</style>' +
      '<p>A readable long ticket title wraps naturally across several lines.</p><span class="icon">+</span>' +
      '<p class="vertical">A deliberately vertical heading</p>');
    assert.deepEqual((await page.evaluate(readabilityMetrics)).narrowText, []);
    await page.setContent('<p style="width:100px;white-space:nowrap;overflow:hidden">A long title is silently clipped here</p>');
    assert.equal((await page.evaluate(readabilityMetrics)).clippedText.length, 1);
  } finally { await browser.close(); }
});

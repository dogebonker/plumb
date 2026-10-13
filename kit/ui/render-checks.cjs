// Shared capture inputs and rendered facts; the reviewer decides severity.
function viewportWidths(css, { minimum = 320, baseline = [390, 768, 1280], rootFontSize = 16 } = {}) {
  if (![minimum, rootFontSize, ...baseline].every(value => Number.isFinite(value) && value > 0)) {
    throw new Error('Viewport widths and rootFontSize must be positive finite numbers');
  }
  const widths = new Set([Math.ceil(minimum), ...baseline.map(Math.ceil)]);
  const source = css.replace(/\/\*[\s\S]*?\*\//g, '');
  // shortcut: literal px/em/rem media boundaries only; add computed CSSOM widths for calc/var or container-query layouts.
  for (const media of source.matchAll(/@media\s*([^{}]+)\{/gi)) {
    for (const feature of media[1].matchAll(/(?:\b(?:min-|max-)?width\s*[:<>=]=?\s*(\d*\.?\d+)\s*(px|rem|em)\b)|(?:(\d*\.?\d+)\s*(px|rem|em)\s*[<>=]=?\s*width\b)/gi)) {
      const value = Number(feature[1] || feature[3]);
      const unit = (feature[2] || feature[4]).toLowerCase();
      const boundary = value * (unit === 'px' ? 1 : rootFontSize);
      for (const width of [Math.floor(boundary) - 1, Math.ceil(boundary), Math.ceil(boundary) + 1]) {
        if (width >= minimum) widths.add(width);
      }
    }
  }
  return [...widths].sort((a, b) => a - b);
}

function readabilityMetrics() {
  const narrowText = [], clippedText = [];
  for (const element of document.body.querySelectorAll('*')) {
    const style = getComputedStyle(element), rect = element.getBoundingClientRect();
    if (!rect.width || !rect.height || style.visibility === 'hidden' || style.display === 'none' || +style.opacity === 0) continue;
    const text = [...element.childNodes].filter(node => node.nodeType === 3).map(node => node.textContent).join(' ').trim();
    if (text.length < 12 || style.writingMode !== 'horizontal-tb') continue;
    const width = element.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
    const evidence = { tag: element.tagName, text: text.slice(0, 160), width: Math.round(width), height: Math.round(rect.height) };
    // Three em is a candidate threshold for long prose, never a ban on intentional narrow controls.
    if (width > 0 && width < 3 * parseFloat(style.fontSize)) narrowText.push(evidence);
    if ((['hidden', 'clip'].includes(style.overflowX) && element.scrollWidth > element.clientWidth + 1) ||
        (['hidden', 'clip'].includes(style.overflowY) && element.scrollHeight > element.clientHeight + 1)) clippedText.push(evidence);
  }
  return { viewportWidth: innerWidth, horizontalOverflow: document.documentElement.scrollWidth > innerWidth + 1,
    narrowText, clippedText };
}
module.exports = { viewportWidths, readabilityMetrics };

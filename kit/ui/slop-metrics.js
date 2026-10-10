// Rendered-DOM slop metrics. Paste into page.evaluate() or a devtools console.
// Returns numbers, not verdicts: thresholds live in the skill.
(() => {
  const vis = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  const all = [...document.body.querySelectorAll('*')].filter(vis);
  // Any CSS color (rgb, oklch, lab, color()) to [r, g, b, a] through a 1x1 canvas.
  const ctx = Object.assign(document.createElement('canvas'), { width: 1, height: 1 }).getContext('2d', { willReadFrequently: true });
  const rgb = c => { ctx.clearRect(0, 0, 1, 1); ctx.fillStyle = '#0000'; ctx.fillStyle = c; ctx.fillRect(0, 0, 1, 1);
    const [r, g, b, a] = ctx.getImageData(0, 0, 1, 1).data; return [r, g, b, a / 255]; };
  const hsl = ([r, g, b]) => { r/=255; g/=255; b/=255; const mx=Math.max(r,g,b), mn=Math.min(r,g,b), l=(mx+mn)/2, d=mx-mn;
    if (!d) return [0,0,l]; const s=d/(1-Math.abs(2*l-1)); let h = mx===r?((g-b)/d)%6 : mx===g?(b-r)/d+2 : (r-g)/d+4;
    return [(h*60+360)%360, s, l]; };
  const purple = c => { const [h,s] = hsl(rgb(c)); return h >= 230 && h <= 290 && s > 0.35; };
  const colorsIn = str => str.match(/(?:rgba?|oklch|oklab|lab|lch|hsla?|color)\([^)]*\)/g) || [];
  const EMOJI = /^[\s\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{2B50}\u{FE0F}\u{200D}]+$/u;

  const text = all.filter(el => /^(P|LI|H[1-6]|BLOCKQUOTE|DD|FIGCAPTION)$/.test(el.tagName) && el.innerText.trim().length > 20);
  const centered = text.filter(el => getComputedStyle(el).textAlign === 'center').length;

  const sizes = [...new Set(all.filter(el => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()))
    .map(el => Math.round(parseFloat(getComputedStyle(el).fontSize))))].sort((a, b) => a - b);
  const steps = sizes.slice(1).map((s, i) => +(s / sizes[i]).toFixed(2));
  const families = [...new Set(all.map(el => getComputedStyle(el).fontFamily.split(',')[0].replace(/["']/g, '').trim().toLowerCase()))];

  const gradientText = all.filter(el => { const s = getComputedStyle(el);
    return /text/.test(s.backgroundClip || s.webkitBackgroundClip) && /gradient/.test(s.backgroundImage); }).length;
  const glass = all.filter(el => { const s = getComputedStyle(el);
    return s.backdropFilter && s.backdropFilter !== 'none' && (rgb(s.backgroundColor)[3] ?? 1) < 0.9; }).length;
  const glow = all.filter(el => /(^|,\s*)(?:rgba?|oklch|oklab|lab|lch|hsla?|color)\([^)]*\)\s+0px\s+0px\s+([1-9]\d*)px/.test(getComputedStyle(el).boxShadow)
    && colorsIn(getComputedStyle(el).boxShadow).some(c => { const v = rgb(c); return v[3] > 0.2 && hsl(v)[1] > 0.35; })).length;
  const purpleSurfaces = all.filter(el => { const s = getComputedStyle(el);
    return [s.backgroundColor, ...colorsIn(s.backgroundImage)].some(c => (rgb(c)[3] ?? 1) > 0.2 && purple(c)); }).length;
  const emojiIcons = all.filter(el => el.children.length === 0 && el.textContent.trim() && EMOJI.test(el.textContent)).length;

  const boxes = all.filter(el => { const r = el.getBoundingClientRect(); return r.width > 120 && r.height > 80; });
  const roundShadow = boxes.filter(el => { const s = getComputedStyle(el);
    return parseFloat(s.borderTopLeftRadius) >= 16 && s.boxShadow !== 'none'; }).length;

  // Rows of >= 3 equal-width siblings that each hold a heading and a paragraph: the feature-card row.
  const cardRows = all.filter(p => {
    const kids = [...p.children].filter(vis);
    if (kids.length < 3 || kids.length > 4) return false;
    const w = kids.map(k => Math.round(k.getBoundingClientRect().width)), t = kids.map(k => Math.round(k.getBoundingClientRect().top));
    return Math.max(...w) - Math.min(...w) <= 2 && Math.max(...t) - Math.min(...t) <= 2
      && kids.every(k => k.querySelector('h2,h3,h4,[role=heading]') && k.querySelector('p'));
  }).length;

  return { textBlocks: text.length, centeredRatio: text.length ? +(centered / text.length).toFixed(2) : 0,
    fontSizes: sizes, sizeSteps: steps, families, gradientText, glass, glow, purpleSurfaces, emojiIcons,
    boxes: boxes.length, roundShadowRatio: boxes.length ? +(roundShadow / boxes.length).toFixed(2) : 0, cardRows };
})();

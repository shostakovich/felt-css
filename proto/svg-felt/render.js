// render.js URL OUT [w h dpr] [clipX clipY clipW clipH]: screenshot with the preinstalled Playwright (used by calibrate.py)
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
(async () => {
  const [url, out, w = 1200, h = 800, dpr = 2, ...clip] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: +dpr });
  await p.goto(url, { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(400);
  const opt = { path: out };
  if (clip.length === 4) opt.clip = { x: +clip[0], y: +clip[1], width: +clip[2], height: +clip[3] };
  else opt.fullPage = true;
  await p.screenshot(opt);
  await b.close();
})();

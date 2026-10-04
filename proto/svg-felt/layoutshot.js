// layoutshot.js URL OUT v(photo|svg) theme [w h dpr]: shoots a real page; for v=svg the library's felt.css and its
// img/ requests are answered with the prototype's copy and SVG assets, everything else is served as is.
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const [url, out, v, theme, w = 1280, h = 900, dpr = 2] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: +dpr });
  await p.addInitScript(t => { try { localStorage.setItem('theme', t); localStorage.setItem('look', 'felt'); } catch {} }, theme);
  if (v === 'svg') {
    const proto = path.join(__dirname);
    await p.route(/\/felt\.css(\?.*)?$/, r => r.fulfill({ contentType: 'text/css', body: fs.readFileSync(path.join(proto, 'felt.css')) }));
    await p.route(/\/img\/[\w-]+\.svg$/, r => r.fulfill({ contentType: 'image/svg+xml', body: fs.readFileSync(path.join(proto, 'img', path.basename(new URL(r.request().url()).pathname))) }));
  }
  await p.goto(url + (url.includes('?') ? '&' : '?') + 'theme=' + theme, { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(500);
  await p.screenshot({ path: out, fullPage: true });
  await b.close();
})();

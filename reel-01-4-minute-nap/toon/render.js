// usage: node render.js stills 1.0 3.0 ...   |   node render.js all
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const [mode, ...ts] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => m.type()==='error' && errs.push(m.text()));
  await p.goto('file://' + path.join(__dirname, 'reel.html')); await p.waitForFunction('window.ready===true');
  const out = path.join(__dirname, '..', 'build', mode === 'all' ? 'toonframes' : 'toonstills'); fs.mkdirSync(out, { recursive: true });
  const list = mode === 'all' ? [...Array(630).keys()].map(i => i / 30) : ts.map(Number);
  for (let i = 0; i < list.length; i++) {
    const url = await p.evaluate(t => { renderAt(t); return document.getElementById('c').toDataURL('image/png'); }, list[i]);
    const name = mode === 'all' ? `f${String(i).padStart(4,'0')}.png` : `s_${list[i].toFixed(2)}.png`;
    fs.writeFileSync(path.join(out, name), Buffer.from(url.split(',')[1], 'base64'));
  }
  if (errs.length) console.log('ERRORS', errs.slice(0,5));
  await b.close(); console.log('done', list.length);
})();

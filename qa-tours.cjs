'use strict';
/* ZENTRA VR3D tours page — QA harness (local + production).
   Verifies the redesign: grid, glass cards, search + pill filters, honest counts. */
const puppeteer = require('puppeteer-core');

const URL = process.env.QA_URL || 'http://127.0.0.1:8114/tours.html';
const PROD = /^https?:/.test(URL) && !/127\.0\.0\.1|localhost/.test(URL);

const EXPECTED_TOURS = 7;
const EXPECTED_ALBUMS = 6;   // DNA Workspace, Armani A1, Armani E1, Terra A2, Terra B1, Terra C

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/usr/bin/google-chrome',
    headless: 'new',
    protocolTimeout: 240000,
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });
  const page = await browser.newPage();

  const jsErrors = [], httpErrors = [];
  page.on('pageerror', e => jsErrors.push(e.message));
  page.on('requestfailed', r => httpErrors.push(r.url()));
  page.on('response', r => { if (r.status() >= 400 && !/favicon/.test(r.url())) httpErrors.push(r.status() + ' ' + r.url()); });

  await page.setViewport({ width: 1440, height: 900 });
  await page.goto(URL, { waitUntil: 'networkidle2', timeout: 90000 });
  await page.waitForSelector('.card', { timeout: 30000 });
  await new Promise(r => setTimeout(r, 500));

  /* ── responsive pass ── */
  const widths = [1440, 1100, 800, 560, 390];
  for (const w of widths) {
    await page.setViewport({ width: w, height: 900 });
    await new Promise(r => setTimeout(r, 320));
    const d = await page.evaluate(() => ({
      sw: document.documentElement.scrollWidth,
      cw: document.documentElement.clientWidth,
      cards: document.querySelectorAll('.card').length,
      cols: getComputedStyle(document.querySelector('.grid')).gridTemplateColumns.split(' ').length,
      broken: [...document.querySelectorAll('img')].filter(i => i.complete && i.naturalWidth === 0).map(i => i.getAttribute('src')),
    }));
    const ok = d.sw <= d.cw + 1 && d.broken.length === 0 && d.cards === EXPECTED_TOURS;
    console.log(`  ${String(w).padEnd(5)} overflow=${d.sw > d.cw + 1} (${d.sw}/${d.cw})  cols=${d.cols}  cards=${d.cards}/${EXPECTED_TOURS}  broken=${d.broken.length}  ${ok ? 'OK' : 'FAIL'}`);
    if (d.broken.length) console.log('    broken:', d.broken.slice(0, 5));
  }

  /* ── desktop assertions ── */
  await page.setViewport({ width: 1440, height: 900 });
  await new Promise(r => setTimeout(r, 320));

  const base = await page.evaluate(() => {
    const cards = [...document.querySelectorAll('.card')];
    const g = document.querySelector('.grid');
    return {
      h1: (document.querySelector('h1') || {}).textContent.trim(),
      cards: cards.length,
      albums: document.querySelectorAll('section.album').length,
      cardAlbum: (document.querySelector('.card .album') || {}).textContent || '',
      perRow: (() => {
        const ys = {};
        [...document.querySelectorAll('.card')].forEach(c => {
          const y = Math.round(c.getBoundingClientRect().y);
          ys[y] = (ys[y] || 0) + 1;
        });
        return Math.max(0, ...Object.values(ys));
      })(),
      pills: [...document.querySelectorAll('.pill')].map(p => p.textContent.trim()),
      pressed: (document.querySelector('.pill[aria-pressed="true"]') || {}).textContent,
      count: (document.querySelector('#count') || {}).textContent.trim(),
      cols: getComputedStyle(g).gridTemplateColumns.split(' ').length,
      glass: cards.length ? getComputedStyle(cards[0]).backdropFilter : '',
      neon: cards.length ? getComputedStyle(cards[0].querySelector('.pano-tag')).color : '',
      hoverTargets: cards.filter(c => c.querySelector('.enter')).length,
      metas: cards.map(c => c.querySelector('.card-meta').textContent.replace(/\s+/g, ' ').trim()),
      hrefs: cards.map(c => c.getAttribute('href')),
      pw: document.querySelectorAll('input[type="password"]').length,
      forms: document.querySelectorAll('form').length,
      navCurrent: (document.querySelector('nav a[aria-current]') || {}).textContent,
    };
  });

  /* ── search behaviour ── */
  await page.type('#q', 'terra');
  await new Promise(r => setTimeout(r, 320));
  const afterSearch = await page.evaluate(() => ({
    cards: document.querySelectorAll('.card').length,
    count: document.querySelector('#count').textContent.trim(),
  }));
  await page.evaluate(() => { const q = document.querySelector('#q'); q.value = ''; q.dispatchEvent(new Event('input')); });
  await new Promise(r => setTimeout(r, 320));

  /* ── pill filter behaviour ── */
  const afterPill = await page.evaluate(async () => {
    const ws = [...document.querySelectorAll('.pill')].find(p => p.textContent.trim() === 'Workspaces');
    if (!ws) return { skipped: true };
    ws.click();
    await new Promise(r => setTimeout(r, 260));
    return {
      cards: document.querySelectorAll('.card').length,
      pressed: document.querySelector('.pill[aria-pressed="true"]').textContent.trim(),
      count: document.querySelector('#count').textContent.trim(),
    };
  });

  console.log('h1               :', JSON.stringify(base.h1));
  console.log('cards / albums   :', base.cards, '/', base.albums);
  console.log('cards per row    :', base.perRow);
  console.log('grid cols @1440  :', base.cols);
  console.log('backdrop-filter  :', base.glass);
  console.log('pano-tag colour  :', base.neon);
  console.log('hover overlays   :', base.hoverTargets, '/', base.cards);
  console.log('pills            :', JSON.stringify(base.pills), 'pressed:', base.pressed);
  console.log('count label      :', JSON.stringify(base.count));
  console.log('meta sample      :', JSON.stringify(base.metas.slice(0, 2)));
  console.log('search "terra"   :', JSON.stringify(afterSearch));
  console.log('pill Workspaces  :', JSON.stringify(afterPill));
  console.log('nav current      :', JSON.stringify(base.navCurrent));
  console.log('password / forms :', base.pw, '/', base.forms, '(both must be 0)');
  console.log('JS errors        :', jsErrors.length, jsErrors.slice(0, 3));
  console.log('HTTP errors      :', httpErrors.length, httpErrors.slice(0, 3));

  const checks = [
    ['h1', base.h1 === 'Virtual Tours'],
    ['7 tour cards', base.cards === EXPECTED_TOURS],
    ['cards fill the row (>=3 at 1440)', base.perRow >= 3],
    ['album shown on card', base.cardAlbum.length > 0],
    ['4 columns at 1440', base.cols === 4],
    ['no orphan album headings', base.albums === 0],
    ['glassmorphism (backdrop-filter blur)', /blur/.test(base.glass || '')],
    ['neon cyan accent', /38,\s*216,\s*245|rgb\(38, 216, 245\)/.test(base.neon || '')],
    ['every card has Enter 360 overlay', base.hoverTargets === base.cards],
    ['filter pills present', base.pills.includes('All') && base.pills.length >= 3],
    ['All pill active by default', base.pressed === 'All'],
    ['count label shown', /of 7 tours/.test(base.count || '')],
    ['meta uses icons (no emoji)', !/[\u{1F300}-\u{1FAFF}]/u.test(base.metas.join(' '))],
    ['every card links to tour.html?id=', base.hrefs.every(h => /^tour\.html\?id=/.test(h || ''))],
    ['search "terra" narrows list', afterSearch.cards > 0 && afterSearch.cards < EXPECTED_TOURS],
    ['search count updates', /of 7 tours/.test(afterSearch.count || '')],
    ['pill filter narrows list', afterPill.skipped || afterPill.cards < EXPECTED_TOURS],
    ['pill aria-pressed moves', afterPill.skipped || afterPill.pressed === 'Workspaces'],
    ['nav marks Browse current', base.navCurrent === 'Browse'],
    ['no password inputs', base.pw === 0],
    ['no forms', base.forms === 0],
    ['no JS errors', jsErrors.length === 0],
    ['no HTTP errors', httpErrors.length === 0],
  ];
  let fail = 0;
  for (const [n, ok] of checks) if (!ok) { console.log('  FAIL:', n); fail++; }
  console.log(`\nRESULT: ${fail === 0 ? 'PASS' : 'FAIL'} (${PROD ? 'production' : 'local'})`);
  await browser.close();
  process.exit(fail === 0 ? 0 : 1);
})().catch(e => { console.error('GAGAL:', e.message); process.exit(2); });

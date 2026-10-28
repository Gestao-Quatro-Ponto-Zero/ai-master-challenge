const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const app = 'file:///home/user/ai-master-challenge/submissions/felipe-holanda/solution/app/index.html';
  for (const [name, vp, scheme] of [['desktop', {width: 1280, height: 900}, 'light'], ['mobile', {width: 390, height: 844}, 'dark']]) {
    const ctx = await b.newContext({ viewport: vp, colorScheme: scheme, acceptDownloads: true });
    const p = await ctx.newPage();
    const errs = [];
    p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.text()); });
    p.on('pageerror', e => errs.push('PAGEERROR ' + e.message));
    await p.goto(app);
    await p.click('[data-tab=time]');
    await p.screenshot({ path: `/tmp/claude-0/shots/${name}-7-saude.png`, fullPage: name === 'mobile' ? false : false });
    await p.locator('#health').screenshot({ path: `/tmp/claude-0/shots/${name}-7b-health.png` });
    await p.click('[data-tab=prova]');
    await p.click('[data-tt="2017-09-18"]');
    await p.screenshot({ path: `/tmp/claude-0/shots/${name}-8-prova.png` });
    await p.click('[data-tab=revisar]');
    const btns = p.locator('[data-decide=encerrar]');
    await btns.nth(0).click(); await p.locator('[data-decide=vivo]').nth(1).click(); await p.locator('[data-decide=encerrar]').nth(2).click();
    await p.screenshot({ path: `/tmp/claude-0/shots/${name}-9-revisar-decisoes.png` });
    const [dl] = await Promise.all([p.waitForEvent('download'), p.click('[data-export]')]);
    const path = `/tmp/claude-0/shots/${name}-export.csv`; await dl.saveAs(path);
    const sw = await p.evaluate(() => document.documentElement.scrollWidth);
    console.log(name, 'scrollWidth', sw, 'errors:', JSON.stringify(errs));
    await ctx.close();
  }
  await b.close();
})();

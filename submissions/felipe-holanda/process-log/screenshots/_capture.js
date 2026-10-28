const { chromium } = require(process.env.PW || 'playwright');
(async () => {
  const b = await chromium.launch();
  const app = 'file:///home/user/ai-master-challenge/submissions/felipe-holanda/solution/app/index.html';
  const out = process.argv[2] || '/tmp/claude-0/shots';
  for (const [name, vp, scheme] of [['desktop', {width: 1280, height: 900}, 'light'], ['mobile', {width: 390, height: 844}, 'dark']]) {
    const ctx = await b.newContext({ viewport: vp, colorScheme: scheme });
    const p = await ctx.newPage();
    const errs = [];
    p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.text()); });
    p.on('pageerror', e => errs.push('PAGEERROR ' + e.message));
    await p.goto(app);
    await p.screenshot({ path: `${out}/${name}-1-foco.png`, fullPage: false });
    await p.click('.deal > button');
    await p.screenshot({ path: `${out}/${name}-2-detail.png`, fullPage: false });
    await p.selectOption('#f-agent', 'Kami Bicknell');
    await p.screenshot({ path: `${out}/${name}-3-agent.png`, fullPage: true });
    await p.click('[data-tab=revisar]');
    await p.screenshot({ path: `${out}/${name}-4-revisar.png` });
    await p.selectOption('#f-agent', '');
    await p.selectOption('#f-manager', '');
    await p.selectOption('#f-region', '');
    await p.click('[data-tab=time]');
    await p.screenshot({ path: `${out}/${name}-5-time.png`, fullPage: true });
    await p.click('[data-tab=metodo]');
    await p.screenshot({ path: `${out}/${name}-6-metodo.png`, fullPage: true });
    const sw = await p.evaluate(() => document.documentElement.scrollWidth);
    console.log(name, 'scrollWidth', sw, 'errors:', JSON.stringify(errs));
    await ctx.close();
  }
  await b.close();
})();

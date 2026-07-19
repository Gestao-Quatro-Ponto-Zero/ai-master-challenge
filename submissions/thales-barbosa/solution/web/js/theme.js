/* PAUTA — tema ECharts + formatadores pt-BR (fonte única dos gráficos). */
(function () {
  'use strict';

  const css = (name) =>
    getComputedStyle(document.documentElement).getPropertyValue(name).trim();

  const T = {
    ink1: css('--ink-1'), ink2: css('--ink-2'), ink3: css('--ink-3'),
    surface1: css('--surface-1'), surface2: css('--surface-2'),
    border: css('--border'), borderStrong: css('--border-strong'),
    hairline: css('--hairline'),
    copper: css('--copper'), copperBright: css('--copper-bright'),
    good: css('--good'), warn: css('--warn'), critical: css('--critical'),
    series: [css('--series-1'), css('--series-2'), css('--series-3'),
             css('--series-4'), css('--series-5'), css('--series-6')],
  };

  const MONO = "'IBM Plex Mono', monospace";
  const UI = "'Instrument Sans', sans-serif";

  echarts.registerTheme('pauta', {
    color: T.series,
    backgroundColor: 'transparent',
    textStyle: { fontFamily: UI, color: T.ink2 },
    axisPointer: {
      lineStyle: { color: T.borderStrong },
      crossStyle: { color: T.borderStrong },
      label: { backgroundColor: T.surface2, color: T.ink1, fontFamily: MONO, fontSize: 11 },
    },
    categoryAxis: {
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: T.ink3, fontFamily: MONO, fontSize: 11 },
      splitLine: { show: false },
    },
    valueAxis: {
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: T.ink3, fontFamily: MONO, fontSize: 11 },
      splitLine: { lineStyle: { color: T.hairline, type: [3, 4] } },
    },
    bar: { itemStyle: { borderRadius: [3, 3, 0, 0] }, barMaxWidth: 28 },
  });

  const nfInt = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });
  const nf1 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const nf2 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  const fmt = {
    int: (v) => nfInt.format(Math.round(v)),
    d1: (v) => nf1.format(v),
    d2: (v) => nf2.format(v),
    pct0: (v) => nfInt.format(Math.round(v)) + '%',
    pct1: (v) => nf1.format(v) + '%',
    /* manchete: R$ 368 mil · R$ 1,2 mi ; tooltip/tabela: valor completo */
    mil: (v) => {
      const a = Math.abs(v);
      if (a >= 995_000) return 'R$ ' + nf1.format(v / 1_000_000) + ' mi';
      if (a >= 1_000) return 'R$ ' + nfInt.format(v / 1_000) + ' mil';
      return 'R$ ' + nfInt.format(v);
    },
    money: (v) => 'R$ ' + nfInt.format(Math.round(v)),
    months: (v) => (v == null ? 'nunca' : nf1.format(v) + ' meses'),
  };

  /* tooltip HTML custom (kicker mono + valores mono à direita) */
  function tooltip(kicker, rows) {
    const body = rows.map(([label, value, color]) =>
      `<div style="display:flex;justify-content:space-between;gap:24px;margin-top:4px;">
         <span style="color:${T.ink3};">${color ? `<span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${color};margin-right:6px;"></span>` : ''}${label}</span>
         <span style="font-family:${MONO};color:${T.ink1};">${value}</span>
       </div>`).join('');
    return `<div style="font-family:${UI};font-size:12.5px;min-width:150px;">
      <div style="font-family:${MONO};font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:${T.ink3};">${kicker}</div>
      ${body}</div>`;
  }

  const TOOLTIP_BOX = {
    backgroundColor: T.surface2,
    borderColor: T.borderStrong,
    borderWidth: 1,
    padding: [10, 14],
    extraCssText: 'border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.5);',
    textStyle: { color: T.ink2 },
  };

  /* count-up com expo-out; respeita prefers-reduced-motion */
  const REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function countUp(el, to, format, duration = 800) {
    if (el._done) { clearTimeout(el._done); el._done = null; }
    if (REDUCED || duration <= 0) { el.textContent = format(to); return; }
    const from = parseFloat(el.dataset.cur || '0');
    const t0 = performance.now();
    el.dataset.cur = to;
    let cancelled = false;
    function tick(t) {
      if (cancelled || parseFloat(el.dataset.cur) !== to) return;
      const p = Math.min(1, (t - t0) / duration);
      const e = 1 - Math.pow(2, -10 * p);
      el.textContent = format(from + (to - from) * e);
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
    // rAF pode não disparar em aba sem pintura — o valor final é garantido:
    el._done = setTimeout(() => {
      cancelled = true;
      if (parseFloat(el.dataset.cur) === to) el.textContent = format(to);
    }, duration + 60);
  }

  /* encolhe o font-size dos números-manchete até caberem na coluna */
  function fitValues(rootSel) {
    document.querySelectorAll(rootSel + ' .m-value').forEach((el) => {
      if (!el.offsetParent) return;              // view oculta
      el.style.fontSize = '';
      let guard = 24;
      while (el.scrollWidth > el.clientWidth + 1 && guard-- > 0) {
        const cur = parseFloat(getComputedStyle(el).fontSize);
        if (cur <= 18) break;
        el.style.fontSize = (cur - 1.5) + 'px';
      }
    });
  }
  window.addEventListener('resize', () => setTimeout(() => fitValues('.view:not([hidden])'), 180));

  window.PAUTA = { T, MONO, UI, fmt, tooltip, TOOLTIP_BOX, countUp, REDUCED, fitValues };
})();

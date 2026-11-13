/* abacus-viz — manifest-driven dashboard runtime on Apache ECharts (prototype v0) */
(function (global) {
  'use strict';

  // Theme tokens live on `.av-root` (and on `[data-theme]` ancestors), so they are read from the mounted root:
  // embedded in an app, the host page's own `--card` / `--accent` tokens never leak into the kit.
  let cssHost = document.documentElement;
  const css = (name) => getComputedStyle(cssHost).getPropertyValue(name).trim();
  const palette = () => [css('--accent'), css('--accent-2'), css('--accent-3'), '#5b7fa6', '#9a6fb0', '#6b8e7a'];
  let colorMap = {};
  // semantic colour: the same category gets the same colour on every tile (manifest.colors: {category: token})
  const colorFor = (key, i = 0) => (colorMap[key] ? css('--' + colorMap[key]) : palette()[i % palette().length]);

  // ---------- formatting ----------
  const fmt = {
    currency_compact: (v) => (v < 0 ? '−$' : '$') + compact(Math.abs(v)),
    integer: (v) => Math.round(v).toLocaleString('en-US'),
    percent: (v) => (v * 100).toFixed(v < 0.1 ? 1 : 0) + '%',
    percent_delta: (v) => (v >= 0 ? '+' : '−') + (Math.abs(v) * 100).toFixed(1) + '%',
    number: (v) => (Math.abs(v) >= 1000 ? compact(v) : (+v).toFixed(Math.abs(v) < 10 ? 1 : 0)),
    status: (v) => v,
    month: (m) => (isTime(m) ? new Date(m.slice(0, 7) + '-02').toLocaleString('en-US', { month: 'short', year: '2-digit' }).replace(' ', ' ’') : m),
  };
  function compact(v) {
    const a = Math.abs(v);
    if (a >= 1e12) return (v / 1e12).toFixed(1) + 'T';
    if (a >= 1e9) return (v / 1e9).toFixed(1) + 'B';
    if (a >= 1e6) return (v / 1e6).toFixed(1) + 'M';
    if (a >= 1e3) return (v / 1e3).toFixed(0) + 'k';
    return String(Math.round(v));
  }
  const f = (format, v) => (fmt[format] || fmt.number)(v);
  // tile-level value formatter: `format` (a fmt key) wins, then the '$M' unit convention, then a bare unit suffix
  const uf = (t, v) => (t.format ? f(t.format, v) : t.unit === '$M' ? '$' + (+v).toFixed(1) + 'M' : (+v).toFixed(Math.abs(v) < 10 ? 1 : 0) + (t.unit ? ' ' + t.unit : ''));
  const isTime = (v) => typeof v === 'string' && /^\d{4}-\d{2}(-\d{2})?$/.test(v);
  // status pills: any label maps to one of the three tones; a column may override via status_map {value: {tone, label}}
  const statusClass = (v, map) => {
    const explicit = map?.[v]?.tone || map?.[v];
    if (typeof explicit === 'string') return explicit;
    const k = String(v).toLowerCase();
    if (/churn|critical|bad|fail|down|red|at.?risk|overdue|lost/.test(k)) return 'at-risk';
    if (/watch|warn|risk|amber|pending|slow|late|medium/.test(k)) return 'watch';
    return 'healthy';
  };
  const statusLabel = (v) => { const s = String(v).replace(/[_-]+/g, ' ').trim(); return s.charAt(0).toUpperCase() + s.slice(1); };
  const xf = (rows, key) => (rows.length && isTime(rows[0][key]) ? fmt.month : (v) => v);

  // ---------- ECharts theme ----------
  function registerTheme() {
    echarts.registerTheme('abacus', {
      color: palette(),
      backgroundColor: 'transparent',
      textStyle: { fontFamily: css('--font-body'), color: css('--ink-2') },
      title: { show: false },
      legend: { show: false },
      grid: { left: 8, right: 16, top: 24, bottom: 8, containLabel: true },
      categoryAxis: { axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: css('--muted'), fontSize: 11.5, margin: 12, hideOverlap: true }, splitLine: { show: false } },
      valueAxis: { axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: css('--muted'), fontSize: 11.5, hideOverlap: true }, splitLine: { lineStyle: { color: css('--line'), type: [2, 4] } } },
      tooltip: { backgroundColor: css('--card'), borderColor: css('--line'), borderWidth: 1, textStyle: { color: css('--ink'), fontSize: 12.5 }, padding: [8, 12], extraCssText: 'box-shadow: var(--shadow); border-radius: 10px;' },
      line: { smooth: 0.25, symbol: 'none', lineStyle: { width: 2.2 } },
      bar: { barMaxWidth: 28, itemStyle: { borderRadius: [0, 4, 4, 0] } },
      animationDuration: 900, animationEasing: 'cubicOut', animationDurationUpdate: 600, animationEasingUpdate: 'cubicInOut',
    });
  }

  // ---------- helpers ----------
  const el = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
  const uniq = (rows, k) => [...new Set(rows.map((r) => r[k]))];
  const sum = (a) => a.reduce((s, v) => s + v, 0);
  function countUp(node, format, target, ms = 900) {
    const t0 = performance.now();
    const step = (t) => { const p = Math.min(1, (t - t0) / ms); const e = 1 - Math.pow(1 - p, 3); node.textContent = f(format, target * e); if (p < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  }

  // ---------- runtime ----------
  // Standalone (the dashboard IS the page): the theme sits on <html>, the page background follows it.
  // Embedded (`opts.embedded`, a page inside an app): the theme sits on the root, the host owns the page and its
  // theme switch, so the kit's Theme button is hidden and nothing outside the root is touched.
  // Slots (`opts.slots`, the story runtime): the host's own markup carries `[data-tile="<id>"]` placeholders (and
  // optional `[data-filter="<id>"]` ones); the kit renders into those instead of building header / filters / grid,
  // and with `opts.lazy` only when the host asks (`renderIn(node)`), so a scene's charts animate when it is entered.
  function mount(root, manifest, data, opts = {}) {
    const embedded = !!opts.embedded;
    const slots = !!opts.slots;
    const lazy = slots && !!opts.lazy;
    const themeHost = embedded ? root : document.documentElement;
    root.classList.add('av-root');
    cssHost = root;
    registerTheme();
    // `auto` (embedded): follow the host app's dark mode (the `dark` class on <html>) — midnight when dark
    const autoTheme = () => (document.documentElement.classList.contains('dark') ? 'midnight' : '');
    const themeOf = (t) => (t === 'light' || t === 'editorial' ? '' : t === 'auto' ? autoTheme() : t);
    const ownsTheme = opts.theme !== false; // the story runtime sets the theme itself
    if (ownsTheme && manifest.theme && (embedded || !new URLSearchParams(global.location.search).get('theme'))) themeHost.dataset.theme = themeOf(manifest.theme);
    let themeWatch = null;
    if (ownsTheme && embedded && manifest.theme === 'auto') {
      themeWatch = new MutationObserver(() => { const t = autoTheme(); if (t !== (themeHost.dataset.theme || '')) { themeHost.dataset.theme = t; rerender(); } });
      themeWatch.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    }
    const paintPage = () => { if (!embedded && ownsTheme) { document.documentElement.style.background = css('--bg'); document.documentElement.style.color = css('--ink'); } };
    paintPage();
    colorMap = manifest.colors || {};
    const charts = [];
    const state = { filters: {}, tiles: {}, sorts: {}, rendered: new Set() };
    (manifest.filters || []).forEach((fl) => (state.filters[fl.id] = fl.default ?? fl.options[0]));

    const asofText = (iso) => {
      const d = iso ? new Date(iso) : null;
      const when = d && !isNaN(d) ? d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : 'now';
      return `<span class="dot"></span>Data as of ${when}`;
    };
    // a filter's tab bar, into any container (the dashboard's filter row or a story's `[data-filter]` slot)
    const filterTabs = (fl) => {
      const tabs = el('div', 'av-tabs');
      tabs.setAttribute('role', 'tablist');
      fl.options.forEach((o) => {
        const b = el('button', 'av-tab', o);
        b.setAttribute('role', 'tab');
        b.setAttribute('aria-selected', String(state.filters[fl.id] === o));
        b.onclick = () => { state.filters[fl.id] = o; [...tabs.children].forEach((c) => c.setAttribute('aria-selected', String(c === b))); fl.applies_to.forEach((id) => { if (state.tiles[id]) renderTile(id, true); }); dimForFilter(fl, o); };
        tabs.appendChild(b);
      });
      return tabs;
    };

    if (slots) {
      // placeholders in the host markup become the tile nodes; tiles without a placeholder are not drawn
      const specs = Object.fromEntries(manifest.tiles.map((t) => [t.id, t]));
      root.querySelectorAll('[data-tile]').forEach((node, i) => {
        const t = specs[node.dataset.tile];
        if (!t || state.tiles[t.id]) return;
        node.classList.add('av-tile', 'av-slot');
        if (t.type === 'kpi') node.classList.add('av-kpi');
        node.style.setProperty('--i', i % 6);
        node.setAttribute('data-export-visual-key', t.id);
        state.tiles[t.id] = { spec: t, node };
      });
      (manifest.filters || []).forEach((fl) => {
        root.querySelectorAll(`[data-filter="${fl.id}"]`).forEach((slot) => { slot.innerHTML = ''; slot.classList.add('av-filters'); if (fl.label) slot.appendChild(el('span', 'av-filter-label', fl.label)); slot.appendChild(filterTabs(fl)); });
      });
    } else {
      root.innerHTML = '';
      // the root paints the canvas edge to edge; the body centres the content (max-width, gutters)
      const body = el('div', 'av-body');
      root.appendChild(body);

      // header
      const head = el('div', 'av-header');
      const left = el('div');
      if (manifest.eyebrow) left.appendChild(el('div', 'av-eyebrow', manifest.eyebrow));
      left.appendChild(el('h1', 'av-title', manifest.title));
      if (manifest.subtitle) left.appendChild(el('p', 'av-subtitle', manifest.subtitle));
      const meta = el('div', 'av-meta');
      meta.appendChild(el('div', 'av-asof', asofText(manifest.data_as_of)));
      if (!embedded) {
        const tb = el('div', 'av-toolbar');
        const themeBtn = el('button', 'av-btn', '◐ Theme');
        themeBtn.onclick = () => { const d = themeHost; const order = ['', 'journal', 'midnight']; d.dataset.theme = order[(order.indexOf(d.dataset.theme || '') + 1) % order.length]; rerender(); };
        // Refresh / Share belong to the host pane header; the page itself only toggles the theme.
        tb.append(themeBtn);
        meta.appendChild(tb);
      }
      head.append(left, meta);
      body.appendChild(head);

      // filters
      if (manifest.filters?.length) {
        const bar = el('div', 'av-filters');
        manifest.filters.forEach((fl) => {
          bar.appendChild(el('span', 'av-filter-label', fl.label));
          bar.appendChild(filterTabs(fl));
        });
        body.appendChild(bar);
      }

      // grid
      const grid = el('div', 'av-grid');
      body.appendChild(grid);
      manifest.tiles.forEach((t, i) => {
        const tile = el('section', 'av-tile' + (t.type === 'kpi' ? ' av-kpi' : ''));
        tile.style.setProperty('--span', t.span || 4);
        tile.style.setProperty('--i', i);
        tile.dataset.tile = t.id;
        tile.setAttribute('data-export-visual-key', t.id);
        grid.appendChild(tile);
        state.tiles[t.id] = { spec: t, node: tile };
      });

      const src = el('div', 'av-sources', (manifest.sources || []).map((s) => `<span>${s.label}</span>`).join(''));
      body.appendChild(src);
    }

    // A tile pinned to one option (`where: {<filter field>: value}`, the kpi strip) dims when another option is
    // selected: the strip responds above the fold, so a click that only re-renders tiles further down still reads.
    function dimForFilter(fl, v) {
      Object.values(state.tiles).forEach(({ spec, node }) => {
        const pinned = spec.where && spec.where[fl.field] !== undefined;
        node.classList.toggle('av-dim', !!pinned && v !== 'All' && spec.where[fl.field] !== v);
      });
    }

    // ---------- data access ----------
    function rowsFor(t) {
      let rows = data[t.data] || [];
      if (t.where) rows = rows.filter((r) => Object.entries(t.where).every(([k, v]) => r[k] === v));
      (manifest.filters || []).forEach((fl) => {
        if (!fl.applies_to.includes(t.id)) return;
        const v = state.filters[fl.id];
        if (rows.length && rows[0][fl.field] !== undefined) {
          const has = rows.some((r) => r[fl.field] === v);
          rows = has ? rows.filter((r) => r[fl.field] === v) : (v === 'All' ? rows.filter((r) => r[fl.field] !== 'All') : []);
        }
      });
      return rows;
    }

    function chartIn(container, cls) {
      const box = el('div', 'av-chart' + (cls ? ' ' + cls : ''));
      container.appendChild(box);
      const c = echarts.init(box, 'abacus', { renderer: 'canvas' });
      charts.push(c);
      new ResizeObserver(() => c.resize()).observe(box);
      return c;
    }

    function shell(t, node) {
      node.innerHTML = '';
      if (t.title) {
        const h = el('div', 'av-tile-head');
        const tt = el('div');
        tt.appendChild(el('h3', 'av-tile-title', t.title));
        if (t.subtitle) tt.appendChild(el('p', 'av-tile-sub', t.subtitle));
        h.appendChild(tt);
        const act = el('div', 'av-tile-actions');
        const q = el('button', 'av-icon-btn', 'View query'); q.onclick = () => openDrawer(t, 'query');
        const d = el('button', 'av-icon-btn', 'Data'); d.onclick = () => openDrawer(t, 'data');
        act.append(q, d);
        h.appendChild(act);
        node.appendChild(h);
      }
      if (t.insight) node.appendChild(el('p', 'av-tile-insight', t.insight));
    }

    // ---------- renderers ----------
    const R = {
      kpi(t, node, rows) {
        const r = rows[0]; if (!r) return;
        node.innerHTML = '';
        node.style.setProperty('--kpi-accent', css('--' + (t.accent || 'ink')));
        node.appendChild(el('p', 'av-kpi-label', r.label));
        const row = el('div', 'av-kpi-row');
        const val = el('div', 'av-kpi-value', f(r.format, r.value));
        row.appendChild(val);
        const sp = el('div', 'av-kpi-spark'); row.appendChild(sp);
        node.appendChild(row);
        const delta = typeof r.delta === 'number' ? r.delta : 0;
        const good = r.good_when === 'down' ? delta < 0 : delta >= 0;
        if (typeof r.delta === 'number') node.appendChild(el('span', 'av-delta ' + (good ? 'up' : 'down'), `${delta >= 0 ? '▲' : '▼'} ${(Math.abs(delta) * 100).toFixed(1)}${r.format === 'percent' ? ' pts' : '%'} <small>${r.delta_label || ''}</small>`));
        countUp(val, r.format, r.value);
        if (!Array.isArray(r.spark) || r.spark.length < 2) { sp.remove(); return; }
        const c = echarts.init(sp, 'abacus'); charts.push(c);
        c.setOption({ grid: { left: 0, right: 0, top: 4, bottom: 0 }, xAxis: { type: 'category', show: false, data: r.spark.map((_, i) => i) }, yAxis: { type: 'value', show: false, min: 'dataMin' }, tooltip: { show: false },
          series: [{ type: 'line', data: r.spark, smooth: 0.3, symbol: 'none', lineStyle: { width: 1.8, color: good ? css('--pos') : css('--neg') }, areaStyle: { color: good ? css('--pos-bg') : css('--neg-bg') } }] });
      },

      area(t, node, rows) {
        shell(t, node);
        const xs = uniq(rows, t.x);
        const c = chartIn(node);
        const colors = t.series.map((s, i) => colorFor(s.label, i));
        const lastRow = rows.find((r) => r[t.x] === xs[xs.length - 1]) || {};
        const series = t.series.map((s, i) => ({
          name: s.label, type: 'line', stack: t.stacked ? 'total' : undefined, smooth: 0.3, symbol: 'none',
          data: xs.map((x) => rows.find((r) => r[t.x] === x)?.[s.field] ?? 0),
          lineStyle: { width: i === 0 ? 0 : 1.6, color: colors[i] },
          areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: colors[i] + (i === 0 ? 'cc' : 'b3') }, { offset: 1, color: colors[i] + (i === 0 ? '66' : '33') }]) },
          emphasis: { focus: 'series' },
          endLabel: { show: true, formatter: t.end_values ? `{a|${s.label}}\n{b|${uf(t, +lastRow[s.field] || 0)}}` : s.label, rich: { a: { color: colors[i], fontSize: 11.5, fontWeight: 600, lineHeight: 15 }, b: { color: css('--ink'), fontSize: 11, lineHeight: 14 } }, color: colors[i], fontSize: 11.5, fontWeight: 600, offset: [6, 0] },
          markArea: i === 0 && t.bands ? { silent: true, itemStyle: { color: css('--ink') + '0a' }, label: { show: true, position: 'insideTopLeft', color: css('--muted'), fontSize: 10.5, padding: [6, 0, 0, 6] }, data: t.bands.map((b) => [{ xAxis: b.from, name: b.label }, { xAxis: b.to }]) } : undefined,
          markLine: i === 0 && t.annotations ? { symbol: 'none', silent: true, lineStyle: { color: css('--muted'), type: [3, 4], width: 1 }, label: { position: 'end', color: css('--ink-2'), fontSize: 11, formatter: (p) => p.name, distance: 6 }, data: t.annotations.map((a) => ({ xAxis: a.x, name: a.label })) } : undefined,
        }));
        c.setOption({
          grid: { left: 8, right: 86, top: 36, bottom: 8, containLabel: true },
          tooltip: { trigger: 'axis', axisPointer: { type: 'line', lineStyle: { color: css('--line') } }, valueFormatter: (v) => uf(t, v) },
          xAxis: { type: 'category', data: xs, boundaryGap: false, axisLabel: { formatter: xf(rows, t.x) } },
          yAxis: { type: 'value', axisLabel: { formatter: (v) => uf(t, v) } },
          series,
        });
        // de-collide end labels of thin stacked bands: measure pixel y of each series' end, push apart >= 30px
        if (t.stacked && series.length > 1) {
          let cum = 0;
          const ys = series.map((sr) => { cum += +sr.data[sr.data.length - 1] || 0; return c.convertToPixel({ seriesIndex: 0 }, [xs.length - 1, cum])[1]; });
          // series i sits above series i-1 (smaller pixel y); keep each label >= 30px above the one below it
          const want = ys.slice();
          for (let i = 1; i < ys.length; i++) want[i] = Math.min(want[i], want[i - 1] - 30);
          const shift = Math.max(0, 14 - want[want.length - 1]);
          c.setOption({ series: series.map((sr, i) => ({ endLabel: { ...sr.endLabel, offset: [6, want[i] + shift - ys[i]] } })) });
        }
      },

      bar(t, node, rows) {
        shell(t, node);
        rows = [...rows].sort((a, b) => (t.sort === 'desc' ? b[t.value] - a[t.value] : a[t.value] - b[t.value]));
        const c = chartIn(node);
        const colors = palette();
        c.setOption({
          grid: { left: 8, right: 56, top: 8, bottom: 8, containLabel: true },
          tooltip: { trigger: 'item', valueFormatter: (v) => uf(t, v) },
          xAxis: { type: 'value', axisLabel: { show: false }, splitLine: { show: false } },
          yAxis: { type: 'category', inverse: true, data: rows.map((r) => r[t.category]), axisLabel: { color: css('--ink'), fontSize: 13 } },
          series: [{ type: 'bar', barMaxWidth: 22, data: rows.map((r) => ({ value: r[t.value], itemStyle: { color: r[t.value] < 0 ? css('--neg') : (colorMap[r[t.category]] ? colorFor(r[t.category]) : colors[0]), borderRadius: r[t.value] < 0 ? [4, 0, 0, 4] : [0, 4, 4, 0] } })),
            label: { show: true, position: 'right', color: css('--ink'), fontWeight: 600, formatter: (p) => (t.signed === false ? '' : p.value >= 0 ? '+' : '−') + uf(t, Math.abs(p.value)) }, showBackground: true, backgroundStyle: { color: css('--bg'), borderRadius: 4 } }],
        });
      },

      heatmap(t, node, rows) {
        shell(t, node);
        const xs = uniq(rows, t.x).sort((a, b) => a - b);
        const ys = uniq(rows, t.y);
        const vals = rows.map((r) => r[t.value]);
        // legend ends follow the tile's own format/unit (percent for a cohort grid, '°C' for a temperature one)
        const lo = t.min ?? Math.min(...vals), hi = t.max ?? Math.max(...vals);
        const c = chartIn(node);
        c.setOption({
          grid: { left: 8, right: 8, top: 8, bottom: 56, containLabel: true },
          tooltip: { formatter: (p) => `${t.y_label || t.y}: ${fmt.month(ys[p.value[1]])} · ${t.x_label || t.x}: ${xs[p.value[0]]}<br><b>${uf(t, p.value[2])}</b>` },
          xAxis: { type: 'category', data: xs, name: t.x_label, nameLocation: 'middle', nameGap: 28, nameTextStyle: { color: css('--muted'), fontSize: 11.5 }, axisLabel: { color: css('--muted') } },
          yAxis: { type: 'category', data: ys, inverse: true, axisLabel: { formatter: fmt.month, color: css('--ink-2') } },
          visualMap: { min: lo, max: hi, show: true, orient: 'horizontal', right: 0, bottom: 0, itemWidth: 8, itemHeight: 90, text: [uf(t, hi), uf(t, lo)], textStyle: { color: css('--muted'), fontSize: 10.5 }, inRange: { color: [css('--bg'), css('--accent') + '99', css('--accent')] } },
          series: [{ type: 'heatmap', data: rows.map((r) => [xs.indexOf(r[t.x]), ys.indexOf(r[t.y]), r[t.value]]), itemStyle: { borderColor: css('--card'), borderWidth: 2, borderRadius: 3 },
            label: { show: true, fontSize: 10.5, color: css('--ink'), formatter: (p) => (t.format === 'percent' ? (p.value[2] >= 1 ? '' : Math.round(p.value[2] * 100)) : fmt.number(p.value[2])) }, emphasis: { itemStyle: { shadowBlur: 8, shadowColor: 'rgba(0,0,0,.25)' } } }],
        });
      },

      // funnel: stages left-aligned, every label in one column clear of the widest stage (each leader runs from the
      // stage's mid-right edge to the column). Widths are log-scaled once the stages span >10x so the small stages stay
      // readable; the exact count, share of the first stage and step conversion are printed, not inferred from width.
      funnel(t, node, rows) {
        shell(t, node);
        rows = [...rows].sort((a, b) => b[t.value] - a[t.value]);
        const c = chartIn(node);
        const vals = rows.map((r) => +r[t.value]);
        const top = vals[0], first = rows[0][t.category];
        const vmin = Math.max(Math.min(...vals), 1e-9), useLog = top / vmin > 10;
        const geo = (v) => (useLog ? Math.log10(Math.max(v, vmin) / vmin) : v);
        const gmax = geo(top) || 1, MIN = 0.3, GAP = 16, FUNNEL = 0.52;
        // stage i is a trapezoid from frac(i) to frac(i+1) of the funnel width; the last one ends at minSize
        const frac = (i) => (i < vals.length ? MIN + (1 - MIN) * (geo(vals[i]) / gmax) : MIN);
        const pct = (a, b) => { const p = (a / b) * 100; return (p >= 10 ? p.toFixed(0) : p >= 1 ? p.toFixed(1) : p.toFixed(2)) + '%'; };
        const share = (i) => `${pct(vals[i], top)} of ${first}`;
        const alpha = (i) => Math.round(255 * Math.max(0.4, 1 - i * 0.12)).toString(16).padStart(2, '0');
        const layout = () => {
          if (c.isDisposed() || !c.getWidth()) return;
          const W = c.getWidth() * FUNNEL, colX = Math.round(W) + GAP, wrap = { width: Math.max(80, c.getWidth() - colX - 8), overflow: 'break' };
          c.setOption({
            tooltip: { trigger: 'item', position: (pt, p, dom, rect, size) => [Math.max(0, pt[0] - size.contentSize[0] - 12), Math.max(0, pt[1] - size.contentSize[1] / 2)],
              formatter: (p) => { const i = p.dataIndex; return `${p.name}<br><b>${fmt.integer(vals[i])}</b>` + (i ? ` · ${share(i)}` : '') + (i > 1 ? `<br>${pct(vals[i], vals[i - 1])} of ${rows[i - 1][t.category]}` : ''); } },
            series: [{ type: 'funnel', left: 0, width: FUNNEL * 100 + '%', top: 6, bottom: 6, sort: 'descending', funnelAlign: 'left', gap: 4, min: 0, max: gmax, minSize: MIN * 100 + '%', maxSize: '100%',
              itemStyle: { borderColor: css('--card'), borderWidth: 2, borderRadius: 4 },
              label: { position: 'right', color: css('--ink'), fontSize: 12,
                formatter: (p) => `{n|${p.name}}\n{v|${fmt.integer(vals[p.dataIndex])}${p.dataIndex ? ' · ' + share(p.dataIndex) : ''}}`,
                // width/overflow on the rich segments (not the block) so long names wrap without losing the line break
                rich: { n: { fontWeight: 600, color: css('--ink'), lineHeight: 16, ...wrap }, v: { color: css('--muted'), fontSize: 11.5, lineHeight: 15, ...wrap } } },
              labelLine: { lineStyle: { color: css('--line') } },
              data: rows.map((r, i) => ({ name: r[t.category], value: geo(vals[i]), itemStyle: { color: palette()[0] + alpha(i) },
                labelLine: { length: colX - (W * (frac(i) + frac(i + 1))) / 2 } })) }],
          });
        };
        layout();
        new ResizeObserver(layout).observe(c.getDom());
      },

      table(t, node, rows) {
        shell(t, node);
        const sort = state.sorts[t.id] || t.sort;
        if (sort) {
          const cmp = (a, b) => (typeof a[sort.field] === 'number' ? a[sort.field] - b[sort.field] : String(a[sort.field]).localeCompare(String(b[sort.field])));
          rows = [...rows].sort((a, b) => (sort.dir === 'desc' ? -cmp(a, b) : cmp(a, b)));
        }
        const max = Math.max(...rows.map((r) => r[t.columns.find((c) => c.bar)?.field] || 0));
        const tbl = el('table', 'av-table');
        const arrow = (c) => (sort && sort.field === c.field ? (sort.dir === 'desc' ? ' ↓' : ' ↑') : '');
        tbl.innerHTML = `<thead><tr>${t.columns.map((c) => `<th class="${c.format && c.format !== 'status' ? 'num' : ''}" data-field="${c.field}">${c.label}${arrow(c)}</th>`).join('')}</tr></thead>`;
        tbl.querySelectorAll('th').forEach((th) => (th.onclick = () => {
          const field = th.dataset.field;
          state.sorts[t.id] = { field, dir: sort && sort.field === field && sort.dir === 'desc' ? 'asc' : 'desc' };
          renderTile(t.id, true);
        }));
        const tb = el('tbody');
        rows.forEach((r) => {
          const tr = el('tr');
          tr.innerHTML = t.columns.map((c) => {
            const v = r[c.field];
            if (c.format === 'swatch') return `<td><span class="av-swatch" style="background:${colorFor(v)}"></span>${v}</td>`;
            if (c.format === 'status') return `<td><span class="av-status ${statusClass(v, c.status_map)}">${c.status_map?.[v]?.label ?? statusLabel(v)}</span></td>`;
            if (c.format === 'percent_delta') return `<td class="num ${v >= 0 ? 'av-pos' : 'av-neg'}">${fmt.percent_delta(v)}</td>`;
            if (c.bar) return `<td class="num"><span class="av-bar" style="width:${Math.round((v / max) * 70)}px"></span>${f(c.format, v)}</td>`;
            return `<td class="${c.format ? 'num' : ''}">${c.format ? f(c.format, v) : v}</td>`;
          }).join('');
          tb.appendChild(tr);
        });
        tbl.appendChild(tb);
        const wrap = el('div', 'av-table-wrap');
        wrap.appendChild(tbl);
        node.appendChild(wrap);
      },

      // diverging lollipop: stem from zero to value, dot coloured by a semantic category, value on the dot side
      lollipop(t, node, rows) {
        shell(t, node);
        const n = t.limit || 14, byV = [...rows].sort((a, b) => b[t.value] - a[t.value]);
        rows = byV.length > n ? [...byV.slice(0, Math.ceil(n / 2)), ...byV.slice(-Math.floor(n / 2))] : byV;
        const c = chartIn(node, 'tall');
        const ext = Math.max(...rows.map((r) => Math.abs(r[t.value]))) * (c.getDom().clientWidth < 420 ? 1.7 : 1.35);
        const cats = rows.map((r) => r[t.category]);
        const vfmt = (v) => (v >= 0 ? '+' : '−') + (t.format === 'currency_compact' ? '$' + compact(Math.abs(v)) : f(t.format, Math.abs(v)));
        c.setOption({
          grid: { left: 8, right: 8, top: 6, bottom: 6, containLabel: true },
          tooltip: { trigger: 'item', formatter: (p) => `<b>${p.name}</b><br>${vfmt(p.value)} · ${rows[p.dataIndex][t.color]}` },
          xAxis: { type: 'value', min: -ext, max: ext, axisLabel: { show: false }, splitLine: { show: false } },
          yAxis: { type: 'category', data: cats, inverse: true, axisLabel: { color: css('--ink'), fontSize: 12.5, margin: 10 }, axisLine: { show: true, lineStyle: { color: css('--ink'), width: 1 } } },
          series: [
            { type: 'bar', barWidth: 2, silent: true, data: rows.map((r) => ({ value: r[t.value], itemStyle: { color: colorFor(r[t.color]) + '99', borderRadius: 0 } })), z: 1 },
            { type: 'scatter', symbolSize: 13, data: rows.map((r) => ({ name: r[t.category], value: r[t.value], itemStyle: { color: colorFor(r[t.color]), borderColor: css('--card'), borderWidth: 2 } })),
              label: { show: true, color: css('--ink'), fontWeight: 600, fontSize: 11.5, formatter: (p) => vfmt(p.value), position: 'right', distance: 10 },
              labelLayout: (p) => ({ x: p.rect.x + (rows[p.dataIndex][t.value] < 0 ? -p.rect.width - 10 : p.rect.width + 10), align: rows[p.dataIndex][t.value] < 0 ? 'right' : 'left' }),
              emphasis: { scale: 1.6 }, z: 3 },
          ],
          animationDelay: (i) => i * 40,
        });
      },

      // beeswarm: one dot per row along a value axis, packed so dots never overlap; colour semantic, outliers labelled
      beeswarm(t, node, rows) {
        shell(t, node);
        const c = chartIn(node, 'tall');
        const box = c.getDom();
        const W = box.clientWidth, H = box.clientHeight;
        const r = t.radius || 4.5, pad = { l: 16, r: (t.label_top ? Math.min(110, Math.round(c.getDom().clientWidth * 0.28)) : 16), t: 8, b: 34 };
        const log = t.scale === 'log';
        const xv = (v) => (log ? Math.log10(v) : v);
        const vals = rows.map((d) => xv(d[t.value]));
        const lo = Math.min(...vals), hi = Math.max(...vals);
        const px = (v) => pad.l + ((xv(v) - lo) / (hi - lo)) * (W - pad.l - pad.r);
        // greedy pack: sort by x, place each dot at the lowest |y| lane that doesn't collide
        const placed = [];
        const mid = (H - pad.b + pad.t) / 2;
        [...rows].sort((a, b) => b[t.value] - a[t.value]).forEach((d) => {
          const x = px(d[t.value]);
          const near = placed.filter((p) => Math.abs(p.x - x) < 2 * r + 1);
          let y = mid, k = 0;
          while (near.some((p) => (p.x - x) ** 2 + (p.y - y) ** 2 < (2 * r + 1) ** 2)) { k++; y = mid + (k % 2 ? 1 : -1) * Math.ceil(k / 2) * (r * 1.75); }
          placed.push({ x, y, d });
        });
        const top = [...rows].sort((a, b) => b[t.value] - a[t.value]).slice(0, t.label_top || 3).map((d) => d[t.category]);
        const ticks = t.ticks || [];
        c.setOption({
          grid: { left: pad.l, right: pad.r, top: pad.t, bottom: pad.b },
          tooltip: { trigger: 'item', formatter: (p) => { const d = p.data.d; return `<b>${d[t.category]}</b><br>${f(t.format, d[t.value])} · ${d[t.color]}${t.sub ? ' · ' + d[t.sub] : ''}`; } },
          xAxis: { type: 'value', min: 0, max: W, show: false }, yAxis: { type: 'value', min: 0, max: H, inverse: true, show: false },
          graphic: [
            { type: 'line', shape: { x1: pad.l, y1: H - pad.b + 8, x2: W - pad.r, y2: H - pad.b + 8 }, style: { stroke: css('--line'), lineWidth: 1 }, silent: true },
            ...ticks.map((v) => ({ type: 'group', children: [
              { type: 'line', shape: { x1: px(v), y1: H - pad.b + 4, x2: px(v), y2: H - pad.b + 12 }, style: { stroke: css('--muted') } },
              { type: 'text', style: { text: f(t.format, v), x: px(v), y: H - pad.b + 16, textAlign: 'center', fill: css('--muted'), fontSize: 11, fontFamily: css('--font-body') } }] })),
          ],
          series: [{ type: 'scatter', symbolSize: r * 2, data: placed.map((p) => ({ value: [p.x, p.y], d: p.d, itemStyle: { color: colorFor(p.d[t.color]), opacity: 0.92 } })),
            label: { show: true, position: 'right', distance: 7, color: css('--ink'), fontSize: 11, fontWeight: 600, formatter: (p) => (top.includes(p.data.d[t.category]) ? p.data.d[t.category] : '') }, labelLayout: { hideOverlap: true, moveOverlap: 'shiftY' },
            emphasis: { scale: 1.8, itemStyle: { borderColor: css('--ink'), borderWidth: 1.5 } }, animationDelay: (i) => Math.min(i * 3, 700) }],
        });
      },

      // bubble landscape: x/y with quadrant guides at the medians, bubble area = size field, biggest few labelled
      bubble(t, node, rows) {
        shell(t, node);
        const c = chartIn(node, 'tall');
        const med = (a) => { const s = [...a].sort((p, q) => p - q); return s[Math.floor(s.length / 2)]; };
        const mx = med(rows.map((r) => r[t.x])), my = med(rows.map((r) => r[t.y]));
        const smax = Math.max(...rows.map((r) => r[t.size]));
        const big = [...rows].sort((a, b) => b[t.size] - a[t.size]).slice(0, t.label_top || 6).map((r) => r[t.category]);
        c.setOption({
          grid: { left: 8, right: 90, top: 30, bottom: 8, containLabel: true },
          tooltip: { trigger: 'item', formatter: (p) => { const d = rows[p.dataIndex]; return `<b>${d[t.category]}</b><br>${t.x_label}: ${f(t.x_format, d[t.x])}<br>${t.y_label}: ${f(t.y_format, d[t.y])}<br>${t.size_label}: ${f(t.size_format, d[t.size])}`; } },
          xAxis: { type: 'value', name: t.x_label, nameLocation: 'middle', nameGap: 26, nameTextStyle: { color: css('--muted'), fontSize: 11.5 }, axisLabel: { hideOverlap: true, formatter: (v) => (t.x_format === 'percent_delta' ? (v > 0 ? '+' : '') + Math.round(v * 100) + '%' : f(t.x_format, v)) }, splitLine: { show: false } },
          yAxis: { type: 'value', name: t.y_label + ' ↑', nameLocation: 'end', nameGap: 10, nameTextStyle: { color: css('--muted'), fontSize: 11.5, align: 'left' }, axisLabel: { formatter: (v) => f(t.y_format, v) }, splitLine: { show: false } },
          series: [{ type: 'scatter', data: rows.map((r) => ({ value: [r[t.x], r[t.y]], itemStyle: { color: colorFor(r[t.color]) + 'b3', borderColor: colorFor(r[t.color]), borderWidth: 1 } })),
            symbolSize: (v, p) => 6 + Math.sqrt(rows[p.dataIndex][t.size] / smax) * 46,
            label: { show: true, position: 'right', distance: 6, color: css('--ink'), fontSize: 11, fontWeight: 600, formatter: (p) => (big.includes(rows[p.dataIndex][t.category]) ? rows[p.dataIndex][t.category] : '') }, labelLayout: { hideOverlap: true },
            emphasis: { focus: 'self', itemStyle: { opacity: 1, borderColor: css('--ink') } },
            markLine: { symbol: 'none', silent: true, lineStyle: { color: css('--muted'), type: [3, 4], width: 1 }, label: { color: css('--muted'), fontSize: 10.5, position: 'insideEndTop' },
              data: [{ xAxis: mx, label: { show: false } }, { yAxis: my, name: 'median ' + f(t.y_format, my), label: { position: 'end' } }] },
            animationDelay: (i) => Math.min(i * 4, 800) }],
        });
      },

      // unit chart: one dot per row, grouped into columns by `group`, coloured by `color` — "every customer, at a glance"
      dots(t, node, rows) {
        shell(t, node);
        const groups = t.groups || uniq(rows, t.group);
        const order = t.color_order || uniq(rows, t.color);
        const wrap = el('div', 'av-dots');
        wrap.style.setProperty('--cols', groups.length);
        node.appendChild(wrap);
        let k = 0;
        groups.forEach((g) => {
          const gr = rows.filter((r) => r[t.group] === g).sort((a, b) => order.indexOf(a[t.color]) - order.indexOf(b[t.color]));
          const col = el('div', 'av-dots-col');
          const counts = order.map((o) => gr.filter((r) => r[t.color] === o).length);
          col.appendChild(el('div', 'av-dots-head', `<span class="av-sm-name">${g}</span><span class="av-sm-val">${gr.length}</span>`));
          const field = el('div', 'av-dots-field');
          gr.forEach((r) => { const d = el('span', 'av-dot'); d.style.background = colorFor(r[t.color]); d.style.animationDelay = Math.min(k++ * 2, 900) + 'ms'; d.title = `${r[t.category]} · ${r[t.color]}`; field.appendChild(d); });
          col.appendChild(field);
          col.appendChild(el('div', 'av-dots-foot', order.map((o, i) => `<span><i class="av-swatch" style="background:${colorFor(o)}"></i>${o} <b>${Math.round((counts[i] / gr.length) * 100)}%</b></span>`).join('')));
          wrap.appendChild(col);
        });
      },

      // slope: two periods, one line per category, dots at both ends, labels both sides, colour semantic / neg on decline
      slope(t, node, rows) {
        shell(t, node);
        const c = chartIn(node, 'tall');
        const periods = t.periods || uniq(rows, t.period);
        const cats = uniq(rows, t.category);
        const val = (cat, p) => rows.find((r) => r[t.category] === cat && r[t.period] === p)?.[t.value] ?? 0;
        const vf = (v) => uf(t, v);
        const gut = Math.min(150, Math.round(c.getDom().clientWidth * 0.36));
        c.setOption({
          grid: { left: gut, right: gut, top: 28, bottom: 8, containLabel: false, outerBoundsMode: 'none' },
          tooltip: { trigger: 'item', formatter: (p) => `<b>${p.seriesName}</b><br>${periods[0]} ${vf(val(p.seriesName, periods[0]))} → ${periods[1]} ${vf(val(p.seriesName, periods[1]))}` },
          xAxis: { type: 'category', data: periods, boundaryGap: false, position: 'top', axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: css('--ink'), fontWeight: 600, fontSize: 12.5, margin: 12 } },
          yAxis: { type: 'value', show: false, min: (v) => v.min * 0.8, max: (v) => v.max * 1.08 },
          series: cats.map((cat, i) => {
            const a = val(cat, periods[0]), b = val(cat, periods[1]);
            const col = b < a ? css('--neg') : colorFor(cat, i);
            return { name: cat, type: 'line', data: [a, b], symbol: 'circle', symbolSize: 9, smooth: false,
              lineStyle: { width: b < a ? 2 : 2.4, color: col, type: b < a ? [4, 3] : 'solid' }, itemStyle: { color: col, borderColor: css('--card'), borderWidth: 2 },
              label: { show: true, color: css('--ink'), fontSize: 11.5, formatter: (p) => (gut < 130 ? (p.dataIndex === 0 ? `{n|${cat}}` : `{v|${vf(b)}} {d|${fmt.percent_delta(b / a - 1)}}`) : (p.dataIndex === 0 ? `{n|${cat}}  {v|${vf(a)}}` : `{v|${vf(b)}}  {d|${fmt.percent_delta(b / a - 1)}}`)), position: 'left', distance: 10, rich: { n: { color: css('--ink'), fontWeight: 600 }, v: { color: css('--ink-2') }, d: { color: col, fontWeight: 600 } } },
              labelLayout: (p) => ({ align: p.dataIndex === 0 ? 'right' : 'left', x: p.dataIndex === 0 ? p.rect.x - 10 : p.rect.x + p.rect.width + 10 }),
              emphasis: { focus: 'series', lineStyle: { width: 3.5 } } };
          }),
        });
      },

      small_multiples(t, node, rows) {
        shell(t, node);
        const facets = uniq(rows, t.facet);
        const wrap = el('div', 'av-sm-grid');
        node.appendChild(wrap);
        const all = rows.map((r) => r[t.value]);
        const yMin = Math.min(...all) * 0.9, yMax = Math.max(...all) * 1.05;
        const group = [];
        facets.forEach((fc, i) => {
          const fr = rows.filter((r) => r[t.facet] === fc);
          const first = fr[0][t.value], last = fr[fr.length - 1][t.value];
          const box = el('div', 'av-sm');
          const h = el('div', 'av-sm-head');
          h.append(el('span', 'av-sm-name', fc), el('span', 'av-sm-val', `${uf(t, last)} <small class="${last >= first ? 'av-pos' : 'av-neg'}" style="font-family:var(--font-body);font-size:12px;font-weight:600">${fmt.percent_delta(last / first - 1)}</small>`));
          box.appendChild(h);
          wrap.appendChild(box);
          const c = chartIn(box, 'sm');
          c.setOption({
            grid: { left: 24, right: 24, top: 10, bottom: 0, containLabel: true },
            tooltip: { trigger: 'axis', valueFormatter: (v) => uf(t, v) },
            xAxis: { type: 'category', data: fr.map((r) => r[t.x]), boundaryGap: false, axisLabel: { formatter: xf(fr, t.x), interval: (i) => i === 0 || i === 6 || i === 11, showMinLabel: true, showMaxLabel: true } },
            yAxis: { type: 'value', min: Math.min(yMin, t.reference ? t.reference.value * 0.9 : yMin), max: yMax, axisLabel: { show: false }, splitLine: { show: false } },
            series: [{ type: 'line', data: fr.map((r) => r[t.value]), smooth: 0.3, symbol: 'none', lineStyle: { width: 2, color: colorFor(fc, i) }, areaStyle: { color: colorFor(fc, i) + '22' },
              markLine: t.reference ? { symbol: 'none', silent: true, lineStyle: { color: css('--muted'), type: [3, 4], width: 1 }, label: { show: i === 0, position: 'insideEndTop', color: css('--muted'), fontSize: 10.5, formatter: t.reference.label }, data: [{ yAxis: t.reference.value }] } : undefined,
              markPoint: { symbol: 'circle', symbolSize: 7, itemStyle: { color: colorFor(fc, i), borderColor: css('--card'), borderWidth: 2 }, label: { show: false }, data: [{ coord: [fr.length - 1, last] }] } }],
          });
          group.push(c);
        });
        echarts.connect(group);
      },
    };

    // per-tile drawer: the exact query behind a tile, or its first rows
    let drawer = null;
    function openDrawer(t, mode) {
      if (drawer) drawer.remove();
      drawer = el('aside', 'av-drawer');
      const head = el('div', 'av-drawer-head');
      head.append(el('strong', null, (t.title || t.id) + (mode === 'query' ? ' · query' : ' · data')));
      const close = el('button', 'av-icon-btn', 'Close'); close.onclick = () => { drawer.remove(); drawer = null; };
      head.appendChild(close);
      drawer.appendChild(head);
      const body = el('pre', 'av-drawer-body');
      drawer.appendChild(body);
      // the drawer is fixed to the viewport, so it lives on <body>; it carries the theme so its tokens resolve
      if (themeHost.dataset.theme) drawer.dataset.theme = themeHost.dataset.theme;
      document.body.appendChild(drawer);
      if (mode === 'data') { body.textContent = JSON.stringify(rowsFor(t).slice(0, 50), null, 1); return; }
      if (t.query_text) { body.textContent = t.query_text; return; }
      if (!t.query) { body.textContent = 'No query recorded for this tile.'; return; }
      if (!/\.(sql|py)$/.test(t.query)) { body.textContent = t.query; return; }
      const inlined = global.__AV_QUERIES && global.__AV_QUERIES[t.query]; // frozen share bundle: no files to fetch
      if (inlined) body.textContent = inlined;
      else fetch('./' + t.query).then((r) => (r.ok ? r.text() : 'Query file not found: ' + t.query)).then((txt) => { body.textContent = txt; }).catch(() => { body.textContent = 'Query file not found: ' + t.query; });
    }

    // a re-rendered tile replaces its chart boxes: dispose the instances whose box left the document
    function pruneCharts() {
      for (let i = charts.length - 1; i >= 0; i--) { if (!charts[i].getDom().isConnected) { charts[i].dispose(); charts.splice(i, 1); } }
    }

    function renderTile(id, isUpdate) {
      if (!state.tiles[id]) return;
      const { spec, node } = state.tiles[id];
      state.rendered.add(id);
      const rows = rowsFor(spec);
      if (!rows.length) { shell(spec, node); node.appendChild(el('p', 'av-kpi-label', 'No data for this selection')); pruneCharts(); return; }
      if (isUpdate) { node.style.animation = 'none'; node.offsetHeight; node.style.animation = ''; }
      // one malformed tile must not blank the dashboard: surface it inside its own box
      try { (R[spec.type] || R.table)(spec, node, rows); }
      catch (e) { shell(spec, node); node.appendChild(el('p', 'av-kpi-label', `Tile "${id}" (${spec.type}) could not render: ${e.message}`)); console.error('[abacus-viz] tile', id, e); }
      pruneCharts();
    }
    // every placed tile (lazy hosts render per scene through renderIn instead)
    const placed = () => Object.keys(state.tiles);
    if (!lazy) placed().forEach((id) => renderTile(id, false));

    function rerender() { registerTheme(); paintPage(); charts.forEach((c) => c.dispose()); charts.length = 0; placed().forEach((id) => { if (!lazy || state.rendered.has(id)) renderTile(id, true); }); }
    function setAsOf(iso) { manifest.data_as_of = iso; const n = root.querySelector('.av-asof'); if (n) n.innerHTML = asofText(iso); }
    // live data: replace the rows of the given data keys and re-render only the tiles that read them
    function setData(next) {
      const keys = Object.keys(next || {});
      keys.forEach((k) => { data[k] = next[k]; });
      placed().forEach((id) => { if (keys.includes(state.tiles[id].spec.data) && (!lazy || state.rendered.has(id))) renderTile(id, true); });
    }
    // (re)draw the tiles inside `node` — a story scene being entered — so their charts animate in
    function renderIn(node) { placed().forEach((id) => { if (node === root || node.contains(state.tiles[id].node)) renderTile(id, true); }); }
    function resizeAll() { charts.forEach((c) => c.resize()); }

    // postMessage bridge: host can push fresh rows for a tile ({type:'av:data', tile_id, rows})
    const onMessage = (e) => {
      const msg = e.data || {};
      if (msg.type === 'av:data' && state.tiles[msg.tile_id]) { data[state.tiles[msg.tile_id].spec.data] = msg.rows; if (!lazy || state.rendered.has(msg.tile_id)) renderTile(msg.tile_id, true); }
      if (msg.type === 'av:asof' && msg.data_as_of) setAsOf(msg.data_as_of);
    };
    window.addEventListener('message', onMessage);
    function dispose() { window.removeEventListener('message', onMessage); if (themeWatch) themeWatch.disconnect(); if (drawer) { drawer.remove(); drawer = null; } charts.forEach((c) => c.dispose()); charts.length = 0; if (!slots) root.innerHTML = ''; }

    return { rerender, setData, setAsOf, renderIn, resizeAll, dispose, state };
  }

  global.AbacusViz = { mount, fmt };
})(window);

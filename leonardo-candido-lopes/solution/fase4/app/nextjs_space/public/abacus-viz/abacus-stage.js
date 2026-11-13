/* abacus-stage — story runtime for DeepAgent (scenes on a canvas, a camera, live abacus-viz tiles inside scenes).
   AbacusStage.mount(root, manifest, data, scenes, opts) → { go, next, prev, overview, viz, state, current, dispose }
   manifest: the dashboard.json of a `format: "story"` bundle — `scenes[]` ({id, title, html, frame:{x,y,w,h,scale,rotate}}),
   optional `path[]` (scene order), plus the usual `tiles[]` / `filters[]` / `sources[]` the viz kit renders.
   scenes: {id: innerHTML} — the authored markup of every scene (fetched by index.html, inlined by the share page). */
(function (global) {
  'use strict';

  const DEFAULT_W = 1600, DEFAULT_H = 900;
  const MARGIN = 0.035; // viewport share kept clear around a focused scene
  const STACK_W = 640; // logical scene width in stack mode (narrow portrait viewports)
  const el = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const reduced = () => global.matchMedia && global.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const isInteractive = (node) => !!node.closest('a, button, input, select, textarea, label, [data-goto], [data-tab], figure, .av-tile, .av-tabs, [data-ab="compare"], [data-ab="embed"], .as-scroll');

  function frameOf(s) {
    const f = s.frame || {};
    const w = +f.w || DEFAULT_W, h = +f.h || DEFAULT_H;
    return { x: +f.x || 0, y: +f.y || 0, w, h, scale: +f.scale || 1, rotate: +f.rotate || 0 };
  }

  function mount(root, manifest, data, scenes, opts = {}) {
    const embedded = !!opts.embedded;
    const sceneSpecs = (manifest.scenes || []).filter((s) => s && s.id);
    const path = (Array.isArray(manifest.path) && manifest.path.length ? manifest.path : sceneSpecs.map((s) => s.id)).filter((id) => sceneSpecs.some((s) => s.id === id));
    const byId = Object.fromEntries(sceneSpecs.map((s) => [s.id, s]));

    // ---------- theme (same contract as abacus-viz: html standalone, root embedded, ?theme= wins standalone) ----------
    const themeHost = embedded ? root : document.documentElement;
    const themeOf = (t) => (t === 'light' || t === 'editorial' ? '' : t === 'auto' ? (document.documentElement.classList.contains('dark') ? 'midnight' : '') : t);
    const urlTheme = !embedded && new URLSearchParams(global.location.search).get('theme');
    if (urlTheme) themeHost.dataset.theme = themeOf(urlTheme);
    else if (manifest.theme) themeHost.dataset.theme = themeOf(manifest.theme);

    // ---------- dom ----------
    root.classList.add('as-root', 'av-root');
    if (embedded) root.classList.add('as-embedded');
    root.innerHTML = '';
    const viewport = el('div', 'as-viewport');
    viewport.tabIndex = 0;
    const canvas = el('div', 'as-canvas');
    viewport.appendChild(canvas);
    root.appendChild(viewport);

    // one keypress per step value: every element with the same data-step appears (and hides) together
    function stepGroups(scene) {
      const byStep = new Map();
      scene.querySelectorAll('[data-step]').forEach((s) => { const k = +s.dataset.step || 0; if (!byStep.has(k)) byStep.set(k, []); byStep.get(k).push(s); });
      return [...byStep.entries()].sort((a, b) => a[0] - b[0]).map(([, els]) => els);
    }
    const setShown = (group, shown) => group.forEach((s) => s.classList.toggle('is-shown', shown));
    const isShown = (group) => group[0].classList.contains('is-shown');
    const nodes = {};
    sceneSpecs.forEach((s) => {
      const f = frameOf(s);
      const slot = el('div', 'as-slot');
      slot.style.cssText = `left:${f.x}px;top:${f.y}px;width:${f.w}px;height:${f.h}px;transform:rotate(${f.rotate}deg) scale(${f.scale})`;
      const scene = el('section', 'as-scene' + (s.class ? ' ' + s.class : ''), scenes[s.id] || '');
      scene.id = 'scene-' + s.id;
      scene.dataset.scene = s.id;
      scene.dataset.title = s.title || s.id;
      slot.appendChild(scene);
      canvas.appendChild(slot);
      nodes[s.id] = { spec: s, frame: f, slot, scene, entered: false, steps: stepGroups(scene) };
    });

    // hud
    const hud = el('div', 'as-hud');
    const title = el('div', 'as-hud-title');
    if (manifest.eyebrow) title.appendChild(el('span', 'as-hud-eyebrow', manifest.eyebrow));
    title.appendChild(el('span', 'as-hud-name', manifest.title || ''));
    const count = el('span', 'as-count');
    const prevBtn = el('button', 'as-btn', '←'); prevBtn.title = 'Previous (←)'; prevBtn.onclick = () => prev();
    const nextBtn = el('button', 'as-btn', '→'); nextBtn.title = 'Next (→ / space)'; nextBtn.onclick = () => next();
    const ovBtn = el('button', 'as-btn as-ov', 'Overview'); ovBtn.title = 'Overview (esc)'; ovBtn.onclick = () => (state.current === null ? go(path[0]) : overview());
    hud.append(title, count, prevBtn, nextBtn, ovBtn);
    if (!embedded && document.fullscreenEnabled) {
      const fsBtn = el('button', 'as-btn', 'Present'); fsBtn.title = 'Fullscreen (f)';
      fsBtn.onclick = () => (document.fullscreenElement ? document.exitFullscreen() : root.requestFullscreen());
      hud.appendChild(fsBtn);
    }
    root.appendChild(hud);
    const progress = el('div', 'as-progress', '<i></i>');
    root.appendChild(progress);
    const dots = el('div', 'as-dots');
    path.forEach((id) => { const b = el('button'); b.title = byId[id].title || id; b.onclick = () => go(id); dots.appendChild(b); });
    root.appendChild(dots);
    root.appendChild(el('div', 'as-hint', '← → to move · esc for overview'));

    // lightbox (galleries)
    const lightbox = el('div', 'as-lightbox');
    const lbImg = el('img'); const lbCap = el('figcaption');
    const lbClose = el('button', 'as-btn as-lb-close', 'Close'); const lbPrev = el('button', 'as-btn as-lb-prev', '←'); const lbNext = el('button', 'as-btn as-lb-next', '→');
    lightbox.append(lbImg, lbCap, lbClose, lbPrev, lbNext);
    root.appendChild(lightbox);
    let lb = { figs: [], i: 0 };
    const showLb = (i) => { lb.i = (i + lb.figs.length) % lb.figs.length; const fig = lb.figs[lb.i]; const img = fig.querySelector('img'); lbImg.src = img ? (img.dataset.full || img.src) : ''; lbImg.alt = img ? img.alt : ''; const cap = fig.querySelector('figcaption'); lbCap.textContent = cap ? cap.textContent : (img ? img.alt : ''); lightbox.classList.add('is-open'); };
    const closeLb = () => lightbox.classList.remove('is-open');
    lbClose.onclick = closeLb; lbPrev.onclick = () => showLb(lb.i - 1); lbNext.onclick = () => showLb(lb.i + 1);
    lightbox.onclick = (e) => { if (e.target === lightbox) closeLb(); };

    // ---------- viz tiles inside scenes ----------
    const viz = global.AbacusViz ? global.AbacusViz.mount(canvas, manifest, data, { slots: true, lazy: true, embedded: true, theme: false }) : null;
    canvas.classList.remove('av-root'); // tokens come from the stage root; the canvas must not become a container
    const fmt = global.AbacusViz ? global.AbacusViz.fmt : {};

    // ---------- camera ----------
    // The hud (top) and the dots / progress bar (bottom) overlay the viewport: a focused scene is fitted to the
    // band between them, so the chrome never covers scene content (it did when the scene filled the viewport).
    const state = { current: null, path, stack: false, vw: 0, vh: 0, top: 0, bottom: 0 };
    const size = () => {
      state.vw = viewport.clientWidth || 1; state.vh = viewport.clientHeight || 1;
      state.top = hud.offsetHeight; state.bottom = dots.offsetHeight ? Math.max(0, state.vh - dots.offsetTop) : 0;
    };
    const stageH = () => Math.max(1, state.vh - state.top - state.bottom);
    const sceneFit = (f) => {
      const k = Math.min(state.vw / (f.w * f.scale), stageH() / (f.h * f.scale)) * (1 - 2 * MARGIN);
      return { k, cx: f.x + f.w / 2, cy: f.y + f.h / 2, r: f.rotate };
    };
    const bounds = () => {
      let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
      Object.values(nodes).forEach(({ frame: f }) => {
        // rotated/scaled extent, conservatively: the bounding box of the transformed rectangle
        const rad = (f.rotate * Math.PI) / 180, cw = Math.abs(Math.cos(rad)), sw = Math.abs(Math.sin(rad));
        const hw = ((f.w * cw + f.h * sw) * f.scale) / 2, hh = ((f.w * sw + f.h * cw) * f.scale) / 2;
        const cx = f.x + f.w / 2, cy = f.y + f.h / 2;
        x0 = Math.min(x0, cx - hw); y0 = Math.min(y0, cy - hh); x1 = Math.max(x1, cx + hw); y1 = Math.max(y1, cy + hh);
      });
      if (!isFinite(x0)) return { k: 1, cx: 0, cy: 0, r: 0 };
      const k = Math.min(state.vw / (x1 - x0), stageH() / (y1 - y0)) * 0.88;
      return { k, cx: (x0 + x1) / 2, cy: (y0 + y1) / 2, r: 0 };
    };
    const apply = ({ k, cx, cy, r }, instant) => {
      if (instant || reduced()) { canvas.classList.add('no-transition'); canvas.offsetHeight; }
      canvas.style.transform = `translate(${state.vw / 2}px, ${state.top + stageH() / 2}px) scale(${k}) rotate(${-r}deg) translate(${-cx}px, ${-cy}px)`;
      if (instant || reduced()) { canvas.offsetHeight; canvas.classList.remove('no-transition'); }
    };

    // ---------- scene lifecycle ----------
    function enter(id, backwards) {
      const n = nodes[id];
      if (!n) return;
      n.scene.classList.add('is-active');
      n.steps.forEach((g) => setShown(g, !!backwards));
      if (!n.entered) {
        n.entered = true;
        n.scene.querySelectorAll('[data-ab="embed"][data-src]').forEach((box) => { if (!box.querySelector('iframe')) { const f = el('iframe'); f.src = box.dataset.src; f.loading = 'lazy'; f.allow = 'fullscreen'; box.appendChild(f); } });
      }
      if (viz) viz.renderIn(n.scene);
      n.scene.querySelectorAll('[data-ab="counter"]').forEach((c) => countUp(c));
      n.scene.dispatchEvent(new CustomEvent('as:enter', { bubbles: true, detail: { id } }));
    }
    function leave(id) {
      const n = nodes[id];
      if (!n) return;
      n.scene.classList.remove('is-active');
      n.scene.dispatchEvent(new CustomEvent('as:leave', { bubbles: true, detail: { id } }));
    }
    function countUp(node) {
      const target = parseFloat(node.dataset.value); if (isNaN(target)) return;
      const format = node.dataset.format || 'number';
      const f = fmt[format] || (format === 'decimal' ? (v) => v.toFixed(1) : (v) => Math.round(v).toLocaleString('en-US'));
      const suffix = node.dataset.suffix || '', prefix = node.dataset.prefix || '';
      if (reduced()) { node.textContent = prefix + f(target) + suffix; return; }
      const t0 = performance.now(), ms = +node.dataset.ms || 1100;
      const step = (t) => { const p = Math.min(1, (t - t0) / ms); const e = 1 - Math.pow(1 - p, 3); node.textContent = prefix + f(target * e) + suffix; if (p < 1) requestAnimationFrame(step); };
      requestAnimationFrame(step);
    }

    // ---------- navigation ----------
    function paintChrome() {
      const i = state.current === null ? -1 : path.indexOf(state.current);
      count.textContent = i < 0 ? `${path.length} scenes` : `${i + 1} / ${path.length}`;
      progress.firstChild.style.width = i < 0 ? '0%' : `${((i + 1) / path.length) * 100}%`;
      [...dots.children].forEach((b, j) => b.setAttribute('aria-current', String(j === i)));
      ovBtn.setAttribute('aria-pressed', String(state.current === null));
      ovBtn.textContent = state.current === null ? 'Start' : 'Overview';
      root.classList.toggle('is-overview', state.current === null);
    }
    function setHash(id) {
      if (embedded || opts.hash === false) return;
      const next = id === null ? '#overview' : '#s=' + encodeURIComponent(id);
      if (global.location.hash !== next) { try { history.replaceState(null, '', next); } catch (e) { /* sandboxed */ } }
    }
    function go(id, o = {}) {
      if (!nodes[id]) return;
      const prevId = state.current;
      const backwards = !!o.backwards;
      if (prevId !== null && prevId !== id) leave(prevId);
      state.current = id;
      closeLb();
      if (state.stack) { nodes[id].slot.scrollIntoView({ behavior: o.instant || reduced() ? 'auto' : 'smooth', block: 'start' }); }
      else apply(sceneFit(nodes[id].frame), o.instant);
      if (prevId !== id) enter(id, backwards);
      paintChrome(); setHash(id);
      root.classList.remove('show-hint');
    }
    function overview(o = {}) {
      if (state.stack) return;
      if (state.current !== null) leave(state.current);
      state.current = null;
      closeLb();
      apply(bounds(), o.instant);
      paintChrome(); setHash(null);
    }
    // A step group nobody can see (inside a closed tab panel, display:none) would make a press do nothing: it is
    // marked shown and skipped.
    const rendered = (group) => group.some((s) => s.getClientRects().length > 0);
    function next() {
      if (lightbox.classList.contains('is-open')) return showLb(lb.i + 1);
      if (state.current === null) return go(path[0]);
      const n = nodes[state.current];
      for (const hidden of n.steps.filter((g) => !isShown(g))) {
        setShown(hidden, true);
        if (rendered(hidden)) { if (viz) hidden.forEach((s) => viz.renderIn(s)); return; }
      }
      const i = path.indexOf(state.current);
      if (i < path.length - 1) go(path[i + 1]); else overview();
    }
    function prev() {
      if (lightbox.classList.contains('is-open')) return showLb(lb.i - 1);
      if (state.current === null) return;
      const n = nodes[state.current];
      for (const shown of [...n.steps].reverse().filter(isShown)) {
        setShown(shown, false);
        if (rendered(shown)) return;
      }
      const i = path.indexOf(state.current);
      if (i > 0) go(path[i - 1], { backwards: true }); else overview();
    }

    // ---------- input ----------
    const onKey = (e) => {
      if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.altKey) return;
      const t = e.target; if (t && t.closest && t.closest('input, textarea, select, [contenteditable]')) return;
      if ((e.key === 'Enter' || e.key === ' ') && t && t.closest && t.closest('button, a, [data-goto], [data-tab]')) return; // the browser clicks it
      switch (e.key) {
        case 'ArrowRight': case 'ArrowDown': case 'PageDown': case ' ': case 'Enter': next(); e.preventDefault(); break;
        case 'ArrowLeft': case 'ArrowUp': case 'PageUp': case 'Backspace': prev(); e.preventDefault(); break;
        case 'Escape': if (lightbox.classList.contains('is-open')) closeLb(); else if (state.current === null) go(path[0]); else overview(); e.preventDefault(); break;
        case 'Home': go(path[0]); e.preventDefault(); break;
        case 'End': go(path[path.length - 1]); e.preventDefault(); break;
        case 'f': case 'F': if (!embedded && document.fullscreenEnabled) (document.fullscreenElement ? document.exitFullscreen() : root.requestFullscreen()); break;
        default: break;
      }
    };
    let wheelAcc = 0, wheelLock = 0;
    const onWheel = (e) => {
      if (state.stack) return;
      if (e.target.closest && e.target.closest('.as-scroll, .av-table-wrap, .av-drawer')) return;
      e.preventDefault();
      const now = performance.now();
      if (now < wheelLock) return;
      wheelAcc += e.deltaY;
      if (Math.abs(wheelAcc) > 60) { wheelAcc > 0 ? next() : prev(); wheelAcc = 0; wheelLock = now + 800; }
    };
    let touch = null;
    const onTouchStart = (e) => { touch = e.touches.length === 1 ? { x: e.touches[0].clientX, y: e.touches[0].clientY } : null; };
    const onTouchEnd = (e) => {
      if (!touch || state.stack) return;
      const dx = e.changedTouches[0].clientX - touch.x, dy = e.changedTouches[0].clientY - touch.y; touch = null;
      if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy)) (dx < 0 ? next() : prev());
    };
    const onClick = (e) => {
      const goto = e.target.closest && e.target.closest('[data-goto]');
      if (goto && nodes[goto.dataset.goto]) { e.preventDefault(); e.stopPropagation(); go(goto.dataset.goto); return; }
      const tab = e.target.closest && e.target.closest('[data-ab="tabs"] [data-tab]');
      if (tab) {
        const box = tab.closest('[data-ab="tabs"]');
        box.querySelectorAll('[data-tab]').forEach((b) => b.setAttribute('aria-selected', String(b === tab)));
        box.querySelectorAll('[data-panel]').forEach((p) => p.classList.toggle('is-on', p.dataset.panel === tab.dataset.tab));
        const panel = box.querySelector(`[data-panel="${tab.dataset.tab}"]`);
        if (viz && panel) { viz.renderIn(panel); viz.resizeAll(); }
        return;
      }
      const fig = e.target.closest && e.target.closest('[data-ab="gallery"] figure, .as-gallery figure');
      if (fig && fig.querySelector('img')) { const gal = fig.closest('[data-ab="gallery"], .as-gallery'); lb.figs = [...gal.querySelectorAll('figure')]; showLb(lb.figs.indexOf(fig)); return; }
      const sceneEl = e.target.closest && e.target.closest('.as-scene');
      if (!sceneEl) return;
      const id = sceneEl.dataset.scene;
      if (state.current !== id && !state.stack) { go(id); return; }
      if (state.current === id && !isInteractive(e.target)) next();
    };
    const onHash = () => {
      if (embedded) return;
      const h = global.location.hash || '';
      if (h === '#overview') { if (state.current !== null) overview(); return; }
      const m = /^#s=(.+)$/.exec(h);
      if (m) { const id = decodeURIComponent(m[1]); if (nodes[id] && state.current !== id) go(id); }
    };

    // compare sliders: wire the range input to the clip
    root.querySelectorAll('[data-ab="compare"]').forEach((box) => {
      const after = box.querySelector('img[data-after]'); if (!after) return;
      if (!box.querySelector('.as-cmp-handle')) box.appendChild(el('div', 'as-cmp-handle'));
      if (box.dataset.before) { box.appendChild(el('span', 'as-cmp-label before', box.dataset.before)); }
      if (box.dataset.afterLabel) { box.appendChild(el('span', 'as-cmp-label after', box.dataset.afterLabel)); }
      const range = el('input'); range.type = 'range'; range.min = 0; range.max = 100; range.value = 50; box.appendChild(range);
      range.oninput = () => box.style.setProperty('--cut', range.value + '%');
    });
    // tabs: first panel on unless one is marked
    root.querySelectorAll('[data-ab="tabs"]').forEach((box) => {
      const tabs = [...box.querySelectorAll('[data-tab]')]; if (!tabs.length) return;
      const on = tabs.find((b) => b.getAttribute('aria-selected') === 'true') || tabs[0];
      tabs.forEach((b) => b.setAttribute('aria-selected', String(b === on)));
      box.querySelectorAll('[data-panel]').forEach((p) => p.classList.toggle('is-on', p.dataset.panel === on.dataset.tab));
      if (!box.querySelector('.as-tabs') && tabs[0].parentElement) tabs[0].parentElement.classList.add('as-tabs');
    });
    // galleries: grid columns from the figure count unless set
    root.querySelectorAll('[data-ab="gallery"]').forEach((g) => { g.classList.add('as-gallery'); if (!g.style.getPropertyValue('--cols') && !g.dataset.cols) g.style.setProperty('--cols', String(clamp(g.querySelectorAll('figure').length, 2, 4))); if (g.dataset.cols) g.style.setProperty('--cols', g.dataset.cols); });

    // ---------- layout mode ----------
    function layout(instant) {
      size();
      const stack = !embedded && state.vw < 640 && state.vw < state.vh;
      if (stack !== state.stack) {
        state.stack = stack;
        root.classList.toggle('as-stack', stack);
        if (stack) {
          // every scene becomes a block scaled to the width; all scenes read as active (steps shown, tiles drawn)
          Object.values(nodes).forEach((n) => { n.scene.classList.add('is-active'); n.steps.forEach((g) => setShown(g, true)); if (!n.entered) { n.entered = true; } n.scene.querySelectorAll('[data-ab="counter"]').forEach((c) => countUp(c)); });
          if (viz) viz.renderIn(canvas);
        } else {
          Object.values(nodes).forEach((n) => { if (n.spec.id !== state.current) n.scene.classList.remove('is-active'); });
        }
      }
      if (stack) {
        // each scene reflows at STACK_W logical px (height from its content) and is scaled to the viewport width
        const w = state.vw - 16, k = w / STACK_W;
        Object.values(nodes).forEach((n) => { n.slot.style.width = `${w}px`; n.scene.style.width = `${STACK_W}px`; n.scene.style.height = ''; n.scene.style.transform = `scale(${k})`; });
        fitStack();
        if (state.current === null && path.length) state.current = path[0];
      } else {
        Object.values(nodes).forEach((n) => { n.slot.style.height = `${n.frame.h}px`; n.slot.style.width = `${n.frame.w}px`; n.scene.style.width = ''; n.scene.style.height = ''; n.scene.style.transform = ''; });
        apply(state.current === null ? bounds() : sceneFit(nodes[state.current].frame), instant !== false);
      }
      if (viz) viz.resizeAll();
      paintChrome();
    }

    // stack mode: a slot is as tall as its scaled scene; re-measure when a scene's content (images, charts) changes height
    function fitStack() {
      if (!state.stack) return;
      const k = (state.vw - 16) / STACK_W;
      Object.values(nodes).forEach((n) => { n.slot.style.height = `${Math.ceil(n.scene.offsetHeight * k)}px`; });
    }
    const ro = new ResizeObserver(() => layout(true));
    ro.observe(viewport);
    const sceneRo = new ResizeObserver(() => fitStack());
    Object.values(nodes).forEach((n) => sceneRo.observe(n.scene));
    // Standalone, the story owns the page: keys work wherever focus sits (a hud button just clicked, the body).
    // Embedded, only keys from inside the stage, so a host page keeps its own shortcuts.
    const keyHost = embedded ? root : document;
    keyHost.addEventListener('keydown', onKey);
    viewport.addEventListener('wheel', onWheel, { passive: false });
    viewport.addEventListener('touchstart', onTouchStart, { passive: true });
    viewport.addEventListener('touchend', onTouchEnd, { passive: true });
    viewport.addEventListener('click', onClick);
    global.addEventListener('hashchange', onHash);
    document.addEventListener('fullscreenchange', () => layout(true));

    // ---------- start ----------
    layout(true);
    const startHash = !embedded && /^#s=(.+)$/.exec(global.location.hash || '');
    const startId = startHash && nodes[decodeURIComponent(startHash[1])] ? decodeURIComponent(startHash[1]) : (opts.start && nodes[opts.start] ? opts.start : path[0]);
    if (state.stack) { if (path.length) { state.current = path[0]; paintChrome(); } }
    else if (!embedded && (global.location.hash === '#overview' || opts.start === 'overview')) overview({ instant: true });
    else if (startId) go(startId, { instant: true });
    root.classList.add('show-hint');
    setTimeout(() => root.classList.remove('show-hint'), 4000);
    if (!embedded) viewport.focus({ preventScroll: true });

    function dispose() {
      ro.disconnect(); sceneRo.disconnect();
      global.removeEventListener('hashchange', onHash);
      keyHost.removeEventListener('keydown', onKey);
      if (viz) viz.dispose();
      root.innerHTML = '';
      root.classList.remove('as-root', 'av-root', 'as-embedded', 'is-overview', 'as-stack');
    }

    return { go, next, prev, overview, viz, state, current: () => state.current, dispose, layout: () => layout(true) };
  }

  global.AbacusStage = { mount, frameOf };
})(window);

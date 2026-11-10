"use strict";
/* Segunda-feira: reads only the contract files (out/index.json, out/score-*.json)
   and, when it exists, ai/textos.json. Every number shown comes from those files;
   this script formats and lays out, it never sums or scores. Data is always
   written with textContent, never as HTML.
   The first view carries the conclusion and one line per deal. Everything that
   explains a line opens on hover, on keyboard focus and on a tap, and closes again;
   the notes of method live in one panel, "Como a ferramenta decide". */
(() => {
  const $ = (id) => document.getElementById(id);
  const NBSP = " ";
  const nf = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });
  const num = (v) => nf.format(v);
  const money = (v) => "US$" + NBSP + nf.format(v);
  const brDate = (iso) => iso.split("-").reverse().join("/");
  const pl = (n, one, many) => (n === 1 ? one : many);
  const count = (n, one, many, none) => (n === 0 ? none : `${num(n)} ${pl(n, one, many)}`);
  const SVG = "http://www.w3.org/2000/svg";
  const PLAY = {
    trabalhar: "Trabalhar esta semana.",
    confirmar: "Confirmar esta semana se segue de pé.",
    engajar: "Engajar e registrar a data.",
    encerrar: "Encerrar no CRM e tirar da segunda-feira.",
  };

  function h(tag, attrs, ...kids) {
    const el = tag === "svg" || (attrs && attrs.svg) ? document.createElementNS(SVG, tag) : document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (k === "svg" || v === null || v === undefined || v === false) continue;
      if (k === "class") el.setAttribute("class", v);
      else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
      else if (k === "style") el.style.cssText = v;
      else el.setAttribute(k, v === true ? "" : v);
    }
    for (const kid of kids.flat(Infinity)) {
      if (kid === null || kid === undefined || kid === false) continue;
      el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
    }
    return el;
  }
  const s = (tag, attrs, ...kids) => h(tag, { ...attrs, svg: true }, ...kids);
  const para = (...kids) => h("p", {}, ...kids);

  // --- state -----------------------------------------------------------------
  const query = new URLSearchParams(location.search);
  const state = { view: "vendedor", seller: null, manager: "", region: "", monday: null };
  const shown = {}; // what the user opened, so a re-render keeps it
  let index = null;
  let texts = null;
  let current = null; // the score on the screen, for the "how it decides" panel
  let lineReady = false; // whether the background image of the line of time is there
  const scores = new Map();
  let run = 0; // every render takes a number; a stale one never writes

  function readHash() {
    const p = new URLSearchParams(location.hash.slice(1));
    if (p.get("visao") === "gestor") state.view = "gestor";
    for (const [key, name] of [["seller", "vendedor"], ["manager", "gestor"], ["region", "regiao"], ["monday", "segunda"]]) {
      if (p.has(name)) state[key] = p.get(name);
    }
  }
  function writeHash() {
    const p = new URLSearchParams();
    p.set("visao", state.view);
    if (state.view === "vendedor") p.set("vendedor", state.seller);
    if (state.manager) p.set("gestor", state.manager);
    if (state.region) p.set("regiao", state.region);
    p.set("segunda", state.monday);
    history.replaceState(null, "", location.pathname + location.search + "#" + p.toString());
  }
  async function getJSON(url) {
    const r = await fetch(url);
    if (!r.ok) throw new Error(`${url}: ${r.status}`);
    return r.json();
  }
  async function loadTexts() {
    // The product is whole without this file: any failure just means "no AI text".
    try {
      const r = await fetch("ai/textos.json");
      if (!r.ok) return null;
      const file = await r.json();
      const byId = new Map();
      for (const t of file.texts || []) byId.set(t.id, t);
      return byId.size ? { meta: file.meta || {}, byId } : null;
    } catch (e) {
      return null;
    }
  }
  async function getScore(monday) {
    if (!scores.has(monday)) {
      const entry = index.mondays.find((m) => m.monday === monday);
      scores.set(monday, await getJSON("out/" + entry.file));
    }
    return scores.get(monday);
  }
  const part = (id, name) => {
    const t = texts && texts.byId.get(id);
    return t && t.parts && t.parts[name] && t.parts[name].text ? t.parts[name].text : null;
  };

  // --- the tip: one floating box for every explanation --------------------------
  // Opens on hover and on keyboard focus, toggles on click or tap, closes on leave,
  // blur, Escape, scroll or a tap elsewhere. The anchor points to it while it is open.
  const tip = { el: null, anchor: null, pinned: false };
  function openTip(anchor, build, pin) {
    tip.el.replaceChildren(...[build(),
      pin ? h("button", { type: "button", class: "tp-tip-close", onclick: (e) => { e.stopPropagation(); closeTip(); } }, "Fechar") : null].flat(Infinity).filter(Boolean));
    tip.el.classList.toggle("tp-pinned", !!pin);
    tip.el.hidden = false;
    for (const m of document.querySelectorAll(".tp-m-on")) m.classList.remove("tp-m-on");
    const mark = anchor.id && document.querySelector(`.tp-mark[data-id="${anchor.id.replace("deal-", "")}"]`);
    if (mark) mark.classList.add("tp-m-on");
    if (tip.anchor && tip.anchor !== anchor) releaseTip();
    tip.anchor = anchor;
    tip.pinned = !!pin;
    anchor.setAttribute("aria-describedby", "tip");
    if (anchor.hasAttribute("data-tip-toggle")) anchor.setAttribute("aria-expanded", "true");
    const a = anchor.getBoundingClientRect(), w = Math.min(430, innerWidth - 24);
    tip.el.style.width = w + "px";
    const hgt = tip.el.offsetHeight, head = document.querySelector(".tp-head");
    const inHead = !!anchor.closest(".tp-head, .tp-bar");
    const floor = head && !inHead ? head.getBoundingClientRect().bottom + 4 : 8; // never over the headline
    let left, top;
    if (innerWidth >= 900 && !inHead) { // beside its own line
      left = a.right + 10 + w <= innerWidth - 12 ? a.right + 10 : a.left - 10 - w;
      left = Math.max(12, Math.min(left, innerWidth - w - 12));
      top = Math.max(floor, Math.min(a.top, innerHeight - 8 - hgt));
    } else {
      left = Math.max(12, Math.min(a.left, innerWidth - w - 12));
      top = a.bottom + 8 + hgt <= innerHeight - 8 || a.top - 8 - hgt < floor ? a.bottom + 8 : a.top - 8 - hgt;
    }
    tip.el.style.left = left + "px";
    tip.el.style.top = top + "px";
  }
  function releaseTip() {
    if (!tip.anchor) return;
    tip.anchor.removeAttribute("aria-describedby");
    if (tip.anchor.hasAttribute("data-tip-toggle")) tip.anchor.setAttribute("aria-expanded", "false");
    tip.anchor = null;
  }
  function closeTip() {
    releaseTip();
    tip.pinned = false;
    for (const m of document.querySelectorAll(".tp-m-on")) m.classList.remove("tp-m-on");
    if (tip.el) tip.el.hidden = true;
  }
  // `click: false` leaves the click to the element's own action (copy, open a list)
  function withTip(el, build, opts) {
    const o = opts || {};
    el.addEventListener("mouseenter", () => { if (!tip.pinned) openTip(el, build, false); });
    el.addEventListener("mouseleave", () => { if (!tip.pinned && tip.anchor === el) closeTip(); });
    el.addEventListener("focus", () => { if (!tip.pinned) openTip(el, build, false); });
    el.addEventListener("blur", () => { if (tip.anchor === el) closeTip(); });
    if (o.click !== false) {
      el.setAttribute("data-tip-toggle", "");
      el.setAttribute("aria-expanded", "false");
      el.addEventListener("click", (e) => {
        e.stopPropagation();
        if (tip.anchor === el && tip.pinned) closeTip(); else openTip(el, build, true);
      });
    }
    return el;
  }

  // --- filters ---------------------------------------------------------------
  function fillSelect(sel, options, value) {
    sel.replaceChildren(...options.map(([v, label]) => h("option", { value: v, selected: v === value }, label)));
    sel.value = value;
  }
  function syncFilters() {
    const manager = state.view === "gestor";
    const regions = [...new Set(index.sellers.map((x) => x.region))].sort();
    if (state.region && !regions.includes(state.region)) state.region = "";
    const inRegion = index.sellers.filter((x) => !state.region || x.region === state.region);
    const managers = [...new Set(inRegion.map((x) => x.manager))].sort();
    if (state.manager && !managers.includes(state.manager)) state.manager = "";
    if (!index.sellers.some((x) => x.seller === state.seller)) state.seller = index.default_seller;
    fillSelect($("f-region"), [["", "Todas"], ...regions.map((r) => [r, r])], state.region);
    fillSelect($("f-manager"), [["", "Todos"], ...managers.map((m) => [m, m])], state.manager);
    fillSelect($("f-seller"), index.sellers.map((x) => [x.seller, x.seller]), state.seller);
    fillSelect($("f-monday"), index.mondays.map((m) => [m.monday, "segunda " + brDate(m.monday) + (m.past ? " (passado)" : "")]), state.monday);
    $("l-seller").hidden = manager;
    for (const el of document.querySelectorAll(".tp-team-filter")) el.hidden = !manager;
    $("view-seller").setAttribute("aria-pressed", String(!manager));
    $("view-manager").setAttribute("aria-pressed", String(manager));
  }

  // --- what a deal says when asked ------------------------------------------------
  function afterText(d) {
    const a = d.after;
    if (!a) return null;
    if (a.result === "ganho") return `Depois: ganho em ${brDate(a.close_date)}, ${money(a.close_value)} (${num(a.days_after)} ${pl(a.days_after, "dia", "dias")} depois).`;
    if (a.result === "perdido") return `Depois: perdido em ${brDate(a.close_date)} (${num(a.days_after)} ${pl(a.days_after, "dia", "dias")} depois).`;
    return "Depois: seguia aberto no fim dos dados.";
  }
  function dealTip(d, table) {
    const reason = part("deal:" + d.id, "reason");
    const step = part("deal:" + d.id, "next_step");
    const left = d.days_left === 0 ? "último dia do prazo" : `${num(d.days_left)} ${pl(d.days_left, "dia restante", "dias restantes")} no prazo`;
    return [
      h("p", { class: "tp-tip-h" }, d.product, d.account ? " · " + d.account : " · sem conta registrada"),
      para(h("b", {}, "Próximo passo: "), step || PLAY[d.play]),
      para(`Aberto há ${num(d.days_open)} ${pl(d.days_open, "dia", "dias")}; ${left}, até ${brDate(d.window_end)}.` + (d.cooling ? " Prazo acabando: aberto há mais de 90 dias." : "")),
      reason && !reason.includes(d.time_sentence) ? para(reason) : null,
      para(d.time_sentence, table.exists ? " Vale para todos os negócios que chegaram a essa idade; não é a chance deste negócio." : ""),
      para(`${money(d.value)} é o valor de tabela: o preço de lista do produto, porque negócio aberto não tem valor de fechamento.`),
      d.after ? para(afterText(d)) : null,
      h("p", { class: "tp-tip-id" }, "ID " + d.id + (step ? " · frase do próximo passo redigida por IA" : "")),
    ];
  }

  // --- the window: one line of time ------------------------------------------------
  // On the left a deal that has just opened, on the right the end of the window; one
  // mark for each living deal, at its age. No vertical axis, no rate, no column. The
  // body of the line is a static image; marks and words are live.
  const LINE = { x0: 0.05, x1: 0.80, y: 0.62, half: 0.085 }; // the same fractions as the background image
  const isDark = () => document.documentElement.hasAttribute("data-tema");
  function drawLine(svg, score, seller, animate) {
    const W = Math.max(280, Math.floor(svg.parentNode.getBoundingClientRect().width));
    const narrow = W < 700, longest = score.meta.window.longest_win_days, cool = score.meta.cooling_after_days;
    const H = narrow ? 104 : 136, x0 = LINE.x0 * W, x1 = (narrow ? 0.95 : LINE.x1) * W, y = LINE.y * H, half = LINE.half * H;
    const X = (age) => x0 + (Math.min(age, longest) / longest) * (x1 - x0);
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.setAttribute("width", W);
    svg.setAttribute("height", H);
    svg.classList.toggle("tp-still", !animate);
    const cooling = seller.alive.filter((d) => d.cooling).length;
    svg.setAttribute("aria-label",
      `O prazo, de ${num(0)} a ${longest} dias de aberto: ${count(seller.alive.length, "negócio no prazo", "negócios no prazo", "nenhum negócio no prazo")}, ` +
      `${count(cooling, "com prazo acabando", "com prazo acabando", "nenhum com prazo acabando")} (depois de ${cool} dias). A lista "No prazo" traz os mesmos negócios.`);
    const kids = [];
    if (!narrow && lineReady) {
      kids.push(s("image", { href: `img/janela-${isDark() ? "escuro" : "claro"}.webp`, x: 0, y: 0, width: W, height: H, preserveAspectRatio: "none", "aria-hidden": "true" }));
    } else { // the same line, flat, drawn here (phone, or the picture is missing)
      kids.push(s("rect", { class: "tp-l-rail", x: x0, y: y - half, width: x1 - x0, height: 2 * half, rx: half }));
      kids.push(s("rect", { class: "tp-l-cool", x: X(cool), y: y - half, width: x1 - X(cool), height: 2 * half, rx: half }));
      kids.push(s("line", { class: "tp-l-end", x1: x1, y1: y - half - 8, x2: x1, y2: y + half + 8 }));
    }
    kids.push(s("text", { x: (X(cool) + x1) / 2, y: y + 4.5, "font-size": 13, "text-anchor": "middle", class: "tp-l-word" }, "prazo acabando"));
    kids.push(s("text", { x: x0, y: y + half + 19, "font-size": 12.5, "data-dado": "" }, narrow ? "0" : "abriu agora"));
    kids.push(s("text", { x: X(cool), y: y + half + 19, "font-size": 12.5, "text-anchor": "middle", "data-dado": "" }, String(cool)));
    kids.push(s("text", { x: x1, y: y + half + 19, "font-size": 12.5, "text-anchor": "end", "data-dado": "" }, narrow ? `${longest} dias` : `fim do prazo: ${longest} dias`));
    kids.push(s("text", { x: x0, y: 14, "font-size": 12.5 }, "ponto = negócio no prazo"));
    const deals = [...seller.alive].sort((a, b) => a.days_open - b.days_open || (a.id < b.id ? -1 : 1));
    // the largest marks that still let every deal sit on the track
    const levelsFor = (rr) => { const lv = []; for (const d of deals) { const cx = X(d.days_open); let k = 0; while (lv[k] !== undefined && cx - lv[k] < 2 * rr + 2) k += 1; lv[k] = cx; } return lv.length; };
    const room = (rr) => Math.max(1, Math.floor((y - half - 18) / (2 * rr + 2)));
    const r = [narrow ? 6 : 8, 6, 5, 4, 3].find((rr) => levelsFor(rr) <= room(rr)) || 3, step = 2 * r + 2, maxLevels = room(r);
    const levels = [];
    deals.forEach((d, i) => {
      const cx = X(d.days_open);
      let level = 0;
      while (levels[level] !== undefined && cx - levels[level] < 2 * r + 2) level += 1;
      levels[level] = cx;
      if (level >= maxLevels) return; // a very long list: the marks that do not fit stay in the list only
      const cy = y - half - 3 - r - level * step;
      const shape = d.cooling
        ? s("path", { d: `M${cx} ${cy - r - 1}L${cx + r + 1} ${cy}L${cx} ${cy + r + 1}L${cx - r - 1} ${cy}Z`, class: "tp-mark tp-m-frio" })
        : s("circle", { cx, cy, r, class: "tp-mark tp-m-vivo" });
      shape.style.setProperty("--i", Math.min(i, 30));
      shape.setAttribute("data-id", d.id);
      shape.addEventListener("mouseenter", () => { if (!tip.pinned) openTip(shape, () => dealTip(d, score.meta.time_table), false); });
      shape.addEventListener("mouseleave", () => { if (!tip.pinned && tip.anchor === shape) closeTip(); });
      shape.addEventListener("click", (e) => { e.stopPropagation(); focusDeal(d.id); });
      kids.push(shape);
    });
    if (!deals.length) kids.push(s("text", { class: "tp-r-strong", x: x0, y: y - half - 12, "font-size": 13 }, "Nenhum negócio no prazo."));
    svg.replaceChildren(...kids);
  }
  function focusDeal(id) {
    const row = $("deal-" + id);
    if (!row) return;
    closeTip();
    row.scrollIntoView({ block: "nearest", behavior: "auto" });
    row.focus();
  }
  function windowSection(score, seller, animate) {
    const svg = s("svg", { class: "tp-ruler", role: "img" });
    const n = seller.headline.clean;
    // after the end of the window there is no bar and no block: one line of text that leads to the list
    const out = h("button", { type: "button", class: "tp-out", id: "out-link" }, n ? `${num(n)} ${pl(n, "vencido", "vencidos")}` : "nenhum vencido");
    out.addEventListener("click", () => { const t = document.querySelector(".tp-limpar .tp-title"); if (t) { t.scrollIntoView({ block: "nearest" }); t.focus(); } });
    const section = h("section", { class: "tp-window", "aria-label": "O prazo" }, svg, out);
    let lastW = 0;
    const draw = (anim) => {
      const wNow = Math.floor(section.getBoundingClientRect().width);
      if (wNow === lastW || wNow === 0) return;
      lastW = wNow;
      drawLine(svg, score, seller, anim);
    };
    requestAnimationFrame(() => draw(animate));
    new ResizeObserver(() => draw(false)).observe(section);
    return section;
  }

  // --- seller ----------------------------------------------------------------
  function sellerHeadline(sel, past) {
    const hd = sel.headline;
    const first = sel.seller.split(" ")[0];
    if (!hd.alive && !hd.queue && !hd.clean) {
      return [past ? `Naquela segunda o pipeline de ${first} estava limpo: nenhum negócio no prazo e nenhum vencido.`
        : `${first}, seu pipeline está limpo: nenhum negócio no prazo, nenhum para iniciar e nenhum vencido.`];
    }
    // the punctuation rides inside the coloured chunk so a line never starts with a comma
    const alive = (tail) => h("span", { class: "tp-k-vivo" }, count(hd.alive, "negócio no prazo", "negócios no prazo", "nenhum negócio no prazo"), h("i", {}, tail));
    const clean = h("span", { class: "tp-k-limpar" }, hd.clean ? `${num(hd.clean)} ${pl(hd.clean, "vencido", "vencidos")}` : "nenhum vencido", h("i", {}, "."));
    if (past) return [`Naquela segunda, ${first} tinha `, alive(""), " e ", clean];
    const queue = h("span", { class: "tp-k-fila" }, hd.queue ? `${num(hd.queue)} para iniciar` : "nenhum para iniciar");
    return hd.alive ? [`${first}, você tem `, alive(","), " ", queue, " e ", clean] : [`${first}: `, alive(","), " ", queue, " e ", clean];
  }
  // only what the headline does not already say: three numbers, the unit said once
  function kpis(hd) {
    const cell = (cls, label, value) => h("div", { class: "tp-kpi " + cls }, h("dt", {}, label), h("dd", {}, h("b", {}, value)));
    return h("dl", { class: "tp-kpis", "data-dado": "" },
      cell("tp-kv", "Dentro do prazo", num(hd.alive_value)),
      cell("tp-kf", "Prazo acabando", num(hd.cooling)),
      cell("tp-kl", "Vencido", num(hd.clean_value)),
      h("div", { class: "tp-kpi-unit" }, h("dt", { class: "tp-sr" }, "Unidade"), h("dd", {}, "valores em US$ de tabela; prazo acabando em negócios")));
  }
  function briefButton(sel) {
    const body = part("briefing:" + sel.seller, "body");
    if (!body) return null;
    const t = texts.byId.get("briefing:" + sel.seller), p = t.provenance || {};
    const btn = h("button", { type: "button", class: "tp-btn", id: "brief" }, "Copiar resumo");
    btn.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(body); btn.textContent = "Resumo copiado"; } catch (e) { btn.textContent = "Não copiou: leia abaixo"; }
      openTip(btn, build, true);
    });
    const build = () => [h("p", { class: "tp-tip-h" }, "Resumo da segunda"), para(body),
      h("p", { class: "tp-tip-id" }, `Redigido por IA${p.model ? " (" + p.model + ")" : ""}; números e nomes preenchidos pelo código.`)];
    return withTip(btn, build, { click: false });
  }
  function aliveRow(d, table, past) {
    const result = d.after ? { ganho: "ganho", perdido: "perdido", aberto: "aberto" }[d.after.result] : null;
    const row = h("button", { type: "button", class: "tp-row tp-alive" + (past ? " tp-has-after" : ""), id: "deal-" + d.id },
      h("span", { class: "tp-name" }, h("span", { class: "tp-prod" }, d.product), d.account ? h("span", { class: "tp-acct" }, d.account) : null,
        d.cooling ? h("span", { class: "tp-tag" }, "prazo acabando") : null),
      h("span", { class: "tp-num tp-c-val" }, num(d.value)),
      h("span", { class: "tp-c-days" }, h("span", { class: "tp-num" }, d.days_left === 0 ? "último" : num(d.days_left)),
        h("span", { class: "tp-left" + (d.cooling ? " tp-left-frio" : ""), "aria-hidden": "true" }, h("i", { style: `width:${Math.max(4, (d.days_left / 138) * 100).toFixed(1)}%` }))),
      result ? h("span", { class: "tp-c-after tp-" + d.after.result }, result) : null);
    return h("li", {}, withTip(row, () => dealTip(d, table)));
  }
  function slimRow(d, window) {
    const fact = d.block !== "limpar" ? ""
      : `aberto há ${num(d.days_open)} dias · ` + (d.clean_fact === "idade" ? `passou dos ${window.longest_win_days} dias` : `prazo venceu em ${brDate(d.deadline)}`);
    return h("li", { class: "tp-slim", id: "deal-" + d.id },
      h("span", { class: d.account ? "tp-acct" : "tp-acct tp-none" }, d.account || "sem conta"),
      h("span", { class: "tp-id" }, "ID " + d.id),
      fact ? h("span", { class: "tp-fact" }, fact + (d.after ? " · " + afterText(d).toLowerCase() : "")) : null);
  }
  // The queue and the clean list repeat a product many times: one line per product
  // (there are only seven list prices), each opening its own deals.
  function grouped(key, items, window) {
    const groups = [];
    for (const d of items) {
      const last = groups[groups.length - 1];
      if (last && last.product === d.product) last.items.push(d); else groups.push({ product: d.product, value: d.value, items: [d] });
    }
    return h("ul", { class: "tp-list tp-groups" }, groups.map((g) => {
      const n = g.items.length, k = `${key}:${g.product}`;
      const list = h("ol", { class: "tp-sub", id: `${key}-${g.product.replace(/\W+/g, "-")}`, hidden: !shown[k] }, g.items.map((d) => slimRow(d, window)));
      const btn = h("button", { type: "button", class: "tp-row tp-group", "aria-expanded": String(!!shown[k]), "aria-controls": list.id },
        h("span", { class: "tp-name" }, h("span", { class: "tp-prod" }, g.product), h("span", { class: "tp-acct" }, `× ${num(n)}`)),
        h("span", { class: "tp-num tp-c-val" }, num(g.value * n)));
      btn.addEventListener("click", () => { shown[k] = !shown[k]; list.hidden = !shown[k]; btn.setAttribute("aria-expanded", String(!!shown[k])); });
      withTip(btn, () => [para(`${num(n)} ${pl(n, "negócio", "negócios")} de ${g.product}: ${money(g.value)} cada, valor de tabela. Clique para ${pl(n, "ver o negócio", "ver os negócios")}.`)], { click: false });
      return h("li", {}, btn, list);
    }));
  }
  // the title of each block says what the block is, when asked
  function panel(cls, label, n, sum, kids, def) {
    const title = h("button", { type: "button", class: "tp-title" }, label, n === null ? null : h("span", { class: "tp-n" }, n));
    const hint = { "tp-fila": "sem data" }[cls];
    if (def) withTip(title, () => [h("p", { class: "tp-tip-h" }, label), para(def)]);
    return h("section", { class: "tp-panel " + cls, "aria-label": label },
      h("header", { class: "tp-panel-head" }, h("h2", {}, title), h("p", { class: "tp-sum" }, sum || hint)),
      kids);
  }
  function renderSeller(score, animate) {
    const meta = score.meta, past = meta.past;
    const sel = score.sellers.find((x) => x.seller === state.seller);
    const hd = sel.headline, ev = index.evidence, a = sel.after;
    const cols = (third) => h("p", { class: "tp-cols" + (past ? " tp-has-after" : ""), "aria-hidden": "true" },
      h("span", {}, "Negócio"), h("span", {}, "Preço, US$"), third ? h("span", {}, third) : null, past && third ? h("span", {}, "Depois") : null);
    const alive = panel("tp-vivos", "No prazo", num(hd.alive),
      hd.alive && past ? `depois: ${num(a.alive_won)} ${pl(a.alive_won, "ganho", "ganhos")} · ${num(a.alive_lost)} ${pl(a.alive_lost, "perdido", "perdidos")} · ${num(a.alive_open)} ${pl(a.alive_open, "aberto", "abertos")}` : null,
      hd.alive
        ? [cols("Dias restantes"), h("ol", { class: "tp-list" }, sel.alive.map((d) => aliveRow(d, meta.time_table, past)))]
        : h("p", { class: "tp-empty" }, past ? "Nenhum negócio no prazo naquela data." : hd.queue ? "Nenhum no prazo: comece pelos negócios para iniciar." : "Nenhum negócio no prazo."),
      `Negócios dentro do prazo em que negócios já foram ganhos: abertos há no máximo ${meta.window.longest_win_days} dias e antes do fim do trimestre seguinte ao do engajamento. A ordem é por valor de tabela; no empate, mais dias restantes.`);
    const queue = past
      ? panel("tp-fila", "Para iniciar", null, null, h("p", { class: "tp-empty" }, "Não dá para reconstruir esta lista no passado."),
        "O CRM não guarda a data em que um negócio entrou; por isso a lista para iniciar não existe numa segunda do passado.")
      : panel("tp-fila", "Para iniciar", num(hd.queue), null,
        hd.queue ? [cols(null), grouped("fila", sel.queue, meta.window)] : h("p", { class: "tp-empty" }, "Nenhum negócio para iniciar."),
        "Negócios ainda sem data de início: o próximo trabalho é iniciar e registrar a data. É só uma lista por valor de tabela; nada mais nos dados ordena esses negócios.");
    const cleanList = hd.clean ? h("div", { id: "clean-list", hidden: !shown.clean }, cols(null), grouped("limpar", sel.clean, meta.window)) : null;
    const cleanBtn = hd.clean ? h("button", { type: "button", class: "tp-btn", "aria-expanded": String(!!shown.clean), "aria-controls": "clean-list" }, shown.clean ? "Ocultar lista" : "Ver lista") : null;
    if (cleanBtn) cleanBtn.addEventListener("click", () => { shown.clean = !shown.clean; cleanList.hidden = !shown.clean; cleanBtn.textContent = shown.clean ? "Ocultar lista" : "Ver lista"; cleanBtn.setAttribute("aria-expanded", String(!!shown.clean)); });
    const clean = panel("tp-limpar", "Vencidos", num(hd.clean),
      hd.clean && past ? `depois: ${count(a.clean_won, "ganho", "ganhos", "nenhum ganho")}` : null,
      hd.clean ? [
        h("p", { class: "tp-evidence" }, `${count(ev.won_after, "ganho", "ganhos", "Nenhum ganho")} em ${num(ev.distinct_deals_past_window)} casos assim.`),
        h("p", { class: "tp-action" }, h("b", {}, "Ação: "), "encerrar no CRM."), cleanBtn, cleanList,
      ] : h("p", { class: "tp-empty" }, "Nenhum vencido."),
      "Negócios que passaram do prazo. Por que estão vencidos: em “Como a ferramenta decide”.");
    const brief = past ? null : briefButton(sel);
    return [
      h("div", { class: "tp-head" },
        h("h1", { class: "tp-headline" }, sellerHeadline(sel, past)),
        h("div", { class: "tp-head-side" },
          past ? h("p", { class: "tp-past" }, "Segunda do passado: cada linha mostra o que veio depois.") : null, brief)),
      kpis(hd),
      windowSection(score, sel, animate),
      h("div", { class: "tp-blocks" + (hd.alive ? "" : " tp-no-alive") + (hd.queue ? "" : " tp-no-queue") }, alive, queue, clean),
    ];
  }

  // --- manager ---------------------------------------------------------------
  function renderManager(score) {
    const meta = score.meta, team = score.team, past = meta.past;
    const scope = state.manager ? team.by_manager.find((m) => m.manager === state.manager)
      : state.region ? team.by_region.find((g) => g.region === state.region) : team.total;
    const label = state.manager ? `O time de ${state.manager}` : state.region ? `A regional ${state.region}` : "O time";
    const rows = team.by_seller.filter((x) => (!state.region || x.region === state.region) && (!state.manager || x.manager === state.manager));
    const headline = [`${label} tem `,
      h("span", { class: "tp-k-vivo" }, count(scope.alive, "negócio no prazo", "negócios no prazo", "nenhum negócio no prazo"), h("i", {}, past ? "" : ",")),
      past ? " e " : [" ", h("span", { class: "tp-k-fila" }, scope.queue ? `${num(scope.queue)} para iniciar` : "nenhum para iniciar"), " e "],
      h("span", { class: "tp-k-limpar" }, scope.clean ? `${num(scope.clean)} ${pl(scope.clean, "vencido", "vencidos")}` : "nenhum vencido", h("i", {}, "."))];
    const body = state.manager && !past ? part("manager:" + state.manager, "body") : null;
    let brief = null;
    if (body) {
      const p = (texts.byId.get("manager:" + state.manager).provenance || {});
      brief = withTip(h("button", { type: "button", class: "tp-btn", id: "brief" }, "Resumo do gestor"),
        () => [h("p", { class: "tp-tip-h" }, "Resumo do gestor"), para(body),
          h("p", { class: "tp-tip-id" }, `Redigido por IA${p.model ? " (" + p.model + ")" : ""}; números e nomes preenchidos pelo código.`)]);
    }
    const facts = (x) => [para(`${count(x.alive, "negócio no prazo", "negócios no prazo", "Nenhum negócio no prazo")}: ${money(x.alive_value)} de tabela` + (x.cooling ? `, ${num(x.cooling)} com prazo acabando.` : ".")),
      para(`${num(x.clean)} ${pl(x.clean, "vencido", "vencidos")}: ${money(x.clean_value)} de tabela.`),
      past ? null : para(x.queue ? `${num(x.queue)} para iniciar: ${money(x.queue_value)} de tabela.` : "Nenhum negócio para iniciar."),
      x.sellers > 1 ? para(`${num(x.sellers_without_alive)} de ${num(x.sellers)} vendedores sem nenhum negócio no prazo.`) : null];
    const open = (x) => x.alive + (past ? 0 : x.queue) + x.clean;
    const scale = Math.max(1, ...rows.map(open));
    const seg = (cls, n) => (n ? h("i", { class: cls, style: `width:${((n / scale) * 100).toFixed(2)}%` }) : null);
    const sellerRow = (x) => {
      const btn = h("button", { type: "button", class: "tp-who", onclick: () => { state.view = "vendedor"; state.seller = x.seller; render(true); } }, x.seller);
      withTip(btn, () => [h("p", { class: "tp-tip-h" }, x.seller), ...facts(x), h("p", { class: "tp-tip-id" }, "Clique para abrir a segunda-feira deste vendedor.")], { click: false });
      return h("li", { class: "tp-trow" }, btn,
        h("span", { class: "tp-three", "aria-hidden": "true" }, seg("tp-3v", x.alive), seg("tp-3q", past ? 0 : x.queue), seg("tp-3l", x.clean)),
        h("span", { class: "tp-num tp-t-n" }, num(x.alive)), h("span", { class: "tp-num tp-t-n" }, past ? "–" : num(x.queue)), h("span", { class: "tp-num tp-t-n" }, num(x.clean)));
    };
    const managers = team.by_manager.filter((m) => (!state.region || m.region === state.region) && (!state.manager || m.manager === state.manager));
    const group = (m) => {
      const mine = rows.filter((x) => x.manager === m.manager);
      const withDeals = mine.filter((x) => open(x) > 0).sort((p, q) => q.alive - p.alive || open(q) - open(p) || (p.seller < q.seller ? -1 : 1));
      const none = mine.filter((x) => open(x) === 0).map((x) => x.seller).sort();
      return h("div", { class: "tp-mgr" }, h("h2", { class: "tp-mgr-h" }, `${m.manager} · ${m.region}`),
        h("ol", {}, withDeals.map(sellerRow)),
        none.length ? h("p", { class: "tp-none-open" }, `Sem negócios abertos: ${none.join(", ")}.`) : null);
    };
    const regions = state.manager ? [] : team.by_region.filter((g) => !state.region || g.region === state.region);
    return [
      h("div", { class: "tp-head" }, h("h1", { class: "tp-headline" }, headline),
        h("div", { class: "tp-head-side" },
          past ? h("p", { class: "tp-past" }, "Segunda do passado: a lista para iniciar não existe nessa data.") : null,
          h("p", { class: "tp-lead" }, `${num(scope.sellers_without_alive)} de ${num(scope.sellers)} sem nenhum no prazo.`), brief)),
      regions.length ? h("section", { class: "tp-regions", "aria-label": "Por regional" }, regions.map((g) => {
        const b = h("button", { type: "button", class: "tp-region" }, h("b", {}, g.region),
          ` ${count(g.alive, "no prazo", "no prazo", "nenhum no prazo")}` + (past ? "" : ` · ${num(g.queue)} para iniciar`) + ` · ${num(g.clean)} ${pl(g.clean, "vencido", "vencidos")}`);
        return withTip(b, () => [h("p", { class: "tp-tip-h" }, "Regional " + g.region), ...facts(g)]);
      })) : null,
      h("section", { class: "tp-panel tp-team", "aria-label": "Por vendedor" },
        h("p", { class: "tp-cols tp-tcols", "aria-hidden": "true" }, h("span", {}, "Vendedor"),
          h("span", { class: "tp-key" }, "Negócios abertos: ", h("i", { class: "tp-3v" }), "no prazo ", h("i", { class: "tp-3q" }), "para iniciar ", h("i", { class: "tp-3l" }), "vencidos"),
          h("span", {}, "No prazo"), h("span", {}, "Iniciar"), h("span", {}, "Vencidos")),
        h("div", { class: "tp-list" }, managers.map(group))),
    ];
  }

  // --- "Como a ferramenta decide": every note of method, one action away ---------
  function fillHow() {
    const dlg = $("how");
    if (!current) return;
    const m = current.meta, w = m.window, t = m.time_table, ev = index.evidence;
    const any = texts && [...texts.byId.values()][0];
    const prov = any ? any.provenance || {} : null;
    const close = h("button", { type: "button", class: "tp-btn", onclick: () => dlg.close() }, "Fechar");
    dlg.replaceChildren(...[
      h("div", { class: "tp-how-head" }, h("h2", { id: "how-h" }, "Como a ferramenta decide"), close),
      h("h3", {}, "No prazo ou vencido"),
      para(`No prazo é o negócio dentro do prazo em que negócios já foram ganhos: aberto há no máximo ${w.longest_win_days} dias e antes do fim do trimestre seguinte ao do engajamento. Passou de um dos dois, está vencido.`),
      para(`Nenhum negócio foi ganho depois de ${w.longest_win_days} dias aberto. Dos ${num(w.closings_known)} fechamentos conhecidos, ${num(w.closings_after_deadline)} ${pl(w.closings_after_deadline, "ocorreu", "ocorreram")} depois do prazo do trimestre.`),
      para(`No teste, em ${num(ev.cuts)} datas: ${num(ev.distinct_deals_past_window)} negócios distintos venceram; ${num(ev.won_after)} ${pl(ev.won_after, "foi ganho", "foram ganhos")} depois, ${num(ev.lost_after)} ${pl(ev.lost_after, "perdido", "perdidos")} e ${num(ev.still_open_at_data_end)} seguiam abertos. As datas se sobrepõem no tempo: não é um teste independente.`),
      para("A ação nos vencidos é encerrar no CRM e tirar da segunda-feira. Os dados não dizem por que esses negócios pararam."),
      h("h3", {}, "A ordem dos negócios no prazo"),
      para(`Valor de tabela, do maior para o menor; no empate, mais dias restantes primeiro. Com ${index.value_note.list_prices} preços de tabela é quase ordem por produto, e ela não foi confirmada em datas novas.`),
      para("Os dias restantes e a marca “prazo acabando” (aberto há mais de " + m.cooling_after_days + " dias) informam, mas não mudam a ordem. Nada na tela diz que um negócio no prazo fecha mais que outro."),
      h("h3", {}, "Valor"),
      para("É o valor de tabela: o preço de lista do produto. Negócio aberto ainda não tem valor de fechamento."),
      h("h3", {}, "A conta por idade"),
      t.exists
        ? [para(`De cada 100 negócios que chegaram abertos a cada idade, cerca de quantos foram ganhos depois. Conta de ${brDate(t.counted_on)}, com os ${num(t.deals)} negócios que já tinham tido tempo de fechar. Vale para a faixa de idade, não para um negócio.`),
          h("ol", { class: "tp-table" }, t.rows.map((row) => h("li", {},
            h("span", {}, row.reached_days === 0 ? "Engajados (0 dias)" : `Abertos aos ${row.reached_days} dias`),
            h("span", {}, `cerca de ${row.won_per_100} em cada 100 ganhos depois`))))]
        : para("Sem histórico suficiente nesta data: nenhum negócio tinha tido tempo de fechar."),
      h("h3", {}, "Para iniciar"),
      para("São os negócios ainda sem data de início. É só uma lista por valor de tabela: nada mais nos dados ordena esses negócios. Numa segunda do passado essa lista não pode ser reconstruída, porque o CRM não guarda a data em que um negócio entrou."),
      h("h3", {}, "Os textos"),
      para(prov
        ? `O próximo passo de cada negócio é escolhido por regra. A frase que o acompanha, o resumo da segunda e o resumo do gestor foram redigidos por IA (${prov.model || "modelo não registrado"}, em ${prov.generated_on || "data não registrada"}); os números e os nomes são preenchidos pelo código.`
        : "O próximo passo de cada negócio é escolhido por regra. Os textos de IA não estão carregados: a tela mostra só as frases de regra."),
      h("h3", {}, "Os dados"),
      para(`Segunda-feira ${brDate(m.monday)}, com os dados fechados no domingo ${brDate(m.data_closed)}. As idades são contadas nessa data, e o último dia do prazo ainda conta como no prazo.` +
        (m.past ? ` É uma segunda do passado: a tela usa só o que se sabia naquele dia, e “depois” vai até ${brDate(m.outcomes_until)}.` : "")),
    ].flat(Infinity));
  }

  // --- render ----------------------------------------------------------------
  async function render(animate) {
    const tok = ++run;
    closeTip();
    syncFilters();
    writeHash();
    const score = await getScore(state.monday);
    if (tok !== run) return; // a newer action took over: write nothing
    current = score;
    document.body.classList.toggle("tp-view-gestor", state.view === "gestor");
    $("app").replaceChildren(...(state.view === "gestor" ? renderManager(score) : renderSeller(score, !!animate)).flat(Infinity).filter(Boolean));
    const t = score.meta.time_table;
    $("foot-note").textContent = `Valor = preço de tabela · dados até ${brDate(score.meta.data_closed)}` +
      (t.exists ? "" : " · sem histórico suficiente nesta data");
    document.title = (state.view === "gestor" ? "Gestor" : state.seller) + " · Segunda-feira";
  }

  function setTheme(dark, keep) {
    document.documentElement.toggleAttribute("data-tema", false);
    if (dark) document.documentElement.setAttribute("data-tema", "escuro");
    document.querySelector('meta[name="color-scheme"]').setAttribute("content", dark ? "only dark" : "only light");
    $("theme").setAttribute("aria-pressed", String(dark));
    $("theme").textContent = dark ? "Claro" : "Escuro";
    if (keep) { try { localStorage.setItem("tp-tema", dark ? "escuro" : "claro"); } catch (e) { /* private mode */ } }
  }

  async function start() {
    tip.el = $("tip");
    let saved = null;
    try { saved = localStorage.getItem("tp-tema"); } catch (e) { /* private mode */ }
    setTheme((query.get("tema") || saved) === "escuro", false);
    try {
      [index, texts, lineReady] = await Promise.all([getJSON("out/index.json"), loadTexts(),
        fetch("img/janela-claro.webp", { method: "HEAD" }).then((r) => r.ok).catch(() => false)]);
    } catch (e) {
      $("app").replaceChildren(h("h1", { class: "tp-headline" }, "Não encontrei os arquivos do score."),
        h("p", { class: "tp-lead" }, "Rode python3 run.py --port 8000 na pasta solution e abra o endereço que ele mostrar."));
      return;
    }
    state.seller = index.default_seller;
    state.monday = index.default_monday;
    readHash();
    if (!index.mondays.some((m) => m.monday === state.monday)) state.monday = index.default_monday;
    const reset = () => { for (const k in shown) delete shown[k]; };
    $("f-region").addEventListener("change", (e) => { state.region = e.target.value; render(true); });
    $("f-manager").addEventListener("change", (e) => { state.manager = e.target.value; render(true); });
    $("f-seller").addEventListener("change", (e) => { state.seller = e.target.value; reset(); render(true); });
    $("f-monday").addEventListener("change", (e) => { state.monday = e.target.value; reset(); render(true); });
    $("view-seller").addEventListener("click", () => { state.view = "vendedor"; render(true); });
    $("view-manager").addEventListener("click", () => { state.view = "gestor"; render(true); });
    $("theme").addEventListener("click", () => { setTheme(!document.documentElement.hasAttribute("data-tema"), true); render(false); });
    $("how-open").addEventListener("click", () => { closeTip(); fillHow(); $("how").showModal(); });
    $("how").addEventListener("click", (e) => { if (e.target === $("how")) $("how").close(); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeTip(); });
    document.addEventListener("click", () => closeTip());
    document.addEventListener("scroll", () => { if (!tip.pinned) closeTip(); }, true);
    await render(true);
  }
  start();
})();

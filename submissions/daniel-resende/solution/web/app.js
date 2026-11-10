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
  let pics = null; // img/janela.json: the background images of the window and the numbers they were drawn from
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
    fillSelect($("f-monday"), index.mondays.map((m) => [m.monday, brDate(m.monday) + (m.past ? " (passado)" : " (atual)")]), state.monday);
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
    const left = d.days_left === 0 ? "último dia na janela" : `${num(d.days_left)} ${pl(d.days_left, "dia restante", "dias restantes")} na janela`;
    return [
      h("p", { class: "tp-tip-h" }, d.product, d.account ? " · " + d.account : " · sem conta registrada"),
      para(h("b", {}, "Próximo passo: "), step || PLAY[d.play]),
      para(`Aberto há ${num(d.days_open)} ${pl(d.days_open, "dia", "dias")}; ${left}, até ${brDate(d.window_end)}.` + (d.cooling ? " Esfriando: aberto há mais de 90 dias." : "")),
      reason && !reason.includes(d.time_sentence) ? para(reason) : null,
      para(d.time_sentence, table.exists ? " Vale para todos os negócios que chegaram a essa idade; não é a chance deste negócio." : ""),
      para(`${money(d.value)} é o valor de tabela: o preço de lista do produto, porque negócio aberto não tem valor de fechamento.`),
      d.after ? para(afterText(d)) : null,
      h("p", { class: "tp-tip-id" }, "ID " + d.id + (step ? " · frase do próximo passo redigida por IA" : "")),
    ];
  }

  // --- the window: the chart of the product ---------------------------------------
  // Columns: of each 100 deals that reached an age still open, how many were won
  // afterwards, as known on that Monday. Marks: the seller's living deals on the same
  // axis of age. The picture with depth is a ready file (img/), drawn from the same
  // numbers; this layer writes every number and every word live, from the score file.
  const FLAT = { h: 230, x0: 0.05, x1: 0.75, base: 0.652, unit: 0.522 / 70, col: 0.0125, ox: 0, oy: 0, out0: 0.80, out1: 0.955, outH: 0.30 };
  const isDark = () => document.documentElement.hasAttribute("data-tema");
  function tickTip(row, table) {
    return () => [para(row.reached_days === 0
      ? `Cerca de ${row.won_per_100} em cada 100 negócios foram ganhos depois de engajados.`
      : `Cerca de ${row.won_per_100} em cada 100 negócios que chegaram abertos aos ${row.reached_days} dias foram ganhos depois.`),
    para(`Conta de ${brDate(table.counted_on)}: ${num(row.deals)} negócios chegaram a essa idade; ${num(row.won_after)} ganhos, ${num(row.lost_after)} perdidos, ${num(row.never_closed)} nunca fecharam. É a história de todos os negócios dessa idade, não a chance de um negócio.`)];
  }
  const chartTitle = (table) => (table.exists
    ? `Ganhos depois, em cada 100 que chegaram abertos a cada idade · conta de ${brDate(table.counted_on)}`
    : "Sem histórico suficiente nesta data: só as idades e os seus negócios.");
  function picture(score) {
    // a background image is shown only if it was drawn from exactly the numbers of this score file
    if (!pics) return null;
    const table = score.meta.time_table, theme = isDark() ? "escuro" : "claro";
    if (!table.exists) return pics.empty[theme] || null;
    const made = pics.mondays[score.meta.monday];
    const same = made && made.values.length === table.rows.length && table.rows.every((r, i) => r.won_per_100 === made.values[i]);
    return same ? made[theme] : null;
  }
  function drawWindow(svg, score, seller, animate) {
    const W = Math.max(700, Math.floor(svg.parentNode.getBoundingClientRect().width));
    const table = score.meta.time_table, longest = score.meta.window.longest_win_days;
    const pic = picture(score), G = pic ? pics.geometry : FLAT, H = innerHeight < 900 ? 208 : G.h; // every measure below is a fraction of H
    const X = (age) => (G.x0 + (Math.min(age, longest) / longest) * (G.x1 - G.x0)) * W;
    const base = G.base * H, unit = G.unit * H, lift = G.oy * H;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.setAttribute("width", W);
    svg.setAttribute("height", H);
    svg.classList.toggle("tp-still", !animate);
    const cooling = seller.alive.filter((d) => d.cooling).length;
    svg.setAttribute("aria-label",
      `A janela de ${longest} dias. ` + (table.exists ? `De cada 100 negócios que chegaram abertos a cada idade, ganhos depois (conta de ${brDate(table.counted_on)}): ` +
        table.rows.map((row) => `${row.reached_days} dias, ${row.won_per_100}`).join("; ") + ". " : "Sem histórico suficiente nesta data. ") +
      `${count(seller.alive.length, "negócio vivo", "negócios vivos", "Nenhum negócio vivo")}, ${count(cooling, "esfriando", "esfriando", "nenhum esfriando")}; ` +
      `${num(seller.headline.clean)} fora da janela, para limpar. A lista de vivos traz os mesmos negócios.`);
    const kids = [];
    const blockTop = base - G.outH * H, bx0 = G.out0 * W, bx1 = G.out1 * W;
    if (pic) {
      kids.push(s("image", { href: "img/" + pic.file, x: 0, y: 0, width: W, height: H, preserveAspectRatio: "none", "aria-hidden": "true" }));
    } else { // no background image for these numbers: the same chart, flat, drawn here
      kids.push(s("rect", { class: "tp-w-zone", x: X(score.meta.cooling_after_days), y: 0, width: X(longest) - X(score.meta.cooling_after_days), height: H }));
      kids.push(s("rect", { class: "tp-w-block", x: bx0, y: blockTop, width: bx1 - bx0, height: base - blockTop }));
      kids.push(s("line", { class: "tp-r-axis", x1: G.x0 * W - 12, y1: base, x2: bx1 + 12, y2: base }));
      if (table.exists) for (const row of table.rows) {
        kids.push(s("rect", { class: "tp-w-col", x: X(row.reached_days) - (G.col * W) / 2, y: base - row.won_per_100 * unit - (row.won_per_100 ? 0 : 2), width: G.col * W, height: row.won_per_100 * unit + (row.won_per_100 ? 0 : 2) }));
      }
    }
    kids.push(s("text", { class: "tp-r-strong", x: G.x0 * W - (G.col * W) / 2, y: 17, "font-size": 13 }, chartTitle(table)));
    kids.push(s("text", { x: X(score.meta.cooling_after_days) + G.col * W + 6, y: 40, "font-size": 12.5 }, "esfriando"));
    const ages = table.exists ? table.rows : [0, 30, 60, 90, 120, longest].map((a) => ({ reached_days: a }));
    ages.forEach((row, i) => {
      const cx = X(row.reached_days), last = row.reached_days === longest;
      kids.push(s("text", { class: "tp-r-strong", "data-dado": "", x: cx, y: base + 17, "text-anchor": "middle", "font-size": 12.5 }, last ? `${row.reached_days} dias` : String(row.reached_days)));
      if (!table.exists) return;
      // the number of the column, in ink, on top of it
      kids.push(s("text", { class: "tp-r-num", "data-dado": "", "data-age": row.reached_days, x: cx + (G.ox * W) / 2, y: base - row.won_per_100 * unit - lift - 6, "text-anchor": "middle", "font-size": 14 }, String(row.won_per_100)));
      const lo = i ? (cx + X(ages[i - 1].reached_days)) / 2 : G.x0 * W - 30, hi = last ? cx + 30 : (cx + X(ages[i + 1].reached_days)) / 2;
      kids.push(withTip(s("rect", { class: "tp-r-hit", x: lo, y: 24, width: hi - lo, height: base - 2, tabindex: 0, role: "button",
        "aria-label": `Idade de ${row.reached_days} dias: cerca de ${row.won_per_100} em cada 100 negócios que chegaram abertos até ali foram ganhos depois` }), tickTip(row, table)));
    });
    kids.push(s("text", { class: "tp-r-num", "data-dado": "", x: (bx0 + bx1) / 2 + (G.ox * W) / 2, y: blockTop - lift - 6, "text-anchor": "middle", "font-size": 14 }, num(seller.headline.clean)));
    kids.push(s("text", { class: "tp-r-strong", x: (bx0 + bx1) / 2, y: base + 17, "text-anchor": "middle", "font-size": 12.5 }, "para limpar"));
    // the living deals: one mark each, on the same axis of age, in a lane in front of the columns
    const deals = [...seller.alive].sort((a, b) => a.days_open - b.days_open || (a.id < b.id ? -1 : 1));
    const r = deals.length > 45 ? 4 : 5, laneTop = base + 24, step = 2 * r + 2, maxLevels = Math.max(1, Math.floor((H - laneTop - 2) / step));
    const levels = [];
    // the lane says in words what its marks are
    kids.push(s("text", { x: (G.x1 + 0.012) * W, y: laneTop + r + 4, "font-size": 12.5 }, deals.length ? "← seus negócios vivos, pela idade" : "nenhum negócio vivo"));
    deals.forEach((d, i) => {
      const cx = X(d.days_open);
      let level = 0;
      while (levels[level] !== undefined && cx - levels[level] < 2 * r + 2) level += 1;
      levels[level] = cx;
      if (level >= maxLevels) return; // a very long list: the marks beyond the lane stay in the list only
      const cy = laneTop + r + level * step;
      const shape = d.cooling
        ? s("path", { d: `M${cx} ${cy - r - 1}L${cx + r + 1} ${cy}L${cx} ${cy + r + 1}L${cx - r - 1} ${cy}Z`, class: "tp-mark tp-m-frio" })
        : s("circle", { cx, cy, r, class: "tp-mark tp-m-vivo" });
      shape.style.setProperty("--i", Math.min(i, 30));
      shape.setAttribute("data-id", d.id);
      shape.addEventListener("mouseenter", () => { if (!tip.pinned) openTip(shape, () => dealTip(d, table), false); });
      shape.addEventListener("mouseleave", () => { if (!tip.pinned && tip.anchor === shape) closeTip(); });
      shape.addEventListener("click", (e) => { e.stopPropagation(); focusDeal(d.id); });
      kids.push(shape);
    });
    svg.replaceChildren(...kids);
  }
  // on a phone the same chart is rows, one per age, drawn here
  function windowRows(score, seller) {
    const table = score.meta.time_table, longest = score.meta.window.longest_win_days;
    const ages = table.exists ? table.rows : [0, 30, 60, 90, 120, longest].map((a) => ({ reached_days: a }));
    const band = (d) => [...ages].reverse().find((row) => row.reached_days <= d.days_open).reached_days;
    return h("div", { class: "tp-wrows" },
      h("p", { class: "tp-wtitle" }, chartTitle(table)),
      h("ol", {}, ages.map((row) => h("li", { class: "tp-wrow" + (row.reached_days >= score.meta.cooling_after_days ? " tp-wfrio" : "") },
        h("span", { class: "tp-wage", "data-dado": "" }, `${row.reached_days} dias`),
        table.exists ? withTip(h("button", { type: "button", class: "tp-wbar", "aria-label": `Idade de ${row.reached_days} dias: cerca de ${row.won_per_100} em cada 100 foram ganhos depois` },
          h("i", { style: `width:${Math.max(1.5, (row.won_per_100 / 70) * 100).toFixed(1)}%` }), h("b", { "data-dado": "" }, String(row.won_per_100))), tickTip(row, table)) : h("span", { class: "tp-wbar" }),
        h("span", { class: "tp-wmarks" }, seller.alive.filter((d) => band(d) === row.reached_days).map((d) =>
          withTip(h("button", { type: "button", class: "tp-wmark" + (d.cooling ? " tp-wm-frio" : ""), "data-id": d.id, "aria-label": `${d.product}, aberto há ${d.days_open} dias` }), () => dealTip(d, table)))))),
        h("li", { class: "tp-wrow tp-wout" }, h("span", { class: "tp-wage" }, "fora"), h("span", { class: "tp-wbar" }, h("b", { "data-dado": "" }, num(seller.headline.clean))), h("span", { class: "tp-wmarks" }, "para limpar"))));
  }
  function focusDeal(id) {
    const row = $("deal-" + id);
    if (!row) return;
    closeTip();
    row.scrollIntoView({ block: "nearest", behavior: "auto" });
    row.focus();
  }
  function windowSection(score, seller, animate) {
    const section = h("section", { class: "tp-window", "aria-label": "A janela" });
    let mode = "";
    const draw = (anim) => {
      const wNow = Math.floor(section.getBoundingClientRect().width);
      if (wNow === 0) return;
      const next = wNow < 700 ? "rows" : "chart:" + wNow;
      if (next === mode) return;
      mode = next;
      if (wNow < 700) { section.replaceChildren(windowRows(score, seller)); return; }
      const svg = s("svg", { class: "tp-ruler", role: "group" }); // a group, not an image: the ages inside it take focus
      section.replaceChildren(svg);
      drawWindow(svg, score, seller, anim);
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
      return [past ? `Naquela segunda o pipeline de ${first} estava limpo: nenhum vivo e nada para limpar.`
        : `${first}, seu pipeline está limpo: nenhum vivo, nada na fila e nada para limpar.`];
    }
    // the punctuation rides inside the coloured chunk so a line never starts with a comma
    const alive = (tail) => h("span", { class: "tp-k-vivo" }, count(hd.alive, "vivo", "vivos", "nenhum vivo"), h("i", {}, tail));
    const clean = h("span", { class: "tp-k-limpar" }, hd.clean ? `${num(hd.clean)} para limpar` : "nada para limpar", h("i", {}, "."));
    if (past) return [`Naquela segunda, ${first} tinha `, alive(""), " e ", clean];
    const queue = h("span", { class: "tp-k-fila" }, hd.queue ? `${num(hd.queue)} na fila` : "nenhum na fila");
    return [`${first}, você tem `, alive(","), " ", queue, " e ", clean];
  }
  function kpis(hd, past) {
    const cell = (cls, label, value, unit) => h("div", { class: "tp-kpi " + cls }, h("dt", {}, label), h("dd", {}, h("b", {}, value), h("span", {}, unit)));
    return h("dl", { class: "tp-kpis", "data-dado": "" },
      cell("tp-kv", "Negócios vivos", num(hd.alive), "negócios"),
      cell("tp-kv", "Valor vivo", num(hd.alive_value), "US$ de tabela"),
      cell("tp-kf", "Esfriando agora", num(hd.cooling), "negócios"),
      cell("tp-kq", "Na fila", past ? "–" : num(hd.queue), "negócios"),
      cell("tp-kl", "Para limpar", num(hd.clean), "negócios"),
      cell("tp-kl", "Valor parado", num(hd.clean_value), "US$ de tabela"));
  }
  function briefButton(sel) {
    const body = part("briefing:" + sel.seller, "body");
    if (!body) return null;
    const t = texts.byId.get("briefing:" + sel.seller), p = t.provenance || {};
    const btn = h("button", { type: "button", class: "tp-btn", id: "brief" }, "Copiar briefing");
    btn.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(body); btn.textContent = "Briefing copiado"; } catch (e) { btn.textContent = "Não copiou: leia abaixo"; }
      openTip(btn, build, true);
    });
    const build = () => [h("p", { class: "tp-tip-h" }, "Briefing de segunda"), para(body),
      h("p", { class: "tp-tip-id" }, `Redigido por IA${p.model ? " (" + p.model + ")" : ""}; números e nomes preenchidos pelo código.`)];
    return withTip(btn, build, { click: false });
  }
  function aliveRow(d, table, past) {
    const result = d.after ? { ganho: "ganho", perdido: "perdido", aberto: "aberto" }[d.after.result] : null;
    const row = h("button", { type: "button", class: "tp-row tp-alive" + (past ? " tp-has-after" : ""), id: "deal-" + d.id },
      h("span", { class: "tp-name" }, h("span", { class: "tp-prod" }, d.product), d.account ? h("span", { class: "tp-acct" }, d.account) : null,
        d.cooling ? h("span", { class: "tp-tag" }, "esfriando") : null),
      h("span", { class: "tp-num tp-c-val" }, num(d.value)),
      h("span", { class: "tp-num tp-c-days" }, d.days_left === 0 ? "último" : num(d.days_left)),
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
    if (def) withTip(title, () => [h("p", { class: "tp-tip-h" }, label), para(def)]);
    return h("section", { class: "tp-panel " + cls, "aria-label": label },
      h("header", { class: "tp-panel-head" }, h("h2", {}, title), sum ? h("p", { class: "tp-sum" }, sum) : null),
      kids);
  }
  function renderSeller(score, animate) {
    const meta = score.meta, past = meta.past;
    const sel = score.sellers.find((x) => x.seller === state.seller);
    const hd = sel.headline, ev = index.evidence, a = sel.after;
    const cols = (third) => h("p", { class: "tp-cols" + (past ? " tp-has-after" : ""), "aria-hidden": "true" },
      h("span", {}, "Negócio"), h("span", {}, "Tabela, US$"), third ? h("span", {}, third) : null, past && third ? h("span", {}, "Depois") : null);
    const alive = panel("tp-vivos", "Vivos", num(hd.alive),
      hd.alive && past ? `depois: ${num(a.alive_won)} ${pl(a.alive_won, "ganho", "ganhos")} · ${num(a.alive_lost)} ${pl(a.alive_lost, "perdido", "perdidos")} · ${num(a.alive_open)} ${pl(a.alive_open, "aberto", "abertos")}` : null,
      hd.alive
        ? [cols("Restam, dias"), h("ol", { class: "tp-list" }, sel.alive.map((d) => aliveRow(d, meta.time_table, past)))]
        : h("p", { class: "tp-empty" }, past ? "Nenhum vivo naquela data." : hd.queue ? "Nenhum vivo: comece pela fila." : "Nenhum negócio vivo."),
      `Vivo é o negócio dentro da janela em que negócios já foram ganhos: aberto há no máximo ${meta.window.longest_win_days} dias e antes do fim do trimestre seguinte ao do engajamento. A ordem é por valor de tabela; no empate, mais dias restantes.`);
    const queue = past
      ? panel("tp-fila", "Fila", null, null, h("p", { class: "tp-empty" }, "A fila não pode ser reconstruída no passado."),
        "O CRM não guarda a data em que um negócio entrou na fila; por isso ela não existe numa segunda do passado.")
      : panel("tp-fila", "Fila para engajar", num(hd.queue), null,
        hd.queue ? [cols(null), grouped("fila", sel.queue, meta.window)] : h("p", { class: "tp-empty" }, "Fila vazia."),
        "Negócios ainda sem data de engajamento: o próximo trabalho é engajar e registrar a data. É só uma lista por valor de tabela; nada mais nos dados ordena esses negócios.");
    const cleanList = hd.clean ? h("div", { id: "clean-list", hidden: !shown.clean }, cols(null), grouped("limpar", sel.clean, meta.window)) : null;
    const cleanBtn = hd.clean ? h("button", { type: "button", class: "tp-btn", "aria-expanded": String(!!shown.clean), "aria-controls": "clean-list" }, shown.clean ? "Ocultar lista" : "Ver lista") : null;
    if (cleanBtn) cleanBtn.addEventListener("click", () => { shown.clean = !shown.clean; cleanList.hidden = !shown.clean; cleanBtn.textContent = shown.clean ? "Ocultar lista" : "Ver lista"; cleanBtn.setAttribute("aria-expanded", String(!!shown.clean)); });
    const clean = panel("tp-limpar", "Para limpar", num(hd.clean),
      hd.clean && past ? `depois: ${count(a.clean_won, "ganho", "ganhos", "nenhum ganho")}` : null,
      hd.clean ? [
        h("p", { class: "tp-evidence" }, `${num(ev.won_after)} ${pl(ev.won_after, "ganho", "ganhos")} em ${num(ev.distinct_deals_past_window)} fora da janela.`),
        h("p", { class: "tp-action" }, h("b", {}, "Ação: "), "encerrar no CRM."), cleanBtn, cleanList,
      ] : h("p", { class: "tp-empty" }, "Nada para limpar."),
      `Negócios fora da janela: abertos há mais de ${meta.window.longest_win_days} dias, ou com o prazo do trimestre vencido. No teste, ${num(ev.won_after)} de ${num(ev.distinct_deals_past_window)} negócios assim ${pl(ev.won_after, "foi ganho", "foram ganhos")} depois. Os dados não dizem por que pararam.`);
    const brief = past ? null : briefButton(sel);
    return [
      h("div", { class: "tp-head" },
        h("h1", { class: "tp-headline" }, sellerHeadline(sel, past)),
        h("div", { class: "tp-head-side" },
          past ? h("p", { class: "tp-past" }, "Segunda do passado: cada linha mostra o que veio depois.") : null, brief)),
      kpis(hd, past),
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
    const scale = Math.max(1, ...rows.map((x) => Math.max(x.alive_value, x.clean_value)));
    const headline = [`${label} tem `,
      h("span", { class: "tp-k-vivo" }, count(scope.alive, "vivo", "vivos", "nenhum vivo"), h("i", {}, past ? "" : ",")),
      past ? " e " : [" ", h("span", { class: "tp-k-fila" }, scope.queue ? `${num(scope.queue)} na fila` : "nenhum na fila"), " e "],
      h("span", { class: "tp-k-limpar" }, scope.clean ? `${num(scope.clean)} para limpar` : "nada para limpar", h("i", {}, "."))];
    const body = state.manager && !past ? part("manager:" + state.manager, "body") : null;
    let brief = null;
    if (body) {
      const p = (texts.byId.get("manager:" + state.manager).provenance || {});
      brief = withTip(h("button", { type: "button", class: "tp-btn", id: "brief" }, "Resumo do gestor"),
        () => [h("p", { class: "tp-tip-h" }, "Resumo do gestor"), para(body),
          h("p", { class: "tp-tip-id" }, `Redigido por IA${p.model ? " (" + p.model + ")" : ""}; números e nomes preenchidos pelo código.`)]);
    }
    const facts = (x) => [para(`${count(x.alive, "negócio vivo", "negócios vivos", "Nenhum negócio vivo")}: ${money(x.alive_value)} de tabela` + (x.cooling ? `, ${num(x.cooling)} esfriando.` : ".")),
      para(`${num(x.clean)} para limpar: ${money(x.clean_value)} de tabela, fora da janela.`),
      past ? null : para(x.queue ? `${num(x.queue)} na fila: ${money(x.queue_value)} de tabela.` : "Nenhum negócio na fila."),
      x.sellers > 1 ? para(`${num(x.sellers_without_alive)} de ${num(x.sellers)} vendedores sem nenhum vivo.`) : null];
    const bar = (cls, value) => h("span", { class: "tp-bar-track", "aria-hidden": "true" },
      value ? h("span", { class: "tp-bar-fill " + cls, style: `width:${((value / scale) * 100).toFixed(2)}%` }) : null);
    const sellerRow = (x) => {
      const open = h("button", { type: "button", class: "tp-who", onclick: () => { state.view = "vendedor"; state.seller = x.seller; render(true); } }, x.seller);
      withTip(open, () => [h("p", { class: "tp-tip-h" }, x.seller), ...facts(x), h("p", { class: "tp-tip-id" }, "Clique para abrir a segunda-feira deste vendedor.")], { click: false });
      return h("li", { class: "tp-trow" }, open,
        h("span", { class: "tp-bars" }, bar("tp-b-vivo", x.alive_value), bar("tp-b-limpar", x.clean_value)),
        h("span", { class: "tp-num tp-t-n" }, num(x.alive)), h("span", { class: "tp-num tp-t-n" }, past ? "–" : num(x.queue)), h("span", { class: "tp-num tp-t-n" }, num(x.clean)));
    };
    const managers = team.by_manager.filter((m) => (!state.region || m.region === state.region) && (!state.manager || m.manager === state.manager));
    const regions = state.manager ? [] : team.by_region.filter((g) => !state.region || g.region === state.region);
    return [
      h("div", { class: "tp-head" }, h("h1", { class: "tp-headline" }, headline),
        h("div", { class: "tp-head-side" },
          past ? h("p", { class: "tp-past" }, "Segunda do passado: a fila não existe nessa data.") : null,
          h("p", { class: "tp-lead" }, `${num(scope.sellers_without_alive)} de ${num(scope.sellers)} sem nenhum vivo.`), brief)),
      regions.length ? h("section", { class: "tp-regions", "aria-label": "Por regional" }, regions.map((g) => {
        const b = h("button", { type: "button", class: "tp-region" }, h("b", {}, g.region),
          ` ${count(g.alive, "vivo", "vivos", "nenhum vivo")}` + (past ? "" : ` · ${num(g.queue)} na fila`) + ` · ${num(g.clean)} para limpar`);
        return withTip(b, () => [h("p", { class: "tp-tip-h" }, "Regional " + g.region), ...facts(g)]);
      })) : null,
      h("section", { class: "tp-panel tp-team", "aria-label": "Por vendedor" },
        h("p", { class: "tp-cols tp-tcols", "aria-hidden": "true" }, h("span", {}, "Vendedor"), h("span", {}, "Valor vivo e valor parado"), h("span", {}, "Vivos"), h("span", {}, "Fila"), h("span", {}, "Limpar")),
        h("div", { class: "tp-list" }, managers.map((m) => h("div", { class: "tp-mgr" },
          h("h2", { class: "tp-mgr-h" }, `${m.manager} · ${m.region}`),
          h("ol", {}, rows.filter((x) => x.manager === m.manager).map(sellerRow)))))),
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
      h("h3", {}, "Vivo ou para limpar"),
      para(`Vivo é o negócio dentro da janela em que negócios já foram ganhos: aberto há no máximo ${w.longest_win_days} dias e antes do fim do trimestre seguinte ao do engajamento. Passou de um dos dois, é para limpar.`),
      para(`Nenhum negócio foi ganho depois de ${w.longest_win_days} dias aberto. Dos ${num(w.closings_known)} fechamentos conhecidos, ${num(w.closings_after_deadline)} ${pl(w.closings_after_deadline, "ocorreu", "ocorreram")} depois do prazo do trimestre.`),
      para(`No teste, em ${num(ev.cuts)} datas: ${num(ev.distinct_deals_past_window)} negócios distintos saíram da janela; ${num(ev.won_after)} ${pl(ev.won_after, "foi ganho", "foram ganhos")} depois, ${num(ev.lost_after)} ${pl(ev.lost_after, "perdido", "perdidos")} e ${num(ev.still_open_at_data_end)} seguiam abertos. As datas se sobrepõem no tempo: não é um teste independente.`),
      para("A ação em “para limpar” é encerrar no CRM e tirar da segunda-feira. Os dados não dizem por que esses negócios estão parados."),
      h("h3", {}, "A ordem entre os vivos"),
      para(`Valor de tabela, do maior para o menor; no empate, mais dias restantes primeiro. Com ${index.value_note.list_prices} preços de tabela é quase ordem por produto, e ela não foi confirmada em datas novas.`),
      para("A contagem regressiva e a marca “esfriando” (vivo há mais de " + m.cooling_after_days + " dias) informam, mas não mudam a ordem. Nada na tela diz que um negócio vivo fecha mais que outro."),
      h("h3", {}, "Valor"),
      para("É o valor de tabela: o preço de lista do produto. Negócio aberto ainda não tem valor de fechamento."),
      h("h3", {}, "A conta por idade"),
      t.exists
        ? [para(`De cada 100 negócios que chegaram abertos a cada idade, cerca de quantos foram ganhos depois. Conta de ${brDate(t.counted_on)}, com os ${num(t.deals)} negócios que já tinham tido tempo de fechar. Vale para a faixa de idade, não para um negócio.`),
          h("ol", { class: "tp-table" }, t.rows.map((row) => h("li", {},
            h("span", {}, row.reached_days === 0 ? "Engajados (0 dias)" : `Abertos aos ${row.reached_days} dias`),
            h("span", {}, `cerca de ${row.won_per_100} em cada 100 ganhos depois`))))]
        : para("Sem histórico suficiente nesta data: nenhum negócio tinha tido tempo de fechar."),
      h("h3", {}, "A fila"),
      para("São os negócios ainda sem data de engajamento. É só uma lista por valor de tabela: nada mais nos dados ordena esses negócios. Numa segunda do passado a fila não pode ser reconstruída, porque o CRM não guarda a data em que um negócio entrou."),
      h("h3", {}, "Os textos"),
      para(prov
        ? `O próximo passo de cada negócio é escolhido por regra. A frase que o acompanha, o briefing e o resumo do gestor foram redigidos por IA (${prov.model || "modelo não registrado"}, em ${prov.generated_on || "data não registrada"}); os números e os nomes são preenchidos pelo código.`
        : "O próximo passo de cada negócio é escolhido por regra. Os textos de IA não estão carregados: a tela mostra só as frases de regra."),
      h("h3", {}, "Os dados"),
      para(`Segunda-feira ${brDate(m.monday)}, com os dados fechados no domingo ${brDate(m.data_closed)}. As idades são contadas nessa data, e o dia do prazo ainda conta como vivo.` +
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
      [index, texts, pics] = await Promise.all([getJSON("out/index.json"), loadTexts(), getJSON("img/janela.json").catch(() => null)]);
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

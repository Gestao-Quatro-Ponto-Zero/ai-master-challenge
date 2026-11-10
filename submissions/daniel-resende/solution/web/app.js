"use strict";
/* Segunda-feira: reads only the contract files (out/index.json, out/score-*.json)
   and, when it exists, ai/textos.json. Every number shown comes from those files;
   this script formats and lays out, it never sums or scores. Data is always
   written with textContent, never as HTML. */
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
  const SHOW = { alive: 12, queue: 8, clean: 8 };

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

  // --- state -----------------------------------------------------------------
  const query = new URLSearchParams(location.search);
  const state = { view: "vendedor", seller: null, manager: "", region: "", monday: null };
  const shown = {}; // lists the user asked to see in full, per render key
  let index = null;
  let texts = null;
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

  // --- filters ---------------------------------------------------------------
  function fillSelect(sel, options, value) {
    sel.replaceChildren(...options.map(([v, label]) => h("option", { value: v, selected: v === value }, label)));
    sel.value = value;
  }
  function syncFilters() {
    const regions = [...new Set(index.sellers.map((x) => x.region))].sort();
    if (state.region && !regions.includes(state.region)) state.region = "";
    const inRegion = index.sellers.filter((x) => !state.region || x.region === state.region);
    const managers = [...new Set(inRegion.map((x) => x.manager))].sort();
    if (state.manager && !managers.includes(state.manager)) state.manager = "";
    const sellers = inRegion.filter((x) => !state.manager || x.manager === state.manager);
    if (!sellers.some((x) => x.seller === state.seller)) {
      state.seller = sellers.some((x) => x.seller === index.default_seller) ? index.default_seller : sellers[0].seller;
    }
    fillSelect($("f-region"), [["", "Todas"], ...regions.map((r) => [r, r])], state.region);
    fillSelect($("f-manager"), [["", "Todos"], ...managers.map((m) => [m, m])], state.manager);
    fillSelect($("f-seller"), sellers.map((x) => [x.seller, x.seller]), state.seller);
    fillSelect($("f-monday"), index.mondays.map((m) => [m.monday,
      brDate(m.monday) + (m.past ? " (passado)" : " (atual)")]), state.monday);
    $("l-seller").hidden = state.view !== "vendedor";
    document.body.classList.toggle("tp-view-vendedor", state.view === "vendedor");
    $("view-seller").setAttribute("aria-pressed", String(state.view === "vendedor"));
    $("view-manager").setAttribute("aria-pressed", String(state.view === "gestor"));
  }

  // --- pieces ----------------------------------------------------------------
  function whenLine(meta) {
    return h("p", { class: "tp-when" },
      `Segunda-feira, ${brDate(meta.monday)} · dados fechados no domingo, ${brDate(meta.data_closed)}`);
  }
  function pastBanner(meta) {
    return h("p", { class: "tp-past" },
      `Você está vendo uma segunda-feira do passado, só com o que se sabia naquele dia. ` +
      `Em cada negócio, a linha "Depois" mostra o que aconteceu até ${brDate(meta.outcomes_until)}.`);
  }
  function account(d) {
    return d.account
      ? h("span", { class: "tp-acct" }, d.account)
      : h("span", { class: "tp-acct tp-none" }, "sem conta registrada");
  }
  const dealId = (d) => h("span", { class: "tp-id" }, "ID " + d.id);
  function afterLine(d) {
    const a = d.after;
    if (!a) return null;
    if (a.result === "ganho") {
      return h("p", { class: "tp-after tp-won" }, "Depois: ", h("b", {}, "ganho"),
        ` em ${brDate(a.close_date)}, ${money(a.close_value)} (${num(a.days_after)} ${pl(a.days_after, "dia", "dias")} depois).`);
    }
    if (a.result === "perdido") {
      return h("p", { class: "tp-after tp-lost" }, "Depois: ", h("b", {}, "perdido"),
        ` em ${brDate(a.close_date)} (${num(a.days_after)} ${pl(a.days_after, "dia", "dias")} depois).`);
    }
    return h("p", { class: "tp-after" }, "Depois: ", h("b", {}, "seguia aberto"), " no fim dos dados.");
  }
  function moreButton(key, total, limit, label) {
    if (total <= limit || shown[key]) return null;
    return h("button", { type: "button", class: "tp-btn tp-more", onclick: () => { shown[key] = true; render(); } },
      `Mostrar ${pl(total - limit, "o outro", "os outros")} ${num(total - limit)} ${label}`);
  }
  const visible = (key, items, limit) => (shown[key] ? items : items.slice(0, limit));
  // a button that shows or hides the element it controls; the state survives a re-render
  function toggle(key, target, closed, open, cls) {
    const btn = h("button", { type: "button", class: cls || "tp-link", "aria-expanded": String(!!shown[key]), "aria-controls": target.id },
      shown[key] ? open : closed);
    target.hidden = !shown[key];
    btn.addEventListener("click", () => {
      shown[key] = !shown[key];
      target.hidden = !shown[key];
      btn.textContent = shown[key] ? open : closed;
      btn.setAttribute("aria-expanded", String(!!shown[key]));
    });
    return btn;
  }

  function aliveRow(d, table) {
    const reason = part("deal:" + d.id, "reason");
    const step = part("deal:" + d.id, "next_step");
    const left = d.days_left === 0 ? "Último dia" : `${num(d.days_left)} ${pl(d.days_left, "dia", "dias")}`;
    const why = h("div", { class: "tp-why", id: "why-" + d.id },
      reason && !reason.includes(d.time_sentence) ? h("p", {}, reason) : null,
      h("p", {}, d.time_sentence),
      table.exists ? h("p", {}, "Essa conta vale para todos os negócios que chegaram a essa idade; não é a chance deste negócio.") : null,
      reason && reason.includes(d.time_sentence) ? h("p", {}, reason.replace(d.time_sentence, "").trim()) : null);
    return h("li", { class: "tp-row tp-alive", id: "deal-" + d.id },
      h("span", { class: "tp-rank" }, d.rank + "º"),
      h("div", { class: "tp-what" },
        h("p", {}, h("span", { class: "tp-prod" }, d.product), account(d),
          d.cooling ? h("span", { class: "tp-tag" }, "esfriando") : null)),
      h("div", { class: "tp-val" }, h("span", { class: "tp-num" }, money(d.value)),
        h("span", { class: "tp-cap" }, "valor de tabela")),
      h("div", { class: "tp-left" },
        h("div", { class: "tp-mini", style: `--p:${Math.min(100, (d.days_open / 138) * 100).toFixed(1)}%`, "aria-hidden": "true" }, h("i", {})),
        h("p", {}, h("b", { class: "tp-num" }, left),
          `${d.days_left === 0 ? "" : pl(d.days_left, " restante", " restantes")} na janela, até ${brDate(d.window_end)} · aberto há ${num(d.days_open)} ${pl(d.days_open, "dia", "dias")}`)),
      h("p", { class: "tp-step" }, h("b", {}, "Próximo passo: "), step || PLAY[d.play]),
      h("p", { class: "tp-foot-row" }, toggle("why:" + d.id, why, "Por quê?", "Fechar"), dealId(d)),
      why,
      afterLine(d));
  }
  function slimRow(d, window) {
    const fact = d.block !== "limpar" ? "sem data de engajamento"
      : `aberto há ${num(d.days_open)} dias · ` + (d.clean_fact === "idade"
        ? `passou dos ${window.longest_win_days} dias` : `prazo venceu em ${brDate(d.deadline)}`);
    return h("li", { class: "tp-row tp-slim", id: "deal-" + d.id },
      h("span", { class: "tp-rank" }, d.rank + "º"),
      h("div", { class: "tp-what" }, h("p", {}, account(d), dealId(d)), h("p", { class: "tp-cap" }, fact)),
      afterLine(d));
  }
  // The queue and the clean list repeat the same product many times: one line per
  // product (there are only seven list prices), each opening its own deals.
  function grouped(key, items, window) {
    const groups = [];
    for (const d of items) {
      const last = groups[groups.length - 1];
      if (last && last.product === d.product) last.items.push(d); else groups.push({ product: d.product, value: d.value, items: [d] });
    }
    return h("ul", { class: "tp-groups" }, groups.map((g) => {
      const list = h("ol", { class: "tp-rows", id: `${key}-${g.product.replace(/\W+/g, "-")}` }, g.items.map((d) => slimRow(d, window)));
      const n = g.items.length;
      return h("li", { class: "tp-group" },
        h("div", { class: "tp-group-head" },
          h("p", {}, h("span", { class: "tp-prod" }, g.product), h("span", { class: "tp-acct" }, `${num(n)} ${pl(n, "negócio", "negócios")}`)),
          h("p", { class: "tp-val" }, h("span", { class: "tp-num" }, money(g.value * n)),
            h("span", { class: "tp-cap" }, n === 1 ? "valor de tabela" : `${money(g.value)} cada, valor de tabela`)),
          toggle(`${key}:${g.product}`, list, n === 1 ? "Ver o negócio" : `Ver os ${num(n)}`, "Ocultar", "tp-link tp-group-btn")),
        list);
    }));
  }

  // --- the window, drawn at the pixels of its container -----------------------
  function drawRuler(svg, score, seller, animate) {
    const W = Math.max(280, Math.floor(svg.parentNode.getBoundingClientRect().width));
    const narrow = W < 700;
    const roomy = W >= 1100; // the "cerca de N em cada 100" notes fit under every tick
    const table = score.meta.time_table;
    const longest = score.meta.window.longest_win_days;
    const pad = Math.max(16, Math.round(W * 0.04));
    const outW = narrow ? 76 : Math.max(150, Math.round(W * 0.15));
    const x0 = pad + 4, x1 = W - pad - outW;
    const x = (d) => x0 + (Math.min(d, longest) / longest) * (x1 - x0);
    const deals = [...seller.alive].sort((a, b) => a.days_open - b.days_open || (a.id < b.id ? -1 : 1));
    const r = deals.length > 45 ? 4 : 6;
    const levels = [];
    const placed = deals.map((d) => {
      const cx = x(d.days_open);
      let level = 0;
      while (levels[level] !== undefined && cx - levels[level] < 2 * r + 2) level += 1;
      levels[level] = cx;
      return { d, cx, level };
    });
    const top = Math.max(44, 18 + levels.length * (2 * r + 3));
    const axisY = top + 6;
    const H = axisY + (roomy ? 66 : 30);
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.setAttribute("width", W);
    svg.setAttribute("height", H);
    svg.classList.toggle("tp-still", !animate);
    const cooling = seller.alive.filter((d) => d.cooling).length;
    svg.setAttribute("aria-label",
      `Régua da janela de ${longest} dias: ${count(seller.alive.length, "negócio vivo", "negócios vivos", "nenhum negócio vivo")}, ` +
      `${count(cooling, "esfriando", "esfriando", "nenhum esfriando")}, ` +
      `${count(seller.headline.clean, "fora da janela", "fora da janela", "nenhum fora da janela")}. ` +
      (table.exists ? "De cada 100 negócios que chegaram abertos a cada idade, cerca de quantos foram ganhos depois: " +
        table.rows.map((row) => `${row.reached_days} dias, ${row.won_per_100}`).join("; ") + ". " : "") +
      "A lista de vivos abaixo traz os mesmos negócios.");
    const kids = [];
    // the zone after 90 days: tinted AND hatched, so it does not depend on colour
    const zx = x(score.meta.cooling_after_days);
    kids.push(s("rect", { class: "tp-r-zone", x: zx, y: 6, width: x1 - zx, height: axisY - 6 }));
    for (let hx = zx + 6; hx < x1; hx += 9) {
      kids.push(s("line", { class: "tp-r-hatch", x1: hx, y1: axisY, x2: Math.min(hx + 5, x1), y2: axisY - 5 }));
    }
    kids.push(s("text", { x: zx + 6, y: 20, "font-size": 12.5 }, narrow ? "esfriando" : "esfriando: mais de 90 dias aberto"));
    kids.push(s("line", { class: "tp-r-axis", x1: x0, y1: axisY, x2: x1, y2: axisY }));
    kids.push(s("line", { class: "tp-r-edge", x1: x1, y1: 4, x2: x1, y2: axisY + 8 }));
    const rows = table.exists ? table.rows : [0, 30, 60, 90, 120, longest].map((a) => ({ reached_days: a }));
    for (const row of rows) {
      const tx = x(row.reached_days);
      const last = row.reached_days === longest;
      const anchor = row.reached_days === 0 ? "start" : last ? "end" : "middle";
      kids.push(s("line", { class: "tp-r-tick", x1: tx, y1: axisY, x2: tx, y2: axisY + 6 }));
      if (narrow && row.reached_days === 120) continue; // no room beside the last label
      kids.push(s("text", { class: "tp-r-strong", x: tx, y: axisY + 21, "text-anchor": anchor, "font-size": 13 },
        narrow ? String(row.reached_days) : `${row.reached_days} ${last ? "dias" : row.reached_days === 0 ? "dias" : ""}`.trim()));
      if (roomy && table.exists) {
        kids.push(s("text", { x: tx, y: axisY + 39, "text-anchor": anchor, "font-size": 12.5 }, `cerca de ${row.won_per_100}`));
        kids.push(s("text", { x: tx, y: axisY + 54, "text-anchor": anchor, "font-size": 12.5 }, "em cada 100"));
      }
    }
    if (roomy && !table.exists) {
      kids.push(s("text", { x: (x0 + x1) / 2, y: axisY + 46, "text-anchor": "middle", "font-size": 13 },
        "Sem histórico suficiente nesta data para dizer o que aconteceu em cada idade."));
    }
    // beyond the edge
    const ox = x1 + 10;
    kids.push(s("text", { class: "tp-r-strong", x: ox, y: axisY - 22, "font-size": 13 }, narrow ? "fora" : "fora da janela"));
    kids.push(s("text", { x: ox, y: axisY - 6, "font-size": 12.5 },
      narrow ? `${num(seller.headline.clean)}` : count(seller.headline.clean, "para limpar", "para limpar", "nada para limpar")));
    if (!deals.length) {
      kids.push(s("text", { x: x0 + 2, y: axisY - 14, "font-size": 13 }, "Nenhum negócio vivo nesta data."));
    }
    // the pile outside the window: one small open square per deal to clean, when they fit
    const cell = 8, perCol = 4, room = Math.floor((W - pad - ox) / cell) * perCol;
    if (!narrow && seller.headline.clean && seller.headline.clean <= room) {
      for (let i = 0; i < seller.headline.clean; i += 1) {
        kids.push(s("rect", { class: "tp-r-out", x: ox + Math.floor(i / perCol) * cell, y: axisY + 12 + (i % perCol) * cell, width: 5, height: 5 }));
      }
    }
    placed.forEach(({ d, cx, level }, i) => {
      const cy = axisY - r - 5 - level * (2 * r + 3);
      const title = s("title", {}, `${d.product} · aberto há ${d.days_open} dias · ${d.days_left === 0 ? "último dia na janela" : "faltam " + d.days_left + " dias"}`);
      const shape = d.cooling
        ? s("path", { d: `M${cx} ${cy - r - 1}L${cx + r + 1} ${cy}L${cx} ${cy + r + 1}L${cx - r - 1} ${cy}Z`, class: "tp-mark tp-m-frio" }, title)
        : s("circle", { cx, cy, r, class: "tp-mark tp-m-vivo" }, title);
      shape.style.setProperty("--i", Math.min(i, 30));
      shape.addEventListener("click", () => focusDeal(d.id));
      kids.push(shape);
    });
    svg.replaceChildren(...kids);
    svg.closest(".tp-window").classList.toggle("tp-narrow", narrow);
    svg.closest(".tp-window").classList.toggle("tp-roomy", roomy); // below 1100 px the notes move to a list the user opens
  }
  function focusDeal(id) {
    shown.alive = true;
    const go = () => {
      const row = $("deal-" + id);
      if (!row) return;
      row.scrollIntoView({ block: "center", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
      row.classList.add("tp-flash");
      setTimeout(() => row.classList.remove("tp-flash"), 1600);
    };
    if ($("deal-" + id)) go(); else render().then(go);
  }
  function windowSection(score, seller, animate) {
    const table = score.meta.time_table;
    const w = score.meta.window;
    const svg = s("svg", { class: "tp-ruler", role: "img" });
    const list = table.exists ? h("ol", { class: "tp-table", id: "tp-table" }, table.rows.map((row) => h("li", {},
      h("span", {}, row.reached_days === 0 ? "Engajados (0 dias)" : `Abertos aos ${row.reached_days} dias`),
      h("span", {}, `cerca de ${row.won_per_100} em cada 100 ganhos depois`)))) : null;
    const section = h("section", { class: "tp-window", "aria-labelledby": "tp-window-h" },
      h("h2", { id: "tp-window-h" }, `A janela: ${w.longest_win_days} dias, ou o fim do trimestre seguinte ao do engajamento`),
      h("p", { class: "tp-note tp-wide-only" }, table.exists
        ? `Sob cada idade: de cada 100 negócios que chegaram abertos até ali, cerca de quantos foram ganhos depois (conta de ${brDate(table.counted_on)}, com ${num(table.deals)} negócios que já tinham tido tempo de fechar).`
        : "Sem histórico suficiente nesta data: nenhum negócio tinha tido tempo de fechar, então a régua mostra só as idades."),
      svg,
      h("p", { class: "tp-legend" },
        h("span", {}, s("svg", { width: 14, height: 14, "aria-hidden": "true" }, s("circle", { cx: 7, cy: 7, r: 6, fill: "var(--vivo)" })), "negócio vivo"),
        h("span", {}, s("svg", { width: 14, height: 14, "aria-hidden": "true" }, s("path", { d: "M7 0L14 7L7 14L0 7Z", fill: "var(--frio)" })), "vivo, esfriando"),
        h("span", {}, s("svg", { width: 14, height: 14, "aria-hidden": "true" }, s("line", { x1: 7, y1: 0, x2: 7, y2: 14, stroke: "var(--limpar)", "stroke-width": 2, "stroke-dasharray": "4 3" })), "fim da janela"),
        h("span", {}, "A posição de cada marca é a idade do negócio: não é ordem nem chance.")),
      h("p", { class: "tp-note tp-narrow-only" }, table.exists
        ? [toggle("table", list, "Ver o que aconteceu em cada idade", "Ocultar a conta por idade"), ` (conta de ${brDate(table.counted_on)})`]
        : "Sem histórico suficiente nesta data para dizer o que aconteceu em cada idade."),
      list);
    let lastW = 0;
    const draw = (anim) => {
      const wNow = Math.floor(section.getBoundingClientRect().width);
      if (wNow === lastW || wNow === 0) return;
      lastW = wNow;
      drawRuler(svg, score, seller, anim);
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
  function sellerLead(sel, meta) {
    const hd = sel.headline;
    if (meta.past) {
      const a = sel.after;
      if (!hd.alive && !hd.clean) return "Nada estava aberto com data naquele dia.";
      return `Depois, até ${brDate(meta.outcomes_until)}: ` +
        (hd.alive ? `${pl(hd.alive, "do", "dos")} ${count(hd.alive, "vivo", "vivos", "")}, ${count(a.alive_won, "foi ganho", "foram ganhos", "nenhum foi ganho")} (${money(a.alive_won_value)}), ` +
          `${count(a.alive_lost, "perdido", "perdidos", "nenhum perdido")} e ${count(a.alive_open, "seguia aberto", "seguiam abertos", "nenhum seguia aberto")}. ` : "") +
        (hd.clean ? `${pl(hd.clean, "Do", "Dos")} ${num(hd.clean)} para limpar, ${count(a.clean_won, "foi ganho", "foram ganhos", "nenhum foi ganho")}.` : "");
    }
    if (hd.alive) return "Comece pelos vivos, do maior valor de tabela para o menor.";
    if (hd.queue) return "Nenhum negócio vivo: comece pela fila.";
    if (hd.clean) return "Nenhum vivo e nada na fila: a segunda é para limpar e abrir negócios novos.";
    return "Nenhum negócio aberto em seu nome nestes dados.";
  }
  function briefing(sel) {
    const body = part("briefing:" + sel.seller, "body");
    if (!body) return null;
    const btn = h("button", { type: "button", class: "tp-btn" }, "Copiar o briefing");
    btn.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(body); btn.textContent = "Copiado"; } catch (e) { btn.textContent = "Selecione o texto e copie"; }
    });
    const inner = h("div", { class: "tp-brief-body", id: "tp-brief-body" }, h("p", {}, body), btn, aiNote("briefing:" + sel.seller));
    const section = h("section", { class: "tp-brief", "aria-labelledby": "tp-brief-h" },
      h("h2", { id: "tp-brief-h" }, "Briefing de segunda"),
      h("p", { class: "tp-narrow-only" }, toggle("brief", inner, "Ler o briefing", "Fechar o briefing")),
      inner);
    inner.hidden = false; // on a wide screen it is always open; the narrow rule hides it until asked
    section.classList.toggle("tp-open", !!shown.brief);
    section.addEventListener("click", () => section.classList.toggle("tp-open", !!shown.brief));
    return section;
  }
  function aiNote(id) {
    const t = texts && texts.byId.get(id);
    if (!t) return null;
    const p = t.provenance || {};
    return h("p", { class: "tp-ai" },
      `Texto redigido por IA${p.model ? " (" + p.model + ")" : ""} a partir dos fatos desta tela; os números e os nomes foram preenchidos pelo código.`);
  }
  function blockHead(n, title, def, sum, kids) {
    return h("div", { class: "tp-block-head" },
      h("h2", {}, title, n === null ? null : h("span", { class: "tp-n" }, n)),
      def ? h("p", { class: "tp-def" }, def) : null,
      sum ? h("p", { class: "tp-block-sum" }, sum) : null,
      kids);
  }
  function renderSeller(score, animate) {
    const meta = score.meta;
    const sel = score.sellers.find((x) => x.seller === state.seller);
    const hd = sel.headline;
    const ev = index.evidence;
    const anyAi = sel.alive.some((d) => part("deal:" + d.id, "next_step"));
    const alive = h("section", { class: "tp-block tp-vivos", "aria-label": "Vivos" },
      blockHead(num(hd.alive), "Vivos",
        `Dentro da janela em que negócios já foram ganhos: até ${meta.window.longest_win_days} dias abertos e antes do prazo do trimestre.`,
        hd.alive ? `${money(hd.alive_value)} em valor de tabela` + (hd.cooling ? ` · ${num(hd.cooling)} esfriando (há mais de ${meta.cooling_after_days} dias aberto)` : "") : null,
        hd.alive ? h("p", { class: "tp-note" },
          `Ordem: valor de tabela (o preço de lista do produto; negócio aberto não tem valor de fechamento); no empate, mais dias restantes. ` +
          `Com ${index.value_note.list_prices} preços de tabela é quase ordem por produto, e ela não foi confirmada em datas novas.`) : null),
      hd.alive
        ? [h("ol", { class: "tp-rows" }, visible("alive", sel.alive, SHOW.alive).map((d) => aliveRow(d, meta.time_table))),
          moreButton("alive", sel.alive.length, SHOW.alive, "vivos"),
          anyAi ? h("p", { class: "tp-ai" }, "O próximo passo é escolhido por regra; a frase que o acompanha foi redigida por IA, com os números e os nomes preenchidos pelo código.") : null]
        : h("p", { class: "tp-empty" }, meta.past ? "Nenhum negócio vivo naquela data."
          : hd.queue ? "Nenhum negócio vivo. Comece pela fila." : "Nenhum negócio vivo."));
    const queue = meta.past
      ? h("section", { class: "tp-block tp-fila", "aria-label": "Fila para engajar" },
        blockHead(null, "Fila para engajar",
          "A fila não pode ser reconstruída no passado: o CRM não guarda a data em que um negócio entrou.", null, null))
      : h("section", { class: "tp-block tp-fila", "aria-label": "Fila para engajar" },
        blockHead(num(hd.queue), "Fila para engajar",
          "Negócios ainda sem data de engajamento. Lista por valor de tabela: nada mais nos dados ordena estes negócios.",
          hd.queue ? `${money(hd.queue_value)} em valor de tabela · próximo passo de todos: engajar e registrar a data` : null, null),
        hd.queue ? grouped("fila", sel.queue, meta.window) : h("p", { class: "tp-empty" }, "Nenhum negócio na fila."));
    const clean = h("section", { class: "tp-block tp-limpar", "aria-label": "Para limpar" },
      blockHead(num(hd.clean), "Para limpar",
        `Fora da janela: mais de ${meta.window.longest_win_days} dias abertos, ou prazo do trimestre vencido.`,
        hd.clean ? `${money(hd.clean_value)} em valor de tabela` : null,
        hd.clean ? [
          h("p", { class: "tp-evidence" }, "Nenhum negócio foi ganho depois de sair da janela: ",
            h("strong", {}, `${num(ev.won_after)} em ${num(ev.distinct_deals_past_window)}`),
            ` negócios distintos, nas ${num(ev.cuts)} datas medidas.`),
          h("p", { class: "tp-note" }, "Ação: encerrar no CRM e tirar da segunda-feira. Os dados não dizem por que estes negócios estão parados."),
        ] : null),
      hd.clean ? grouped("limpar", sel.clean, meta.window) : h("p", { class: "tp-empty" }, "Nada para limpar."));
    // the block the seller works on first takes the wide column; the other two share the rail
    const order = hd.alive ? [alive, queue, clean] : hd.queue ? [queue, alive, clean] : [clean, alive, queue];
    const brief = meta.past ? null : briefing(sel);
    return [
      h("div", { class: "tp-top" + (brief ? " tp-has-brief" : "") },
        h("div", { class: "tp-head" }, whenLine(meta), h("h1", { class: "tp-headline" }, sellerHeadline(sel, meta.past)),
          h("p", { class: "tp-lead" }, sellerLead(sel, meta))),
        brief),
      meta.past ? pastBanner(meta) : null,
      windowSection(score, sel, animate),
      h("div", { class: "tp-blocks" }, h("div", { class: "tp-main" }, order[0]), h("div", { class: "tp-side" }, order[1], order[2])),
    ];
  }

  // --- manager ---------------------------------------------------------------
  function renderManager(score) {
    const meta = score.meta;
    const team = score.team;
    const scope = state.manager ? team.by_manager.find((m) => m.manager === state.manager)
      : state.region ? team.by_region.find((g) => g.region === state.region) : team.total;
    const label = state.manager ? `O time de ${state.manager}` : state.region ? `A regional ${state.region}` : "O time inteiro";
    const rows = team.by_seller.filter((x) => (!state.region || x.region === state.region) && (!state.manager || x.manager === state.manager));
    const scale = Math.max(1, ...rows.map((x) => Math.max(x.alive_value, x.clean_value)));
    const headline = [`${label} tem `,
      h("span", { class: "tp-k-vivo" }, count(scope.alive, "vivo", "vivos", "nenhum vivo"), h("i", {}, meta.past ? "" : ",")),
      meta.past ? " e " : [" ", h("span", { class: "tp-k-fila" }, scope.queue ? `${num(scope.queue)} na fila` : "nenhum na fila"), " e "],
      h("span", { class: "tp-k-limpar" }, scope.clean ? `${num(scope.clean)} para limpar` : "nada para limpar", h("i", {}, "."))];
    const body = state.manager ? part("manager:" + state.manager, "body") : null;
    const line = (x) => `${count(x.alive, "vivo", "vivos", "nenhum vivo")} (${money(x.alive_value)})` +
      (meta.past ? "" : ` · ${num(x.queue)} na fila`) + ` · ${num(x.clean)} para limpar (${money(x.clean_value)})`;
    const bar = (cls, value, text) => h("div", { class: "tp-bar-line" },
      h("div", { class: "tp-bar-track", "aria-hidden": "true" },
        value ? h("div", { class: "tp-bar-fill " + cls, style: `width:${((value / scale) * 100).toFixed(2)}%` }) : null),
      h("span", { class: value ? null : "tp-zero" }, text));
    const extra = (x) => [x.cooling ? `${num(x.cooling)} esfriando` : null, !meta.past && x.queue ? `${num(x.queue)} na fila` : null,
      x.alive === 0 ? "sem nenhum vivo" : null].filter(Boolean).join(" · ");
    const sellerRow = (x) => h("li", { class: "tp-trow" },
      h("div", { class: "tp-who" },
        h("button", { type: "button", onclick: () => { state.view = "vendedor"; state.seller = x.seller; render(true); } }, x.seller),
        extra(x) ? h("span", { class: "tp-cap tp-flag" }, extra(x)) : null),
      h("div", { class: "tp-bars" },
        bar("tp-b-vivo", x.alive_value, `${count(x.alive, "vivo", "vivos", "nenhum vivo")} · ${money(x.alive_value)}`),
        bar("tp-b-limpar", x.clean_value, `${num(x.clean)} para limpar · ${money(x.clean_value)}`)));
    const managers = team.by_manager.filter((m) => (!state.region || m.region === state.region) && (!state.manager || m.manager === state.manager));
    const brief = body && !meta.past
      ? h("section", { class: "tp-brief" }, h("h2", {}, "Resumo do gestor"), h("p", {}, body), aiNote("manager:" + state.manager)) : null;
    return [
      h("div", { class: "tp-top" + (brief ? " tp-has-brief" : "") },
        h("div", { class: "tp-head" }, whenLine(meta), h("h1", { class: "tp-headline" }, headline),
          h("p", { class: "tp-lead" },
            `${num(scope.sellers_without_alive)} de ${num(scope.sellers)} ${pl(scope.sellers, "vendedor", "vendedores")} ${pl(scope.sellers_without_alive, "não tem", "não têm")} nenhum negócio vivo. ` +
            `Valor de tabela vivo: ${money(scope.alive_value)}; fora da janela, para limpar: ${money(scope.clean_value)}.`)),
        brief),
      meta.past ? pastBanner(meta) : null,
      state.manager ? null : h("section", { class: "tp-regions", "aria-label": "Por regional" },
        team.by_region.filter((g) => !state.region || g.region === state.region).map((g) => h("div", { class: "tp-region" },
          h("h3", {}, g.region), h("p", {}, line(g)),
          h("p", {}, `${num(g.sellers_without_alive)} de ${num(g.sellers)} vendedores sem nenhum vivo`)))),
      h("section", { class: "tp-team", "aria-labelledby": "tp-team-h" },
        h("h2", { id: "tp-team-h" }, "Valor vivo contra valor parado, por vendedor"),
        h("p", { class: "tp-note" }, `Só fatos: a barra cheia é o valor de tabela dos negócios vivos; a hachurada, o dos que estão fora da janela, para limpar. Mesma escala em todas as linhas: a largura inteira vale ${money(scale)}. Nada aqui diz por que um negócio parou.`),
        managers.map((m) => h("div", { class: "tp-mgr" },
          h("h3", {}, `${m.manager} · ${m.region}`),
          h("p", { class: "tp-mgr-sum" }, line(m)),
          h("ol", {}, rows.filter((x) => x.manager === m.manager).map(sellerRow))))),
    ];
  }

  // --- render ----------------------------------------------------------------
  async function render(animate) {
    const tok = ++run;
    syncFilters();
    writeHash();
    const score = await getScore(state.monday);
    if (tok !== run) return; // a newer action took over: write nothing
    const app = $("app");
    app.replaceChildren(...(state.view === "gestor" ? renderManager(score) : renderSeller(score, !!animate))
      .flat().filter(Boolean));
    document.title = (state.view === "gestor" ? "Gestor" : state.seller) + " · Segunda-feira";
  }

  function setTheme(dark, keep) {
    document.documentElement.toggleAttribute("data-tema", false);
    if (dark) document.documentElement.setAttribute("data-tema", "escuro");
    document.querySelector('meta[name="color-scheme"]').setAttribute("content", dark ? "only dark" : "only light");
    $("theme").setAttribute("aria-pressed", String(dark));
    $("theme").textContent = dark ? "Tema claro" : "Tema escuro";
    if (keep) { try { localStorage.setItem("tp-tema", dark ? "escuro" : "claro"); } catch (e) { /* private mode */ } }
  }

  async function start() {
    let saved = null;
    try { saved = localStorage.getItem("tp-tema"); } catch (e) { /* private mode */ }
    setTheme((query.get("tema") || saved) === "escuro", false);
    // two compositions for the owner to choose: wide column plus rail (default) or stacked (?comp=pilha)
    if (query.get("comp") !== "pilha") document.body.classList.add("tp-comp-trilho");
    try {
      [index, texts] = await Promise.all([getJSON("out/index.json"), loadTexts()]);
    } catch (e) {
      $("app").replaceChildren(h("h1", { class: "tp-headline" }, "Não encontrei os arquivos do score."),
        h("p", { class: "tp-lead", style: "padding:0 var(--gap)" }, "Rode python3 run.py --port 8000 na pasta solution e abra o endereço que ele mostrar."));
      return;
    }
    state.seller = index.default_seller;
    state.monday = index.default_monday;
    readHash();
    if (!index.mondays.some((m) => m.monday === state.monday)) state.monday = index.default_monday;
    $("f-region").addEventListener("change", (e) => { state.region = e.target.value; render(true); });
    $("f-manager").addEventListener("change", (e) => { state.manager = e.target.value; render(true); });
    $("f-seller").addEventListener("change", (e) => { state.seller = e.target.value; for (const k in shown) delete shown[k]; render(true); });
    $("f-monday").addEventListener("change", (e) => { state.monday = e.target.value; for (const k in shown) delete shown[k]; render(true); });
    $("view-seller").addEventListener("click", () => { state.view = "vendedor"; render(true); });
    $("view-manager").addEventListener("click", () => { state.view = "gestor"; render(true); });
    $("theme").addEventListener("click", () => setTheme(!document.documentElement.hasAttribute("data-tema"), true));
    await render(true);
  }
  start();
})();

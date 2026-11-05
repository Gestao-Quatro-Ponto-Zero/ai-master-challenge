"use strict";

const DATA = window.LEAD_DATA;
const REPLAY = window.LEAD_REPLAY || [];
const HISTORY = window.LEAD_HISTORY || { deals: [], actions: [], snapshots: [] };
const PAGE_SIZE = 30;
const HIGHLIGHTED_DEALS = 3;
const TEAM_LIST_SIZE = 20;
const HOURS_PER_PERSON_WEEK = 40;
const DEFAULT_REPLAY_DATE = "2017-08-07"; // mid-quarter, when every age band is active
const DEFAULT_CALCULATOR = { weekly: 5, cleanup: 3 };

const STORAGE = {
  agent: "focoSemana.agent",
  decisions: "focoSemana.decisions",
  focusActions: "focoSemana.focusActions",
  calculator: "focoSemana.calculator",
};

const ICON_PATHS = {
  foco: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/>',
  decidir: '<path d="M12 4v4M12 16v4M4 12h4M16 12h4"/><circle cx="12" cy="12" r="4"/>',
  prospeccao: '<circle cx="11" cy="11" r="6"/><path d="m20 20-4.5-4.5"/>',
  revisar: '<path d="M5 12.5 10 17l9-10"/>',
  equipe: '<circle cx="9" cy="9" r="3.5"/><path d="M3 20c.6-3.5 3-5.5 6-5.5s5.4 2 6 5.5M16 6a3.5 3.5 0 0 1 0 6.5M18 15c1.6.8 2.6 2.6 3 5"/>',
  tempo: '<circle cx="12" cy="12" r="8"/><path d="M12 7.5V12l3 2"/>',
  como: '<circle cx="12" cy="12" r="8"/><path d="M12 11v5M12 8h.01"/>',
};

const TABS = [
  { id: "foco", label: "Minha semana" },
  { id: "decidir", label: "Decidir" },
  { id: "prospeccao", label: "Prospecção" },
  { id: "revisar", label: "Revisar" },
  { id: "equipe", label: "Equipe" },
  { id: "tempo", label: "Máquina do tempo" },
  { id: "como", label: "Como funciona" },
];

const CURRENT_SNAPSHOT = {
  date: DATA.asOf,
  week: DATA.quarterWeek,
  maxCycle: DATA.maxCycle,
  engaged: DATA.engaged,
  prospecting: DATA.prospecting,
  historic: false,
};
const snapshotCache = new Map();

/** Expands a past Monday from history.js. Those deals carry no account: see build_history. */
function historicSnapshot(entry) {
  if (!snapshotCache.has(entry.date)) {
    const engaged = entry.rows.map(([index, age, score, valuePts, timingPts, probability, zone, action]) => {
      const [id, agent, product, price, engageDate] = HISTORY.deals[index];
      return {
        id, agent, product, price, engageDate, age, score, valuePts, timingPts, probability, zone,
        account: null,
        sector: null,
        queue: age > entry.maxCycle ? "decidir" : "foco",
        action: HISTORY.actions[action],
        pastDeals: 0,
        pastWins: 0,
      };
    });
    snapshotCache.set(entry.date, { date: entry.date, week: entry.week, maxCycle: entry.maxCycle, engaged, prospecting: [], historic: true });
  }
  return snapshotCache.get(entry.date);
}

function snapshot() {
  const entry = HISTORY.snapshots.find((item) => item.date === state.date);
  return entry ? historicSnapshot(entry) : CURRENT_SNAPSHOT;
}

function zones() {
  return [
    { id: "novo", label: "Deal novo", from: 0, to: 14 },
    { id: "intermediario", label: "Em andamento", from: 15, to: 44 },
    { id: "janela", label: "Janela de fechamento", from: 45, to: 119 },
    { id: "prazo_final", label: "Prazo final", from: 120, to: snapshot().maxCycle },
  ];
}

const teamByAgent = new Map(DATA.team.map((member) => [member.agent, member]));
const state = {
  region: "",
  manager: "",
  agent: readStorage(STORAGE.agent, ""),
  tab: "foco",
  date: DATA.asOf,
  sort: "padrao",
  limit: PAGE_SIZE,
  decisions: readObject(STORAGE.decisions),
  focusActions: readObject(STORAGE.focusActions),
  calculator: { ...DEFAULT_CALCULATOR, ...readObject(STORAGE.calculator) },
  skipped: new Set(),
  lastDecision: null,
  replayIndex: Math.max(0, REPLAY.findIndex((monday) => monday.date === DEFAULT_REPLAY_DATE)),
  revealed: false,
};
if (!teamByAgent.has(state.agent)) state.agent = "";

function readStorage(key, fallback) {
  try {
    const value = localStorage.getItem(key);
    return value === null ? fallback : value;
  } catch {
    return fallback;
  }
}

function writeStorage(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch {
    // Private windows can block storage. The page keeps working for this visit.
  }
}

function readObject(key) {
  try {
    const parsed = JSON.parse(readStorage(key, "{}"));
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (char) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]
  ));
}

const money = (value) => "US$ " + Math.round(value).toLocaleString("pt-BR");
const count = (value) => value.toLocaleString("pt-BR");
const plural = (n, one, many) => `${count(n)} ${n === 1 ? one : many}`;
const sumPrice = (deals) => deals.reduce((total, deal) => total + deal.price, 0);
const shortDate = (date) => new Date(`${date}T12:00:00`).toLocaleDateString("pt-BR");

function compactMoney(value) {
  if (Math.abs(value) >= 1000000) return `US$ ${(value / 1000000).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} mi`;
  if (Math.abs(value) >= 1000) return `US$ ${Math.round(value / 1000).toLocaleString("pt-BR")} mil`;
  return money(value);
}

function matchesFilters(agent) {
  const member = teamByAgent.get(agent);
  if (!member) return false;
  if (state.agent) return agent === state.agent;
  if (state.manager) return member.manager === state.manager;
  if (state.region) return member.region === state.region;
  return true;
}

function selection() {
  const current = snapshot();
  const engaged = current.engaged.filter((deal) => matchesFilters(deal.agent));
  return {
    foco: engaged.filter((deal) => deal.queue === "foco"),
    decidir: engaged.filter((deal) => deal.queue === "decidir").sort((a, b) => b.price - a.price || b.age - a.age),
    prospecting: current.prospecting.filter((deal) => matchesFilters(deal.agent)),
  };
}

// Marks belong to the current pipeline. Past dates are for reading only.
const isHandled = (deal) => !snapshot().historic && Boolean(state.focusActions[deal.id]);
const isDecided = (deal) => !snapshot().historic && Boolean(state.decisions[deal.id]);
const pendingFocus = (sel) => sel.foco.filter((deal) => !isHandled(deal));
const undecided = (sel) => sel.decidir.filter((deal) => !isDecided(deal));

function sortedByDate(deals) {
  if (state.sort === "padrao") return deals;
  const direction = state.sort === "antigos" ? 1 : -1;
  return [...deals].sort((a, b) => direction * a.engageDate.localeCompare(b.engageDate) || a.id.localeCompare(b.id));
}

function sortControl(defaultLabel) {
  const option = (value, label) => `<option value="${value}" ${state.sort === value ? "selected" : ""}>${label}</option>`;
  return `<label class="inline-label sort-bar">Ordenar por <select id="sort-deals">
    ${option("padrao", defaultLabel)}
    ${option("antigos", "Entrada em Engaging: mais antigos")}
    ${option("recentes", "Entrada em Engaging: mais recentes")}
  </select></label>`;
}

function historyBanner() {
  const current = snapshot();
  if (!current.historic) return "";
  const hasOutcome = REPLAY.some((monday) => monday.date === current.date);
  return `
    <div class="history-banner">
      <p><strong>Pipeline como estava em ${shortDate(current.date)}</strong>, com o score calculado só com o que se sabia naquele dia. Datas passadas são só para consulta, e a conta fica oculta porque revelaria o resultado.</p>
      <div class="row-actions">
        ${hasOutcome ? `<button class="action-button" data-go="tempo">Ver o que aconteceu</button>` : ""}
        <button class="action-button primary" data-action="back-to-today">Voltar para ${shortDate(DATA.asOf)}</button>
      </div>
    </div>`;
}

/** Replay result for the chance band, because high predictions ran above reality. */
function observedChance(probability) {
  const limits = [0.05, 0.1, 0.2, 0.3, Infinity];
  const index = limits.findIndex((limit) => probability <= limit);
  return Math.round(DATA.backtest.calibration[index].real * 100);
}

/* Sidebar */

function renderHeader() {
  const current = snapshot();
  document.getElementById("as-of").textContent =
    `Segunda, ${shortDate(current.date)} · semana ${current.week} do trimestre`;
}

function renderDateFilter() {
  const option = (date, label) => `<option value="${date}">${label}</option>`;
  const past = [...HISTORY.snapshots].reverse().map((item) => option(item.date, `${shortDate(item.date)} · semana ${item.week}`));
  const select = document.getElementById("filter-date");
  select.innerHTML = [option(DATA.asOf, `${shortDate(DATA.asOf)} · atual`), ...past].join("");
  select.value = state.date;
}

function fillSelect(id, emptyLabel, values, selected) {
  const select = document.getElementById(id);
  const options = [`<option value="">${emptyLabel}</option>`]
    .concat(values.map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`));
  select.innerHTML = options.join("");
  select.value = selected;
}

function renderFilters() {
  const unique = (items) => [...new Set(items)].sort((a, b) => a.localeCompare(b, "pt-BR"));
  const inRegion = DATA.team.filter((member) => !state.region || member.region === state.region);
  const inManager = inRegion.filter((member) => !state.manager || member.manager === state.manager);
  fillSelect("filter-region", "Todas", unique(DATA.team.map((member) => member.region)), state.region);
  fillSelect("filter-manager", "Todos", unique(inRegion.map((member) => member.manager)), state.manager);
  fillSelect("filter-agent", "Todos", unique(inManager.map((member) => member.agent)), state.agent);
}

function reviewCount(sel) {
  return sel.foco.filter(isHandled).length + sel.decidir.filter(isDecided).length;
}

function renderTabs(sel) {
  const counts = {
    foco: pendingFocus(sel).length,
    decidir: undecided(sel).length,
    prospeccao: sel.prospecting.length,
    revisar: reviewCount(sel),
  };
  document.getElementById("tabs").innerHTML = TABS.map((tab) => {
    const badge = tab.id in counts ? `<span class="nav-count">${count(counts[tab.id])}</span>` : "";
    return `<button class="tab" role="tab" data-tab="${tab.id}" aria-selected="${state.tab === tab.id}">
      <svg viewBox="0 0 24 24" aria-hidden="true">${ICON_PATHS[tab.id]}</svg>${tab.label}${badge}
    </button>`;
  }).join("");
}

/* Shared pieces */

function accountLabel(deal) {
  return deal.account ? escapeHtml(deal.account) : "Conta em branco";
}

function dealName(deal) {
  const product = escapeHtml(deal.product);
  return snapshot().historic ? product : `${product} · ${accountLabel(deal)}`;
}

function queueBar(sel, rowsAlign) {
  const parts = [
    { key: "live", label: "Vivos", deals: sel.foco },
    { key: "stale", label: "Parados", deals: sel.decidir },
    { key: "prospect", label: "Em prospecção", deals: sel.prospecting },
  ];
  const total = parts.reduce((all, part) => all + sumPrice(part.deals), 0);
  const stack = parts
    .filter((part) => part.deals.length > 0)
    .map((part) => {
      const value = sumPrice(part.deals);
      const tip = `${part.label}: ${plural(part.deals.length, "deal", "deals")}, ${money(value)}`;
      return `<i class="${part.key}" style="flex:${value} 1 0" data-tip="${escapeHtml(tip)}"></i>`;
    }).join("");
  const legend = parts.map((part) => `
    <div class="legend-row">
      <span class="swatch ${part.key}"></span>${part.label}: ${count(part.deals.length)}
      <b>${compactMoney(sumPrice(part.deals))}</b>
    </div>`).join("");
  return { total, html: `<div class="stack" role="img" aria-label="Divisão do valor de tabela por fila">${stack}</div><div class="legend ${rowsAlign || ""}">${legend}</div>` };
}

function lifeTrack(deal) {
  const { maxCycle } = snapshot();
  const allZones = zones();
  const zone = allZones.find((item) => item.id === deal.zone);
  const name = zone ? zone.label : "Parado";
  const segments = allZones.map((item) => `<i class="zone-${item.id}" style="flex:${item.to - item.from + 1} 1 0"></i>`).join("");
  const position = Math.min(deal.age, maxCycle) / maxCycle * 100;
  return `
    <div class="life">
      <div class="life-label"><b>${name}</b><span>${deal.age} de ${maxCycle} dias · desde ${shortDate(deal.engageDate)}</span></div>
      <div class="track" role="img" aria-label="${name}, ${deal.age} dias em Engaging">
        ${segments}<span class="marker" style="left:${position}%"></span>
      </div>
    </div>`;
}

function ring(score) {
  return `<div class="ring" style="--score:${score}" role="img" aria-label="Score ${score}"><span>${score}</span></div>`;
}

function whyDetails(deal) {
  const row = (label, value, max) => `
    <div class="points">
      <span>${label}</span>
      <span class="meter"><i style="width:${(value / max) * 100}%"></i></span>
      <span>${value} de ${max}</span>
    </div>`;
  return `
    <details class="why">
      <summary>Por que este score?</summary>
      <div class="why-body">
        ${row("Valor", deal.valuePts, DATA.maxValuePoints)}
        ${row("Momento", deal.timingPts, DATA.maxTimingPoints)}
        <p style="margin:6px 0 0">Valor vem do preço de tabela. Momento vem da idade do deal e da semana do trimestre: deals parecidos foram ganhos em 30 dias em cerca de ${observedChance(deal.probability)} de cada 100 casos.</p>
      </div>
    </details>`;
}

function contextChips(deal) {
  const chips = [];
  if (!snapshot().historic) {
    const stats = DATA.productStats[deal.product];
    if (stats) chips.push(`<span class="chip">Se ganhar: cerca de ${money(stats.median)}</span>`);
    if (!deal.account) chips.push(`<span class="chip attention">Preencha a conta no CRM</span>`);
    else if (deal.pastDeals > 0) chips.push(`<span class="chip">Histórico da conta: ${deal.pastWins} de ${deal.pastDeals} ganhos, ${compactMoney(DATA.accounts[deal.account].wonRevenue)}</span>`);
  }
  if (!state.agent) chips.push(`<span class="chip">${escapeHtml(deal.agent)}</span>`);
  return chips.length ? `<div class="chips">${chips.join("")}</div>` : "";
}

function companySize(revenueInMillions) {
  if (revenueInMillions >= 1000) return `US$ ${(revenueInMillions / 1000).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} bi`;
  return `US$ ${Math.round(revenueInMillions).toLocaleString("pt-BR")} mi`;
}

function daysSince(date) {
  const milliseconds = new Date(`${snapshot().date}T12:00:00`) - new Date(`${date}T12:00:00`);
  return Math.round(milliseconds / 86400000);
}

function listItems(items) {
  return `<ul>${items.map((item) => `<li>${item}</li>`).join("")}</ul>`;
}

function accountColumns(deal) {
  if (!deal.account) {
    return `<div><h4>Conta</h4>${listItems(["Conta em branco no CRM. Preencha para ver o porte e o histórico do cliente."])}</div>`;
  }
  const account = DATA.accounts[deal.account];
  const profile = [
    escapeHtml(account.sector),
    `Receita anual: ${companySize(account.revenue)}`,
    `${count(account.employees)} funcionários`,
    `${escapeHtml(account.location)}, desde ${account.founded}`,
  ];
  if (account.parent) profile.push(`Faz parte do grupo ${escapeHtml(account.parent)}`);

  const relationship = [`Já gerou ${money(account.wonRevenue)} em ${plural(account.wins, "deal ganho", "deals ganhos")} de ${count(account.closed)} encerrados`];
  if (account.lastWin) relationship.push(`Última compra há ${plural(daysSince(account.lastWin), "dia", "dias")}`);
  const bought = account.products[deal.product];
  relationship.push(bought
    ? `Já comprou ${escapeHtml(deal.product)} ${bought.wins === 1 ? "1 vez" : `${bought.wins} vezes`}, a última em ${shortDate(bought.last)}`
    : `Nunca comprou ${escapeHtml(deal.product)}: seria um produto novo na conta`);
  const others = Object.keys(account.products).filter((product) => product !== deal.product);
  if (others.length) relationship.push(`Também comprou: ${others.map(escapeHtml).join(", ")}`);
  if (account.parent) relationship.push(`O grupo já gerou ${money(account.groupRevenue)}`);
  if (deal.repAccountClosed) relationship.push(`Com este vendedor: ${deal.repAccountWins} de ${deal.repAccountClosed} ganhos`);
  return `<div><h4>Quem é o cliente</h4>${listItems(profile)}</div><div><h4>Relacionamento</h4>${listItems(relationship)}</div>`;
}

function dealDetails(deal) {
  if (snapshot().historic) return "";
  const stats = DATA.productStats[deal.product];
  const product = stats ? [
    `Tabela: ${money(deal.price)}`,
    `Fechamento típico: ${money(stats.median)}`,
    `Metade dos ganhos entre ${money(stats.low)} e ${money(stats.high)}`,
    `${Math.round((stats.wins / stats.closed) * 100)}% dos deals encerrados foram ganhos`,
  ] : [`Tabela: ${money(deal.price)}`];
  if (deal.repProductClosed) product.push(`Este vendedor: ${deal.repProductWins} de ${deal.repProductClosed} ganhos`);
  return `
    <details class="why">
      <summary>Ver detalhes do deal</summary>
      <div class="details-grid">
        ${accountColumns(deal)}
        <div><h4>${escapeHtml(deal.product)}: quanto costuma render</h4>${listItems(product)}</div>
      </div>
      <p class="details-note">Contexto para preparar a conversa, com deals encerrados até esta data. Estes dados não entram no score, porque quase não preveem o resultado.</p>
    </details>`;
}

function dealTitle(deal) {
  const sector = deal.sector ? ` · ${escapeHtml(deal.sector)}` : "";
  return `
    <div class="deal-title">
      <h3>${dealName(deal)}</h3>
      <div class="deal-meta">${escapeHtml(deal.id)}${sector}</div>
    </div>`;
}

function focusButtons(deal) {
  if (snapshot().historic) return "";
  return `<div class="row-actions">
    <button class="action-button primary" data-focus="feito" data-id="${escapeHtml(deal.id)}">Feito</button>
    <button class="action-button" data-focus="adiado" data-id="${escapeHtml(deal.id)}">Adiar</button>
  </div>`;
}

function highlightedCard(deal) {
  return `
    <article class="deal">
      <div class="deal-top">
        ${ring(deal.score)}
        ${dealTitle(deal)}
        <span class="price">${money(deal.price)}</span>
      </div>
      ${lifeTrack(deal)}
      <p class="deal-action">${escapeHtml(deal.action)}</p>
      ${contextChips(deal)}
      ${focusButtons(deal)}
      ${whyDetails(deal)}
      ${dealDetails(deal)}
    </article>`;
}

function compactCard(deal) {
  return `
    <article class="deal compact">
      <div class="deal-top">
        ${ring(deal.score)}
        <div class="deal-title">
          <h3>${dealName(deal)}</h3>
          <div class="deal-meta"><span class="price">${money(deal.price)}</span> · ${escapeHtml(deal.id)}${state.agent ? "" : ` · ${escapeHtml(deal.agent)}`}</div>
        </div>
      </div>
      ${lifeTrack(deal)}
      ${focusButtons(deal)}
      <p class="deal-action" style="grid-column:1 / -1">${escapeHtml(deal.action)}</p>
      ${whyDetails(deal)}
      ${dealDetails(deal)}
    </article>`;
}

function moreButton(total) {
  if (state.limit >= total) return "";
  return `<button class="action-button more" data-action="more">Mostrar mais (${count(total - state.limit)} restantes)</button>`;
}

function sectionHead(title, note) {
  return `<div class="section-head"><h2>${title}</h2>${note ? `<p>${note}</p>` : ""}</div>`;
}

/* Minha semana */

function briefingText(sel) {
  const pending = pendingFocus(sel);
  const stale = undecided(sel);
  const prospects = sel.prospecting;
  if (!state.agent) {
    const scope = state.manager || state.region || "Toda a operação";
    const engagedTotal = sel.foco.length + sel.decidir.length;
    const staleShare = engagedTotal ? Math.round((sel.decidir.length / engagedTotal) * 100) : 0;
    const follow = sel.foco.length === 0 && sel.decidir.length > 0
      ? "Nesta seleção não há deal vivo. Confirme com RevOps se os parados são reais ou efeito de importação de dados."
      : "Se você é vendedor, escolha seu nome no filtro Vendedor para ver sua semana.";
    return {
      title: escapeHtml(scope),
      text: `<p><strong>${staleShare}% dos deals em Engaging já passaram de ${snapshot().maxCycle} dias</strong>, a maior duração entre todos os deals encerrados.</p><p>${follow}</p>`,
    };
  }
  const first = escapeHtml(state.agent.split(" ")[0]);
  if (pending.length > 0) {
    const top = pending[0];
    const account = top.account ? ` na ${escapeHtml(top.account)}` : "";
    return {
      title: `${first}, ${snapshot().historic ? `semana de ${shortDate(snapshot().date)}` : "sua semana"}`,
      text: `<p><strong>Comece por ${escapeHtml(top.product)}${account}.</strong> ${escapeHtml(top.action)}</p>`,
    };
  }
  if (sel.foco.length > 0) {
    return { title: `${first}, sua semana`, text: `<p><strong>Você passou por todos os deals vivos.</strong> Confira o que marcou em Revisar.</p>` };
  }
  if (stale.length > 0 || prospects.length > 0) {
    const parts = [];
    if (stale.length) parts.push(`revise ${plural(stale.length, "deal parado", "deals parados")}`);
    if (prospects.length) parts.push(`avance ${plural(prospects.length, "deal", "deals")} em prospecção`);
    return { title: `${first}, sua semana`, text: `<p><strong>Você não tem nenhum deal vivo em Engaging.</strong> Esta semana, ${parts.join(" e depois ")}.</p>` };
  }
  return { title: `${first}, sua semana`, text: `<p><strong>Você não tem nenhum deal aberto nesta base.</strong> Fale com seu manager sobre novas oportunidades.</p>` };
}

function heroSection(sel) {
  const { title, text } = briefingText(sel);
  const bar = queueBar(sel);
  const staleValue = sumPrice(sel.decidir);
  const health = bar.total === 0 ? "" : `
    <div>
      <div class="health-title">Valor de tabela em aberto</div>
      <div class="health-number">${compactMoney(staleValue)} parados, de ${compactMoney(bar.total)}</div>
      ${bar.html}
    </div>`;
  return `
    <section class="hero">
      <div>
        <h1>${title}</h1>
        <div id="briefing">${text}</div>
      </div>
      ${health}
    </section>`;
}

function planStep(number, title, progress, percent, target, enabled) {
  const meter = percent === null ? "" : `<span class="meter"><i style="width:${percent}%"></i></span>`;
  return `
    <button class="step" data-go="${target}" ${enabled ? "" : "disabled"}>
      <span class="step-number">Passo ${number}</span>
      <span class="step-title">${title}</span>
      <span class="step-progress">${progress}</span>
      ${meter}
    </button>`;
}

function planSection(sel) {
  const weekTarget = Math.min(sel.foco.length, DATA.topK);
  const handled = sel.foco.filter(isHandled).length;
  const handledInTarget = Math.min(handled, weekTarget);
  const decided = sel.decidir.length - undecided(sel).length;
  const percent = (part, whole) => (whole ? Math.round((part / whole) * 100) : 0);
  return `
    <section class="plan" aria-label="Plano da semana">
      ${planStep(1, weekTarget ? `Agir em ${plural(weekTarget, "deal", "deals")}` : "Nenhum deal vivo", `${count(handledInTarget)} de ${count(weekTarget)} feitos`, percent(handledInTarget, weekTarget), "foco-lista", weekTarget > 0)}
      ${planStep(2, sel.decidir.length ? `Decidir ${plural(sel.decidir.length, "deal parado", "deals parados")}` : "Nada a decidir", `${count(decided)} de ${count(sel.decidir.length)} decididos`, percent(decided, sel.decidir.length), "decidir", sel.decidir.length > 0)}
      ${planStep(3, sel.prospecting.length ? `Avançar ${plural(sel.prospecting.length, "deal", "deals")} em prospecção` : "Nada em prospecção", "Maior valor primeiro", null, "prospeccao", sel.prospecting.length > 0)}
    </section>`;
}

function handledCard(deal) {
  const label = state.focusActions[deal.id] === "feito" ? "Feito" : "Adiado";
  return `
    <article class="simple-row done-row">
      <div>
        <h3>${escapeHtml(deal.product)} · ${accountLabel(deal)}</h3>
        <div class="deal-meta">${label} · ${money(deal.price)}${state.agent ? "" : ` · ${escapeHtml(deal.agent)}`}</div>
      </div>
      <div class="right"><button class="action-button quiet" data-undo-focus="${escapeHtml(deal.id)}">Desfazer</button></div>
    </article>`;
}

function viewFoco(sel) {
  const pending = pendingFocus(sel);
  const handled = sel.foco.filter(isHandled);
  const { week, historic } = snapshot();
  const plan = historic ? "" : planSection(sel);
  let list;
  if (sel.foco.length === 0) {
    const links = [];
    if (sel.decidir.length) links.push(`<button class="action-button primary" data-go="decidir">Ir para Decidir</button>`);
    if (sel.prospecting.length) links.push(`<button class="action-button" data-go="prospeccao">Ir para Prospecção</button>`);
    list = `<div class="empty"><p>Nenhum deal vivo nesta seleção.</p>${links.length ? `<div class="row-actions">${links.join("")}</div>` : ""}</div>`;
  } else if (state.sort !== "padrao") {
    list = `
      <div id="foco-lista"></div>
      ${sectionHead("Deals vivos por data de entrada")}
      ${sortControl("Score")}
      <div class="deal-list">${sortedByDate(pending).slice(0, state.limit).map(compactCard).join("")}</div>
      ${moreButton(pending.length)}`;
  } else {
    const highlighted = pending.slice(0, HIGHLIGHTED_DEALS);
    const thisWeek = pending.slice(HIGHLIGHTED_DEALS, DATA.topK);
    const rest = pending.slice(DATA.topK, state.limit);
    const quarterNote = week === 1
      ? "Primeira semana de trimestre: nas três vezes observadas, só deals com até 14 dias tiveram chance relevante de fechar logo."
      : "";
    list = `
      <div id="foco-lista"></div>
      ${sortControl("Score")}
      ${highlighted.length ? sectionHead("Comece por aqui", quarterNote) + `<div class="hero-deals">${highlighted.map(highlightedCard).join("")}</div>` : ""}
      ${thisWeek.length ? sectionHead("Também nesta semana") + `<div class="deal-list">${thisWeek.map(compactCard).join("")}</div>` : ""}
      ${rest.length ? sectionHead("Demais deals vivos") + `<div class="deal-list">${rest.map(compactCard).join("")}</div>` : ""}
      ${moreButton(pending.length)}
      ${handled.length ? sectionHead("Já marcados", "Tudo isso também aparece em Revisar") + `<div class="deal-list">${handled.map(handledCard).join("")}</div>` : ""}`;
  }
  return historyBanner() + heroSection(sel) + plan + list;
}

/* Decidir */

function decisionButtons(deal) {
  if (snapshot().historic) return "";
  const current = state.decisions[deal.id];
  const button = (value, label) => `<button class="action-button" data-decision="${value}" data-id="${escapeHtml(deal.id)}" aria-pressed="${current === value}">${label}</button>`;
  return `<div class="row-actions">${button("vivo", "Ainda está vivo")}${button("encerrar", "Encerrar")}</div>`;
}

function nextForTriage(sel) {
  const remaining = undecided(sel);
  return remaining.find((deal) => !state.skipped.has(deal.id)) || remaining[0] || null;
}

function triagePanel(sel) {
  const total = sel.decidir.length;
  const decided = total - undecided(sel).length;
  const decidedValue = sumPrice(sel.decidir.filter((deal) => state.decisions[deal.id]));
  const next = nextForTriage(sel);
  const undo = state.lastDecision
    ? `<button class="action-button quiet" data-action="undo-decision">Desfazer último<kbd>U</kbd></button>`
    : "";
  const progress = `
    <div class="triage-progress">
      <span id="decision-progress">${count(decided)} de ${count(total)} decididos</span>
      <span>${compactMoney(decidedValue)} de ${compactMoney(sumPrice(sel.decidir))} esclarecidos</span>
    </div>
    <div class="meter"><i style="width:${total ? (decided / total) * 100 : 0}%"></i></div>`;
  if (!next) {
    return `<section class="triage">${progress}
      <h2>Tudo decidido nesta seleção.</h2>
      <p>Confira e exporte em Revisar para o RevOps atualizar o CRM.</p>
      <div class="row-actions"><button class="action-button" data-go="revisar">Ir para Revisar</button>${undo}</div>
    </section>`;
  }
  const beyond = next.age - snapshot().maxCycle;
  const agent = state.agent ? "" : ` · ${escapeHtml(next.agent)}`;
  const account = next.account
    ? `Conta ${escapeHtml(next.account)}${next.pastDeals ? `: ${next.pastWins} de ${next.pastDeals} deals ganhos` : ""}`
    : "Conta em branco no CRM";
  return `
    <section class="triage" aria-label="Triagem de deals parados">
      ${progress}
      <div class="triage-deal">
        <h2>${escapeHtml(next.product)} · ${accountLabel(next)}</h2>
        <span class="triage-price">${money(next.price)}</span>
      </div>
      <p>${next.age} dias em Engaging, ${plural(beyond, "dia", "dias")} além do limite histórico · ${account}${agent}</p>
      ${dealDetails(next)}
      <div class="row-actions">
        <button class="action-button" data-decision="vivo" data-id="${escapeHtml(next.id)}">Ainda está vivo<kbd>V</kbd></button>
        <button class="action-button" data-decision="encerrar" data-id="${escapeHtml(next.id)}">Encerrar<kbd>E</kbd></button>
        <button class="action-button quiet" data-action="skip" data-id="${escapeHtml(next.id)}">Pular<kbd>P</kbd></button>
        ${undo}
      </div>
    </section>`;
}

function viewDecidir(sel) {
  if (sel.decidir.length === 0) {
    return `${historyBanner()}<div class="page-head"><h1>Decidir</h1></div><div class="empty"><p>Nenhum deal parado nesta seleção.</p></div>`;
  }
  const { historic, maxCycle } = snapshot();
  const rows = sortedByDate(sel.decidir).slice(0, state.limit).map((deal) => `
    <article class="simple-row">
      <div>
        <h3>${dealName(deal)}</h3>
        <div class="deal-meta">${escapeHtml(deal.id)} · ${deal.age} dias · desde ${shortDate(deal.engageDate)}${state.agent ? "" : ` · ${escapeHtml(deal.agent)}`}</div>
      </div>
      <div class="right"><span class="price">${money(deal.price)}</span>${decisionButtons(deal)}</div>
    </article>`).join("");
  return `
    ${historyBanner()}
    <div class="page-head">
      <h1>Decidir</h1>
      <p>Nenhum deal encerrado passou de ${maxCycle} dias, e estes já passaram. Fale com o cliente e registre: a ferramenta nunca encerra um deal sozinha.</p>
    </div>
    ${historic ? "" : triagePanel(sel)}
    <div class="section-head">
      <h2>Todos os parados</h2>
      ${historic ? "" : `<button class="action-button" data-action="export">Exportar decisões (CSV)</button>`}
    </div>
    ${sortControl("Maior valor")}
    <div class="deal-list">${rows}</div>
    ${moreButton(sel.decidir.length)}`;
}

function recordDecision(id, decision) {
  if (state.decisions[id] === decision) {
    delete state.decisions[id];
    if (state.lastDecision === id) state.lastDecision = null;
  } else {
    state.decisions[id] = decision;
    state.lastDecision = id;
  }
  state.skipped.delete(id);
  writeStorage(STORAGE.decisions, JSON.stringify(state.decisions));
  render();
  document.querySelector(".triage [data-decision], .triage .action-button")?.focus({ preventScroll: true });
}

function undoDecision() {
  if (!state.lastDecision) return;
  delete state.decisions[state.lastDecision];
  state.lastDecision = null;
  writeStorage(STORAGE.decisions, JSON.stringify(state.decisions));
  render();
}

function skipTriage(id) {
  state.skipped.add(id);
  const remaining = undecided(selection());
  if (remaining.every((deal) => state.skipped.has(deal.id))) state.skipped.clear();
  render();
}

/* Prospecção */

function viewProspeccao(sel) {
  const head = `
    <div class="page-head">
      <h1>Prospecção</h1>
      <p>Estes deals não têm data nem histórico de conversão para Engaging, então <strong>não recebem score</strong>: seria inventar precisão. A ordem é só por valor de tabela.</p>
    </div>`;
  const intro = `<p class="view-intro">Comece pelos de maior valor e complete a conta quando ela estiver em branco.</p>`;
  if (snapshot().historic) {
    return historyBanner() + head + `<div class="empty"><p>Sem histórico nesta data: deals em Prospecting não têm data no CRM.</p></div>`;
  }
  if (sel.prospecting.length === 0) {
    return head + `<div class="empty"><p>Nenhum deal em Prospecting nesta seleção.</p></div>`;
  }
  const rows = sel.prospecting.slice(0, state.limit).map((deal) => {
    const chips = [];
    if (!deal.account) chips.push(`<span class="chip attention">Preencha a conta no CRM</span>`);
    else if (deal.pastDeals > 0) chips.push(`<span class="chip">Histórico da conta: ${deal.pastWins} de ${deal.pastDeals} ganhos, ${compactMoney(DATA.accounts[deal.account].wonRevenue)}</span>`);
    if (!state.agent) chips.push(`<span class="chip">${escapeHtml(deal.agent)}</span>`);
    return `
      <article class="simple-row">
        <div>
          <h3>${escapeHtml(deal.product)} · ${accountLabel(deal)}</h3>
          <div class="deal-meta">${escapeHtml(deal.id)}</div>
          ${chips.length ? `<div class="chips">${chips.join("")}</div>` : ""}
          ${dealDetails(deal)}
        </div>
        <div class="right"><span class="price">${money(deal.price)}</span></div>
      </article>`;
  }).join("");
  return head + intro + `<div class="deal-list">${rows}</div>` + moreButton(sel.prospecting.length);
}

/* Revisar */

function viewRevisar(sel) {
  if (snapshot().historic) {
    return `${historyBanner()}<div class="page-head"><h1>Revisar</h1></div><div class="empty"><p>As marcações valem para o pipeline atual. Datas passadas são só para consulta.</p></div>`;
  }
  const done = sel.foco.filter((deal) => state.focusActions[deal.id] === "feito");
  const postponed = sel.foco.filter((deal) => state.focusActions[deal.id] === "adiado");
  const alive = sel.decidir.filter((deal) => state.decisions[deal.id] === "vivo");
  const closing = sel.decidir.filter((deal) => state.decisions[deal.id] === "encerrar");
  const tile = (label, deals) => `
    <div class="tile">
      <div class="label">${label}</div>
      <div class="number">${count(deals.length)}</div>
      <div class="detail">${money(sumPrice(deals))} em valor de tabela</div>
    </div>`;
  const row = (deal, attribute) => `
    <article class="simple-row">
      <div>
        <h3>${escapeHtml(deal.product)} · ${accountLabel(deal)}</h3>
        <div class="deal-meta">${escapeHtml(deal.id)} · ${deal.age} dias${state.agent ? "" : ` · ${escapeHtml(deal.agent)}`}</div>
      </div>
      <div class="right"><span class="price">${money(deal.price)}</span><button class="action-button quiet" ${attribute}="${escapeHtml(deal.id)}">Desfazer</button></div>
    </article>`;
  const group = (title, deals, attribute) => (deals.length
    ? sectionHead(title) + `<div class="deal-list">${deals.map((deal) => row(deal, attribute)).join("")}</div>`
    : "");
  const total = done.length + postponed.length + alive.length + closing.length;
  const body = total === 0
    ? `<div class="empty"><p>Nada marcado nesta seleção ainda.</p><div class="row-actions"><button class="action-button primary" data-go="foco">Voltar para Minha semana</button></div></div>`
    : group("Para encerrar no CRM", closing, "data-undo-decision")
      + group("Confirmados como vivos", alive, "data-undo-decision")
      + group("Feitos nesta semana", done, "data-undo-focus")
      + group("Adiados", postponed, "data-undo-focus");
  const exportButton = total === 0 ? "" : `<button class="action-button primary" data-action="export">Exportar tudo (CSV)</button>`;
  return `
    <div class="toolbar">
      <div class="page-head" style="margin:0"><h1>Revisar</h1><p>Confira o que foi marcado, desfaça o que precisar e envie ao RevOps.</p></div>
      ${exportButton}
    </div>
    <div class="tiles">
      ${tile("Para encerrar", closing)}
      ${tile("Confirmados vivos", alive)}
      ${tile("Feitos", done)}
      ${tile("Adiados", postponed)}
    </div>
    <p class="muted" style="margin-bottom:8px">As marcações ficam salvas só neste navegador até você exportar.</p>
    ${body}`;
}

function exportReview() {
  const byId = new Map(DATA.engaged.map((deal) => [deal.id, deal]));
  const quote = (value) => `"${String(value ?? "").replace(/"/g, '""')}"`;
  const header = ["opportunity_id", "tipo", "vendedor", "produto", "conta", "idade_dias", "valor_tabela", "decisao"];
  const toRows = (store, type) => Object.entries(store)
    .filter(([id]) => byId.has(id))
    .map(([id, decision]) => {
      const deal = byId.get(id);
      return [id, type, deal.agent, deal.product, deal.account, deal.age, deal.price, decision].map(quote).join(",");
    });
  const rows = [...toRows(state.decisions, "parado"), ...toRows(state.focusActions, "foco")];
  const blob = new Blob(["﻿" + [header.join(","), ...rows].join("\r\n")], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "revisao-foco-da-semana.csv";
  link.click();
  URL.revokeObjectURL(link.href);
}

/* Equipe */

function calculatorResult(sel) {
  const stale = sel.decidir.length;
  const { weekly, cleanup } = state.calculator;
  const oneDecimal = (value) => value.toLocaleString("pt-BR", { maximumFractionDigits: 1 });
  const weeklyHours = (stale * weekly) / 60;
  const cleanupHours = (stale * cleanup) / 60;
  if (stale === 0) return "Nenhum deal parado nesta seleção.";
  // In Portuguese, values below 2 take the singular ("1,5 pessoa").
  const withUnit = (value, one, many) => `${oneDecimal(value)} ${value < 2 ? one : many}`;
  const people = withUnit(weeklyHours / HOURS_PER_PERSON_WEEK, "pessoa", "pessoas");
  const payback = weeklyHours > 0
    ? ` A limpeza custa ${withUnit(cleanupHours, "hora", "horas")} uma única vez e se paga em ${withUnit(cleanupHours / weeklyHours, "semana", "semanas")}.`
    : "";
  return `<strong>${withUnit(weeklyHours, "hora", "horas")} por semana</strong> em ${plural(stale, "deal parado", "deals parados")}, o equivalente a ${people} em tempo integral (${HOURS_PER_PERSON_WEEK}h).${payback}`;
}

function viewCalculator(sel) {
  const { weekly, cleanup } = state.calculator;
  return `
    <section class="calculator">
      <h2>Quanto tempo os deals parados consomem?</h2>
      <p class="muted">Os dados têm a quantidade de deals, não o tempo gasto. Os minutos são uma <strong>premissa</strong>: ajuste com o time.</p>
      <div class="calculator-inputs">
        <label>Minutos por semana em cada deal parado
          <input type="number" min="0" max="120" step="1" value="${weekly}" data-calc="weekly">
        </label>
        <label>Minutos para decidir cada deal, uma vez
          <input type="number" min="0" max="120" step="1" value="${cleanup}" data-calc="cleanup">
        </label>
      </div>
      <p id="calc-result" aria-live="polite">${calculatorResult(sel)}</p>
    </section>`;
}

function regionCards() {
  const regions = [...new Set(DATA.team.filter((member) => matchesFilters(member.agent)).map((member) => member.region))].sort();
  const cards = regions.map((region) => {
    const inRegion = (deal) => teamByAgent.get(deal.agent)?.region === region && matchesFilters(deal.agent);
    const engaged = snapshot().engaged.filter(inRegion);
    const sel = {
      foco: engaged.filter((deal) => deal.queue === "foco"),
      decidir: engaged.filter((deal) => deal.queue === "decidir"),
      prospecting: snapshot().prospecting.filter(inRegion),
    };
    const alert = sel.foco.length === 0 && sel.decidir.length > 0
      ? `<p class="region-alert">Sem deal vivo. Confirme com RevOps se é processo ou importação de dados.</p>`
      : "";
    return `<article class="region"><h3>${escapeHtml(region)}</h3>${queueBar(sel).html}${alert}</article>`;
  });
  return `<section class="regions" aria-label="Pipeline por região">${cards.join("")}</section>`;
}

function viewEquipe(sel) {
  const members = DATA.team.filter((member) => matchesFilters(member.agent));
  const rows = members.map((member) => {
    const engaged = snapshot().engaged.filter((deal) => deal.agent === member.agent);
    const live = engaged.filter((deal) => deal.queue === "foco");
    const stale = engaged.filter((deal) => deal.queue === "decidir");
    const prospecting = snapshot().prospecting.filter((deal) => deal.agent === member.agent).length;
    return { member, live: live.length, stale: stale.length, staleValue: sumPrice(stale), prospecting };
  }).sort((a, b) => b.stale - a.stale || a.member.agent.localeCompare(b.member.agent, "pt-BR"));
  const largest = Math.max(1, ...rows.map((row) => row.live + row.stale));
  const body = rows.map((row) => {
    const segment = (value, name, label) => (value
      ? `<i class="${name}" style="width:${(value / largest) * 100}%" data-tip="${label}: ${value}"></i>`
      : "");
    return `
      <tr>
        <td><button class="link-button" data-agent="${escapeHtml(row.member.agent)}">${escapeHtml(row.member.agent)}</button></td>
        <td>${escapeHtml(row.member.region)}</td>
        <td class="team-bar"><div class="stack">${segment(row.live, "live", "Vivos")}${segment(row.stale, "stale", "Parados")}</div></td>
        <td>${count(row.live)}</td>
        <td>${count(row.stale)}</td>
        <td>${money(row.staleValue)}</td>
        <td>${count(row.prospecting)}</td>
      </tr>`;
  }).join("");
  return `
    ${historyBanner()}
    <div class="page-head"><h1>Equipe</h1><p>Onde o pipeline está parado e quem está sem deals vivos.</p></div>
    ${regionCards()}
    ${viewCalculator(sel)}
    ${sectionHead("Por vendedor", "Clique em um nome para abrir a semana da pessoa")}
    <div class="table-wrap"><table>
      <thead><tr><th>Vendedor</th><th>Região</th><th style="text-align:left">Vivos e parados</th><th>Vivos</th><th>Parados</th><th>Valor parado</th><th>Prospecção</th></tr></thead>
      <tbody>${body}</tbody>
    </table></div>`;
}

/* Máquina do tempo */

/** Field order written by scoring/backtest.py to keep replay.js small. */
function replayDeal(row, agent) {
  const [id, product, account, price, age, score, valuePts, timingPts, outcome, realized, daysToClose] = row;
  return { id, product, account, price, age, score, valuePts, timingPts, outcome, realized, daysToClose, agent };
}

function replaySelection(monday) {
  const entries = Object.entries(monday.agents).filter(([agent]) => matchesFilters(agent));
  const sum = (pick) => entries.reduce((total, [, entry]) => total + pick(entry), 0);
  const deals = entries
    .flatMap(([agent, entry]) => entry.deals.map((row) => replayDeal(row, agent)))
    .sort((a, b) => b.score - a.score || b.price - a.price || a.id.localeCompare(b.id));
  return {
    deals,
    scoreRevenue: deals.reduce((total, deal) => total + deal.realized, 0),
    scoreWins: deals.filter((deal) => deal.outcome === "won").length,
    lost: deals.filter((deal) => deal.outcome === "lost").length,
    stillOpen: deals.filter((deal) => deal.outcome === "open").length,
    valueRevenue: sum((entry) => entry.valueRevenue),
    valueWins: sum((entry) => entry.valueWins),
    liveValueRevenue: sum((entry) => entry.liveValueRevenue),
    poolRevenue: sum((entry) => entry.poolRevenue),
  };
}

function outcomeLine(deal) {
  if (deal.outcome === "won") return `<span class="outcome won">✓ Ganho: ${money(deal.realized)} em ${deal.daysToClose} dias</span>`;
  if (deal.outcome === "lost") return `<span class="outcome lost">✕ Perdido em ${deal.daysToClose} dias</span>`;
  return `<span class="outcome open">– Seguia aberto após ${DATA.backtest.horizon_days} dias</span>`;
}

function replayCard(deal) {
  // The account stays hidden until the reveal. Every closed deal has an account,
  // so "Conta em branco" would give away that a deal never closed.
  const title = state.revealed ? `${escapeHtml(deal.product)} · ${accountLabel(deal)}` : escapeHtml(deal.product);
  const agent = state.agent ? "" : ` · ${escapeHtml(deal.agent)}`;
  return `
    <article class="deal">
      <div class="deal-top">
        ${ring(deal.score)}
        <div class="deal-title">
          <h3>${title}</h3>
          <div class="deal-meta">${escapeHtml(deal.id)} · ${deal.age} dias em Engaging${agent}</div>
          ${state.revealed ? outcomeLine(deal) : ""}
        </div>
        <span class="price">${money(deal.price)}</span>
      </div>
    </article>`;
}

function replayVerdict(result) {
  const difference = result.scoreRevenue - result.liveValueRevenue;
  if (difference > 0) {
    const percent = result.liveValueRevenue > 0 ? ` (${Math.round((difference / result.liveValueRevenue) * 100)}% a mais)` : "";
    return `O score trouxe ${money(difference)} a mais que ordenar por valor sem os parados${percent}.`;
  }
  if (difference < 0) {
    const { better_mondays: better } = DATA.backtest.score_vs_live_value;
    return `Nesta segunda e nesta seleção, ordenar por valor sem os parados venceu por ${money(-difference)}. No total da operação, o score venceu em ${better} das ${DATA.backtest.mondays} segundas.`;
  }
  return "Nesta segunda e nesta seleção, as duas estratégias empataram.";
}

function mondayStrip() {
  const differences = REPLAY.map((monday) => {
    const result = replaySelection(monday);
    return result.scoreRevenue - result.liveValueRevenue;
  });
  // The zero line moves so the strip has no empty half when one side never wins.
  const largestUp = Math.max(0, ...differences);
  const largestDown = Math.max(0, ...differences.map((difference) => -difference));
  const span = Math.max(1, largestUp + largestDown);
  const zero = (largestDown / span) * 100;
  const columns = REPLAY.map((monday, index) => {
    const difference = differences[index];
    const height = (Math.abs(difference) / span) * 100;
    const direction = difference >= 0 ? "up" : "down";
    const tip = `${shortDate(monday.date)}: ${difference >= 0 ? "score à frente" : "valor sem parados à frente"} por ${money(Math.abs(difference))}`;
    return `<button class="strip-col ${index === state.replayIndex ? "current" : ""}" data-replay="${index}" aria-label="${tip}" data-tip="${tip}">
      <i class="${direction}" style="height:${height}%"></i>
    </button>`;
  }).join("");
  const wins = differences.filter((difference) => difference > 0).length;
  return `
    <section class="card">
      <h2>Todas as segundas: score contra o rival mais forte</h2>
      <p class="muted">O rival ordena por maior valor e já ignora os deals parados. Acima da linha, o score ganhou; abaixo, o rival ganhou. O score ficou à frente em ${wins} de ${differences.length}. Clique para abrir outra segunda.</p>
      <div class="strip" style="--zero:${zero}%">${columns}</div>
      <div class="strip-note"><span>${shortDate(REPLAY[0].date)}</span><span>${shortDate(REPLAY[REPLAY.length - 1].date)}</span></div>
    </section>`;
}

function comparisonBars(result) {
  const largest = Math.max(1, result.poolRevenue, result.scoreRevenue, result.valueRevenue, result.liveValueRevenue);
  const bar = (label, value, highlight) => `
    <div class="bar-row ${highlight ? "highlight" : ""}">
      <span>${label}</span>
      <span class="bar-track"><i style="width:${(value / largest) * 100}%"></i></span>
      <span class="amount">${compactMoney(value)}</span>
    </div>`;
  return `<div class="bars">
    ${bar("Lista do score", result.scoreRevenue, true)}
    ${bar("Valor, sem os parados", result.liveValueRevenue, false)}
    ${bar("Lista por maior valor", result.valueRevenue, false)}
    ${bar("Todos os deals abertos", result.poolRevenue, false)}
  </div>`;
}

function viewTempo() {
  const head = `
    <div class="page-head">
      <h1>Máquina do tempo</h1>
      <p>Volte a uma segunda de 2017 e veja a lista que a ferramenta teria mostrado, usando só o que se sabia naquele dia. Depois, revele o que aconteceu nos ${DATA.backtest.horizon_days} dias seguintes.</p>
    </div>`;
  if (REPLAY.length === 0) return head + `<div class="empty"><p>Dados do replay não encontrados. Rode scoring/backtest.py.</p></div>`;
  const monday = REPLAY[state.replayIndex];
  const result = replaySelection(monday);
  const options = REPLAY.map((item, index) => (
    `<option value="${index}" ${index === state.replayIndex ? "selected" : ""}>${shortDate(item.date)} · semana ${item.week} do trimestre</option>`
  )).join("");
  const controls = `
    <div class="toolbar">
      <label class="inline-label">Segunda-feira <select id="replay-date">${options}</select></label>
      ${state.revealed || result.deals.length === 0 ? "" : `<button class="action-button primary" data-action="reveal">Revelar o que aconteceu</button>`}
    </div>`;
  if (result.deals.length === 0) {
    return head + controls + `<div class="empty"><p>Sem deals vivos nesta seleção nesta segunda.</p></div>`;
  }
  const size = state.agent ? DATA.topK : TEAM_LIST_SIZE;
  const shown = result.deals.slice(0, size);
  const listTitle = state.agent ? "Lista desta segunda" : `Os ${shown.length} maiores scores da seleção`;
  const listNote = state.agent ? "" : `De ${count(result.deals.length)} nas listas dos vendedores`;
  const verdict = !state.revealed ? "" : `
    <section class="card">
      <p class="verdict-title verdict">${replayVerdict(result)}</p>
      ${comparisonBars(result)}
      <p class="muted" style="margin-top:8px">Lista do score: ${plural(result.scoreWins, "ganho", "ganhos")}, ${plural(result.lost, "perdido", "perdidos")} e ${count(result.stillOpen)} seguiam abertos. A comparação usa o top ${DATA.topK} de cada vendedor. Ela mede se a lista aponta os deals certos, não se a atenção mudou o resultado.</p>
    </section>
    ${mondayStrip()}`;
  return head + controls + verdict + sectionHead(listTitle, listNote)
    + `<div class="hero-deals">${shown.map(replayCard).join("")}</div>`;
}

/* Como funciona */

function ageCurveChart() {
  const largest = Math.max(...DATA.ageCurve.map((point) => point.rate));
  const columns = DATA.ageCurve.map((point) => {
    const percent = Math.round(point.rate * 100);
    const height = (point.rate / largest) * 82;
    const tip = `${point.age} a ${point.age + 14} dias: ${percent}% ganhos em 30 dias`;
    return `<div class="curve-col" data-tip="${tip}">
      <b style="bottom:calc(${height}% + 2px)">${percent}%</b>
      <i style="height:${height}%"></i>
    </div>`;
  }).join("");
  const axis = DATA.ageCurve.map((point) => `<span>${point.age}</span>`).join("");
  return `<div class="curve" role="img" aria-label="Chance de vitória em 30 dias por idade do deal">${columns}</div>
    <div class="curve-axis">${axis}</div>
    <p class="muted" style="margin-top:6px">Idade do deal em dias, em faixas de 15. Média de todas as semanas do trimestre.</p>`;
}

function viewComo() {
  const backtest = DATA.backtest;
  const pilotPlan = DATA.pilot;
  const order = ["score", "maior_valor_sem_parados", "maior_valor", "mais_novo", "aleatorio", "mais_antigo"];
  const names = { score: "Score desta ferramenta", maior_valor_sem_parados: "Maior valor, sem os parados", maior_valor: "Maior valor", mais_novo: "Mais novo primeiro", aleatorio: "Aleatório", mais_antigo: "Mais antigo primeiro" };
  const largest = backtest.all.score.revenue;
  const bars = order.map((key) => `
    <div class="bar-row ${key === "score" ? "highlight" : ""}">
      <span>${names[key]}</span>
      <span class="bar-track"><i style="width:${(backtest.all[key].revenue / largest) * 100}%"></i></span>
      <span class="amount">US$ ${Math.round(backtest.all[key].revenue / 1000)} mil</span>
    </div>`).join("");
  const percent = (value) => `${Math.round(value * 1000) / 10}%`.replace(".", ",");
  const strategyRows = order.map((key) => `
    <tr class="${key === "score" ? "highlight" : ""}">
      <td>${names[key]}</td>
      <td>${money(backtest.selection_jul_sep[key].revenue)}</td>
      <td>${money(backtest.holdout_oct_nov[key].revenue)}</td>
      <td>${percent(backtest.all[key].win_rate)}</td>
      <td>${Math.round(backtest.all[key].stale)}</td>
    </tr>`).join("");
  const calibrationRows = backtest.calibration.map((band) => `
    <tr><td>${escapeHtml(band.band)}</td><td>${count(band.deals)}</td><td>${percent(band.previsto)}</td><td>${percent(band.real)}</td></tr>`).join("");
  const comparison = backtest.score_vs_value;
  const gainOver = (period, rival) => Math.round((backtest[period].score.revenue / backtest[period][rival].revenue - 1) * 100);
  const gain = gainOver("all", "maior_valor");
  const liveGain = gainOver("all", "maior_valor_sem_parados");
  const liveHoldoutGain = gainOver("holdout_oct_nov", "maior_valor_sem_parados");
  const liveBetter = backtest.score_vs_live_value.better_mondays;

  return `<div class="explain">
    <h1 style="margin-bottom:12px">Como funciona</h1>
    <p class="formula">Score = chance de ganhar em ${backtest.horizon_days} dias × valor do deal, em escala de 0 a 100</p>
    <ul>
      <li><strong>Valor</strong> é o preço de tabela do produto. O preço fechado costuma ficar muito próximo dele (mediana de 99,8%).</li>
      <li><strong>Momento</strong> é a frequência histórica de vitória em ${backtest.horizon_days} dias para deals da mesma idade, na mesma semana do trimestre.</li>
      <li>A escala é logarítmica, pois os preços variam de US$ 55 a US$ 26.768. As duas partes somadas ordenam os deals pela receita esperada.</li>
    </ul>

    <h2>A vida de um deal</h2>
    <p>A chance não sobe em linha reta com a idade. Ela tem dois picos, e depois de ${DATA.maxCycle} dias nenhum deal fechou.</p>
    ${ageCurveChart()}

    <h2>O que ficou de fora, de propósito</h2>
    <p>Vendedor, produto, setor e porte da conta quase não preveem o resultado (AUC de cerca de 0,55) e não melhoraram a lista quando testados. Colocá-los no score criaria uma precisão falsa, e ainda penalizaria deals por causa de quem os atende.</p>

    <h2>Isso funciona?</h2>
    <p>Reconstruímos ${backtest.mondays} segundas-feiras, de julho a novembro de 2017. Em cada uma, montamos o top ${backtest.top_k} de cada vendedor usando só o que se sabia naquele dia e medimos a receita ganha nos ${backtest.horizon_days} dias seguintes.</p>
    <p><strong>O score trouxe ${gain}% mais receita do que ordenar por valor e ficou à frente em ${comparison.better_mondays} das ${backtest.mondays} segundas.</strong> Mas boa parte disso vem só de tirar os deals parados da lista.</p>
    <p><strong>Contra o rival mais forte, que ordena por valor e já ignora os parados, o ganho é de ${liveGain}%</strong>, à frente em ${liveBetter} das ${backtest.mondays} segundas. E ele é desigual: em outubro e novembro, caiu para ${liveHoldoutGain}%. Limpar o pipeline é o ganho mais sólido; o momento agrega, com menos certeza. Confira segunda a segunda na Máquina do tempo.</p>
    <div class="bars" aria-hidden="true">${bars}</div>
    <div class="table-wrap"><table>
      <caption>Receita média por segunda no top ${backtest.top_k} de cada vendedor</caption>
      <thead><tr><th>Estratégia</th><th>Jul–set</th><th>Out–nov</th><th>Ganhos em ${backtest.horizon_days} dias</th><th>Parados na lista</th></tr></thead>
      <tbody>${strategyRows}</tbody>
    </table></div>

    <h2>Quanto confiar nas chances</h2>
    <p>A ordem é confiável, mas o modelo superestima as chances mais altas. Por isso, os cartões mostram a taxa observada no replay, não a prevista.</p>
    <div class="table-wrap"><table>
      <thead><tr><th>Chance prevista</th><th>Observações</th><th>Média prevista</th><th>Real</th></tr></thead>
      <tbody>${calibrationRows}</tbody>
    </table></div>

    <h2>Próximo passo: medir o ganho real</h2>
    <p>Simulamos ${count(pilotPlan.placebo_splits)} divisões falsas dos ${pilotPlan.reps} vendedores ativos para saber o que um teste com grupo de controle conseguiria detectar, comparando cada pessoa com o próprio histórico:</p>
    <div class="table-wrap"><table>
      <thead><tr><th>Duração do teste</th><th>Menor ganho em vitórias</th><th>Menor ganho em receita</th></tr></thead>
      <tbody>
        <tr><td>Um mês</td><td>${pilotPlan.periods.um_mes_outubro.wins.adjusted_percent}%</td><td>${pilotPlan.periods.um_mes_outubro.revenue.adjusted_percent}%</td></tr>
        <tr class="highlight"><td>Um trimestre completo</td><td>${pilotPlan.periods.um_trimestre_q4.wins.adjusted_percent}%</td><td>${pilotPlan.periods.um_trimestre_q4.revenue.adjusted_percent}%</td></tr>
      </tbody>
    </table></div>
    <p style="margin-top:8px">Um piloto de um mês não concluiria quase nada. O teste precisa durar um trimestre inteiro, com vitórias como métrica principal. Um ganho real menor que esses valores pode passar despercebido.</p>

    <h2>O que esta ferramenta não sabe</h2>
    <ul>
      <li><strong>Ela não prova aumento de vendas.</strong> O replay mostra que a lista aponta os deals que iam fechar, não que a atenção do vendedor muda o resultado.</li>
      <li><strong>Mais receita não é mais vitórias.</strong> Entre outubro e novembro, ordenar pelo mais novo ganhou mais deals, enquanto o score trouxe mais receita.</li>
      <li><strong>O efeito de trimestre é uma hipótese.</strong> Melhorou o replay, mas se baseia em no máximo três trimestres observados e pode ser efeito do dataset. RevOps precisa confirmar se é processo comercial.</li>
      <li><strong>Passar de ${DATA.maxCycle} dias não prova que um deal morreu.</strong> Por isso, a decisão fica com o vendedor.</li>
      <li><strong>O CRM não registra atividade</strong>, como e-mails, reuniões ou último contato. "Parado" aqui significa apenas tempo em Engaging.</li>
      <li><strong>A idade é a única medida de tempo.</strong> Não há histórico de mudanças de estágio, e deals em Prospecting não têm data.</li>
    </ul>
  </div>`;
}

/* Rendering */

function renderView(sel) {
  const views = { foco: viewFoco, decidir: viewDecidir, prospeccao: viewProspeccao, revisar: viewRevisar, equipe: viewEquipe, tempo: viewTempo, como: viewComo };
  document.getElementById("view").innerHTML = views[state.tab](sel);
}

function render() {
  const sel = selection();
  renderHeader();
  renderDateFilter();
  renderFilters();
  renderTabs(sel);
  renderView(sel);
  hideTooltip();
}

function changeFilter(update) {
  Object.assign(state, update, { limit: PAGE_SIZE, revealed: false, lastDecision: null });
  state.skipped.clear();
  writeStorage(STORAGE.agent, state.agent);
  render();
}

function changeDate(date) {
  state.date = date;
  const replayIndex = REPLAY.findIndex((monday) => monday.date === date);
  if (replayIndex >= 0) state.replayIndex = replayIndex;
  state.limit = PAGE_SIZE;
  state.revealed = false;
  state.lastDecision = null;
  render();
}

function goTo(target) {
  if (target === "foco-lista") {
    document.getElementById("foco-lista")?.scrollIntoView({ behavior: "smooth" });
    return;
  }
  state.tab = target;
  state.limit = PAGE_SIZE;
  state.revealed = false;
  render();
  window.scrollTo(0, 0);
}

function setFocusAction(id, action) {
  state.focusActions[id] = action;
  writeStorage(STORAGE.focusActions, JSON.stringify(state.focusActions));
  render();
  document.querySelector("[data-focus]")?.focus({ preventScroll: true });
}

function clearMark(store, storageKey, id) {
  delete store[id];
  writeStorage(storageKey, JSON.stringify(store));
  render();
}

/* Tooltip */

const tooltip = document.getElementById("tooltip");

function showTooltip(target) {
  tooltip.textContent = target.dataset.tip;
  tooltip.hidden = false;
  const box = target.getBoundingClientRect();
  const left = Math.min(Math.max(8, box.left + box.width / 2 - tooltip.offsetWidth / 2), window.innerWidth - tooltip.offsetWidth - 8);
  const top = box.top - tooltip.offsetHeight - 6;
  tooltip.style.left = `${left}px`;
  tooltip.style.top = `${top < 8 ? box.bottom + 6 : top}px`;
}

function hideTooltip() {
  tooltip.hidden = true;
}

document.addEventListener("mouseover", (event) => {
  const target = event.target.closest("[data-tip]");
  if (target) showTooltip(target);
  else hideTooltip();
});
document.addEventListener("focusin", (event) => {
  const target = event.target.closest("[data-tip]");
  if (target) showTooltip(target);
  else hideTooltip();
});

/* Events */

document.getElementById("filter-date").addEventListener("change", (event) => {
  changeDate(event.target.value);
});

document.getElementById("filter-region").addEventListener("change", (event) => {
  changeFilter({ region: event.target.value, manager: "", agent: "" });
});

document.getElementById("filter-manager").addEventListener("change", (event) => {
  changeFilter({ manager: event.target.value, agent: "" });
});

document.getElementById("filter-agent").addEventListener("change", (event) => {
  changeFilter({ agent: event.target.value });
});

document.getElementById("tabs").addEventListener("click", (event) => {
  const button = event.target.closest("[data-tab]");
  if (!button) return;
  goTo(button.dataset.tab);
  document.querySelector(`[data-tab="${state.tab}"]`).focus();
});

const view = document.getElementById("view");

view.addEventListener("change", (event) => {
  if (event.target.id === "sort-deals") {
    state.sort = event.target.value;
    state.limit = PAGE_SIZE;
    renderView(selection());
    document.getElementById("sort-deals")?.focus();
    return;
  }
  if (event.target.id !== "replay-date") return;
  state.replayIndex = Number(event.target.value);
  state.revealed = false;
  renderView(selection());
  document.getElementById("replay-date").focus();
});

view.addEventListener("input", (event) => {
  const field = event.target.dataset.calc;
  if (!field) return;
  const value = Number(event.target.value);
  state.calculator[field] = Number.isFinite(value) && value >= 0 ? value : 0;
  writeStorage(STORAGE.calculator, JSON.stringify(state.calculator));
  // Only the result changes, so the input keeps focus while typing.
  document.getElementById("calc-result").innerHTML = calculatorResult(selection());
});

view.addEventListener("click", (event) => {
  const target = event.target.closest("button");
  if (!target) return;
  const { dataset } = target;
  if (dataset.go) goTo(dataset.go);
  else if (dataset.focus) setFocusAction(dataset.id, dataset.focus);
  else if (dataset.undoFocus) clearMark(state.focusActions, STORAGE.focusActions, dataset.undoFocus);
  else if (dataset.undoDecision) clearMark(state.decisions, STORAGE.decisions, dataset.undoDecision);
  else if (dataset.decision) recordDecision(dataset.id, dataset.decision);
  else if (dataset.replay) {
    state.replayIndex = Number(dataset.replay);
    state.revealed = true;
    renderView(selection());
  } else if (dataset.agent) {
    state.tab = "foco";
    changeFilter({ agent: dataset.agent });
    window.scrollTo(0, 0);
  } else if (dataset.action === "back-to-today") {
    changeDate(DATA.asOf);
  } else if (dataset.action === "reveal") {
    state.revealed = true;
    renderView(selection());
  } else if (dataset.action === "more") {
    state.limit += PAGE_SIZE;
    renderView(selection());
  } else if (dataset.action === "export") {
    exportReview();
  } else if (dataset.action === "skip") {
    skipTriage(dataset.id);
  } else if (dataset.action === "undo-decision") {
    undoDecision();
  }
});

document.addEventListener("keydown", (event) => {
  if (state.tab !== "decidir" || snapshot().historic || event.ctrlKey || event.metaKey || event.altKey) return;
  if (["INPUT", "SELECT", "TEXTAREA"].includes(event.target.tagName)) return;
  const next = nextForTriage(selection());
  const key = event.key.toLowerCase();
  if (key === "u") undoDecision();
  else if (next && key === "v") recordDecision(next.id, "vivo");
  else if (next && key === "e") recordDecision(next.id, "encerrar");
  else if (next && key === "p") skipTriage(next.id);
});

render();

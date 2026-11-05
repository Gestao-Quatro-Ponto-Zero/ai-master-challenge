"use strict";

const DATA = window.LEAD_DATA;
const PAGE_SIZE = 30;
const STORAGE_AGENT = "focoSemana.agent";
const STORAGE_DECISIONS = "focoSemana.decisions";

const TABS = [
  { id: "foco", label: "Foco" },
  { id: "decidir", label: "Decidir" },
  { id: "prospeccao", label: "Prospecção" },
  { id: "equipe", label: "Equipe" },
  { id: "como", label: "Como funciona" },
];

const teamByAgent = new Map(DATA.team.map((member) => [member.agent, member]));
const state = {
  region: "",
  manager: "",
  agent: readStorage(STORAGE_AGENT, ""),
  tab: "foco",
  limit: PAGE_SIZE,
  decisions: readDecisions(),
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

function readDecisions() {
  try {
    const parsed = JSON.parse(readStorage(STORAGE_DECISIONS, "{}"));
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

function matchesFilters(agent) {
  const member = teamByAgent.get(agent);
  if (!member) return false;
  if (state.agent) return agent === state.agent;
  if (state.manager) return member.manager === state.manager;
  if (state.region) return member.region === state.region;
  return true;
}

function selection() {
  const engaged = DATA.engaged.filter((deal) => matchesFilters(deal.agent));
  return {
    foco: engaged.filter((deal) => deal.queue === "foco"),
    decidir: engaged.filter((deal) => deal.queue === "decidir").sort((a, b) => b.price - a.price || b.age - a.age),
    prospecting: DATA.prospecting.filter((deal) => matchesFilters(deal.agent)),
  };
}

const sumPrice = (deals) => deals.reduce((total, deal) => total + deal.price, 0);

/** Replay result for the chance band, because high predictions ran above reality. */
function observedChance(probability) {
  const limits = [0.05, 0.1, 0.2, 0.3, Infinity];
  const index = limits.findIndex((limit) => probability <= limit);
  return Math.round(DATA.backtest.calibration[index].real * 100);
}

function renderHeader() {
  const date = new Date(`${DATA.asOf}T12:00:00`).toLocaleDateString("pt-BR", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  });
  document.getElementById("as-of").textContent =
    `Pipeline de ${date}, semana ${DATA.quarterWeek} do trimestre. Dados do CRM até 31/12/2017.`;
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

function briefingText(sel) {
  const { foco, decidir, prospecting } = sel;
  if (!state.agent) {
    const scope = state.manager || state.region || "Toda a operação";
    const staleShare = foco.length + decidir.length ? Math.round((decidir.length / (foco.length + decidir.length)) * 100) : 0;
    const firstLine = `<p><strong>${escapeHtml(scope)}: ${count(foco.length)} deals vivos e ${count(decidir.length)} parados.</strong> ${staleShare}% dos deals em Engaging já passaram de ${DATA.maxCycle} dias, a maior duração entre todos os deals encerrados.</p>`;
    const secondLine = foco.length === 0 && decidir.length > 0
      ? `<p>Nesta seleção não há deal vivo. Confirme com RevOps se os parados são reais ou efeito de importação de dados.</p>`
      : `<p>Vendedor: escolha seu nome no filtro acima para ver sua lista.</p>`;
    return firstLine + secondLine;
  }
  const first = escapeHtml(state.agent.split(" ")[0]);
  if (foco.length > 0) {
    const top = foco[0];
    const account = top.account ? ` na ${escapeHtml(top.account)}` : "";
    const staleLine = decidir.length ? ` Depois, reserve um tempo para decidir ${plural(decidir.length, "deal parado", "deals parados")}.` : "";
    return `<p><strong>${first}, comece por ${escapeHtml(top.product)}${account}.</strong> Sua lista tem ${plural(Math.min(foco.length, DATA.topK), "deal", "deals")} para esta semana.${staleLine}</p>`;
  }
  if (decidir.length > 0 || prospecting.length > 0) {
    const parts = [];
    if (decidir.length) parts.push(`revise ${plural(decidir.length, "deal parado", "deals parados")} em Decidir`);
    if (prospecting.length) parts.push(`avance ${plural(prospecting.length, "deal", "deals")} em Prospecção`);
    return `<p><strong>${first}, você não tem nenhum deal vivo em Engaging.</strong> Esta semana, ${parts.join(" e depois ")}.</p>`;
  }
  return `<p><strong>${first}, você não tem nenhum deal aberto nesta base.</strong> Todos os seus deals já foram encerrados. Fale com seu manager sobre novas oportunidades.</p>`;
}

function renderBriefing(sel) {
  document.getElementById("briefing").innerHTML = briefingText(sel);
}

function renderTiles(sel) {
  const tile = (label, number, detail) => `
    <div class="tile">
      <div class="label">${label}</div>
      <div class="number">${count(number)}</div>
      <div class="detail">${detail}</div>
    </div>`;
  document.getElementById("tiles").innerHTML = [
    tile("Foco: deals vivos", sel.foco.length, `${money(sumPrice(sel.foco))} em valor de tabela`),
    tile("Decidir: deals parados", sel.decidir.length, `${money(sumPrice(sel.decidir))} em valor de tabela`),
    tile("Prospecção: sem data", sel.prospecting.length, `${money(sumPrice(sel.prospecting))} em valor de tabela`),
  ].join("");
}

function renderTabs(sel) {
  const counts = { foco: sel.foco.length, decidir: sel.decidir.length, prospeccao: sel.prospecting.length };
  document.getElementById("tabs").innerHTML = TABS.map((tab) => {
    const suffix = tab.id in counts ? ` (${count(counts[tab.id])})` : "";
    return `<button class="tab" role="tab" data-tab="${tab.id}" aria-selected="${state.tab === tab.id}">${tab.label}${suffix}</button>`;
  }).join("");
}

function accountLabel(deal) {
  return deal.account ? escapeHtml(deal.account) : "Conta em branco";
}

function contextChips(deal) {
  const chips = [];
  if (!deal.account) chips.push(`<span class="chip attention">Preencha a conta no CRM</span>`);
  else if (deal.pastDeals > 0) chips.push(`<span class="chip">Histórico da conta: ${deal.pastWins} de ${deal.pastDeals} ganhos</span>`);
  if (deal.zone === "prazo_final") chips.push(`<span class="chip attention">Prazo final</span>`);
  if (!state.agent) chips.push(`<span class="chip">${escapeHtml(deal.agent)}</span>`);
  return chips.length ? `<div class="chips">${chips.join("")}</div>` : "";
}

function dealCard(deal) {
  const sector = deal.sector ? ` · ${escapeHtml(deal.sector)}` : "";
  return `
    <article class="deal">
      <div class="score" aria-label="Score ${deal.score}">${deal.score}<small>score</small></div>
      <div>
        <div class="deal-head">
          <h3>${escapeHtml(deal.product)} · ${accountLabel(deal)}</h3>
          <span class="price">${money(deal.price)}</span>
        </div>
        <div class="deal-meta">${escapeHtml(deal.id)}${sector} · ${deal.age} dias em Engaging</div>
        <div class="bar" role="img" aria-label="Valor ${deal.valuePts} pontos, Momento ${deal.timingPts} pontos">
          <i class="value" style="width:${deal.valuePts}%"></i><i class="timing" style="width:${deal.timingPts}%"></i>
        </div>
        <p class="reason">Valor ${deal.valuePts} + Momento ${deal.timingPts}. Em deals parecidos, cerca de ${observedChance(deal.probability)} em cada 100 foram ganhos em ${DATA.backtest.horizon_days} dias.</p>
        <p class="action">${escapeHtml(deal.action)}</p>
        ${contextChips(deal)}
      </div>
    </article>`;
}

function moreButton(total) {
  if (state.limit >= total) return "";
  return `<button class="action-button more" data-action="more">Mostrar mais (${count(total - state.limit)} restantes)</button>`;
}

function viewFoco(sel) {
  if (sel.foco.length === 0) {
    const links = [];
    if (sel.decidir.length) links.push(`<button class="action-button" data-go="decidir">Ir para Decidir</button>`);
    if (sel.prospecting.length) links.push(`<button class="action-button" data-go="prospeccao">Ir para Prospecção</button>`);
    return `<div class="empty"><p>Nenhum deal vivo nesta seleção.</p>${links.length ? `<div class="row-actions">${links.join("")}</div>` : ""}</div>`;
  }
  const legend = `
    <div class="legend" aria-label="Legenda do score">
      <span><i class="swatch value"></i>Valor: preço de tabela do produto</span>
      <span><i class="swatch timing"></i>Momento: idade do deal e semana do trimestre</span>
    </div>`;
  const quarterNote = DATA.quarterWeek === 1
    ? ` Primeira semana de trimestre: nas três vezes observadas, só deals com até 14 dias tiveram chance relevante de fechar logo.`
    : "";
  const intro = `<p class="view-intro">Ordenado por receita esperada em ${DATA.backtest.horizon_days} dias. Só entram deals que ainda estão dentro do tempo em que deals costumam fechar.${quarterNote}</p>`;
  const top = sel.foco.slice(0, DATA.topK);
  const rest = sel.foco.slice(DATA.topK, state.limit);
  const restTitle = rest.length ? `<h2 class="section-title">Demais deals vivos</h2>` : "";
  return intro + legend + `<h2 class="section-title">Para esta semana</h2>`
    + top.map(dealCard).join("") + restTitle + rest.map(dealCard).join("") + moreButton(sel.foco.length);
}

function decisionButtons(deal) {
  const current = state.decisions[deal.id];
  const button = (value, label) => `<button class="action-button" data-decision="${value}" data-id="${escapeHtml(deal.id)}" aria-pressed="${current === value}">${label}</button>`;
  return `<div class="row-actions">${button("vivo", "Ainda está vivo")}${button("encerrar", "Encerrar")}</div>`;
}

function viewDecidir(sel) {
  if (sel.decidir.length === 0) {
    return `<div class="empty">Nenhum deal parado nesta seleção.</div>`;
  }
  const decided = sel.decidir.filter((deal) => state.decisions[deal.id]).length;
  const rows = sel.decidir.slice(0, state.limit).map((deal) => `
    <article class="simple-row">
      <div class="deal-head">
        <h3>${escapeHtml(deal.product)} · ${accountLabel(deal)}</h3>
        <span class="price">${money(deal.price)}</span>
      </div>
      <div class="deal-meta">${escapeHtml(deal.id)} · ${deal.age} dias em Engaging${state.agent ? "" : ` · ${escapeHtml(deal.agent)}`}</div>
      ${decisionButtons(deal)}
    </article>`).join("");
  return `
    <p class="view-intro">Nenhum deal encerrado passou de ${DATA.maxCycle} dias, e estes já passaram. Eles não recebem score. Fale com o cliente e registre sua decisão: a ferramenta nunca encerra um deal sozinha.</p>
    <div class="toolbar">
      <span id="decision-progress">${count(decided)} de ${count(sel.decidir.length)} decididos · maior valor primeiro</span>
      <button class="action-button" data-action="export">Exportar decisões (CSV)</button>
    </div>
    <p class="muted" style="margin-bottom:12px">As decisões ficam salvas só neste navegador. Exporte o CSV para o RevOps atualizar o CRM.</p>
    ${rows}${moreButton(sel.decidir.length)}`;
}

function viewProspeccao(sel) {
  if (sel.prospecting.length === 0) {
    return `<div class="empty">Nenhum deal em Prospecting nesta seleção.</div>`;
  }
  const rows = sel.prospecting.slice(0, state.limit).map((deal) => {
    const chips = [];
    if (!deal.account) chips.push(`<span class="chip attention">Preencha a conta no CRM</span>`);
    else if (deal.pastDeals > 0) chips.push(`<span class="chip">Histórico da conta: ${deal.pastWins} de ${deal.pastDeals} ganhos</span>`);
    if (!state.agent) chips.push(`<span class="chip">${escapeHtml(deal.agent)}</span>`);
    return `
      <article class="simple-row">
        <div class="deal-head">
          <h3>${escapeHtml(deal.product)} · ${accountLabel(deal)}</h3>
          <span class="price">${money(deal.price)}</span>
        </div>
        <div class="deal-meta">${escapeHtml(deal.id)}</div>
        ${chips.length ? `<div class="chips" style="margin-top:6px">${chips.join("")}</div>` : ""}
      </article>`;
  }).join("");
  return `
    <p class="view-intro">Estes deals não têm data nem histórico de conversão para Engaging, então <strong>não recebem score</strong>: seria inventar precisão. A ordem é só por valor de tabela.</p>
    ${rows}${moreButton(sel.prospecting.length)}`;
}

function viewEquipe() {
  const members = DATA.team.filter((member) => matchesFilters(member.agent));
  const rows = members.map((member) => {
    const engaged = DATA.engaged.filter((deal) => deal.agent === member.agent);
    const live = engaged.filter((deal) => deal.queue === "foco");
    const stale = engaged.filter((deal) => deal.queue === "decidir");
    const prospecting = DATA.prospecting.filter((deal) => deal.agent === member.agent).length;
    return { member, live: live.length, liveValue: sumPrice(live), stale: stale.length, staleValue: sumPrice(stale), prospecting };
  }).sort((a, b) => b.stale - a.stale || a.member.agent.localeCompare(b.member.agent, "pt-BR"));
  const body = rows.map((row) => `
    <tr>
      <td><button class="link-button" data-agent="${escapeHtml(row.member.agent)}">${escapeHtml(row.member.agent)}</button></td>
      <td>${escapeHtml(row.member.region)}</td>
      <td>${count(row.live)}</td>
      <td>${money(row.liveValue)}</td>
      <td>${count(row.stale)}</td>
      <td>${money(row.staleValue)}</td>
      <td>${count(row.prospecting)}</td>
    </tr>`).join("");
  return `
    <p class="view-intro">Para o manager: quem precisa limpar pipeline e quem está sem deals vivos. Clique em um nome para abrir a lista da pessoa.</p>
    <div class="table-wrap"><table>
      <thead><tr><th>Vendedor</th><th>Região</th><th>Vivos</th><th>Valor vivo</th><th>Parados</th><th>Valor parado</th><th>Prospecção</th></tr></thead>
      <tbody>${body}</tbody>
    </table></div>`;
}

function viewComo() {
  const backtest = DATA.backtest;
  const order = ["score", "maior_valor", "mais_novo", "aleatorio", "mais_antigo"];
  const names = { score: "Score desta ferramenta", maior_valor: "Maior valor", mais_novo: "Mais novo primeiro", aleatorio: "Aleatório", mais_antigo: "Mais antigo primeiro" };
  const largest = backtest.all.score.revenue;
  const bars = order.map((key) => `
    <div class="bar-row ${key === "score" ? "highlight" : ""}">
      <span>${names[key]}</span>
      <span class="track"><i style="width:${(backtest.all[key].revenue / largest) * 100}%"></i></span>
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
  const gain = Math.round((backtest.all.score.revenue / backtest.all.maior_valor.revenue - 1) * 100);

  return `<div class="explain">
    <h2>O que é o score</h2>
    <p class="formula">Score = chance de ganhar em ${backtest.horizon_days} dias × valor do deal, em escala de 0 a 100</p>
    <ul>
      <li><strong>Valor</strong> é o preço de tabela do produto. O preço fechado costuma ficar muito próximo dele (mediana de 99,8%).</li>
      <li><strong>Momento</strong> é a frequência histórica de vitória em ${backtest.horizon_days} dias para deals da mesma idade, na mesma semana do trimestre.</li>
      <li>A escala é logarítmica, pois os preços variam de US$ 55 a US$ 26.768. As duas partes somadas ordenam os deals exatamente pela receita esperada.</li>
    </ul>

    <h2>O que ficou de fora, de propósito</h2>
    <p>Vendedor, produto, setor e porte da conta quase não preveem o resultado (AUC de cerca de 0,55) e não melhoraram a lista quando testados. Colocá-los no score criaria uma precisão falsa, e ainda penalizaria deals por causa de quem os atende.</p>

    <h2>Isso funciona?</h2>
    <p>Reconstruímos ${backtest.mondays} segundas-feiras, de julho a novembro de 2017. Em cada uma, montamos o top ${backtest.top_k} de cada vendedor usando só o que se sabia naquele dia e medimos a receita ganha nos ${backtest.horizon_days} dias seguintes.</p>
    <p><strong>O score trouxe ${gain}% mais receita do que ordenar por valor e ficou à frente em ${comparison.better_mondays} das ${backtest.mondays} segundas.</strong></p>
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

    <h2>O que esta ferramenta não sabe</h2>
    <ul>
      <li><strong>Ela não prova aumento de vendas.</strong> O replay mostra que a lista aponta os deals que iam fechar, não que a atenção do vendedor muda o resultado. Medir isso exige um teste com grupo de controle.</li>
      <li><strong>Mais receita não é mais vitórias.</strong> Entre outubro e novembro, ordenar pelo mais novo ganhou mais deals, enquanto o score trouxe mais receita.</li>
      <li><strong>O efeito de trimestre é uma hipótese.</strong> Melhorou o replay, mas se baseia em no máximo três trimestres observados e pode ser efeito do dataset. RevOps precisa confirmar se é processo comercial.</li>
      <li><strong>Passar de ${DATA.maxCycle} dias não prova que um deal morreu.</strong> Por isso, a decisão fica com o vendedor.</li>
      <li><strong>O CRM não registra atividade</strong>, como e-mails, reuniões ou último contato. "Parado" aqui significa apenas tempo em Engaging.</li>
      <li><strong>A idade é a única medida de tempo.</strong> Não há histórico de mudanças de estágio, e deals em Prospecting não têm data.</li>
    </ul>
  </div>`;
}

function renderView(sel) {
  const views = { foco: viewFoco, decidir: viewDecidir, prospeccao: viewProspeccao, equipe: viewEquipe, como: viewComo };
  document.getElementById("view").innerHTML = views[state.tab](sel);
}

function render() {
  const sel = selection();
  renderFilters();
  renderBriefing(sel);
  renderTiles(sel);
  renderTabs(sel);
  renderView(sel);
}

function changeFilter(update) {
  Object.assign(state, update, { limit: PAGE_SIZE });
  writeStorage(STORAGE_AGENT, state.agent);
  render();
}

function exportDecisions() {
  const byId = new Map(DATA.engaged.map((deal) => [deal.id, deal]));
  const quote = (value) => `"${String(value ?? "").replace(/"/g, '""')}"`;
  const header = ["opportunity_id", "vendedor", "produto", "conta", "idade_dias", "valor_tabela", "decisao"];
  const rows = Object.entries(state.decisions)
    .filter(([id]) => byId.has(id))
    .map(([id, decision]) => {
      const deal = byId.get(id);
      return [id, deal.agent, deal.product, deal.account, deal.age, deal.price, decision].map(quote).join(",");
    });
  const blob = new Blob(["﻿" + [header.join(","), ...rows].join("\r\n")], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "decisoes-deals-parados.csv";
  link.click();
  URL.revokeObjectURL(link.href);
}

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
  state.tab = button.dataset.tab;
  state.limit = PAGE_SIZE;
  render();
  document.querySelector(`[data-tab="${state.tab}"]`).focus();
});

document.getElementById("view").addEventListener("click", (event) => {
  const target = event.target.closest("button");
  if (!target) return;
  if (target.dataset.go) {
    state.tab = target.dataset.go;
    state.limit = PAGE_SIZE;
    render();
  } else if (target.dataset.action === "more") {
    state.limit += PAGE_SIZE;
    renderView(selection());
  } else if (target.dataset.action === "export") {
    exportDecisions();
  } else if (target.dataset.agent) {
    state.tab = "foco";
    changeFilter({ agent: target.dataset.agent });
    window.scrollTo(0, 0);
  } else if (target.dataset.decision) {
    const { id, decision } = target.dataset;
    if (state.decisions[id] === decision) delete state.decisions[id];
    else state.decisions[id] = decision;
    writeStorage(STORAGE_DECISIONS, JSON.stringify(state.decisions));
    const buttons = target.parentElement.querySelectorAll("[data-decision]");
    buttons.forEach((button) => button.setAttribute("aria-pressed", String(state.decisions[id] === button.dataset.decision)));
    const sel = selection();
    const decided = sel.decidir.filter((deal) => state.decisions[deal.id]).length;
    document.getElementById("decision-progress").textContent =
      `${count(decided)} de ${count(sel.decidir.length)} decididos · maior valor primeiro`;
  }
});

renderHeader();
render();

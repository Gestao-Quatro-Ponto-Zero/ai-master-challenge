import { createOpportunityRepository } from "./infrastructure/repositories/repository-factory.js";
import { createDashboardDataHook } from "./presentation/hooks/use-dashboard-data.js";
import { wireManagerCombobox } from "./presentation/widgets/manager-combobox.js";
import { normalizeSortDedupeStrings } from "./shared/filter-options-utils.js";

const rankingState = document.getElementById("ranking-state");
const rankingList = document.getElementById("ranking-list");
const kpiState = document.getElementById("kpi-state");
const kpiStrip = document.getElementById("kpi-strip");
const detailState = document.getElementById("detail-state");
const detailView = document.getElementById("detail-view");
const detailRetry = document.getElementById("detail-retry");
const detailClose = document.getElementById("detail-close");
const form = document.getElementById("filters-form");
const filtersClear = document.getElementById("filters-clear");
const resultCountEl = document.getElementById("result-count");
const repository = createOpportunityRepository();
const dashboardData = createDashboardDataHook(repository);
let selectedOpportunityId = null;
/** @type {string[]} */
let managersCache = [];
/** @type {ReturnType<typeof wireManagerCombobox> | null} */
let managerCombo = null;

const STAGE_LABELS = {
  Prospecting: "Prospecção",
  Engaging: "Engajamento",
  Won: "Ganho",
  Lost: "Perdido",
};

function formatMoney(value) {
  const n = Number(value);
  if (Number.isNaN(n)) return "—";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "USD" }).format(n);
}

function priorityBandLabel(band) {
  const b = String(band || "").toLowerCase();
  if (b === "high") return "Alta";
  if (b === "medium") return "Média";
  if (b === "low") return "Baixa";
  return "—";
}

function stageLabel(stage) {
  const s = String(stage || "");
  return STAGE_LABELS[s] || s || "—";
}

function makeBandBadge(band) {
  const span = document.createElement("span");
  const b = String(band || "").toLowerCase();
  span.className = `badge badge-band-${b === "high" || b === "medium" || b === "low" ? b : "low"}`;
  span.textContent = priorityBandLabel(band);
  return span;
}

function makeStageBadge(stage) {
  const span = document.createElement("span");
  span.className = "badge badge-stage";
  span.textContent = stageLabel(stage);
  return span;
}

function truncate(text, max) {
  const s = String(text || "");
  if (s.length <= max) return s;
  return `${s.slice(0, max - 1)}…`;
}

function setRankingState(kind, message) {
  rankingState.textContent = message;
  rankingState.classList.remove("state-loading", "state-error", "state-empty");
  if (kind === "loading") rankingState.classList.add("state-loading");
  if (kind === "error") rankingState.classList.add("state-error");
  if (kind === "empty") rankingState.classList.add("state-empty");
}

function setKpiState(kind, message) {
  kpiState.textContent = message;
  kpiState.classList.remove("state-loading", "state-error");
  if (kind === "loading") kpiState.classList.add("state-loading");
  if (kind === "error") kpiState.classList.add("state-error");
}

function appendFactGrid(parent, entries) {
  const dl = document.createElement("dl");
  dl.className = "detail-facts";
  entries.forEach(([term, def]) => {
    if (def === undefined || def === null || def === "") return;
    const dt = document.createElement("dt");
    dt.textContent = term;
    const dd = document.createElement("dd");
    dd.textContent = String(def);
    dl.append(dt, dd);
  });
  parent.appendChild(dl);
}

function appendBulletBlock(parent, title, items) {
  if (!items || !items.length) return;
  const h = document.createElement("p");
  h.className = "detail-list-title";
  h.textContent = title;
  parent.appendChild(h);
  const ul = document.createElement("ul");
  ul.className = "detail-bullet-list";
  items.forEach((t) => {
    const li = document.createElement("li");
    li.textContent = t;
    ul.appendChild(li);
  });
  parent.appendChild(ul);
}

function renderDetailPayload(payload) {
  detailView.replaceChildren();
  const expl = payload.scoreExplanation;
  const closeVal = payload.close_value ?? payload.amount;

  const hero = document.createElement("div");
  hero.className = "detail-hero";
  const scoreEl = document.createElement("div");
  scoreEl.className = "detail-hero-score";
  scoreEl.textContent = expl ? String(expl.score) : "—";
  const meta = document.createElement("div");
  meta.className = "detail-hero-meta";
  const idLine = document.createElement("div");
  idLine.className = "detail-hero-id";
  idLine.textContent = `Oportunidade ${payload.id}`;
  meta.appendChild(idLine);
  if (expl) {
    const badges = document.createElement("div");
    badges.style.display = "flex";
    badges.style.flexWrap = "wrap";
    badges.style.gap = "8px";
    badges.appendChild(makeBandBadge(expl.priority_band));
    badges.appendChild(makeStageBadge(payload.deal_stage));
    meta.appendChild(badges);
  }
  hero.append(scoreEl, meta);
  detailView.appendChild(hero);

  const factsCard = document.createElement("section");
  factsCard.className = "detail-card";
  const hFacts = document.createElement("h3");
  hFacts.className = "detail-card-title";
  hFacts.textContent = "Resumo comercial";
  factsCard.appendChild(hFacts);
  appendFactGrid(factsCard, [
    ["Conta", payload.account || payload.title],
    ["Produto", payload.product],
    ["Série", payload.product_series],
    ["Vendedor", payload.sales_agent || payload.seller],
    ["Gestor", payload.manager],
    ["Escritório regional", payload.regional_office || payload.region],
    ["Valor de fecho", formatMoney(closeVal)],
    ["Data de engajamento", payload.engage_date],
    ["Data de fecho", payload.close_date],
  ]);
  detailView.appendChild(factsCard);

  if (expl) {
    const whyCard = document.createElement("section");
    whyCard.className = "detail-card";
    const hWhy = document.createElement("h3");
    hWhy.className = "detail-card-title";
    hWhy.textContent = "Porque este score?";
    whyCard.appendChild(hWhy);
    appendBulletBlock(whyCard, "O que aumenta a prioridade", expl.positive_factors);
    appendBulletBlock(whyCard, "O que reduz a prioridade", expl.negative_factors);
    appendBulletBlock(whyCard, "Alertas", expl.risk_flags);
    detailView.appendChild(whyCard);

    if (expl.next_action) {
      const na = document.createElement("div");
      na.className = "detail-next-action";
      na.textContent = `Próxima ação sugerida: ${expl.next_action}`;
      detailView.appendChild(na);
    }
  }
}

async function loadKpis() {
  setKpiState("loading", "A carregar indicadores…");
  kpiStrip.hidden = true;
  kpiStrip.replaceChildren();
  try {
    const data = await repository.getDashboardKpis();
    kpiState.textContent = "Indicadores atualizados.";
    kpiState.classList.remove("state-loading", "state-error");
    kpiStrip.hidden = false;
    const cards = [
      ["Total de oportunidades", data.total_opportunities],
      ["Em aberto (pipeline)", data.open_opportunities],
      ["Ganhas", data.won_opportunities],
      ["Perdidas", data.lost_opportunities],
      ["Score médio", data.avg_score],
    ];
    cards.forEach(([label, val]) => {
      const card = document.createElement("div");
      card.className = "kpi-card";
      const lb = document.createElement("span");
      lb.className = "kpi-label";
      lb.textContent = label;
      const vv = document.createElement("strong");
      vv.className = "kpi-value";
      vv.textContent = String(val);
      card.append(lb, vv);
      kpiStrip.appendChild(card);
    });
  } catch {
    setKpiState("error", "Não foi possível carregar os indicadores. Verifique a API e tente recarregar a página.");
  }
}

function buildFilterObject() {
  const region = document.getElementById("filter-region").value.trim();
  const manager = document.getElementById("manager-value").value.trim();
  const dealStage = document.getElementById("filter-deal-stage").value.trim();
  const q = document.getElementById("search-q").value.trim();
  const priorityBand = document.getElementById("priority-band").value.trim();
  /** @type {Record<string, string | number>} */
  const filters = { limit: 20 };
  if (region) filters.region = region;
  if (manager) filters.manager = manager;
  if (dealStage) filters.deal_stage = dealStage;
  if (q) filters.q = q;
  if (priorityBand) filters.priority_band = priorityBand;
  return filters;
}

async function initFilterWidgets() {
  const wrap = document.getElementById("manager-combobox-root");
  const searchInput = document.getElementById("manager-search");
  const hiddenInput = document.getElementById("manager-value");
  const listEl = document.getElementById("manager-listbox");
  const hintEl = document.getElementById("manager-hint");
  const emptyEl = document.getElementById("manager-empty");

  if (managerCombo?.destroy) {
    managerCombo.destroy();
  }
  managerCombo = null;

  hintEl.textContent = "A carregar gestores…";
  searchInput.disabled = true;
  searchInput.setAttribute("aria-busy", "true");

  try {
    const opts = await repository.getDashboardFilterOptions();
    const offices = normalizeSortDedupeStrings(
      opts.regional_offices?.length ? opts.regional_offices : opts.regions,
    );
    managersCache = normalizeSortDedupeStrings(opts.managers);
    const stages = normalizeSortDedupeStrings(opts.deal_stages);

    const regionSel = document.getElementById("filter-region");
    regionSel.replaceChildren();
    const ro = document.createElement("option");
    ro.value = "";
    ro.textContent = "Selecione o escritório (ou Todos)";
    regionSel.appendChild(ro);
    offices.forEach((name) => {
      const o = document.createElement("option");
      o.value = name;
      o.textContent = name;
      regionSel.appendChild(o);
    });

    const stageSel = document.getElementById("filter-deal-stage");
    stageSel.replaceChildren();
    const so = document.createElement("option");
    so.value = "";
    so.textContent = "Todos os estágios";
    stageSel.appendChild(so);
    const stageOrder = ["Prospecting", "Engaging", "Won", "Lost"];
    const ordered = stageOrder.filter((code) => stages.includes(code));
    const rest = stages.filter((s) => !stageOrder.includes(s));
    [...ordered, ...rest].forEach((code) => {
      const o = document.createElement("option");
      o.value = code;
      o.textContent = stageLabel(code);
      stageSel.appendChild(o);
    });

    managerCombo = wireManagerCombobox({
      rootEl: wrap,
      searchInput,
      hiddenInput,
      listEl,
      hintEl,
      emptyEl,
      getOptions: () => managersCache,
    });
    hintEl.textContent =
      "Clique ou foco para ver todos os gestores. Digite para filtrar.";
  } catch {
    managersCache = [];
    hintEl.textContent = "Não foi possível carregar a lista de gestores.";
    managerCombo = wireManagerCombobox({
      rootEl: wrap,
      searchInput,
      hiddenInput,
      listEl,
      hintEl,
      emptyEl,
      getOptions: () => managersCache,
    });
  } finally {
    searchInput.disabled = false;
    searchInput.setAttribute("aria-busy", "false");
  }
}

async function loadRanking() {
  setRankingState("loading", "A carregar oportunidades…");
  resultCountEl.textContent = "";
  rankingList.innerHTML = "";
  try {
    const filters = buildFilterObject();
    const { payload } = await dashboardData.loadRanking(filters);
    if (!payload.items.length) {
      setRankingState(
        "empty",
        "Nenhum resultado com estes filtros. Limpe os filtros ou ajuste a pesquisa.",
      );
      resultCountEl.textContent = "0 oportunidades";
      detailState.textContent = "Sem oportunidades para mostrar no painel.";
      detailView.replaceChildren();
      detailRetry.hidden = true;
      selectedOpportunityId = null;
      return;
    }
    resultCountEl.textContent = `${payload.total.toLocaleString("pt-BR")} oportunidade(s) no resultado`;
    rankingState.textContent = "Ranking atualizado (ordenado por score).";
    rankingState.classList.remove("state-loading", "state-error", "state-empty");

    const hasSelectedInCurrentResult = payload.items.some((item) => item.id === selectedOpportunityId);
    if (!hasSelectedInCurrentResult) selectedOpportunityId = payload.items[0].id;

    payload.items.forEach((item, index) => {
      const tr = document.createElement("tr");
      tr.tabIndex = 0;
      tr.setAttribute("role", "button");
      tr.setAttribute("aria-label", `Abrir detalhe da oportunidade ${item.id}`);
      if (item.id === selectedOpportunityId) tr.classList.add("is-selected");
      if (index === 0) tr.classList.add("is-top-pick");

      const mkTd = (content) => {
        const td = document.createElement("td");
        if (typeof content === "string" || typeof content === "number") {
          td.textContent = String(content);
        } else {
          td.appendChild(content);
        }
        return td;
      };

      const nextRaw = item.nextBestAction || item.next_action || "";
      const cells = [
        mkTd(item.id),
        mkTd(item.account || item.title),
        mkTd(item.product || "—"),
        mkTd(item.sales_agent || item.seller),
        mkTd(item.manager),
        mkTd(item.regional_office || item.region),
        mkTd(makeStageBadge(item.deal_stage)),
        mkTd(formatMoney(item.close_value ?? item.amount)),
        mkTd(String(item.score)),
        mkTd(makeBandBadge(item.priority_band)),
      ];
      const actionTd = document.createElement("td");
      actionTd.className = "next-action-cell";
      actionTd.textContent = truncate(nextRaw, 72);

      const btnTd = document.createElement("td");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Detalhe";
      btn.addEventListener("click", (event) => {
        event.stopPropagation();
        loadDetail(item.id);
      });
      btnTd.appendChild(btn);

      tr.append(...cells, actionTd, btnTd);
      tr.addEventListener("click", () => loadDetail(item.id));
      tr.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          loadDetail(item.id);
        }
      });
      rankingList.appendChild(tr);
    });
    if (selectedOpportunityId) await loadDetail(selectedOpportunityId);
  } catch {
    setRankingState("error", "Não foi possível carregar o ranking. Verifique a API e tente novamente.");
    resultCountEl.textContent = "";
  }
}

async function loadDetail(id) {
  selectedOpportunityId = id;
  detailState.textContent = "A carregar detalhe…";
  detailView.replaceChildren();
  detailRetry.hidden = true;
  try {
    const { payload } = await dashboardData.loadDetail(id);
    detailState.textContent = `Oportunidade ${payload.id} — explicação pronta para decisão.`;
    renderDetailPayload(payload);
    Array.from(rankingList.querySelectorAll("tr")).forEach((row) => {
      const first = row.querySelector("td");
      row.classList.toggle("is-selected", !!(first && first.textContent === id));
    });
  } catch (err) {
    if (String(err).includes("404") || String(err).toLowerCase().includes("not found")) {
      detailState.textContent = "Oportunidade não encontrada.";
    } else if (String(err).toLowerCase().includes("abort")) {
      detailState.textContent = "Pedido de detalhe cancelado.";
    } else {
      detailState.textContent = "Erro ao carregar o detalhe. Use «Tentar novamente».";
    }
    detailRetry.hidden = false;
  }
}

detailRetry.addEventListener("click", async () => {
  if (selectedOpportunityId) await loadDetail(selectedOpportunityId);
});

detailClose.addEventListener("click", () => {
  selectedOpportunityId = null;
  detailState.textContent = "Selecione uma linha na tabela.";
  detailView.replaceChildren();
  detailRetry.hidden = true;
  Array.from(rankingList.querySelectorAll("tr")).forEach((row) => row.classList.remove("is-selected"));
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  await loadRanking();
});

filtersClear.addEventListener("click", async () => {
  document.getElementById("filter-region").value = "";
  document.getElementById("filter-deal-stage").value = "";
  document.getElementById("search-q").value = "";
  document.getElementById("priority-band").value = "";
  if (managerCombo) managerCombo.reset();
  await loadRanking();
});

async function bootstrap() {
  await loadKpis();
  try {
    await initFilterWidgets();
  } catch {
    /* filter-options falhou: selects ficam mínimos; ranking ainda pode correr */
  }
  await loadRanking();
}

bootstrap();

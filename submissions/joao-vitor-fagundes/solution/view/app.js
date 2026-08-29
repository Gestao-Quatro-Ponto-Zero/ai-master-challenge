const STAGES = ["Prospecting", "Engaging", "Won", "Lost"];
const BOARD_BATCH_SIZE = 14;
const requestedView = new URLSearchParams(window.location.search).get("view");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

const state = {
  data: null,
  filtered: [],
  page: 1,
  pageSize: 40,
  view: ["board", "list"].includes(requestedView) ? requestedView : "board",
  boardLimits: {
    Prospecting: BOARD_BATCH_SIZE,
    Engaging: BOARD_BATCH_SIZE,
    Won: BOARD_BATCH_SIZE,
    Lost: BOARD_BATCH_SIZE,
  },
  activeOpportunity: null,
  opportunityDetails: new Map(),
  recommendations: new Map(),
  recommendationRequests: new Map(),
  columnObservers: new Map(),
  columnObserverFrame: null,
  lastFocusedElement: null,
  eventsBound: false,
};

const elements = {
  systemState: document.querySelector("#system-state"),
  scoreVersion: document.querySelector("#score-version"),
  totalRecordCount: document.querySelector("#total-record-count"),
  snapshotDate: document.querySelector("#snapshot-date"),
  sidebarActiveCount: document.querySelector("#sidebar-active-count"),
  activeCount: document.querySelector("#active-count"),
  pipelineValue: document.querySelector("#pipeline-value"),
  staleCount: document.querySelector("#stale-count"),
  missingAccountCount: document.querySelector("#missing-account-count"),
  viewButtons: [...document.querySelectorAll("[data-view]")],
  filters: document.querySelector("#filters"),
  search: document.querySelector("#search"),
  sellerFilter: document.querySelector("#seller-filter"),
  regionFilter: document.querySelector("#region-filter"),
  productFilter: document.querySelector("#product-filter"),
  attentionFilter: document.querySelector("#attention-filter"),
  sortOrder: document.querySelector("#sort-order"),
  resultDescription: document.querySelector("#result-description"),
  activeFilters: document.querySelector("#active-filters"),
  filterToggle: document.querySelector("#filter-toggle"),
  filterPanel: document.querySelector("#filter-panel"),
  filterCount: document.querySelector("#filter-count"),
  resetFiltersPanel: document.querySelector("#reset-filters-panel"),
  densityToggle: document.querySelector("#density-toggle"),
  mobileNav: document.querySelector("#mobile-nav"),
  closeMobileNav: document.querySelector("#close-mobile-nav"),
  mobileNavBackdrop: document.querySelector("#mobile-nav-backdrop"),
  loadingState: document.querySelector("#loading-state"),
  pipelineWorkspace: document.querySelector("#pipeline-workspace"),
  loadingProgress: document.querySelector("#loading-progress"),
  errorState: document.querySelector("#error-state"),
  retryLoad: document.querySelector("#retry-load"),
  boardView: document.querySelector("#board-view"),
  board: document.querySelector("#pipeline-board"),
  listView: document.querySelector("#list-view"),
  rows: document.querySelector("#opportunity-rows"),
  emptyState: document.querySelector("#empty-state"),
  resetFilters: document.querySelector("#reset-filters"),
  paginationSummary: document.querySelector("#pagination-summary"),
  pageIndicator: document.querySelector("#page-indicator"),
  previousPage: document.querySelector("#previous-page"),
  nextPage: document.querySelector("#next-page"),
  backdrop: document.querySelector("#drawer-backdrop"),
  drawer: document.querySelector("#detail-drawer"),
  detailTitle: document.querySelector("#detail-title"),
  detailSubtitle: document.querySelector("#detail-subtitle"),
  drawerContent: document.querySelector("#drawer-content"),
  closeDrawer: document.querySelector("#close-drawer"),
  drawerCompanySymbol: document.querySelector("#drawer-company-symbol"),
  previousRecord: document.querySelector("#previous-record"),
  nextRecord: document.querySelector("#next-record"),
  modalValue: document.querySelector("#modal-value"),
  modalOwner: document.querySelector("#modal-owner"),
  modalAttention: document.querySelector("#modal-attention"),
  modalProductLine: document.querySelector("#modal-product-line"),
  modalAccountLine: document.querySelector("#modal-account-line"),
  modalManager: document.querySelector("#modal-manager"),
  modalRegion: document.querySelector("#modal-region"),
  modalEngagement: document.querySelector("#modal-engagement"),
  modalPriority: document.querySelector("#modal-priority"),
  modalPriorityScore: document.querySelector("#modal-priority-score"),
  modalPriorityScale: document.querySelector("#modal-priority-scale"),
  modalStageTrack: document.querySelector("#modal-stage-track"),
};

const currency = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

const compactCurrency = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "USD",
  notation: "compact",
  maximumFractionDigits: 1,
});

const integer = new Intl.NumberFormat("pt-BR");
const decimal = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 });

const powerLibraryLoads = new Map();

function loadPowerLibrary(src, ready) {
  if (ready()) return Promise.resolve();
  if (powerLibraryLoads.has(src)) return powerLibraryLoads.get(src);
  const request = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = src;
    script.async = true;
    script.onload = () => ready() ? resolve() : reject(new Error(`Library did not initialize: ${src}`));
    script.onerror = () => reject(new Error(`Could not load local library: ${src}`));
    document.head.append(script);
  });
  powerLibraryLoads.set(src, request);
  return request;
}

async function ensurePowerLibraries() {
  await Promise.all([
    loadPowerLibrary("./vendor/echarts/echarts.min.js?v=6.1.0", () => Boolean(window.echarts)),
    loadPowerLibrary("./vendor/d3-thermometer/d3.min.js?v=4.13.0", () => Boolean(window.d3)),
  ]);
  await loadPowerLibrary("./vendor/d3-thermometer/thermometer.min.js?v=1.2.0", () => Boolean(window.Thermometer));
}

const dateFormatter = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  timeZone: "UTC",
});

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function slugify(value) {
  return String(value)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

function formatDate(value) {
  return value ? dateFormatter.format(new Date(`${value}T00:00:00Z`)) : "Não registrada";
}

function formatPercent(value) {
  return value === null || value === undefined ? "Sem histórico" : `${Math.round(value)}%`;
}

function getInitials(name) {
  const parts = String(name || "Não informado")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  return (parts[0]?.[0] || "N") + (parts.at(-1)?.[0] || "I");
}

function getSymbolClass(value) {
  const classes = ["symbol-violet", "symbol-blue", "symbol-coral", "symbol-green", "symbol-amber"];
  const total = [...String(value || "")].reduce((sum, letter) => sum + letter.charCodeAt(0), 0);
  return classes[total % classes.length];
}

function getAccountName(opportunity) {
  return opportunity.account || "Conta não informada";
}

function getAgeLabel(opportunity) {
  if (opportunity.age_days === null) return "Sem data";
  return `${integer.format(opportunity.age_days)} ${Number(opportunity.age_days) === 1 ? "dia" : "dias"}`;
}

function formatRevenueMillions(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "Não informada";
  return `US$ ${decimal.format(Number(value))} mi`;
}

function renderStageTrack(currentStage) {
  const currentIndex = STAGES.indexOf(currentStage);
  return STAGES.map((stage, index) => {
    let stepState = "is-upcoming";
    if (stage === currentStage) stepState = "is-current";
    else if (index < currentIndex && index < 2) stepState = "is-complete";
    else if (["Won", "Lost"].includes(stage) && ["Won", "Lost"].includes(currentStage)) stepState = "is-alternative";
    const current = stage === currentStage ? ' aria-current="step"' : "";
    return `<li class="stage-step stage-${slugify(stage)} ${stepState}"${current}><i></i><span>${escapeHtml(stage)}</span></li>`;
  }).join("");
}

function populateSelect(select, values) {
  const selectedValue = select.value;
  const firstOption = select.options[0]?.cloneNode(true);
  select.replaceChildren();
  if (firstOption) select.append(firstOption);
  const fragment = document.createDocumentFragment();
  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    fragment.append(option);
  });
  select.append(fragment);
  if (values.includes(selectedValue)) select.value = selectedValue;
}

function resetBoardLimits() {
  STAGES.forEach((stage) => {
    state.boardLimits[stage] = BOARD_BATCH_SIZE;
  });
}

function getWarmthContext(opportunity) {
  const copies = {
    "Sem contato": {
      title: "No engagement recorded",
      body: "The source has no engage date for this opportunity. Warmth remains zero; missing activity is not treated as positive evidence.",
    },
    Quente: {
      title: "Warmth · Quente",
      body: `${integer.format(opportunity.age_days || 0)} days have elapsed since engagement, inside the current 0–8 day temperature band.`,
    },
    Morna: {
      title: "Warmth · Morna",
      body: `${integer.format(opportunity.age_days || 0)} days have elapsed since engagement, inside the current 9–45 day temperature band.`,
    },
    Fria: {
      title: "Warmth · Fria",
      body: `${integer.format(opportunity.age_days || 0)} days have elapsed since engagement, inside the current 46–85 day temperature band.`,
    },
    Estagnada: {
      title: "Warmth · Estagnada",
      body: `${integer.format(opportunity.age_days || 0)} days have elapsed since engagement, above the current 85 day temperature band.`,
    },
  };
  if (opportunity.stage === "Won") {
    return { title: "Closed · Won", body: "POWER preserves the evidence that was available at the historical scoring date." };
  }
  if (opportunity.stage === "Lost") {
    return { title: "Closed · Lost", body: "The record remains available as historical evidence; no loss reason is inferred." };
  }
  return copies[opportunity.attention] || { title: "Warmth unavailable", body: "No temperature context is available for this opportunity." };
}

function renderStaticSummary() {
  const { meta } = state.data;
  const scoreVersion = state.data.opportunities.find((item) => item.score_version)?.score_version || "POWER";
  const totalAvailable = meta.total_available || meta.total_opportunities;
  const isPipelineLoading = meta.load_state === "loading";

  elements.systemState.classList.remove("is-loading", "is-error", "is-ready");
  if (meta.load_state === "loading") {
    elements.systemState.classList.add("is-loading");
    elements.scoreVersion.textContent = "Syncing dataset";
  } else if (meta.load_state === "partial") {
    elements.systemState.classList.add("is-error");
    elements.scoreVersion.textContent = "Partial read model";
  } else {
    elements.systemState.classList.add("is-ready");
    elements.scoreVersion.textContent = scoreVersion;
  }
  elements.totalRecordCount.textContent = integer.format(totalAvailable);
  if (elements.loadingProgress) {
    elements.loadingProgress.textContent = `Loading ${integer.format(meta.total_opportunities)} of ${integer.format(totalAvailable)} opportunities…`;
  }
  elements.snapshotDate.textContent = formatDate(meta.snapshot_date);
  elements.activeCount.textContent = integer.format(totalAvailable);
  elements.activeCount.classList.remove("metric-placeholder");
  elements.sidebarActiveCount.textContent = integer.format(totalAvailable);
  elements.pipelineValue.textContent = isPipelineLoading ? "" : compactCurrency.format(meta.pipeline_value);
  elements.staleCount.textContent = isPipelineLoading ? "" : integer.format(meta.stale_opportunities);
  elements.missingAccountCount.textContent = isPipelineLoading ? "" : integer.format(meta.missing_account);
  [elements.pipelineValue, elements.staleCount, elements.missingAccountCount].forEach((element) => {
    element.classList.toggle("metric-placeholder", isPipelineLoading);
  });
}

function updateControls() {
  elements.viewButtons.forEach((button) => {
    const isActive = button.dataset.view === state.view;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  });
}

function hasActiveFilters() {
  return Boolean(
    elements.search.value.trim() ||
    elements.sellerFilter.value ||
    elements.regionFilter.value ||
    elements.productFilter.value ||
    elements.attentionFilter.value,
  );
}

function getFilteredOpportunities() {
  const query = elements.search.value.trim().toLocaleLowerCase("pt-BR");
  const seller = elements.sellerFilter.value;
  const region = elements.regionFilter.value;
  const product = elements.productFilter.value;
  const attention = elements.attentionFilter.value;

  const results = state.data.opportunities.filter((opportunity) => {
    return (
      (!query || opportunity._search.includes(query)) &&
      (!seller || opportunity.seller === seller) &&
      (!region || opportunity.region === region) &&
      (!product || opportunity.product === product) &&
      (!attention ||
        (attention === "Com pendência"
          ? opportunity.issues.length > 0
          : opportunity.attention === attention))
    );
  });

  results.sort((a, b) => {
    if (elements.sortOrder.value === "value-desc") {
      return (b.potential_value || 0) - (a.potential_value || 0);
    }
    if (elements.sortOrder.value === "age-desc") {
      return (b.age_days ?? -1) - (a.age_days ?? -1);
    }
    if (elements.sortOrder.value === "age-asc") {
      return (a.age_days ?? Number.MAX_SAFE_INTEGER) - (b.age_days ?? Number.MAX_SAFE_INTEGER);
    }
    if (elements.sortOrder.value === "account") {
      return getAccountName(a).localeCompare(getAccountName(b), "pt-BR");
    }
    const left = a.scores.PP === null || a.scores.PP === undefined ? null : Number(a.scores.PP);
    const right = b.scores.PP === null || b.scores.PP === undefined ? null : Number(b.scores.PP);
    if (left === null && right === null) return a.id.localeCompare(b.id);
    if (left === null) return 1;
    if (right === null) return -1;
    return (right - left) || a.id.localeCompare(b.id);
  });

  return results;
}

function renderFilterChips() {
  const filters = [
    ["search", "Busca", elements.search.value.trim()],
    ["seller", "Vendedor", elements.sellerFilter.value],
    ["region", "Região", elements.regionFilter.value],
    ["product", "Produto", elements.productFilter.value],
    ["attention", "Situação", elements.attentionFilter.value],
  ].filter(([, , value]) => value);

  elements.activeFilters.innerHTML = filters
    .map(
      ([key, label, value]) => `
        <span class="filter-chip">
          ${escapeHtml(label)}: ${escapeHtml(value)}
          <button type="button" data-clear-filter="${escapeHtml(key)}" aria-label="Remover filtro ${escapeHtml(label)}">×</button>
        </span>
      `,
    )
    .join("");
  elements.filterCount.textContent = String(filters.length);
  elements.filterCount.hidden = filters.length === 0;
}

function renderPowerPriority(score) {
  const value = score === null || score === undefined ? null : Number(score);
  if (!Number.isFinite(value)) {
    return `
      <span class="record-priority is-missing" title="POWER Priority indisponível: P ou E sem histórico suficiente">
        <span class="priority-score"><b>PP</b><em>Indisponível</em></span>
      </span>
    `;
  }
  const normalized = Math.max(0, Math.min(100, value));
  return `
    <span
      class="record-priority"
      title="POWER Priority ${normalized.toFixed(2).replace(".", ",")} de 100"
    >
      <span class="priority-score"><b>PP</b><em>${normalized.toFixed(1).replace(".", ",")}</em><small>/100</small></span>
    </span>
  `;
}

function renderKanbanCard(opportunity) {
  const accountName = getAccountName(opportunity);
  const companyLetter = accountName === "Conta não informada" ? "?" : accountName.charAt(0).toUpperCase();
  const dateLabel = opportunity.engage_date ? formatDate(opportunity.engage_date) : "Não informada";
  const priorityValue = opportunity.scores.PP === null || opportunity.scores.PP === undefined
    ? null
    : Number(opportunity.scores.PP);
  const priorityLabel = Number.isFinite(priorityValue)
    ? `${priorityValue} de 100`
    : "indisponível";

  return `
    <button
      class="record-card stage-${slugify(opportunity.stage)}"
      type="button"
      data-opportunity-id="${escapeHtml(opportunity.id)}"
      aria-label="Abrir detalhes de ${escapeHtml(opportunity.id)}, ${escapeHtml(getAccountName(opportunity))}, POWER Priority ${escapeHtml(priorityLabel)}"
    >
      <span class="record-head">
        <span class="company-symbol ${getSymbolClass(accountName)}">${escapeHtml(companyLetter)}</span>
        <span><strong>${escapeHtml(accountName)}</strong><small>${escapeHtml(opportunity.id)}</small></span>
        ${renderPowerPriority(opportunity.scores.PP)}
      </span>
      <span class="record-field">${escapeHtml(opportunity.product)}${opportunity.series ? ` · ${escapeHtml(opportunity.series)}` : ""}</span>
      <span class="record-grid">
        <span><svg class="icon" aria-hidden="true"><use href="#icon-calendar"></use></svg><small>Entrada</small><strong>${escapeHtml(dateLabel)}</strong></span>
        <span><svg class="icon" aria-hidden="true"><use href="#icon-money"></use></svg><small>Valor de lista</small><strong>${escapeHtml(currency.format(opportunity.potential_value || 0))}</strong></span>
      </span>
      <span class="record-foot">
        <span class="record-owner"><i class="avatar ${getSymbolClass(opportunity.seller).replace("symbol-", "avatar-")}">${escapeHtml(getInitials(opportunity.seller).toUpperCase())}</i><strong>${escapeHtml(opportunity.seller)}</strong></span>
        <em><svg class="icon"><use href="#icon-clock"></use></svg>${escapeHtml(getAgeLabel(opportunity))}</em>
      </span>
    </button>
  `;
}

function renderColumn(stage) {
  const stageItems = state.filtered.filter((opportunity) => opportunity.stage === stage);
  const visibleItems = stageItems.slice(0, state.boardLimits[stage]);
  const isPipelineLoading = state.data.meta.load_state === "loading";
  const stageTotal = hasActiveFilters()
    ? stageItems.length
    : (state.data.meta.stage_counts?.[stage] ?? stageItems.length);
  const totalValue = stageItems.reduce(
    (sum, opportunity) => sum + (opportunity.potential_value || 0),
    0,
  );

  let content = "";
  if (!stageItems.length) {
    content = isPipelineLoading
      ? `<div class="column-sync" role="status"><i></i><span>Loading ${escapeHtml(stage)}…</span></div>`
      : `
        <div class="column-empty">
          <span aria-hidden="true">0</span>
          <strong>No records in this stage</strong>
          <p>Change the search or remove an active filter.</p>
        </div>
      `;
  } else {
    content = `
      <div class="column-cards">${visibleItems.map((opportunity) => renderKanbanCard(opportunity)).join("")}</div>
      ${renderColumnTail(stage, visibleItems.length, stageItems.length, stageTotal, isPipelineLoading)}
    `;
  }

  return `
    <section class="pipeline-column" data-stage="${escapeHtml(stage)}" aria-labelledby="column-${slugify(stage)}">
      <header class="column-header">
        <div>
          <i class="stage-dot ${slugify(stage)}" aria-hidden="true"></i>
          <strong id="column-${slugify(stage)}">${escapeHtml(stage)}</strong>
          <span>${integer.format(stageTotal)}</span>
        </div>
        <div><small ${isPipelineLoading ? 'class="metric-placeholder" aria-label="Carregando"' : ""}>${isPipelineLoading ? "" : escapeHtml(compactCurrency.format(totalValue))}</small></div>
      </header>
      <div class="column-scroll" data-column-scroll="${escapeHtml(stage)}" tabindex="0" aria-label="Oportunidades em ${escapeHtml(stage)}">
        ${content}
      </div>
    </section>
  `;
}

function renderColumnTail(stage, visibleCount, itemCount, stageTotal, isPipelineLoading) {
  const remaining = itemCount - visibleCount;
  if (remaining > 0) {
    return `<button class="column-more" type="button" data-load-stage="${escapeHtml(stage)}" data-column-sentinel aria-label="Carregar mais oportunidades de ${escapeHtml(stage)}"><i aria-hidden="true"></i><span>Load ${integer.format(Math.min(BOARD_BATCH_SIZE, remaining))} more</span><small>${integer.format(visibleCount)} of ${integer.format(stageTotal)}</small></button>`;
  }
  if (isPipelineLoading) {
    return `<div class="column-sync" role="status"><i></i><span>${integer.format(visibleCount)} of ${integer.format(stageTotal)} ready · syncing</span></div>`;
  }
  return "";
}

function disconnectColumnObservers() {
  if (state.columnObserverFrame !== null) {
    window.cancelAnimationFrame(state.columnObserverFrame);
    state.columnObserverFrame = null;
  }
  state.columnObservers.forEach((observer) => observer.disconnect());
  state.columnObservers.clear();
}

function captureColumnScrollPositions() {
  return new Map(
    [...elements.board.querySelectorAll("[data-column-scroll]")].map((scroller) => [
      scroller.dataset.columnScroll,
      scroller.scrollTop,
    ]),
  );
}

function loadNextColumnBatch(stage, trigger) {
  const stageTotal = state.filtered.filter((opportunity) => opportunity.stage === stage).length;
  if (state.boardLimits[stage] >= stageTotal) return;
  const observer = state.columnObservers.get(stage);
  observer?.disconnect();
  trigger?.classList.add("is-loading");
  if (trigger) trigger.disabled = true;

  window.requestAnimationFrame(() => {
    state.boardLimits[stage] = Math.min(
      state.boardLimits[stage] + BOARD_BATCH_SIZE,
      stageTotal,
    );
    renderBoard(true);
  });
}

function bindColumnObservers() {
  if (!("IntersectionObserver" in window)) return;
  elements.board.querySelectorAll("[data-column-scroll]").forEach((scroller) => {
    const sentinel = scroller.querySelector("[data-column-sentinel]");
    if (!sentinel) return;
    const stage = scroller.dataset.columnScroll;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          loadNextColumnBatch(stage, sentinel);
        }
      },
      { root: scroller, rootMargin: "0px 0px 180px 0px", threshold: 0 },
    );
    observer.observe(sentinel);
    state.columnObservers.set(stage, observer);
  });
}

function renderBoard(preserveScroll = false) {
  const scrollPositions = preserveScroll ? captureColumnScrollPositions() : new Map();
  disconnectColumnObservers();
  elements.board.innerHTML = STAGES.map(renderColumn).join("");
  state.columnObserverFrame = window.requestAnimationFrame(() => {
    elements.board.querySelectorAll("[data-column-scroll]").forEach((scroller) => {
      scroller.scrollTop = scrollPositions.get(scroller.dataset.columnScroll) || 0;
    });
    bindColumnObservers();
    state.columnObserverFrame = null;
  });
}

function finalizeBoardInPlace() {
  disconnectColumnObservers();

  STAGES.forEach((stage) => {
    const column = [...elements.board.querySelectorAll("[data-stage]")]
      .find((candidate) => candidate.dataset.stage === stage);
    if (!column) return;

    const stageItems = state.filtered.filter((opportunity) => opportunity.stage === stage);
    const totalValue = stageItems.reduce(
      (sum, opportunity) => sum + (opportunity.potential_value || 0),
      0,
    );
    const count = column.querySelector(".column-header > div:first-child > span");
    const value = column.querySelector(".column-header > div:last-child > small");
    const scroller = column.querySelector("[data-column-scroll]");
    const cardContainer = scroller?.querySelector(".column-cards");

    const stageTotal = state.data.meta.stage_counts?.[stage] ?? stageItems.length;
    if (count) count.textContent = integer.format(stageTotal);
    if (value) value.textContent = compactCurrency.format(totalValue);
    if (!scroller || !cardContainer) return;

    scroller.querySelector(".column-more, .column-sync")?.remove();
    const visibleCount = cardContainer.children.length;
    scroller.insertAdjacentHTML(
      "beforeend",
      renderColumnTail(stage, visibleCount, stageItems.length, stageTotal, false),
    );
  });

  state.columnObserverFrame = window.requestAnimationFrame(() => {
    bindColumnObservers();
    state.columnObserverFrame = null;
  });
}

function renderListRow(opportunity) {
  const issueText = opportunity.issues.length
    ? `<span class="issue-flag">${opportunity.issues.length} pendência${opportunity.issues.length > 1 ? "s" : ""}</span>`
    : "";

  return `
    <button
      class="opportunity-row"
      type="button"
      data-opportunity-id="${escapeHtml(opportunity.id)}"
      aria-label="Abrir detalhes da oportunidade ${escapeHtml(opportunity.id)}"
    >
      <span class="cell">
        <span class="cell-id">${escapeHtml(opportunity.id)}</span>
        <span class="cell-secondary">${escapeHtml(opportunity.stage)}</span>
      </span>
      <span class="cell">
        <span class="cell-primary">${escapeHtml(getAccountName(opportunity))}</span>
        <span class="cell-secondary">${escapeHtml(opportunity.sector || "Setor não informado")}</span>
      </span>
      <span class="cell">
        <span class="cell-primary">${escapeHtml(opportunity.seller)}</span>
        <span class="cell-secondary">${escapeHtml(opportunity.region || "Sem região")}</span>
      </span>
      <span class="cell">
        <span class="cell-primary">${escapeHtml(opportunity.product)}</span>
        <span class="cell-secondary">${escapeHtml(opportunity.series || "Sem série")}</span>
      </span>
      <span class="cell">
        <span class="cell-value">${escapeHtml(currency.format(opportunity.potential_value || 0))}</span>
        <span class="cell-note">preço de lista</span>
      </span>
      <span class="cell">
        <span class="cell-primary">${escapeHtml(getAgeLabel(opportunity))}</span>
        <span class="cell-secondary">${escapeHtml(formatDate(opportunity.engage_date))}</span>
      </span>
      <span class="cell">
        <span class="attention-pill attention-${slugify(opportunity.attention)}">${escapeHtml(opportunity.attention)}</span>
        ${issueText}
      </span>
      <span class="cell"><span class="row-arrow" aria-hidden="true">↗</span></span>
    </button>
  `;
}

function renderRows() {
  const totalPages = Math.max(1, Math.ceil(state.filtered.length / state.pageSize));
  if (state.page > totalPages) state.page = totalPages;

  const start = (state.page - 1) * state.pageSize;
  const pageRows = state.filtered.slice(start, start + state.pageSize);
  elements.rows.innerHTML = pageRows.map(renderListRow).join("");

  const visibleStart = state.filtered.length ? start + 1 : 0;
  const visibleEnd = Math.min(start + state.pageSize, state.filtered.length);
  elements.paginationSummary.textContent = `${integer.format(visibleStart)}–${integer.format(visibleEnd)} de ${integer.format(state.filtered.length)}`;
  elements.pageIndicator.textContent = `${state.page} / ${totalPages}`;
  elements.previousPage.disabled = state.page <= 1;
  elements.nextPage.disabled = state.page >= totalPages;
}

function renderEmptyState() {
  const shouldShow = state.filtered.length === 0;

  elements.emptyState.hidden = !shouldShow;
  if (!shouldShow) return;

  const title = elements.emptyState.querySelector("h3");
  const description = elements.emptyState.querySelector("p");
  const action = elements.emptyState.querySelector("button");
  title.textContent = "Nenhuma oportunidade neste recorte";
  description.textContent = "Altere a busca ou remova um dos filtros ativos.";
  action.textContent = "Limpar filtros";
}

function renderResultDescription() {
  const filteredValue = state.filtered.reduce(
    (sum, opportunity) => sum + (opportunity.potential_value || 0),
    0,
  );
  const { meta } = state.data;
  const totalAvailable = meta.total_available || meta.total_opportunities;
  if (meta.load_state === "loading" && !hasActiveFilters()) {
    elements.resultDescription.innerHTML = `<strong>${integer.format(totalAvailable)}</strong> oportunidades · sincronizando valores`;
    return;
  }
  const loadMessage = meta.load_state === "loading"
    ? " · resultados parciais durante a sincronização"
    : meta.load_state === "partial"
      ? ` · base parcial ${integer.format(meta.total_opportunities)}/${integer.format(totalAvailable)}. Tente novamente`
      : "";
  elements.resultDescription.innerHTML = `<strong>${integer.format(state.filtered.length)}</strong> oportunidades · ${escapeHtml(currency.format(filteredValue))} em valor de lista${escapeHtml(loadMessage)}`;
}

function renderView(options = {}) {
  const isInitialReveal = !elements.loadingState.hidden;
  elements.errorState.hidden = true;
  const hasGlobalEmpty = state.filtered.length === 0;

  elements.boardView.hidden = state.view !== "board" || hasGlobalEmpty;
  elements.listView.hidden = state.view !== "list" || hasGlobalEmpty;

  if (state.view === "board") {
    renderBoard(Boolean(options.preserveBoardScroll));
  } else {
    disconnectColumnObservers();
    renderRows();
  }
  renderEmptyState();

  if (isInitialReveal) {
    window.requestAnimationFrame(() => {
      elements.loadingState.hidden = true;
    });
  } else {
    elements.loadingState.hidden = true;
  }
}

function render(options = {}) {
  if (!state.data) return;
  state.filtered = getFilteredOpportunities();
  renderResultDescription();
  renderFilterChips();
  updateControls();
  renderView(options);
}

function resetFilters() {
  elements.filters.reset();
  elements.sortOrder.value = "power-priority";
  state.page = 1;
  resetBoardLimits();
  render();
}

function clearFilter(key) {
  if (key === "search") elements.search.value = "";
  if (key === "seller") elements.sellerFilter.value = "";
  if (key === "region") elements.regionFilter.value = "";
  if (key === "product") elements.productFilter.value = "";
  if (key === "attention") elements.attentionFilter.value = "";
  state.page = 1;
  resetBoardLimits();
  render();
}

function renderHistoryCard(label, history) {
  return `
    <article class="history-card">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(formatPercent(history?.win_rate))}</strong>
      <small>${history ? `${integer.format(history.cases)} casos · ${integer.format(history.won)} ganhos` : "base insuficiente"}</small>
    </article>
  `;
}

function getPropensityLens(opportunity, name) {
  return opportunity.propensity_evidence?.lenses?.find((lens) => lens.name === name) || null;
}

function renderNumericPowerLens(letter, label, score, detail, descriptor) {
  const missing = score === null || score === undefined;
  const value = missing ? null : Math.max(0, Math.min(100, Number(score)));
  const roundedValue = missing ? null : Math.round(value);
  const chartType = letter === "P" ? "propensity" : "execution";
  return `
    <article class="power-lens power-lens-${letter.toLowerCase()} power-numeric-lens ${missing ? "is-missing" : ""}" aria-label="${escapeHtml(label)}: ${missing ? "indisponível" : `${roundedValue} de 100`}">
      <header class="power-lens-heading"><span>${letter}</span><small>${missing ? "Indisponível" : escapeHtml(descriptor)}</small></header>
      <div class="power-lens-visual power-meter-stage">
        ${missing
          ? `<div class="power-meter-empty" aria-hidden="true"><span>N/D</span><small>Sem pontuação</small></div>`
          : `<div class="power-echart" data-power-chart="${chartType}" data-value="${roundedValue}" role="meter" aria-label="${escapeHtml(label)}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${roundedValue}"></div>`}
      </div>
      <footer class="power-lens-caption"><strong>${escapeHtml(label)}</strong><span>${escapeHtml(detail)}</span></footer>
    </article>
  `;
}

function renderPropensityLens(score) {
  return renderNumericPowerLens(
    "P",
    "Propensity",
    score,
    score === null || score === undefined ? "Evidência histórica indisponível" : "Conversão histórica",
    "Intensidade · 0–100",
  );
}

const OPPORTUNITY_VALUE_TIERS = [
  { key: "bronze", label: "Bronze", badge: "./assets/power-ranks/bronze.png" },
  { key: "silver", label: "Prata", badge: "./assets/power-ranks/silver.png" },
  { key: "gold", label: "Ouro", badge: "./assets/power-ranks/gold.png" },
  { key: "diamond", label: "Diamante", badge: "./assets/power-ranks/diamond.png" },
];

function normalizeOpportunityValueTier(tier) {
  const aliases = {
    bronze: "bronze",
    silver: "silver",
    prata: "silver",
    gold: "gold",
    ouro: "gold",
    diamond: "diamond",
    diamante: "diamond",
  };
  return aliases[String(tier || "").trim().toLocaleLowerCase("pt-BR")] || null;
}

function renderOpportunityValueLens(tier) {
  const activeKey = normalizeOpportunityValueTier(tier);
  const activeTier = OPPORTUNITY_VALUE_TIERS.find((item) => item.key === activeKey) || null;

  return `
    <article class="power-lens power-lens-o power-value-lens ${activeTier ? "" : "is-missing"}" aria-label="Opportunity Value: ${activeTier ? `${activeTier.label}, faixa de valor` : "classificação indisponível"}">
      <header class="power-lens-heading"><span>O</span><small>${activeTier ? "Faixa de valor" : "Indisponível"}</small></header>
      <div class="power-lens-visual">
        ${activeTier ? `
          <div class="value-tier-composition">
            <div class="value-tier-hero" aria-hidden="true">
              <img src="${activeTier.badge}" alt="" width="66" height="66" />
              <strong>${activeTier.label}</strong>
            </div>
            <ol class="value-tier-scale" aria-label="Posição atual entre os tiers de valor">
              ${OPPORTUNITY_VALUE_TIERS.map((item) => `
                <li class="value-rank value-rank-${item.key} ${item.key === activeKey ? "is-active" : "is-muted"}" ${item.key === activeKey ? 'aria-current="true"' : ""}>
                  <img class="value-rank-emblem" src="${item.badge}" alt="" width="31" height="31" />
                  <span class="value-rank-copy"><b>${item.label}</b></span>
                </li>
              `).join("")}
            </ol>
          </div>
        ` : '<div class="power-meter-empty" aria-hidden="true"><span>N/D</span><small>Sem classificação</small></div>'}
      </div>
      <footer class="power-lens-caption"><strong>Opportunity Value</strong><span>${activeTier ? `${activeTier.label} · faixa de valor` : "Classificação indisponível"}</span></footer>
    </article>
  `;
}

const WARMTH_STATES = [
  { key: "hot", label: "Quente", source: "Quente", detail: "0–8 dias", level: 100, color: "#d65a4f" },
  { key: "warm", label: "Morna", source: "Morna", detail: "9–45 dias", level: 75, color: "#c4862f" },
  { key: "cold", label: "Fria", source: "Fria", detail: "46–85 dias", level: 50, color: "#5e82b7" },
  { key: "stagnant", label: "Estagnada", source: "Estagnada", detail: "> 85 dias", level: 25, color: "#bc6a66" },
  { key: "no-contact", label: "Sem contato", source: "Sem contato", detail: "Sem engajamento", level: 0, color: "#8d9299" },
];

function normalizeWarmthState(temperature) {
  const aliases = {
    quente: "hot",
    morna: "warm",
    fria: "cold",
    estagnada: "stagnant",
    "sem contato": "no-contact",
  };
  return aliases[String(temperature || "").trim().toLocaleLowerCase("pt-BR")] || null;
}

function renderWarmthLens(temperature, ageDays) {
  const activeKey = normalizeWarmthState(temperature);
  const activeState = WARMTH_STATES.find((item) => item.key === activeKey) || null;
  const parsedAgeDays = Number(ageDays);
  const hasRecordedContact = activeKey !== "no-contact"
    && ageDays !== null
    && ageDays !== undefined
    && ageDays !== ""
    && Number.isFinite(parsedAgeDays);
  const contactDetail = activeKey === "no-contact"
    ? "Nenhum contato registrado"
    : hasRecordedContact
      ? `Último contato há ${integer.format(parsedAgeDays)} ${parsedAgeDays === 1 ? "dia" : "dias"}`
      : activeState?.detail;
  const stateScale = WARMTH_STATES.map((item) => `
    <li class="warmth-state warmth-state-${item.key} ${item.key === activeKey ? "is-active" : "is-muted"}">
      <i aria-hidden="true"></i><span><b>${item.label}</b>${item.key === activeKey && activeKey === "no-contact" ? "<small>sem registro</small>" : ""}</span>
    </li>
  `).join("");

  return `
    <article class="power-lens power-lens-w power-warmth-lens ${activeState ? "" : "is-missing"}" aria-label="Warmth: ${activeState ? `${activeState.label}, ${activeState.detail}` : "classificação indisponível"}">
      <header class="power-lens-heading"><span>W</span><small>${activeState ? "Temperatura" : "Indisponível"}</small></header>
      <div class="power-lens-visual">
        <div class="warmth-instrument" aria-hidden="true">
          <div class="warmth-thermometer-canvas" data-power-thermometer data-value="${activeState?.level ?? 0}" data-color="${activeState?.color ?? "#8d9299"}"></div>
          <ol class="warmth-state-list">${stateScale}</ol>
        </div>
      </div>
      <footer class="power-lens-caption"><strong>Warmth</strong><span>${activeState ? contactDetail : "Classificação indisponível"}</span></footer>
    </article>
  `;
}

const EXECUTION_FIT_LABELS = {
  product: "Produto",
  sector: "Setor",
  ticket: "Ticket",
};

function renderExecutionFitLens(opportunity) {
  const score = opportunity.scores.E;
  const missing = score === null || score === undefined;
  const value = missing ? null : Math.max(0, Math.min(100, Number(score)));
  const roundedValue = missing ? null : Math.round(value);
  const fits = (opportunity.execution_fit_evidence?.fits || [])
    .filter((item) => item.fit !== null && item.fit !== undefined && Number.isFinite(Number(item.fit)))
    .map((item) => ({
      label: EXECUTION_FIT_LABELS[item.name] || item.name,
      value: Math.max(0, Math.min(100, Number(item.fit))),
    }));
  const breakdown = fits.length
    ? `<dl class="execution-fit-breakdown">${fits.map((item) => `
        <div><dt>${escapeHtml(item.label)}</dt><dd><span>${Math.round(item.value)}</span><i><b style="--fit:${item.value}%"></b></i></dd></div>
      `).join("")}</dl>`
    : '<p class="execution-fit-empty">Critérios detalhados indisponíveis</p>';

  return `
    <article class="power-lens power-lens-e power-execution-lens ${missing ? "is-missing" : ""}" aria-label="Execution Fit: ${missing ? "indisponível" : `${roundedValue} de 100`}">
      <header class="power-lens-heading"><span>E</span><small>${missing ? "Indisponível" : "Aderência · 0–100"}</small></header>
      <div class="power-lens-visual execution-fit-visual">
        ${missing
          ? '<div class="power-meter-empty" aria-hidden="true"><span>N/D</span><small>Sem pontuação</small></div>'
          : `<div class="power-echart" data-power-chart="execution" data-value="${roundedValue}" role="meter" aria-label="Execution Fit" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${roundedValue}"></div>${breakdown}`}
      </div>
      <footer class="power-lens-caption"><strong>Execution Fit</strong><span>${fits.length ? `${fits.length} critérios observados` : "Aderência do vendedor"}</span></footer>
    </article>
  `;
}

function renderRecommendationLensContent(opportunity) {
  const entry = state.recommendations.get(opportunity.id);
  let status = "Próxima ação";
  let keyword = "Definindo ação";
  let summary = "A recomendação será carregada automaticamente.";
  let detail = "Consultando resultado";
  let stateClass = "is-idle";
  let action = "";
  if (entry?.status === "loading") {
    status = "POWER em análise";
    keyword = "Definindo ação";
    summary = "Lendo P, O, W e E para indicar o próximo passo.";
    detail = "Consultando cache ou gerando";
    stateClass = "is-loading";
    action = `<span class="recommendation-progress" aria-hidden="true"></span>`;
  } else if (entry?.status === "error") {
    status = "Próxima ação";
    keyword = "Não foi possível gerar";
    summary = "Tente novamente; P, O, W e E continuam disponíveis.";
    detail = "Falha na geração";
    stateClass = "is-error";
    action = `<button type="button" data-retry-recommendation="${escapeHtml(opportunity.id)}">Tentar novamente</button>`;
  } else if (entry?.status === "ready") {
    status = "Faça agora";
    keyword = entry.recommendation?.action_label || "Agir";
    summary = entry.recommendation?.recommendation || "Execute a próxima ação indicada pelo POWER.";
    detail = entry.cached ? "Resultado salvo no CRM" : "Gerada e salva agora";
    stateClass = "is-ready";
    action = "";
  }
  return `
    <header class="power-lens-heading"><span>R</span><small>Próxima ação</small></header>
    <div class="power-lens-visual recommendation-readout ${stateClass}">
      <span>${escapeHtml(status)}</span>
      <strong>${escapeHtml(keyword)}</strong>
      <p>${escapeHtml(summary)}</p>
      ${action}
    </div>
    <footer class="power-lens-caption"><strong>Recommendation</strong><span>${escapeHtml(detail)}</span></footer>
  `;
}

function updateRecommendationPanel(opportunity) {
  const lens = elements.drawerContent.querySelector(`[data-recommendation-lens="${CSS.escape(opportunity.id)}"]`);
  if (lens) lens.innerHTML = renderRecommendationLensContent(opportunity);
}

async function ensureRecommendation(opportunity, force = false) {
  const current = state.recommendations.get(opportunity.id);
  if (!force && current?.status === "ready") {
    if (!current.cached) {
      state.recommendations.set(opportunity.id, { ...current, cached: true });
      updateRecommendationPanel(opportunity);
    }
    return;
  }
  if (!force && state.recommendationRequests.has(opportunity.id)) return state.recommendationRequests.get(opportunity.id);

  state.recommendations.set(opportunity.id, { status: "loading" });
  updateRecommendationPanel(opportunity);
  const request = window.POWER_BACKEND.generateRecommendation(opportunity.id)
    .then((result) => {
      state.recommendations.set(opportunity.id, {
        status: "ready",
        cached: Boolean(result.cached),
        recommendation: result.recommendation,
      });
    })
    .catch((error) => {
      state.recommendations.set(opportunity.id, { status: "error", error: error.message });
    })
    .finally(() => {
      state.recommendationRequests.delete(opportunity.id);
      if (state.activeOpportunity?.id === opportunity.id) updateRecommendationPanel(opportunity);
    });
  state.recommendationRequests.set(opportunity.id, request);
  return request;
}

function getPowerGaugeOption(type, value, reducedMotion) {
  const propensity = type === "propensity";
  const color = propensity ? "#6558d3" : "#26996b";
  return {
    animation: !reducedMotion,
    animationDuration: 1150,
    animationEasing: "cubicOut",
    series: [{
      type: "gauge",
      silent: true,
      min: 0,
      max: 100,
      splitNumber: propensity ? 4 : 0,
      center: ["50%", propensity ? "58%" : "50%"],
      radius: propensity ? "86%" : "78%",
      startAngle: propensity ? 205 : 90,
      endAngle: propensity ? -25 : -270,
      progress: propensity
        ? { show: false }
        : { show: true, roundCap: true, width: 6, itemStyle: { color } },
      axisLine: {
        roundCap: !propensity,
        lineStyle: {
          width: propensity ? 11 : 6,
          color: propensity
            ? [[.25, "#efacb3"], [.5, "#edc39f"], [.75, "#bad39b"], [1, "#6eae6a"]]
            : [[1, "#eceef1"]],
        },
      },
      pointer: propensity ? {
        show: true,
        icon: "path://M2 0 L-2 0 L-1.35 -52 L1.35 -52 Z",
        length: "54%",
        width: 4,
        offsetCenter: [0, "-4%"],
        itemStyle: { color: "#202329" },
      } : { show: false },
      anchor: propensity ? {
        show: true,
        showAbove: true,
        size: 8,
        itemStyle: { color: "#202329", borderColor: "#ffffff", borderWidth: 2 },
      } : { show: false },
      axisTick: { show: propensity, distance: -17, splitNumber: 3, length: 3, lineStyle: { color: "rgba(255,255,255,.82)", width: 1 } },
      splitLine: { show: propensity, distance: -18, length: 6, lineStyle: { color: "#ffffff", width: 1.3 } },
      axisLabel: {
        show: propensity,
        distance: 5,
        color: "#8f949d",
        fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif",
        fontSize: 7,
        formatter(label) { return label === 0 || label === 50 || label === 100 ? String(label) : ""; },
      },
      title: { show: false },
      detail: {
        valueAnimation: !reducedMotion,
        offsetCenter: [0, propensity ? "54%" : "3%"],
        formatter: propensity ? `{value|${value}}{unit| /100}` : `{value|${value}}\n{unit|/100}`,
        rich: {
          value: { color: "#202329", fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif", fontSize: propensity ? 34 : 31, fontWeight: 680, lineHeight: propensity ? 34 : 32 },
          unit: { color: "#90949b", fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif", fontSize: 8, fontWeight: 500, lineHeight: 11 },
        },
      },
      data: [{ value }],
    }],
  };
}

function mountPowerGauge(node, reducedMotion) {
  if (!window.echarts || !node.isConnected) return;
  const existing = window.echarts.getInstanceByDom(node);
  if (existing) existing.dispose();
  const chart = window.echarts.init(node, null, { renderer: "svg" });
  chart.setOption(getPowerGaugeOption(node.dataset.powerChart, Number(node.dataset.value || 0), reducedMotion));
  if (window.ResizeObserver) {
    const observer = new ResizeObserver(() => chart.resize());
    observer.observe(node);
    node.powerResizeObserver = observer;
  }
}

function mountWarmthThermometer(node, reducedMotion) {
  if (!window.Thermometer || !window.d3 || !node.isConnected) return;
  const value = Number(node.dataset.value || 0);
  const color = node.dataset.color || "#8d9299";
  const thermometer = new window.Thermometer({
    width: 64,
    height: 166,
    mercuryColor: color,
    bulbShineColor: "#ffffff",
    borderColor: "#c9cdd3",
    borderWidth: 1,
    backgroundColor: "#f5f6f7",
    bulbRadius: 14,
    tubeWidth: 12,
  });
  thermometer.render(node, reducedMotion ? value : 0, 0, 100);
  const svg = node.querySelector("svg");
  if (svg) {
    svg.setAttribute("viewBox", "0 0 64 166");
    svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
    svg.removeAttribute("width");
    svg.removeAttribute("height");
  }
  if (!reducedMotion) {
    const mercury = node.querySelector(".thermometer-mercury-column");
    if (mercury) {
      const top = thermometer._axisData.scale(value);
      const bottom = thermometer._dim.bulbCy;
      window.d3.select(mercury)
        .transition()
        .duration(900)
        .ease(window.d3.easeCubicOut)
        .attr("y", top)
        .attr("height", bottom - top);
    }
  }
  node.powerThermometer = thermometer;
}

function disposePowerVisuals(root = elements.drawerContent) {
  root.querySelectorAll("[data-power-chart]").forEach((node) => {
    node.powerResizeObserver?.disconnect();
    if (window.echarts) window.echarts.getInstanceByDom(node)?.dispose();
  });
  root.querySelectorAll("[data-power-thermometer]").forEach((node) => {
    try { node.powerThermometer?.destroy(); } catch (_error) { /* The SVG may already be detached. */ }
  });
}

async function animatePowerVisuals(panel) {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  panel.classList.add("is-loading-instruments");
  try {
    await ensurePowerLibraries();
    if (!panel.isConnected || panel.hidden) return;
    panel.querySelectorAll("[data-power-chart]").forEach((node) => mountPowerGauge(node, reducedMotion));
    panel.querySelectorAll("[data-power-thermometer]").forEach((node) => mountWarmthThermometer(node, reducedMotion));
    panel.classList.remove("is-instrument-error");
  } catch (error) {
    panel.classList.add("is-instrument-error");
    panel.querySelectorAll("[data-power-chart], [data-power-thermometer]").forEach((node) => {
      node.innerHTML = '<span class="power-instrument-error">Visual indisponível</span>';
    });
    console.error(error);
  } finally {
    panel.classList.remove("is-loading-instruments");
  }

  panel.classList.remove("is-entering");
  if (!reducedMotion) {
    void panel.offsetWidth;
    panel.classList.add("is-entering");
  }
}

function setPowerPillar(key, focusTab = false) {
  const tabs = [...elements.drawerContent.querySelectorAll("[data-power-pillar-tab]")];
  const lenses = [...elements.drawerContent.querySelectorAll(".power-lens")];
  tabs.forEach((tab) => {
    const active = tab.dataset.powerPillarTab === key;
    tab.classList.toggle("is-active", active);
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
    if (active && focusTab) tab.focus();
  });
  let activeLens = null;
  lenses.forEach((lens) => {
    const active = lens.classList.contains(`power-lens-${key}`);
    lens.classList.toggle("is-mobile-active", active);
    if (active) activeLens = lens;
  });
  if (activeLens) {
    requestAnimationFrame(() => {
      activeLens.querySelectorAll("[data-power-chart]").forEach((node) => {
        window.echarts?.getInstanceByDom(node)?.resize();
      });
    });
  }
}

function bindPowerPillarTabs() {
  const tabs = [...elements.drawerContent.querySelectorAll("[data-power-pillar-tab]")];
  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => setPowerPillar(tab.dataset.powerPillarTab));
    tab.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      let nextIndex = index;
      if (event.key === "ArrowLeft") nextIndex = index === 0 ? tabs.length - 1 : index - 1;
      if (event.key === "ArrowRight") nextIndex = index === tabs.length - 1 ? 0 : index + 1;
      if (event.key === "Home") nextIndex = 0;
      if (event.key === "End") nextIndex = tabs.length - 1;
      setPowerPillar(tabs[nextIndex].dataset.powerPillarTab, true);
    });
  });
  setPowerPillar("p");
}

function updateRecordNavigation(opportunity) {
  const index = state.filtered.findIndex((item) => item.id === opportunity.id);
  elements.previousRecord.disabled = index <= 0;
  elements.nextRecord.disabled = index < 0 || index >= state.filtered.length - 1;
}

function openDrawer(opportunity, trigger) {
  disposePowerVisuals();
  state.activeOpportunity = opportunity;
  if (trigger) state.lastFocusedElement = trigger;
  const issues = opportunity.issues.length
    ? `<ul class="issue-list">${opportunity.issues.map((issue) => `<li>${escapeHtml(issue)}</li>`).join("")}</ul>`
    : '<p class="no-issues">Nenhuma lacuna foi encontrada nos campos verificados por esta interface.</p>';
  const historyContent = opportunity._detailLoadError
    ? '<div class="history-load-error"><strong>As evidências não puderam ser carregadas</strong><p>As pontuações resumidas continuam visíveis, mas as lentes históricas deste registro estão indisponíveis.</p></div>'
    : `<div class="history-grid">${renderHistoryCard("Setor", getPropensityLens(opportunity, "sector"))}${renderHistoryCard("Produto", getPropensityLens(opportunity, "product"))}${renderHistoryCard("Ticket", getPropensityLens(opportunity, "ticket"))}</div>`;
  const accountName = getAccountName(opportunity);
  const ownerAvatarClass = getSymbolClass(opportunity.seller).replace("symbol-", "avatar-");
  const propensityScore = opportunity.scores.P === null || opportunity.scores.P === undefined
    ? null
    : Math.max(0, Math.min(100, Number(opportunity.scores.P)));
  const priorityScore = opportunity.scores.PP === null || opportunity.scores.PP === undefined
    ? null
    : Math.max(0, Math.min(100, Number(opportunity.scores.PP)));
  const isClosed = ["Won", "Lost"].includes(opportunity.stage);

  elements.detailTitle.textContent = accountName;
  elements.detailSubtitle.innerHTML = `<i class="stage-dot ${slugify(opportunity.stage)}"></i>${escapeHtml(opportunity.stage)} <b>·</b> ${escapeHtml(opportunity.id)}`;
  elements.drawerCompanySymbol.textContent = accountName === "Conta não informada" ? "?" : accountName.charAt(0).toUpperCase();
  elements.drawerCompanySymbol.className = `company-symbol company-symbol-large ${getSymbolClass(accountName)}`;
  elements.modalValue.textContent = currency.format(opportunity.potential_value || 0);
  elements.modalOwner.innerHTML = `<i class="avatar ${ownerAvatarClass}">${escapeHtml(getInitials(opportunity.seller).toUpperCase())}</i>${escapeHtml(opportunity.seller)}`;
  elements.modalAttention.innerHTML = `<i class="warmth-indicator warmth-${slugify(opportunity.attention)}"></i>${escapeHtml(opportunity.attention)}`;
  elements.modalProductLine.textContent = [opportunity.product, opportunity.series, opportunity.product_key].filter(Boolean).join(" · ") || "Produto não informado";
  elements.modalAccountLine.textContent = [
    opportunity.sector,
    opportunity.office_location,
    opportunity.account_employees !== null && opportunity.account_employees !== undefined
      ? `${integer.format(opportunity.account_employees)} colaboradores`
      : null,
    opportunity.account_revenue !== null && opportunity.account_revenue !== undefined
      ? formatRevenueMillions(opportunity.account_revenue)
      : null,
  ].filter(Boolean).join(" · ") || "Contexto da conta não informado";
  elements.modalManager.textContent = opportunity.manager || "Não informado";
  elements.modalRegion.textContent = opportunity.region || "Não informada";
  elements.modalEngagement.textContent = opportunity.engage_date
    ? `${formatDate(opportunity.engage_date)} · ${getAgeLabel(opportunity)}`
    : "Não registrado";
  elements.modalPriority.className = `modal-priority stage-${slugify(opportunity.stage)}${priorityScore === null ? " is-missing" : ""}`;
  elements.modalPriorityScore.textContent = priorityScore === null ? "Indisponível" : priorityScore.toFixed(1).replace(".", ",");
  elements.modalPriorityScale.hidden = priorityScore === null;
  elements.modalPriority.setAttribute("aria-label", priorityScore === null
    ? "POWER Priority indisponível"
    : `POWER Priority ${priorityScore.toFixed(1).replace(".", ",")} de 100`);
  elements.modalStageTrack.className = `modal-stage-track stage-track-${slugify(opportunity.stage)}`;
  elements.modalStageTrack.innerHTML = renderStageTrack(opportunity.stage);
  updateRecordNavigation(opportunity);

  elements.drawerContent.className = "modal-content modal-content-unified";
  elements.drawerContent.innerHTML = `
    <div class="record-unified-view">
      <section class="unified-section unified-power-section power-modal-panel" aria-label="Leitura POWER da oportunidade" data-unified-power>
        <section class="power-scorecard">
          <div class="power-mobile-tabs" role="tablist" aria-label="Pilares do POWER">
            <button type="button" role="tab" aria-label="P · Propensity" data-power-pillar-tab="p">P</button>
            <button type="button" role="tab" aria-label="O · Opportunity Value" data-power-pillar-tab="o">O</button>
            <button type="button" role="tab" aria-label="W · Warmth" data-power-pillar-tab="w">W</button>
            <button type="button" role="tab" aria-label="E · Execution Fit" data-power-pillar-tab="e">E</button>
            <button type="button" role="tab" aria-label="R · Recommendation" data-power-pillar-tab="r">R</button>
          </div>
          <div class="power-lenses" aria-label="POWER profile da oportunidade">
            ${renderPropensityLens(opportunity.scores.P)}
            ${renderOpportunityValueLens(opportunity.value_tier)}
            ${renderWarmthLens(opportunity.temperature || opportunity.attention, opportunity.warmth_evidence?.age_days)}
            ${renderExecutionFitLens(opportunity)}
            <article class="power-lens power-lens-r" data-recommendation-lens="${escapeHtml(opportunity.id)}" aria-label="Leitura qualitativa de Recommendation" aria-live="polite">${renderRecommendationLensContent(opportunity)}</article>
          </div>
        </section>
      </section>

      <section class="unified-section unified-evidence-section" aria-label="Evidências e histórico">
        <div class="unified-evidence-grid">
          <section class="unified-evidence-card unified-propensity-evidence">
            <header><div><span class="evidence-pillar evidence-pillar-p">P</span><span><small>Base de Propensity</small><h4>Histórico observado</h4></span></div><strong>${propensityScore === null ? "Indisponível" : `${Math.round(propensityScore)} / 100`}</strong></header>
            ${historyContent}
          </section>

          <section class="unified-evidence-card unified-source-timeline">
            <header><div><span class="evidence-icon" aria-hidden="true"><svg class="icon"><use href="#icon-clock"></use></svg></span><span><small>Linha do tempo</small><h4>Fonte observada</h4></span></div><strong>${escapeHtml(opportunity.score_version || "Versão não informada")}</strong></header>
            <ol class="record-timeline">
              <li class="is-present"><i></i><div><small>Snapshot</small><strong>${escapeHtml(formatDate(opportunity.snapshot_date))}</strong><p>Data de referência do modelo.</p></div></li>
              <li class="${opportunity.engage_date ? "is-present" : "is-missing"}"><i></i><div><small>Engajamento</small><strong>${escapeHtml(opportunity.engage_date ? formatDate(opportunity.engage_date) : "Não registrado")}</strong><p>${opportunity.engage_date ? `${escapeHtml(getAgeLabel(opportunity))} no snapshot.` : "A fonte não expõe data de contato."}</p></div></li>
              <li class="${isClosed ? "is-present" : "is-open"}"><i></i><div><small>${isClosed ? "Resultado" : "Ciclo de vida"}</small><strong>${escapeHtml(isClosed ? opportunity.stage : `${opportunity.stage} no snapshot`)}</strong><p>${isClosed ? `${escapeHtml(opportunity.close_date ? formatDate(opportunity.close_date) : "Data não informada")} · ${escapeHtml(opportunity.close_value !== null && opportunity.close_value !== undefined ? currency.format(opportunity.close_value) : "Valor não informado")}` : "Nenhum fechamento foi inferido."}</p></div></li>
            </ol>
          </section>

          <section class="unified-evidence-card unified-quality-summary">
            <header><div><span class="evidence-icon" aria-hidden="true"><svg class="icon"><use href="${opportunity.issues.length ? "#icon-alert" : "#icon-check"}"></use></svg></span><span><small>Qualidade dos dados</small><h4>Integridade do registro</h4></span></div><strong>${opportunity.issues.length ? `${opportunity.issues.length} ${opportunity.issues.length > 1 ? "lacunas" : "lacuna"}` : "Sem lacunas"}</strong></header>
            ${issues}
          </section>
        </div>
      </section>
    </div>
  `;

  bindPowerPillarTabs();
  animatePowerVisuals(elements.drawerContent.querySelector("[data-unified-power]"));
  void ensureRecommendation(opportunity);
  elements.backdrop.hidden = false;
  elements.drawer.setAttribute("aria-hidden", "false");
  document.body.classList.add("modal-open");
  requestAnimationFrame(() => {
    elements.backdrop.classList.add("is-visible");
    elements.drawer.classList.add("is-open");
    requestAnimationFrame(() => elements.closeDrawer.focus());
  });
}

function closeDrawer() {
  disposePowerVisuals();
  elements.drawer.classList.remove("is-open");
  elements.backdrop.classList.remove("is-visible");
  elements.drawer.setAttribute("aria-hidden", "true");
  document.body.classList.remove("modal-open");
  window.setTimeout(() => {
    elements.backdrop.hidden = true;
    state.lastFocusedElement?.focus();
  }, 180);
}

async function getOpportunityDetail(opportunity) {
  if (state.opportunityDetails.has(opportunity.id)) return state.opportunityDetails.get(opportunity.id);
  try {
    const detail = await window.POWER_BACKEND.loadOpportunity(opportunity.id);
    state.opportunityDetails.set(opportunity.id, detail);
    return detail;
  } catch (error) {
    console.warn("Could not load POWER evidence", error);
    return { ...opportunity, _detailLoadError: true };
  }
}

async function openOpportunityFromEvent(event) {
  const trigger = event.target.closest("[data-opportunity-id]");
  if (!trigger || !state.data) return;
  const opportunity = state.data.opportunities.find(
    (item) => item.id === trigger.dataset.opportunityId,
  );
  if (!opportunity) return;
  trigger.classList.add("is-opening");
  trigger.setAttribute("aria-busy", "true");
  trigger.disabled = true;
  try {
    openDrawer(await getOpportunityDetail(opportunity), trigger);
  } finally {
    trigger.classList.remove("is-opening");
    trigger.removeAttribute("aria-busy");
    trigger.disabled = false;
  }
}

async function navigateRecord(direction) {
  if (!state.activeOpportunity) return;
  const currentIndex = state.filtered.findIndex(
    (item) => item.id === state.activeOpportunity.id,
  );
  const nextOpportunity = state.filtered[currentIndex + direction];
  if (!nextOpportunity) return;
  openDrawer(await getOpportunityDetail(nextOpportunity), null);
}

function handleDrawerKeyboard(event) {
  if (!elements.drawer.classList.contains("is-open")) {
    if (event.key === "Escape") setMobileNavigation(false);
    return;
  }
  if (event.key === "Escape") {
    closeDrawer();
    return;
  }
  if (event.key !== "Tab") return;

  const focusable = [
    ...elements.drawer.querySelectorAll(
      'button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])',
    ),
  ];
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable.at(-1);
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}

function setMobileNavigation(open) {
  document.body.classList.toggle("mobile-sidebar-open", open);
  elements.mobileNav.setAttribute("aria-expanded", String(open));
  elements.mobileNavBackdrop.hidden = !open;
  if (open) {
    window.requestAnimationFrame(() => elements.closeMobileNav.focus());
  } else if (document.activeElement && elements.mobileNavBackdrop !== document.activeElement && document.querySelector("#app-sidebar")?.contains(document.activeElement)) {
    elements.mobileNav.focus();
  }
}

function syncViewUrl() {
  const url = new URL(window.location.href);
  if (state.view === "board") url.searchParams.delete("view");
  else url.searchParams.set("view", state.view);
  window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
}

function bindEvents() {
  if (state.eventsBound) return;
  state.eventsBound = true;

  elements.filters.addEventListener("input", () => {
    state.page = 1;
    resetBoardLimits();
    render();
  });

  elements.sortOrder.addEventListener("change", () => {
    state.page = 1;
    resetBoardLimits();
    render();
  });

  elements.filterToggle.addEventListener("click", () => {
    const expanded = elements.filterToggle.getAttribute("aria-expanded") === "true";
    elements.filterToggle.setAttribute("aria-expanded", String(!expanded));
    elements.filterPanel.hidden = expanded;
  });

  elements.resetFiltersPanel.addEventListener("click", resetFilters);

  elements.densityToggle.addEventListener("click", () => {
    const compact = elements.boardView.classList.toggle("is-compact");
    elements.densityToggle.setAttribute("aria-pressed", String(compact));
    elements.densityToggle.textContent = compact ? "Comfortable" : "Compact";
  });

  elements.mobileNav.addEventListener("click", () => {
    setMobileNavigation(!document.body.classList.contains("mobile-sidebar-open"));
  });
  elements.closeMobileNav.addEventListener("click", () => setMobileNavigation(false));
  elements.mobileNavBackdrop.addEventListener("click", () => setMobileNavigation(false));
  document.querySelectorAll(".primary-nav a").forEach((link) => {
    link.addEventListener("click", () => setMobileNavigation(false));
  });

  elements.viewButtons.forEach((button) => {
    button.addEventListener("click", () => {
      state.view = button.dataset.view;
      state.page = 1;
      syncViewUrl();
      render();
    });
  });

  elements.activeFilters.addEventListener("click", (event) => {
    const button = event.target.closest("[data-clear-filter]");
    if (button) clearFilter(button.dataset.clearFilter);
  });

  elements.resetFilters.addEventListener("click", resetFilters);
  elements.retryLoad.addEventListener("click", init);

  elements.previousPage.addEventListener("click", () => {
    state.page -= 1;
    renderRows();
    elements.listView.scrollIntoView({ behavior: reduceMotion.matches ? "auto" : "smooth", block: "start" });
  });

  elements.nextPage.addEventListener("click", () => {
    state.page += 1;
    renderRows();
    elements.listView.scrollIntoView({ behavior: reduceMotion.matches ? "auto" : "smooth", block: "start" });
  });

  elements.board.addEventListener("click", (event) => {
    const loadButton = event.target.closest("[data-load-stage]");
    if (loadButton) {
      loadNextColumnBatch(loadButton.dataset.loadStage, loadButton);
      return;
    }
    openOpportunityFromEvent(event);
  });

  elements.rows.addEventListener("click", openOpportunityFromEvent);
  elements.drawerContent.addEventListener("click", (event) => {
    const retry = event.target.closest("[data-retry-recommendation]");
    if (retry && state.activeOpportunity) ensureRecommendation(state.activeOpportunity, true);
  });
  elements.closeDrawer.addEventListener("click", closeDrawer);
  elements.previousRecord.addEventListener("click", () => navigateRecord(-1));
  elements.nextRecord.addEventListener("click", () => navigateRecord(1));
  elements.backdrop.addEventListener("click", closeDrawer);
  document.addEventListener("keydown", handleDrawerKeyboard);

  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      elements.search.focus();
    }
  });
}

function prepareOpportunitySearch(opportunities) {
  opportunities.forEach((opportunity) => {
    opportunity._search = [
      opportunity.id,
      opportunity.account,
      opportunity.seller,
      opportunity.product,
      opportunity.region,
    ]
      .filter(Boolean)
      .join(" ")
      .toLocaleLowerCase("pt-BR");
  });
}

function applyPipelineData(data) {
  const canFinalizeInPlace = Boolean(
    state.data?.meta.load_state === "loading" &&
    data.meta.load_state !== "loading" &&
    state.view === "board" &&
    !hasActiveFilters() &&
    elements.sortOrder.value === "power-priority" &&
    elements.board.querySelector(".pipeline-column"),
  );

  state.data = data;
  elements.pipelineWorkspace.setAttribute("aria-busy", String(data.meta.load_state === "loading"));
  prepareOpportunitySearch(data.opportunities);
  populateSelect(elements.sellerFilter, data.filters.sellers);
  populateSelect(elements.regionFilter, data.filters.regions);
  populateSelect(elements.productFilter, data.filters.products);
  renderStaticSummary();

  if (canFinalizeInPlace) {
    state.filtered = getFilteredOpportunities();
    renderResultDescription();
    renderFilterChips();
    updateControls();
    finalizeBoardInPlace();
    renderEmptyState();
    return;
  }

  render({ preserveBoardScroll: true });
}

async function init() {
  bindEvents();
  state.data = null;
  elements.systemState.classList.remove("is-ready", "is-error");
  elements.systemState.classList.add("is-loading");
  elements.scoreVersion.textContent = "Connecting";
  elements.totalRecordCount.textContent = "";
  elements.loadingState.hidden = false;
  elements.pipelineWorkspace.setAttribute("aria-busy", "true");
  elements.errorState.hidden = true;
  elements.boardView.hidden = true;
  elements.listView.hidden = true;
  elements.emptyState.hidden = true;
  if (elements.loadingProgress) {
    elements.loadingProgress.textContent = "Connecting to the Supabase read model…";
  }

  try {
    if (!window.POWER_BACKEND) throw new Error("POWER backend adapter is unavailable");
    const data = await window.POWER_BACKEND.loadPipeline({
      onProgress: applyPipelineData,
    });
    applyPipelineData(data);
    if (data.meta.load_state === "partial") {
      console.warn("Pipeline loaded with missing ranges", data.meta.failed_ranges);
    }
  } catch (error) {
    console.error(error);
    elements.systemState.classList.remove("is-loading", "is-ready");
    elements.systemState.classList.add("is-error");
    elements.scoreVersion.textContent = "Read model unavailable";
    elements.totalRecordCount.textContent = "N/D";
    [elements.activeCount, elements.pipelineValue, elements.staleCount, elements.missingAccountCount].forEach((element) => {
      element.textContent = "N/D";
      element.classList.remove("metric-placeholder");
    });
    elements.loadingState.hidden = true;
    elements.pipelineWorkspace.setAttribute("aria-busy", "false");
    elements.errorState.hidden = false;
    elements.boardView.hidden = true;
    elements.listView.hidden = true;
    elements.emptyState.hidden = true;
    elements.resultDescription.textContent = "Dados indisponíveis";
  }
}

init();

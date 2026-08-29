const DIRECTORY_TYPES = ["products", "sellers", "companies", "sectors", "regions"];
const STAGES = ["Prospecting", "Engaging", "Won", "Lost"];
const DIRECTORY_PAGE_SIZE = 40;

const currency = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});
const integer = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });
const decimal = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 });

const TYPE_CONFIG = {
  products: { label: "Products", singular: "Product", description: "Produtos e séries observados nas oportunidades do dataset.", placeholder: "Search products" },
  sellers: { label: "Sellers", singular: "Seller", description: "Vendedores e sua cobertura comercial observada no histórico.", placeholder: "Search sellers" },
  companies: { label: "Companies", singular: "Company", description: "Empresas identificadas nas oportunidades, sem completar campos ausentes.", placeholder: "Search companies" },
  sectors: { label: "Sectors", singular: "Sector", description: "Segmentos utilizados para relacionar empresas e oportunidades.", placeholder: "Search sectors" },
  regions: { label: "Regions", singular: "Region", description: "Escritórios regionais presentes na base comercial.", placeholder: "Search regions" },
};

const state = {
  data: null,
  catalogs: Object.fromEntries(DIRECTORY_TYPES.map((type) => [type, []])),
  activeType: DIRECTORY_TYPES.includes(location.hash.slice(1)) ? location.hash.slice(1) : "products",
  query: "",
  sort: "opportunities-desc",
  page: 1,
  filtered: [],
  activeEntity: null,
  lastFocusedElement: null,
  eventsBound: false,
};

const elements = {
  sidebarEntityCount: document.querySelector("#sidebar-entity-count"),
  systemState: document.querySelector("#system-state"),
  dataStateLabel: document.querySelector("#data-state-label"),
  totalRecordCount: document.querySelector("#total-record-count"),
  activeEntityCount: document.querySelector("#active-entity-count"),
  description: document.querySelector("#directory-description"),
  snapshotLabel: document.querySelector("#snapshot-label"),
  tabs: [...document.querySelectorAll("[data-directory-view]")],
  counts: Object.fromEntries(DIRECTORY_TYPES.map((type) => [type, document.querySelector(`#${type}-count`)])),
  controls: document.querySelector("#directory-controls"),
  search: document.querySelector("#directory-search"),
  sort: document.querySelector("#directory-sort"),
  resultDescription: document.querySelector("#directory-result-description"),
  loading: document.querySelector("#directory-loading"),
  workspace: document.querySelector("#directory-workspace"),
  loadingProgress: document.querySelector("#directory-loading-progress"),
  error: document.querySelector("#directory-error"),
  retry: document.querySelector("#directory-retry"),
  empty: document.querySelector("#directory-empty"),
  clearSearch: document.querySelector("#directory-clear-search"),
  tableShell: document.querySelector("#directory-table-shell"),
  tableHead: document.querySelector("#directory-table-head"),
  tableBody: document.querySelector("#directory-table-body"),
  pagination: document.querySelector("#directory-pagination"),
  paginationSummary: document.querySelector("#directory-pagination-summary"),
  pageIndicator: document.querySelector("#directory-page-indicator"),
  previous: document.querySelector("#directory-previous"),
  next: document.querySelector("#directory-next"),
  mobileNav: document.querySelector("#mobile-nav"),
  closeMobileNav: document.querySelector("#close-mobile-nav"),
  mobileNavBackdrop: document.querySelector("#mobile-nav-backdrop"),
  modalBackdrop: document.querySelector("#entity-modal-backdrop"),
  modal: document.querySelector("#entity-modal"),
  modalClose: document.querySelector("#entity-modal-close"),
  modalSymbol: document.querySelector("#entity-modal-symbol"),
  modalType: document.querySelector("#entity-modal-type"),
  modalTitle: document.querySelector("#entity-modal-title"),
  modalSubtitle: document.querySelector("#entity-modal-subtitle"),
  modalFacts: document.querySelector("#entity-modal-facts"),
  modalContent: document.querySelector("#entity-modal-content"),
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function normalize(value) {
  return String(value || "").trim();
}

function getInitials(value) {
  const parts = normalize(value).split(/\s+/).filter(Boolean);
  if (!parts.length) return "?";
  return `${parts[0][0]}${parts.length > 1 ? parts.at(-1)[0] : ""}`.toUpperCase();
}

function getSymbolClass(value) {
  const classes = ["violet", "blue", "green", "coral", "amber"];
  const hash = [...normalize(value)].reduce((sum, character) => sum + character.charCodeAt(0), 0);
  return `entity-${classes[hash % classes.length]}`;
}

function formatDate(value) {
  if (!value) return "Date unavailable";
  return new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(`${value}T12:00:00`));
}

function createEntity(type, key, name) {
  return {
    id: `${type}:${key}`,
    type,
    key,
    name,
    stageCounts: Object.fromEntries(STAGES.map((stage) => [stage, 0])),
    opportunityCount: 0,
    listValue: 0,
    realizedValue: 0,
    revenue: null,
    employees: null,
    relations: {
      series: new Set(),
      sellers: new Set(),
      companies: new Set(),
      products: new Set(),
      managers: new Set(),
      regions: new Set(),
      sectors: new Set(),
      locations: new Set(),
    },
  };
}

function getOrCreate(map, type, key, name) {
  const normalizedKey = normalize(key || name);
  if (!map.has(normalizedKey)) map.set(normalizedKey, createEntity(type, normalizedKey, normalize(name || key)));
  return map.get(normalizedKey);
}

function addRelation(entity, relation, value) {
  const normalized = normalize(value);
  if (normalized) entity.relations[relation].add(normalized);
}

function addOpportunity(entity, opportunity) {
  entity.opportunityCount += 1;
  entity.stageCounts[opportunity.stage] = (entity.stageCounts[opportunity.stage] || 0) + 1;
  entity.listValue += Number(opportunity.potential_value) || 0;
  entity.realizedValue += Number(opportunity.close_value) || 0;
}

function finalizeEntity(entity) {
  entity.activeCount = entity.stageCounts.Prospecting + entity.stageCounts.Engaging;
  entity.closedCount = entity.stageCounts.Won + entity.stageCounts.Lost;
  entity._search = [
    entity.name,
    entity.key,
    ...Object.values(entity.relations).flatMap((values) => [...values]),
  ].join(" ").toLocaleLowerCase("pt-BR");
  return entity;
}

function buildCatalogs(opportunities) {
  const maps = Object.fromEntries(DIRECTORY_TYPES.map((type) => [type, new Map()]));

  opportunities.forEach((opportunity) => {
    const productName = normalize(opportunity.product);
    if (productName) {
      const entity = getOrCreate(maps.products, "products", opportunity.product_key || productName, productName);
      addOpportunity(entity, opportunity);
      addRelation(entity, "series", opportunity.series);
      addRelation(entity, "sellers", opportunity.seller);
      addRelation(entity, "companies", opportunity.account);
      addRelation(entity, "sectors", opportunity.sector);
      addRelation(entity, "regions", opportunity.region);
    }

    const sellerName = normalize(opportunity.seller);
    if (sellerName) {
      const entity = getOrCreate(maps.sellers, "sellers", sellerName, sellerName);
      addOpportunity(entity, opportunity);
      addRelation(entity, "managers", opportunity.manager);
      addRelation(entity, "regions", opportunity.region);
      addRelation(entity, "products", opportunity.product);
      addRelation(entity, "companies", opportunity.account);
      addRelation(entity, "sectors", opportunity.sector);
    }

    const companyName = normalize(opportunity.account);
    if (companyName) {
      const entity = getOrCreate(maps.companies, "companies", companyName, companyName);
      addOpportunity(entity, opportunity);
      addRelation(entity, "sectors", opportunity.sector);
      addRelation(entity, "locations", opportunity.office_location);
      addRelation(entity, "regions", opportunity.region);
      addRelation(entity, "sellers", opportunity.seller);
      addRelation(entity, "products", opportunity.product);
      if (entity.revenue === null && opportunity.account_revenue !== null && opportunity.account_revenue !== undefined) entity.revenue = Number(opportunity.account_revenue);
      if (entity.employees === null && opportunity.account_employees !== null && opportunity.account_employees !== undefined) entity.employees = Number(opportunity.account_employees);
    }

    const sectorName = normalize(opportunity.sector);
    if (sectorName) {
      const entity = getOrCreate(maps.sectors, "sectors", sectorName, sectorName);
      addOpportunity(entity, opportunity);
      addRelation(entity, "companies", opportunity.account);
      addRelation(entity, "products", opportunity.product);
      addRelation(entity, "sellers", opportunity.seller);
      addRelation(entity, "regions", opportunity.region);
    }

    const regionName = normalize(opportunity.region);
    if (regionName) {
      const entity = getOrCreate(maps.regions, "regions", regionName, regionName);
      addOpportunity(entity, opportunity);
      addRelation(entity, "sellers", opportunity.seller);
      addRelation(entity, "managers", opportunity.manager);
      addRelation(entity, "companies", opportunity.account);
      addRelation(entity, "products", opportunity.product);
      addRelation(entity, "sectors", opportunity.sector);
    }
  });

  return Object.fromEntries(
    DIRECTORY_TYPES.map((type) => [type, [...maps[type].values()].map(finalizeEntity)]),
  );
}

function setToArray(entity, relation) {
  return [...entity.relations[relation]].sort((a, b) => a.localeCompare(b, "pt-BR"));
}

function summarizeList(values, limit = 2) {
  if (!values.length) return "Not available";
  const shown = values.slice(0, limit).join(" · ");
  return values.length > limit ? `${shown} +${values.length - limit}` : shown;
}

function renderEntityIdentity(entity, detail) {
  return `
    <button class="entity-identity" type="button" data-entity-id="${escapeHtml(entity.id)}" aria-label="Open ${escapeHtml(entity.name)}">
      <span class="entity-symbol ${getSymbolClass(entity.name)}">${escapeHtml(getInitials(entity.name))}</span>
      <span><strong>${escapeHtml(entity.name)}</strong><small>${escapeHtml(detail || entity.key)}</small></span>
      <svg class="icon" aria-hidden="true"><use href="#icon-chevron"></use></svg>
    </button>`;
}

function renderStageCell(entity) {
  const total = Math.max(1, entity.opportunityCount);
  const segments = STAGES.map((stage) => `<i class="${stage.toLocaleLowerCase("en-US")}" style="--segment:${(entity.stageCounts[stage] / total) * 100}%"></i>`).join("");
  return `<div class="opportunity-volume"><strong>${integer.format(entity.opportunityCount)}</strong><span class="stage-stack" aria-label="Prospecting ${entity.stageCounts.Prospecting}, Engaging ${entity.stageCounts.Engaging}, Won ${entity.stageCounts.Won}, Lost ${entity.stageCounts.Lost}">${segments}</span></div>`;
}

function renderClosedCell(entity) {
  return `<span class="closed-split"><b>${integer.format(entity.stageCounts.Won)}</b><i>/</i><em>${integer.format(entity.stageCounts.Lost)}</em></span>`;
}

function getTableDefinition(type) {
  const definitions = {
    products: {
      headers: ["Product", "Coverage", "Opportunities", "Active", "Won / Lost", "List value"],
      row: (entity) => `<tr>${cell(renderEntityIdentity(entity, entity.key))}${cell(`<strong>${integer.format(entity.relations.series.size)}</strong><small>series · ${integer.format(entity.relations.sellers.size)} sellers</small>`, "relation-cell")}${cell(renderStageCell(entity))}${numberCell(entity.activeCount)}${cell(renderClosedCell(entity))}${valueCell(entity.listValue)}</tr>`,
    },
    sellers: {
      headers: ["Seller", "Team context", "Coverage", "Opportunities", "Active", "Won / Lost"],
      row: (entity) => `<tr>${cell(renderEntityIdentity(entity, summarizeList(setToArray(entity, "regions"), 1)))}${cell(`<strong>${escapeHtml(summarizeList(setToArray(entity, "managers"), 1))}</strong><small>${integer.format(entity.relations.regions.size)} region${entity.relations.regions.size === 1 ? "" : "s"}</small>`, "relation-cell")}${cell(`<strong>${integer.format(entity.relations.products.size)}</strong><small>products · ${integer.format(entity.relations.companies.size)} companies</small>`, "relation-cell")}${cell(renderStageCell(entity))}${numberCell(entity.activeCount)}${cell(renderClosedCell(entity))}</tr>`,
    },
    companies: {
      headers: ["Company", "Profile", "Coverage", "Opportunities", "Active", "List value"],
      row: (entity) => `<tr>${cell(renderEntityIdentity(entity, summarizeList(setToArray(entity, "sectors"), 1)))}${cell(`<strong>${entity.revenue === null ? "Not available" : `${escapeHtml(decimal.format(entity.revenue))} M USD`}</strong><small>${entity.employees === null ? "Employees unavailable" : `${integer.format(entity.employees)} employees`}</small>`, "relation-cell")}${cell(`<strong>${integer.format(entity.relations.products.size)}</strong><small>products · ${integer.format(entity.relations.sellers.size)} sellers</small>`, "relation-cell")}${cell(renderStageCell(entity))}${numberCell(entity.activeCount)}${valueCell(entity.listValue)}</tr>`,
    },
    sectors: {
      headers: ["Sector", "Coverage", "Opportunities", "Active", "Won / Lost", "List value"],
      row: (entity) => `<tr>${cell(renderEntityIdentity(entity, `${integer.format(entity.relations.companies.size)} companies`))}${cell(`<strong>${integer.format(entity.relations.products.size)}</strong><small>products · ${integer.format(entity.relations.sellers.size)} sellers</small>`, "relation-cell")}${cell(renderStageCell(entity))}${numberCell(entity.activeCount)}${cell(renderClosedCell(entity))}${valueCell(entity.listValue)}</tr>`,
    },
    regions: {
      headers: ["Region", "Coverage", "Opportunities", "Active", "Won / Lost", "List value"],
      row: (entity) => `<tr>${cell(renderEntityIdentity(entity, `${integer.format(entity.relations.sellers.size)} sellers`))}${cell(`<strong>${integer.format(entity.relations.managers.size)}</strong><small>managers · ${integer.format(entity.relations.companies.size)} companies</small>`, "relation-cell")}${cell(renderStageCell(entity))}${numberCell(entity.activeCount)}${cell(renderClosedCell(entity))}${valueCell(entity.listValue)}</tr>`,
    },
  };
  return definitions[type];
}

function cell(content, className = "") {
  return `<td class="${className}">${content}</td>`;
}

function numberCell(value) {
  return `<td class="numeric-cell"><strong>${integer.format(value)}</strong></td>`;
}

function valueCell(value) {
  return `<td class="value-cell"><strong>${escapeHtml(currency.format(value))}</strong></td>`;
}

function getFilteredEntities() {
  const query = state.query.trim().toLocaleLowerCase("pt-BR");
  const entities = state.catalogs[state.activeType].filter((entity) => !query || entity._search.includes(query));
  return entities.sort((left, right) => {
    if (state.sort === "active-desc") return right.activeCount - left.activeCount || left.name.localeCompare(right.name, "pt-BR");
    if (state.sort === "value-desc") return right.listValue - left.listValue || left.name.localeCompare(right.name, "pt-BR");
    if (state.sort === "name-asc") return left.name.localeCompare(right.name, "pt-BR");
    return right.opportunityCount - left.opportunityCount || left.name.localeCompare(right.name, "pt-BR");
  });
}

function updateNavigation() {
  elements.tabs.forEach((tab) => {
    const active = tab.dataset.directoryView === state.activeType;
    tab.classList.toggle("is-active", active);
    tab.setAttribute("aria-pressed", String(active));
  });
  DIRECTORY_TYPES.forEach((type) => {
    elements.counts[type].textContent = state.data ? integer.format(state.catalogs[type].length) : "";
    elements.counts[type].classList.toggle("metric-placeholder", !state.data);
  });
  elements.sidebarEntityCount.textContent = state.data
    ? integer.format(DIRECTORY_TYPES.reduce((sum, type) => sum + state.catalogs[type].length, 0))
    : "";
}

function renderDirectory() {
  updateNavigation();
  const config = TYPE_CONFIG[state.activeType];
  const definition = getTableDefinition(state.activeType);
  state.filtered = getFilteredEntities();
  const pageCount = Math.max(1, Math.ceil(state.filtered.length / DIRECTORY_PAGE_SIZE));
  state.page = Math.min(state.page, pageCount);
  const start = (state.page - 1) * DIRECTORY_PAGE_SIZE;
  const pageEntities = state.filtered.slice(start, start + DIRECTORY_PAGE_SIZE);
  const visibleStart = state.filtered.length ? start + 1 : 0;
  const visibleEnd = Math.min(start + DIRECTORY_PAGE_SIZE, state.filtered.length);
  const linkedOpportunities = state.filtered.reduce((sum, entity) => sum + entity.opportunityCount, 0);
  const activeLinks = state.filtered.reduce((sum, entity) => sum + entity.activeCount, 0);

  elements.activeEntityCount.textContent = state.data ? integer.format(state.catalogs[state.activeType].length) : "";
  elements.activeEntityCount.classList.toggle("metric-placeholder", !state.data);
  elements.description.textContent = config.description;
  elements.search.placeholder = config.placeholder;
  elements.resultDescription.innerHTML = `<strong>${integer.format(state.filtered.length)}</strong> ${escapeHtml(config.label.toLocaleLowerCase("en-US"))} · ${integer.format(linkedOpportunities)} linked opportunities · ${integer.format(activeLinks)} active`;
  elements.tableShell.dataset.view = state.activeType;
  elements.tableHead.innerHTML = `<tr>${definition.headers.map((header) => `<th scope="col">${escapeHtml(header)}</th>`).join("")}</tr>`;
  elements.tableBody.innerHTML = pageEntities.map(definition.row).join("");

  const hasResults = state.filtered.length > 0;
  elements.empty.hidden = hasResults || !state.data;
  elements.tableShell.hidden = !hasResults;
  elements.pagination.hidden = !hasResults;
  elements.paginationSummary.textContent = `${integer.format(visibleStart)}–${integer.format(visibleEnd)} of ${integer.format(state.filtered.length)}`;
  elements.pageIndicator.textContent = `${state.page} / ${pageCount}`;
  elements.previous.disabled = state.page <= 1;
  elements.next.disabled = state.page >= pageCount;
}

function renderSystemState() {
  if (!state.data) return;
  const { meta } = state.data;
  const total = meta.total_available || meta.total_opportunities;
  const isLoading = meta.load_state === "loading";
  elements.systemState.classList.toggle("is-loading", isLoading);
  elements.systemState.classList.toggle("is-ready", !isLoading && meta.load_state !== "partial");
  elements.systemState.classList.toggle("is-error", meta.load_state === "partial");
  elements.dataStateLabel.textContent = isLoading ? "Indexing directory" : meta.load_state === "partial" ? "Partial read model" : "Directory ready";
  elements.totalRecordCount.textContent = integer.format(meta.total_opportunities);
  elements.snapshotLabel.textContent = `${formatDate(meta.snapshot_date)} · ${integer.format(total)} opportunities`;
  elements.loadingProgress.textContent = isLoading
    ? `Indexing ${integer.format(meta.total_opportunities)} of ${integer.format(total)} opportunities…`
    : "Relationship index ready";
}

function primeDirectoryLoading(data) {
  const total = data.meta.total_available || data.meta.total_opportunities;
  elements.totalRecordCount.textContent = integer.format(total);
  elements.snapshotLabel.textContent = `${formatDate(data.meta.snapshot_date)} · ${integer.format(total)} opportunities`;
  elements.loadingProgress.textContent = "Indexing relationships in the background…";
}

function updateDirectoryLoadingStatus(status) {
  elements.loadingProgress.setAttribute(
    "aria-label",
    `${integer.format(status.loaded)} of ${integer.format(status.total)} opportunities indexed`,
  );
}

function applyData(data) {
  const isInitialReveal = !elements.loading.hidden;
  state.data = data;
  elements.workspace.setAttribute("aria-busy", String(data.meta.load_state === "loading"));
  state.catalogs = buildCatalogs(data.opportunities);
  elements.error.hidden = true;
  renderSystemState();
  renderDirectory();

  if (state.activeEntity) {
    const updated = state.catalogs[state.activeType].find((entity) => entity.id === state.activeEntity.id);
    if (updated) {
      state.activeEntity = updated;
      renderModal(updated);
    }
  }

  if (isInitialReveal) {
    window.requestAnimationFrame(() => {
      elements.loading.hidden = true;
    });
  } else {
    elements.loading.hidden = true;
  }
}

function renderLifecycle(entity) {
  return STAGES.map((stage) => `<div class="lifecycle-stat ${stage.toLocaleLowerCase("en-US")}"><span><i></i>${escapeHtml(stage)}</span><strong>${integer.format(entity.stageCounts[stage])}</strong><small>${entity.opportunityCount ? decimal.format((entity.stageCounts[stage] / entity.opportunityCount) * 100) : "0"}%</small></div>`).join("");
}

function renderRelationGroup(label, values) {
  if (!values.length) return "";
  const visible = values.slice(0, 8);
  return `<div class="relation-group"><span>${escapeHtml(label)}</span><div>${visible.map((value) => `<i>${escapeHtml(value)}</i>`).join("")}${values.length > visible.length ? `<i>+${values.length - visible.length}</i>` : ""}</div></div>`;
}

function getKnownFields(entity) {
  if (entity.type === "products") return [["Product key", entity.key], ["Series", integer.format(entity.relations.series.size)], ["Sellers", integer.format(entity.relations.sellers.size)], ["Companies", integer.format(entity.relations.companies.size)]];
  if (entity.type === "sellers") return [["Managers", summarizeList(setToArray(entity, "managers"), 2)], ["Regions", summarizeList(setToArray(entity, "regions"), 2)], ["Products", integer.format(entity.relations.products.size)], ["Companies", integer.format(entity.relations.companies.size)]];
  if (entity.type === "companies") return [["Sector", summarizeList(setToArray(entity, "sectors"), 2)], ["Revenue", entity.revenue === null ? "Not available" : `${decimal.format(entity.revenue)} M USD`], ["Employees", entity.employees === null ? "Not available" : integer.format(entity.employees)], ["Location", summarizeList(setToArray(entity, "locations"), 2)]];
  if (entity.type === "sectors") return [["Companies", integer.format(entity.relations.companies.size)], ["Products", integer.format(entity.relations.products.size)], ["Sellers", integer.format(entity.relations.sellers.size)], ["Regions", integer.format(entity.relations.regions.size)]];
  return [["Sellers", integer.format(entity.relations.sellers.size)], ["Managers", integer.format(entity.relations.managers.size)], ["Companies", integer.format(entity.relations.companies.size)], ["Products", integer.format(entity.relations.products.size)]];
}

function renderModal(entity) {
  const config = TYPE_CONFIG[entity.type];
  elements.modalSymbol.textContent = getInitials(entity.name);
  elements.modalSymbol.className = `entity-symbol entity-symbol-large ${getSymbolClass(entity.name)}`;
  elements.modalType.textContent = config.singular;
  elements.modalTitle.textContent = entity.name;
  elements.modalSubtitle.textContent = entity.key === entity.name ? "Derived from opportunity relationships" : entity.key;
  elements.modalFacts.innerHTML = `
    <div><dt>Linked opportunities</dt><dd>${integer.format(entity.opportunityCount)}</dd></div>
    <div><dt>Active</dt><dd>${integer.format(entity.activeCount)}</dd></div>
    <div><dt>List value</dt><dd>${escapeHtml(currency.format(entity.listValue))}</dd></div>`;

  const relationGroups = [
    ["Products", setToArray(entity, "products")],
    ["Series", setToArray(entity, "series")],
    ["Companies", setToArray(entity, "companies")],
    ["Sellers", setToArray(entity, "sellers")],
    ["Sectors", setToArray(entity, "sectors")],
    ["Regions", setToArray(entity, "regions")],
  ].map(([label, values]) => renderRelationGroup(label, values)).filter(Boolean).join("");

  elements.modalContent.innerHTML = `
    <div class="entity-modal-grid">
      <section class="entity-detail-section lifecycle-section">
        <header><span>01</span><div><h3>Lifecycle distribution</h3><p>Factual stage counts in the current snapshot.</p></div></header>
        <div class="lifecycle-grid">${renderLifecycle(entity)}</div>
      </section>
      <section class="entity-detail-section known-fields-section">
        <header><span>02</span><div><h3>Known fields</h3><p>Only values present or directly derived from the dataset.</p></div></header>
        <dl class="entity-field-list">${getKnownFields(entity).map(([label, value]) => `<div><dt>${escapeHtml(label)}</dt><dd class="${value === "Not available" ? "is-unavailable" : ""}">${escapeHtml(value)}</dd></div>`).join("")}</dl>
      </section>
      <section class="entity-detail-section relationship-section">
        <header><span>03</span><div><h3>Relationship coverage</h3><p>Connected catalog entities observed across linked opportunities.</p></div></header>
        <div class="relation-groups">${relationGroups || '<p class="relationships-empty">No secondary relationships available.</p>'}</div>
      </section>
    </div>`;
}

function openModal(entity, trigger) {
  state.activeEntity = entity;
  state.lastFocusedElement = trigger;
  renderModal(entity);
  elements.modalBackdrop.hidden = false;
  elements.modalBackdrop.classList.add("is-visible");
  elements.modal.classList.add("is-open");
  elements.modal.setAttribute("aria-hidden", "false");
  document.body.classList.add("entity-modal-open");
  window.requestAnimationFrame(() => {
    window.requestAnimationFrame(() => elements.modalClose.focus());
  });
}

function closeModal() {
  if (!state.activeEntity) return;
  const returnFocus = state.lastFocusedElement;
  elements.modalBackdrop.classList.remove("is-visible");
  elements.modal.classList.remove("is-open");
  elements.modal.setAttribute("aria-hidden", "true");
  document.body.classList.remove("entity-modal-open");
  window.setTimeout(() => {
    elements.modalBackdrop.hidden = true;
    returnFocus?.focus();
  }, 160);
  state.activeEntity = null;
}

function setMobileNavigation(open) {
  document.body.classList.toggle("mobile-sidebar-open", open);
  elements.mobileNav.setAttribute("aria-expanded", String(open));
  elements.mobileNavBackdrop.hidden = !open;
  if (open) {
    window.requestAnimationFrame(() => elements.closeMobileNav.focus());
  } else if (document.activeElement && document.querySelector("#app-sidebar")?.contains(document.activeElement)) {
    elements.mobileNav.focus();
  }
}

function selectType(type) {
  if (!DIRECTORY_TYPES.includes(type)) return;
  state.activeType = type;
  state.page = 1;
  history.replaceState(null, "", `#${type}`);
  renderDirectory();
}

function bindEvents() {
  if (state.eventsBound) return;
  state.eventsBound = true;

  elements.tabs.forEach((tab) => tab.addEventListener("click", () => selectType(tab.dataset.directoryView)));
  elements.controls.addEventListener("input", () => {
    state.query = elements.search.value;
    state.sort = elements.sort.value;
    state.page = 1;
    if (state.data) renderDirectory();
  });
  elements.previous.addEventListener("click", () => { state.page -= 1; renderDirectory(); elements.tableShell.scrollTop = 0; });
  elements.next.addEventListener("click", () => { state.page += 1; renderDirectory(); elements.tableShell.scrollTop = 0; });
  elements.clearSearch.addEventListener("click", () => { elements.search.value = ""; state.query = ""; state.page = 1; renderDirectory(); elements.search.focus(); });
  elements.tableBody.addEventListener("click", (event) => {
    const trigger = event.target.closest("[data-entity-id]");
    if (!trigger) return;
    const entity = state.catalogs[state.activeType].find((item) => item.id === trigger.dataset.entityId);
    if (entity) openModal(entity, trigger);
  });

  elements.modalClose.addEventListener("click", closeModal);
  elements.modalBackdrop.addEventListener("click", closeModal);
  elements.mobileNav.addEventListener("click", () => setMobileNavigation(!document.body.classList.contains("mobile-sidebar-open")));
  elements.closeMobileNav.addEventListener("click", () => setMobileNavigation(false));
  elements.mobileNavBackdrop.addEventListener("click", () => setMobileNavigation(false));
  document.querySelectorAll(".primary-nav a").forEach((link) => link.addEventListener("click", () => setMobileNavigation(false)));
  elements.retry.addEventListener("click", init);

  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLocaleLowerCase("en-US") === "k") {
      event.preventDefault();
      elements.search.focus();
    }
    if (event.key === "Escape") {
      closeModal();
      setMobileNavigation(false);
    }
    if (event.key !== "Tab" || !state.activeEntity) return;
    const focusable = [...elements.modal.querySelectorAll('button:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])')];
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  });
}

async function init() {
  bindEvents();
  elements.loading.hidden = false;
  elements.workspace.setAttribute("aria-busy", "true");
  elements.error.hidden = true;
  elements.empty.hidden = true;
  elements.tableShell.hidden = true;
  elements.pagination.hidden = true;
  elements.systemState.classList.remove("is-ready", "is-error");
  elements.systemState.classList.add("is-loading");
  elements.dataStateLabel.textContent = "Connecting";
  elements.totalRecordCount.textContent = "";
  elements.snapshotLabel.textContent = "Loading source data";
  elements.resultDescription.textContent = "Connecting to the read model…";

  try {
    if (!window.POWER_BACKEND) throw new Error("POWER backend adapter is unavailable");
    const data = await window.POWER_BACKEND.loadPipeline({
      onProgress: primeDirectoryLoading,
      onStatus: updateDirectoryLoadingStatus,
    });
    applyData(data);
  } catch (error) {
    console.error(error);
    state.data = null;
    elements.loading.hidden = true;
    elements.workspace.setAttribute("aria-busy", "false");
    elements.error.hidden = false;
    elements.empty.hidden = true;
    elements.tableShell.hidden = true;
    elements.pagination.hidden = true;
    elements.systemState.classList.remove("is-loading", "is-ready");
    elements.systemState.classList.add("is-error");
    elements.dataStateLabel.textContent = "Read model unavailable";
    elements.resultDescription.textContent = "Directory data unavailable";
    elements.totalRecordCount.textContent = "N/D";
    elements.sidebarEntityCount.textContent = "N/D";
    elements.activeEntityCount.textContent = "N/D";
    Object.values(elements.counts).forEach((element) => { element.textContent = "N/D"; });
    elements.activeEntityCount.classList.remove("metric-placeholder");
    Object.values(elements.counts).forEach((element) => element.classList.remove("metric-placeholder"));
  }
}

init();

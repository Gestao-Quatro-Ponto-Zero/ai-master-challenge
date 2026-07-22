const dashboardState = {
  filters: {},
  riskRows: [],
  riskPage: 1,
  riskSort: "priority_score",
  riskDirection: "desc",
  riskQuickFilter: "all"
};

const filterLabels = {
  start_date: "Inicio",
  end_date: "Fim",
  plan_tier: "Plano",
  industry: "Industria",
  country: "Pais",
  referral_source: "Origem",
  is_trial: "Trial",
  status: "Status",
  billing_frequency: "Cobranca",
  auto_renew_flag: "Renovacao",
  reason_code: "Motivo"
};

document.addEventListener("DOMContentLoaded", async () => {
  bindDashboardEvents();
  await loadFilters();
  await refreshDashboard();
  window.Raven.refreshPage = refreshDashboard;
});

function bindDashboardEvents() {
  document.getElementById("filtersForm").addEventListener("submit", (event) => {
    event.preventDefault();
    dashboardState.filters = Object.fromEntries(new FormData(event.target).entries());
    refreshDashboard();
    document.body.classList.remove("filters-open");
    window.Raven.ui.toast("Filtros aplicados.");
  });
  document.getElementById("clearFilters").addEventListener("click", () => {
    document.getElementById("filtersForm").reset();
    dashboardState.filters = {};
    refreshDashboard();
    window.Raven.ui.toast("Filtros removidos.");
  });
  document.getElementById("riskSearch").addEventListener("input", window.Raven.ui.debounce(() => {
    dashboardState.riskPage = 1;
    renderRiskTable();
  }));
  document.getElementById("openFilters").addEventListener("click", () => {
    document.body.classList.add("filters-open");
    const backdrop = document.getElementById("sidebarBackdrop");
    if (backdrop) backdrop.hidden = false;
  });
  document.getElementById("collapseFilters").addEventListener("click", () => {
    document.getElementById("filtersPanel").classList.toggle("collapsed");
  });
  document.getElementById("riskQuickFilters").addEventListener("click", (event) => {
    const button = event.target.closest("[data-risk-filter]");
    if (!button) return;
    dashboardState.riskQuickFilter = button.dataset.riskFilter;
    document.querySelectorAll("#riskQuickFilters .chip").forEach((item) => item.classList.toggle("active", item === button));
    dashboardState.riskPage = 1;
    renderRiskTable();
  });
  document.getElementById("exportRisk").addEventListener("click", () => window.Raven.ui.toast("Exportacao CSV iniciada."));
}

async function loadFilters() {
  const data = await window.Raven.api.get("/api/filters");
  for (const [name, values] of Object.entries(data)) {
    const select = document.querySelector(`[name="${name}"]`);
    if (!select) continue;
    values.forEach((value) => select.append(new Option(value, value)));
  }
}

async function api(path) {
  return window.Raven.api.get(path, dashboardState.filters);
}

async function refreshDashboard() {
  showLoading(true);
  try {
    const results = await Promise.allSettled([
      api("/api/kpis"),
      api("/api/churn/timeline"),
      api("/api/churn/reasons"),
      api("/api/churn/segments"),
      api("/api/revenue"),
      api("/api/usage"),
      api("/api/support"),
      api("/api/reactivation"),
      api("/api/risk-accounts")
    ]);
    const [kpis, timeline, reasons, segments, revenue, usage, support, reactivation, risk] = results.map((result, index) => {
      if (result.status === "fulfilled") return result.value;
      console.error("Falha ao carregar bloco do dashboard", index, result.reason);
      return emptyDashboardData(index);
    });
    if (!kpis || !Number(kpis.total_accounts)) {
      throw new Error("Nao foi possivel carregar os KPIs principais.");
    }
    dashboardState.riskRows = risk.accounts || [];
    renderKpis(kpis, support.summary || {});
    renderActiveFilters();
    renderAttention(kpis, reasons, segments, revenue, dashboardState.riskRows);
    renderActionPlan(kpis, reasons, segments, revenue, support, dashboardState.riskRows);
    renderCharts(timeline, reasons, segments, revenue, usage, support, reactivation);
    renderRiskSummary();
    renderRiskTable();
    updateHeader(kpis);
    const qs = new URLSearchParams(Object.entries(dashboardState.filters).filter(([, value]) => value !== ""));
    document.getElementById("exportRisk").href = `/api/export/risk-accounts.csv?${qs}`;
    window.Raven.ui.toast("Dados atualizados.");
  } catch (error) {
    document.getElementById("kpiGrid").innerHTML = window.Raven.ui.errorState(error.message);
    window.Raven.ui.toast(error.message, "error");
  } finally {
    showLoading(false);
  }
}

function emptyDashboardData(index) {
  const empty = [
    null,
    { timeline: [] },
    { reasons: [] },
    { plan_tier: [], industry: [], country: [] },
    { mrr_by_plan: [], arr_by_industry: [], lost_mrr_by_plan: [], mrr_bands: [] },
    { features: [], active_vs_churn: [], timeline: [], beta: [] },
    { priority: [], summary: {}, active_vs_churn: [] },
    { total: { reactivation_events: 0 }, timeline: [], by_plan: [] },
    { accounts: [] }
  ];
  return empty[index];
}

function updateHeader(kpis) {
  document.getElementById("accountCount").textContent = window.Raven.format.number(kpis.total_accounts);
  const start = dashboardState.filters.start_date;
  const end = dashboardState.filters.end_date;
  document.getElementById("periodLabel").textContent = start || end ? `${start || "inicio"} - ${end || "hoje"}` : "Base completa";
}

function renderKpis(data, supportSummary) {
  const f = window.Raven.format;
  const groups = [
    {
      title: "Base de clientes",
      cards: [
        ["Total de contas", f.number(data.total_accounts), "Contas unicas no filtro", "base"],
        ["Contas ativas", f.number(data.active_accounts), "Status consolidado atual", "active"],
        ["Contas com churn", f.number(data.churned_accounts), "Conta com churn vigente", "churn"],
        ["Taxa de churn", f.percent(data.churn_rate, 2), `${f.number(data.churned_accounts)} de ${f.number(data.total_accounts)} contas`, "rate"]
      ]
    },
    {
      title: "Receita",
      cards: [
        ["MRR ativo", f.money(data.active_mrr), "Assinatura considerada por conta", "mrr"],
        ["ARR ativo", f.money(data.active_arr), "Assinatura considerada por conta", "arr"],
        ["MRR perdido", f.money(data.lost_mrr), "MRR de contas churn", "lost"],
        ["ARR perdido", f.money(data.lost_arr), "ARR de contas churn", "lost"]
      ]
    },
    {
      title: "Experiencia e risco",
      cards: [
        ["Total de tickets", f.number(data.total_tickets), "Tickets de suporte", "tickets"],
        ["Satisfacao media", Number(supportSummary.avg_satisfaction || 0).toFixed(2), "Media dos tickets filtrados", "satisfaction"],
        ["Contas reativadas", f.number(data.reactivated_accounts), "Com evento de reativacao", "reactivated"],
        ["Alto risco", f.number(data.high_risk_accounts), "Ativas com score >= 60", "risk"]
      ]
    }
  ];
  document.getElementById("kpiGrid").innerHTML = groups.map((group) => `
    <section class="kpi-group">
      <div class="kpi-group-header"><h3>${group.title}</h3></div>
      <div class="kpi-row">
        ${group.cards.map(([label, value, help, icon]) => `
          <article class="kpi-card" title="${help}">
            <div class="kpi-top">
              <span>${label}</span>
              <span class="kpi-icon" aria-hidden="true">${iconSvg(icon)}</span>
            </div>
            <div><strong>${value ?? "-"}</strong><small>${help}</small></div>
          </article>
        `).join("")}
      </div>
    </section>
  `).join("");
}

function renderAttention(kpis, reasons, segments, revenue, risks) {
  const critical = risks.filter((row) => row.risk_classification === "critico" && row.status === "ativa").length;
  const topReason = (reasons.reasons || [])[0];
  const topSegment = [...(segments.industry || [])].sort((a, b) => b.churn_rate - a.churn_rate)[0];
  const topLostPlan = (revenue.lost_mrr_by_plan || [])[0];
  const highValueRisk = risks.filter((row) => row.status === "ativa" && row.value_score >= 70 && row.risk_score >= 60).length;
  const cards = [
    ["Risco critico", `${critical} contas`, "Precisam de atencao imediata", "#risk"],
    ["Maior motivo", topReason ? topReason.reason_code : "-", topReason ? `${topReason.churn_events} eventos` : "Sem dados", "#churn"],
    ["Segmento sensivel", topSegment ? topSegment.segment : "-", topSegment ? `${window.Raven.format.percent(topSegment.churn_rate, 1)} de churn` : "Sem dados", "#churn"],
    ["Receita em risco", topLostPlan ? topLostPlan.segment : "-", topLostPlan ? `${window.Raven.format.money(topLostPlan.value)} de MRR perdido` : "Sem dados", "#revenue"],
    ["Alto valor em risco", `${highValueRisk} contas`, "Risco alto ou critico com valor relevante", "#risk"],
    ["Base filtrada", `${window.Raven.format.number(kpis.total_accounts)} contas`, "Escopo atual dos indicadores", "#overview"]
  ];
  document.getElementById("attentionGrid").innerHTML = cards.map(([label, value, body, href]) => `
    <a class="attention-card" href="${href}">
      <span>${label}</span>
      <strong>${value}</strong>
      <p>${body}</p>
    </a>
  `).join("");
}

function renderActionPlan(kpis, reasons, segments, revenue, support, risks) {
  const f = window.Raven.format;
  const criticalAccounts = risks.filter((row) => row.risk_classification === "critico" && row.status === "ativa");
  const highValueRisk = risks.filter((row) => row.status === "ativa" && row.value_score >= 70 && row.risk_score >= 60);
  const inactiveRisk = risks.filter((row) => row.status === "ativa" && (row.days_since_last_usage === null || row.days_since_last_usage > 45));
  const lowSatisfactionRisk = risks.filter((row) => row.status === "ativa" && row.avg_satisfaction > 0 && row.avg_satisfaction < 3.5);
  const topReason = (reasons.reasons || [])[0];
  const topIndustry = [...(segments.industry || [])].sort((a, b) => b.churn_rate - a.churn_rate)[0];
  const topLostPlan = (revenue.lost_mrr_by_plan || [])[0];
  const supportSummary = support.summary || {};

  const steps = [
    {
      title: "Conter contas criticas",
      metric: `${f.number(criticalAccounts.length)} contas`,
      action: "Abrir war room de CS e Produto para as contas ativas com risco critico, priorizando contato executivo em ate 48h.",
      anchor: "#risk"
    },
    {
      title: "Proteger receita de alto valor",
      metric: `${f.number(highValueRisk.length)} contas`,
      action: `Revisar contratos, health score e proximas renovacoes das contas com maior valor em risco. ${topLostPlan ? `Plano mais sensivel: ${topLostPlan.segment}.` : ""}`,
      anchor: "#revenue"
    },
    {
      title: "Atacar causa raiz do churn",
      metric: topReason ? topReason.reason_code : "Sem motivo dominante",
      action: topReason ? `Transformar o motivo "${topReason.reason_code}" em plano de correcao com owner, prazo e experimento de retencao.` : "Padronizar captura dos motivos de churn para orientar as proximas decisoes.",
      anchor: "#churn"
    },
    {
      title: "Reativar engajamento baixo",
      metric: `${f.number(inactiveRisk.length)} contas`,
      action: "Rodar campanha de ativacao para contas sem uso recente, conectando onboarding, features essenciais e acompanhamento semanal.",
      anchor: "#usage"
    },
    {
      title: "Elevar experiencia nos segmentos frageis",
      metric: topIndustry ? topIndustry.segment : "Base completa",
      action: `Criar rotina de revisao por segmento com Suporte e CS. ${topIndustry ? `Churn do segmento lider: ${f.percent(topIndustry.churn_rate, 1)}.` : ""} ${lowSatisfactionRisk.length ? `${f.number(lowSatisfactionRisk.length)} contas em risco tambem tem baixa satisfacao.` : `Satisfacao media atual: ${Number(supportSummary.avg_satisfaction || 0).toFixed(2)}.`}`,
      anchor: "#support"
    }
  ];

  document.getElementById("actionPlan").innerHTML = steps.map((step, index) => `
    <article class="action-step">
      <div class="action-step-rank">P${index + 1}</div>
      <div class="action-step-body">
        <div class="action-step-top">
          <h3>${step.title}</h3>
          <span>${step.metric}</span>
        </div>
        <p>${step.action}</p>
        <a href="${step.anchor}">Ver dados relacionados</a>
      </div>
    </article>
  `).join("");
}

function renderCharts(timeline, reasons, segments, revenue, usage, support, reactivation) {
  const charts = window.Raven.charts;
  charts.dualAxisTimeline("churnTimeline", timeline.timeline);
  charts.horizontalBar("churnReasons", reasons.reasons || [], "reason_code", "churn_events", charts.colors.red, { limit: 8 });
  charts.segment("churnPlan", segments.plan_tier);
  charts.segment("churnIndustry", segments.industry);
  charts.segment("churnCountry", segments.country);
  charts.horizontalBar("mrrPlan", revenue.mrr_by_plan || [], "segment", "value", charts.colors.blue, { formatter: window.Raven.format.money });
  charts.horizontalBar("arrIndustry", revenue.arr_by_industry || [], "segment", "value", charts.colors.green, { formatter: window.Raven.format.money });
  charts.horizontalBar("lostMrrPlan", revenue.lost_mrr_by_plan || [], "segment", "value", charts.colors.red, { formatter: window.Raven.format.money });
  charts.bar("mrrBands", revenue.mrr_bands || [], "band", "accounts", charts.colors.amber);
  charts.horizontalBar("featureUsage", usage.features || [], "feature_name", "usage_count", charts.colors.blue);
  charts.bar("usageStatus", usage.active_vs_churn || [], "status", "avg_usage_count", charts.colors.green);
  charts.bar("usageTimeline", usage.timeline || [], "month", "usage_count", charts.colors.blue);
  charts.bar("betaUsage", usage.beta || [], "feature_type", "usage_count", charts.colors.amber);
  charts.bar("ticketsPriority", support.priority || [], "priority", "tickets", charts.colors.blue);
  charts.bar("supportStatus", support.active_vs_churn || [], "status", "tickets", charts.colors.amber);
  charts.bar("reactivationChart", reactivation.timeline || [], "month", "reactivations", charts.colors.green);
  renderSupportSummary(support.summary || {});
}

function renderSupportSummary(summary) {
  document.getElementById("supportSummary").innerHTML = `
    <div class="panel-header"><div><h2>Resumo de suporte</h2><p>Indicadores medios dos tickets filtrados.</p></div></div>
    <div class="insight-list">
      <div class="insight-item"><span>Primeira resposta</span><strong>${summary.avg_first_response_minutes || 0} min</strong></div>
      <div class="insight-item"><span>Resolucao</span><strong>${summary.avg_resolution_hours || 0} h</strong></div>
      <div class="insight-item"><span>Satisfacao</span><strong>${summary.avg_satisfaction || 0}</strong></div>
      <div class="insight-item"><span>Escalonamento</span><strong>${window.Raven.format.percent(summary.escalation_rate, 2)}</strong></div>
    </div>`;
}

function renderRiskSummary() {
  const counts = { critico: 0, alto: 0, medio: 0, baixo: 0 };
  dashboardState.riskRows.forEach((row) => { counts[row.risk_classification] = (counts[row.risk_classification] || 0) + 1; });
  document.getElementById("riskSummary").innerHTML = [
    ["Critico", counts.critico, "critico"],
    ["Alto", counts.alto, "alto"],
    ["Medio", counts.medio, "medio"],
    ["Baixo", counts.baixo, "baixo"]
  ].map(([label, count, klass]) => `<div class="risk-summary-card"><span>${label}</span><strong>${count}</strong><em class="badge-risk ${klass}">${label}</em></div>`).join("");
  window.Raven.charts.bar("riskDistribution", [
    { label: "Critico", value: counts.critico },
    { label: "Alto", value: counts.alto },
    { label: "Medio", value: counts.medio },
    { label: "Baixo", value: counts.baixo }
  ], "label", "value", window.Raven.charts.colors.purple, { layout: { margin: { l: 38, r: 10, t: 12, b: 42 } } });
}

function filteredRiskRows() {
  const search = document.getElementById("riskSearch").value.toLowerCase();
  return dashboardState.riskRows.filter((row) => {
    const matchesSearch = `${row.account_name} ${row.account_id}`.toLowerCase().includes(search);
    const quick = dashboardState.riskQuickFilter;
    const matchesQuick =
      quick === "all" ||
      (quick === "critical" && row.risk_classification === "critico") ||
      (quick === "high" && ["alto", "critico"].includes(row.risk_classification)) ||
      (quick === "value" && row.value_score >= 70) ||
      (quick === "inactive" && (row.days_since_last_usage === null || row.days_since_last_usage > 45)) ||
      (quick === "satisfaction" && row.avg_satisfaction > 0 && row.avg_satisfaction < 3.5);
    return matchesSearch && matchesQuick;
  });
}

function renderRiskTable() {
  let rows = filteredRiskRows();
  rows.sort((a, b) => {
    const av = a[dashboardState.riskSort];
    const bv = b[dashboardState.riskSort];
    return (dashboardState.riskDirection === "asc" ? 1 : -1) * (av > bv ? 1 : av < bv ? -1 : 0);
  });
  const page = window.Raven.ui.paginate({
    rows,
    page: dashboardState.riskPage,
    pageSize: 12,
    targetId: "riskPagination",
    onPage: (nextPage) => { dashboardState.riskPage = nextPage; renderRiskTable(); }
  });
  dashboardState.riskPage = page.page;
  const table = document.getElementById("riskTable");
  if (!page.pageRows.length) {
    table.innerHTML = `<tbody><tr><td>${window.Raven.ui.emptyState()}</td></tr></tbody>`;
    return;
  }
  const cols = [
    ["account_name", "Conta"],
    ["plan_tier", "Plano"],
    ["mrr", "MRR"],
    ["usage_recent", "Uso recente"],
    ["ticket_count", "Tickets"],
    ["avg_satisfaction", "Satisfacao"],
    ["risk_score", "Risk score"],
    ["priority_score", "Prioridade"],
    ["risk_signals", "Sinais"]
  ];
  table.innerHTML = `<thead><tr>${cols.map((col) => `<th data-key="${col[0]}">${col[1]}</th>`).join("")}<th>Acao</th></tr></thead>
    <tbody>${page.pageRows.map((row) => `<tr class="${row.risk_classification === "critico" ? "critical" : row.risk_classification === "alto" ? "high" : ""}">
      <td><span class="account-name">${row.account_name}</span><span class="account-id">${row.account_id}</span><span class="badge-risk ${row.risk_classification}">${window.Raven.format.riskLabel(row.risk_classification)}</span></td>
      <td>${row.plan_tier || "-"}</td>
      <td>${window.Raven.format.money(row.mrr)}</td>
      <td>${window.Raven.format.number(row.usage_recent)}</td>
      <td>${window.Raven.format.number(row.ticket_count)}</td>
      <td>${Number(row.avg_satisfaction || 0).toFixed(2)}</td>
      <td><strong>${row.risk_score}</strong></td>
      <td><strong>${row.priority_score}</strong></td>
      <td title="${row.risk_signals || ""}">${truncate(row.risk_signals, 72)}</td>
      <td><a class="btn btn-secondary" href="/accounts/${row.account_id}">Ver detalhes</a></td>
    </tr>`).join("")}</tbody>`;
  table.querySelectorAll("th[data-key]").forEach((th) => {
    th.addEventListener("click", () => {
      dashboardState.riskSort = th.dataset.key;
      dashboardState.riskDirection = dashboardState.riskDirection === "asc" ? "desc" : "asc";
      renderRiskTable();
    });
  });
}

function renderActiveFilters() {
  const container = document.getElementById("activeFilters");
  const entries = Object.entries(dashboardState.filters).filter(([, value]) => value !== "");
  if (!entries.length) {
    container.innerHTML = `<span class="chip">Base completa</span>`;
    return;
  }
  container.innerHTML = entries.map(([key, value]) => `<button class="chip" type="button" data-filter-key="${key}">${filterLabels[key] || key}: ${labelValue(key, value)} x</button>`).join("");
  container.querySelectorAll("[data-filter-key]").forEach((button) => {
    button.addEventListener("click", () => {
      const key = button.dataset.filterKey;
      dashboardState.filters[key] = "";
      const field = document.querySelector(`[name="${key}"]`);
      if (field) field.value = "";
      refreshDashboard();
      window.Raven.ui.toast("Filtro removido.");
    });
  });
}

function labelValue(key, value) {
  if (key === "is_trial") return value === "1" || value === 1 ? "Trial" : "Pagante";
  if (key === "auto_renew_flag") return value === "1" || value === 1 ? "Automatica" : "Manual";
  if (key === "status") return value === "active" ? "Ativo" : "Churn";
  return value;
}

function iconSvg(name) {
  const paths = {
    base: "M4 5h16v14H4V5Zm2 2v10h12V7H6Z",
    active: "M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2Z",
    churn: "M12 2 2 20h20L12 2Zm1 15h-2v-2h2v2Zm0-4h-2V8h2v5Z",
    rate: "M7 17 17 7l1.4 1.4-10 10L7 17Zm1-6a3 3 0 1 1 0-6 3 3 0 0 1 0 6Zm8 8a3 3 0 1 1 0-6 3 3 0 0 1 0 6Z",
    mrr: "M11 2h2v3c2.8.4 5 2.1 5 4.6h-2c0-1.5-1.8-2.7-4-2.7S8 8.1 8 9.6c0 1.4 1.3 2 4.4 2.8 3.1.8 5.6 1.8 5.6 4.8 0 2.5-2.1 4.2-5 4.7V24h-2v-2.1c-3.2-.4-5.6-2.2-5.6-5h2c0 1.8 2 3.1 4.6 3.1 2.4 0 4-1.1 4-2.8 0-1.4-1.1-2.1-4.2-2.9C8.6 13.5 6 12.5 6 9.7 6 7.3 8 5.5 11 5.1V2Z",
    arr: "M4 19h16v2H4v-2Zm1-3 5-5 4 4 6-8 1.6 1.2-7.4 9.8-4.1-4.1L6.4 17.4 5 16Z",
    lost: "M12 22A10 10 0 1 1 12 2a10 10 0 0 1 0 20Zm-4-9h8v-2H8v2Z",
    tickets: "M4 4h16v12H7l-3 3V4Z",
    satisfaction: "M12 22a10 10 0 1 1 0-20 10 10 0 0 1 0 20Zm-4-8c1 2 2.4 3 4 3s3-1 4-3H8Z",
    reactivated: "M12 6V3L8 7l4 4V8a4 4 0 1 1-4 4H6a6 6 0 1 0 6-6Z",
    risk: "M12 2 2 20h20L12 2Z"
  };
  return `<svg viewBox="0 0 24 24"><path d="${paths[name] || paths.base}"/></svg>`;
}

function truncate(value, size) {
  if (!value) return "-";
  return value.length > size ? `${value.slice(0, size)}...` : value;
}

function showLoading(show) {
  document.getElementById("loading").style.display = show ? "grid" : "none";
}

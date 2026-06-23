const state = {
  portal: "seller",
  selectedSeller: "",
  selectedManager: "",
  managerTab: "scenario",
  signal: "all",
  search: "",
  approvals: {},
};

let dashboard = null;

const signalLabels = {
  manter: "Manter",
  consultar_especialista: "Consultar especialista",
  remanejar: "Remanejar",
  manager_review: "Revisão gerente",
  corrigir_dados: "Corrigir dados",
  last_chance: "Última tentativa",
  nurture: "Nutrição",
};

const ageLabels = {
  prospecting: "Prospecting",
  normal: "0-90 dias",
  recovery: "91-180 dias",
  intervention: "181-270 dias",
  quarantine: ">270 dias",
  unknown_age: "Sem idade",
};

const redFlagLabels = {
  none: "Sem red-flag",
  tier_1_low_performance: "Tier 1",
  tier_2_last_chance: "Tier 2",
  tier_3_capacity_watch: "Tier 3",
};

const approvalStatusLabels = {
  pending: "Pendente",
  approved: "Aprovado",
  rejected: "Recusado",
  delegated: "Apoio delegado",
};

const approvalStatusClasses = {
  pending: "warning",
  approved: "success",
  rejected: "danger",
  delegated: "brand",
};

const money = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

function $(selector) {
  return document.querySelector(selector);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function fmtMoney(value) {
  return money.format(Number(value || 0));
}

function fmtPct(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return `${(Number(value) * 100).toFixed(1)}%`;
}

function signalClass(signal) {
  return {
    manter: "brand",
    consultar_especialista: "warning",
    remanejar: "success",
    manager_review: "warning",
    corrigir_dados: "danger",
    last_chance: "danger",
    nurture: "neutral",
  }[signal] || "neutral";
}

function priorityClass(priority) {
  return {
    alta: "success",
    media: "brand",
    baixa: "neutral",
    revisao: "warning",
  }[priority] || "neutral";
}

function confidenceClass(confidence) {
  return {
    alta: "success",
    media: "warning",
    baixa: "danger",
  }[confidence] || "neutral";
}

function redFlagClass(tier) {
  return {
    tier_1_low_performance: "danger",
    tier_2_last_chance: "warning",
    tier_3_capacity_watch: "warning",
    none: "neutral",
  }[tier] || "neutral";
}

function badge(label, type = "neutral") {
  return `<span class="badge ${type}">${escapeHtml(label)}</span>`;
}

function metricCard(label, value, note = "") {
  return `
    <article class="metric-card">
      <p class="metric-label">${escapeHtml(label)}</p>
      <div class="metric-value">${escapeHtml(value)}</div>
      <p class="metric-note">${escapeHtml(note)}</p>
    </article>
  `;
}

function scoreBreakdown(deal) {
  const components = [
    ["Valor", deal.value_score],
    ["Fit", deal.fit_score],
    ["Tempo", deal.timing_score],
    ["Conta", deal.account_score],
  ];
  return `
    <div class="score-breakdown" aria-label="Composição do score">
      ${components
        .map(
          ([label, value]) => `
            <span class="score-component">
              ${escapeHtml(label)} <strong>${Number(value || 0).toFixed(0)}</strong>
            </span>
          `,
        )
        .join("")}
    </div>
  `;
}

function loadApprovalDecisions() {
  try {
    state.approvals = JSON.parse(localStorage.getItem("leadScorerApprovalDecisions") || "{}");
  } catch {
    state.approvals = {};
  }
}

function saveApprovalDecisions() {
  localStorage.setItem("leadScorerApprovalDecisions", JSON.stringify(state.approvals));
}

function getApprovalStatus(deal) {
  return state.approvals[deal.opportunity_id]?.status || "pending";
}

function setApprovalDecision(opportunityId, status) {
  state.approvals[opportunityId] = {
    status,
    decidedAt: new Date().toISOString(),
  };
  saveApprovalDecisions();
  render();
}

function setPortal(portal) {
  state.portal = portal;
  state.signal = "all";
  $("#signalFilter").value = "all";
  $(".portal-button.active")?.classList.remove("active");
  document.querySelector(`[data-portal="${portal}"]`).classList.add("active");
  populatePrimarySelect();
  render();
}

function setManagerTab(tab) {
  state.managerTab = tab;
  document.querySelectorAll("[data-manager-tab]").forEach((button) => {
    button.classList.toggle("active", button.dataset.managerTab === tab);
  });
  render();
}

function populatePrimarySelect() {
  const select = $("#primarySelect");
  select.innerHTML = "";

  if (state.portal === "seller") {
    $("#primarySelectLabel").textContent = "Vendedor";
    const sellers = [...dashboard.sellers].sort((a, b) =>
      a.current_sales_agent.localeCompare(b.current_sales_agent),
    );
    if (!state.selectedSeller || !sellers.some((s) => s.current_sales_agent_id === state.selectedSeller)) {
      state.selectedSeller = sellers[0]?.current_sales_agent_id || "";
    }
    select.innerHTML = sellers
      .map(
        (seller) =>
          `<option value="${escapeHtml(seller.current_sales_agent_id)}">${escapeHtml(seller.current_sales_agent)}</option>`,
      )
      .join("");
    select.value = state.selectedSeller;
  } else {
    $("#primarySelectLabel").textContent = "Gerente";
    const managers = [...dashboard.managers].sort((a, b) =>
      a.current_manager.localeCompare(b.current_manager),
    );
    if (!state.selectedManager || !managers.some((m) => m.current_manager === state.selectedManager)) {
      state.selectedManager = managers[0]?.current_manager || "";
    }
    select.innerHTML = managers
      .map(
        (manager) =>
          `<option value="${escapeHtml(manager.current_manager)}">${escapeHtml(manager.current_manager)}</option>`,
      )
      .join("");
    select.value = state.selectedManager;
  }
}

function getFilteredDeals() {
  const term = state.search.trim().toLowerCase();
  return dashboard.deals
    .filter((deal) => {
      if (state.portal === "seller" && deal.current_sales_agent_id !== state.selectedSeller) return false;
      if (state.portal === "manager" && deal.current_manager !== state.selectedManager) return false;
      if (state.signal !== "all" && deal.routing_signal !== state.signal) return false;
      if (!term) return true;
      return [
        deal.opportunity_id,
        deal.account,
        deal.product,
        deal.current_sales_agent,
        deal.recommended_sales_agent,
        deal.sector,
        deal.routing_signal,
      ]
        .join(" ")
        .toLowerCase()
        .includes(term);
    })
    .sort((a, b) => {
      const signalRank = {
        remanejar: 6,
        manager_review: 5,
        corrigir_dados: 4,
        last_chance: 3,
        consultar_especialista: 2,
        manter: 1,
        nurture: 0,
      };
      if (state.portal === "manager") {
        return (
          (signalRank[b.routing_signal] || 0) - (signalRank[a.routing_signal] || 0) ||
          Number(b.estimated_deal_value || 0) - Number(a.estimated_deal_value || 0) ||
          Number(b.priority_score || 0) - Number(a.priority_score || 0)
        );
      }
      return (
        Number(b.priority_score || 0) - Number(a.priority_score || 0) ||
        Number(b.estimated_deal_value || 0) - Number(a.estimated_deal_value || 0)
      );
    });
}

function dealMatchesSearch(deal) {
  const term = state.search.trim().toLowerCase();
  if (!term) return true;
  return [
    deal.opportunity_id,
    deal.account,
    deal.product,
    deal.current_sales_agent,
    deal.recommended_sales_agent,
    deal.sector,
    deal.routing_signal,
  ]
    .join(" ")
    .toLowerCase()
    .includes(term);
}

function getApprovalDealsForCurrentManager() {
  if (state.portal !== "manager") return [];
  return dashboard.deals
    .filter((deal) => {
      if (deal.current_manager !== state.selectedManager) return false;
      if (!deal.approval_required) return false;
      if (state.signal !== "all" && deal.routing_signal !== state.signal) return false;
      return dealMatchesSearch(deal);
    })
    .sort((a, b) => {
      const statusRank = { pending: 3, delegated: 2, approved: 1, rejected: 0 };
      const signalRank = { remanejar: 2, manager_review: 1 };
      return (
        (statusRank[getApprovalStatus(b)] || 0) - (statusRank[getApprovalStatus(a)] || 0) ||
        (signalRank[b.routing_signal] || 0) - (signalRank[a.routing_signal] || 0) ||
        Number(b.estimated_deal_value || 0) - Number(a.estimated_deal_value || 0) ||
        Number(b.priority_score || 0) - Number(a.priority_score || 0)
      );
    });
}

function renderMetrics(deals) {
  let html = "";
  if (state.portal === "seller") {
    const seller = dashboard.sellers.find((item) => item.current_sales_agent_id === state.selectedSeller);
    html = [
      metricCard("Carteira aberta", fmtMoney(seller?.open_value), `${seller?.open_deals || 0} deals`),
      metricCard("Score medio", String(seller?.avg_priority_score ?? "-"), `${seller?.high_priority_deals || 0} alta prioridade`),
      metricCard("Revisao", String(seller?.review_deals || 0), `${seller?.low_confidence_deals || 0} baixa confianca`),
      metricCard("Sinal de risco", redFlagLabels[seller?.seller_red_flag_tier] || "-", seller?.seller_action || ""),
    ].join("");
  } else {
    const manager = dashboard.managers.find((item) => item.current_manager === state.selectedManager);
    const approvals = getApprovalDealsForCurrentManager();
    const pendingApprovals = approvals.filter((deal) => getApprovalStatus(deal) === "pending");
    const remanejarApprovals = approvals.filter((deal) => deal.routing_signal === "remanejar").length;
    const reviewApprovals = approvals.filter((deal) => deal.routing_signal === "manager_review").length;
    html = [
      metricCard("Pipeline aberto", fmtMoney(manager?.open_value), `${manager?.open_deals || 0} deals`),
      metricCard("Aprovações", String(pendingApprovals.length), `${remanejarApprovals} remanejamentos · ${reviewApprovals} revisões`),
      metricCard("Corrigir dados", String(manager?.data_fix_deals || 0), `${manager?.low_confidence_deals || 0} baixa confianca`),
      metricCard("Última tentativa", String(manager?.last_chance_deals || 0), `${manager?.red_flag_sellers || 0} vendedores em alerta`),
    ].join("");
  }
  $("#metricsGrid").innerHTML = html;
}

function renderDealsTable(deals) {
  $("#tableWrap").innerHTML = `
    <table>
      <thead id="dealsHead"></thead>
      <tbody id="dealsBody"></tbody>
    </table>
  `;
  $("#tableCount").textContent = `${deals.length} deals`;
  if (state.portal === "seller") {
    $("#dealsHead").innerHTML = `
      <tr>
        <th>Deal</th>
        <th>Score</th>
        <th>Ação</th>
        <th>Valor</th>
        <th>Idade</th>
        <th>Fit</th>
        <th>Motivos</th>
      </tr>
    `;
  } else {
    $("#dealsHead").innerHTML = `
      <tr>
        <th>Deal</th>
        <th>Vendedor</th>
        <th>Sinal</th>
        <th>Valor</th>
        <th>Score</th>
        <th>Especialista consultivo</th>
        <th>Motivos</th>
      </tr>
    `;
  }

  if (!deals.length) {
    $("#dealsBody").innerHTML = `<tr><td colspan="7"><div class="empty-state">Nenhuma oportunidade encontrada.</div></td></tr>`;
    return;
  }

  $("#dealsBody").innerHTML = deals
    .slice(0, 80)
    .map((deal) => {
      const reasonValues = (deal.reason_codes_list || String(deal.reason_codes || "").split(" | ")).slice(0, 4);
      const primaryReason = reasonValues[0] || "Prioridade calculada por score balanceado";
      const dealCell = `
        <div class="deal-main">
          <span class="deal-id">${escapeHtml(deal.opportunity_id)}</span>
          <span class="deal-sub">${escapeHtml(deal.product)} · ${escapeHtml(deal.account || "Conta ausente")}</span>
          <span class="deal-sub">${escapeHtml(primaryReason)}</span>
        </div>
      `;
      const reasons = reasonValues
        .map((reason) => `<span class="reason-item">${escapeHtml(reason)}</span>`)
        .join("");
      const scoreCell = `
        <div class="score-stack">
          <div class="score-main">
            <span class="score-pill">${Number(deal.priority_score || 0).toFixed(1)}</span>
            ${badge(deal.priority_band, priorityClass(deal.priority_band))}
          </div>
          ${scoreBreakdown(deal)}
        </div>
      `;
      if (state.portal === "seller") {
        return `
          <tr>
            <td>${dealCell}</td>
            <td>${scoreCell}</td>
            <td>${badge(signalLabels[deal.routing_signal], signalClass(deal.routing_signal))}</td>
            <td>${fmtMoney(deal.estimated_deal_value)}</td>
            <td>${escapeHtml(ageLabels[deal.age_class] || deal.age_class)}</td>
            <td>
              <div class="deal-main">
                <span>${Number(deal.current_match_score || 0).toFixed(1)}</span>
                <span class="deal-sub">delta ${Number(deal.fit_delta || 0).toFixed(1)}</span>
              </div>
            </td>
            <td><div class="reason-list">${reasons}</div></td>
          </tr>
        `;
      }
      return `
        <tr>
          <td>${dealCell}</td>
          <td>
            <div class="deal-main">
              <span class="deal-id">${escapeHtml(deal.current_sales_agent)}</span>
              <span class="deal-sub">${escapeHtml(redFlagLabels[deal.seller_red_flag_tier] || "Sem red-flag")}</span>
            </div>
          </td>
          <td>
            <div class="deal-main">
              <span>${badge(signalLabels[deal.routing_signal], signalClass(deal.routing_signal))}</span>
              ${
                deal.approval_required
                  ? `<span>${badge(approvalStatusLabels[getApprovalStatus(deal)], approvalStatusClasses[getApprovalStatus(deal)])}</span>`
                  : ""
              }
            </div>
          </td>
          <td>${fmtMoney(deal.estimated_deal_value)}</td>
          <td>${scoreCell}</td>
          <td>
            <div class="deal-main">
              <span>${escapeHtml(deal.recommended_sales_agent || "-")}</span>
              <span class="deal-sub">${
                deal.routing_signal === "remanejar"
                  ? "Ownership sujeito à aprovação"
                  : "Apoio consultivo, sem transferência"
              }</span>
              <span class="deal-sub">fit +${Number(deal.fit_delta || 0).toFixed(1)}</span>
            </div>
          </td>
          <td><div class="reason-list">${reasons}</div></td>
        </tr>
      `;
    })
    .join("");
}

function renderApprovalQueue(approvals) {
  const pendingCount = approvals.filter((deal) => getApprovalStatus(deal) === "pending").length;
  $("#tableCount").textContent = `${pendingCount} pendentes`;

  if (!approvals.length) {
    $("#tableWrap").innerHTML = `<div class="empty-state">Nenhuma aprovação para os filtros atuais.</div>`;
    return;
  }

  $("#tableWrap").innerHTML = `
    <div class="approval-list">
      ${approvals
        .slice(0, 18)
        .map((deal) => {
          const status = getApprovalStatus(deal);
          const reasonValues = (deal.reason_codes_list || String(deal.reason_codes || "").split(" | ")).slice(0, 3);
          const primaryReason = reasonValues[0] || "Prioridade calculada por score balanceado";
          const route =
            deal.routing_signal === "remanejar"
              ? `${deal.current_sales_agent} → ${deal.recommended_sales_agent}`
              : `${deal.current_sales_agent} · revisão antes da ação`;
          return `
            <article class="approval-card ${status === "pending" ? "" : status}">
              <div class="approval-topline">
                <div class="approval-title">
                  <strong>${escapeHtml(deal.opportunity_id)} · ${escapeHtml(deal.product)}</strong>
                  <span>${escapeHtml(deal.account || "Conta ausente")}</span>
                </div>
                ${badge(approvalStatusLabels[status], approvalStatusClasses[status])}
              </div>
              <div class="approval-route">
                <span>${badge(deal.approval_label || signalLabels[deal.routing_signal], signalClass(deal.routing_signal))}</span>
                <span>${escapeHtml(route)}</span>
                <span>${fmtMoney(deal.estimated_deal_value)} · score ${Number(deal.priority_score || 0).toFixed(1)} · fit +${Number(deal.fit_delta || 0).toFixed(1)}</span>
                <span>${escapeHtml(primaryReason)}</span>
              </div>
              <div class="approval-actions">
                <button class="action-button primary" type="button" data-approval-action="approved" data-deal-id="${escapeHtml(deal.opportunity_id)}">Aprovar</button>
                <button class="action-button" type="button" data-approval-action="delegated" data-deal-id="${escapeHtml(deal.opportunity_id)}">Delegar apoio</button>
                <button class="action-button" type="button" data-approval-action="rejected" data-deal-id="${escapeHtml(deal.opportunity_id)}">Recusar</button>
              </div>
            </article>
          `;
        })
        .join("")}
    </div>
  `;
}

function summaryRow(label, value) {
  return `
    <div class="summary-row">
      <span class="summary-label">${escapeHtml(label)}</span>
      <span class="summary-value">${value}</span>
    </div>
  `;
}

function renderSellerSide() {
  const seller = dashboard.sellers.find((item) => item.current_sales_agent_id === state.selectedSeller);
  if (!seller) return;
  $("#sideEyebrow").textContent = "Resumo";
  $("#sideTitle").textContent = seller.current_sales_agent;
  $("#sideContent").innerHTML = [
    summaryRow("Manager", escapeHtml(seller.current_manager)),
    summaryRow("Win rate historico", escapeHtml(fmtPct(seller.win_rate))),
    summaryRow("Historico", escapeHtml(seller.history_maturity)),
    summaryRow("Performance", escapeHtml(seller.performance_band)),
    summaryRow("Red-flag", badge(redFlagLabels[seller.seller_red_flag_tier], redFlagClass(seller.seller_red_flag_tier))),
    summaryRow("Backlog antigo", `${Number(seller.old_engaging_deals || 0)} deals`),
    summaryRow("Corrigir dados", `${Number(seller.corrigir_dados_deals || 0)} deals`),
    summaryRow("Consultar especialista", `${Number(seller.consultar_especialista_deals || 0)} deals`),
    summaryRow("Remanejar", `${Number(seller.remanejar_deals || 0)} deals`),
  ].join("");
}

function renderManagerSide() {
  const manager = dashboard.managers.find((item) => item.current_manager === state.selectedManager);
  const sellers = dashboard.sellers
    .filter((seller) => seller.current_manager === state.selectedManager)
    .sort((a, b) => {
      const rank = {
        tier_1_low_performance: 3,
        tier_2_last_chance: 2,
        tier_3_capacity_watch: 1,
        none: 0,
      };
      return (
        (rank[b.seller_red_flag_tier] || 0) - (rank[a.seller_red_flag_tier] || 0) ||
        Number(b.open_value || 0) - Number(a.open_value || 0)
      );
    });
  $("#sideEyebrow").textContent = "Equipe";
  $("#sideTitle").textContent = state.selectedManager;
  $("#sideContent").innerHTML = `
    ${summaryRow("Foco do gerente", escapeHtml(manager?.manager_focus || "-"))}
    ${summaryRow("Red-flags", `${Number(manager?.red_flag_sellers || 0)} vendedores`)}
    ${summaryRow("Pipeline aberto", fmtMoney(manager?.open_value))}
    <div class="seller-list">
      ${sellers
        .map(
          (seller) => `
            <div class="seller-item">
              <div class="seller-item-title">
                <span>${escapeHtml(seller.current_sales_agent)}</span>
                <span>${fmtMoney(seller.open_value)}</span>
              </div>
              <div class="seller-item-meta">
                ${badge(redFlagLabels[seller.seller_red_flag_tier], redFlagClass(seller.seller_red_flag_tier))}
                ${badge(`${Number(seller.review_deals || 0)} revisão`, "warning")}
                ${badge(`${Number(seller.open_deals || 0)} deals`, "neutral")}
              </div>
            </div>
          `,
        )
        .join("")}
    </div>
  `;
}

function render() {
  const deals = getFilteredDeals();
  const isManager = state.portal === "manager";
  const isApprovalsTab = isManager && state.managerTab === "approvals";

  $("#managerTabs").hidden = !isManager;
  document.querySelectorAll("[data-manager-tab]").forEach((button) => {
    button.classList.toggle("active", button.dataset.managerTab === state.managerTab);
  });
  $("#contentGrid").classList.toggle("approvals-mode", isApprovalsTab);
  $("#sidePanel").hidden = isApprovalsTab;

  $("#portalEyebrow").textContent = state.portal === "seller" ? "Portal do vendedor" : "Portal do gerente";
  $("#portalTitle").textContent = state.portal === "seller" ? "Fila de prioridades" : "Gestão de carteira";

  renderMetrics(deals);

  if (state.portal === "seller") {
    $("#queueEyebrow").textContent = "Carteira atual";
    $("#queueTitle").textContent = "Oportunidades priorizadas";
    renderDealsTable(deals);
    renderSellerSide();
  } else if (isApprovalsTab) {
    const approvals = getApprovalDealsForCurrentManager();
    $("#queueEyebrow").textContent = "Aprovações pendentes";
    $("#queueTitle").textContent = "Fila de decisões do gerente";
    renderApprovalQueue(approvals);
  } else {
    $("#queueEyebrow").textContent = "Cenário";
    $("#queueTitle").textContent = "Risco e roteamento atual";
    renderDealsTable(deals);
    renderManagerSide();
  }
}

async function boot() {
  const response = await fetch("./data/dashboard_data.json");
  dashboard = await response.json();
  loadApprovalDecisions();

  $("#cutoffValue").textContent = fmtMoney(dashboard.cutoffs.high_value);
  $("#fitGapValue").textContent = `${dashboard.cutoffs.fit_delta_transfer}+`;

  document.querySelectorAll(".portal-button").forEach((button) => {
    button.addEventListener("click", () => setPortal(button.dataset.portal));
  });

  document.querySelectorAll("[data-manager-tab]").forEach((button) => {
    button.addEventListener("click", () => setManagerTab(button.dataset.managerTab));
  });

  $("#primarySelect").addEventListener("change", (event) => {
    if (state.portal === "seller") {
      state.selectedSeller = event.target.value;
    } else {
      state.selectedManager = event.target.value;
    }
    render();
  });

  $("#signalFilter").addEventListener("change", (event) => {
    state.signal = event.target.value;
    render();
  });

  $("#searchInput").addEventListener("input", (event) => {
    state.search = event.target.value;
    render();
  });

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-approval-action]");
    if (!button) return;
    setApprovalDecision(button.dataset.dealId, button.dataset.approvalAction);
  });

  populatePrimarySelect();
  render();
}

boot().catch((error) => {
  document.body.innerHTML = `<main class="empty-state">Erro ao carregar dados: ${escapeHtml(error.message)}</main>`;
});

const detail = JSON.parse(document.getElementById("detailData").textContent);

document.addEventListener("DOMContentLoaded", () => {
  bindTabs();
  renderSummaryCards();
  renderFacts();
  renderTables();
  renderUsageChart();
  renderTimeline();
  window.Raven.refreshPage = () => window.location.reload();
});

function bindTabs() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((item) => item.classList.toggle("active", item === tab));
      document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.toggle("active", panel.id === `tab-${tab.dataset.tab}`));
    });
  });
}

function renderSummaryCards() {
  const a = detail.account;
  const risk = detail.risk || {};
  const usageTotal = (detail.usage || []).reduce((sum, row) => sum + Number(row.usage_count || 0), 0);
  const errors = (detail.usage || []).reduce((sum, row) => sum + Number(row.errors || 0), 0);
  const cards = [
    ["Receita", window.Raven.format.money(a.mrr_amount), `${window.Raven.format.money(a.arr_amount)} ARR`],
    ["Uso", window.Raven.format.number(usageTotal), `${window.Raven.format.number(errors)} erros`],
    ["Suporte", window.Raven.format.number((detail.tickets || []).length), "tickets registrados"],
    ["Churn", window.Raven.format.number((detail.churn_events || []).length), "eventos e reativacoes"],
    ["Renovacao", a.auto_renew_flag ? "Automatica" : "Manual", risk.risk_signals || "sem sinais relevantes"]
  ];
  document.getElementById("accountSummaryCards").innerHTML = cards.map(([label, value, helper]) => `
    <article class="summary-card"><span>${label}</span><strong>${value}</strong><small>${helper}</small></article>
  `).join("");
}

function renderFacts() {
  const a = detail.account;
  document.getElementById("accountFacts").innerHTML = [
    ["Status", a.churned_account ? "Churn" : "Ativa"],
    ["Cadastro", window.Raven.format.date(a.signup_date)],
    ["Origem", a.referral_source],
    ["Plano", a.plan_tier],
    ["Assentos", a.seats],
    ["Trial", a.is_trial ? "sim" : "nao"],
    ["MRR", window.Raven.format.money(a.mrr_amount)],
    ["ARR", window.Raven.format.money(a.arr_amount)],
    ["Cobranca", a.billing_frequency],
    ["Renovacao automatica", a.auto_renew_flag ? "sim" : "nao"]
  ].map(([key, value]) => `<dt>${key}</dt><dd>${value ?? "-"}</dd>`).join("");
}

function renderTables() {
  table("subsTable", detail.subscriptions);
  table("churnTable", detail.churn_events);
  table("ticketsTable", detail.tickets);
}

function renderUsageChart() {
  const rows = detail.usage || [];
  window.Raven.charts.horizontalBar("accountUsageChart", rows, "feature_name", "usage_count", window.Raven.charts.colors.blue, { limit: 10 });
}

function renderTimeline() {
  const icons = {
    cadastro: "Cadastro",
    assinatura: "Assinatura",
    upgrade: "Upgrade",
    downgrade: "Downgrade",
    ticket: "Ticket",
    churn: "Churn",
    reativacao: "Reativacao",
    encerramento: "Encerramento"
  };
  document.getElementById("timeline").innerHTML = (detail.timeline || []).map((event) => `
    <li class="timeline-${event.type}">
      <span class="timeline-date">${window.Raven.format.date(event.date)}</span>
      <span class="timeline-title">${icons[event.type] || event.type}</span>
      <span>${event.label}</span>
    </li>
  `).join("") || window.Raven.ui.emptyState();
}

function table(id, rows) {
  const target = document.getElementById(id);
  if (!rows || !rows.length) {
    target.innerHTML = `<tbody><tr><td>${window.Raven.ui.emptyState("Sem registros", "Nao ha dados para esta conta.")}</td></tr></tbody>`;
    return;
  }
  const columns = Object.keys(rows[0]);
  target.innerHTML = `<thead><tr>${columns.map((column) => `<th>${column}</th>`).join("")}</tr></thead>
    <tbody>${rows.map((row) => `<tr>${columns.map((column) => `<td>${formatTableValue(column, row[column])}</td>`).join("")}</tr>`).join("")}</tbody>`;
}

function formatTableValue(column, value) {
  if (value === null || value === undefined || value === "") return "-";
  if (column.includes("date") || column.includes("_at")) return window.Raven.format.date(value);
  if (column.includes("mrr") || column.includes("arr") || column.includes("refund")) return window.Raven.format.money(value);
  return value;
}

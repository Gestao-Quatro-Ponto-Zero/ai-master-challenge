const accountsState = {
  rows: [],
  risks: new Map(),
  page: 1,
  sort: "account_name",
  direction: "asc",
  quickFilter: "all"
};

document.addEventListener("DOMContentLoaded", async () => {
  bindAccountsEvents();
  await loadAccounts();
  window.Raven.refreshPage = loadAccounts;
});

function bindAccountsEvents() {
  document.getElementById("accountsSearch").addEventListener("input", window.Raven.ui.debounce(() => {
    accountsState.page = 1;
    renderAccounts();
  }));
  document.getElementById("clearAccountFilters").addEventListener("click", () => {
    document.getElementById("accountsSearch").value = "";
    accountsState.quickFilter = "all";
    document.querySelectorAll("#accountQuickFilters .chip").forEach((button) => button.classList.toggle("active", button.dataset.accountFilter === "all"));
    accountsState.page = 1;
    renderAccounts();
    window.Raven.ui.toast("Filtros removidos.");
  });
  document.getElementById("accountQuickFilters").addEventListener("click", (event) => {
    const button = event.target.closest("[data-account-filter]");
    if (!button) return;
    accountsState.quickFilter = button.dataset.accountFilter;
    document.querySelectorAll("#accountQuickFilters .chip").forEach((item) => item.classList.toggle("active", item === button));
    accountsState.page = 1;
    renderAccounts();
  });
}

async function loadAccounts() {
  try {
    const [accounts, risk] = await Promise.all([
      window.Raven.api.get("/api/accounts"),
      window.Raven.api.get("/api/risk-accounts")
    ]);
    accountsState.risks = new Map((risk.accounts || []).map((row) => [row.account_id, row]));
    accountsState.rows = (accounts.accounts || []).map((row) => ({ ...row, risk: accountsState.risks.get(row.account_id) }));
    renderAccounts();
    window.Raven.ui.toast("Contas atualizadas.");
  } catch (error) {
    document.getElementById("accountsTable").innerHTML = `<tbody><tr><td>${window.Raven.ui.errorState(error.message)}</td></tr></tbody>`;
    window.Raven.ui.toast(error.message, "error");
  }
}

function accountRows() {
  const search = document.getElementById("accountsSearch").value.toLowerCase();
  return accountsState.rows.filter((row) => {
    const matchesSearch = `${row.account_name} ${row.account_id}`.toLowerCase().includes(search);
    const risk = row.risk || {};
    const quick = accountsState.quickFilter;
    const matchesQuick =
      quick === "all" ||
      (quick === "active" && row.status === "ativa") ||
      (quick === "churn" && row.status === "churn") ||
      (quick === "high-risk" && risk.risk_score >= 60) ||
      (quick === "high-value" && risk.value_score >= 70);
    return matchesSearch && matchesQuick;
  });
}

function renderAccounts() {
  let rows = accountRows();
  rows.sort((a, b) => {
    const av = sortValue(a, accountsState.sort);
    const bv = sortValue(b, accountsState.sort);
    return (accountsState.direction === "asc" ? 1 : -1) * (av > bv ? 1 : av < bv ? -1 : 0);
  });
  document.getElementById("accountsCount").textContent = window.Raven.format.number(rows.length);
  const page = window.Raven.ui.paginate({
    rows,
    page: accountsState.page,
    pageSize: 16,
    targetId: "accountsPagination",
    onPage: (nextPage) => { accountsState.page = nextPage; renderAccounts(); }
  });
  accountsState.page = page.page;
  const table = document.getElementById("accountsTable");
  if (!page.pageRows.length) {
    table.innerHTML = `<tbody><tr><td>${window.Raven.ui.emptyState()}</td></tr></tbody>`;
    return;
  }
  const cols = [
    ["account_name", "Conta"],
    ["industry", "Industria"],
    ["country", "Pais"],
    ["plan_tier", "Plano"],
    ["status", "Status"],
    ["mrr", "MRR"],
    ["risk_score", "Risco"],
    ["last_activity", "Ultima atividade"]
  ];
  table.innerHTML = `<thead><tr>${cols.map((col) => `<th data-key="${col[0]}">${col[1]}</th>`).join("")}<th>Acao</th></tr></thead>
    <tbody>${page.pageRows.map((row) => renderRow(row)).join("")}</tbody>`;
  table.querySelectorAll("th[data-key]").forEach((th) => {
    th.addEventListener("click", () => {
      accountsState.sort = th.dataset.key;
      accountsState.direction = accountsState.direction === "asc" ? "desc" : "asc";
      renderAccounts();
    });
  });
}

function renderRow(row) {
  const risk = row.risk || {};
  const classification = risk.risk_classification || "baixo";
  const statusClass = row.status === "churn" ? "danger" : "success";
  const lastActivity = risk.days_since_last_usage === null || risk.days_since_last_usage === undefined
    ? "-"
    : `${risk.days_since_last_usage} dias sem uso`;
  return `<tr>
    <td><span class="account-name">${row.account_name}</span><span class="account-id">${row.account_id}</span></td>
    <td>${row.industry || "-"}</td>
    <td>${row.country || "-"}</td>
    <td>${row.plan_tier || "-"}</td>
    <td><span class="status-pill ${statusClass}">${row.status}</span></td>
    <td>${window.Raven.format.money(row.mrr)}</td>
    <td><span class="badge-risk ${classification}">${window.Raven.format.riskLabel(classification)} ${risk.risk_score ?? 0}</span></td>
    <td>${lastActivity}</td>
    <td><a class="btn btn-secondary" href="/accounts/${row.account_id}">Ver detalhes</a></td>
  </tr>`;
}

function sortValue(row, key) {
  if (key === "risk_score") return row.risk?.risk_score || 0;
  if (key === "last_activity") return row.risk?.days_since_last_usage || 0;
  return row[key] || "";
}

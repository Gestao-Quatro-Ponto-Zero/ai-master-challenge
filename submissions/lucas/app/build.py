"""
Gera app/index.html — app single-file (HTML+CSS+JS, sem build no lado do
avaliador, sem backend).

Por que embutir os dados em vez de fetch(): abrir um HTML via file:// e
chamar fetch()/XHR pra outro arquivo local e bloqueado por CORS no Chrome
(cada file:// e uma origem opaca). Pra garantir que o app rode tanto
clicando duas vezes quanto via `python -m http.server`, os dados de
scoring_reference.json + os deals abertos de pipeline_clean.csv (+ sector
de accounts.csv + manager/regiao de sales_teams.csv) sao embutidos como
JSON inline no HTML. O SCORE CONTINUA SENDO CALCULADO NO BROWSER, em JS,
a partir desses dados — so a etapa de "carregar arquivo" muda de fetch()
pra "já esta na pagina".

Rode este script de novo se os dados em ../analysis ou ../data mudarem.
"""
import json
import pandas as pd

ANALYSIS = "../analysis"
DATA = "../data"

with open(f"{ANALYSIS}/scoring_reference.json", encoding="utf-8") as f:
    scoring_ref = json.load(f)

pipeline = pd.read_csv(f"{ANALYSIS}/pipeline_clean.csv", parse_dates=["engage_date", "close_date"])
accounts = pd.read_csv(f"{DATA}/accounts.csv")
teams = pd.read_csv(f"{DATA}/sales_teams.csv")

REFERENCE_DATE = pd.concat([pipeline["engage_date"], pipeline["close_date"]]).max()

open_deals = pipeline[pipeline["deal_stage"].isin(["Prospecting", "Engaging"])].copy()
open_deals_records = []
for _, r in open_deals.iterrows():
    open_deals_records.append({
        "opportunity_id": r["opportunity_id"],
        "sales_agent": r["sales_agent"] if pd.notna(r["sales_agent"]) else None,
        "product": r["product"],
        "account": r["account"] if pd.notna(r["account"]) else None,
        "deal_stage": r["deal_stage"],
        "engage_date": r["engage_date"].strftime("%Y-%m-%d") if pd.notna(r["engage_date"]) else None,
    })

account_sector = {
    row["account"]: row["sector"]
    for _, row in accounts.iterrows()
    if pd.notna(row["account"])
}

sales_teams_map = {
    row["sales_agent"]: {"manager": row["manager"], "regional_office": row["regional_office"]}
    for _, row in teams.iterrows()
}

def js_json(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</script>", "<\\/script>")

n_open = len(open_deals_records)
ref_date_iso = str(REFERENCE_DATE.date())
ref_date_br = REFERENCE_DATE.strftime("%d/%m/%Y")

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lead Scorer — Painel do Vendedor</title>
<style>
  :root {
    --green-bg: #e6f4ea; --green-fg: #1e7e34; --green-border: #b7e1c3;
    --orange-bg: #fdf0e0; --orange-fg: #a15c00; --orange-border: #f3d5a8;
    --gray-bg: #f3f4f6; --gray-fg: #52525b; --gray-border: #dcdfe3;
    --red-bg: #fdecea; --red-fg: #b3261e; --red-border: #f6c6c0;
    --ink: #1f2430; --muted: #6b7280; --line: #e3e5e8; --bg: #fafafa; --card: #ffffff;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 0 16px 48px; background: var(--bg); color: var(--ink);
    font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  }
  .wrap { max-width: 1080px; margin: 0 auto; }
  header { padding: 28px 0 8px; }
  h1 { font-size: 22px; margin: 0 0 4px; }
  .subtitle { color: var(--muted); font-size: 13.5px; margin: 0; }
  section { margin-top: 20px; }
  .card { background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 16px; }

  .filters { display: flex; flex-wrap: wrap; gap: 10px; align-items: flex-end; }
  .filters label { display: flex; flex-direction: column; font-size: 12px; color: var(--muted); gap: 4px; }
  .filters select {
    font-size: 13.5px; padding: 6px 8px; border-radius: 6px; border: 1px solid var(--line);
    background: #fff; min-width: 150px;
  }
  .filters button {
    font-size: 13px; padding: 7px 12px; border-radius: 6px; border: 1px solid var(--line);
    background: #fff; cursor: pointer; color: var(--muted);
  }
  .filters button:hover { background: var(--gray-bg); }

  .summary { font-size: 13.5px; color: var(--muted); }
  .summary b { color: var(--ink); }

  .matrix-axis-label { font-size: 11.5px; color: var(--muted); text-align: center; }
  .matrix-grid {
    display: grid; grid-template-columns: 92px 1fr 1fr; grid-template-rows: auto 1fr 1fr;
    gap: 8px; align-items: stretch;
  }
  .matrix-corner {}
  .matrix-rowlabel {
    display: flex; align-items: center; justify-content: center; writing-mode: vertical-rl;
    transform: rotate(180deg); font-size: 11.5px; color: var(--muted); text-align: center;
  }
  .quadrant {
    border-radius: 10px; border: 1.5px solid; padding: 14px; text-align: left; cursor: pointer;
    font-family: inherit; min-height: 96px; transition: filter .12s ease;
  }
  .quadrant:hover { filter: brightness(0.97); }
  .quadrant.selected { outline: 2.5px solid var(--ink); outline-offset: 2px; }
  .quadrant .qtitle { font-size: 14.5px; font-weight: 600; margin-bottom: 6px; }
  .quadrant .qmeta { font-size: 12.5px; opacity: .85; }
  .q-trabalhar { background: var(--green-bg); border-color: var(--green-border); color: var(--green-fg); }
  .q-resgatar { background: var(--orange-bg); border-color: var(--orange-border); color: var(--orange-fg); }
  .q-radar { background: var(--gray-bg); border-color: var(--gray-border); color: var(--gray-fg); }
  .q-despriorizar { background: var(--red-bg); border-color: var(--red-border); color: var(--red-fg); }
  .matrix-caption { font-size: 11.5px; color: var(--muted); margin-top: 10px; }

  .deal-list h2 { font-size: 15px; margin: 0 0 10px; }
  .deal-row { border: 1px solid var(--line); border-radius: 8px; margin-bottom: 8px; background: #fff; }
  .deal-row summary {
    list-style: none; cursor: pointer; padding: 10px 12px; display: flex; gap: 14px;
    align-items: center; flex-wrap: wrap; font-size: 13px;
  }
  .deal-row summary::-webkit-details-marker { display: none; }
  .deal-row summary:before { content: "▸"; color: var(--muted); font-size: 11px; margin-right: 2px; }
  .deal-row[open] summary:before { content: "▾"; }
  .dr-id { font-family: ui-monospace, monospace; color: var(--muted); font-size: 11.5px; min-width: 78px; }
  .dr-product { font-weight: 600; min-width: 120px; }
  .dr-account { color: var(--muted); min-width: 150px; }
  .dr-stage { font-size: 11.5px; padding: 2px 7px; border-radius: 999px; background: var(--gray-bg); color: var(--gray-fg); }
  .dr-ev { margin-left: auto; font-weight: 700; }
  .dr-days { color: var(--muted); font-size: 12px; }
  .conf { font-size: 11px; padding: 2px 7px; border-radius: 999px; border: 1px solid; }
  .conf-alta { color: #1e7e34; border-color: #b7e1c3; }
  .conf-media { color: #a15c00; border-color: #f3d5a8; }
  .conf-baixa { color: #b3261e; border-color: #f6c6c0; }
  .drivers { padding: 2px 12px 12px 34px; font-size: 12.5px; color: #3a3f47; }
  .drivers ul { margin: 4px 0 0; padding-left: 18px; }
  .drivers li { margin-bottom: 3px; }
  .empty-state { color: var(--muted); font-size: 13px; padding: 20px 0; text-align: center; }

  .honesty { margin-top: 28px; background: #fff8ec; border: 1px solid #f0dfb8; border-radius: 10px; padding: 18px 20px; }
  .honesty h2 { font-size: 14.5px; margin: 0 0 8px; }
  .honesty ul { margin: 0; padding-left: 18px; font-size: 13px; line-height: 1.6; color: #3a3f47; }
  .honesty li { margin-bottom: 4px; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Lead Scorer — Painel do Vendedor</h1>
    <p class="subtitle">Pipeline referente a __REF_DATE_BR__ · __N_OPEN__ deals abertos · organizador de ação, não previsão</p>
  </header>

  <section class="card filters">
    <label>Vendedor
      <select id="f-agent"><option value="">Todos</option></select>
    </label>
    <label>Manager
      <select id="f-manager"><option value="">Todos</option></select>
    </label>
    <label>Região
      <select id="f-region"><option value="">Todas</option></select>
    </label>
    <label>Produto
      <select id="f-product"><option value="">Todos</option></select>
    </label>
    <button id="f-clear">Limpar filtros</button>
  </section>

  <section class="summary" id="summary"></section>

  <section class="card">
    <div class="matrix-grid" id="matrix"></div>
    <p class="matrix-caption">
      Alto/baixo valor = acima/abaixo da mediana de EV de todos os __N_OPEN__ deals abertos da empresa (fixo, não muda com o filtro).
      Esfriando = entre os 25% mais velhos (dias desde o engajamento) entre os deals abertos <em>do mesmo produto</em>, considerando toda a empresa.
      Deals em Prospecting nunca são flagados como esfriando (ainda não têm data de engajamento).
    </p>
  </section>

  <section class="deal-list card" id="deal-list-section">
    <h2 id="deal-list-title">Deals</h2>
    <div id="deal-list"></div>
  </section>

  <div class="honesty">
    <h2>Como ler este score</h2>
    <ul>
      <li><b>Isto não prevê quem vai fechar.</b> Testamos (backtest com validação cruzada, sem vazamento de dado): a probabilidade de fechar por produto/setor tem AUC 0,485 — não discrimina melhor que sorte. Não escondemos isso.</li>
      <li><b>O que o score faz de verdade:</b> organiza o pipeline por valor em jogo (Valor Esperado = probabilidade histórica × valor do produto) e sinaliza deals que estão parados há mais tempo que o normal para o produto deles ("esfriando").</li>
      <li><b>"Confiança baixa"</b> = a estimativa está apoiada em pouco dado histórico (produto raro, poucas vendas fechadas) e/ou o deal não tem conta identificada no CRM — não é sobre o deal em si, é sobre o quão sólida é a conta que estamos fazendo.</li>
      <li><b>Use os drivers</b> (clique num deal pra expandir) pra entender o "porquê" de cada número — sem isso o score é só mais um número na tela.</li>
    </ul>
  </div>
</div>

<script>
const REF = __SCORING_REF_JSON__;
const OPEN_DEALS_RAW = __OPEN_DEALS_JSON__;
const ACCOUNT_SECTOR = __ACCOUNT_SECTOR_JSON__;
const SALES_TEAMS = __SALES_TEAMS_JSON__;
const REFERENCE_DATE = "__REF_DATE_ISO__";

function daysSince(dateStr) {
  if (!dateStr) return null;
  const d = new Date(dateStr + "T00:00:00");
  const ref = new Date(REFERENCE_DATE + "T00:00:00");
  return Math.round((ref - d) / 86400000);
}

function percentile(values, p) {
  const arr = [...values].sort((a, b) => a - b);
  if (arr.length === 0) return Infinity;
  const idx = (p / 100) * (arr.length - 1);
  const lo = Math.floor(idx), hi = Math.ceil(idx);
  if (lo === hi) return arr[lo];
  return arr[lo] + (arr[hi] - arr[lo]) * (idx - lo);
}

function scoreDeal(raw) {
  const prodRef = REF.product_win_rate[raw.product];
  const pBase = prodRef.shrunk;
  const drivers = [];
  drivers.push(`Produto '${raw.product}' fecha historicamente ${(prodRef.shrunk * 100).toFixed(0)}% das vezes (base: ${prodRef.n} deals fechados)`);

  const sector = raw.account ? (ACCOUNT_SECTOR[raw.account] || null) : null;
  let pAdj = pBase;
  if (sector && REF.sector_win_rate[sector]) {
    const secRef = REF.sector_win_rate[sector];
    const effect = secRef.shrunk - REF.meta.global_win_rate;
    pAdj = pBase + effect;
    const sign = effect >= 0 ? "+" : "";
    drivers.push(`Setor '${sector}' ${sign}${(effect * 100).toFixed(1)}pp vs. média global (base: ${secRef.n} deals)`);
  } else {
    drivers.push("Conta não identificada no CRM — sem ajuste de setor");
  }

  const mult = REF.stage_multiplier[raw.deal_stage];
  const pFinal = Math.min(Math.max(pAdj * mult, 0.01), 0.99);
  drivers.push(`Estágio '${raw.deal_stage}': multiplicador heurístico x${mult} (não é medido no histórico — é suposição)`);

  const valorPotencial = REF.product_sales_price[raw.product];
  const ev = pFinal * valorPotencial;
  const daysOpen = daysSince(raw.engage_date);

  let confidence = prodRef.n >= 100 ? "alta" : (prodRef.n >= 30 ? "media" : "baixa");
  if (!sector) confidence = confidence === "alta" ? "media" : "baixa";

  const team = SALES_TEAMS[raw.sales_agent] || { manager: null, regional_office: null };

  return {
    ...raw,
    sector,
    manager: team.manager,
    regional_office: team.regional_office,
    p_fechar: pFinal,
    valor_potencial: valorPotencial,
    ev,
    days_open: daysOpen,
    confidence,
    drivers,
  };
}

const DEALS = OPEN_DEALS_RAW.map(scoreDeal);

// esfriando: relativo, top 25% mais velhos entre ABERTOS do MESMO PRODUTO (empresa toda)
const agesByProduct = {};
DEALS.forEach((d) => {
  if (d.deal_stage === "Engaging" && d.days_open != null) {
    (agesByProduct[d.product] = agesByProduct[d.product] || []).push(d.days_open);
  }
});
const coolingThreshold = {};
for (const [product, ages] of Object.entries(agesByProduct)) {
  coolingThreshold[product] = percentile(ages, 75);
}
DEALS.forEach((d) => {
  d.esfriando = d.deal_stage === "Engaging" && d.days_open != null && d.days_open >= coolingThreshold[d.product];
});

// alto/baixo valor: mediana global de EV, fixa (nao muda com filtro)
const medianEV = percentile(DEALS.map((d) => d.ev), 50);

function quadrantOf(d) {
  const alto = d.ev >= medianEV;
  if (alto && !d.esfriando) return "trabalhar";
  if (alto && d.esfriando) return "resgatar";
  if (!alto && !d.esfriando) return "radar";
  return "despriorizar";
}
DEALS.forEach((d) => { d.quadrant = quadrantOf(d); });

const QUADRANTS = [
  { key: "trabalhar", cls: "q-trabalhar", emoji: "🟢", title: "Trabalhar agora", desc: "alto valor, dentro do ciclo" },
  { key: "resgatar", cls: "q-resgatar", emoji: "🟠", title: "Resgatar ou soltar", desc: "alto valor, esfriando" },
  { key: "radar", cls: "q-radar", emoji: "⚪", title: "Manter no radar", desc: "baixo valor, dentro do ciclo" },
  { key: "despriorizar", cls: "q-despriorizar", emoji: "🔴", title: "Despriorizar", desc: "baixo valor, esfriando" },
];

let selectedQuadrant = "trabalhar";
const filters = { agent: "", manager: "", region: "", product: "" };

function fmtMoney(v) {
  return "$" + Math.round(v).toLocaleString("pt-BR");
}

function uniqueSorted(arr) {
  return [...new Set(arr.filter((x) => x != null && x !== ""))].sort((a, b) => a.localeCompare(b, "pt-BR"));
}

function populateSelect(id, values) {
  const sel = document.getElementById(id);
  values.forEach((v) => {
    const opt = document.createElement("option");
    opt.value = v; opt.textContent = v;
    sel.appendChild(opt);
  });
}

populateSelect("f-agent", uniqueSorted(Object.keys(SALES_TEAMS)));
populateSelect("f-manager", uniqueSorted(Object.values(SALES_TEAMS).map((t) => t.manager)));
populateSelect("f-region", uniqueSorted(Object.values(SALES_TEAMS).map((t) => t.regional_office)));
populateSelect("f-product", uniqueSorted(Object.keys(REF.product_sales_price)));

function filteredDeals() {
  return DEALS.filter((d) =>
    (!filters.agent || d.sales_agent === filters.agent) &&
    (!filters.manager || d.manager === filters.manager) &&
    (!filters.region || d.regional_office === filters.region) &&
    (!filters.product || d.product === filters.product)
  );
}

function renderMatrix(deals) {
  const matrixEl = document.getElementById("matrix");
  const byQ = { trabalhar: [], resgatar: [], radar: [], despriorizar: [] };
  deals.forEach((d) => byQ[d.quadrant].push(d));

  const sumEv = (arr) => arr.reduce((s, d) => s + d.ev, 0);

  matrixEl.innerHTML = `
    <div class="matrix-corner"></div>
    <div class="matrix-axis-label">Dentro do ciclo</div>
    <div class="matrix-axis-label">Esfriando</div>
    <div class="matrix-rowlabel">Alto valor</div>
    ${quadBtn("trabalhar", byQ)}
    ${quadBtn("resgatar", byQ)}
    <div class="matrix-rowlabel">Baixo valor</div>
    ${quadBtn("radar", byQ)}
    ${quadBtn("despriorizar", byQ)}
  `;

  function quadBtn(key, byQ) {
    const q = QUADRANTS.find((x) => x.key === key);
    const arr = byQ[key];
    const sel = selectedQuadrant === key ? " selected" : "";
    return `<button class="quadrant ${q.cls}${sel}" data-q="${key}">
      <div class="qtitle">${q.emoji} ${q.title}</div>
      <div class="qmeta">${arr.length} deal${arr.length === 1 ? "" : "s"} · ${fmtMoney(sumEv(arr))} em EV</div>
    </button>`;
  }

  matrixEl.querySelectorAll(".quadrant").forEach((btn) => {
    btn.addEventListener("click", () => {
      selectedQuadrant = btn.dataset.q;
      render();
    });
  });
}

function renderDealList(deals) {
  const q = QUADRANTS.find((x) => x.key === selectedQuadrant);
  document.getElementById("deal-list-title").textContent = `${q.emoji} ${q.title} (${q.desc})`;
  const listEl = document.getElementById("deal-list");
  const items = deals.filter((d) => d.quadrant === selectedQuadrant).sort((a, b) => b.ev - a.ev);

  if (items.length === 0) {
    listEl.innerHTML = `<div class="empty-state">Nenhum deal neste quadrante com os filtros atuais.</div>`;
    return;
  }

  listEl.innerHTML = items.map((d) => `
    <details class="deal-row">
      <summary>
        <span class="dr-id">${d.opportunity_id}</span>
        <span class="dr-product">${d.product}</span>
        <span class="dr-account">${d.account || "conta não identificada"}</span>
        <span class="dr-stage">${d.deal_stage}</span>
        <span class="dr-days">${d.days_open != null ? d.days_open + "d aberto" : "não engajado"}</span>
        <span class="conf conf-${d.confidence}">confiança ${d.confidence}</span>
        <span class="dr-ev">${fmtMoney(d.ev)}</span>
      </summary>
      <div class="drivers">
        <div>Vendedor: ${d.sales_agent || "—"} · Manager: ${d.manager || "—"} · Região: ${d.regional_office || "—"} · Valor potencial: ${fmtMoney(d.valor_potencial)} · P(fechar): ${(d.p_fechar * 100).toFixed(0)}%</div>
        <ul>${d.drivers.map((x) => `<li>${x}</li>`).join("")}</ul>
      </div>
    </details>
  `).join("");
}

function renderSummary(deals) {
  const total = deals.reduce((s, d) => s + d.ev, 0);
  document.getElementById("summary").innerHTML =
    `<b>${deals.length}</b> deals abertos no filtro atual · <b>${fmtMoney(total)}</b> em EV total`;
}

function render() {
  const deals = filteredDeals();
  renderSummary(deals);
  renderMatrix(deals);
  renderDealList(deals);
}

["agent", "manager", "region", "product"].forEach((key) => {
  document.getElementById("f-" + key).addEventListener("change", (e) => {
    filters[key] = e.target.value;
    render();
  });
});
document.getElementById("f-clear").addEventListener("click", () => {
  filters.agent = filters.manager = filters.region = filters.product = "";
  ["agent", "manager", "region", "product"].forEach((key) => { document.getElementById("f-" + key).value = ""; });
  render();
});

render();
</script>
</body>
</html>
"""

html = (
    HTML_TEMPLATE
    .replace("__SCORING_REF_JSON__", js_json(scoring_ref))
    .replace("__OPEN_DEALS_JSON__", js_json(open_deals_records))
    .replace("__ACCOUNT_SECTOR_JSON__", js_json(account_sector))
    .replace("__SALES_TEAMS_JSON__", js_json(sales_teams_map))
    .replace("__REF_DATE_ISO__", ref_date_iso)
    .replace("__REF_DATE_BR__", ref_date_br)
    .replace("__N_OPEN__", str(n_open))
)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"OK -> app/index.html gerado ({len(html):,} bytes, {n_open} deals abertos embutidos)")

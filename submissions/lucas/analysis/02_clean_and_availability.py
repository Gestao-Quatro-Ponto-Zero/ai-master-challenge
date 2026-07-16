"""
Passo 2 (versionado, roda sobre os CSVs originais sem sobrescreve-los):
  1. Normaliza o mismatch de produto 'GTXPro' -> 'GTX Pro' e revalida
     que 100% dos registros de sales_pipeline casam com products.csv.
     Gera ./pipeline_clean.csv como artefato derivado (dado bruto em
     ../data/ permanece intocado).
  2. Quantifica disponibilidade de features SOMENTE nos deals abertos
     (Prospecting + Engaging) -- o que da pra usar de verdade no
     scoring de um deal que ainda nao fechou.
Nao propoe pesos de scoring. Saida: ./02_availability_summary.md
"""
import pandas as pd

DATA = "../data"
OUT_MD = "02_availability_summary.md"
OUT_CLEAN = "pipeline_clean.csv"

accounts = pd.read_csv(f"{DATA}/accounts.csv")
products = pd.read_csv(f"{DATA}/products.csv")
teams = pd.read_csv(f"{DATA}/sales_teams.csv")
pipeline = pd.read_csv(f"{DATA}/sales_pipeline.csv", parse_dates=["engage_date", "close_date"])

lines = []
def w(s=""):
    lines.append(s)

w("# Passo 2 — Normalizacao de produto + Disponibilidade de features (deals abertos)\n")

# ------------------------------------------------------------------
# 1. Normalizacao do mismatch de produto
# ------------------------------------------------------------------
w("## 1. Normalizacao do mismatch de produto")

PRODUCT_NAME_MAP = {
    "GTXPro": "GTX Pro",
}

before_mismatch = set(pipeline["product"].dropna().unique()) - set(products["product"].dropna().unique())
w(f"- Mismatches ANTES da normalizacao: {sorted(before_mismatch)}")

pipeline_clean = pipeline.copy()
pipeline_clean["product"] = pipeline_clean["product"].replace(PRODUCT_NAME_MAP)

after_mismatch = set(pipeline_clean["product"].dropna().unique()) - set(products["product"].dropna().unique())
w(f"- Mapeamento aplicado: {PRODUCT_NAME_MAP}")
w(f"- Mismatches DEPOIS da normalizacao: {sorted(after_mismatch)}")

n_total = len(pipeline_clean)
n_matched = pipeline_clean["product"].isin(products["product"]).sum()
w(f"- Join por produto: {n_matched}/{n_total} registros casam com products.csv ({n_matched/n_total:.2%})")
assert n_matched == n_total, "Join por produto ainda incompleto apos normalizacao!"
w("- **Validado: 100% dos registros de sales_pipeline casam com products.csv apos a normalizacao.**")
w()
w(f"- CSV original (`../data/sales_pipeline.csv`) NAO foi alterado.")
w(f"- Versao normalizada salva em `./{OUT_CLEAN}` (mesmas colunas, so `product` corrigido) para uso nos proximos passos.")
w()

pipeline_clean.to_csv(OUT_CLEAN, index=False)

# ------------------------------------------------------------------
# 2. Disponibilidade de features nos deals ABERTOS
# ------------------------------------------------------------------
w("## 2. Disponibilidade de features — deals ABERTOS (Prospecting + Engaging)")

open_deals = pipeline_clean[pipeline_clean["deal_stage"].isin(["Prospecting", "Engaging"])].copy()
open_deals = open_deals.merge(accounts, on="account", how="left", suffixes=("", "_acc"))

n_open = len(open_deals)
w(f"- Total de deals abertos: {n_open} (Prospecting={int((open_deals.deal_stage=='Prospecting').sum())}, "
  f"Engaging={int((open_deals.deal_stage=='Engaging').sum())})\n")

def avail(col, df=open_deals):
    n = df[col].notna().sum()
    return n, n / len(df)

candidate_cols = {
    "sales_agent (pipeline)": "sales_agent",
    "product (pipeline, normalizado)": "product",
    "account (pipeline, chave)": "account",
    "engage_date (pipeline)": "engage_date",
    "sector (via account)": "sector",
    "revenue (via account)": "revenue",
    "employees (via account)": "employees",
    "office_location (via account)": "office_location",
    "year_established (via account)": "year_established",
    "subsidiary_of (via account)": "subsidiary_of",
}

w("### Disponibilidade geral (Prospecting + Engaging juntos)")
w("| Feature | Disponivel | % |")
w("|---|---|---|")
avail_summary = {}
for label, col in candidate_cols.items():
    n, pct = avail(col)
    avail_summary[label] = pct
    w(f"| {label} | {n}/{n_open} | {pct:.1%} |")
w()

w("### Disponibilidade por estagio (Prospecting vs Engaging)")
w("| Feature | Prospecting % | Engaging % |")
w("|---|---|---|")
for label, col in candidate_cols.items():
    prosp = open_deals[open_deals.deal_stage == "Prospecting"]
    engag = open_deals[open_deals.deal_stage == "Engaging"]
    p_pct = prosp[col].notna().mean() if len(prosp) else float("nan")
    e_pct = engag[col].notna().mean() if len(engag) else float("nan")
    w(f"| {label} | {p_pct:.1%} | {e_pct:.1%} |")
w()

# Combinacao: account presente E dados de conta presentes (deveriam ser identicos se join account for 1:1 limpo)
has_account = open_deals["account"].notna()
has_sector = open_deals["sector"].notna()
w("### Checagem: account presente implica sempre dados de conta completos?")
w(f"- account presente: {has_account.sum()} | sector presente: {has_sector.sum()} | "
  f"iguais: {(has_account.sum() == has_sector.sum())}")
w()

w("## Conclusao — o que da pra usar de verdade num deal aberto")
w("- **Sempre disponivel (100%)**: sales_agent, product (normalizado), deal_stage.")
w(f"- **account e features derivadas de conta (sector/revenue/employees/...)**: disponivel em "
  f"{avail_summary['account (pipeline, chave)']:.1%} dos deals abertos — precisa de fallback nos "
  f"{n_open - int(open_deals['account'].notna().sum())} deals sem conta.")
w(f"- **engage_date**: disponivel em {avail_summary['engage_date (pipeline)']:.1%} dos deals abertos — "
  f"falta em 100% dos Prospecting (por definicao, ainda nao engajou) e presente em 100% dos Engaging.")
w("- Nao propus pesos ainda — so mapeamento do que existe pra decidir depois com que fallback tratar "
  "cada gap (account ausente, engage_date ausente em Prospecting).")

with open(OUT_MD, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"OK -> escrito {OUT_MD} e {OUT_CLEAN} ({len(lines)} linhas no resumo)")

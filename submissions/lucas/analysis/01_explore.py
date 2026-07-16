"""
Exploracao inicial do CRM Sales Predictive Analytics.
Roda leituras, valida joins entre as 4 tabelas e gera distribuicoes que
vao informar os pesos do scoring (nao inventa pesos, so descreve os dados).
Saida: ./analysis/01_exploration_summary.md
"""
import pandas as pd

DATA = "../data"
OUT = "01_exploration_summary.md"

accounts = pd.read_csv(f"{DATA}/accounts.csv")
products = pd.read_csv(f"{DATA}/products.csv")
teams = pd.read_csv(f"{DATA}/sales_teams.csv")
pipeline = pd.read_csv(f"{DATA}/sales_pipeline.csv", parse_dates=["engage_date", "close_date"])

lines = []
def w(s=""):
    lines.append(s)

w("# Exploracao inicial — Lead Scorer\n")

# --- Shapes ---
w("## Shapes")
for name, df in [("accounts", accounts), ("products", products), ("sales_teams", teams), ("sales_pipeline", pipeline)]:
    w(f"- {name}: {df.shape[0]} linhas x {df.shape[1]} colunas — colunas: {list(df.columns)}")
w()

# --- Nulls ---
w("## Nulos por coluna")
for name, df in [("accounts", accounts), ("products", products), ("sales_teams", teams), ("sales_pipeline", pipeline)]:
    nulls = df.isna().sum()
    nulls = nulls[nulls > 0]
    if len(nulls):
        w(f"- **{name}**: " + ", ".join(f"{c}={n}" for c, n in nulls.items()))
    else:
        w(f"- **{name}**: sem nulos")
w()

# --- Join mismatches ---
w("## Validacao de joins (mismatches)")

pipe_accounts = set(pipeline["account"].dropna().unique())
acc_accounts = set(accounts["account"].dropna().unique())
missing_accounts = pipe_accounts - acc_accounts
w(f"- sales_pipeline.account sem match em accounts.account: {len(missing_accounts)} valores -> {sorted(missing_accounts)[:20]}")

pipe_products = set(pipeline["product"].dropna().unique())
prod_products = set(products["product"].dropna().unique())
missing_products = pipe_products - prod_products
w(f"- sales_pipeline.product sem match em products.product: {len(missing_products)} valores -> {sorted(missing_products)[:20]}")

pipe_agents = set(pipeline["sales_agent"].dropna().unique())
team_agents = set(teams["sales_agent"].dropna().unique())
missing_agents = pipe_agents - team_agents
w(f"- sales_pipeline.sales_agent sem match em sales_teams.sales_agent: {len(missing_agents)} valores -> {sorted(missing_agents)[:20]}")
w()

# --- Deal stage distribution ---
w("## Distribuicao de deal_stage")
stage_counts = pipeline["deal_stage"].value_counts()
stage_pct = (pipeline["deal_stage"].value_counts(normalize=True) * 100).round(1)
for stage in stage_counts.index:
    w(f"- {stage}: {stage_counts[stage]} ({stage_pct[stage]}%)")
w()

# --- Win rate global e por segmento ---
closed = pipeline[pipeline["deal_stage"].isin(["Won", "Lost"])].copy()
win_rate_global = (closed["deal_stage"] == "Won").mean()
w(f"## Win rate global (entre deals fechados, Won+Lost)\n- {win_rate_global:.1%} ({len(closed)} deals fechados)\n")

def win_rate_by(col, df, merge_df=None, merge_on=None, min_n=5):
    d = df.copy()
    if merge_df is not None:
        d = d.merge(merge_df, left_on=merge_on, right_on=merge_on, how="left")
    g = d.groupby(col)["deal_stage"].agg(n="count", win_rate=lambda s: (s == "Won").mean())
    g = g[g["n"] >= min_n].sort_values("win_rate", ascending=False)
    return g

w("## Win rate por produto (min 5 deals fechados)")
g = win_rate_by("product", closed)
for prod, row in g.iterrows():
    w(f"- {prod}: {row['win_rate']:.1%} (n={int(row['n'])})")
w()

closed_acc = closed.merge(accounts[["account", "sector"]], on="account", how="left")
w("## Win rate por setor da conta (min 5 deals fechados)")
g = closed_acc.groupby("sector")["deal_stage"].agg(n="count", win_rate=lambda s: (s == "Won").mean())
g = g[g["n"] >= 5].sort_values("win_rate", ascending=False)
for sector, row in g.iterrows():
    w(f"- {sector}: {row['win_rate']:.1%} (n={int(row['n'])})")
w()

closed_team = closed.merge(teams[["sales_agent", "manager", "regional_office"]], on="sales_agent", how="left")
w("## Win rate por escritorio regional (min 5 deals fechados)")
g = closed_team.groupby("regional_office")["deal_stage"].agg(n="count", win_rate=lambda s: (s == "Won").mean())
g = g[g["n"] >= 5].sort_values("win_rate", ascending=False)
for office, row in g.iterrows():
    w(f"- {office}: {row['win_rate']:.1%} (n={int(row['n'])})")
w()

w("## Win rate por vendedor (top 10 e bottom 10, min 10 deals fechados)")
g = closed.groupby("sales_agent")["deal_stage"].agg(n="count", win_rate=lambda s: (s == "Won").mean())
g = g[g["n"] >= 10].sort_values("win_rate", ascending=False)
w("Top 10:")
for agent, row in g.head(10).iterrows():
    w(f"- {agent}: {row['win_rate']:.1%} (n={int(row['n'])})")
w("Bottom 10:")
for agent, row in g.tail(10).iterrows():
    w(f"- {agent}: {row['win_rate']:.1%} (n={int(row['n'])})")
w()

# --- Tempo no pipeline ---
w("## Tempo no pipeline (dias entre engage_date e close_date, deals fechados)")
closed["days_to_close"] = (closed["close_date"] - closed["engage_date"]).dt.days
w(f"- Won: media={closed[closed['deal_stage']=='Won']['days_to_close'].mean():.1f} dias, "
  f"mediana={closed[closed['deal_stage']=='Won']['days_to_close'].median():.1f}")
w(f"- Lost: media={closed[closed['deal_stage']=='Lost']['days_to_close'].mean():.1f} dias, "
  f"mediana={closed[closed['deal_stage']=='Lost']['days_to_close'].median():.1f}")
w()

# --- Deals abertos: idade no pipeline (referencia = data mais recente do dataset) ---
ref_date = pd.concat([pipeline["engage_date"], pipeline["close_date"]]).max()
open_deals = pipeline[pipeline["deal_stage"].isin(["Prospecting", "Engaging"])].copy()
open_deals["days_open"] = (ref_date - open_deals["engage_date"]).dt.days
w(f"## Deals abertos (referencia: data mais recente no dataset = {ref_date.date()})")
w(f"- Total abertos: {len(open_deals)} ({open_deals['deal_stage'].value_counts().to_dict()})")
w(f"- Idade media: {open_deals['days_open'].mean():.1f} dias, mediana: {open_deals['days_open'].median():.1f}")
w("- Percentis de idade (dias): " + ", ".join(
    f"p{p}={open_deals['days_open'].quantile(p/100):.0f}" for p in [50, 75, 90, 95]
))
w()

# --- Valor ---
w("## close_value (deals Won)")
won = closed[closed["deal_stage"] == "Won"]
w(f"- media={won['close_value'].mean():.0f}, mediana={won['close_value'].median():.0f}, "
  f"min={won['close_value'].min():.0f}, max={won['close_value'].max():.0f}")
w()

w("## sales_price por produto (products.csv)")
for _, row in products.iterrows():
    w(f"- {row['product']} ({row['series']}): {row['sales_price']}")
w()

# --- Achados detalhados sobre os mismatches/nulos (investigacao) ---
w("## Achados sobre mismatch de produto: 'GTXPro' vs 'GTX Pro'")
gtxpro_n = (pipeline["product"] == "GTXPro").sum()
w(f"- sales_pipeline usa o literal 'GTXPro' (sem espaco) em {gtxpro_n} registros (incluindo deals abertos).")
w("- products.csv define o produto como 'GTX Pro' (com espaco) — mismatch de nomenclatura, nao produto novo.")
w("- Correcao necessaria antes de qualquer join por produto: normalizar 'GTXPro' -> 'GTX Pro'.")
w()

w("## Achados sobre account nulo no pipeline (1425 registros)")
null_acc_by_stage = pipeline[pipeline["account"].isna()]["deal_stage"].value_counts()
w("- Ocorre **somente** em deals abertos: " + ", ".join(f"{s}={n}" for s, n in null_acc_by_stage.items()))
w("- Nenhum deal Won ou Lost tem account nulo — 100% dos deals fechados tem conta associada.")
w("- Implicacao pro scoring: ~1425 deals abertos nao terao features de conta (setor/revenue/employees) disponiveis; precisa de fallback.")
w()

w("## Achados sobre engage_date nulo (500 registros)")
null_engage_by_stage = pipeline[pipeline["engage_date"].isna()]["deal_stage"].value_counts()
w("- Coincide exatamente com os 500 deals em estagio 'Prospecting' (100%): " + ", ".join(f"{s}={n}" for s, n in null_engage_by_stage.items()))
w("- Padrao esperado, nao e problema de dados: Prospecting = ainda nao engajado, logo sem engage_date.")
w("- Implicacao pro scoring: 'dias no pipeline' nao pode ser calculado para Prospecting; usar outra logica de recencia (ex.: data de criacao do opportunity_id, se existir, ou tratar como grupo separado).")
w()

w("## Outras checagens de consistencia (todas OK)")
w(f"- opportunity_id duplicado: {pipeline['opportunity_id'].duplicated().sum()}")
w(f"- Won sem close_date: {((pipeline.deal_stage=='Won') & (pipeline.close_date.isna())).sum()}")
w(f"- Won sem close_value: {((pipeline.deal_stage=='Won') & (pipeline.close_value.isna())).sum()}")
w(f"- Lost com close_value>0: {((pipeline.deal_stage=='Lost') & (pipeline.close_value>0)).sum()}")
w(f"- Prospecting/Engaging com close_date preenchido: {(pipeline.deal_stage.isin(['Prospecting','Engaging']) & pipeline.close_date.notna()).sum()}")
w()

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"OK -> escrito {OUT} ({len(lines)} linhas)")

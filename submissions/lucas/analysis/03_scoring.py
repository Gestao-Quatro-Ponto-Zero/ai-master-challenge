"""
Fase 3 — Motor de scoring (so a logica / tabelas de referencia, sem app).

P(fechar) = EMPIRICO (win rate historico) x multiplicador de estagio (HEURISTICO).
Valor Esperado (EV) = P(fechar) x valor potencial (products.sales_price).
Flag "esfriando" = tempo aberto acima do p75 do ciclo de deals VENCEDORES do mesmo produto.

Usa pipeline_clean.csv (produto ja normalizado no passo 2), nao o CSV original.

Saidas:
  - scoring_reference.json  -> tabelas de referencia (o app vai consumir isso)
  - 03_scoring_summary.md   -> metodologia + validacao com amostra de deals scorados
"""
import json
import pandas as pd

DATA = "../data"
PIPELINE_CLEAN = "pipeline_clean.csv"
OUT_MD = "03_scoring_summary.md"
OUT_JSON = "scoring_reference.json"

# Limiar de shrinkage documentado no enunciado: segmentos com n < 30 regridem
# fortemente a media global. Usamos k=30 como pseudo-contagem: em n=k=30 o
# segmento pesa 50/50 entre taxa crua e media global; n>>30 -> taxa crua;
# n<<30 -> media global.
SHRINKAGE_K = 30

# HEURISTICA (nao empirica): deal_stage nao tem outcome historico associavel
# por linha (cada opportunity_id so tem o estagio final/atual, sem historico
# de transicao). Multiplicadores abaixo sao suposicoes de que um deal ja
# engajado tem probabilidade condicional maior de fechar do que um deal ainda
# em prospeccao. Precisam de validacao com o time comercial depois.
STAGE_MULTIPLIER = {
    "Prospecting": 0.85,   # HEURISTICA: reduz P(fechar) do produto/setor
    "Engaging": 1.15,      # HEURISTICA: aumenta P(fechar) do produto/setor
}

accounts = pd.read_csv(f"{DATA}/accounts.csv")
products = pd.read_csv(f"{DATA}/products.csv")
pipeline = pd.read_csv(PIPELINE_CLEAN, parse_dates=["engage_date", "close_date"])

lines = []
def w(s=""):
    lines.append(s)


def shrink(raw_rate, n, global_rate, k=SHRINKAGE_K):
    return (n * raw_rate + k * global_rate) / (n + k)


# ------------------------------------------------------------------
# 1. Win rate global (base para shrinkage e para o efeito de setor)
# ------------------------------------------------------------------
closed = pipeline[pipeline["deal_stage"].isin(["Won", "Lost"])].copy()
global_rate = (closed["deal_stage"] == "Won").mean()
global_n = len(closed)

# ------------------------------------------------------------------
# 2. Win rate EMPIRICO por produto (base do P(fechar)), com shrinkage
# ------------------------------------------------------------------
prod_stats = closed.groupby("product")["deal_stage"].agg(n="count", raw=lambda s: (s == "Won").mean())
prod_stats["shrunk"] = shrink(prod_stats["raw"], prod_stats["n"], global_rate)
product_win_rate = {
    p: {"n": int(r.n), "raw": round(float(r.raw), 4), "shrunk": round(float(r.shrunk), 4)}
    for p, r in prod_stats.iterrows()
}

# ------------------------------------------------------------------
# 3. Win rate EMPIRICO por setor da conta (ajuste/blend), com shrinkage
# ------------------------------------------------------------------
closed_acc = closed.merge(accounts[["account", "sector"]], on="account", how="left")
sector_stats = closed_acc.groupby("sector")["deal_stage"].agg(n="count", raw=lambda s: (s == "Won").mean())
sector_stats["shrunk"] = shrink(sector_stats["raw"], sector_stats["n"], global_rate)
sector_win_rate = {
    s: {"n": int(r.n), "raw": round(float(r.raw), 4), "shrunk": round(float(r.shrunk), 4)}
    for s, r in sector_stats.iterrows()
}

# ------------------------------------------------------------------
# 4. Limiar de "esfriando": p75 do ciclo (dias) dos deals WON, por produto
# ------------------------------------------------------------------
won = closed[closed["deal_stage"] == "Won"].copy()
won["days_to_close"] = (won["close_date"] - won["engage_date"]).dt.days
cooling_stats = won.groupby("product")["days_to_close"].agg(n_won="count", p75_days=lambda s: s.quantile(0.75))
product_cooling_threshold = {
    p: {"n_won": int(r.n_won), "p75_days": round(float(r.p75_days), 1)}
    for p, r in cooling_stats.iterrows()
}

REFERENCE_DATE = pd.concat([pipeline["engage_date"], pipeline["close_date"]]).max()

# ------------------------------------------------------------------
# 5. Valor potencial de deal aberto = products.sales_price (close_value
#    e desconhecido ate o deal fechar, entao nao pode ser usado como input).
# ------------------------------------------------------------------
product_sales_price = dict(zip(products["product"], products["sales_price"]))

# ------------------------------------------------------------------
# 6. Salva a tabela de referencia (o app vai consumir isso, sem reprocessar
#    as 8800 linhas do pipeline).
# ------------------------------------------------------------------
reference = {
    "meta": {
        "generated_from": PIPELINE_CLEAN,
        "reference_date": str(REFERENCE_DATE.date()),
        "global_win_rate": round(float(global_rate), 4),
        "global_n_closed": int(global_n),
        "shrinkage_k": SHRINKAGE_K,
        "shrinkage_formula": "shrunk = (n*raw + k*global) / (n+k)",
        "shrinkage_threshold_note": "segmentos com n<30 regridem fortemente a media global; em n=k=30 o peso e 50/50 entre taxa crua e media global",
        "valor_potencial_note": "para deals abertos, valor potencial = products.sales_price do produto (close_value e desconhecido ate o fechamento)",
        "cooling_note": "esfriando = dias desde engage_date > p75 do days_to_close de deals WON do mesmo produto; Prospecting nunca recebe a flag (sem engage_date)",
        "stage_multiplier_note": "HEURISTICO, nao derivado do historico (deal_stage nao tem outcome historico associado por linha, e um estado unico, nao uma serie temporal de transicoes)",
    },
    "product_win_rate": product_win_rate,
    "sector_win_rate": sector_win_rate,
    "stage_multiplier": STAGE_MULTIPLIER,
    "product_cooling_threshold_days": product_cooling_threshold,
    "product_sales_price": product_sales_price,
}
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(reference, f, ensure_ascii=False, indent=2)


# ------------------------------------------------------------------
# 7. Aplica a logica nos deals ABERTOS (Prospecting + Engaging) para
#    VALIDAR — nao e o app, e so a checagem de que a logica funciona.
# ------------------------------------------------------------------
account_sector = dict(zip(accounts["account"], accounts["sector"]))
open_deals = pipeline[pipeline["deal_stage"].isin(["Prospecting", "Engaging"])].copy()


def score_row(row):
    product = row["product"]
    stage = row["deal_stage"]
    prod_ref = product_win_rate[product]
    p_base = prod_ref["shrunk"]
    drivers = [f"Produto '{product}' fecha historicamente {prod_ref['shrunk']:.0%} (n={prod_ref['n']})"]

    sector = account_sector.get(row["account"]) if pd.notna(row["account"]) else None
    if sector is not None:
        sec_ref = sector_win_rate[sector]
        sector_effect = sec_ref["shrunk"] - global_rate
        p_adj = p_base + sector_effect
        sign = "+" if sector_effect >= 0 else ""
        drivers.append(f"Setor '{sector}' {sign}{sector_effect*100:.1f}pp vs. media global (n={sec_ref['n']})")
    else:
        p_adj = p_base
        drivers.append("Conta nao identificada no CRM — sem ajuste de setor")

    mult = STAGE_MULTIPLIER[stage]
    p_final = min(max(p_adj * mult, 0.01), 0.99)
    drivers.append(f"Estagio '{stage}': multiplicador heuristico x{mult} (nao empirico)")

    valor_potencial = product_sales_price[product]

    cooling = False
    if stage == "Engaging" and pd.notna(row["engage_date"]):
        days_open = (REFERENCE_DATE - row["engage_date"]).days
        p75 = product_cooling_threshold[product]["p75_days"]
        if days_open > p75:
            cooling = True
            drivers.append(f"{days_open} dias aberto — acima do típico de vitória do produto ({p75:.0f} dias, p75)")

    ev = p_final * valor_potencial
    return pd.Series({
        "p_fechar": round(p_final, 4),
        "valor_potencial": valor_potencial,
        "ev": round(ev, 2),
        "esfriando": cooling,
        "drivers": " | ".join(drivers),
    })


scored = open_deals.join(open_deals.apply(score_row, axis=1))

# ------------------------------------------------------------------
# 8. Resumo markdown — metodologia + validacao
# ------------------------------------------------------------------
w("# Fase 3 — Motor de scoring (logica + validacao)\n")

w("## Metodologia")
w(f"- **Win rate global** (base do shrinkage): {global_rate:.1%} (n={global_n})")
w(f"- **Shrinkage**: `shrunk = (n*raw + k*global) / (n+k)`, k={SHRINKAGE_K}. "
  f"Segmentos com n<{SHRINKAGE_K} regridem fortemente a media global; em n={SHRINKAGE_K} o peso e 50/50.")
w("- **P(fechar)** = win rate do PRODUTO (shrunk) + efeito aditivo do SETOR (shrunk - global, em pp), "
  "só quando o deal tem `account`; depois multiplicado pelo fator HEURISTICO de `deal_stage`. Resultado limitado a [1%, 99%].")
w("- **deal_stage NAO tem win rate empirico** — cada opportunity_id so registra o estagio final, sem historico "
  "de transicao, entao nao da pra medir 'taxa de fechamento condicional ao estagio' nos dados. O multiplicador "
  f"e uma HEURISTICA explicita: {STAGE_MULTIPLIER} (Engaging > Prospecting).")
w("- **Valor potencial** de deal aberto = `products.sales_price` do produto — `close_value` so existe apos o "
  "fechamento, entao nao pode ser usado como input do scoring de um deal aberto.")
w("- **EV = P(fechar) x valor potencial**.")
w("- **Esfriando** = dias desde `engage_date` > p75 do `days_to_close` dos deals **WON do mesmo produto**. "
  "Deals `Prospecting` nunca recebem a flag (nao tem `engage_date`).")
w()

w("## Tabela de referencia — win rate por PRODUTO (empirico, com shrinkage)")
w("| Produto | n | raw | shrunk | shrunk < raw? (regrediu p/ media) |")
w("|---|---|---|---|---|")
for p, r in prod_stats.sort_values("n").iterrows():
    flag = "sim" if r.n < SHRINKAGE_K else ("leve" if abs(r.shrunk - r.raw) > 0.01 else "nao")
    w(f"| {p} | {int(r.n)} | {r.raw:.1%} | {r.shrunk:.1%} | {flag} |")
w()

w("## Tabela de referencia — win rate por SETOR da conta (empirico, com shrinkage)")
w("| Setor | n | raw | shrunk | efeito vs. global (pp) |")
w("|---|---|---|---|---|")
for s, r in sector_stats.sort_values("n").iterrows():
    effect = (r.shrunk - global_rate) * 100
    sign = "+" if effect >= 0 else ""
    w(f"| {s} | {int(r.n)} | {r.raw:.1%} | {r.shrunk:.1%} | {sign}{effect:.1f} |")
w()

w("## Multiplicador de estagio (HEURISTICO — nao derivado do historico)")
w("| Estagio | Multiplicador |")
w("|---|---|")
for stage, mult in STAGE_MULTIPLIER.items():
    w(f"| {stage} | x{mult} |")
w()

w("## Limiar de 'esfriando' por produto (p75 do ciclo dos deals WON)")
w("| Produto | n_won | p75 dias |")
w("|---|---|---|")
for p, r in cooling_stats.sort_values("n_won").iterrows():
    w(f"| {p} | {int(r.n_won)} | {r.p75_days:.0f} |")
w()

w("## Valor potencial por produto (products.sales_price)")
w("| Produto | sales_price |")
w("|---|---|")
for p, price in product_sales_price.items():
    w(f"| {p} | {price} |")
w()

# --- Validacao agregada ---
w("## Validacao agregada — deals abertos scorados (Prospecting + Engaging)")
w(f"- Total scorado: {len(scored)}")
w(f"- P(fechar): media={scored['p_fechar'].mean():.1%}, mediana={scored['p_fechar'].median():.1%}, "
  f"min={scored['p_fechar'].min():.1%}, max={scored['p_fechar'].max():.1%}")
w(f"- EV: media={scored['ev'].mean():.0f}, mediana={scored['ev'].median():.0f}, "
  f"min={scored['ev'].min():.0f}, max={scored['ev'].max():.0f}")
n_cooling = int(scored["esfriando"].sum())
n_engaging = int((scored["deal_stage"] == "Engaging").sum())
w(f"- Flag 'esfriando': {n_cooling} deals ({n_cooling/n_engaging:.1%} dos Engaging — Prospecting nunca flegado)")
w()
w("### Limitacao conhecida da flag 'esfriando'")
w(f"- {n_cooling/n_engaging:.1%} dos deals Engaging estao flegados como esfriando — proporcao alta demais pra "
  "discriminar prioridade de verdade. Motivo provavel: o dataset e uma FOTO estatica (nao um CRM ao vivo). A "
  "data de referencia usada e a data mais recente encontrada no proprio dataset "
  f"({REFERENCE_DATE.date()}), entao TODO deal que segue aberto ali e, por construcao, um deal que nao fechou "
  "rapido — os que fechariam rapido ja teriam saido do balde 'aberto' antes dessa data. Isso enviesa a amostra "
  "de deals abertos para os mais antigos (nao e erro de calculo, e vies de amostragem por corte no tempo). Num "
  "CRM ao vivo, com deals novos entrando toda semana, a proporcao tende a ser bem menor. Vale reconsiderar o "
  "percentil (ex.: p90 em vez de p75) ou comunicar esse caveat explicitamente no app.")
w()

# --- Amostra para inspecao manual (deterministica, cobre os cenarios da fase 2) ---
w("## Amostra para inspecao manual (drivers completos)")

def sample_block(title, mask, n=3):
    w(f"### {title}")
    subset = scored[mask].sort_values("opportunity_id").head(n)
    if subset.empty:
        w("_(nenhum registro nesse cenario)_")
        w()
        return
    for _, r in subset.iterrows():
        w(f"- **{r.opportunity_id}** ({r['product']}, {r.deal_stage}) — P(fechar)={r.p_fechar:.0%}, "
          f"valor_potencial={r.valor_potencial}, EV={r.ev:.0f}, esfriando={r.esfriando}")
        w(f"  - Drivers: {r.drivers}")
    w()

sample_block("Engaging, com conta, esfriando", (scored.deal_stage == "Engaging") & scored.esfriando & scored.account.notna())
sample_block("Engaging, com conta, nao esfriando", (scored.deal_stage == "Engaging") & ~scored.esfriando & scored.account.notna())
sample_block("Engaging, sem conta", (scored.deal_stage == "Engaging") & scored.account.isna())
sample_block("Prospecting, com conta", (scored.deal_stage == "Prospecting") & scored.account.notna())
sample_block("Prospecting, sem conta", (scored.deal_stage == "Prospecting") & scored.account.isna())

w("## Sanity check — top 5 e bottom 5 por EV")
w("Top 5:")
for _, r in scored.sort_values("ev", ascending=False).head(5).iterrows():
    w(f"- {r.opportunity_id} ({r['product']}, {r.deal_stage}): EV={r.ev:.0f} — {r.drivers}")
w("Bottom 5:")
for _, r in scored.sort_values("ev", ascending=True).head(5).iterrows():
    w(f"- {r.opportunity_id} ({r['product']}, {r.deal_stage}): EV={r.ev:.0f} — {r.drivers}")
w()

with open(OUT_MD, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"OK -> escrito {OUT_MD} e {OUT_JSON} ({len(lines)} linhas no resumo, {len(scored)} deals scorados)")

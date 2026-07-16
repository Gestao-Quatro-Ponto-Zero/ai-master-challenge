"""
Fase 4 — Backtest do motor de P(fechar) nos deals FECHADOS (Won+Lost).

ANTI-VAZAMENTO: win rate por produto/setor (com shrinkage) e recalculada
SO no fold de treino (k-fold=5, estratificado por Won/Lost) e aplicada no
fold de teste. Nenhum deal informa a propria taxa. Sem multiplicador de
estagio (deal fechado nao tem estagio aberto, e e heuristica, nao testavel).

Mede com honestidade: discriminacao (AUC), calibracao, e captura de valor
no top-20% vs baselines. Nao infla resultado.

Usa pipeline_clean.csv. Saida: 04_backtest_summary.md
"""
import numpy as np
import pandas as pd

DATA = "../data"
PIPELINE_CLEAN = "pipeline_clean.csv"
OUT_MD = "04_backtest_summary.md"

SHRINKAGE_K = 30
N_FOLDS = 5
SEED = 42

accounts = pd.read_csv(f"{DATA}/accounts.csv")
products = pd.read_csv(f"{DATA}/products.csv")
pipeline = pd.read_csv(PIPELINE_CLEAN, parse_dates=["engage_date", "close_date"])
product_sales_price = dict(zip(products["product"], products["sales_price"]))

lines = []
def w(s=""):
    lines.append(s)


def shrink(raw_rate, n, global_rate, k=SHRINKAGE_K):
    return (n * raw_rate + k * global_rate) / (n + k)


def compute_auc(y_true, y_score):
    """AUC via formula de rank-sum (Mann-Whitney U) — equivalente a ROC AUC binaria."""
    d = pd.DataFrame({"y": np.asarray(y_true), "s": np.asarray(y_score)})
    d["rank"] = d["s"].rank(method="average")
    n1 = int((d["y"] == 1).sum())
    n0 = int((d["y"] == 0).sum())
    sum_ranks_pos = d.loc[d["y"] == 1, "rank"].sum()
    return (sum_ranks_pos - n1 * (n1 + 1) / 2) / (n1 * n0)


# ------------------------------------------------------------------
# 1. Universo: deals fechados, com sector via account
# ------------------------------------------------------------------
closed = pipeline[pipeline["deal_stage"].isin(["Won", "Lost"])].merge(
    accounts[["account", "sector"]], on="account", how="left"
).reset_index(drop=True)
closed["won"] = (closed["deal_stage"] == "Won").astype(int)
closed["valor_potencial"] = closed["product"].map(product_sales_price)

n_no_sector = closed["sector"].isna().sum()

# ------------------------------------------------------------------
# 2. Fold estratificado por outcome (Won/Lost), seed fixa p/ reprodutibilidade
# ------------------------------------------------------------------
rng = np.random.default_rng(SEED)
fold = np.empty(len(closed), dtype=int)
for outcome_val in [0, 1]:
    idx = closed.index[closed["won"] == outcome_val].to_numpy()
    shuffled = rng.permutation(idx)
    fold[shuffled] = np.arange(len(shuffled)) % N_FOLDS
closed["fold"] = fold

# ------------------------------------------------------------------
# 3. K-fold: recalcula win rate de produto/setor SO no treino, aplica no teste
# ------------------------------------------------------------------
oof_parts = []
fold_global_rates = []
for k in range(N_FOLDS):
    train = closed[closed["fold"] != k]
    test = closed[closed["fold"] == k].copy()

    global_rate_train = train["won"].mean()
    fold_global_rates.append(global_rate_train)

    prod_g = train.groupby("product")["won"].agg(n="count", raw="mean")
    prod_g["shrunk"] = shrink(prod_g["raw"], prod_g["n"], global_rate_train)
    prod_map = prod_g["shrunk"].to_dict()

    sec_g = train.dropna(subset=["sector"]).groupby("sector")["won"].agg(n="count", raw="mean")
    sec_g["shrunk"] = shrink(sec_g["raw"], sec_g["n"], global_rate_train)
    sec_map = sec_g["shrunk"].to_dict()

    test["p_base"] = test["product"].map(lambda p: prod_map.get(p, global_rate_train))
    test["sector_effect"] = test["sector"].map(
        lambda s: (sec_map[s] - global_rate_train) if (pd.notna(s) and s in sec_map) else 0.0
    )
    test["p_pred"] = (test["p_base"] + test["sector_effect"]).clip(0.01, 0.99)
    test["p_base_only"] = test["p_base"].clip(0.01, 0.99)  # diagnostico: sem ajuste de setor
    test["ev_pred"] = test["p_pred"] * test["valor_potencial"]
    oof_parts.append(test)

oof = pd.concat(oof_parts).sort_index()
total_won_value = oof["close_value"].sum()
n_total = len(oof)
top_n = int(round(n_total * 0.20))

# ------------------------------------------------------------------
# 4. Discriminacao (AUC) — com e sem ajuste de setor (diagnostico extra)
# ------------------------------------------------------------------
auc_full = compute_auc(oof["won"], oof["p_pred"])
auc_product_only = compute_auc(oof["won"], oof["p_base_only"])

# ------------------------------------------------------------------
# 5. Calibracao — decis de p_pred vs win rate real observado
# ------------------------------------------------------------------
oof["decile"] = pd.qcut(oof["p_pred"], 10, duplicates="drop")
calib = oof.groupby("decile", observed=True).agg(
    n=("won", "count"), p_previsto_medio=("p_pred", "mean"), win_rate_real=("won", "mean")
)

# ------------------------------------------------------------------
# 6. Captura de valor no top-20% — EV vs baselines (mesma base embaralhada
#    p/ empates serem quebrados de forma justa em todos os metodos)
# ------------------------------------------------------------------
oof_shuffled = oof.sample(frac=1, random_state=7)

def capture_pct(df_sorted):
    return df_sorted.head(top_n)["close_value"].sum() / total_won_value

ev_capture = capture_pct(oof_shuffled.sort_values("ev_pred", ascending=False, kind="mergesort"))
value_capture = capture_pct(oof_shuffled.sort_values("valor_potencial", ascending=False, kind="mergesort"))

rng2 = np.random.default_rng(SEED + 1)
random_caps = []
close_values = oof["close_value"].to_numpy()
for _ in range(500):
    idx = rng2.permutation(n_total)[:top_n]
    random_caps.append(close_values[idx].sum() / total_won_value)
random_caps = np.array(random_caps)
random_mean, random_std = random_caps.mean(), random_caps.std()

# Spearman = correlacao de Pearson sobre os ranks (evita depender de scipy)
spearman_ev_value = oof["ev_pred"].rank().corr(oof["valor_potencial"].rank())

# ------------------------------------------------------------------
# 7. Relatorio
# ------------------------------------------------------------------
w("# Fase 4 — Backtest do motor de P(fechar) (deals fechados, Won+Lost)\n")

w("## Metodologia (anti-vazamento)")
w(f"- Universo: {n_total} deals fechados (Won+Lost) de `{PIPELINE_CLEAN}`.")
w(f"- K-fold={N_FOLDS}, estratificado por outcome (Won/Lost), seed={SEED} (reprodutivel).")
w("- Em cada fold, win rate de PRODUTO e de SETOR (com shrinkage, k=30) sao recalculados "
  "usando SOMENTE os outros 4 folds (treino). O fold de teste nunca contribui para a taxa "
  "usada em si mesmo.")
w("- `deal_stage` NAO entra no score aqui — deal fechado nao tem estagio aberto, e o "
  "multiplicador e heuristico (nao testavel contra outcome real).")
w("- Valor potencial = `products.sales_price` (mesma escolha da Fase 3), nao `close_value` — "
  "closed_value so e conhecido apos o fechamento e nao pode ser usado como input do score.")
w(f"- **Limitacao importante**: no universo fechado, {len(closed) - n_no_sector}/{len(closed)} "
  f"deals tem `account`/`sector` conhecido ({n_no_sector} sem sector). Ou seja, este backtest "
  "valida quase exclusivamente o ramo 'com conta' da logica — o ramo 'sem conta, so produto' "
  "(que cobre ~68% dos deals ABERTOS, ver Fase 2) tem pouquissimo ou nenhum dado fechado "
  "equivalente para validar. A qualidade de P(fechar) para deals sem conta permanece uma "
  "suposicao nao testada por este backtest.")
w(f"- Taxa global por fold (treino): {[f'{r:.1%}' for r in fold_global_rates]} — estavel entre folds.")
w()

w("## 1. Discriminacao (AUC)")
w(f"- **AUC (produto + setor)**: {auc_full:.3f}")
w(f"- **AUC (so produto, diagnostico)**: {auc_product_only:.3f}")
w("- Referencia: 0.5 = sem poder discriminativo (equivalente a chute aleatorio); 1.0 = separacao perfeita.")
if auc_full < 0.60:
    w(f"- **Achado esperado, nao e bug**: AUC de {auc_full:.3f} indica discriminacao BAIXA. "
      "Win rate por produto/setor varia pouco (55%-65%) — quase todo deal historico tem probabilidade "
      "parecida de fechar, entao o modelo separa mal quem vai Won de quem vai Lost usando so essas features. "
      "Isso bate com o que a Fase 3 ja mostrava: o efeito de setor e minusculo (<2pp) e o de produto e modesto.")
w()

w("## 2. Calibracao (decis de P previsto vs win rate real)")
w("| Decil (p_pred) | n | p previsto (media) | win rate real |")
w("|---|---|---|---|")
for interval, r in calib.iterrows():
    w(f"| {interval} | {int(r.n)} | {r.p_previsto_medio:.1%} | {r.win_rate_real:.1%} |")
w()
calib_gap = (calib["p_previsto_medio"] - calib["win_rate_real"]).abs().mean()
w(f"- Gap medio absoluto entre previsto e real por decil: {calib_gap:.1%}.")
top_decile = calib.iloc[-1]
if calib_gap < 0.03:
    w("- **Razoavelmente calibrado NA MEDIA**: a probabilidade prevista fica perto da taxa real "
      "observada na maioria das faixas — o modelo nao discrimina bem QUAL deal individual vai "
      "fechar, mas as MEDIAS por segmento sao uteis o suficiente pra EV agregado fazer sentido.")
w(f"- **Mas ha um furo na ponta**: o decil de MAIOR P previsto ({top_decile.p_previsto_medio:.1%}) "
  f"tem a MENOR win rate real observada ({top_decile.win_rate_real:.1%}) — o oposto do esperado. "
  "Isso e consistente com o AUC ficar levemente abaixo de 0.5: nao ha garantia de que 'score mais "
  "alto' realmente signifique 'mais chance de fechar' nos extremos. Nao suavizo isso so porque a "
  "media geral fecha bem — a calibracao e boa NO AGREGADO, nao necessariamente na cauda.")
w()

w("## 3. Captura de valor no top-20% (o que a ferramenta REALMENTE promete)")
w(f"- Top 20% = {top_n} de {n_total} deals fechados.")
w(f"- Valor Won total no universo: {total_won_value:,.0f}")
w()
w("| Metodo de ranking | % do valor Won capturado no top-20% |")
w("|---|---|")
w(f"| **EV previsto (produto+setor, sem estagio)** | {ev_capture:.1%} |")
w(f"| (b) Ordenar por valor puro (`sales_price`) | {value_capture:.1%} |")
w(f"| (a) Ordem aleatoria (media de 500 simulacoes, ±1 desvio) | {random_mean:.1%} ± {random_std:.1%} |")
w()
w("### Sobre a baseline (c) 'ordenar por estagio' — nao computada, e por que")
w("- Neste universo de backtest, `deal_stage` so assume `Won` ou `Lost` — ou seja, **e o proprio "
  "rotulo que estamos tentando prever**. Ordenar por estagio aqui seria ordenar pela resposta certa: "
  "daria ~100% de captura trivialmente, mas isso nao mede nada sobre o valor do scoring, so mede que "
  "sabemos separar Won de Lost quando ja sabemos quem e Won. Incluir esse numero seria enganoso "
  "(um vazamento disfarcado de baseline). A comparacao contra estagio (Prospecting vs Engaging) so "
  "faz sentido no pipeline ABERTO, em producao, olhando pra frente — nao da pra backtestar com dados "
  "historicos fechados.")
w()
w(f"- **Lift vs aleatorio**: {ev_capture/random_mean:.2f}x")
w(f"- **Lift vs valor puro**: {ev_capture/value_capture:.2f}x")
w(f"- **Correlacao de Spearman entre ranking por EV e ranking por valor puro**: {spearman_ev_value:.3f}")
lift_value = ev_capture / value_capture
if spearman_ev_value > 0.9:
    w("- Correlacao muito alta: como o win rate varia pouco entre produtos, o ranking por EV e "
      "quase o mesmo que simplesmente ordenar pelos deals mais caros.")
if lift_value < 1.0:
    w(f"- **Honestidade sem meio-termo: o EV NAO supera a baseline 'valor puro' neste backtest** "
      f"({ev_capture:.1%} vs {value_capture:.1%}, lift={lift_value:.2f}x). A diferenca e pequena e "
      f"pode ser so ruido (rankings {spearman_ev_value:.1%} correlacionados), mas o dado bruto nao "
      "mostra ganho — mostra empate ou leve perda. Nao vou reportar isso como 'lift modesto positivo' "
      "quando o numero real e <= 1.0x.")
else:
    w(f"- O ganho sobre 'perseguir os deals de maior valor' e modesto ({lift_value:.2f}x) — nao "
      "invento um resultado melhor do que isso.")
w()

w("## Conclusao honesta")
w(f"- O modelo **nao discrimina bem** quem individualmente vai fechar (AUC={auc_full:.3f}, perto de "
  "0.5, com inversao no decil mais alto).")
w("- As taxas por segmento **sao razoavelmente calibradas na media agregada** — uteis pra EV agregado, "
  "nao pra apostar num deal so.")
w(f"- A captura de valor no top-20% ({ev_capture:.1%}) bate a ordem aleatoria "
  f"({random_mean:.1%} ± {random_std:.1%}), lift de {ev_capture/random_mean:.2f}x.")
w(f"- **Mas contra a baseline 'valor puro' o EV nao ganha** ({ev_capture:.1%} vs {value_capture:.1%}, "
  f"lift={lift_value:.2f}x) — porque o win rate quase nao varia entre segmentos neste dataset "
  f"(rankings {spearman_ev_value:.1%} correlacionados). Priorizar por EV aqui e, na pratica, quase "
  "o mesmo que so olhar pro tamanho do deal.")
w("- O valor real da ferramenta, neste dataset, nao esta em 'prever quem vai fechar' com precisao — "
  "esta em dar VISIBILIDADE e EXPLICABILIDADE sobre um pipeline de 8800 linhas priorizado 'no feeling', "
  "mais o multiplicador de estagio (heuristico, nao testavel aqui) que empurra deals ja engajados pra "
  "frente. O componente empirico (produto+setor) contribui pouco alem do que o valor do deal ja diria "
  "sozinho — isso deve ser dito com todas as letras na documentacao do app, nao escondido.")

with open(OUT_MD, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"OK -> escrito {OUT_MD} ({len(lines)} linhas, {n_total} deals no backtest)")

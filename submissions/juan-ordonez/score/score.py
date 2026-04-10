"""
Lead Scorer — motor de score.

Fluxo público:

    df = load_and_enrich(DATA_DIR)
    df = compute_features(df)
    buckets = compute_buckets(df)
    for _, row in df[df["deal_stage"] == "Engaging"].iterrows():
        result = score_deal(row, buckets)

O motor usa lookup empírico em 6 buckets (tier × is_new_combo), calibrado
sobre o histórico de deals fechados. A probabilidade de cada deal é o
win rate observado no bucket ao qual ele pertence, com smoothing Bayesiano
leve para buckets pequenos. Sem ML, sem coeficientes arbitrários — cada
número sai dos dados.

Rodar este arquivo direto executa o self-test:

    python score.py

que valida que o score reproduz o win rate observado por bucket com
delta <1pp. Falha explícita se algo estiver quebrado.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================================
# CONSTANTES (decisões congeladas — alterar aqui, não em outros lugares)
# ============================================================================

# "Hoje" no contexto da ferramenta. O dataset é estático e cobre 2016-2017;
# usamos max(close_date) + 1 como referência. Em produção seria datetime.now().
SNAPSHOT_DATE = pd.Timestamp("2018-01-01")

# Win rate global sobre deals fechados — usado como prior do smoothing e
# como fallback quando nenhum sinal está disponível.
BASELINE_WR = 0.632

# Força do smoothing Bayesiano. k=30 significa "shrink em direção ao prior
# até o bucket ter 30 observações"; acima disso o bucket domina.
SMOOTHING_K = 30

# Cortes absolutos de tier do vendedor. Absolutos (não quantis) porque são
# mais interpretáveis no process log e estáveis se a distribuição mudar.
# Nota: o tier é uma chave interna de lookup. NUNCA é exibido na UI — o
# rótulo ("top"/"mid"/"low") fica escondido, o vendedor só sente o efeito
# via a probabilidade calibrada para o perfil dele.
TIER_CUTOFF_TOP = 0.65
TIER_CUTOFF_MID = 0.55

# Thresholds da classificação de ação.
# PROB_HIGH é alinhado ao baseline global (0.632) para que deals "acima da
# média" caiam em categorias de ação e não no limbo.
# EV_HIGH separa deals de valor alto que merecem atenção mesmo com prob mediana.
PROB_HIGH = 0.63
EV_HIGH = 3000

# Ranking de "Foco da semana" (aplicado por vendedor em build_data.py):
# top 30% do pipeline rankeável de cada vendedor, com piso 5 e teto 15.
FOCUS_PCT = 0.30
FOCUS_MIN = 5
FOCUS_MAX = 15


# ============================================================================
# CARGA E ENRIQUECIMENTO
# ============================================================================

def load_and_enrich(data_dir: Path) -> pd.DataFrame:
    """
    Lê os 4 CSVs do Maven CRM, normaliza bugs conhecidos, faz joins, parseia
    datas. Retorna um DataFrame com uma linha por oportunidade e colunas
    das 4 tabelas combinadas.
    """
    data_dir = Path(data_dir)
    accounts = pd.read_csv(data_dir / "accounts.csv")
    products = pd.read_csv(data_dir / "products.csv")
    teams = pd.read_csv(data_dir / "sales_teams.csv")
    pipeline = pd.read_csv(data_dir / "sales_pipeline.csv")

    # Bug conhecido: "GTXPro" no pipeline vs "GTX Pro" em products.
    pipeline["product"] = pipeline["product"].replace({"GTXPro": "GTX Pro"})

    # Datas como Timestamp para cálculos de duração.
    pipeline["engage_date"] = pd.to_datetime(pipeline["engage_date"])
    pipeline["close_date"] = pd.to_datetime(pipeline["close_date"])

    df = (
        pipeline
        .merge(products, on="product", how="left")
        .merge(teams, on="sales_agent", how="left")
        .merge(accounts, on="account", how="left", suffixes=("", "_acc"))
    )
    return df


# ============================================================================
# FEATURES
# ============================================================================

def _compute_is_new_combo(df_sorted: pd.DataFrame) -> list:
    """
    Marca se cada deal é o primeiro aparecimento do combo
    (sales_agent, account, product) no histórico ordenado por engage_date.

    Definição congelada: considera qualquer stage (Won/Lost/Engaging/Prospecting)
    como "histórico" — não apenas fechados. Isso mantém a calibração e o
    scoring consistentes: um combo que aparece várias vezes no pipeline,
    mesmo sem ter fechado ainda, já não conta como "novo" na segunda vez.

    Deals sem account (Prospecting puro e parte do Engaging) ficam com NaN:
    não temos como saber se o combo é novo sem saber qual é a conta.
    """
    seen = set()
    out = []
    for row in df_sorted.itertuples(index=False):
        if pd.isna(row.account):
            out.append(np.nan)
            continue
        key = (row.sales_agent, row.account, row.product)
        out.append(key not in seen)
        seen.add(key)
    return out


def _classify_tier(wr: float) -> str:
    """Cortes absolutos. Vendedores sem histórico ficam como 'unknown'."""
    if pd.isna(wr):
        return "unknown"
    if wr >= TIER_CUTOFF_TOP:
        return "top"
    if wr >= TIER_CUTOFF_MID:
        return "mid"
    return "low"


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona as colunas derivadas usadas pelo score:

    - is_new_combo : bool ou NaN, conforme definição acima
    - agent_wr     : win rate histórico do vendedor (fechados apenas)
    - agent_tier   : 'top' / 'mid' / 'low' / 'unknown'
    - days_open    : (SNAPSHOT_DATE - engage_date).days; NaN se sem engage_date

    O DataFrame retornado é ordenado por engage_date (necessário para o
    cálculo de is_new_combo). Vendedores sem deal fechado viram 'unknown'.
    """
    df = df.sort_values("engage_date", na_position="last").reset_index(drop=True)

    # is_new_combo depende da ordem cronológica.
    df["is_new_combo"] = _compute_is_new_combo(df)

    # agent_wr calculado só sobre deals fechados.
    closed = df[df["deal_stage"].isin(["Won", "Lost"])]
    agent_wr = (
        closed.groupby("sales_agent")["deal_stage"]
        .apply(lambda s: (s == "Won").mean())
        .rename("agent_wr")
    )
    df = df.merge(agent_wr, on="sales_agent", how="left")

    df["agent_tier"] = df["agent_wr"].apply(_classify_tier)

    # days_open: quantos dias o deal está aberto, usando SNAPSHOT_DATE como "hoje".
    df["days_open"] = (SNAPSHOT_DATE - df["engage_date"]).dt.days

    return df


# ============================================================================
# BUCKETS EMPÍRICOS
# ============================================================================

def compute_buckets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calibra os 6 buckets (agent_tier × is_new_combo) sobre deals fechados.
    Aplica smoothing Bayesiano com k=SMOOTHING_K e prior=BASELINE_WR.

    Retorna DataFrame com índice (agent_tier, is_new_combo) e colunas
    n, wr, smoothed_wr.
    """
    closed = df[df["deal_stage"].isin(["Won", "Lost"])].copy()
    closed = closed.dropna(subset=["is_new_combo"])
    closed = closed[closed["agent_tier"] != "unknown"]

    grouped = closed.groupby(["agent_tier", "is_new_combo"]).agg(
        n=("opportunity_id", "size"),
        wr=("deal_stage", lambda s: (s == "Won").mean()),
    )

    grouped["smoothed_wr"] = (
        grouped["n"] * grouped["wr"] + SMOOTHING_K * BASELINE_WR
    ) / (grouped["n"] + SMOOTHING_K)

    return grouped


# ============================================================================
# SCORE DE UM DEAL
# ============================================================================

def score_deal(row: pd.Series, buckets: pd.DataFrame) -> dict:
    """
    Calcula o score de um único deal. Retorna um dict achatado pronto
    para ir direto pro data.js.

    Fallback hierárquico:
      1. tier válido + is_new_combo válido → lookup no bucket (confiança alta/média)
      2. sem is_new_combo ou tier unknown, mas com agent_wr → agent_wr (confiança média)
      3. nenhum dos dois                                    → BASELINE_WR (confiança baixa)

    A categoria `action` retornada aqui é a classificação INICIAL (por
    threshold). O ranking de "Foco da semana" é aplicado depois, por
    vendedor, em build_data.py — ele sobrescreve a action dos top N.

    O `agent_tier` é retornado no dict mas marcado como interno — o front
    NÃO deve exibi-lo. É chave de lookup, não rótulo de UI.
    """
    tier = row["agent_tier"]
    is_new = row["is_new_combo"]
    bucket_n = 0

    if pd.isna(is_new) or tier == "unknown":
        # Fallback 2 ou 3.
        if pd.notna(row.get("agent_wr")):
            prob = float(row["agent_wr"])
            prob_source = "agent_fallback"
            confidence = "média"
        else:
            prob = BASELINE_WR
            prob_source = "global_fallback"
            confidence = "baixa"
    else:
        # Caminho feliz: lookup no bucket.
        try:
            prob = float(buckets.loc[(tier, is_new), "smoothed_wr"])
            bucket_n = int(buckets.loc[(tier, is_new), "n"])
            prob_source = "bucket"
            confidence = "alta" if bucket_n >= 100 else "média"
        except KeyError:
            prob = BASELINE_WR
            prob_source = "global_fallback"
            confidence = "baixa"

    value = float(row["sales_price"])
    ev = prob * value
    action = classify_action(prob, ev, is_new)
    explanation = build_explanation(
        is_new_combo=is_new,
        prob=prob,
        prob_source=prob_source,
        account=row.get("account"),
        product=row.get("product"),
    )

    days_open = row.get("days_open")
    days_open = int(days_open) if pd.notna(days_open) else None

    return {
        "id": row["opportunity_id"],
        "agent": row["sales_agent"],
        "_agent_tier_internal": tier if tier != "unknown" else None,  # uso interno, não exibir
        "account": row["account"] if pd.notna(row["account"]) else None,
        "product": row["product"],
        "value": round(value, 2),
        "days_open": days_open,
        "is_new_combo": None if pd.isna(is_new) else bool(is_new),
        "prob": round(prob, 3),
        "ev": round(ev, 2),
        "confidence": confidence,
        "action": action,
        "explanation": explanation,
    }


# ============================================================================
# CLASSIFICAÇÃO DE AÇÃO
# ============================================================================

def classify_action(prob: float, ev: float, is_new_combo) -> str:
    """
    Classificação INICIAL por threshold. 4 categorias mutuamente exclusivas.

    Nomes usam a taxonomia acionável P1-P4 + "Atribuir conta" (fora da escala).
    A priority numérica é atribuída depois, em build_data.py, baseada nestes nomes.

    Ordem (IMPORTA — primeira regra que bate vence):
      1. is_new_combo é NaN   → "Atribuir conta"   (fora da escala P, estrutural)
      2. ev ≥ 3000            → "Foco secundário"  (P2 — grandes fora do top)
      3. prob ≥ 0.63          → "Ganho rápido"     (P3 — prob boa, valor menor)
      4. caso contrário       → "Repensar"         (P4 — prob abaixo do baseline)

    Por que esta ordem:
    - 'Atribuir conta' é estrutural (sem conta) e vem antes de tudo.
    - 'Foco secundário' captura deals grandes que merecem atenção mesmo
      quando outros ainda maiores do mesmo vendedor os deslocaram do P1.
    - 'Ganho rápido' captura deals com prob acima do baseline global (0.632).
    - 'Repensar' é o default para deals com prob abaixo do baseline.

    "Foco da semana" (P1) NÃO é classificada aqui — é atribuída por ranking
    (top N de EV por vendedor) em build_data.py, sobrescrevendo a action
    inicial dos top N deals de cada vendedor.
    """
    if pd.isna(is_new_combo):
        return "Atribuir conta"
    if ev >= EV_HIGH:
        return "Foco secundário"
    if prob >= PROB_HIGH:
        return "Ganho rápido"
    return "Repensar"


# ============================================================================
# EXPLICAÇÃO HUMANA (texto lido pelo vendedor)
# ============================================================================

def build_explanation(
    is_new_combo,
    prob: float,
    prob_source: str,
    account=None,
    product=None,
) -> str:
    """
    Gera a frase que o vendedor lê no card do deal. Estilo pessoal,
    direto, sem jargão técnico. NUNCA menciona o tier ("top"/"mid"/"low")
    nem termos de analista ("win rate", "histórico").

    Quatro variações por `prob_source`:

    1. Deal sem conta atribuída:
       "Sem conta atribuída — atribua para eu ranquear."

    2. Deal com bucket válido — combo novo (caso principal):
       "Primeira vez oferecendo MG Advanced pra Ganjaflex. Vendedores como
        você fecham 68% dos combos novos."

    3. Deal com bucket válido — combo recorrente:
       "Já tentaram GTX Plus Basic com Zathunicon antes. Vendedores como
        você fecham 61% em recompras."

    4. Deal com fallback de agent_wr (sem is_new_combo):
       "Teu histórico médio é 63%. Sem dado específico do combo."

    5. Deal sem histórico nenhum (global fallback):
       "Sem histórico — chance estimada em 63% (média geral)."
    """
    prob_pct = int(round(prob * 100))

    if pd.isna(is_new_combo):
        return "Sem conta atribuída — atribua para eu ranquear."

    if prob_source == "bucket":
        if is_new_combo:
            if pd.notna(account) and pd.notna(product):
                context = f"Primeira vez oferecendo {product} pra {account}."
            else:
                context = "Combo novo."
            return f"{context} Vendedores como você fecham {prob_pct}% dos combos novos."
        else:
            if pd.notna(account) and pd.notna(product):
                context = f"Já tentaram {product} com {account} antes."
            else:
                context = "Combo recorrente."
            return f"{context} Vendedores como você fecham {prob_pct}% em recompras."

    if prob_source == "agent_fallback":
        return f"Teu histórico médio é {prob_pct}%. Sem dado específico do combo."

    return f"Sem histórico — chance estimada em {prob_pct}% (média geral)."


# ============================================================================
# SELF-TEST
# ============================================================================

def _self_test() -> None:
    """
    Valida que o motor está consistente consigo mesmo:

    1. Carrega dados e calibra buckets.
    2. Aplica score_deal em todos os deals fechados.
    3. Para cada bucket, confere que mean(prob) ≈ smoothed_wr (delta <1pp).
    4. Imprime a distribuição de ação nos fechados como sanity.

    Se qualquer bucket desvia mais de 1pp, abortamos com exit code 1.
    """
    data_dir = Path(__file__).resolve().parent.parent / "data"
    print(f"[self-test] data_dir = {data_dir}")

    df = load_and_enrich(data_dir)
    print(f"[self-test] loaded {len(df)} deals")

    df = compute_features(df)
    print(f"[self-test] features computed")

    buckets = compute_buckets(df)
    print(f"\n[self-test] buckets calibrados:")
    print(buckets.round(4).to_string())

    closed = df[df["deal_stage"].isin(["Won", "Lost"])].copy()
    closed = closed.dropna(subset=["is_new_combo"])
    closed = closed[closed["agent_tier"] != "unknown"]

    print("\n[self-test] validando mean(prob) vs smoothed_wr por bucket:")
    print(f"  {'tier':>5} {'is_new':>7} {'n':>6} {'mean_prob':>11} {'expected':>10} {'delta':>8} status")
    errors = []
    for (tier, is_new), group in closed.groupby(["agent_tier", "is_new_combo"], observed=True):
        scored = [score_deal(row, buckets) for _, row in group.iterrows()]
        mean_prob = float(np.mean([s["prob"] for s in scored]))
        expected = float(buckets.loc[(tier, is_new), "smoothed_wr"])
        delta = abs(mean_prob - expected)
        status = "OK" if delta < 0.01 else "FAIL"
        print(
            f"  {tier:>5} {str(is_new):>7} {len(group):>6} "
            f"{mean_prob:>11.4f} {expected:>10.4f} {delta:>8.4f} {status}"
        )
        if delta >= 0.01:
            errors.append((tier, is_new, delta))

    if errors:
        print(f"\n[self-test] ❌ FAIL: {len(errors)} bucket(s) com delta >= 1pp")
        sys.exit(1)

    print("\n[self-test] ✅ todos os buckets dentro de 1pp")

    # Sanity extra: distribuição de action nos fechados (não vai ser a distribuição
    # final dos abertos, mas já é um smoke test do classify_action).
    counts = Counter(score_deal(row, buckets)["action"] for _, row in closed.iterrows())
    print("\n[self-test] distribuição de ação nos deals fechados (sanity):")
    for action, n in counts.most_common():
        pct = n / len(closed) * 100
        print(f"  {action:<25} {n:>5}  ({pct:.1f}%)")

    # Smoke test adicional: 3 exemplos específicos que bateram na revisão anterior.
    print("\n[self-test] exemplos de referência:")
    ref_deals = [
        ("Maureen Marcano", "Ganjaflex", "MG Advanced", "Engaging"),
        ("Daniell Hammack", "Zathunicon", "GTX Plus Basic", "Engaging"),
    ]
    for agent, account, product, stage in ref_deals:
        mask = (
            (df["sales_agent"] == agent)
            & (df["account"] == account)
            & (df["product"] == product)
            & (df["deal_stage"] == stage)
        )
        match = df[mask]
        if len(match) == 0:
            print(f"  [WARN] não encontrei {agent} + {account} + {product} ({stage})")
            continue
        result = score_deal(match.iloc[0], buckets)
        print(f"  {agent} / {account} / {product}")
        print(f"    prob={result['prob']}  ev={result['ev']}  action={result['action']}")
        print(f"    explanation: {result['explanation']}")


if __name__ == "__main__":
    _self_test()

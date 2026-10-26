"""Fatos dos dados: todo número da fase 0 e do bloco 2 que os documentos citam sai daqui.

`build_facts` devolve um dicionário só com números crus (frações como 0.632) e `write_facts`
grava `data/processed/facts.json`. As seções `evidencia_2a/2b/2c` trazem a evidência das
investigações do bloco 2, com o resultado de cada critério de decisão.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, rankdata

from . import config


# --- utilidades ---------------------------------------------------------------------------
def to_jsonable(obj):
    """Converte tipos numpy/pandas para tipos JSON; NaN, NaT e infinitos viram None."""
    if isinstance(obj, dict):
        return {str(key): to_jsonable(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple, np.ndarray, pd.Index)):
        return [to_jsonable(value) for value in obj]
    if obj is None or obj is pd.NaT:
        return None
    if isinstance(obj, (pd.Timestamp, pd.Period)):
        return obj.strftime("%Y-%m-%d") if isinstance(obj, pd.Timestamp) else str(obj)
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        return None if (math.isnan(obj) or math.isinf(obj)) else float(obj)
    return obj


def _auc(x, y) -> float:
    """AUC por Mann-Whitney com posto médio (0,5 = sem poder de ordenação)."""
    ranks = rankdata(x)
    n1 = int(y.sum())
    n0 = len(y) - n1
    return float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def _quarter(period: pd.Period) -> str:
    return f"{period.year}-Q{period.quarter}"


def _quarter_index(dates: pd.Series) -> pd.Series:
    """Número sequencial do trimestre, para medir a distância entre dois trimestres."""
    return dates.dt.year * 4 + dates.dt.quarter


def _share(mask: pd.Series) -> float:
    return float(mask.mean())


def _by_count(series: pd.Series) -> dict:
    """Contagem por valor, da maior para a menor (empates em ordem alfabética)."""
    counts = series.value_counts().sort_index().sort_values(ascending=False, kind="stable")
    return {name: int(n) for name, n in counts.items()}


# --- seções gerais ------------------------------------------------------------------------
def _pipeline(deals: pd.DataFrame, closed: pd.DataFrame) -> dict:
    stages = deals["deal_stage"].value_counts()
    return {
        "total_deals": len(deals),
        "deals_por_estagio": {stage: int(stages.get(stage, 0)) for stage in config.STAGE_ORDER},
        "n_fechados": len(closed),
        "n_abertos": int(deals["is_open"].sum()),
        "win_rate_fechados": closed["won"].mean(),
        "engajamento_primeiro": deals["engage_date"].min(),
        "engajamento_ultimo": deals["engage_date"].max(),
        "fechamento_primeiro": deals["close_date"].min(),
        "fechamento_ultimo": deals["close_date"].max(),
    }


def _products(deals: pd.DataFrame, closed: pd.DataFrame) -> dict:
    all_counts = _by_count(deals["product"])
    closed_counts = _by_count(closed["product"])
    prices = deals.drop_duplicates("product").set_index("product")["sales_price"].sort_index()
    top_price_product = str(prices.idxmax())
    won = closed[closed["won"] == 1]
    revenue = won.groupby("product")["close_value"].sum().sort_index()
    share = (revenue / revenue.sum()).sort_values(ascending=False, kind="stable")
    ranking = list(all_counts)
    return {
        "deals_por_produto": all_counts,
        "deals_fechados_por_produto": closed_counts,
        "produto_com_mais_deals": ranking[0],
        "segundo_produto_em_deals": ranking[1],
        "preco_de_tabela_por_produto": prices.to_dict(),
        "produto_maior_preco": top_price_product,
        "preco_maximo": int(prices.max()),
        "preco_minimo": int(prices.min()),
        "deals_fechados_do_produto_maior_preco": closed_counts[top_price_product],
        "receita_ganha_share_por_produto": share.to_dict(),
        "receita_ganha_top3_produtos": list(share.index[:3]),
        "receita_ganha_top3_share": share.iloc[:3].sum(),
    }


def _quality(raw: dict, deals: pd.DataFrame) -> dict:
    pipeline, accounts = raw["pipeline"], raw["accounts"]
    wrong_names = {old: int((pipeline["product"] == old).sum()) for old in config.PRODUCT_NAME_MAP}
    typo_accounts = accounts.loc[accounts["sector"].isin(config.SECTOR_MAP), "account"]
    no_account = deals[~deals["has_account"]]
    return {
        "linhas_do_pipeline": len(pipeline),
        "linhas_apos_o_join": len(deals),
        "linhas_com_nome_de_produto_errado": wrong_names,
        "linhas_gtxpro": wrong_names.get("GTXPro", 0),
        "produtos_fora_do_catalogo": sorted(set(pipeline["product"]) - set(raw["products"]["product"])),
        "contas_com_setor_technolgy": len(typo_accounts),
        "deals_de_contas_com_setor_technolgy": int(pipeline["account"].isin(typo_accounts).sum()),
        "sem_conta": {
            "total": len(no_account),
            "por_estagio": {s: int((no_account["deal_stage"] == s).sum()) for s in config.STAGE_ORDER},
            "fechados": int(no_account["deal_stage"].isin(config.CLOSED_STAGES).sum()),
            "pct_dos_abertos": len(no_account) / int(deals["is_open"].sum()),
        },
        "prospecting_sem_engage_date": int(
            ((deals["deal_stage"] == "Prospecting") & deals["engage_date"].isna()).sum()
        ),
        "engaging_sem_engage_date": int(
            ((deals["deal_stage"] == "Engaging") & deals["engage_date"].isna()).sum()
        ),
    }


def _cycles(closed: pd.DataFrame) -> dict:
    won, lost = closed[closed["won"] == 1], closed[closed["won"] == 0]
    max_by_engage_quarter = closed.groupby(closed["engage_date"].dt.to_period("Q"))["cycle_days"].max()
    return {
        "ciclo_maximo_fechados": int(closed["cycle_days"].max()),
        "ciclo_mediano_ganhos": won["cycle_days"].median(),
        "ciclo_mediano_perdidos": lost["cycle_days"].median(),
        "ciclo_p90_ganhos": won["cycle_days"].quantile(0.9),
        "ciclo_rapido_dias": config.FAST_CYCLE_DAYS,
        "perdidos_total": len(lost),
        "perdidos_ciclo_rapido": int((lost["cycle_days"] <= config.FAST_CYCLE_DAYS).sum()),
        "ciclo_maximo_por_trimestre_de_engajamento": {
            _quarter(q): int(v) for q, v in max_by_engage_quarter.items()
        },
    }


def _attributes(closed: pd.DataFrame) -> dict:
    """Quanto cada atributo separa ganho e perda (win rate, qui-quadrado, AUC)."""
    size_quartile = pd.qcut(closed["employees"], 4, labels=["q1_menores", "q2", "q3", "q4_maiores"])
    win_rates = {
        "produto": closed.groupby("product")["won"].mean(),
        "setor": closed.groupby("sector")["won"].mean(),
        "regiao": closed.groupby("regional_office")["won"].mean(),
        "manager": closed.groupby("manager")["won"].mean(),
        "porte_quartil_de_funcionarios": closed.groupby(size_quartile, observed=True)["won"].mean(),
    }
    win_rates = {
        name: {str(k): float(v) for k, v in series.sort_index().items()} for name, series in win_rates.items()
    }
    all_rates = [v for table in win_rates.values() for v in table.values()]
    agent_rates = closed.groupby("sales_agent")["won"].mean()

    p_values = {}
    for column, key in [("product", "produto"), ("sales_agent", "vendedor")]:
        p_values[key] = chi2_contingency(pd.crosstab(closed[column], closed["won"]))[1]

    half = np.where(closed["engage_date"] < "2017-07-01", "H1", "H2")
    by_half = closed.assign(half=half).groupby(["sales_agent", "half"])["won"].mean().unstack().dropna()

    scored = closed.dropna(subset=["cycle_days", "revenue"])
    numeric_auc = {
        col: _auc(scored[col].values, scored["won"].values)
        for col in ["sales_price", "revenue", "employees", "year_established"]
    }
    target_encoding_auc = {}
    for col in ["product", "sector", "sales_agent", "manager", "regional_office", "office_location"]:
        encoded = scored.groupby(col)["won"].transform("mean")  # na própria amostra: otimista
        target_encoding_auc[col] = _auc(encoded.values, scored["won"].values)

    return {
        "win_rate_por_atributo": win_rates,
        "win_rate_atributos_minimo": min(all_rates),
        "win_rate_atributos_maximo": max(all_rates),
        "n_vendedores_com_fechados": len(agent_rates),
        "win_rate_vendedor_minimo": agent_rates.min(),
        "win_rate_vendedor_maximo": agent_rates.max(),
        "qui_quadrado_p": p_values,
        "correlacao_vendedor_h1_h2": by_half["H1"].corr(by_half["H2"]),
        "auc_numericas": numeric_auc,
        "auc_ciclo_dos_fechados": _auc(scored["cycle_days"].values, scored["won"].values),
        "auc_categoricas_target_encoding_na_amostra_inflado": target_encoding_auc,
    }


def _age_bands(deals: pd.DataFrame, max_cycle: int) -> dict:
    """Engaging abertos na data de referência por faixa de idade (as faixas do briefing)."""
    engaging = deals[(deals["deal_stage"] == "Engaging") & deals["age_days"].notna()]
    age, fresh = engaging["age_days"], config.BRIEFING_FRESH_DAYS
    masks = {
        "ate_limite_fresco": age <= fresh,
        "entre_limite_fresco_e_ciclo_maximo": (age > fresh) & (age <= max_cycle),
        "acima_do_ciclo_maximo": age > max_cycle,
    }
    total_value = engaging["sales_price"].sum()
    return {
        "limite_fresco_dias": fresh,
        "ciclo_maximo_dias": max_cycle,
        "engaging_total": len(engaging),
        "valor_tabela_engaging": total_value,
        "faixas": {
            name: {
                "n": int(mask.sum()),
                "pct": _share(mask),
                "valor_tabela": engaging.loc[mask, "sales_price"].sum(),
                "pct_do_valor": engaging.loc[mask, "sales_price"].sum() / total_value,
            }
            for name, mask in masks.items()
        },
    }


def _prospecting(deals: pd.DataFrame) -> dict:
    prospecting = deals[deals["deal_stage"] == "Prospecting"]
    return {
        "n": len(prospecting),
        "valor_tabela": prospecting["sales_price"].sum(),
        "n_por_produto": _by_count(prospecting["product"]),
        "n_sem_conta": int((~prospecting["has_account"]).sum()),
    }


def _snapshot_table(deals: pd.DataFrame, date) -> dict:
    """Foto do pipeline numa data passada: deals abertos naquele dia e seu desfecho final."""
    day = pd.Timestamp(date)
    open_then = (
        deals["engage_date"].notna()
        & (deals["engage_date"] <= day)
        & (deals["close_date"].isna() | (deals["close_date"] > day))
    )
    snap = deals[open_then]
    age = (day - snap["engage_date"]).dt.days
    edges = config.SNAPSHOT_AGE_BINS
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        group = snap[(age > lo) & (age <= hi)]
        won = int((group["deal_stage"] == "Won").sum())
        lost = int((group["deal_stage"] == "Lost").sum())
        n = len(group)
        rows.append(
            {
                "idade_min": lo + 1,
                "idade_max": hi,
                "n": n,
                "ganhos": won,
                "perdidos": lost,
                "abertos_no_fim": n - won - lost,
                "win_rate_se_fechou": won / (won + lost) if won + lost else None,
                "pct_abertos_no_fim": (n - won - lost) / n if n else None,
                "pct_ganhos": won / n if n else None,
            }
        )
    return {"data": day, "n_abertos": len(snap), "faixas": rows}


# --- investigação 2a: win rate de 82% no 1º trimestre de 2017 ---------------------------------
def _stats(group: pd.DataFrame) -> dict:
    return {
        "n": len(group),
        "win_rate": group["won"].mean(),
        "ciclo_mediano": group["cycle_days"].median(),
        "ciclo_min": int(group["cycle_days"].min()),
        "pct_ciclo_rapido": _share(group["cycle_days"] <= config.FAST_CYCLE_DAYS),
    }


def _evidence_2a(closed: pd.DataFrame) -> dict:
    first_close, last_close = closed["close_date"].min(), closed["close_date"].max()
    first_month, first_quarter = first_close.to_period("M"), first_close.to_period("Q")
    close_month = closed["close_date"].dt.to_period("M")
    close_quarter = closed["close_date"].dt.to_period("Q")
    engage_quarter = closed["engage_date"].dt.to_period("Q")

    by_month = [{"mes": str(m), **_stats(g)} for m, g in closed.groupby(close_month)]
    by_quarter = [{"trimestre": _quarter(q), **_stats(g)} for q, g in closed.groupby(close_quarter)]
    by_position = [
        {"mes_do_trimestre": int(k), **_stats(g)}
        for k, g in closed.groupby((closed["close_date"].dt.month - 1) % 3 + 1)
    ]

    cohorts = []
    for month, group in closed.groupby(closed["engage_date"].dt.to_period("M")):
        month_end = month.end_time.normalize()
        floor = (first_close - month_end).days if month_end < first_close else None
        stats = _stats(group)
        cohorts.append(
            {
                "mes": str(month),
                "n_fechados": stats["n"],
                "win_rate": stats["win_rate"],
                "ciclo_min": stats["ciclo_min"],
                "piso_do_recorte_dias": floor,
                "folga_dias": None if floor is None else stats["ciclo_min"] - floor,
                "pct_ciclo_rapido": stats["pct_ciclo_rapido"],
            }
        )

    lag = _quarter_index(closed["close_date"]) - _quarter_index(closed["engage_date"])
    crosstab = pd.crosstab(engage_quarter.map(_quarter), close_quarter.map(_quarter))
    crosstab_dict = {
        row: {col: int(n) for col, n in crosstab.loc[row].items() if n > 0} for row in crosstab.index
    }

    # Critério de decisão (definido antes de olhar o resultado, ver docs/DATA_QUALITY.md)
    q1 = closed[close_quarter == first_quarter]
    outside_first_month = int((q1["close_date"].dt.to_period("M") != first_month).sum())
    month_rates = {row["mes"]: row["win_rate"] for row in by_month}
    quarter_end_months = [
        m for m in month_rates if pd.Period(m).month % 3 == 0 and pd.Period(m) != first_month
    ]
    reference_rate = float(np.mean([month_rates[m] for m in quarter_end_months]))
    diff_pp = (month_rates[str(first_month)] - reference_rate) * 100
    gaps = [c["folga_dias"] for c in cohorts if c["folga_dias"] is not None]
    cond_1 = outside_first_month == 0
    cond_2 = abs(diff_pp) <= config.Q1_MARCH_TOLERANCE_PP
    cond_3 = max(gaps) <= config.TRUNCATION_GAP_DAYS

    first_quarter_rate = float(q1["won"].mean())
    after = closed[close_quarter != first_quarter]
    fast = closed["cycle_days"] <= config.FAST_CYCLE_DAYS
    return {
        "primeiro_fechamento": first_close,
        "ultimo_fechamento": last_close,
        "primeiro_engajamento_dos_fechados": closed["engage_date"].min(),
        "primeiro_trimestre": _quarter(first_quarter),
        "primeiro_mes_com_fechamento": str(first_month),
        "win_rate_primeiro_trimestre": first_quarter_rate,
        "win_rate_depois_do_primeiro_trimestre": after["won"].mean(),
        "por_mes_de_fechamento": by_month,
        "por_trimestre_de_fechamento": by_quarter,
        "por_mes_dentro_do_trimestre": by_position,
        "pct_fechamentos_rapidos_no_1o_mes_do_trimestre": float(
            (fast & (((closed["close_date"].dt.month - 1) % 3) == 0)).sum() / fast.sum()
        ),
        "por_coorte_de_engajamento": cohorts,
        "cruzamento_trimestre_engajamento_x_fechamento": crosstab_dict,
        "fechados_no_mesmo_trimestre": int((lag == 0).sum()),
        "fechados_no_trimestre_seguinte": int((lag == 1).sum()),
        "fechados_fora_da_regra_q_q1": int((~lag.isin([0, 1])).sum()),
        "criterio": {
            "c1_fechamentos_do_1o_trimestre_fora_do_1o_mes": outside_first_month,
            "c1_vale": cond_1,
            "c2_win_rate_do_1o_mes": month_rates[str(first_month)],
            "c2_media_dos_meses_de_fim_de_trimestre": reference_rate,
            "c2_meses_de_fim_de_trimestre": quarter_end_months,
            "c2_diferenca_pp": diff_pp,
            "c2_tolerancia_pp": config.Q1_MARCH_TOLERANCE_PP,
            "c2_vale": cond_2,
            "c3_maior_folga_dias": max(gaps),
            "c3_tolerancia_dias": config.TRUNCATION_GAP_DAYS,
            "c3_coortes_avaliadas": len(gaps),
            "c3_vale": cond_3,
            # Reforço sem tolerância: coortes que o recorte impede de fechar rápido (piso >= 14 dias)
            # contra coortes sem recorte, onde o fechamento rápido é comum.
            "c3_pct_ciclo_rapido_coortes_com_piso_alto": max(
                c["pct_ciclo_rapido"]
                for c in cohorts
                if c["piso_do_recorte_dias"] is not None and c["piso_do_recorte_dias"] >= config.FAST_CYCLE_DAYS
            ),
            "c3_pct_ciclo_rapido_coortes_sem_recorte_minimo": min(
                c["pct_ciclo_rapido"] for c in cohorts if c["piso_do_recorte_dias"] is None
            ),
            "artefato_de_recorte": cond_1 and cond_2 and cond_3,
        },
    }


# --- investigação 2b: vendedores sem deals ---------------------------------------------------
def _evidence_2b(raw: dict, deals: pd.DataFrame) -> dict:
    teams = raw["sales_teams"]
    with_deals = set(deals["sales_agent"])
    with_open = set(deals.loc[deals["is_open"], "sales_agent"])

    def people(mask) -> list[dict]:
        rows = teams[mask].sort_values("sales_agent")
        return rows[["sales_agent", "manager", "regional_office"]].to_dict("records")

    no_deals = people(~teams["sales_agent"].isin(with_deals))
    only_closed = people(teams["sales_agent"].isin(with_deals - with_open))
    managers_with_missing = sorted({row["manager"] for row in no_deals})
    return {
        "vendedores_cadastro": len(teams),
        "vendedores_com_deals": len(with_deals),
        "vendedores_sem_deals": len(no_deals),
        "vendedores_com_deals_abertos": len(with_open),
        "vendedores_com_engaging": int(deals.loc[deals["deal_stage"] == "Engaging", "sales_agent"].nunique()),
        "vendedores_so_com_fechados": len(only_closed),
        "managers": int(teams["manager"].nunique()),
        "regioes": int(teams["regional_office"].nunique()),
        "sem_deals": no_deals,
        "so_com_fechados": only_closed,
        "managers_com_vendedor_sem_deals": managers_with_missing,
        "managers_sem_vendedor_sem_deals": sorted(set(teams["manager"]) - set(managers_with_missing)),
    }


# --- investigação 2c: close_value x preço de tabela ------------------------------------------
def _ratio_stats(ratio: pd.Series) -> dict:
    return {
        "n": len(ratio),
        "media": ratio.mean(),
        "mediana": ratio.median(),
        "p5": ratio.quantile(0.05),
        "p95": ratio.quantile(0.95),
        "min": ratio.min(),
        "max": ratio.max(),
    }


def _evidence_2c(closed: pd.DataFrame) -> dict:
    won, lost = closed[closed["won"] == 1].copy(), closed[closed["won"] == 0]
    won["ratio"] = won["close_value"] / won["sales_price"]
    by_product = {p: _ratio_stats(g["ratio"]) for p, g in won.groupby("product")}
    by_quarter = {
        _quarter(q): _ratio_stats(g["ratio"]) for q, g in won.groupby(won["close_date"].dt.to_period("Q"))
    }
    product_means = [v["media"] for v in by_product.values()]
    quarter_means = [v["media"] for v in by_quarter.values()]
    low, high = config.RATIO_MEAN_RANGE
    quarter_spread_pp = (max(quarter_means) - min(quarter_means)) * 100
    range_ok = bool(min(product_means) >= low and max(product_means) <= high)
    spread_ok = bool(quarter_spread_pp <= config.RATIO_QUARTER_MAX_PP)
    return {
        "geral": _ratio_stats(won["ratio"]),
        "por_produto": by_product,
        "por_trimestre_de_fechamento": by_quarter,
        "perdidos_n": len(lost),
        "perdidos_com_close_value_zero": int((lost["close_value"] == 0).sum()),
        "ganhos_com_close_value_zero": int((won["close_value"] == 0).sum()),
        "criterio": {
            "media_por_produto_minima": min(product_means),
            "media_por_produto_maxima": max(product_means),
            "faixa_aceita_min": low,
            "faixa_aceita_max": high,
            "faixa_vale": range_ok,
            "variacao_entre_trimestres_pp": quarter_spread_pp,
            "variacao_aceita_pp": config.RATIO_QUARTER_MAX_PP,
            "variacao_vale": spread_ok,
            "preco_de_tabela_serve_como_valor_do_deal_aberto": range_ok and spread_ok,
        },
    }


# --- montagem e gravação ------------------------------------------------------------------------
def build_facts(raw: dict, deals: pd.DataFrame, reference_date) -> dict:
    """Calcula todos os fatos a partir dos CSVs brutos (`raw`) e dos deals já limpos (`deals`)."""
    closed = deals[deals["deal_stage"].isin(config.CLOSED_STAGES)].copy()
    closed["won"] = (closed["deal_stage"] == "Won").astype(int)
    max_cycle = int(closed["cycle_days"].max())
    facts = {
        "meta": {"reference_date": pd.Timestamp(reference_date)},
        "pipeline": _pipeline(deals, closed),
        "produtos": _products(deals, closed),
        "qualidade": _quality(raw, deals),
        "ciclos": _cycles(closed),
        "atributos": _attributes(closed),
        "idade_hoje": _age_bands(deals, max_cycle),
        "prospecting": _prospecting(deals),
        "fotos_do_briefing": {str(d): _snapshot_table(deals, d) for d in config.SNAPSHOT_DATES},
        "evidencia_2a_q1": _evidence_2a(closed),
        "evidencia_2b_vendedores": _evidence_2b(raw, deals),
        "evidencia_2c_close_value": _evidence_2c(closed),
    }
    return to_jsonable(facts)


def write_facts(raw: dict, deals: pd.DataFrame, reference_date, path=None) -> Path:
    """Grava `facts.json` (UTF-8, LF, sem timestamp: bytes iguais a cada execução)."""
    path = Path(path or config.FACTS_JSON)
    text = json.dumps(build_facts(raw, deals, reference_date), ensure_ascii=False, indent=2) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return path


def load_facts(path=None) -> dict:
    with open(path or config.FACTS_JSON, encoding="utf-8") as handle:
        return json.load(handle)

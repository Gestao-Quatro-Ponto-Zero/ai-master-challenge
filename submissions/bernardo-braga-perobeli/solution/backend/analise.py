"""
Módulo de análise diagnóstica do Dataset 1 (customer_support_tickets.csv).
Retorna estatísticas pré-computadas para o frontend.
"""

import pandas as pd
from functools import lru_cache
from config import DATASET1_PATH


@lru_cache(maxsize=1)
def carregar_diagnostico() -> dict:
    df = pd.read_csv(DATASET1_PATH)
    df["First Response Time"] = pd.to_datetime(df["First Response Time"], errors="coerce")
    df["Time to Resolution"] = pd.to_datetime(df["Time to Resolution"], errors="coerce")

    fechados = df[df["Ticket Status"] == "Closed"].copy()
    fechados["horas_resolucao"] = (
        (fechados["Time to Resolution"] - fechados["First Response Time"]).dt.total_seconds() / 3600
    ).abs()

    def agg_mean(group_df: pd.DataFrame, group_col: str, value_col: str) -> dict:
        return group_df.groupby(group_col)[value_col].mean().round(2).to_dict()

    def agg_count(series: pd.Series) -> dict:
        return series.value_counts().to_dict()

    media_horas = fechados["horas_resolucao"].mean()
    tickets_ano = 30000
    custo_hora = 30
    pct_auto = 0.28
    automatizaveis = int(tickets_ano * pct_auto)
    proj_hours_yr = tickets_ano * media_horas
    custo_atual_yr = proj_hours_yr * custo_hora
    horas_econ = proj_hours_yr * pct_auto
    custo_econ = custo_atual_yr * pct_auto

    return {
        "total_tickets": int(len(df)),
        "tickets_fechados": int(len(fechados)),
        "satisfacao_media": round(float(fechados["Customer Satisfaction Rating"].mean()), 2),
        "tempo_medio_resolucao_horas": round(float(media_horas), 2),
        "tempo_por_canal": agg_mean(fechados, "Ticket Channel", "horas_resolucao"),
        "tempo_por_tipo": agg_mean(fechados, "Ticket Type", "horas_resolucao"),
        "tempo_por_prioridade": agg_mean(fechados, "Ticket Priority", "horas_resolucao"),
        "satisfacao_por_canal": agg_mean(fechados, "Ticket Channel", "Customer Satisfaction Rating"),
        "satisfacao_por_prioridade": agg_mean(fechados, "Ticket Priority", "Customer Satisfaction Rating"),
        "distribuicao_tipo": agg_count(df["Ticket Type"]),
        "distribuicao_prioridade": agg_count(df["Ticket Priority"]),
        "desperdicio": {
            "tickets_automatizaveis_ano": automatizaveis,
            "horas_economizadas_ano": round(float(horas_econ), 0),
            "economia_estimada_ano": round(float(custo_econ), 0),
        },
    }

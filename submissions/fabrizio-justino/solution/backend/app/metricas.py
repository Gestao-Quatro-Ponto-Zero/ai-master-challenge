"""Métricas por vendedor que alimentam a aba Time, os alertas de manager e o modo
emergência: meta/ritmo do trimestre, cobertura de pipeline, velocidade, capacidade ×
carga e qualidade de dado."""
from dataclasses import dataclass

import pandas as pd

from . import config
from .dados import Dados


@dataclass
class Trimestre:
    inicio: pd.Timestamp
    fim: pd.Timestamp
    dias_total: int
    dias_decorridos: int
    dias_restantes: int

    @property
    def pct_decorrido(self) -> float:
        return self.dias_decorridos / self.dias_total

    def como_dict(self) -> dict:
        return {
            "inicio": self.inicio.date().isoformat(), "fim": self.fim.date().isoformat(),
            "dias_total": self.dias_total, "dias_decorridos": self.dias_decorridos,
            "dias_restantes": self.dias_restantes, "pct_decorrido": round(self.pct_decorrido, 3),
        }


def trimestre(t: pd.Timestamp) -> Trimestre:
    inicio = t.to_period("Q").start_time.normalize()
    fim = t.to_period("Q").end_time.normalize()
    total = (fim - inicio).days + 1
    decorridos = (t.normalize() - inicio).days + 1
    return Trimestre(inicio, fim, total, decorridos, total - decorridos)


def _media_trimestral(ganhos: pd.DataFrame, tri: Trimestre, primeiro_fechamento: pd.Timestamp) -> pd.Series:
    """Média de valor fechado por trimestre COMPLETO antes do atual. Trimestres que
    começam antes do primeiro fechamento do dataset ficam de fora (o Q1/2017 só tem
    março — contar ele derrubaria a média artificialmente)."""
    atual = tri.inicio.to_period("Q")
    tri_validos = [
        q for q in pd.period_range(primeiro_fechamento.to_period("Q"), atual, freq="Q")
        if q < atual and q.start_time >= primeiro_fechamento.normalize()
    ]
    if not tri_validos:
        return pd.Series(dtype=float)
    g = ganhos[ganhos.close_date.dt.to_period("Q").isin(tri_validos)]
    return g.groupby("sales_agent").close_value.sum() / len(tri_validos)


def calcular(dados: Dados, deals: pd.DataFrame, bm) -> pd.DataFrame:
    """1 linha por vendedor do time (inclusive quem não tem deal aberto)."""
    t = dados.data_referencia
    tri = trimestre(t)
    f = dados.fechados
    ganhos = f[f.ganhou == 1]
    primeiro = dados.pipeline.close_date.min()

    m = dados.times.rename(columns={"sales_agent": "agente", "regional_office": "regiao"}).set_index("agente")

    media = _media_trimestral(ganhos, tri, primeiro)
    # Sem trimestre completo no histórico → sem meta (NaN). Com histórico, vendedor
    # que não fechou nada tem média 0 — e meta indefinida (NaN), não 0.
    m["media_trimestral"] = media.reindex(m.index).fillna(0) if len(media) else float("nan")
    m["meta"] = (m.media_trimestral * config.META_FATOR).where(m.media_trimestral > 0)
    m["fechado_trimestre"] = ganhos[ganhos.close_date >= tri.inicio].groupby("sales_agent").close_value.sum().reindex(m.index).fillna(0)
    m["pct_meta"] = m.fechado_trimestre / m.meta
    m["pct_trimestre"] = tri.pct_decorrido

    vivos = deals[~deals.fora_do_ciclo] if not deals.empty else deals
    por_agente = vivos.groupby("agente") if not vivos.empty else None
    m["valor_ponderado"] = por_agente.valor_esperado.sum().reindex(m.index).fillna(0) if por_agente is not None else 0.0
    # Projeção: fechado + valor esperado (chance de ganhar ATÉ O FIM DO TRIMESTRE) do
    # que está em Engaging — Prospecting ainda nem engajou, não fecha a tempo
    cabem = vivos[vivos.stage == "Engaging"] if not vivos.empty else vivos
    m["valor_esperado_trimestre"] = (cabem.groupby("agente").valor_esperado_trimestre.sum().reindex(m.index).fillna(0)
                                     if not cabem.empty else 0.0)
    m["projecao"] = m.fechado_trimestre + m.valor_esperado_trimestre
    # Cobertura do que FALTA: valor esperado até o fim do trimestre ÷ (meta − fechado).
    # Abaixo de 1× = nem fechando o provável a meta é batida. Meta já batida → sem cobertura
    # (NaN). Dividir pela média de um trimestre inteiro dava ~0,2× para todos no fim do
    # trimestre, porque o valor esperado só conta o que fecha até o fechamento.
    m["falta"] = (m.meta - m.fechado_trimestre).clip(lower=0)
    m["cobertura"] = m.valor_esperado_trimestre / m.falta.where(m.falta > 0)

    # Velocidade: ciclo mediano dos ganhos do vendedor vs mediana do time
    ciclo_agente = ganhos.groupby("sales_agent").duracao_dias.median()
    m["ciclo_mediano"] = ciclo_agente.reindex(m.index)
    m["ciclo_vs_time"] = m.ciclo_mediano - float(ganhos.duracao_dias.median())

    # Capacidade (lei de Little): quantos deals o vendedor costuma carregar =
    # throughput (fechados/dia nos últimos N dias) × ciclo médio dele. Carga acima
    # disso = deal esperando na fila e esfriando.
    janela = f[f.close_date > t - pd.Timedelta(days=config.JANELA_THROUGHPUT_DIAS)]
    throughput_dia = janela.groupby("sales_agent").size() / config.JANELA_THROUGHPUT_DIAS
    ciclo_medio = f.groupby("sales_agent").duracao_dias.mean()
    m["throughput_mes"] = (throughput_dia * 30).reindex(m.index).fillna(0).round(1)
    m["capacidade"] = (throughput_dia * ciclo_medio).reindex(m.index).fillna(0).round(1)
    engaging_vivos = cabem.groupby("agente").size() if not cabem.empty else pd.Series(dtype=int)
    m["carga"] = engaging_vivos.reindex(m.index).fillna(0).astype(int)
    m["carga_total"] = (deals[deals.stage == "Engaging"].groupby("agente").size().reindex(m.index).fillna(0).astype(int)
                        if not deals.empty else 0)
    m["carga_rel"] = m.carga / m.capacidade.where(m.capacidade > 0)

    # Qualidade de dado: quem deixa muito deal sem conta tem o forecast menos confiável
    if not deals.empty:
        abertos = deals.groupby("agente")
        m["deals_abertos"] = abertos.size().reindex(m.index).fillna(0).astype(int)
        m["pct_sem_conta"] = abertos.conta.apply(lambda c: c.isna().mean()).reindex(m.index)
        m["n_atacar"] = deals[deals.acao == "Atacar agora"].groupby("agente").size().reindex(m.index).fillna(0).astype(int)
    else:
        m["deals_abertos"], m["pct_sem_conta"], m["n_atacar"] = 0, None, 0

    return m.reset_index()

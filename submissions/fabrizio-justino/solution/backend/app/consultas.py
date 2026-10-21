"""Consultas sobre uma Visao (uma data) — usadas pela API (main.py), pelas ferramentas
da IA (ia.py) e pelos e-mails (emails.py). Um lugar só para a regra de cada consulta."""
from typing import Optional

import pandas as pd

from . import alertas as alertas_mod
from . import config, emergencia as emergencia_mod
from .motor import Visao, registros
from .scoring import ORDEM_ACOES, horizonte

# Colunas leves para listas (sem motivos/alertas)
COLUNAS_RESUMO = ["opportunity_id", "agente", "conta", "produto", "stage", "idade_dias", "score",
                  "acao", "probabilidade", "valor", "valor_liquido", "valor_esperado",
                  "prob_trimestre", "valor_esperado_trimestre"]


class FiltroInvalido(ValueError):
    """Filtro com valor que não existe — a API transforma em 400."""


def _filtrar(df: pd.DataFrame, **filtros) -> pd.DataFrame:
    for coluna, valor in filtros.items():
        if valor:
            if coluna not in df.columns or valor not in set(df[coluna].dropna()):
                raise FiltroInvalido(f"Valor desconhecido para '{coluna}': {valor}")
            df = df[df[coluna] == valor]
    return df


def recorte(v: Visao, agente=None, manager=None, regiao=None, stage=None, acao=None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(deals, métricas) do recorte. Filtros de pessoa validam contra o time inteiro
    (vendedor sem deal aberto é válido); stage/ação só se aplicam aos deals."""
    met = _filtrar(v.metricas, agente=agente, manager=manager, regiao=regiao)
    deals = v.deals[v.deals.agente.isin(met.agente)]
    for coluna, valor in (("stage", stage), ("acao", acao)):
        if valor:
            if valor not in ({"Prospecting", "Engaging"} if coluna == "stage" else set(ORDEM_ACOES)):
                raise FiltroInvalido(f"Valor desconhecido para '{coluna}': {valor}")
            deals = deals[deals[coluna] == valor]
    return deals, met


def pipeline(v: Visao, limite: int = 200, colunas: Optional[list] = None, **filtros) -> dict:
    df, _ = recorte(v, **filtros)
    por_acao = df.groupby("acao").agg(n=("opportunity_id", "count"), valor=("valor", "sum"), esperado=("valor_esperado", "sum"))
    hz = horizonte(v.data)
    return {
        "data_referencia": v.data.date().isoformat(),
        "horizonte": {"fim": hz.fim.date().isoformat(), "dias": hz.dias},
        "resumo": {
            "total": len(df),
            "valor_total": float(df.valor.sum()),
            "valor_esperado_total": float(df.valor_esperado.sum()),
            "por_acao": {a: {"n": int(r.n), "valor": float(r.valor), "valor_esperado": float(r.esperado)}
                         for a, r in por_acao.iterrows()},
        },
        "deals": registros(df.head(limite)[colunas] if colunas else df.head(limite)),
    }


def deal(v: Visao, opportunity_id: str) -> Optional[dict]:
    df = v.deals[v.deals.opportunity_id == opportunity_id]
    return registros(df)[0] if len(df) else None


def alertas(v: Visao, severidade: Optional[str] = None, agente=None, manager=None, regiao=None, stage=None) -> dict:
    if severidade and severidade not in alertas_mod.ORDEM_SEVERIDADE:
        raise FiltroInvalido("severidade deve ser critico, atencao ou lembrete.")
    deals, met = recorte(v, agente, manager, regiao, stage)
    emerg = emergencia_mod.avaliar(deals, met, v.trimestre)
    time = alertas_mod.ordenar(alertas_mod.gerar_lembretes_time(deals, met, emerg, v.bm))
    fila = [a for lista in deals.alertas for a in lista if a["na_fila"]]
    todos = alertas_mod.ordenar(time + fila)
    contagem = {s: sum(1 for a in todos if a["severidade"] == s) for s in alertas_mod.ORDEM_SEVERIDADE}
    if severidade:
        todos = [a for a in todos if a["severidade"] == severidade]
    return {"contagem": contagem, "time": time, "alertas": todos}


def emergencia(v: Visao, agente=None, manager=None, regiao=None) -> dict:
    deals, met = recorte(v, agente, manager, regiao)
    r = emergencia_mod.avaliar(deals, met, v.trimestre)
    r["resgate"]["deals"] = registros(r["resgate"]["deals"][COLUNAS_RESUMO])
    r["janela_dias"] = config.JANELA_EMERGENCIA_DIAS
    r["meta_fator"] = config.META_FATOR
    return r


def time(v: Visao, agente=None, manager=None, regiao=None) -> dict:
    _, met = recorte(v, agente, manager, regiao)
    soma = ["meta", "fechado_trimestre", "falta", "valor_esperado_trimestre", "valor_ponderado", "media_trimestral",
            "carga", "capacidade", "deals_abertos", "n_atacar"]
    times = met.groupby(["manager", "regiao"])[soma].sum(min_count=1).reset_index()
    times["pct_meta"] = times.fechado_trimestre / times.meta
    times["cobertura"] = times.valor_esperado_trimestre / times.falta.where(times.falta > 0)
    times["carga_rel"] = times.carga / times.capacidade.where(times.capacidade > 0)
    return {
        "trimestre": v.trimestre.como_dict(),
        "fator_sobrecarga": config.FATOR_SOBRECARGA,
        "vendedores": registros(met.sort_values("pct_meta", na_position="last")),
        "times": registros(times),
    }


def cross_sell(v: Visao, limite: int = 100, agente=None, manager=None, regiao=None) -> dict:
    _, met = recorte(v, agente, manager, regiao)
    cs = v.cross_sell
    if not cs.empty:
        cs = cs[cs.agente.isin(met.agente)]
    return {"total": len(cs), "sugestoes": registros(cs.head(limite))}


def winloss(v: Visao, agente=None, manager=None, regiao=None) -> dict:
    """Ganhos × perdas do trimestre atual até a data, por produto e por vendedor, e
    quanto das perdas morreu na zona de risco. Descritivo (o que aconteceu) — não
    é previsão."""
    _, met = recorte(v, agente, manager, regiao)
    f = v.dados.fechados
    f = f[(f.close_date >= v.trimestre.inicio) & f.sales_agent.isin(met.agente)]

    def tabela(chave: str) -> list[dict]:
        if f.empty:
            return []
        g = f.groupby(chave).agg(ganhos=("ganhou", "sum"), fechados=("ganhou", "size"), valor_ganho=("close_value", "sum"))
        g["perdas"] = g.fechados - g.ganhos
        g["win_rate"] = (g.ganhos / g.fechados).round(3)
        return registros(g.reset_index().rename(columns={chave: "nome"}).sort_values("valor_ganho", ascending=False))

    perdas = f[f.ganhou == 0]
    return {
        "periodo": {"inicio": v.trimestre.inicio.date().isoformat(), "fim": v.data.date().isoformat()},
        "ganhos": int(f.ganhou.sum()),
        "perdas": int(len(perdas)),
        "win_rate": round(float(f.ganhou.mean()), 3) if len(f) else None,
        "valor_ganho": float(f.close_value.sum()),
        "perdas_na_zona_de_risco": int((perdas.duracao_dias <= v.bm.zona_risco_dias).sum()),
        "zona_risco_dias": v.bm.zona_risco_dias,
        "por_produto": tabela("product"),
        "por_vendedor": tabela("sales_agent"),
    }


def benchmarks(v: Visao) -> dict:
    bm, cal = v.bm, v.calibracao
    return {
        "win_rate_geral": bm.win_rate_geral,
        "zona_risco_dias": bm.zona_risco_dias,
        "pct_perdidos_na_zona": bm.pct_perdidos_na_zona,
        "ciclo_max_dias": bm.ciclo_max_dias,
        "ciclo_p75_produto": bm.ciclo_p75_produto,
        "win_fim_trimestre": bm.win_fim_trimestre,
        "win_fora_trimestre": bm.win_fora_trimestre,
        "desconto_produto": bm.desconto_produto,
        "pesos": config.PESOS,
        "limites_acao": {**v.cortes, "percentil_atacar": config.PERCENTIL_ATACAR, "percentil_nutrir": config.PERCENTIL_NUTRIR},
        "calibracao": {
            "calibrada": cal.calibrada, "data_corte": cal.data_corte,
            "curva": cal.curva, "auc": cal.auc, "auc_com_teto": cal.auc_com_teto, "n_observacoes": cal.n_observacoes,
            "data_inicio": cal.datas[0] if cal.datas else None, "data_fim": cal.datas[-1] if cal.datas else None,
            "n_datas": len(cal.datas),
            "zumbis_observados": cal.zumbis_observados, "zumbis_que_ganharam": cal.zumbis_que_ganharam,
        },
    }

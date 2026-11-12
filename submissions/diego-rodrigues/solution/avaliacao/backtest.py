"""Backtest as-of: cinco políticas de ordem, cada uma com a mesma data de corte e o mesmo recorte do produto.

O motor só vê o que `recortar` deixa passar. O desfecho futuro entra apenas aqui, para medir.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from motor.aprender import carga_referencia, datas_analogas, tabela_destino
from motor.carregar import Dados, recortar
from motor.janela import aprender_janela
from motor.pontuar import pontuar

POLITICAS = ("relogio", "preco_prazo", "preco_138", "aleatorio", "oraculo")
RODADAS_ALEATORIO = 200
NUMERO_CONTROLE = 7


def cortes_padrao() -> list[pd.Timestamp]:
    return list(pd.date_range("2017-07-03", "2017-12-03", freq="4W-MON"))


def preparar_corte(dados: Dados, config: dict, corte: pd.Timestamp):
    """Deals não-sem-data em `corte`, com o desfecho dentro do horizonte."""
    r = recortar(dados, corte)
    if not datas_analogas(r, corte):
        return None
    j = aprender_janela(r, config)
    t = tabela_destino(r, j, config, corte)
    c = carga_referencia(r, corte)
    s = pontuar(r, j, t, c, config, corte)
    s = s[s.estado != "sem_data"].copy()

    full = dados.pipeline.set_index("opportunity_id")
    cd = s.opportunity_id.map(full.close_date)
    st = s.opportunity_id.map(full.deal_stage)
    horizonte = pd.Timedelta(days=config["horizonte_dias"])
    s["ganhou"] = ((cd.notna()) & (cd < corte + horizonte) & (st == "Won")).astype(int).values
    s["valor_ganho"] = s.ganhou * s.valor_tabela
    return s, j


def _sorteios(ids: pd.Series, corte: pd.Timestamp) -> pd.DataFrame:
    """Uma coluna por rodada, uma linha por deal. Depende só dos ids e do corte, não da ordem das linhas."""
    ordenados = np.sort(ids.unique())
    rng = np.random.default_rng(int(corte.strftime("%Y%m%d")) + NUMERO_CONTROLE)
    return pd.DataFrame(rng.random((len(ordenados), RODADAS_ALEATORIO)), index=ordenados)


def _topo(df: pd.DataFrame, ordem: list[str], asc: list[bool], k: int) -> pd.DataFrame:
    return df.sort_values(ordem, ascending=asc).groupby("vendedor").head(k)


def _politicas_fixas(s: pd.DataFrame, ciclo_max: int, k: int) -> dict[str, pd.DataFrame]:
    viv = s[s.estado == "vivo"]
    por_idade = s[s.idade <= ciclo_max]
    return {
        "relogio": _topo(viv, ["vendedor", "fila_ordem", "posicao"], [True, True, True], k),
        "preco_prazo": _topo(viv, ["valor_tabela", "dias_restantes", "opportunity_id"], [False, False, True], k),
        "preco_138": _topo(por_idade, ["valor_tabela", "opportunity_id"], [False, True], k),
        "oraculo": _topo(s, ["valor_ganho"], [False], k),
    }


def _aleatorio(s: pd.DataFrame, corte: pd.Timestamp, k: int) -> tuple[float, float]:
    """Média de valor ganho e de acerto sobre as rodadas de sorteio."""
    viv = s[s.estado == "vivo"]
    sorteios = _sorteios(s.opportunity_id, corte)
    valores, acertos = [], []
    for rodada in range(RODADAS_ALEATORIO):
        r = viv.assign(r=sorteios.loc[viv.opportunity_id, rodada].values)
        top = _topo(r, ["r"], [True], k)
        valores.append(top.valor_ganho.sum())
        acertos.append(top.ganhou.mean())
    return float(np.mean(valores)), float(np.mean(acertos))


def backtest(dados: Dados, config: dict, cortes=None, k: int | None = None, detalhado: bool = False) -> pd.DataFrame:
    """Uma linha por corte. Com `detalhado=True`, uma linha por deal escolhido por política determinística.

    O aleatório não entra no detalhado: é uma média de rodadas, não uma escolha.
    """
    cortes = cortes or cortes_padrao()
    k = k or config["foco_por_vendedor"]
    linhas, det = [], []
    for corte in cortes:
        prep = preparar_corte(dados, config, corte)
        if prep is None:
            continue
        s, j = prep
        linha = {
            "corte": str(corte.date()),
            "semana_do_trimestre": int((corte - pd.Timestamp(corte.year, 3 * ((corte.month - 1) // 3) + 1, 1)).days // 7 + 1),
            "vivos": int((s.estado == "vivo").sum()),
            "fila_fechar": int((s.fila == "fechar").sum()),
            "vencidos_ganhos": int(s[s.estado == "vencido"].ganhou.sum()),
        }
        for nome, top in _politicas_fixas(s, j.ciclo_max, k).items():
            linha[f"valor_{nome}"] = int(top.valor_ganho.sum())
            linha[f"acerto_{nome}"] = top.ganhou.mean()
            det.append(pd.DataFrame({
                "corte": str(corte.date()),
                "politica": nome,
                "vendedor": top.vendedor.values,
                "valor_ganho": top.valor_ganho.values,
                "ganhou": top.ganhou.values,
            }))
        valor_medio, acerto_medio = _aleatorio(s, corte, k)
        linha["valor_aleatorio"] = valor_medio
        linha["acerto_aleatorio"] = acerto_medio
        linhas.append(linha)
    if detalhado:
        return pd.concat(det, ignore_index=True)
    return pd.DataFrame(linhas)


def razao_com_ic(det: pd.DataFrame, a: str, b: str, n: int = 5000, controle: int = NUMERO_CONTROLE):
    """Razão de valor ganho a/b e IC 95% por reamostragem de vendedores (a unidade independente)."""
    pv = det.pivot_table(index="vendedor", columns="politica", values="valor_ganho", aggfunc="sum").fillna(0)
    rng = np.random.default_rng(controle)
    reamostras = [
        pv[a].values[i].sum() / pv[b].values[i].sum()
        for i in (rng.integers(0, len(pv), len(pv)) for _ in range(n))
    ]
    return pv[a].sum() / pv[b].sum(), np.percentile(reamostras, 2.5), np.percentile(reamostras, 97.5)

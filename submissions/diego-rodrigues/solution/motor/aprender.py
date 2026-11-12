"""Tabela de destino por faixa de idade, lida das datas análogas de trimestres anteriores."""
from __future__ import annotations

import pandas as pd

from motor.carregar import Dados
from motor.janela import Janela

_CONTAGENS = ["n", "decidiram_28d", "ganharam_28d", "decidiram_trimestre", "ganharam_trimestre"]


def inicio_trimestre(d: pd.Timestamp) -> pd.Timestamp:
    return pd.Timestamp(d.year, 3 * ((d.month - 1) // 3) + 1, 1)


def datas_analogas(dados: Dados, hoje: pd.Timestamp) -> list[pd.Timestamp]:
    """`hoje` menos 3, 6, 9… meses, enquanto não for anterior ao primeiro fechamento conhecido."""
    primeiro = dados.pipeline.close_date.min()
    analogas, x = [], hoje
    while True:
        x = x - pd.DateOffset(months=3)
        if pd.isna(primeiro) or x < primeiro:
            return analogas
        analogas.append(x)


def _faixas(bordas: list[int], ciclo_max: int) -> list[tuple[int, int]]:
    limites = [b for b in bordas if b < ciclo_max] + [ciclo_max]
    lo, faixas = 1, []
    for hi in limites:
        faixas.append((lo, hi))
        lo = hi + 1
    return faixas


def _rotulo(lo: int, hi: int) -> str:
    return f"{lo}-{hi}"


def _abertos_em(dados: Dados, data: pd.Timestamp) -> pd.DataFrame:
    p = dados.pipeline
    p = p[p.engage_date.notna()]
    return p[(p.engage_date < data) & ((p.close_date >= data) | p.close_date.isna())]


def _observacoes(dados: Dados, janela: Janela, config: dict, hoje: pd.Timestamp) -> pd.DataFrame:
    faixas = _faixas(config["bordas_faixa"], janela.ciclo_max)
    blocos = []
    for A in datas_analogas(dados, hoje):
        al = _abertos_em(dados, A).copy()
        al["idade"] = (A - al.engage_date).dt.days
        al = al[al.idade <= janela.ciclo_max]
        decidiu_28 = al.close_date.notna() & (al.close_date < A + pd.Timedelta(days=config["horizonte_dias"]))
        decidiu_tri = al.close_date.notna() & (al.close_date < inicio_trimestre(A) + pd.DateOffset(months=3))
        ganhou = al.deal_stage == "Won"
        al["decidiram_28d"] = decidiu_28.astype(int)
        al["ganharam_28d"] = (decidiu_28 & ganhou).astype(int)
        al["decidiram_trimestre"] = decidiu_tri.astype(int)
        al["ganharam_trimestre"] = (decidiu_tri & ganhou).astype(int)
        blocos.append(al[["idade", "decidiram_28d", "ganharam_28d", "decidiram_trimestre", "ganharam_trimestre"]])
    return pd.concat(blocos) if blocos else pd.DataFrame(columns=["idade"] + _CONTAGENS[1:])


def _agrupar(bruto: pd.DataFrame, n_min: int) -> list[tuple[int, int, pd.Series, bool]]:
    """Junta cada faixa rala à vizinha mais velha; a cauda rala junta-se à anterior."""
    grupos: list[list] = []
    acc, lo, juntou = None, None, False
    for (flo, fhi), linha in bruto.iterrows():
        if acc is None:
            acc, lo, juntou = linha.copy(), flo, False
        else:
            acc, juntou = acc + linha, True
        if acc["n"] >= n_min:
            grupos.append([lo, fhi, acc, juntou])
            acc = None
    if acc is not None:
        if grupos:
            grupos[-1][1] = bruto.index[-1][1]
            grupos[-1][2] = grupos[-1][2] + acc
            grupos[-1][3] = True
        else:
            grupos.append([lo, bruto.index[-1][1], acc, True])
    return [tuple(g) for g in grupos]


def _com_probabilidades(t: pd.DataFrame) -> pd.DataFrame:
    n = t["n"].where(t["n"] > 0)
    t["p_decide"] = (t["decidiram_28d"] / n).fillna(0.0)
    t["p_ganha_28d"] = (t["ganharam_28d"] / n).fillna(0.0)
    t["p_ganha_trimestre"] = (t["ganharam_trimestre"] / n).fillna(0.0)
    return t


def tabela_vazia_para(hoje: pd.Timestamp, rotulos: list[str]) -> pd.DataFrame:
    t = pd.DataFrame(0, index=pd.Index(rotulos), columns=_CONTAGENS)
    t = _com_probabilidades(t)
    t["agrupada"] = True
    t["motivo"] = f"sem data análoga em {hoje.date()}: nenhum trimestre anterior com fechamento conhecido"
    return t


def tabela_destino(dados: Dados, janela: Janela, config: dict, hoje: pd.Timestamp) -> pd.DataFrame:
    faixas = _faixas(config["bordas_faixa"], janela.ciclo_max)
    rotulos = [_rotulo(*f) for f in faixas]
    obs = _observacoes(dados, janela, config, hoje)
    if obs.empty:
        return tabela_vazia_para(hoje, rotulos)

    bruto = pd.DataFrame(0, index=pd.MultiIndex.from_tuples(faixas), columns=_CONTAGENS)
    for lo, hi in faixas:
        sel = obs[(obs.idade >= lo) & (obs.idade <= hi)]
        bruto.loc[(lo, hi), "n"] = len(sel)
        for c in _CONTAGENS[1:]:
            bruto.loc[(lo, hi), c] = int(sel[c].sum())

    grupos = _agrupar(bruto, config["n_min_faixa"])
    t = pd.DataFrame(
        [g[2] for g in grupos],
        index=pd.Index([_rotulo(g[0], g[1]) for g in grupos]),
    ).astype(int)
    t["agrupada"] = [g[3] for g in grupos]
    return _com_probabilidades(t)[_CONTAGENS + ["p_decide", "p_ganha_28d", "p_ganha_trimestre", "agrupada"]]


def carga_referencia(dados: Dados, hoje: pd.Timestamp) -> pd.Series:
    """Mediana, entre as datas análogas, de deals abertos por vendedor que depois fecharam."""
    cs = []
    for A in datas_analogas(dados, hoje):
        viv = _abertos_em(dados, A)
        viv = viv[viv.close_date.notna()]
        cs.append(viv.groupby("sales_agent").size().rename(str(A.date())))
    if not cs:
        return pd.Series(dtype=float)
    return pd.concat(cs, axis=1).fillna(0).median(axis=1)

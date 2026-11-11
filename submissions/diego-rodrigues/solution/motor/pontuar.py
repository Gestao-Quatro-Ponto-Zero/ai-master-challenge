"""Fila, ordem, foco e índice dos deals abertos, a partir da janela e da tabela aprendidas."""
from __future__ import annotations

import numpy as np
import pandas as pd

from motor.aprender import carga_referencia, tabela_destino
from motor.carregar import Dados, recortar
from motor.janela import Janela, aprender_janela, estado, prazo_do_deal

FILA_ORDEM = {"fechar": 0, "preparar": 1, "iniciar": 2, "encerrar": 3}
VERBO = {
    "fechar": "Ligar e propor data de fechamento",
    "preparar": "Avançar uma etapa: próxima reunião ou proposta",
    "iniciar": "Registrar data de engajamento e fazer o primeiro contato",
    "encerrar": "Confirmar ou fechar como perdido no CRM",
}


def _faixa_da_idade(idade: float, rotulos: list[str]) -> str | None:
    for r in rotulos:
        lo, hi = (int(x) for x in r.split("-"))
        if lo <= idade <= hi:
            return r
    return None


def pontuar(
    dados: Dados,
    janela: Janela,
    tabela: pd.DataFrame,
    carga: pd.Series,
    config: dict,
    hoje: pd.Timestamp,
) -> pd.DataFrame:
    op = dados.pipeline[dados.pipeline.close_date.isna()].copy()
    op["vendedor"] = op["sales_agent"]
    op["conta"] = op["account"]
    op["stage"] = op["deal_stage"]
    op["estado"] = estado(op, janela, hoje)

    op["idade"] = (hoje - op.engage_date).dt.days
    prazo = pd.Series(pd.NaT, index=op.index, dtype=op.engage_date.dtype)
    com_data = op.engage_date.notna()
    prazo[com_data] = prazo_do_deal(op.engage_date[com_data], janela)
    op["prazo"] = prazo
    op["dias_restantes"] = (op.prazo - hoje).dt.days

    rotulos = list(tabela.index)
    op["faixa"] = [
        _faixa_da_idade(i, rotulos) if e == "vivo" else None
        for i, e in zip(op.idade, op.estado)
    ]
    for col in ("p_decide", "p_ganha_28d", "p_ganha_trimestre"):
        op[col] = op.faixa.map(tabela[col])

    op["ve_28"] = op.valor_tabela * op.p_ganha_28d
    op["ve_trimestre"] = op.valor_tabela * op.p_ganha_trimestre

    op["fila"] = np.select(
        [op.estado == "sem_data", op.estado == "vencido", op.p_decide >= config["p_decide_min"]],
        ["iniciar", "encerrar", "fechar"],
        "preparar",
    )
    op["fila_ordem"] = op.fila.map(FILA_ORDEM)
    op["chave"] = np.select(
        [op.fila == "fechar", op.fila == "preparar"],
        [op.ve_28, op.ve_trimestre],
        op.valor_tabela,
    )

    op = op.sort_values(
        ["vendedor", "fila_ordem", "chave", "dias_restantes", "opportunity_id"],
        ascending=[True, True, False, True, True],
    )
    op["posicao"] = op.groupby(["vendedor", "fila"]).cumcount() + 1

    rank_foco = op[op.fila != "encerrar"].groupby("vendedor").cumcount() + 1
    op["em_foco"] = op.index.isin(rank_foco[rank_foco <= config["foco_por_vendedor"]].index)

    op["indice"] = np.nan
    viv = op[op.estado == "vivo"]
    if len(viv) > 1:
        indices = []
        for r in viv.itertuples():
            abaixo = (
                (viv.fila_ordem > r.fila_ordem)
                | ((viv.fila_ordem == r.fila_ordem) & (viv.chave < r.chave))
            ).sum()
            indices.append(max(1, round(100 * abaixo / (len(viv) - 1))))
        op.loc[viv.index, "indice"] = indices
    op.loc[op.estado == "vencido", "indice"] = 0

    op["verbo"] = op.fila.map(VERBO)

    return op[[
        "opportunity_id", "vendedor", "gerente", "regiao", "produto", "produto_crm",
        "conta", "setor", "stage", "engage_date", "idade", "faixa", "prazo",
        "dias_restantes", "estado", "p_decide", "valor_tabela", "ve_28", "ve_trimestre",
        "fila", "fila_ordem", "chave", "posicao", "em_foco", "indice", "verbo",
    ]]


def pontuar_em(dados: Dados, config: dict, hoje: pd.Timestamp) -> pd.DataFrame:
    """O que a tela mostraria em `hoje`: o mesmo caminho do produto e do backtest."""
    r = recortar(dados, hoje)
    janela = aprender_janela(r, config)
    tabela = tabela_destino(r, janela, config, hoje)
    carga = carga_referencia(r, hoje)
    return pontuar(r, janela, tabela, carga, config, hoje)

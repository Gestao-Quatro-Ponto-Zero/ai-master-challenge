"""Por que este deal está nesta fila, o que o momento de decisão diz e o que o score não sabe."""
from __future__ import annotations

import pandas as pd

from motor.janela import Janela, prazo_trimestre

NAO_SABE_FIXO = [
    "Não sei o registro de atividade deste deal (ligações, reuniões, e-mails).",
    "Não sei o desconto nem a quantidade negociados.",
    "Não sei o motivo de perda dos deals parecidos.",
]
SEM_CONTA = "Esta oportunidade não tem conta no CRM."
FRASE_VAZIO = (
    "Nenhum deal vivo para este vendedor hoje. Se houver deals em iniciar, "
    "começar por eles; se não houver, a carteira dele está vazia no CRM."
)


def _data(d: pd.Timestamp) -> str:
    return pd.Timestamp(d).strftime("%d/%m/%Y")


def _valor(v: float) -> str:
    return "US$ " + f"{v:,.0f}".replace(",", ".")


def _trimestre(d: pd.Timestamp) -> str:
    return f"{(d.month - 1) // 3 + 1}º trimestre de {d.year}"


def _momento(linha: pd.Series, janela: Janela, t: pd.Series | None) -> str:
    if linha.fila == "fechar":
        pct = round(100 * t.p_decide)
        return (
            "Nas três viradas de trimestre anteriores, cerca de "
            f"{pct} em cada 100 deals nessa idade decidiram nas quatro semanas seguintes."
        )
    if linha.fila == "preparar":
        if t.n == 0:
            return "Não há observação nessa idade para estimar quando este deal decide."
        ate_fim = round(100 * t.decidiram_trimestre / t.n)
        nas_quatro = round(100 * t.decidiram_28d / t.n)
        parte_28 = (
            "nenhum nas próximas quatro semanas" if nas_quatro == 0
            else f"só {nas_quatro} nas próximas quatro semanas"
        )
        return (
            "Nessa idade, deals decidem mais tarde no trimestre: "
            f"{ate_fim} em cada 100 decidiram até o fim dele, mas {parte_28}."
        )
    if linha.fila == "encerrar":
        if linha.idade > janela.ciclo_max:
            return (
                f"Passou do ciclo máximo observado de {janela.ciclo_max} dias "
                f"(engajado em {_data(linha.engage_date)}), por isso está encerrado."
            )
        pt = prazo_trimestre(pd.Series([linha.engage_date])).iloc[0]
        return (
            f"O trimestre em que este deal podia fechar terminou em {_data(pt)} "
            f"({_trimestre(pt)}). O prazo do trimestre venceu antes do ciclo máximo."
        )
    return "Sem data de engajamento: não há como estimar quando este deal decide. O primeiro passo é registrar a data."


def _prazo(linha: pd.Series, janela: Janela) -> str:
    if linha.estado == "sem_data":
        return "Sem data de engajamento, não há prazo."
    if linha.estado == "vencido":
        return "Prazo vencido."
    pelo_trimestre = (
        janela.usa_prazo_trimestre
        and linha.prazo < linha.engage_date + pd.Timedelta(days=janela.ciclo_max)
    )
    limite = "do fim do trimestre" if pelo_trimestre else f"do ciclo de {janela.ciclo_max} dias"
    return f"{int(linha.dias_restantes)} dias até o prazo, pelo limite {limite}."


def _valor_card(linha: pd.Series, carteira: pd.DataFrame) -> str:
    n = int((carteira.fila == linha.fila).sum())
    return (
        f"{_valor(linha.valor_tabela)} de preço de tabela. "
        f"{int(linha.posicao)}º de {n} em {linha.fila} deste vendedor."
    )


def explicar(linha: pd.Series, janela: Janela, tabela: pd.DataFrame, carteira: pd.DataFrame) -> dict:
    t = tabela.loc[linha.faixa] if linha.faixa in tabela.index else None
    nao_sabe = list(NAO_SABE_FIXO)
    if pd.isna(linha.conta):
        nao_sabe.append(SEM_CONTA)
    return {
        "cartoes": {
            "valor": _valor_card(linha, carteira),
            "momento": _momento(linha, janela, t),
            "prazo": _prazo(linha, janela),
        },
        "nao_sabe": nao_sabe,
    }


def resumo_vendedor(vendedor: str, sub: pd.DataFrame, carga: pd.Series) -> dict:
    por_fila = {}
    for f in ("fechar", "preparar", "iniciar", "encerrar"):
        x = sub[sub.fila == f]
        por_fila[f] = {"n": int(len(x)), "valor": float(x.valor_tabela.sum())}
    vivos = int((sub.estado == "vivo").sum())
    return {
        "vivos": vivos,
        "por_fila": por_fila,
        "carga_referencia": float(carga.get(vendedor, 0.0)),
        "frase_vazio": None if vivos > 0 else FRASE_VAZIO,
    }

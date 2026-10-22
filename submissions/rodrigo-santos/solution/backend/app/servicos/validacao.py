"""
Validação da pontuação com o histórico (backtest).

Pergunta: "se a ferramenta existisse no passado, ela teria apontado os
negócios certos?"

Para cada data de corte (config.DATAS_CORTE_VALIDACAO):
  1. Estatísticas calculadas SÓ com negócios fechados antes do corte
     (nada do futuro vaza para o cálculo).
  2. Pontuamos, com a mesma função da tela, os negócios que estavam abertos
     no dia do corte.
  3. Comparamos com o que aconteceu depois: quem ganhou, quem perdeu,
     quanto faturou, e se os "parados" chegaram a fechar.

Também testamos se algum atributo (vendedor, produto, setor, conta...)
prevê quem ganha, usando AUC: 0,5 = sorteio, 1,0 = acerta sempre.

Rodar o relatório completo (dentro de backend/):
    python -m app.servicos.validacao
"""

from functools import lru_cache

import pandas as pd

from app import config
from app.dados.carregador import ETAPA_GANHO, ETAPA_PROSPECCAO, ETAPAS_FECHADAS, carregar_deals
from app.servicos.estatisticas import calcular_estatisticas_de
from app.servicos.pontuacao import PRIORIDADE_ALTA, PRIORIDADE_BAIXA, PRIORIDADE_MEDIA, pontuar

PRIORIDADES = [PRIORIDADE_ALTA, PRIORIDADE_MEDIA, PRIORIDADE_BAIXA]

# Atributos testados como possíveis previsores de vitória: nome amigável -> coluna.
ATRIBUTOS_TESTADOS = {
    "Vendedor": "sales_agent",
    "Gerente": "manager",
    "Escritório regional": "regional_office",
    "Produto": "product",
    "Série do produto": "series",
    "Setor da conta": "sector",
    "Conta": "account",
    "País da conta": "office_location",
    "Porte da conta (receita)": "faixa_receita",
    "Nº de funcionários da conta": "faixa_funcionarios",
    "Vendedor × produto": "vendedor_produto",
}


def calcular_auc(pontuacao: pd.Series, ganho: pd.Series) -> float:
    """
    Área sob a curva ROC: probabilidade de um negócio ganho ter pontuação
    maior que um perdido. 0,5 = não separa nada (sorteio).
    """
    postos = pontuacao.rank()
    ganho = ganho.astype(bool)
    n_ganhos, n_perdidos = ganho.sum(), (~ganho).sum()
    if n_ganhos == 0 or n_perdidos == 0:
        return float("nan")
    return float((postos[ganho].sum() - n_ganhos * (n_ganhos + 1) / 2) / (n_ganhos * n_perdidos))


def _preparar_atributos(deals: pd.DataFrame) -> pd.DataFrame:
    """Cria as colunas derivadas testadas (faixas de porte e combinação vendedor × produto)."""
    deals = deals.copy()
    deals["faixa_receita"] = pd.qcut(deals["revenue"], 4, labels=False, duplicates="drop")
    deals["faixa_funcionarios"] = pd.qcut(deals["employees"], 4, labels=False, duplicates="drop")
    deals["vendedor_produto"] = deals["sales_agent"] + " | " + deals["product"]
    deals["ganho"] = deals["deal_stage"] == ETAPA_GANHO
    return deals


def _taxa_suavizada(treino: pd.DataFrame, coluna: str, taxa_geral: float) -> pd.Series:
    """Taxa de vitória por valor da coluna, puxada para a média em grupos pequenos."""
    m = config.SUAVIZACAO_AMOSTRAS
    agrupado = treino.groupby(coluna)["ganho"].agg(ganhos="sum", total="count")
    return (agrupado["ganhos"] + m * taxa_geral) / (agrupado["total"] + m)


def avaliar_corte(deals: pd.DataFrame, data_corte: str) -> dict:
    """Simula o uso da ferramenta na data de corte e compara com o que aconteceu depois."""
    corte = pd.Timestamp(data_corte)

    # 1. Só o que já tinha fechado antes do corte.
    treino = deals[deals["deal_stage"].isin(ETAPAS_FECHADAS) & (deals["close_date"] < corte)]
    estat = calcular_estatisticas_de(treino, deals["sales_price"].dropna())

    # 2. Negócios em andamento no dia do corte (prospecção não tem data, fica de fora).
    em_andamento = deals[
        (deals["deal_stage"] != ETAPA_PROSPECCAO)
        & (deals["engage_date"] < corte)
        & (deals["close_date"].isna() | (deals["close_date"] >= corte))
    ]
    pontuados = pontuar(em_andamento, estat, corte)

    # 3. O que aconteceu depois.
    resolvidos = pontuados[pontuados["close_date"].notna()]
    resolvidos = resolvidos.assign(receita=resolvidos["close_value"].fillna(0))

    por_prioridade = {}
    for prioridade in PRIORIDADES:
        grupo = resolvidos[resolvidos["prioridade"] == prioridade]
        por_prioridade[prioridade] = {
            "negocios": len(grupo),
            "ganhos": int(grupo["ganho"].sum()),
            "receita": float(grupo["receita"].sum()),
        }

    parados = pontuados[pontuados["parado"]]

    auc_atributos = {}
    for nome, coluna in ATRIBUTOS_TESTADOS.items():
        taxas = _taxa_suavizada(treino, coluna, estat.taxa_vitoria_geral)
        previsao = resolvidos[coluna].map(taxas).fillna(estat.taxa_vitoria_geral)
        auc_atributos[nome] = calcular_auc(previsao, resolvidos["ganho"])

    return {
        "data_corte": data_corte,
        "negocios_treino": len(treino),
        "limite_dias": estat.limite_dias,
        "em_andamento": len(pontuados),
        "resolvidos_depois": len(resolvidos),
        "taxa_vitoria_resolvidos": float(resolvidos["ganho"].mean()),
        "parados": len(parados),
        "parados_fechados_depois": int(parados["close_date"].notna().sum()),
        "por_prioridade": por_prioridade,
        "auc_atributos": auc_atributos,
    }


@lru_cache(maxsize=1)
def executar_validacao() -> dict:
    """Roda todos os cortes e consolida os resultados (calculado uma vez)."""
    deals = _preparar_atributos(carregar_deals())
    cortes = [avaliar_corte(deals, data) for data in config.DATAS_CORTE_VALIDACAO]

    # Consolida por prioridade somando todos os cortes.
    por_prioridade = []
    for prioridade in PRIORIDADES:
        negocios = sum(c["por_prioridade"][prioridade]["negocios"] for c in cortes)
        ganhos = sum(c["por_prioridade"][prioridade]["ganhos"] for c in cortes)
        receita = sum(c["por_prioridade"][prioridade]["receita"] for c in cortes)
        por_prioridade.append({
            "prioridade": prioridade,
            "negocios": negocios,
            "taxa_vitoria": ganhos / negocios if negocios else 0.0,
            "receita_media": receita / negocios if negocios else 0.0,
        })

    atributos = sorted(
        (
            {"atributo": nome, "auc_medio": sum(c["auc_atributos"][nome] for c in cortes) / len(cortes)}
            for nome in ATRIBUTOS_TESTADOS
        ),
        key=lambda a: -a["auc_medio"],
    )

    return {
        "cortes": cortes,
        "por_prioridade": por_prioridade,
        "atributos": atributos,
        "parados": sum(c["parados"] for c in cortes),
        "parados_fechados_depois": sum(c["parados_fechados_depois"] for c in cortes),
    }


def gerar_relatorio() -> str:
    """Relatório em Markdown com todos os números da validação."""
    v = executar_validacao()
    moeda = lambda x: "US$ " + f"{x:,.0f}".replace(",", ".")  # noqa: E731
    linhas = [
        "# Validação da pontuação (backtest)",
        "",
        "Gerado por `python -m app.servicos.validacao`. Em cada data de corte, as estatísticas usam só",
        "negócios fechados antes do corte; os negócios em andamento naquele dia são pontuados com a mesma",
        "função da tela e comparados com o que aconteceu depois.",
        "",
        "## Negócios parados",
        "",
        f"Somando os cortes, **{v['parados']} negócios** já estavam abertos há mais tempo que qualquer negócio",
        f"do histórico. Desses, **{v['parados_fechados_depois']} foram fechados depois** (ganhos ou perdidos).",
        "",
        "| Corte | Fechados antes (treino) | Limite (dias) | Em andamento | Resolvidos depois | Parados | Parados que fecharam |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in v["cortes"]:
        linhas.append(
            f"| {c['data_corte']} | {c['negocios_treino']} | {c['limite_dias']} | {c['em_andamento']} | "
            f"{c['resolvidos_depois']} | {c['parados']} | {c['parados_fechados_depois']} |"
        )
    linhas += [
        "",
        "## Resultado por prioridade (negócios resolvidos depois do corte)",
        "",
        "| Prioridade | Negócios | Taxa de vitória | Receita média por negócio |",
        "|---|---|---|---|",
    ]
    for p in v["por_prioridade"]:
        linhas.append(
            f"| {p['prioridade']} | {p['negocios']} | {p['taxa_vitoria']:.1%} | {moeda(p['receita_media'])} |"
        )
    linhas += [
        "",
        "A taxa de vitória é parecida entre as faixas (nenhum atributo prevê vitória, ver abaixo); a diferença",
        "está na receita por negócio trabalhado. A faixa Baixa fica vazia porque, no dia do corte, todo negócio",
        "que depois foi fechado ainda estava ativo: os de prioridade baixa são os parados (que nunca fecharam)",
        "e a prospecção de baixo valor (sem data de início, fora do backtest).",
    ]
    linhas += [
        "",
        "## Algum atributo prevê quem ganha?",
        "",
        "AUC fora da amostra (0,5 = sorteio; 1,0 = acerta sempre), média dos cortes:",
        "",
        "| Atributo | AUC médio | " + " | ".join(c["data_corte"] for c in v["cortes"]) + " |",
        "|---|---|" + "---|" * len(v["cortes"]),
    ]
    for a in v["atributos"]:
        por_corte = " | ".join(f"{c['auc_atributos'][a['atributo']]:.3f}" for c in v["cortes"])
        linhas.append(f"| {a['atributo']} | {a['auc_medio']:.3f} | {por_corte} |")
    return "\n".join(linhas) + "\n"


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    print(gerar_relatorio())

"""Etapa 2: calcula, para cada deal aberto, a lista, a probabilidade, o valor
esperado e a explicação em português do porquê daquele score.

Decisão validada (ver validacao.py): a probabilidade usa só a IDADE do deal.
A taxa vendedor × produto se mostrou ruído (correlação −0,04 entre metades
aleatórias), então aparece na tela apenas como histórico informativo."""

import pandas as pd

from dados import carregar_dados, separar

# Quantos "deals imaginários" com a taxa média do produto somamos ao histórico
# do vendedor. Assim, quem tem 2 deals e ganhou os 2 não aparece com 100%.
PESO_MEDIA = 20

# Só confiamos na taxa por idade quando há pelo menos esse número de deals
# históricos que chegaram vivos até aquele dia.
MIN_DEALS_POR_IDADE = 100


def taxas_vendedor_produto(fechados: pd.DataFrame) -> pd.DataFrame:
    """Taxa de ganho de cada vendedor em cada produto, puxada para a média do
    produto quando o vendedor tem poucos deals naquele produto."""
    ganhou = fechados["deal_stage"] == "Won"
    taxa_produto = ganhou.groupby(fechados["product"]).mean().rename("taxa_produto")

    t = (
        ganhou.groupby([fechados["sales_agent"], fechados["product"]])
        .agg(ganhos="sum", total="count")
        .reset_index()
        .join(taxa_produto, on="product")
    )
    t["taxa_ajustada"] = (t["ganhos"] + PESO_MEDIA * t["taxa_produto"]) / (
        t["total"] + PESO_MEDIA
    )
    return t


def curva_idade(fechados: pd.DataFrame) -> tuple[pd.Series, int]:
    """Para cada idade d, a taxa de ganho dos deals históricos que ainda estavam
    vivos no dia d. Devolve (curva, limite de dias)."""
    limite = int(fechados["duracao_dias"].max())
    ganhou = fechados["deal_stage"] == "Won"
    taxas = {}
    for d in range(limite + 1):
        vivos = fechados["duracao_dias"] >= d
        if vivos.sum() >= MIN_DEALS_POR_IDADE:
            taxas[d] = ganhou[vivos].mean()
        else:
            taxas[d] = taxas[d - 1]  # pouca amostra: repete o último valor confiável
    return pd.Series(taxas), limite


def pontuar(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Devolve os deals abertos com lista, probabilidade, valor esperado e explicação."""
    if df is None:
        df = carregar_dados()
    fechados, abertos = separar(df)

    taxa_global = (fechados["deal_stage"] == "Won").mean()
    taxas = taxas_vendedor_produto(fechados)
    curva, limite = curva_idade(fechados)

    abertos = abertos.merge(
        taxas[["sales_agent", "product", "ganhos", "total"]],
        on=["sales_agent", "product"],
        how="left",
    )
    abertos[["ganhos", "total"]] = abertos[["ganhos", "total"]].fillna(0).astype(int)

    abertos["valor"] = abertos["sales_price"]  # preço de tabela; close_value só existe depois de fechar
    abertos["lista"] = abertos.apply(lambda r: _lista(r, limite), axis=1)

    resultados = abertos.apply(
        lambda r: _probabilidade(r, curva, taxa_global, limite), axis=1, result_type="expand"
    )
    abertos["probabilidade"] = resultados[0]
    abertos["explicacao"] = resultados[1]
    abertos["valor_esperado"] = (abertos["probabilidade"] * abertos["valor"]).round(0)
    return abertos


def _lista(r: pd.Series, limite: int) -> str:
    if r["deal_stage"] == "Prospecting":
        return "Prospectar"
    if r["idade_dias"] > limite:
        return "Limpar"
    return "Focar"


def _probabilidade(r: pd.Series, curva: pd.Series, taxa_global: float, limite: int):
    nome = r["sales_agent"].split()[0]
    motivos = []
    decisao, idade_antes = r.get("decisao"), r.get("idade_antes")
    if decisao == "manter":
        motivos.append(f"✅ Contato confirmado pelo vendedor (estava parado há {int(idade_antes)} dias)")
    elif decisao == "recomecar":
        motivos.append(f"♻️ Recomeçado como prospect (a negociação antiga estava parada há {int(idade_antes)} dias)")

    if r["lista"] == "Limpar":
        motivos.append(
            f"Parado há {int(r['idade_dias'])} dias. Nenhum deal desse CRM levou "
            f"mais de {limite} dias para fechar → chance real desconhecida, confirme com o cliente"
        )
        p = None
    elif r["lista"] == "Prospectar":
        p = taxa_global
        motivos.append(
            f"Ainda em prospecção: o CRM não registra desde quando, então usamos "
            f"a média geral de {p:.0%}. Na prática, a ordem aqui é pelo valor do produto"
        )
    else:
        idade = int(r["idade_dias"])
        p = curva[idade]
        motivos.append(
            f"Em negociação há {idade} dias. Deals que chegaram vivos até aqui foram "
            f"ganhos {p:.0%} das vezes (média geral: {taxa_global:.0%})"
        )

    # Histórico do vendedor: só informativo, NÃO entra no cálculo.
    if r["total"] > 0:
        motivos.append(
            f"ℹ️ Histórico: {nome} ganhou {r['ganhos']} de {r['total']} deals de "
            f"{r['product']}. Não entra no score: no teste, essa taxa não previu resultados"
        )
    return (None if p is None else round(p, 3)), motivos


# Ordem de cada lista. Os critérios extras desempatam deals de mesmo valor, para
# a lista aparecer sempre na mesma ordem em qualquer computador.
ORDEM = {
    # maior valor esperado → maior chance → id
    "Focar": (["valor_esperado", "probabilidade", "opportunity_id"], [False, False, True]),
    # maior valor esperado → id
    "Prospectar": (["valor_esperado", "opportunity_id"], [False, True]),
    # maior valor → MAIS RECENTE primeiro (mais chance de ainda ser salvo) → id
    "Limpar": (["valor", "idade_dias", "opportunity_id"], [False, True, True]),
}


def ordenar(df: pd.DataFrame, lista: str) -> pd.DataFrame:
    colunas, crescente = ORDEM[lista]
    return df[df["lista"] == lista].sort_values(colunas, ascending=crescente, kind="stable")


if __name__ == "__main__":
    # Rode `python score.py` para ver o resultado no terminal.
    r = pontuar()
    print(r["lista"].value_counts().to_string(), "\n")
    for lista in ["Focar", "Prospectar", "Limpar"]:
        top = ordenar(r, lista).head(3)
        print(f"=== {lista} (top 3) ===")
        for _, d in top.iterrows():
            prob = "—" if pd.isna(d["probabilidade"]) else f"{d['probabilidade']:.0%}"
            print(f"{d['opportunity_id']} | {d['sales_agent']} | {d['product']} | "
                  f"valor US$ {d['valor']:,.0f} | prob {prob} | esperado US$ {d['valor_esperado'] if pd.notna(d['valor_esperado']) else '—'}")
            for m in d["explicacao"]:
                print("   •", m)
        print()

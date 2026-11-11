"""Diagnóstico do Dataset 1 usando 100% dos tickets.

Satisfação e tempo de resolução só existem nos tickets fechados (1/3 da base). Para olhar 100% dos
8.469 tickets, o desfecho usado aqui é o STATUS do ticket, que todo ticket tem:
- Open: ninguém respondeu;
- Pending Customer Response: respondido, esperando o cliente;
- Closed: resolvido.
Pergunta respondida: alguma variável faz o ticket travar (ficar sem resposta ou sem fechar)?

Uso: python diagnostico_base_completa.py <csv> <saida.md>
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

VARIAVEIS = {
    "Ticket Channel": "Canal",
    "Ticket Priority": "Prioridade",
    "Ticket Type": "Tipo",
    "Ticket Subject": "Assunto",
    "Product Purchased": "Produto",
    "Customer Gender": "Gênero",
    "faixa_idade": "Faixa de idade",
    "ano_compra": "Ano da compra",
}


def cramer_v(tabela: pd.DataFrame) -> float:
    chi2 = stats.chi2_contingency(tabela)[0]
    n = tabela.values.sum()
    return float(np.sqrt(chi2 / (n * (min(tabela.shape) - 1))))


def main(origem: str, saida: str) -> None:
    df = pd.read_csv(origem)
    df["faixa_idade"] = pd.cut(df["Customer Age"], [0, 25, 35, 45, 55, 100]).astype(str)
    df["ano_compra"] = pd.to_datetime(df["Date of Purchase"]).dt.year.astype(str)
    df["fechado"] = (df["Ticket Status"] == "Closed").astype(int)
    df["sem_resposta"] = (df["Ticket Status"] == "Open").astype(int)
    n = len(df)

    md = ["# Diagnóstico com 100% dos tickets (Dataset 1)", "",
          f"Base: **{n} tickets**, todos. Desfecho: status do ticket, o único resultado que todo ticket tem.", "",
          "## Funil geral", "", "| Status | Tickets | % |", "|---|---|---|"]
    for st, q in df["Ticket Status"].value_counts().items():
        md.append(f"| {st} | {q} | {100 * q / n:.1f}% |")

    md += ["", "## Alguma variável faz o ticket travar?", "",
           "Teste qui-quadrado de cada variável contra o status (3 níveis). V de Cramér mede a força "
           "da relação (0 = nenhuma, 0,1 = fraca, 0,3 = moderada).", "",
           "| Variável | Categorias | p-valor | V de Cramér | % sem resposta (min a max) | % fechado (min a max) |",
           "|---|---|---|---|---|---|"]
    resumo = []
    for col, nome in VARIAVEIS.items():
        tab = pd.crosstab(df[col], df["Ticket Status"])
        p = stats.chi2_contingency(tab)[1]
        g = df.groupby(col)[["sem_resposta", "fechado"]].mean() * 100
        resumo.append((p, f"| {nome} | {tab.shape[0]} | {p:.3f} | {cramer_v(tab):.3f} | "
                          f"{g['sem_resposta'].min():.1f}% a {g['sem_resposta'].max():.1f}% | "
                          f"{g['fechado'].min():.1f}% a {g['fechado'].max():.1f}% |"))
    md += [linha for _, linha in sorted(resumo)]

    X = pd.get_dummies(df[list(VARIAVEIS)]).assign(idade=df["Customer Age"])
    md += ["", "## Modelo com todas as variáveis juntas", "",
           "Random Forest, validação cruzada em 5 partes, prevendo o status de cada ticket.", "",
           "| Alvo | Acurácia do modelo | Acurácia da linha de base (prever sempre a classe mais comum) |", "|---|---|---|"]
    for alvo, rotulo in [("Ticket Status", "Status (3 níveis)"), ("fechado", "Fechou ou não"),
                         ("sem_resposta", "Ficou sem resposta ou não")]:
        y = df[alvo]
        acc = cross_val_score(RandomForestClassifier(300, min_samples_leaf=20, random_state=0),
                              X, y, cv=5, scoring="accuracy").mean()
        md.append(f"| {rotulo} | {100 * acc:.1f}% | {100 * y.value_counts(normalize=True).max():.1f}% |")

    md += ["", "## Por canal e prioridade (100%)", "",
           "| Canal | Prioridade | Tickets | Sem resposta | Aguardando cliente | Fechado |",
           "|---|---|---|---|---|---|"]
    t = pd.crosstab([df["Ticket Channel"], df["Ticket Priority"]], df["Ticket Status"], normalize="index") * 100
    q = df.groupby(["Ticket Channel", "Ticket Priority"]).size()
    for (c, pr), row in t.sort_values("Open", ascending=False).iterrows():
        md.append(f"| {c} | {pr} | {q[(c, pr)]} | {row['Open']:.1f}% | "
                  f"{row['Pending Customer Response']:.1f}% | {row['Closed']:.1f}% |")

    md += ["", "## O que NÃO dá para calcular em 100%", "",
           "| Métrica | Tickets com o dado | Motivo |", "|---|---|---|",
           f"| Satisfação | {df['Customer Satisfaction Rating'].notna().sum()} | Só o fechado recebe nota |",
           f"| Tempo até resolver | {df['Time to Resolution'].notna().sum()} | Só o fechado tem resolução |",
           f"| Tempo até a 1ª resposta | 0 | Não existe data de abertura do ticket |",
           "", "Preencher nota ou tempo dos outros 5.700 com estimativa seria inventar dado. "
           "Esses números ficam com a base declarada (n = 2.769 ou 1.404)."]
    with open(saida, "w", encoding="utf-8") as h:
        h.write("\n".join(md) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

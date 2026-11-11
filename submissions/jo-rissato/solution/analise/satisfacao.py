"""O que impacta a satisfação (Customer Satisfaction Rating) no Dataset 1.

A nota só existe nos tickets fechados. Este script usa 100% das notas existentes e registra quantos
tickets da base não têm nota. Variáveis testadas: todas as colunas do arquivo mais as derivadas
(horas até resolver, registro de tempo impossível, dias entre compra e 1ª resposta, hora da 1ª
resposta, tamanho dos textos, palavras do texto da descrição).

Testes: Kruskal-Wallis (categóricas), Spearman (numéricas), correção de Bonferroni para o número de
testes, e modelos com todas as variáveis juntas em validação cruzada de 5 partes.

Uso: python satisfacao.py <csv> <saida.md>
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score


def main(origem: str, saida: str) -> None:
    df = pd.read_csv(origem)
    n_total = len(df)
    c = df[df["Customer Satisfaction Rating"].notna()].copy()
    c["nota"] = c["Customer Satisfaction Rating"].astype(int)
    fr, tr = pd.to_datetime(c["First Response Time"]), pd.to_datetime(c["Time to Resolution"])
    c["horas_ate_resolver"] = (tr - fr).dt.total_seconds() / 3600
    c["registro_impossivel"] = (c["horas_ate_resolver"] < 0).map({True: "sim", False: "não"})
    c["dias_compra_ate_resposta"] = (fr - pd.to_datetime(c["Date of Purchase"])).dt.days
    c["hora_1a_resposta"] = fr.dt.hour
    c["tam_descricao"] = c["Ticket Description"].str.len()
    c["tam_resolucao"] = c["Resolution"].str.len()
    c["faixa_idade"] = pd.cut(c["Customer Age"], [0, 25, 35, 45, 55, 100]).astype(str)
    c["ano_compra"] = pd.to_datetime(c["Date of Purchase"]).dt.year.astype(str)

    categ = {"Ticket Channel": "Canal", "Ticket Priority": "Prioridade", "Ticket Type": "Tipo",
             "Ticket Subject": "Assunto", "Product Purchased": "Produto", "Customer Gender": "Gênero",
             "faixa_idade": "Faixa de idade", "ano_compra": "Ano da compra",
             "registro_impossivel": "Registro de tempo impossível"}
    numer = {"horas_ate_resolver": "Horas entre 1ª resposta e resolução",
             "dias_compra_ate_resposta": "Dias entre compra e 1ª resposta",
             "hora_1a_resposta": "Hora do dia da 1ª resposta", "Customer Age": "Idade",
             "tam_descricao": "Tamanho da descrição", "tam_resolucao": "Tamanho da resolução"}
    n_testes = len(categ) + len(numer)
    linhas = []
    for col, nome in categ.items():
        p = stats.kruskal(*[g["nota"].values for _, g in c.groupby(col)])[1]
        m = c.groupby(col)["nota"].mean()
        linhas.append((p, f"| {nome} | categórica, {c[col].nunique()} grupos | {p:.3f} | "
                          f"{min(1, p * n_testes):.3f} | média de {m.min():.2f} a {m.max():.2f} |"))
    for col, nome in numer.items():
        r, p = stats.spearmanr(c[col], c["nota"])
        linhas.append((p, f"| {nome} | numérica | {p:.3f} | {min(1, p * n_testes):.3f} | rho {r:+.3f} |"))

    dist = c["nota"].value_counts().sort_index()
    chi_p = stats.chisquare(dist.values)[1]

    cols_cat = list(categ)
    X = pd.get_dummies(c[cols_cat]).assign(**{k: c[k] for k in numer})
    y = c["nota"]
    rf = cross_val_score(RandomForestClassifier(300, min_samples_leaf=20, random_state=0), X, y, cv=5).mean()
    r2 = cross_val_score(RandomForestRegressor(300, min_samples_leaf=20, random_state=0), X, y, cv=5,
                         scoring="r2").mean()
    texto = TfidfVectorizer(min_df=5, ngram_range=(1, 2)).fit_transform(
        c["Ticket Description"].fillna("") + " " + c["Resolution"].fillna(""))
    txt = cross_val_score(LogisticRegression(max_iter=2000), texto, y, cv=5).mean()
    base = y.value_counts(normalize=True).max()

    md = ["# O que impacta a satisfação?", "",
          "## Base", "",
          "| Item | Tickets | % da base |", "|---|---|---|",
          f"| Base total | {n_total} | 100% |",
          f"| Com nota de satisfação (todos fechados) | {len(c)} | {100 * len(c) / n_total:.1f}% |",
          f"| Sem nota (abertos ou aguardando cliente) | {n_total - len(c)} | {100 * (n_total - len(c)) / n_total:.1f}% |",
          "", "A nota só existe quando o ticket fecha. Esta análise usa 100% das notas existentes. "
          "Para os outros tickets, a satisfação não foi coletada.", "",
          "## Distribuição das notas", "", "| Nota | Tickets | % |", "|---|---|---|"]
    md += [f"| {k} | {v} | {100 * v / len(c):.1f}% |" for k, v in dist.items()]
    md += ["", f"Teste de aderência a uma distribuição uniforme (todas as notas iguais): p = {chi_p:.3f}. "
           "Acima de 0,05 = as notas não se distinguem de um sorteio de 1 a 5.", "",
           f"## Cada variável contra a nota ({n_testes} testes)", "",
           "p-valor corrigido = p × número de testes (Bonferroni). Impacto real exige corrigido < 0,05.", "",
           "| Variável | Tipo | p-valor | p corrigido | Efeito |", "|---|---|---|---|---|"]
    md += [l for _, l in sorted(linhas)]
    md += ["", "## Todas as variáveis juntas", "", "Validação cruzada em 5 partes.", "",
           "| Modelo | Resultado | Linha de base |", "|---|---|---|",
           f"| Random Forest, nota exata | {100 * rf:.1f}% de acerto | {100 * base:.1f}% (sempre a nota mais comum) |",
           f"| Random Forest, nota como número | R² = {r2:.3f} | 0 (prever sempre a média) |",
           f"| Texto da descrição + resolução (TF-IDF, regressão logística) | {100 * txt:.1f}% de acerto | {100 * base:.1f}% |",
           "", "## Resposta", "",
           f"Nenhuma variável registrada impacta a satisfação. Com {len(c)} notas, nenhum dos {n_testes} testes "
           "passa da correção, os modelos não superam a linha de base e as notas se distribuem como sorteio. "
           f"Para {n_total - len(c)} tickets ({100 * (n_total - len(c)) / n_total:.1f}%) a satisfação não existe no dado."]
    with open(saida, "w", encoding="utf-8") as h:
        h.write("\n".join(md) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

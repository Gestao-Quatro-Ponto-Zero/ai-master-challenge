"""
Avaliação honesta do classificador, com os números usados no README.
Roda: python submissions/adson-valeriano/solution/avaliar.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

import triagem

SAIDA = Path(__file__).resolve().parent / "resultados_avaliacao.md"


def main():
    pacote, teste = triagem.treinar(salvar=True)
    vet, modelo = pacote["vetorizador"], pacote["modelo"]
    X = vet.transform(teste["texto"])
    y = teste["Topic_group"].to_numpy()
    pred = modelo.predict(X)
    conf = modelo.predict_proba(X).max(axis=1)

    linhas = ["# Resultados da avaliação do classificador", ""]
    linhas.append(f"- Tickets de teste (nunca vistos no treino): {len(y):,}".replace(",", "."))
    linhas.append(f"- Acurácia geral: {accuracy_score(y, pred):.1%}")
    maior = pd.Series(y).value_counts(normalize=True).iloc[0]
    linhas.append(f"- Referência (chutar sempre a categoria mais comum): {maior:.1%}")
    linhas += ["", "## Cobertura x acerto por limiar de confiança", "",
               "| Limiar | Tickets que a IA decide sozinha | Acerto nesses tickets |", "|---|---|---|"]
    for t in [0.5, 0.6, 0.7, 0.8, 0.9]:
        k = conf >= t
        linhas.append(f"| {t:.0%} | {k.mean():.1%} | {accuracy_score(y[k], pred[k]):.1%} |")

    linhas += ["", "## Desempenho por categoria", "", "```",
               classification_report(y, pred, digits=2), "```"]

    labs = modelo.classes_
    cm = pd.DataFrame(confusion_matrix(y, pred, labels=labs), index=labs, columns=labs)
    linhas += ["", "## Matriz de confusão (linha = real, coluna = previsto)", "", cm.to_markdown()]

    # Teste de domínio: o modelo de TI funciona nos tickets de suporte ao cliente? (pegadinha do cruzamento)
    sup = pd.read_csv(triagem.RAIZ / "datasets" / "customer_support_tickets.csv")
    Xs = vet.transform(sup["Ticket Description"].map(triagem.normalizar))
    ps = modelo.predict(Xs)
    cs = modelo.predict_proba(Xs).max(axis=1)
    dist = pd.Series(ps).value_counts(normalize=True).round(3)
    linhas += ["", "## Teste de transferência: modelo de TI aplicado ao dataset de suporte ao cliente", "",
               f"- Confiança média: {cs.mean():.0%} (no dataset de TI: {conf.mean():.0%})",
               f"- Tickets acima do limiar de 70%: {(cs >= 0.7).mean():.1%}",
               f"- Categoria mais prevista: {dist.index[0]} ({dist.iloc[0]:.0%} dos tickets, inclusive cobrança e reembolso)",
               "- Conclusão: o modelo não transfere. Para o suporte da empresa, é preciso treinar com tickets "
               "rotulados da própria operação."]

    SAIDA.write_text("\n".join(linhas), encoding="utf-8")
    print("\n".join(linhas))


if __name__ == "__main__":
    main()

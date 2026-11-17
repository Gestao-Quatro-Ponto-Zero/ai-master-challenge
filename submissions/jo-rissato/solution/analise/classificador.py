"""Classificador de categoria de ticket (Dataset 2), medido por categoria.

1. Separa 20% dos textos como teste, estratificado, e não toca nele até o fim.
2. Compara modelos com validação cruzada de 5 partes nos 80% de treino. O vetorizador
   fica dentro do pipeline, então aprende o vocabulário só com cada parte de treino.
3. Treina o melhor em todo o treino e mede no teste: acerto por categoria, matriz de
   confusão, Compra com e sem o formulário "new purchase po".
4. Mede a confiança do modelo: quanto acerta quando decide sozinho acima de cada limite
   e quantos tickets iriam para uma pessoa.
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import make_pipeline
from sklearn.svm import LinearSVC

ROTULOS = {"Hardware": "Hardware", "HR Support": "Suporte de RH", "Access": "Acesso",
           "Miscellaneous": "Diversos", "Storage": "Armazenamento", "Purchase": "Compra",
           "Internal Project": "Projeto interno", "Administrative rights": "Direitos de administrador"}
SEMENTE = 42


def tfidf() -> TfidfVectorizer:
    return TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)


MODELOS = {
    "Linha de base (sempre a categoria mais comum)": lambda: DummyClassifier(strategy="most_frequent"),
    "Naive Bayes complementar": lambda: make_pipeline(tfidf(), ComplementNB()),
    "Regressão logística": lambda: make_pipeline(tfidf(), LogisticRegression(max_iter=2000, C=10)),
    "Regressão logística com peso por categoria": lambda: make_pipeline(
        tfidf(), LogisticRegression(max_iter=2000, C=10, class_weight="balanced")),
    "SVM linear": lambda: make_pipeline(tfidf(), LinearSVC(C=0.5)),
}


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def main(origem: str, saida: str, json_saida: str) -> None:
    d = pd.read_csv(origem)
    X, y = d["Document"], d["Topic_group"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEMENTE)
    cv = StratifiedKFold(5, shuffle=True, random_state=SEMENTE)
    md = ["# Classificador de categoria (Dataset 2)", "",
          f"Base: {len(d):,} textos. Treino {len(Xtr):,} (80%) e teste {len(Xte):,} (20%), separados de forma ".replace(",", ".")
          + "estratificada antes de qualquer treino.", "",
          "## 1. Comparação de modelos (validação cruzada de 5 partes, só no treino)", "",
          "O vetorizador de texto fica dentro de cada parte, então nenhum modelo vê o vocabulário da parte "
          "em que é avaliado.", "",
          "| Modelo | Acurácia | F1 macro (média das 8 categorias) | Tempo |", "|---|---|---|---|"]
    res = {}
    for nome, fab in MODELOS.items():
        t0 = time.time()
        r = cross_validate(fab(), Xtr, ytr, cv=cv, scoring=["accuracy", "f1_macro"], n_jobs=5)
        res[nome] = (r["test_accuracy"].mean(), r["test_f1_macro"].mean(), r["test_f1_macro"].std())
        md.append(f"| {nome} | {pct(res[nome][0])} | {pct(res[nome][1])} (±{res[nome][2] * 100:.1f}) | "
                  f"{time.time() - t0:.0f} s |")
        print(nome, res[nome], flush=True)
    melhor = max((k for k in res if not k.startswith("Linha")), key=lambda k: res[k][1])
    md += ["", f"Escolhido pelo maior F1 macro: **{melhor}**.", ""]

    modelo = MODELOS[melhor]()
    modelo.fit(Xtr, ytr)
    pred = modelo.predict(Xte)
    cats = list(ROTULOS)
    p, r, f, s = precision_recall_fscore_support(yte, pred, labels=cats, zero_division=0)
    md += ["## 2. Resultado no teste separado", "",
           f"Acurácia {pct(accuracy_score(yte, pred))}, F1 macro {pct(f1_score(yte, pred, average='macro'))} "
           f"(linha de base: acurácia {pct((yte == ytr.mode()[0]).mean())}).", "",
           "Precisão: dos tickets que o modelo colocou na categoria, quantos eram dela. "
           "Cobertura: dos tickets da categoria, quantos o modelo encontrou.", "",
           "| Categoria | Tickets no teste | Precisão | Cobertura | F1 |", "|---|---|---|---|---|"]
    ordem = np.argsort(-s)
    for i in ordem:
        md.append(f"| {ROTULOS[cats[i]]} | {s[i]} | {pct(p[i])} | {pct(r[i])} | {pct(f[i])} |")

    cm = confusion_matrix(yte, pred, labels=cats)
    md += ["", "## 3. Onde o modelo confunde (matriz de confusão do teste)", "",
           "Linha = categoria real, coluna = categoria prevista, valor = % da linha.", "",
           "| Real \\ Prevista | " + " | ".join(ROTULOS[c][:12] for c in cats) + " |",
           "|---" * (len(cats) + 1) + "|"]
    for i, c in enumerate(cats):
        linha = cm[i] / cm[i].sum() * 100
        md.append(f"| {ROTULOS[c]} | " + " | ".join(f"{v:.0f}" for v in linha) + " |")
    pares = [(cm[i, j], cats[i], cats[j]) for i in range(len(cats)) for j in range(len(cats)) if i != j]
    pares.sort(reverse=True)
    md += ["", "Maiores confusões:", ""]
    for q, a, b in pares[:5]:
        md.append(f"- {ROTULOS[a]} previsto como {ROTULOS[b]}: {q} tickets "
                  f"({q / cm[cats.index(a)].sum() * 100:.1f}% de {ROTULOS[a]}).")

    form = Xte.str.startswith("new purchase po").values
    comp = (yte == "Purchase").values
    md += ["", "## 4. Compra com e sem o formulário automático", "",
           "| Recorte de Compra | Tickets no teste | Cobertura (acerto) |", "|---|---|---|"]
    for nome, m in [("Todos", comp), ("Só o formulário \"new purchase po\"", comp & form),
                    ("Sem o formulário", comp & ~form)]:
        md.append(f"| {nome} | {m.sum()} | {pct((pred[m] == 'Purchase').mean())} |")

    resumo = {"modelo": melhor, "acuracia_teste": float(accuracy_score(yte, pred)),
              "f1_macro_teste": float(f1_score(yte, pred, average="macro"))}
    if hasattr(modelo, "predict_proba"):
        conf = modelo.predict_proba(Xte).max(axis=1)
        md += ["", "## 5. Confiança: quando o modelo decide sozinho e quando passa para uma pessoa", "",
               "Se o modelo só classificar sozinho quando a confiança passar do limite, o resto vai para uma "
               "pessoa. A tabela mostra o acerto nos tickets que ele decide e quantos sobram para a pessoa.", "",
               "| Limite de confiança | Decide sozinho | Acerto quando decide | Vai para uma pessoa |",
               "|---|---|---|---|"]
        curva = []
        for lim in [0.0, 0.5, 0.6, 0.7, 0.8, 0.9]:
            m = conf >= lim
            ac = (pred[m] == yte.values[m]).mean()
            curva.append({"limite": lim, "cobertura": float(m.mean()), "acerto": float(ac)})
            md.append(f"| {lim:.1f} | {pct(m.mean())} | {pct(ac)} | {pct(1 - m.mean())} |")
        resumo["curva_confianca"] = curva
    md.append("")
    with open(saida, "w") as fh:
        fh.write("\n".join(md))
    with open(json_saida, "w") as fh:
        json.dump(resumo, fh, ensure_ascii=False, indent=2)
    print("\n".join(md))


if __name__ == "__main__":
    main(*sys.argv[1:4])

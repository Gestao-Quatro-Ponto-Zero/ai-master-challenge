import time

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.pipeline import make_pipeline

from comum import OUT_DIR, SEED, boot_ic, ler_ds2, salvar_json


def modelo():
    # pipeline fixo, sem busca de hiperparâmetro (spec F3)
    return make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True),
                         LogisticRegression(max_iter=2000, random_state=SEED))


def macro_f1(y, p):
    return f1_score(y, p, average="macro")


def avaliar(y, pred, classes):
    acc, mf1 = accuracy_score(y, pred), macro_f1(y, pred)
    return {
        "n": int(len(y)),
        "acuracia": round(acc, 4), "acuracia_ic95": [round(v, 4) for v in boot_ic(y, pred, accuracy_score)],
        "macro_f1": round(mf1, 4), "macro_f1_ic95": [round(v, 4) for v in boot_ic(y, pred, macro_f1)],
        "f1_por_classe": dict(zip(classes, np.round(f1_score(y, pred, labels=classes, average=None), 4).tolist())),
        "matriz_confusao": {"classes": classes, "linhas_verdadeiro": confusion_matrix(y, pred, labels=classes).tolist()},
    }


def carregar():
    return ler_ds2().merge(pd.read_csv(OUT_DIR / "f1_splits.csv"), on="id")


def main():
    df = carregar()
    classes = sorted(df["Topic_group"].unique())
    saida, modelos = {}, {}
    for col in ["split_grupo", "split_aleatorio"]:
        tr, ho = df[df[col] == "treino"], df[df[col] == "holdout"]
        m = modelo().fit(tr["Document"], tr["Topic_group"])
        modelos[col] = m
        proba = m.predict_proba(ho["Document"])
        pred = m.classes_[proba.argmax(1)]
        saida[col] = avaliar(ho["Topic_group"].values, pred, classes)
        if col == "split_grupo":
            probs = pd.DataFrame(proba, columns=[f"p_{c}" for c in m.classes_])
            probs.insert(0, "p_max", proba.max(1).round(6))
            probs.insert(0, "pred", pred)
            probs.insert(0, "rotulo", ho["Topic_group"].values)
            probs.insert(0, "id", ho["id"].values)
            probs.round(6).to_csv(OUT_DIR / "f3_probs_holdout_grupo.csv", index=False)
        else:
            grupos_treino = set(tr["group_id"])
            exp = ho["group_id"].isin(grupos_treino).values
            acerto = pred == ho["Topic_group"].values
            saida["vazamento_por_exposicao_aleatorio"] = {
                "com_quase_duplicado_no_treino": {"n": int(exp.sum()), "acuracia": round(float(acerto[exp].mean()), 4)},
                "sem_quase_duplicado_no_treino": {"n": int((~exp).sum()), "acuracia": round(float(acerto[~exp].mean()), 4)},
            }
    g, a = saida["split_grupo"], saida["split_aleatorio"]
    saida["vazamento_pp"] = {"acuracia": round(100 * (a["acuracia"] - g["acuracia"]), 2),
                             "macro_f1": round(100 * (a["macro_f1"] - g["macro_f1"]), 2)}

    # latência: 1.000 tickets do holdout por grupo, um a um
    ho = df[df["split_grupo"] == "holdout"].sample(1000, random_state=SEED)
    m = modelos["split_grupo"]
    m.predict_proba(ho["Document"].iloc[:5])  # aquecimento
    lat = []
    for t in ho["Document"]:
        t0 = time.perf_counter()
        m.predict_proba([t])
        lat.append((time.perf_counter() - t0) * 1000)
    saida["latencia_classico"] = {"n": 1000, "p50_ms": round(float(np.percentile(lat, 50)), 3),
                                  "p95_ms": round(float(np.percentile(lat, 95)), 3),
                                  "total_por_1000_s": round(sum(lat) / 1000, 3),
                                  "custo_marginal": "≈ 0 (CPU local)"}
    salvar_json(saida, "f3_classico.json")
    print(f"grupo: acc {g['acuracia']} {g['acuracia_ic95']}, macro-F1 {g['macro_f1']} {g['macro_f1_ic95']}")
    print(f"aleatório: acc {a['acuracia']} {a['acuracia_ic95']}, macro-F1 {a['macro_f1']} {a['macro_f1_ic95']}")
    print(f"vazamento: {saida['vazamento_pp']}; exposição: {saida['vazamento_por_exposicao_aleatorio']}")
    print(f"latência: {saida['latencia_classico']}")


if __name__ == "__main__":
    main()

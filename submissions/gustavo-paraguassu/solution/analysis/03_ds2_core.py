"""03 — Dataset 2: testa as hipóteses H1, H3a, H3b, H6 e o diferencial #5.

H1  — quanto do volume é pedido repetido (quase idêntico a outro ticket)?
H3a — ticket curto/vago (falta de dado) erra mais o roteamento?
H3b — quais filas se confundem? existe o mesmo texto rotulado em filas diferentes?
H6  — com qual confiança dá para rotear sozinho, e que fração do volume isso cobre?
#5  — quantos tickets rotulados uma empresa precisa? quais erros de fila custam mais?

Split: holdout por GRUPO de quase-duplicados (sim. cosseno >= 0.8), para que um ticket
e seu "gêmeo" nunca caiam um no treino e outro no teste (vazamento infla a acurácia).

Uso: python 03_ds2_core.py <all_tickets_processed_improved_v3.csv> <dir_saida>
"""
import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix

SIM_DUP = 0.8          # limiar de "quase idêntico"
SEED = 42
src, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
out_dir.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(SEED)
R = {}  # resultados para JSON (os documentos citam só números daqui)

df = pd.read_csv(src).rename(columns={"Document": "text", "Topic_group": "queue"})
df["text"] = df["text"].fillna("").astype(str).str.strip()
df["n_tok"] = df["text"].str.split().str.len()
R["n"] = len(df)
R["queues"] = df["queue"].value_counts().to_dict()
print("== volume", len(df)); print(df["queue"].value_counts().to_string())
print("\n== tamanho (tokens)"); print(df["n_tok"].describe(percentiles=[.1, .25, .5, .75, .9]).round(1).to_string())

# ---------------------------------------------------------------- exatos
dup_mask = df.duplicated("text", keep=False)
conf = df[dup_mask].groupby("text")["queue"].nunique()
R["exact_dup_share"] = float(dup_mask.mean())
R["exact_dup_texts_conflicting_labels"] = int((conf > 1).sum())
R["exact_dup_texts"] = int(len(conf))
print(f"\n== duplicados EXATOS: {dup_mask.mean():.1%} dos tickets | textos repetidos: {len(conf)} "
      f"| destes, com filas DIFERENTES: {(conf > 1).sum()}")

# ---------------------------------------------------------------- quase-duplicados (H1)
vec_dup = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, dtype=np.float32)
X = vec_dup.fit_transform(df["text"])
n = X.shape[0]
max_sim = np.zeros(n, dtype=np.float32)
nn_idx = np.zeros(n, dtype=np.int64)
parent = np.arange(n)


def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


XT = X.T.tocsc()
CH = 1000
for s in range(0, n, CH):
    S = (X[s:s + CH] @ XT).toarray()
    for k in range(S.shape[0]):
        S[k, s + k] = -1  # ignora a si mesmo
    nn_idx[s:s + CH] = S.argmax(1)
    max_sim[s:s + CH] = S.max(1)
    rows, cols = np.nonzero(S >= SIM_DUP)
    for r, c in zip(rows + s, cols):
        a, b = find(r), find(c)
        if a != b:
            parent[a] = b
groups = np.array([find(i) for i in range(n)])
df["group"] = groups
df["max_sim"] = max_sim
df["nn_queue"] = df["queue"].values[nn_idx]
share_twin = float((max_sim >= SIM_DUP).mean())
gsize = pd.Series(groups).value_counts()
R["near_dup_share"] = share_twin
R["n_groups"] = int(len(gsize))
print(f"\n== H1 quase-duplicados (cos >= {SIM_DUP}): {share_twin:.1%} dos tickets têm um 'gêmeo' "
      f"| grupos: {len(gsize)} | maior grupo: {gsize.max()}")
for thr in [0.5, 0.6, 0.7, 0.8, 0.9]:
    R[f"share_twin_{thr}"] = float((max_sim >= thr).mean())
    print(f"   sim >= {thr}: {(max_sim >= thr).mean():.1%}")
twins = df[df["max_sim"] >= 0.9]
R["twin90_label_disagree"] = float((twins["queue"] != twins["nn_queue"]).mean())
print(f"== H3b: entre pares quase idênticos (>=0.9), filas diferentes em {R['twin90_label_disagree']:.1%} "
      f"(piso de ruído do rótulo)")
print("\n== 8 maiores grupos de pedidos repetidos (candidatos a autoatendimento/macro):")
top = []
for g in gsize.index[:8]:
    sub = df[df["group"] == g]
    q = sub["queue"].value_counts()
    top.append({"size": int(len(sub)), "queue": q.index[0], "queue_purity": round(q.iloc[0] / len(sub), 2),
                "example": sub["text"].iloc[0][:140]})
    print(f"   n={len(sub):4d} fila={q.index[0]:22s} pureza={q.iloc[0]/len(sub):.0%} | {sub['text'].iloc[0][:110]}")
R["top_repeat_groups"] = top

# ---------------------------------------------------------------- split por grupo + modelo
gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=SEED)
tr, te = next(gss.split(df, df["queue"], df["group"]))
train, test = df.iloc[tr].reset_index(drop=True), df.iloc[te].reset_index(drop=True)
R["n_train"], R["n_test"] = len(train), len(test)
print(f"\n== split por grupo: treino={len(train)} teste={len(test)} "
      f"(grupos em comum: {len(set(train.group) & set(test.group))})")


def make_model():
    v = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, max_features=200_000)
    m = LogisticRegression(C=5, max_iter=3000)
    return v, m


vec, clf = make_model()
Xtr, Xte = vec.fit_transform(train["text"]), None
clf.fit(Xtr, train["queue"])
Xte = vec.transform(test["text"])
proba = clf.predict_proba(Xte)
classes = clf.classes_
pred = classes[proba.argmax(1)]
confid = proba.max(1)
top2 = classes[np.argsort(-proba, 1)[:, :2]]
test["pred"], test["conf"] = pred, confid
test["ok"] = test["pred"] == test["queue"]
acc = accuracy_score(test["queue"], pred)
R["accuracy"] = float(acc)
R["macro_f1"] = float(f1_score(test["queue"], pred, average="macro"))
R["top2_accuracy"] = float(np.mean([y in t for y, t in zip(test["queue"], top2)]))
print(f"\n== modelo TF-IDF + regressão logística | acurácia={acc:.3f} | macro-F1={R['macro_f1']:.3f} "
      f"| top-2={R['top2_accuracy']:.3f}")
rep = classification_report(test["queue"], pred, output_dict=True, zero_division=0)
print(classification_report(test["queue"], pred, digits=3, zero_division=0))
R["per_class"] = {c: {k: round(rep[c][k], 3) for k in ["precision", "recall", "f1-score", "support"]} for c in classes}

# split ingênuo (aleatório) para mostrar o vazamento
rnd = rng.permutation(n)
cut = int(0.8 * n)
v2, m2 = make_model()
m2.fit(v2.fit_transform(df["text"].iloc[rnd[:cut]]), df["queue"].iloc[rnd[:cut]])
acc_naive = accuracy_score(df["queue"].iloc[rnd[cut:]], m2.predict(v2.transform(df["text"].iloc[rnd[cut:]])))
R["accuracy_naive_random_split"] = float(acc_naive)
print(f"== mesmo modelo com split ALEATÓRIO (com vazamento): {acc_naive:.3f}  -> inflado em {acc_naive-acc:+.3f}")

# ---------------------------------------------------------------- H3b: confusões
cm = pd.DataFrame(confusion_matrix(test["queue"], pred, labels=classes), index=classes, columns=classes)
pairs = []
for a in classes:
    for b in classes:
        if a != b and cm.loc[a, b] > 0:
            pairs.append({"true": a, "pred": b, "n": int(cm.loc[a, b]), "share_of_true": round(cm.loc[a, b] / cm.loc[a].sum(), 3)})
pairs = sorted(pairs, key=lambda p: -p["n"])
R["top_confusions"] = pairs[:10]
print("\n== H3b: 8 confusões mais frequentes (fila real -> fila prevista)")
for p in pairs[:8]:
    print(f"   {p['true']:22s} -> {p['pred']:22s} n={p['n']:4d} ({p['share_of_true']:.1%} da fila real)")

# ---------------------------------------------------------------- H3a: tamanho x erro
bins = [0, 5, 10, 20, 40, 80, 10_000]
labels = ["1-5", "6-10", "11-20", "21-40", "41-80", "81+"]
test["len_bin"] = pd.cut(test["n_tok"], bins=bins, labels=labels)
by_len = test.groupby("len_bin", observed=True).agg(n=("ok", "size"), acc=("ok", "mean"), conf=("conf", "mean"))
R["acc_by_length"] = {str(k): {"n": int(v.n), "acc": round(v.acc, 3)} for k, v in by_len.iterrows()}
print("\n== H3a: acurácia por tamanho do ticket (tokens)"); print(by_len.round(3).to_string())

# ---------------------------------------------------------------- H6: confiança x cobertura
print("\n== H6: se o sistema só rotear sozinho acima do limiar de confiança...")
tiers = []
for t in [0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95]:
    m = test["conf"] >= t
    tiers.append({"thr": t, "coverage": round(m.mean(), 3), "acc_auto": round(test.loc[m, "ok"].mean(), 4),
                  "errors_per_1000_auto": round(1000 * (1 - test.loc[m, "ok"].mean()), 1)})
    print(f"   conf >= {t:.2f}: cobre {m.mean():.1%} do volume, acerto {test.loc[m,'ok'].mean():.2%} "
          f"({1000*(1-test.loc[m,'ok'].mean()):.0f} erros a cada 1.000 roteados)")
R["confidence_tiers"] = tiers
# calibração: confiança prevista vs acerto real
cal = test.groupby(pd.cut(test["conf"], [0, .4, .5, .6, .7, .8, .9, 1.0]), observed=True).agg(
    n=("ok", "size"), conf_media=("conf", "mean"), acerto=("ok", "mean"))
print("\n== calibração (confiança média vs acerto real por faixa)"); print(cal.round(3).to_string())
R["calibration"] = [{"bin": str(k), "n": int(v.n), "conf": round(v.conf_media, 3), "acc": round(v.acerto, 3)}
                    for k, v in cal.iterrows()]
# limiar por fila: menor limiar com acerto >= 95% nos tickets da fila prevista
per_q = {}
for q in classes:
    sub = test[test["pred"] == q]
    best = None
    for t in np.arange(0.5, 0.99, 0.01):
        s = sub[sub["conf"] >= t]
        if len(s) >= 30 and s["ok"].mean() >= 0.95:
            best = {"thr": round(float(t), 2), "coverage_of_pred": round(len(s) / max(len(sub), 1), 3),
                    "acc": round(float(s["ok"].mean()), 3)}
            break
    per_q[q] = best
R["per_queue_threshold_95"] = per_q
print("\n== limiar por fila para >=95% de acerto (None = fila nunca chega a 95%: sempre humano)")
for q, b in per_q.items():
    print(f"   {q:22s} {b}")

# ---------------------------------------------------------------- #5: curva de aprendizado
print("\n== #5 curva de aprendizado (mesmo teste; 3 sementes por tamanho)")
curve = []
for size in [250, 500, 1000, 2000, 4000, 8000, 16000, len(train)]:
    accs = []
    for sd in range(3):
        sub = train.sample(min(size, len(train)), random_state=sd)
        v, m = make_model()
        if sub["queue"].nunique() < len(classes):
            continue
        m.fit(v.fit_transform(sub["text"]), sub["queue"])
        accs.append(accuracy_score(test["queue"], m.predict(v.transform(test["text"]))))
        if size == len(train):
            break
    curve.append({"n_labeled": int(min(size, len(train))), "acc_mean": round(float(np.mean(accs)), 3),
                  "acc_std": round(float(np.std(accs)), 3)})
    print(f"   {min(size, len(train)):6d} tickets rotulados -> acurácia {np.mean(accs):.3f} ± {np.std(accs):.3f}")
R["learning_curve"] = curve

for i, c in enumerate(classes):  # probabilidade por fila: usada na trava de filas sensíveis (04)
    test[f"p_{c}"] = proba[:, i].round(4)
test[["text", "queue", "pred", "conf", "ok", "n_tok", "group"] + [f"p_{c}" for c in classes]].to_csv(
    out_dir / "ds2_test_predictions.csv", index=False)
(out_dir / "ds2_core_results.json").write_text(json.dumps(R, indent=2, ensure_ascii=False, default=float))

# O protótipo usa EXATAMENTE este modelo (treinado só no split de treino), para que os limiares
# medidos aqui valham para ele. Não é commitado (.gitignore); este script o recria.
import joblib  # noqa: E402
model_dir = out_dir.parent / "models"
model_dir.mkdir(exist_ok=True)
joblib.dump({"vectorizer": vec, "clf": clf, "per_queue_threshold_95": R["per_queue_threshold_95"]},
            model_dir / "router.joblib", compress=3)
print(f"modelo salvo em {model_dir / 'router.joblib'}")
print(f"\nresultados salvos em {out_dir}")

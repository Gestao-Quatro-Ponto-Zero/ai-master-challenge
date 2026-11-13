"""Fase 4 — Etapas 3, 4 e 9: modelos, avaliação no teste, calibração, thresholds empíricos, sensibilidade, salvamento."""
import json, time, warnings, joblib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.dummy import DummyClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import f1_score, classification_report, confusion_matrix, precision_recall_fscore_support, accuracy_score
from text_prep import preprocess
warnings.filterwarnings("ignore")
SEED = 42
t0 = time.time()
tr, va, te = (pd.read_csv(f"splits/{s}.csv") for s in ["train", "val", "test"])
for d in (tr, va, te):
    d["pp"] = d.Document.map(preprocess)
CLS = sorted(tr.Topic_group.unique())
TF = dict(max_features=50000, ngram_range=(1, 2), sublinear_tf=True)
R = {"models": []}


def f1m(y, p): return round(float(f1_score(y, p, average="macro")), 4)


def mk(clf): return Pipeline([("tfidf", TfidfVectorizer(**TF)), ("clf", clf)])


# ---------- Etapa 3: seleção no conjunto de validação ----------
cands = [("M0_dummy_most_frequent", {}, DummyClassifier(strategy="most_frequent"))]
for C in [0.1, 1, 10]:
    cands.append(("M1_tfidf_logreg", {"C": C}, LogisticRegression(C=C, max_iter=1000, class_weight="balanced", solver="lbfgs")))
for C in [0.1, 0.5, 1]:
    cands.append(("M2_tfidf_linearsvc", {"C": C}, LinearSVC(C=C, class_weight="balanced", max_iter=2000)))
fitted = {}
from joblib import Parallel, delayed
def _fit(name, prm, clf):
    s = time.time(); p = mk(clf).fit(tr.pp, tr.Topic_group)
    pv = p.predict(va.pp); ptr = p.predict(tr.pp)
    return name, prm, p, dict(model=name, params=prm, val_f1_macro=f1m(va.Topic_group, pv), val_f1_weighted=round(float(f1_score(va.Topic_group, pv, average="weighted")), 4),
               val_accuracy=round(float(accuracy_score(va.Topic_group, pv)), 4), train_f1_macro=f1m(tr.Topic_group, ptr), fit_s=round(time.time() - s, 1))
for name, prm, p, rec in Parallel(n_jobs=7)(delayed(_fit)(*c) for c in cands):
    R["models"].append(rec); fitted[(name, str(prm))] = p; print(rec)
best = max([m for m in R["models"] if m["model"] != "M0_dummy_most_frequent"], key=lambda m: m["val_f1_macro"])
R["best_by_val"] = best
R["model3_needed"] = best["val_f1_macro"] < 0.75
best_clf = LogisticRegression(C=best["params"]["C"], max_iter=1000, class_weight="balanced", solver="lbfgs") if best["model"].startswith("M1") \
    else LinearSVC(C=best["params"]["C"], class_weight="balanced", max_iter=2000)

# ---------- calibração (escolhida no val por ECE top-label) ----------
def ece(conf, correct, nb=10):
    b = np.clip((conf * nb).astype(int), 0, nb - 1); e = 0
    for i in range(nb):
        m = b == i
        if m.any(): e += m.mean() * abs(correct[m].mean() - conf[m].mean())
    return round(float(e), 4)

cal_opts = {}
if best["model"].startswith("M1"):
    cal_opts["raw"] = fitted[(best["model"], str(best["params"]))]
for meth in ["sigmoid", "isotonic"]:
    cal_opts[meth] = mk(CalibratedClassifierCV(best_clf, method=meth, cv=5, n_jobs=5)).fit(tr.pp, tr.Topic_group)
R["calibration_val"] = {}
for k, p in cal_opts.items():
    P = p.predict_proba(va.pp); pred = p.classes_[P.argmax(1)]
    R["calibration_val"][k] = dict(ece=ece(P.max(1), pred == va.Topic_group.values), f1_macro=f1m(va.Topic_group, pred))
print(R["calibration_val"])
cal_choice = min(R["calibration_val"], key=lambda k: (R["calibration_val"][k]["ece"] - (0.0 if R["calibration_val"][k]["f1_macro"] >= best["val_f1_macro"] - 0.01 else -1)))
R["calibration_choice"] = cal_choice
final_est = best_clf if cal_choice == "raw" else CalibratedClassifierCV(best_clf, method=cal_choice, cv=5, n_jobs=5)
final = Pipeline([("tfidf", TfidfVectorizer(preprocessor=preprocess, **TF)), ("clf", final_est)]).fit(tr.Document, tr.Topic_group)

# ---------- thresholds empíricos (definidos no VAL, reportados no TESTE) ----------
GRID = [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
def cov_prec(df):
    P = final.predict_proba(df.Document); conf = P.max(1); pred = final.classes_[P.argmax(1)]; ok = pred == df.Topic_group.values
    rows = []
    for t in GRID:
        m = conf >= t
        rows.append(dict(threshold=t, coverage=round(float(m.mean()), 4), precision=round(float(ok[m].mean()), 4) if m.any() else None,
                         n=int(m.sum()), f1_macro_covered=f1m(df.Topic_group.values[m], pred[m]) if m.sum() > 50 else None))
    return rows, P, conf, pred, ok
cp_val, *_ = cov_prec(va)
cp_test, Pt, conf_t, pred_t, ok_t = cov_prec(te)
TARGET_HIGH, TARGET_LOW = 0.95, 0.90   # metas de precisão (proposta para validação de negócio)
def pick(rows, tgt):
    for r in rows:
        if r["precision"] is not None and r["precision"] >= tgt: return r["threshold"]
    return None
th_high, th_low = pick(cp_val, TARGET_HIGH), pick(cp_val, TARGET_LOW)
R["thresholds"] = dict(rule=f"menor limiar do grid cuja precisão no VAL >= meta; metas: AUTOMATIC {TARGET_HIGH}, piso p/ sugestão {TARGET_LOW}",
                       threshold_alto=th_high, threshold_baixo=th_low, coverage_precision_val=cp_val, coverage_precision_test=cp_test)
def at(rows, t): return next((r for r in rows if r["threshold"] == t), None)
R["thresholds"]["test_at_alto"] = at(cp_test, th_high); R["thresholds"]["test_at_baixo"] = at(cp_test, th_low)
R["thresholds"]["test_at_prior_0.60"] = at(cp_test, 0.60); R["thresholds"]["test_at_prior_0.85"] = at(cp_test, 0.85)
print(R["thresholds"]["threshold_alto"], R["thresholds"]["threshold_baixo"])

# ---------- Etapa 4: avaliação no TESTE ----------
yt = te.Topic_group.values
rep = classification_report(yt, pred_t, digits=4)
prf = precision_recall_fscore_support(yt, pred_t, labels=CLS)
R["test"] = dict(n=int(len(te)), f1_macro=f1m(yt, pred_t), f1_weighted=round(float(f1_score(yt, pred_t, average="weighted")), 4), accuracy=round(float(accuracy_score(yt, pred_t)), 4),
                 per_class={c: dict(precision=round(float(prf[0][i]), 4), recall=round(float(prf[1][i]), 4), f1=round(float(prf[2][i]), 4), support=int(prf[3][i])) for i, c in enumerate(CLS)},
                 ece=ece(conf_t, ok_t))
dummy_te = fitted[("M0_dummy_most_frequent", "{}")].predict(te.pp)
R["test"]["dummy_f1_macro"] = f1m(yt, dummy_te)
R["test"]["short_subset"] = dict(n=int(te.short_flag.sum()), accuracy=round(float(ok_t[te.short_flag.values].mean()), 4) if te.short_flag.any() else None)
open("evaluation/metrics_report.txt", "w").write(
    f"Modelo final: {best['model']} {best['params']} | calibração: {cal_choice}\nConjunto de TESTE (n={len(te)}), nunca usado em treino/ajuste\n"
    f"F1-macro = {R['test']['f1_macro']} | F1-weighted = {R['test']['f1_weighted']} | accuracy = {R['test']['accuracy']} | ECE = {R['test']['ece']}\n"
    f"Baseline ingênuo (most_frequent) F1-macro no teste = {R['test']['dummy_f1_macro']}\n\n" + rep)
cm = confusion_matrix(yt, pred_t, labels=CLS); cmn = confusion_matrix(yt, pred_t, labels=CLS, normalize="true")
R["test"]["confusion_matrix"] = cm.tolist(); R["test"]["labels"] = CLS
pd.DataFrame(cm, index=CLS, columns=CLS).to_csv("evaluation/confusion_matrix.csv")
pd.DataFrame(cmn.round(4), index=CLS, columns=CLS).to_csv("evaluation/confusion_matrix_normalized.csv")
for M, fn, fmt, tt in [(cm, "confusion_matrix.png", "d", "absoluta"), (cmn, "confusion_matrix_normalized.png", ".2f", "normalizada por linha (recall)")]:
    fig, ax = plt.subplots(figsize=(10, 8)); im = ax.imshow(M, cmap="Blues")
    ax.set_xticks(range(8)); ax.set_yticks(range(8)); ax.set_xticklabels(CLS, rotation=40, ha="right"); ax.set_yticklabels(CLS)
    for i in range(8):
        for j in range(8):
            ax.text(j, i, format(M[i, j], fmt), ha="center", va="center", color="white" if M[i, j] > M.max() / 2 else "black", fontsize=9)
    ax.set_xlabel("Predito"); ax.set_ylabel("Real"); ax.set_title(f"Matriz de confusão — teste (n={len(te)}) — {tt}"); fig.colorbar(im); fig.tight_layout(); fig.savefig("evaluation/" + fn, dpi=130); plt.close(fig)
f1s = sorted(((c, R["test"]["per_class"][c]["f1"]) for c in CLS), key=lambda x: x[1])
fig, ax = plt.subplots(figsize=(9, 5)); ax.barh([c for c, _ in f1s], [v for _, v in f1s], color="#2b6cb0")
for i, (_, v) in enumerate(f1s): ax.text(v + 0.005, i, f"{v:.3f}", va="center")
ax.axvline(R["test"]["f1_macro"], ls="--", c="gray"); ax.set_xlim(0, 1.05); ax.set_xlabel("F1 (teste)"); ax.set_title(f"F1 por categoria — F1-macro {R['test']['f1_macro']}"); fig.tight_layout(); fig.savefig("evaluation/f1_by_category.png", dpi=130); plt.close(fig)

# erros mais graves nas 2 piores categorias
worst2 = [c for c, _ in f1s[:2]]; R["test"]["worst2"] = worst2
err = te.assign(pred=pred_t, conf_pred=conf_t, p_true=[Pt[i, list(final.classes_).index(y)] for i, y in enumerate(yt)])
err = err[(err.pred != err.Topic_group) & err.Topic_group.isin(worst2)]
rows = []
for c in worst2:
    e = err[err.Topic_group == c].sort_values("conf_pred", ascending=False).head(10)
    for _, r in e.iterrows():
        rows.append(dict(categoria_real=c, predita=r.pred, conf_predita=round(r.conf_pred, 4), prob_classe_real=round(r.p_true, 4), n_words=int(r.n_words), texto=r.Document[:400]))
pd.DataFrame(rows).to_csv("evaluation/error_analysis_worst2.csv", index=False)
R["test"]["error_pred_dist_worst2"] = {c: err[err.Topic_group == c].pred.value_counts().to_dict() for c in worst2}

# calibração (teste)
bins = np.linspace(0, 1, 11); b = np.clip(np.digitize(conf_t, bins) - 1, 0, 9)
R["test"]["reliability"] = [dict(bin=f"{bins[i]:.1f}-{bins[i+1]:.1f}", n=int((b == i).sum()), mean_conf=round(float(conf_t[b == i].mean()), 4), accuracy=round(float(ok_t[b == i].mean()), 4)) for i in range(10) if (b == i).any()]
raw_name = "raw" if "raw" in cal_opts else "sigmoid"
fig, ax = plt.subplots(figsize=(6, 6)); rl = R["test"]["reliability"]
ax.plot([0, 1], [0, 1], "--", c="gray"); ax.plot([r["mean_conf"] for r in rl], [r["accuracy"] for r in rl], "o-", label=f"{cal_choice} (ECE={R['test']['ece']})")
ax.set_xlabel("Confiança média (prob. máx.)"); ax.set_ylabel("Acurácia observada"); ax.legend(); ax.set_title("Reliability diagram — teste"); fig.tight_layout(); fig.savefig("evaluation/calibration_reliability.png", dpi=130); plt.close(fig)
# raw (não calibrado) no teste para comparação
if "raw" in cal_opts:
    Pr = cal_opts["raw"].predict_proba(te.pp); cr = Pr.max(1); okr = cal_opts["raw"].classes_[Pr.argmax(1)] == yt; br = np.clip(np.digitize(cr, bins) - 1, 0, 9)
    R["test"]["reliability_raw"] = [dict(n=int((br == i).sum()), mean_conf=round(float(cr[br == i].mean()), 4), accuracy=round(float(okr[br == i].mean()), 4)) for i in range(10) if (br == i).any()]
    R["test"]["ece_raw"] = ece(cr, okr)

# ---------- sensibilidade da limpeza (mesmo split por folds; mesmo teste limpo) ----------
allr = pd.read_csv("splits/all_rows_assignment.csv")
trn_all = allr[allr.split == "train"].copy(); trn_all["pp"] = trn_all.Document.map(preprocess)
variants = {
    "A_sujo_sem_limpeza": trn_all,
    "B_conservador_principal": trn_all[trn_all.status == "clean"],
    "C_conservador_sem_curtos": trn_all[(trn_all.status == "clean") & ~trn_all.short_flag],
    "D_agressivo": trn_all[trn_all.aggressive_keep],
}
R["sensitivity"] = {}
from joblib import Parallel, delayed
def _fit_var(k, d):
    p = mk(LogisticRegression(C=best["params"]["C"], max_iter=1000, class_weight="balanced") if best["model"].startswith("M1") else LinearSVC(C=best["params"]["C"], class_weight="balanced", max_iter=2000)).fit(d.pp, d.Topic_group)
    pv = p.predict(te.pp)
    return k, dict(n_train=int(len(d)), test_f1_macro=f1m(yt, pv), test_short_acc=round(float((pv[te.short_flag.values] == yt[te.short_flag.values]).mean()), 4))
for k, v in Parallel(n_jobs=4)(delayed(_fit_var)(k, d) for k, d in variants.items()):
    R["sensitivity"][k] = v; print(k, v)
# teste "sujo" (inclui quarentena do fold de teste) para o modelo principal
q_te = allr[(allr.split == "test") & (allr.status == "quarantine")]
if len(q_te):
    pq = final.predict(q_te.Document); R["sensitivity"]["quarantine_test_fold_accuracy"] = dict(n=int(len(q_te)), accuracy=round(float((pq == q_te.Topic_group.values).mean()), 4))

# ---------- Etapa 9: salvar ----------
joblib.dump(final, "model/classifier_pipeline.pkl")
R["runtime_s"] = round(time.time() - t0, 1)
json.dump(R, open("evaluation/results.json", "w"), indent=1, ensure_ascii=False, default=str)
pd.DataFrame(cp_test).to_csv("evaluation/coverage_precision_test.csv", index=False); pd.DataFrame(cp_val).to_csv("evaluation/coverage_precision_val.csv", index=False)

# ---------- gráficos plotly (inline) ----------
z = cmn.round(3)
fig = go.Figure(go.Heatmap(z=z, x=CLS, y=CLS, colorscale="Blues", text=[[f"{z[i][j]:.2f}<br>({cm[i][j]})" for j in range(8)] for i in range(8)], texttemplate="%{text}", hovertemplate="Real %{y}<br>Predito %{x}<br>%{z:.3f}<extra></extra>"))
fig.update_layout(title=f"Matriz de confusão normalizada (recall) — teste n={len(te)}", xaxis_title="Predito", yaxis_title="Real", yaxis_autorange="reversed", height=620, xaxis=dict(automargin=True), yaxis=dict(automargin=True))
fig.write_json("charts/ml_confusion_matrix.json")
fig = go.Figure(go.Bar(y=[c for c, _ in f1s], x=[v for _, v in f1s], orientation="h", text=[f"{v:.3f}" for _, v in f1s], textposition="outside",
                       customdata=[[R["test"]["per_class"][c]["precision"], R["test"]["per_class"][c]["recall"], R["test"]["per_class"][c]["support"]] for c, _ in f1s],
                       hovertemplate="%{y}<br>F1 %{x:.3f}<br>Precisão %{customdata[0]:.3f}<br>Recall %{customdata[1]:.3f}<br>Suporte %{customdata[2]}<extra></extra>"))
fig.add_vline(x=R["test"]["f1_macro"], line_dash="dash", annotation_text=f"F1-macro {R['test']['f1_macro']}")
fig.update_layout(title="F1 por categoria — conjunto de teste", xaxis_title="F1", xaxis_range=[0, 1.08], yaxis=dict(automargin=True))
fig.write_json("charts/ml_f1_by_category.json")
fig = go.Figure()
for rows_, nm, dash in [(cp_val, "Validação", "dot"), (cp_test, "Teste", "solid")]:
    fig.add_scatter(x=[r["threshold"] for r in rows_], y=[r["coverage"] for r in rows_], name=f"Cobertura ({nm})", line=dict(dash=dash))
    fig.add_scatter(x=[r["threshold"] for r in rows_], y=[r["precision"] for r in rows_], name=f"Precisão ({nm})", line=dict(dash=dash))
for t, lab in [(th_low, "limiar baixo"), (th_high, "limiar alto")]:
    if t is not None: fig.add_vline(x=t, line_dash="dash", annotation_text=f"{lab} = {t}")
fig.update_layout(title="Cobertura vs. precisão por limiar de confiança (prob. máxima)", xaxis_title="Limiar", yaxis_title="Proporção", yaxis_tickformat=".0%", hovermode="x unified")
fig.write_json("charts/ml_coverage_precision.json")
fig = go.Figure(); fig.add_scatter(x=[0, 1], y=[0, 1], mode="lines", name="Calibração perfeita", line=dict(dash="dash", color="gray"))
fig.add_scatter(x=[r["mean_conf"] for r in rl], y=[r["accuracy"] for r in rl], mode="lines+markers", name=f"Modelo final ({cal_choice}) ECE={R['test']['ece']}", customdata=[r["n"] for r in rl], hovertemplate="conf %{x:.3f}<br>acurácia %{y:.3f}<br>n=%{customdata}<extra></extra>")
if "reliability_raw" in R["test"]:
    rr = R["test"]["reliability_raw"]; fig.add_scatter(x=[r["mean_conf"] for r in rr], y=[r["accuracy"] for r in rr], mode="lines+markers", name=f"LR sem calibração ECE={R['test']['ece_raw']}", visible="legendonly")
fig.update_layout(title="Reliability diagram — teste", xaxis_title="Confiança média", yaxis_title="Acurácia observada", xaxis_range=[0, 1], yaxis_range=[0, 1])
fig.write_json("charts/ml_calibration.json")
print("TEST", R["test"]["f1_macro"], R["test"]["per_class"], "runtime", R["runtime_s"])

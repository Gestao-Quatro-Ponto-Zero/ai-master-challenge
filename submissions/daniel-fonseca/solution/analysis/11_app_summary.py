"""Números que o app lê do Supabase e que ainda não estavam em arquivo (PRD v1.1, Painel).

1. Visão geral do DS1 (status, tempo coerente, CSAT com IC).
2. p-valor por dimensão e métrica (mesmos testes de 02_diagnostic_cuts.py): qui-quadrado do status
   (vale para "% sem 1ª resposta" e "% aguardando cliente"), Kruskal-Wallis para tempo e CSAT.
3. A "armadilha" do ranking: pior e melhor combinação canal × prioridade × tipo e o p-valor conjunto.
4. R² e R² ajustado do CSAT com todas as variáveis.
5. Entradas do ROI (ADR-0009/0010): % do DS1 elegível para autonomia (fora reembolso, cancelamento
   e prioridade Critical) e % de casos com autonomia da IA entre os não sensíveis no holdout do DS2.

Saída: solution/analysis/output/app_summary.json
Uso: .venv/bin/python solution/analysis/11_app_summary.py
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import linalg, stats

warnings.filterwarnings("ignore", category=RuntimeWarning)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import load_raw_datasets as raw  # noqa: E402

OUT = ROOT / "solution/analysis/output"
df = pd.read_csv(ROOT / "data/raw/ds1_customer_support/customer_support_tickets.csv")
df["hours"] = (pd.to_datetime(df["Time to Resolution"]) - pd.to_datetime(df["First Response Time"])).dt.total_seconds() / 3600
df["coherent"] = df["hours"] >= 0
closed = df[df["Ticket Status"] == "Closed"]
coh = closed[closed["coherent"]]
CSAT = "Customer Satisfaction Rating"
DIMS = {"Ticket Channel": "canal", "Ticket Priority": "prioridade", "Ticket Type": "tipo",
        "Ticket Subject": "assunto", "Product Purchased": "produto"}

out = {"overview": {
    "n": int(len(df)),
    "pct_open": round(float(df["Ticket Status"].eq("Open").mean()), 4),
    "pct_pending": round(float(df["Ticket Status"].eq("Pending Customer Response").mean()), 4),
    "pct_closed": round(float(df["Ticket Status"].eq("Closed").mean()), 4),
    "n_closed": int(len(closed)),
    "pct_coherent_closed": round(len(coh) / len(closed), 4),
    "hours_mean_coherent": round(float(coh["hours"].mean()), 2),
    "hours_median_coherent": round(float(coh["hours"].median()), 2),
    "hours_p90_coherent": round(float(coh["hours"].quantile(.9)), 2),
    "csat_mean": round(float(closed[CSAT].mean()), 3),
    "csat_ci_low": round(float(closed[CSAT].mean() - 1.96 * closed[CSAT].sem()), 3),
    "csat_ci_high": round(float(closed[CSAT].mean() + 1.96 * closed[CSAT].sem()), 3),
}, "tests": []}

for col, label in DIMS.items():
    p_status = float(stats.chi2_contingency(pd.crosstab(df[col], df["Ticket Status"]))[1])
    p_hours = float(stats.kruskal(*[s for _, s in coh.groupby(col)["hours"]]).pvalue)
    p_csat = float(stats.kruskal(*[s[CSAT] for _, s in closed.groupby(col)]).pvalue)
    for metric, p in (("pct_open", p_status), ("pct_pending", p_status), ("hours_median_coherent", p_hours), ("csat_mean", p_csat)):
        out["tests"].append({"dimension": label, "metric": metric, "p_value": round(p, 4), "significant": p < 0.05,
                             "test": "qui-quadrado (status)" if metric.startswith("pct") else "Kruskal-Wallis"})

# armadilha do ranking: combinações canal × prioridade × tipo com CSAT
combo = closed.groupby(["Ticket Channel", "Ticket Priority", "Ticket Type"])[CSAT]
agg = combo.agg(["mean", "size"]).reset_index()
worst, best = agg.loc[agg["mean"].idxmin()], agg.loc[agg["mean"].idxmax()]
p_combo = float(stats.kruskal(*[s for _, s in combo]).pvalue)
out["ranking_trap"] = {
    "n_combinations": int(len(agg)), "p_value": round(p_combo, 2),
    "worst": {"canal": worst["Ticket Channel"], "prioridade": worst["Ticket Priority"], "tipo": worst["Ticket Type"],
              "csat": round(float(worst["mean"]), 2), "n": int(worst["size"])},
    "best": {"canal": best["Ticket Channel"], "prioridade": best["Ticket Priority"], "tipo": best["Ticket Type"],
             "csat": round(float(best["mean"]), 2), "n": int(best["size"])},
}

# R² do CSAT com todas as variáveis (mesmo modelo de 02)
X = pd.get_dummies(closed[list(DIMS) + ["Customer Gender"]], drop_first=True).astype(float)
X["age"], X["hours"] = closed["Customer Age"], closed["hours"]
X = np.column_stack([np.ones(len(X)), X.values])
y = closed[CSAT].values
beta, *_ = linalg.lstsq(X, y)
fitted = (X * beta).sum(axis=1)
r2 = 1 - ((y - fitted) ** 2).sum() / ((y - y.mean()) ** 2).sum()
k = X.shape[1] - 1
out["csat_model"] = {"k": int(k), "r2": round(float(r2), 4), "r2_adj": round(float(1 - (1 - r2) * (len(y) - 1) / (len(y) - k - 1)), 4)}

# ROI: elegibilidade no DS1
ineligible = df["Ticket Type"].isin(["Refund request", "Cancellation request"]) | df["Ticket Priority"].eq("Critical")
out["roi_inputs"] = {"ds1_eligible_share": round(float(1 - ineligible.mean()), 4),
                     "ds1_eligible_rule": "fora: Refund request, Cancellation request e prioridade Critical (sempre humano)"}

# ROI: autonomia da IA entre não sensíveis no holdout do DS2 (mesma política de 08)
d2 = raw.ds2(); train, test = d2[d2.split == "train"], d2[d2.split == "test"]
classes = sorted(d2.topic_group.unique()); cidx = {c: i for i, c in enumerate(classes)}
ytr = np.array([cidx[c] for c in train.topic_group]); yte = np.array([cidx[c] for c in test.topic_group])
E = np.load(ROOT / "data/embeddings/ds2_te3s_1536.npy").astype(np.float32)[:, :512]
E /= np.linalg.norm(E, axis=1, keepdims=True)
share = np.zeros((len(test), len(classes)))
for s in range(0, len(test), 1000):
    S = E[test.index.values[s:s + 1000]] @ E[train.index.values].T
    top = np.argpartition(-S, 50, axis=1)[:, :50]; w = np.take_along_axis(S, top, 1).clip(0) ** 16
    v = np.zeros((len(top), len(classes))); np.add.at(v, (np.repeat(np.arange(len(top)), 50), ytr[top].ravel()), w.ravel())
    share[s:s + 1000] = v / v.sum(1, keepdims=True)
pred, conf = share.argmax(1), share.max(1)
SENS = [cidx["HR Support"], cidx["Administrative rights"]]
lvl3 = np.isin(pred, SENS) | (share[:, SENS].sum(1) >= 0.3) | (conf < 0.5)
lvl1 = ~lvl3 & (conf >= 0.9)
true_sens = np.isin(yte, SENS)
out["roi_inputs"].update({
    "ds2_autonomy_share_all": round(float(lvl1.mean()), 4),
    "ds2_autonomy_share_non_sensitive": round(float(lvl1[~true_sens].mean()), 4),
    "ds2_autonomy_precision": round(float((pred[lvl1] == yte[lvl1]).mean()), 4),
    "autonomy_rule": "confiança ≥ 0,9, categoria não sensível, < 30% dos votos em categoria sensível",
})
out["roi_inputs"]["total_autonomy_share"] = round(out["roi_inputs"]["ds1_eligible_share"] * out["roi_inputs"]["ds2_autonomy_share_non_sensitive"], 4)

print(json.dumps(out, ensure_ascii=False, indent=1))
(OUT / "app_summary.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))

"""Dados extras para o Painel e o "Como foi feito" do app (PRD §4.1 e §4.7).

1. Intervalos de confiança de 95% de cada barra do gráfico "Onde o fluxo trava" (diagnóstico do DS1):
   - % sem 1ª resposta e % aguardando cliente: intervalo de Wilson;
   - tempo 1ª resposta → resolução (mediana, só registros coerentes): bootstrap de 2.000 reamostras, seed 42.
   O IC do CSAT já está em diagnostic_cuts.csv (média ± 1,96 × erro padrão).
2. Grupo "Outros" do produto: o gráfico mostra os 10 maiores produtos e agrega os 32 restantes.
3. Matriz de confusão do RAG de produção (mesma política de 08_rag_only_policy.py: 512 dims, k=50,
   peso sim^16, vizinhos só do treino) no holdout de 9.567 tickets do DS2.

Saídas: solution/analysis/output/diagnostic_ci.json e output/rag_confusion.json
Publicar no Supabase: .venv/bin/python scripts/load_analysis.py
Uso: .venv/bin/python solution/analysis/12_painel_extras.py
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=RuntimeWarning)
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "solution/analysis/output"
sys.path.insert(0, str(ROOT / "scripts"))
import load_raw_datasets as raw  # noqa: E402

Z = 1.959964
RNG = np.random.default_rng(42)
B = 2000


def wilson(k: int, n: int) -> list[float]:
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    den = 1 + Z**2 / n
    mid = (p + Z**2 / (2 * n)) / den
    half = Z * np.sqrt(p * (1 - p) / n + Z**2 / (4 * n**2)) / den
    return [round(float(mid - half), 4), round(float(mid + half), 4)]


def median_ci(x: np.ndarray) -> list[float]:
    if len(x) < 2:
        return [float("nan"), float("nan")]
    idx = RNG.integers(0, len(x), size=(B, len(x)))
    meds = np.median(x[idx], axis=1)
    return [round(float(np.quantile(meds, 0.025)), 4), round(float(np.quantile(meds, 0.975)), 4)]


def group_stats(g: pd.DataFrame) -> dict:
    closed = g[g["Ticket Status"] == "Closed"]
    coh = closed[closed["hours"] >= 0]["hours"].to_numpy()
    csat = closed[CSAT]
    n = len(g)
    k_open = int((g["Ticket Status"] == "Open").sum())
    k_pend = int((g["Ticket Status"] == "Pending Customer Response").sum())
    sem = float(csat.sem()) if len(csat) > 1 else float("nan")
    return {
        "n": n,
        "pct_open": round(k_open / n, 4),
        "pct_open_ci": wilson(k_open, n),
        "pct_pending": round(k_pend / n, 4),
        "pct_pending_ci": wilson(k_pend, n),
        "n_closed": int(len(closed)),
        "csat_mean": round(float(csat.mean()), 4),
        "csat_ci": [round(float(csat.mean() - Z * sem), 4), round(float(csat.mean() + Z * sem), 4)],
        "hours_median_coherent": round(float(np.median(coh)), 4) if len(coh) else None,
        "hours_ci": median_ci(coh),
        "n_coherent": int(len(coh)),
    }


# ---------- 1 e 2: diagnóstico do DS1 ----------
df = pd.read_csv(ROOT / "data/raw/ds1_customer_support/customer_support_tickets.csv")
df["hours"] = (pd.to_datetime(df["Time to Resolution"]) - pd.to_datetime(df["First Response Time"])).dt.total_seconds() / 3600
CSAT = "Customer Satisfaction Rating"
DIMS = {"Ticket Channel": "canal", "Ticket Priority": "prioridade", "Ticket Type": "tipo",
        "Ticket Subject": "assunto", "Product Purchased": "produto"}

rows = []
for col, label in DIMS.items():
    for value, g in df.groupby(col):
        s = group_stats(g)
        rows.append({"dimension": label, "value": value, **{k: s[k] for k in ("pct_open_ci", "pct_pending_ci", "hours_ci", "n_coherent")}})

top10 = df["Product Purchased"].value_counts().head(10).index
rest = df[~df["Product Purchased"].isin(top10)]
outros = {"dimension": "produto", "value": "Outros", "groups": int(rest["Product Purchased"].nunique()), **group_stats(rest)}

# Linha "Geral" do seletor de dimensão (todos os tickets). Calculada depois dos grupos para não
# mudar a sequência do bootstrap dos intervalos já publicados.
geral = {"dimension": "geral", "value": "Todos os tickets", **group_stats(df)}

ci_out = {
    "method": {
        "proportions": "Wilson 95%",
        "hours": f"bootstrap da mediana, {B} reamostras, seed 42, só fechados com resolução após a 1ª resposta",
        "csat": "média ± 1,96 × erro padrão (fechados)",
    },
    "rows": rows,
    "produto_top10": list(top10),
    "produto_outros": outros,
    "geral": geral,
}
(OUT / "diagnostic_ci.json").write_text(json.dumps(ci_out, ensure_ascii=False, indent=1))
print(f"diagnostic_ci.json: {len(rows)} grupos; Outros = {outros['groups']} produtos, n = {outros['n']}")

# ---------- 3: matriz de confusão do RAG ----------
ds2 = raw.ds2()
train, test = ds2[ds2.split == "train"], ds2[ds2.split == "test"]
classes = sorted(ds2.topic_group.unique())
cidx = {c: i for i, c in enumerate(classes)}
ytr = np.array([cidx[c] for c in train.topic_group])
yte = np.array([cidx[c] for c in test.topic_group])
E = np.load(ROOT / "data/embeddings/ds2_te3s_1536.npy").astype(np.float32)[:, :512]
E /= np.linalg.norm(E, axis=1, keepdims=True)
K, P = 50, 16
share = np.zeros((len(test), len(classes)))
for s in range(0, len(test), 1000):
    S = E[test.index.values[s:s + 1000]] @ E[train.index.values].T
    top = np.argpartition(-S, K, axis=1)[:, :K]
    w = np.take_along_axis(S, top, 1).clip(0) ** P
    v = np.zeros((len(top), len(classes)))
    np.add.at(v, (np.repeat(np.arange(len(top)), K), ytr[top].ravel()), w.ravel())
    share[s:s + 1000] = v / v.sum(1, keepdims=True)
pred = share.argmax(1)
M = np.zeros((len(classes), len(classes)), dtype=int)
np.add.at(M, (yte, pred), 1)
recall = M.diagonal() / M.sum(1)
precision = M.diagonal() / M.sum(0)
conf_out = {
    "config": {"dims": 512, "k": K, "power": P, "n_test": int(len(test))},
    "labels": classes,
    "matrix": M.tolist(),
    "rows_are": "categoria real",
    "cols_are": "categoria prevista",
    "accuracy": round(float(M.diagonal().sum() / M.sum()), 4),
    "recall": {c: round(float(r), 4) for c, r in zip(classes, recall)},
    "precision": {c: round(float(p), 4) for c, p in zip(classes, precision)},
}
(OUT / "rag_confusion.json").write_text(json.dumps(conf_out, ensure_ascii=False, indent=1))
print(f"rag_confusion.json: acurácia {conf_out['accuracy']:.3f}")
worst = sorted(((M[i, j], classes[i], classes[j]) for i in range(len(classes)) for j in range(len(classes)) if i != j), reverse=True)[:3]
for n, t, p in worst:
    print(f"  maior confusão: {t} → {p}: {n}")

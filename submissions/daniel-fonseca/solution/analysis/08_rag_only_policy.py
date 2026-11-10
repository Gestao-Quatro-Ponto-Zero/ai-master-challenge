"""Política de 3 níveis com o RAG como classificador único (decisão do Daniel, ADR-0010).

Configuração: embeddings 512 dims, k=50 vizinhos, peso = similaridade^16 (melhor ajuste do 06).
Confiança = fração ponderada de votos da categoria vencedora.
Saída: solution/analysis/output/rag_only_policy.json
"""
import json, sys, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore", category=RuntimeWarning)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import load_raw_datasets as raw  # noqa: E402

df = raw.ds2(); train, test = df[df.split == "train"], df[df.split == "test"]
classes = sorted(df.topic_group.unique()); cidx = {c: i for i, c in enumerate(classes)}
ytr = np.array([cidx[c] for c in train.topic_group]); yte = np.array([cidx[c] for c in test.topic_group])
E = np.load(ROOT / "data/embeddings/ds2_te3s_1536.npy").astype(np.float32)[:, :512]
E /= np.linalg.norm(E, axis=1, keepdims=True)
K, P = 50, 16
share = np.zeros((len(test), len(classes)))
for s in range(0, len(test), 1000):
    S = E[test.index.values[s:s + 1000]] @ E[train.index.values].T
    top = np.argpartition(-S, K, axis=1)[:, :K]; w = np.take_along_axis(S, top, 1).clip(0) ** P
    v = np.zeros((len(top), len(classes))); np.add.at(v, (np.repeat(np.arange(len(top)), K), ytr[top].ravel()), w.ravel())
    share[s:s + 1000] = v / v.sum(1, keepdims=True)
pred, conf = share.argmax(1), share.max(1)
out = {"config": {"dims": 512, "k": K, "power": P}, "accuracy": round(float((pred == yte).mean()), 4), "curve": []}
print(f"RAG 512/k{K}/p{P}: acurácia {out['accuracy']:.3f}")
for t in (0.5, 0.7, 0.8, 0.85, 0.9, 0.95, 0.98):
    m = conf >= t
    out["curve"].append({"threshold": t, "coverage": round(float(m.mean()), 4), "precision": round(float((pred[m] == yte[m]).mean()), 4)})
    print(f"  confiança ≥ {t:.2f}: cobertura {m.mean():.1%} → precisão {(pred[m] == yte[m]).mean():.1%}")
SENS = [cidx["HR Support"], cidx["Administrative rights"]]
T1, T3 = 0.9, 0.5
sens = np.isin(pred, SENS) | (share[:, SENS].sum(1) >= 0.3)  # sensível previsto OU ≥30% dos votos em categoria sensível
lvl3 = sens | (conf < T3); lvl1 = ~lvl3 & (conf >= T1); lvl2 = ~lvl3 & ~lvl1
tiers = {n: {"share": round(float(m.mean()), 4), "precision": round(float((pred[m] == yte[m]).mean()), 4)}
         for n, m in (("1_automatico", lvl1), ("2_revisao_humana", lvl2), ("3_so_humano", lvl3))}
true_sens = np.isin(yte, SENS)
tiers["sensitive_escapes"] = {"to_level_1": int((true_sens & lvl1).sum()), "to_level_2": int((true_sens & lvl2).sum()), "total_sensitive": int(true_sens.sum())}
out["tiers"] = tiers
out["rule"] = f"nível 3 = categoria sensível prevista ou ≥30% dos votos em categoria sensível ou confiança < {T3}; nível 1 = confiança ≥ {T1}; nível 2 = resto"
for n, v in tiers.items(): print(f"  {n}: {v}")
(ROOT / "solution/analysis/output/rag_only_policy.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))

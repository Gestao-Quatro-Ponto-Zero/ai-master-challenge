"""Lista de bloqueio do nível 1 (mitigação da ADR-0010): quantos falsos positivos ela gera?

Falso positivo = ticket do nível 1 que NÃO é sensível, mas contém um termo da lista e seria rebaixado para o nível 3
(custa automação, não segurança). "Escape pego" = ticket realmente sensível (HR Support / Administrative rights)
que estava no nível 1 e a lista rebaixaria.

Mesma política e mesmo holdout de 08_rag_only_policy.py. Busca por palavra inteira, no texto pré-processado do DS2.
Saída: solution/analysis/output/blocklist_eval.json
Uso: .venv/bin/python solution/analysis/10_blocklist_eval.py
"""
import json
import re
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore", category=RuntimeWarning)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import load_raw_datasets as raw  # noqa: E402

LISTS = {
    # termos de RH/jurídico estreitos: proposta para o fluxo
    "estreita": ["salary", "payroll", "bonus", "termination", "dismissal", "resignation", "lawsuit", "legal",
                 "harassment", "sick leave", "maternity"],
    # termos amplos testados e descartados: aparecem muito em pedidos comuns de TI
    "ampla": ["salary", "payroll", "bonus", "termination", "dismissal", "resignation", "lawsuit", "legal",
              "harassment", "sick leave", "maternity", "contract", "leaver", "absence", "admin rights",
              "administrator", "password"],
}

df = raw.ds2()
train, test = df[df.split == "train"], df[df.split == "test"]
classes = sorted(df.topic_group.unique())
cidx = {c: i for i, c in enumerate(classes)}
ytr = np.array([cidx[c] for c in train.topic_group])
yte = np.array([cidx[c] for c in test.topic_group])
E = np.load(ROOT / "data/embeddings/ds2_te3s_1536.npy").astype(np.float32)[:, :512]
E /= np.linalg.norm(E, axis=1, keepdims=True)
share = np.zeros((len(test), len(classes)))
for s in range(0, len(test), 1000):
    S = E[test.index.values[s:s + 1000]] @ E[train.index.values].T
    top = np.argpartition(-S, 50, axis=1)[:, :50]
    w = np.take_along_axis(S, top, 1).clip(0) ** 16
    v = np.zeros((len(top), len(classes)))
    np.add.at(v, (np.repeat(np.arange(len(top)), 50), ytr[top].ravel()), w.ravel())
    share[s:s + 1000] = v / v.sum(1, keepdims=True)
pred, conf = share.argmax(1), share.max(1)
SENS = [cidx["HR Support"], cidx["Administrative rights"]]
lvl3 = np.isin(pred, SENS) | (share[:, SENS].sum(1) >= 0.3) | (conf < 0.5)
lvl1 = ~lvl3 & (conf >= 0.9)
true_sens = np.isin(yte, SENS)
docs = test.document.values

out = {"level1_total": int(lvl1.sum()), "sensitive_escapes_level1": int((lvl1 & true_sens).sum()), "lists": {}}
for name, terms in LISTS.items():
    per_term, any_hit = {}, np.zeros(len(docs), bool)
    for t in terms:
        m = np.array([bool(re.search(rf"\b{re.escape(t)}\b", d)) for d in docs])
        any_hit |= m
        per_term[t] = {"false_positives_l1": int((m & lvl1 & ~true_sens).sum()), "escapes_caught": int((m & lvl1 & true_sens).sum())}
    fp = int((any_hit & lvl1 & ~true_sens).sum())
    out["lists"][name] = {
        "terms": terms,
        "false_positives_l1": fp,
        "false_positive_rate_l1": round(fp / int(lvl1.sum()), 4),
        "escapes_caught": int((any_hit & lvl1 & true_sens).sum()),
        "per_term": per_term,
    }
    print(f"{name}: {fp} falsos positivos em {int(lvl1.sum())} do nível 1 ({fp / lvl1.sum():.1%}); "
          f"escapes pegos {out['lists'][name]['escapes_caught']}/{out['sensitive_escapes_level1']}")
(ROOT / "solution/analysis/output/blocklist_eval.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))

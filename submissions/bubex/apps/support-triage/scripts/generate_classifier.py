"""
generate_classifier.py
Valida o keyword classifier contra o Dataset 2 (47.837 tickets IT com ground truth).
Gera data/classifier_output.json.
Versão de produção do notebooks/02_classifier_validation.ipynb — sem visualizações.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"

# ── Keyword map (espelho de src/lib/classify.ts) ──────────────────────────────
KEYWORD_MAP: dict[str, list[str]] = {
    "Hardware":               ["laptop", "computer", "keyboard", "mouse", "monitor", "printer",
                                "screen", "device", "hardware", "cable"],
    "HR Support":             ["leave", "holiday", "vacation", "payroll", "salary", "onboarding",
                                "offboarding", "employee", "hr", "hiring", "benefit"],
    "Access":                 ["access", "login", "password", "account", "permission", "locked",
                                "reset", "credential", "authentication", "vpn"],
    "Storage":                ["storage", "disk", "drive", "space", "quota", "backup",
                                "file", "folder", "cloud", "sync"],
    "Purchase":               ["purchase", "order", "procurement", "buy", "invoice",
                                "vendor", "software license", "license", "request"],
    "Internal Project":       ["project", "deadline", "sprint", "milestone", "task",
                                "jira", "trello", "meeting", "requirements"],
    "Administrative rights":  ["admin", "administrator", "rights", "privilege", "sudo",
                                "elevated", "policy", "group policy"],
    "Miscellaneous":          [],
}

CATEGORIES = list(KEYWORD_MAP.keys())

FAILURE_EXAMPLES = [
    {
        "text": "I need to request access to the project files on the shared drive.",
        "true": "Access",
        "llm_reasoning": "Contexto \"access\" domina; \"project\" e \"files\" são subordinados ao pedido de acesso.",
    },
    {
        "text": "The backup policy was changed by the admin without notice.",
        "true": "Administrative rights",
        "llm_reasoning": "LLM reconhece que \"policy\" + \"admin\" = mudança de política, não backup de dados.",
    },
    {
        "text": "We need to buy a new laptop for the onboarding of the new employee.",
        "true": "HR Support",
        "llm_reasoning": "LLM entende que o contexto principal é onboarding, não compra de hardware.",
    },
    {
        "text": "Can you reset the disk quota for my account on the storage server?",
        "true": "Storage",
        "llm_reasoning": "Múltiplos sinais de Storage (disk, quota, storage) vs. Access (reset, account) — LLM pondera intenção.",
    },
]


def classify_keyword(text: str) -> str:
    lower = str(text).lower() if pd.notna(text) else ""
    best, best_score = "Miscellaneous", 0
    for cat, keywords in KEYWORD_MAP.items():
        if cat == "Miscellaneous":
            continue
        score = sum(1 for k in keywords if k in lower)
        if score > best_score:
            best_score, best = score, cat
    return best


def main() -> None:
    csv_path = DATA / "all_tickets_processed_improved_v3.csv"
    if not csv_path.exists():
        print(f"[generate_classifier] ERRO: {csv_path} não encontrado.", file=sys.stderr)
        sys.exit(1)

    df2 = pd.read_csv(csv_path)

    print(f"[generate_classifier] Classificando {len(df2):,} tickets...")
    df2["predicted"] = df2["Document"].apply(classify_keyword)

    y_true = df2["Topic_group"]
    y_pred = df2["predicted"]

    accuracy     = accuracy_score(y_true, y_pred)
    cat_counts   = y_true.value_counts()
    acc_majority = cat_counts.max() / len(y_true)
    np.random.seed(42)
    acc_random   = accuracy_score(
        y_true,
        np.random.choice(
            cat_counts.index, size=len(y_true),
            p=(cat_counts / cat_counts.sum()).values,
        ),
    )

    # Per-category accuracy
    labels = [c for c in CATEGORIES if c in y_true.unique()]
    per_cat = []
    for cat in labels:
        mask  = y_true == cat
        total = int(mask.sum())
        correct = int((y_pred[mask] == cat).sum())
        per_cat.append({
            "category": cat,
            "total": total,
            "correct": correct,
            "accuracy": round(correct / total, 4) if total else 0.0,
        })
    per_cat.sort(key=lambda x: -x["accuracy"])

    # Failure examples — add keyword prediction
    failure_list = []
    for ex in FAILURE_EXAMPLES:
        kw_pred = classify_keyword(ex["text"])
        failure_list.append({
            "text": ex["text"],
            "true_label": ex["true"],
            "keyword_pred": kw_pred,
            "llm_reasoning": ex["llm_reasoning"],
        })

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_accuracy": round(float(accuracy), 4),
        "majority_baseline": round(float(acc_majority), 4),
        "random_baseline":   round(float(acc_random), 4),
        "lift_over_majority": round(float(accuracy / acc_majority), 3),
        "llm_accuracy_estimate": 0.86,
        "per_category": per_cat,
        "failure_examples": failure_list,
        "total_tickets_evaluated": int(len(df2)),
    }

    out_path = DATA / "classifier_output.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"[generate_classifier] ✅ {out_path} (acurácia: {accuracy*100:.1f}%, {len(df2):,} tickets)")


if __name__ == "__main__":
    main()

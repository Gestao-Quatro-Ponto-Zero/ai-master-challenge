"""Reproducible Out-of-Sample Benchmark, Selective Automation Curve & Domain-Shift Stress Test.

Generates `artifacts/benchmark_report.md` and `artifacts/benchmark_summary.json`
directly from code so README, UI, and artifacts remain 100% reconciled.
Supports both `python -m src.benchmark` and `python src/benchmark.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

# Allow running directly via `python src/benchmark.py` from `solution/`
_SOLUTION_ROOT = Path(__file__).resolve().parent.parent
if str(_SOLUTION_ROOT) not in sys.path:
    sys.path.insert(0, str(_SOLUTION_ROOT))

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import ComplementNB

from src.data_loader import audit_dataset1_forensics, load_support_datasets
from src.roi_calculator import build_standard_roi_scenarios
from src.triage_engine import (
    SupportTriageEngine,
    fit_triage_engine_from_dataframe,
)


def evaluate_dataset1_null_predictability(
    df_d1: pd.DataFrame, random_state: int = 42
) -> Dict[str, float]:
    """Evaluates linear TF-IDF + LogisticRegression predictability on an 80/20 split of Dataset 1."""
    texts = (
        df_d1["Ticket Subject"].fillna("")
        + " "
        + df_d1["Ticket Description"].fillna("")
    ).to_numpy(dtype=str)
    y_type = df_d1["Ticket Type"].fillna("").to_numpy(dtype=str)
    y_prio = df_d1["Ticket Priority"].fillna("").to_numpy(dtype=str)

    x_tr, x_te, yt_tr, yt_te, yp_tr, yp_te = train_test_split(
        texts,
        y_type,
        y_prio,
        test_size=0.20,
        random_state=random_state,
        stratify=y_type,
    )
    vec = TfidfVectorizer(max_features=10000, ngram_range=(1, 2), stop_words="english")
    x_tr_v = vec.fit_transform(x_tr)
    x_te_v = vec.transform(x_te)

    clf_type = LogisticRegression(max_iter=400, random_state=random_state).fit(
        x_tr_v, yt_tr
    )
    clf_prio = LogisticRegression(max_iter=400, random_state=random_state).fit(
        x_tr_v, yp_tr
    )

    pred_t = clf_type.predict(x_te_v)
    pred_p = clf_prio.predict(x_te_v)

    return {
        "d1_test_size": int(len(x_te)),
        "type_accuracy": float(accuracy_score(yt_te, pred_t)),
        "type_macro_f1": float(f1_score(yt_te, pred_t, average="macro")),
        "type_chance_baseline": 0.20,
        "priority_accuracy": float(accuracy_score(yp_te, pred_p)),
        "priority_macro_f1": float(f1_score(yp_te, pred_p, average="macro")),
        "priority_chance_baseline": 0.25,
    }


def run_full_support_benchmark(
    data_dir: Path | None = None,
    tier1_threshold: float = 0.80,
    tier2_threshold: float = 0.55,
) -> Dict[str, Any]:
    """
    Runs the complete out-of-sample evaluation across Dataset 1 and Dataset 2:
    1. Forensic statistical audit of Dataset 1 + linear predictability check
    2. Stratified 80/20 benchmark on Dataset 2 (N_train=38,269, N_test=9,568) + duplicate audit
    3. Selective coverage-vs-accuracy curve (raw confidence AND post-Guardrail/PAM Tier 1)
    4. Domain-shift containment test (passing Dataset 1 consumer tickets into Dataset 2 engine)
    5. Parametric ROI scenarios anchored on empirical test rates
    """
    df_d1, df_d2 = load_support_datasets(data_dir)
    _, d1_audit = audit_dataset1_forensics(df_d1, n_permutations=200)
    d1_null = evaluate_dataset1_null_predictability(df_d1)

    # Fit primary calibrated engine strictly on train_d2 via canonical anti-leakage entrypoint
    engine, train_d2, test_d2 = fit_triage_engine_from_dataframe(
        df_d2,
        test_size=0.20,
        random_state=42,
        tier1_threshold=tier1_threshold,
        tier2_threshold=tier2_threshold,
    )
    y_train = train_d2["Topic_group"].to_numpy(dtype=str)
    y_test = test_d2["Topic_group"].to_numpy(dtype=str)

    # Audit normalized text overlap between train_d2 and test_d2
    train_norm_set = set(
        train_d2["Document"].fillna("").str.strip().str.lower().tolist()
    )
    test_norm_series = test_d2["Document"].fillna("").str.strip().str.lower()
    in_train_dup_mask = test_norm_series.isin(train_norm_set).to_numpy(dtype=bool)

    # Evaluate baselines on identical TF-IDF representation fit on train_d2
    x_tr_vec = engine.vectorizer.transform(
        train_d2["Document"].fillna("").to_numpy(dtype=str)
    )
    x_te_vec = engine.vectorizer.transform(
        test_d2["Document"].fillna("").to_numpy(dtype=str)
    )

    maj_class = pd.Series(y_train).mode()[0]
    maj_preds = np.full_like(y_test, maj_class)

    nb_model = ComplementNB(alpha=0.5).fit(x_tr_vec, y_train)
    nb_preds = nb_model.predict(x_te_vec)

    lr_model = LogisticRegression(C=1.5, max_iter=300, random_state=42).fit(
        x_tr_vec, y_train
    )
    lr_preds = lr_model.predict(x_te_vec)

    # Primary engine triage on held-out test set
    triaged_test = engine.triage_dataframe(
        test_d2,
        text_col="Document",
        id_col="ticket_id",
        include_precedents=False,
    )
    # Align by ticket_id to prevent any ordering mismatch
    aligned = test_d2[["ticket_id", "Topic_group", "Document"]].merge(
        triaged_test, on="ticket_id", how="inner"
    )
    y_true = aligned["Topic_group"].to_numpy(dtype=str)
    y_pred = aligned["pred_category"].to_numpy(dtype=str)
    y_top2 = aligned["top2_category"].to_numpy(dtype=str)
    confs = aligned["confidence"].to_numpy(dtype=float)
    eff_tiers = aligned["effective_tier"].to_numpy(dtype=str)
    guard_trig = aligned["guardrail_triggered"].to_numpy(dtype=bool)

    aligned_norm = aligned["Document"].fillna("").str.strip().str.lower()
    aligned_dup_mask = aligned_norm.isin(train_norm_set).to_numpy(dtype=bool)
    strict_unseen_mask = ~aligned_dup_mask

    top2_acc = float(np.mean((y_true == y_pred) | (y_true == y_top2)))

    model_comparison = [
        {
            "Modelo / Estratégia": "Motor Principal: Calibrated LinearSVC (TF-IDF 1-2g, CV=3 por fold)",
            "Accuracy Global": round(float(accuracy_score(y_true, y_pred)), 4),
            "Macro-F1 Global": round(
                float(f1_score(y_true, y_pred, average="macro")), 4
            ),
            "Top-2 Accuracy": round(top2_acc, 4),
        },
        {
            "Modelo / Estratégia": "Baseline 3: Logistic Regression (TF-IDF 1-2g)",
            "Accuracy Global": round(float(accuracy_score(y_test, lr_preds)), 4),
            "Macro-F1 Global": round(
                float(f1_score(y_test, lr_preds, average="macro")), 4
            ),
            "Top-2 Accuracy": np.nan,
        },
        {
            "Modelo / Estratégia": "Baseline 2: Complement Naive Bayes",
            "Accuracy Global": round(float(accuracy_score(y_test, nb_preds)), 4),
            "Macro-F1 Global": round(
                float(f1_score(y_test, nb_preds, average="macro")), 4
            ),
            "Top-2 Accuracy": np.nan,
        },
        {
            "Modelo / Estratégia": f"Baseline 1: Classe Majoritária ({maj_class})",
            "Accuracy Global": round(float(accuracy_score(y_test, maj_preds)), 4),
            "Macro-F1 Global": round(
                float(f1_score(y_test, maj_preds, average="macro")), 4
            ),
            "Top-2 Accuracy": np.nan,
        },
    ]

    # Selective automation curve across thresholds (both raw confidence and post-guardrail/PAM Tier 1)
    selective_curve: List[Dict[str, Any]] = []
    for thr in [0.55, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90]:
        raw_mask = confs >= thr
        raw_cov = float(raw_mask.mean())
        raw_acc = (
            float(accuracy_score(y_true[raw_mask], y_pred[raw_mask]))
            if raw_mask.sum()
            else 0.0
        )
        raw_f1 = (
            float(f1_score(y_true[raw_mask], y_pred[raw_mask], average="macro"))
            if raw_mask.sum()
            else 0.0
        )
        op_t1_mask = (
            (confs >= thr)
            & (~guard_trig)
            & (y_pred != "Administrative rights")
        )
        op_cov = float(op_t1_mask.mean())
        op_acc = (
            float(accuracy_score(y_true[op_t1_mask], y_pred[op_t1_mask]))
            if op_t1_mask.sum()
            else 0.0
        )
        selective_curve.append(
            {
                "Limiar de Confiança (τ)": f">= {thr:.2f}",
                "Tickets Cobertos (n)": int(raw_mask.sum()),
                "Cobertura da Fila (%)": round(raw_cov * 100.0, 2),
                "Acurácia no Subconjunto (%)": round(raw_acc * 100.0, 2),
                "Macro-F1 no Subconjunto": round(raw_f1, 4),
                "Taxa de Erro Residual (%)": round((1.0 - raw_acc) * 100.0, 2),
                "Tier 1 Operacional (n)": int(op_t1_mask.sum()),
                "Cobertura Tier 1 Operacional (%)": round(op_cov * 100.0, 2),
                "Acurácia Tier 1 Operacional (%)": round(op_acc * 100.0, 2),
            }
        )

    # Operational 3-Tier distribution on held-out test set (with guardrails + PAM rule)
    t1_mask = np.char.startswith(eff_tiers.astype(str), "Tier 1")
    t2_mask = np.char.startswith(eff_tiers.astype(str), "Tier 2")
    t3_mask = np.char.startswith(eff_tiers.astype(str), "Tier 3")

    t1_cov = float(t1_mask.mean())
    t2_cov = float(t2_mask.mean())
    t3_cov = float(t3_mask.mean())
    t1_acc = (
        float(accuracy_score(y_true[t1_mask], y_pred[t1_mask]))
        if t1_mask.sum()
        else 0.0
    )
    t2_top2_acc = (
        float(
            np.mean(
                (y_true[t2_mask] == y_pred[t2_mask])
                | (y_true[t2_mask] == y_top2[t2_mask])
            )
        )
        if t2_mask.sum()
        else 0.0
    )

    # Deduplicated / strictly unseen text metrics on test_d2
    unseen_global_acc = (
        float(accuracy_score(y_true[strict_unseen_mask], y_pred[strict_unseen_mask]))
        if strict_unseen_mask.sum()
        else 0.0
    )
    unseen_t1_mask = t1_mask & strict_unseen_mask
    unseen_t1_acc = (
        float(accuracy_score(y_true[unseen_t1_mask], y_pred[unseen_t1_mask]))
        if unseen_t1_mask.sum()
        else 0.0
    )

    # Per-class report on Dataset 2 test set
    cls_rep = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    per_class_rows = []
    for cls_name in engine.classes_:
        m = cls_rep.get(str(cls_name), {})
        per_class_rows.append(
            {
                "Categoria (Dataset 2)": str(cls_name),
                "Suporte Teste (n)": int(m.get("support", 0)),
                "Precision (%)": round(float(m.get("precision", 0.0)) * 100.0, 2),
                "Recall (%)": round(float(m.get("recall", 0.0)) * 100.0, 2),
                "F1-Score": round(float(m.get("f1-score", 0.0)), 4),
            }
        )

    # Domain-Shift Stress Test on Dataset 1 (Raw and Interpolated)
    d1_raw_docs = pd.DataFrame(
        {
            "ticket_id": [f"D1-RAW-{i:04d}" for i in range(len(df_d1))],
            "Document": (
                df_d1["Ticket Subject"].fillna("")
                + " "
                + df_d1["Ticket Description"].fillna("")
            ),
        }
    )
    d1_raw_triaged = engine.triage_dataframe(
        d1_raw_docs, text_col="Document", id_col="ticket_id", include_precedents=False
    )
    naive_false_auto_rate = float(
        (d1_raw_triaged["confidence"] >= tier1_threshold).mean() * 100.0
    )
    naive_false_auto_count = int(
        (d1_raw_triaged["confidence"] >= tier1_threshold).sum()
    )
    guarded_raw_auto_count = int(
        d1_raw_triaged["effective_tier"].str.startswith("Tier 1").sum()
    )

    # What if `{product_purchased}` is interpolated with the real `Product Purchased` name?
    interp_texts = [
        f"{s} {d.replace('{product_purchased}', str(p))}"
        for s, d, p in zip(
            df_d1["Ticket Subject"].fillna(""),
            df_d1["Ticket Description"].fillna(""),
            df_d1["Product Purchased"].fillna("device"),
        )
    ]
    d1_interp_docs = pd.DataFrame(
        {
            "ticket_id": [f"D1-INT-{i:04d}" for i in range(len(df_d1))],
            "Document": interp_texts,
        }
    )
    d1_interp_triaged = engine.triage_dataframe(
        d1_interp_docs,
        text_col="Document",
        id_col="ticket_id",
        include_precedents=False,
    )
    guarded_interp_blocked_pct = float(
        (~d1_interp_triaged["effective_tier"].str.startswith("Tier 1")).mean() * 100.0
    )

    roi_scenarios = build_standard_roi_scenarios(
        tier1_coverage=t1_cov,
        tier1_accuracy=t1_acc,
        tier2_coverage=t2_cov,
    )

    return {
        "d1_audit": d1_audit,
        "d1_null_predictability": d1_null,
        "d2_train_size": int(len(train_d2)),
        "d2_test_size": int(len(test_d2)),
        "d2_duplicate_audit": {
            "exact_dup_in_test_count": int(in_train_dup_mask.sum()),
            "exact_dup_in_test_pct": round(float(in_train_dup_mask.mean() * 100.0), 2),
            "strict_unseen_test_count": int(strict_unseen_mask.sum()),
            "strict_unseen_global_accuracy_pct": round(unseen_global_acc * 100.0, 2),
            "strict_unseen_tier1_accuracy_pct": round(unseen_t1_acc * 100.0, 2),
        },
        "model_comparison": model_comparison,
        "selective_curve": selective_curve,
        "per_class_metrics": per_class_rows,
        "tier_summary": {
            "tier1_count": int(t1_mask.sum()),
            "tier1_coverage_pct": round(t1_cov * 100.0, 2),
            "tier1_accuracy_pct": round(t1_acc * 100.0, 2),
            "tier2_count": int(t2_mask.sum()),
            "tier2_coverage_pct": round(t2_cov * 100.0, 2),
            "tier2_top2_accuracy_pct": round(t2_top2_acc * 100.0, 2),
            "tier3_count": int(t3_mask.sum()),
            "tier3_coverage_pct": round(t3_cov * 100.0, 2),
        },
        "domain_shift_stress": {
            "d1_total": int(len(df_d1)),
            "naive_false_tier1_count": naive_false_auto_count,
            "naive_false_tier1_pct": round(naive_false_auto_rate, 2),
            "guarded_raw_tier1_count": guarded_raw_auto_count,
            "guarded_raw_containment_pct": round(
                (1.0 - guarded_raw_auto_count / len(df_d1)) * 100.0, 2
            ),
            "guarded_interpolated_containment_pct": round(
                guarded_interp_blocked_pct, 2
            ),
        },
        "roi_scenarios": roi_scenarios,
    }


def generate_markdown_benchmark_report(
    report_data: Dict[str, Any], output_path: Path | None = None
) -> str:
    """Formats the benchmark dictionary into a reproducible Markdown artifact."""
    d1 = report_data["d1_audit"]
    d1_null = report_data["d1_null_predictability"]
    dup = report_data["d2_duplicate_audit"]
    ts = report_data["tier_summary"]
    ds = report_data["domain_shift_stress"]

    lines = [
        "# Relatório Reprodutível de Auditoria Forense, Benchmark Out-of-Sample e Simulação de ROI",
        "",
        "**Desafio:** Challenge 002 — Redesign de Suporte (Operações / CX)<br>",
        "**Autor:** Arthur Lima<br>",
        "",
        "---",
        "",
        "## 1. Diagnóstico Forense do Dataset 1 (`customer_support_tickets.csv`, `N = 8.469`)",
        "",
        f"- **Backlog Aberto/Pendente:** `{d1['backlog_tickets']} / {d1['total_tickets']}` (**{d1['backlog_share_pct']:.2f}%** sem fechamento: `{d1['open_tickets']}` Open + `{d1['pending_customer_tickets']}` Pending Customer Response).",
        f"- **Distribuição Equitativa das 4 Prioridades (`High` + `Critical`):** `{d1['high_critical_tickets']} / {d1['total_tickets']}` (**{d1['high_critical_share_pct']:.2f}%** rotulados como `High` ou `Critical`, ~25% em cada uma das 4 faixas).",
        f"- **Placeholder Não Interpolado (`{{product_purchased}}`):** `{d1['literal_placeholder_count']} / {d1['total_tickets']}` (**{d1['literal_placeholder_pct']:.2f}%** dos chamados).",
        f"- **Inversão Temporal nos Fechados (`Time to Resolution < First Response Time`):** `{d1['negative_ttr_count']} / {d1['closed_tickets']}` (**{d1['negative_ttr_pct']:.2f}%** com duração negativa; média `{d1['mean_delta_hours']:.2f} h`, mediana `{d1['median_delta_hours']:.2f} h`).",
        f"- **CSAT e Intervalo de Resolução (Sem Diferença Significativa Detectada):** CSAT médio `{d1['csat_mean']:.3f}` (DP `{d1['csat_std']:.3f}`), correlação linear com tempo de resolução `r = {d1['csat_delta_corr_r']:.4f}` (`p = {d1['csat_delta_corr_p']:.4f}`).",
        f"- **Teste de Preditibilidade Linear Supervisionada no Dataset 1 (Split 80/20, `N_test = {d1_null['d1_test_size']}`):**",
        f"  - `Ticket Type` (5 classes, baseline uniforme = 20,0%): Accuracy = **{d1_null['type_accuracy']*100:.2f}%**, Macro-F1 = **{d1_null['type_macro_f1']:.4f}**.",
        f"  - `Ticket Priority` (4 classes, baseline uniforme = 25,0%): Accuracy = **{d1_null['priority_accuracy']*100:.2f}%**, Macro-F1 = **{d1_null['priority_macro_f1']:.4f}**.",
        "",
        "### Testes de Hipótese por Dimensão no Dataset 1",
        "",
        "| Dimensão | ANOVA F (CSAT) | ANOVA p (CSAT) | Kruskal p (CSAT) | Permutação p (CSAT) | ANOVA p (Δ Horas) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ]
    for dim, vals in d1["dimension_tests"].items():
        lines.append(
            f"| `{dim}` | {vals['csat_anova_f']:.4f} | {vals['csat_anova_p']:.4f} | {vals['csat_kruskal_p']:.4f} | {vals['csat_perm_p']:.4f} | {vals['delta_anova_p']:.4f} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            f"## 2. Benchmark Out-of-Sample no Dataset 2 (`N_train = {report_data['d2_train_size']}`, `N_test = {report_data['d2_test_size']}`)",
            "",
            f"- **Auditoria de Duplicatas no Corpus (`test_d2` vs. `train_d2`):** `{dup['exact_dup_in_test_count']} / {report_data['d2_test_size']}` (**{dup['exact_dup_in_test_pct']:.2f}%**) das linhas da partição de teste possuem texto normalizado idêntico na partição de treino; nos `{dup['strict_unseen_test_count']}` textos estritamente inéditos, a acurácia global é **{dup['strict_unseen_global_accuracy_pct']:.2f}%** e a acurácia no Tier 1 é **{dup['strict_unseen_tier1_accuracy_pct']:.2f}%**.",
            "",
            "| Modelo / Estratégia | Accuracy Global | Macro-F1 Global | Top-2 Accuracy |",
            "| :--- | :---: | :---: | :---: |",
        ]
    )
    for row in report_data["model_comparison"]:
        t2_str = (
            f"{row['Top-2 Accuracy']*100:.2f}%"
            if pd.notnull(row["Top-2 Accuracy"])
            else "N/A"
        )
        lines.append(
            f"| {row['Modelo / Estratégia']} | {row['Accuracy Global']*100:.2f}% | {row['Macro-F1 Global']:.4f} | {t2_str} |"
        )

    lines.extend(
        [
            "",
            "### Curva de Automação Seletiva (Confiança Bruta vs. Tier 1 Operacional Pós-Guardrail/PAM)",
            "",
            "| Limiar de Confiança (τ) | Tickets Cobertos Bruto (n) | Cobertura Bruta (%) | Acurácia Bruta (%) | Tier 1 Operacional (n) | Cobertura Tier 1 Operacional (%) | Acurácia Tier 1 Operacional (%) |",
            "| :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]
    )
    for row in report_data["selective_curve"]:
        lines.append(
            f"| `{row['Limiar de Confiança (τ)']}` | {row['Tickets Cobertos (n)']} | {row['Cobertura da Fila (%)']:.2f}% | **{row['Acurácia no Subconjunto (%)']:.2f}%** | {row['Tier 1 Operacional (n)']} | **{row['Cobertura Tier 1 Operacional (%)']:.2f}%** | **{row['Acurácia Tier 1 Operacional (%)']:.2f}%** |"
        )

    lines.extend(
        [
            "",
            "### Distribuição Operacional dos 3 Tiers na Partição de Teste (`N = 9.568`)",
            "",
            f"- **Tier 1 — Auto-Route (`conf >= 0.80`, sem bloqueio de guardrail/PAM):** `{ts['tier1_count']}` chamados classificados/encaminhados (**{ts['tier1_coverage_pct']:.2f}%** da fila) com **{ts['tier1_accuracy_pct']:.2f}%** de acurácia.",
            f"- **Tier 2 — Copilot Assist (`0.55 <= conf < 0.80` ou aprovação PAM):** `{ts['tier2_count']}` chamados (**{ts['tier2_coverage_pct']:.2f}%** da fila) com **{ts['tier2_top2_accuracy_pct']:.2f}%** de cobertura nas Top-2 sugestões.",
            f"- **Tier 3 — Escalação Humana (`conf < 0.55` ou Guardrail Acionado):** `{ts['tier3_count']}` chamados (**{ts['tier3_coverage_pct']:.2f}%** da fila).",
            "",
            "---",
            "",
            "## 3. Teste de Estresse de Domain Shift (Dataset 1 Consumidor no Motor de TI Dataset 2)",
            "",
            f"- **Sem Guardrail de Domínio (Apenas `conf >= 0.80`):** `{ds['naive_false_tier1_count']} / {ds['d1_total']}` (**{ds['naive_false_tier1_pct']:.2f}%**) dos tickets de consumidor seriam falsamente auto-roteados para filas internas de TI.",
            f"- **Com Guardrails Determinísticos (Dataset 1 Bruto):** `{ds['guarded_raw_tier1_count']} / {ds['d1_total']}` auto-roteados (**{ds['guarded_raw_containment_pct']:.2f}%** de contenção humana/consumidor).",
            f"- **Com Guardrails Determinísticos (Dataset 1 Interpolando `{{product_purchased}}` pelo Produto Real):** **{ds['guarded_interpolated_containment_pct']:.2f}%** de contenção fora do Tier 1.",
            "",
            "---",
            "",
            "## 4. Simulação Paramétrica de Capacidade, Retrabalho e TCO (Base 30.000 tickets/ano)",
            "",
            "> **Nota de Transparência:** Os cenários separam explicitamente o **tempo de triagem e encaminhamento manual** (Cenário 1: `4,0 min/ticket`, escopo executado pelo protótipo) de ganhos adicionais condicionais de assistência em resolução (Cenários 2 e 3), aplicando penalidade uniforme de retrabalho de `2,0x` sobre os erros residuais do Tier 1.",
            "",
            "| Cenário | Escopo Modelado | Cobertura Tier 1 (%) | Precisão Tier 1 (%) | Horas Base/Ano | Horas Brutas Poupadas | (-) Horas Retrabalho Erro | (=) Horas Líquidas/Ano | FTEs Liberados | Economia Líquida (R$/ano) | Payback (meses) |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]
    )
    for row in report_data["roi_scenarios"]:
        lines.append(
            f"| {row['Cenário']} | {row['Escopo Modelado']} | {row['Cobertura Tier 1 (%)']:.2f}% | {row['Precisão Tier 1 (%)']:.2f}% | {row['Horas Base/Ano']:.1f} | {row['Horas Brutas Poupadas']:.1f} | {row['(-) Horas Retrabalho Erro']:.1f} | **{row['(=) Horas Líquidas/Ano']:.1f}** | {row['FTEs Liberados']:.2f} | **R$ {row['(=) Economia Líquida (R$/ano)']:,.2f}** | {row['Payback Setup (meses)']:.1f} |"
        )

    md_text = "\n".join(lines) + "\n"
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(md_text, encoding="utf-8")
    return md_text


if __name__ == "__main__":
    import json

    artifacts_dir = Path(__file__).resolve().parent.parent / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    out_file = artifacts_dir / "benchmark_report.md"
    json_file = artifacts_dir / "benchmark_summary.json"
    rep = run_full_support_benchmark()
    generate_markdown_benchmark_report(rep, out_file)
    json_file.write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Benchmark report saved to {out_file} and {json_file}")

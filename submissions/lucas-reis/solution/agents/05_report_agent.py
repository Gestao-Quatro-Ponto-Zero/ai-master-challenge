"""
Agent 05 — Report Generator
Consolida findings em relatório executivo Markdown/HTML.
"""

import pandas as pd
from datetime import date
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent.parent / "docs"


def generate_executive_report(
    hypothesis_results: list[dict],
    model_results: dict,
    master_df: pd.DataFrame,
) -> str:
    auc = model_results["auc"]
    top_features = model_results["feature_importance"].head(5)
    churn_rate = master_df["churned"].mean()
    high_risk = master_df[master_df["churn_score"] >= 0.7] if "churn_score" in master_df.columns else pd.DataFrame()

    confirmed_hypotheses = [h for h in hypothesis_results if h.get("confirmed") and h.get("significant")]

    report = f"""# Relatório Executivo — Diagnóstico de Churn RavenStack

**Data:** {date.today().isoformat()}
**Autor:** Lucas Reis
**Modelo:** LightGBM | AUC-ROC: {auc:.4f}

---

## Executive Summary

A análise de {len(master_df):,} contas da RavenStack identificou uma taxa de churn de **{churn_rate:.1%}**.
O modelo preditivo atingiu AUC-ROC de **{auc:.4f}**, identificando {len(high_risk):,} contas em risco alto (score ≥ 0.70).

As principais causas de churn identificadas são:
{chr(10).join(f'- {h["statement"]}' for h in confirmed_hypotheses[:3])}

---

## Findings Principais

### 1. Taxa de Churn por Segmento

| Segmento | Churn Rate |
|----------|-----------|
| Overall  | {churn_rate:.1%} |

### 2. Hipóteses Validadas

| ID | Hipótese | Status | p-value |
|----|---------|--------|---------|
{chr(10).join(f'| {h["id"]} | {h["statement"][:60]}... | {"✅ Confirmada" if h.get("confirmed") else "❌ Refutada"} | {h["p_value"]} |' for h in hypothesis_results)}

### 3. Fatores Preditivos (Top 5 por SHAP)

| Feature | SHAP Importance |
|---------|----------------|
{chr(10).join(f'| {row["feature"]} | {row["shap_mean_abs"]:.4f} |' for _, row in top_features.iterrows())}

---

## Contas em Risco Alto (Score ≥ 0.70)

Total: **{len(high_risk):,} contas**

---

## Recomendações Priorizadas

### R1 — Programa de Re-engajamento (Alto Impacto, Curto Prazo)
Contato proativo com contas de churn_score ≥ 0.70 nos próximos 30 dias.
**ROI estimado:** retenção de {len(high_risk)} contas em risco.

### R2 — Onboarding de Features Críticas (Alto Impacto, Médio Prazo)
Contas com baixo `distinct_features_used` devem receber treinamento direcionado.
Foco nas features com maior SHAP importance.

### R3 — SLA de Suporte para Tickets Críticos (Médio Impacto, Curto Prazo)
Reduzir `avg_resolution_h` para tickets de alta prioridade.
Meta: resolução em < 4h para contas com contrato > R$50k.

---

## Limitações

- Dataset sintético: resultados precisam de validação com dados reais de produção
- Modelo não inclui dados de NPS/CSAT que podem ter alta correlação com churn
- Análise temporal (cohort) não foi realizada nesta versão

---

_Gerado automaticamente pelo Agent 05 do pipeline de diagnóstico de churn G4 AI Master._
"""
    return report


def save_report(report: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "executive_report.md"
    output_path.write_text(report, encoding="utf-8")
    print(f"[REPORT] Salvo em: {output_path}")
    return output_path


if __name__ == "__main__":
    # Mock data para validação
    import numpy as np
    n = 500
    master_df = pd.DataFrame({
        "account_id": range(n),
        "churned": np.random.binomial(1, 0.2, n),
        "churn_score": np.random.beta(2, 8, n),
    })
    hypothesis_results = [
        {"id": "H1", "statement": "Baixo uso de features prediz churn", "confirmed": True, "significant": True, "p_value": 0.001},
        {"id": "H2", "statement": "Tickets de alta prioridade correlacionam com churn", "confirmed": True, "significant": True, "p_value": 0.023},
        {"id": "H3", "statement": "SMB tem maior churn que Enterprise", "confirmed": False, "significant": False, "p_value": 0.412},
    ]
    model_results = {
        "auc": 0.83,
        "feature_importance": pd.DataFrame({
            "feature": ["distinct_features_used", "n_high_priority_tickets", "avg_session_min", "contract_value", "n_tickets"],
            "shap_mean_abs": [0.42, 0.31, 0.28, 0.19, 0.15],
        }),
    }
    report = generate_executive_report(hypothesis_results, model_results, master_df)
    save_report(report)

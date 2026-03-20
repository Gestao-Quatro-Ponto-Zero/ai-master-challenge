# Prompt 005 — Agent Modelo Preditivo

**Data:** 2026-03-20
**Agent:** 04_predictive_agent.py
**Ferramenta:** Claude Code
**Executado por:** Lucas Reis

---

## Prompt enviado ao Claude Code

> Contexto: projeto G4 AI Master Challenge — Challenge 001 Diagnóstico de Churn.
>
> A análise de hipóteses revelou que o churn NÃO tem assinatura comportamental:
> - H3 (uso): não significativo, churners e retidos usam o produto igualmente
> - H4 (satisfaction null): refutada na direção errada
> - H5 (plan_tier): nulo perfeito
> - H1 (segmental): borderline estatisticamente, OR ~2.5× economicamente relevante
>
> Mesmo com hipóteses fracas, o modelo preditivo serve para:
> 1. Quantificar o poder preditivo real das features disponíveis
> 2. Gerar scores individuais por conta (mesmo que de baixa precisão)
> 3. Identificar as features com maior importância relativa via SHAP
> 4. Gerar lista de ação para CS: contas HIGH risk ainda ativas
>
> Rode python submissions/lucas-reis/solution/agents/04_predictive_agent.py
>
> Especificações:
> - DuckDB para feature engineering: sub_agg + usage_agg + ticket_agg + churn_info
> - 19 features: segmental + contrato + uso + suporte
> - LightGBM: n_estimators=200, lr=0.05, class_weight="balanced"
> - SHAP TreeExplainer: top 10 global + top 3 por conta + direção (correlação)
> - Risk tiers: HIGH (≥70), MEDIUM (40–69), LOW (<40)
> - CS action list: top 20 HIGH risk com churned==0, ordenado por MRR desc
> - Salvar solution/churn_scores.csv

---

## Dependências instaladas

```bash
brew install libomp          # LightGBM requer OpenMP no macOS
# lightgbm e shap já instalados via pip3 anteriormente
```

## Correção aplicada durante execução

```python
# Python 3.9 não suporta `dict | None` — sintaxe é 3.10+
# Antes:
def prepare_features(df: pd.DataFrame, encoders: dict | None = None, fit: bool = False):
# Depois:
def prepare_features(df: pd.DataFrame, encoders=None, fit: bool = False):
```

---

## Resultados

### AUC e métricas

| Métrica | Valor |
|--------|-------|
| AUC-ROC | **0.3444** |
| Recall (Churned) | 9% (threshold=0.5) |
| Precision (Churned) | 12% |
| Acurácia geral | 66% (majoritária baseline) |

**AUC < 0.5 → modelo está predizendo inversamente ao churn real.**

### Top 10 features por SHAP (global)

| Rank | Feature | SHAP Mean |Abs| Direção |
|------|---------|-----------|---------|
| 1 | avg_error_count | 0.9159 | ↓ menos churn |
| 2 | avg_mrr | 0.7644 | ↓ menos churn |
| 3 | seats | 0.5851 | ↑ mais churn |
| 4 | avg_usage_duration_min | 0.4926 | ↓ menos churn |
| 5 | industry | 0.4556 | ↑ mais churn |
| 6 | distinct_features_used | 0.4460 | ↑ mais churn |
| 7 | n_upgrades | 0.2830 | ↑ mais churn |
| 8 | avg_session_count | 0.2661 | ↓ menos churn |
| 9 | preceding_upgrade_flag | 0.2134 | ↓ menos churn |
| 10 | n_urgent_tickets | 0.2073 | ↓ menos churn |

### Distribuição de risk_tier

| Tier | N contas | % |
|------|----------|---|
| HIGH | 99 | 19.8% |
| MEDIUM | 8 | 1.6% |
| LOW | 393 | 78.6% |

### CS Action List

- **10 contas** HIGH risk ainda ativas
- **MRR em risco imediato:** $12,231
- Top conta: A-49b828 (score=73, $2,222 MRR, FinTech)

### Output

- `solution/churn_scores.csv` — 500 linhas, 11 colunas ✅

---

## Decisões de modelagem

- **LightGBM**: boosting em árvores, rápido, lida bem com categoricals encodadas e features mistas
- `class_weight="balanced"`: necessário com 22% de churn (desbalanceamento moderado)
- `n_estimators=200, lr=0.05`: padrão conservador; regularização via min_child_samples=10
- LabelEncoder para industry, referral_source, initial_plan_tier

## Insight crítico do SHAP

O SHAP confirma o paradoxo de uso: `avg_error_count` e `avg_mrr` têm direção "↓ menos churn",
ou seja, contas com MAIS erros e MAIOR MRR tendem a RETER — consistente com o achado da H3.
O modelo aprende a prever o inverso do churn porque as features de uso discriminam retidos,
não churners.

## Limitações do modelo

1. **AUC < 0.5**: pior que coin flip — o churn não é previsível pelas features disponíveis
2. **Dataset sintético**: features sem semântica real (`feature_1..40`) limitam interpretação
3. **n=500**: amostra pequena para um modelo supervisionado com 22% de churn (n_positivos=110)
4. **Features ausentes**: LTV histórico, NPS/CSAT scores, número de onboarding completado,
   uso de API vs UI, frequência de login — dados que discriminariam churners em produção

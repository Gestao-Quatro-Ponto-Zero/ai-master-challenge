# Modelo Preditivo de Churn — RavenStack

## Objetivo

Construir um modelo de Machine Learning para prever probabilidade de churn de accounts ativos, complementando a análise exploratória.

---

## Metodologia

### Feature Engineering

Foram criadas 15 features a partir do cruzamento das 5 tabelas:

**Features binárias (baseadas no diagnóstico):**
- `is_devtools` — Indústria = DevTools
- `is_event_ads` — Canal = Event ou Ads
- `low_core_adoption` — Core features < 20%
- `has_escalation` — Tem escalação no suporte
- `low_csat` — CSAT médio < 4.0

**Features de interação:**
- `devtools_event_ads` — DevTools × Event/Ads
- `devtools_low_core` — DevTools × Baixa adoção

**Features numéricas:**
- `seats`, `mrr_amount`, `ticket_count`
- `avg_resolution_hours`, `avg_csat`
- `total_usage`, `core_pct`, `escalation_count`

### Modelos Testados

| Modelo | CV AUC (5-fold) |
|--------|-----------------|
| Logistic Regression | **55.7%** ± 7.9% |
| Random Forest | 52.5% ± 5.5% |
| Gradient Boosting | 52.2% ± 3.2% |

**Melhor modelo:** Logistic Regression (class_weight='balanced')

---

## Resultados

### Performance no Teste (n=150)

| Métrica | Valor |
|---------|-------|
| Accuracy | 59.3% |
| Precision | 30.6% |
| **Recall** | **66.7%** |
| F1 Score | 41.9% |
| ROC AUC | 64.5% |

**Confusion Matrix:**
```
            Previsto
            Não    Sim
Real  Não   67     50
      Sim   11     22
```

### Interpretação

- **Recall de 66.7%** — O modelo captura 2/3 dos churns reais
- **Precision de 30.6%** — Muitos falsos positivos (50 de 72 previsões)
- **Trade-off:** Priorizar recall (não perder churns) gera mais alertas falsos

---

## Previsões para Accounts Ativos

### Distribuição de Probabilidade

| Threshold | Accounts | MRR |
|-----------|----------|-----|
| ≥40% | 315 | $681,295 |
| ≥35% | 354 | $797,452 |
| ≥30% | 378 | $896,331 |

### Top 10 Maior Risco

| Account | Indústria | Canal | MRR | Prob |
|---------|-----------|-------|-----|------|
| A-cc98bc | DevTools | ads | $0 | 74.4% |
| A-22f2df | DevTools | ads | $209 | 72.5% |
| A-dfbd31 | DevTools | partner | $266 | 69.1% |
| A-ffc04f | EdTech | ads | $247 | 68.9% |
| A-3c1a3f | DevTools | event | $133 | 68.6% |
| A-54ecc2 | Cybersecurity | partner | $5,572 | 68.2% |
| A-ad64c6 | DevTools | event | $5,572 | 68.0% |
| A-726cfa | DevTools | partner | $7,562 | 67.7% |
| A-22d9d2 | DevTools | event | $1,568 | 67.7% |
| A-d4ac0e | DevTools | ads | $882 | 67.7% |

---

## Feature Importance

| Feature | Importância |
|---------|-------------|
| core_pct | 19.8% |
| avg_resolution_hours | 15.0% |
| seats | 14.0% |
| total_usage | 13.4% |
| mrr_amount | 11.4% |
| ticket_count | 7.3% |
| avg_csat | 7.0% |
| low_core_adoption | 3.4% |
| is_devtools | 2.0% |
| is_event_ads | 1.8% |

**Insight:** As features contínuas (core_pct, resolution_hours) têm mais peso que as binárias derivadas do diagnóstico.

---

## Limitações

### 1. Performance Limitada

O modelo tem ROC AUC de ~55-65%, pouco melhor que random (50%). Isso indica que:

- **Dados sintéticos** não têm padrões fortes que ML consegue capturar
- **Poucos dados** (500 accounts, 110 churns) limitam generalização
- **Features redundantes** — algumas derivam das mesmas variáveis

### 2. Comparação com Risk Score Manual

O risk score manual (do diagnóstico) identificou 81 contas de alto risco baseado em regras claras. O modelo ML:

- **Não converge** com o manual — correlação de apenas -0.05
- **Dispersa mais** — classifica ~315 contas como ≥40% risco
- **Menos interpretável** — difícil explicar por que uma conta tem 74% vs 68%

### 3. Recomendação

Para este caso específico, **o risk score manual é mais útil** porque:

1. **Interpretável** — Sabemos exatamente por que uma conta é de alto risco
2. **Acionável** — Cada fator tem uma ação correspondente
3. **Validado** — Baseado em padrões comprovados nos dados históricos

O modelo ML seria mais útil com:
- Mais dados (>2000 accounts)
- Features temporais (tendência de uso, velocidade de queda)
- Dados não-sintéticos com padrões reais

---

## Código

```python
# Ver arquivo completo em solution/modelo_churn_ml.py
```

---

## Conclusão

O modelo preditivo foi construído e gera probabilidades de churn, mas tem **performance limitada** neste dataset. Para uso prático, recomenda-se:

1. **Priorizar o risk score manual** para intervenções imediatas
2. **Usar o modelo ML como segundo filtro** para accounts não capturados pelo manual
3. **Retreinar com mais dados** quando disponíveis

---

*Documento gerado como complemento ao Diagnóstico de Churn.*

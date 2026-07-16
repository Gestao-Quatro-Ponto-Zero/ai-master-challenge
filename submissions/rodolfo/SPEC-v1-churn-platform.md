# SPEC-V1: Plataforma de Diagnóstico, Predição e Prescrição de Churn

> **Spec-Driven Development** · Versão 1.0
> Este documento é a *fonte da verdade* para implementação. Nada deve ser
> construído sem antes ter sua spec aprovada. Cada spec tem um harness de
> validação associado.

---

## Índice de Especificações

| # | Spec | Status | Harness |
|---|------|--------|---------|
| 0 | [Metaspec: Linguagem e Convenções](#spec-0-metaspec) | ✅ Template | `harness/metaspec.test.sh` |
| 1 | [Arquitetura do Sistema](#spec-1-arquitetura) | Approved | `harness/arch.test.sh` |
| 2 | [Pipeline de Dados](#spec-2-pipeline-de-dados) | Implemented | `harness/pipeline.test.sh` |
| 3 | [Modelo de Dados Unificado](#spec-3-modelo-de-dados-unificado) | Implemented | `harness/datamodel.test.sh` |
| 4 | [Segmentação e Análise](#spec-4-segmentação) | Implemented | `harness/segmentation.test.sh` |
| 5 | [Health Score e Scoring](#spec-5-health-score) | Implemented | `harness/scoring.test.sh` |
| 6 | [Modelagem Preditiva](#spec-6-modelagem-preditiva) | Implemented | `harness/predictive.test.sh` |
| 7 | [Survival Analysis](#spec-7-survival-analysis) | Implemented | `harness/survival.test.sh` |
| 8 | [Causal Inference & Uplift](#spec-8-causal-uplift) | Draft | `harness/uplift.test.sh` |
| 9 | [Intervention Playbook](#spec-9-playbook) | Draft | `harness/playbook.test.sh` |
| 10 | [Dashboard, API e Visualização](#spec-10-dashboard-api-e-visualização) | Implemented | `harness/dashboard.test.sh` |
| 11 | [Infraestrutura & Deploy (Railway)](#spec-11-infraestrutura--deploy-railway) | Draft | `harness/deploy.test.sh` |
| 12 | [LLM Integration (OpenCode on-demand)](#spec-12-llm-integration-opencode-on-demand) | Draft | `harness/llm.test.sh` |
| A | [Glossário](#apêndice-a-glossário) | ✅ | — |

---

## SPEC-0: Metaspec — Linguagem e Convenções

### 0.1 Estrutura de uma Spec

Toda spec DEVE seguir este formato:

```yaml
spec:
  id: "SPEC-N"
  title: "Nome da Spec"
  status: "Draft" | "Approved" | "Implemented" | "Deprecated"
  owner: "Responsável"
  depends_on: ["SPEC-X", "SPEC-Y"]

context:
  # Por que esta spec existe? Qual problema resolve?

requirements:
  - id: "REQ-N-001"
    description: "..."
    priority: "P0" | "P1" | "P2"
    verification: "automated" | "manual" | "peer-review"

interfaces:
  # Inputs, outputs, contratos com outras specs

acceptance_criteria:
  # Condições explícitas para considerar implementado
```

### 0.2 Prioridades

| Prioridade | Significado | Prazo |
|------------|-------------|-------|
| **P0** | Essencial para o sistema funcionar | Bloqueante |
| **P1** | Importante, mas não bloqueante | Esta sprint |
| **P2** | Melhoria contínua | Backlog |

### 0.3 Convenções de Nomenclatura

- `Contexto/Agregado/Ação` — ex: `Account/ChurnRisk/Calculate`
- Arquivos de spec: `SPEC-N-nome-da-spec.md`
- Harness: `harness/spec-N.test.sh`
- Dados de teste: `test/fixtures/`

### 0.4 Ciclo de Vida

```
Draft → Review → Approved → Implementation → Verified → Done
  ↑                                                |
  └─────────────────── Failed ─────────────────────┘
```

---

## SPEC-1: Arquitetura do Sistema

```yaml
spec:
  id: "SPEC-1"
  title: "Arquitetura do Sistema"
  status: "Draft"
  owner: "Architect"
  depends_on: ["SPEC-0"]
```

### 1.1 Contexto

Sistema evolutivo de 3 estágios para diagnóstico e prescrição de churn em
SaaS B2B. Começa descritivo, evolui para preditivo e prescritivo.

### 1.2 Visão Geral

```
┌─────────────────────────────────────────────────────────────────┐
│                         INPUT LAYER                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Accounts  │  │  Subs    │  │  Usage   │  │ Support  │        │
│  │  .csv     │  │  .csv    │  │  .csv    │  │  .csv    │  ...   │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘        │
└────────┼──────────────┼──────────────┼──────────────┼────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PIPELINE LAYER (SPEC-2)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  Load    │→ │  Clean   │→ │  Merge   │→ │ Feature  │        │
│  │          │  │          │  │          │  │   Eng    │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│                                                    │             │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │              UNIFIED DATA MODEL (SPEC-3)                     ││
│  │  account_view: tabela única com todas as features            ││
│  └──────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ANALYSIS LAYER                              │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐    │
│  │ Descriptive  │  │  Predictive  │  │    Prescriptive      │    │
│  │  (SPEC-4,5)  │  │  (SPEC-6,7)  │  │    (SPEC-8,9)        │    │
│  │             │  │             │  │                      │    │
│  │ • Segments  │  │ • XGBoost   │  │ • Uplift modeling    │    │
│  │ • Health Sc │  │ • Survival  │  │ • Playbook engine    │    │
│  │ • Churn Biz │  │ • SHAP      │  │ • ROI estimation     │    │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬───────────┘    │
└─────────┼─────────────────┼─────────────────────┼───────────────┘
          │                 │                     │
          ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OUTPUT LAYER (SPEC-10)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │  Report HTML  │  │  Dashboard   │  │  Playbooks JSON    │    │
│  │  (static)     │  │ (interactive)│  │  (actionable)      │    │
│  └──────────────┘  └──────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Princípios Arquiteturais

1. **Pipeline em 3 estágios**: Descritivo → Preditivo → Prescritivo.
   Cada estágio consome do anterior e produz para o próximo.
2. **Imutabilidade de dados transformados**: Cada etapa gera um artefato
   versionado (parquet, JSON). Nunca alterar artefato de etapa anterior.
3. **Config-driven**: Dataset source, features, parâmetros de modelo vêm
   de arquivos YAML de configuração, não de código hardcoded.
4. **Testabilidade**: Cada etapa tem harness de validação que verifica
   contrato de entrada/saída.

### REQ-1-001: Pipeline Executável

```yaml
id: "REQ-1-001"
description: >
  O sistema DEVE ser executável com um único comando:
  `python run.py --config config/ravenstack.yaml --output ./output`
priority: "P0"
verification: "automated"
acceptance: "run.py --help lista todos os parâmetros. run.py com config mínima produz saída em <30min."
```

### REQ-1-002: Modularidade por Spec

```yaml
id: "REQ-1-002"
description: >
  Cada spec DEVE ser implementada como um módulo independente em
  `src/<spec-name>/`. Módulos PODEM ser executados isoladamente.
priority: "P1"
verification: "automated"
acceptance: "python -m src.health_score --input accounts.parquet funciona independente."
```

---

## SPEC-2: Pipeline de Dados

```yaml
spec:
  id: "SPEC-2"
  title: "Pipeline de Dados"
  status: "Draft"
  owner: "Data Engineer"
  depends_on: ["SPEC-1"]
```

### 2.1 Contexto

O pipeline carrega, valida, limpa e integra múltiplos datasets em um modelo
unificado. A saída é uma tabela `account_view` pronta para análise.

### 2.2 Requirements

#### REQ-2-001: Load Genérico

```yaml
description: >
  O pipeline DEVE aceitar dados em formato CSV, JSON, Parquet. A config
  DEVE especificar source, delimiter, encoding para cada arquivo.
priority: "P0"
verification: "automated"
acceptance: "Pipeline carrega CSV com encoding latin1 e delimiter ';' corretamente."
```

#### REQ-2-002: Schema Validation

```yaml
description: >
  Cada dataset DEVE ter um schema esperado definido na config. Na carga,
  o pipeline DEVE validar: colunas obrigatórias existem, dtypes conferem,
  null rate por coluna < threshold configurável.
priority: "P0"
verification: "automated"
acceptance: "Pipeline falha com erro claro se coluna 'account_id' está faltando."
```

#### REQ-2-003: Data Quality Report

```yaml
description: >
  O pipeline DEVE gerar um Data Quality Report (DQR) ao final da carga:
  null counts, unique counts, value ranges, outlier detection.
priority: "P1"
verification: "automated"
acceptance: "DQR é um JSON em output/dqr/ com métricas por tabela e coluna."
```

#### REQ-2-004: Merge Configurável

```yaml
description: >
  As regras de merge entre tabelas DEVM ser definidas na config YAML:
  chaves, tipo de join (left/inner), estratégia para duplicatas.
priority: "P0"
verification: "automated"
acceptance: >
  Com 1 account com 3 subscriptions, configuração 'strategy: latest'
  produz 1 linha com a subscription mais recente.
```

#### REQ-2-005: Audit Trail

```yaml
description: >
  O pipeline DEVE logar cada transformação: timestamp, input row count,
  output row count, operação, erros.
priority: "P1"
verification: "manual"
acceptance: "Log é JSON estruturado em output/logs/ com entrada por etapa."
```

### 2.3 Config Template

```yaml
# config/ravenstack.yaml
pipeline:
  name: "ravenstack-churn-diagnostic"
  version: "1.0"

sources:
  accounts:
    path: "data/accounts.csv"
    schema:
      account_id: string
      churn_flag: boolean
      industry: string
      plan_tier: string
      # ...
    validation:
      required_columns: ["account_id"]
      max_null_rate: 0.05

merges:
  main_view:
    type: "left"
    from: "accounts"
    with: "subscriptions"
    on: "account_id"
    strategy: "latest_subscription"  # latest | active_at_churn | all

output:
  format: "parquet"
  path: "output/account_view.parquet"
```

### 2.4 Harness de Validação

```bash
# harness/spec-2.test.sh
# Testa pipeline de dados

test_load_csv() {
    python run.py --config test/fixtures/config_minima.yaml --output /tmp/test_output
    assert_equal $? 0 "Pipeline deve executar sem erro"
    assert_file_exists "/tmp/test_output/account_view.parquet"
}

test_schema_validation() {
    # Config com schema errado deve falhar
    python run.py --config test/fixtures/config_schema_errado.yaml --output /tmp/test_schema 2>&1 | \
        grep -q "column 'account_id' is missing"
    assert_equal $? 0 "Deve rejeitar schema inválido"
}
```

---

## SPEC-3: Modelo de Dados Unificado

```yaml
spec:
  id: "SPEC-3"
  title: "Modelo de Dados Unificado"
  status: "Draft"
  owner: "Data Engineer"
  depends_on: ["SPEC-2"]
```

### 3.1 Entidades e Relacionamentos

```
┌───────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   accounts    │     │  subscriptions    │     │  feature_usage   │
│───────────────│     │──────────────────│     │──────────────────│
│ account_id PK │────→│ account_id FK     │────→│ subscription_id  │
│ industry      │     │ subscription_id PK│     │ feature_name     │
│ country       │     │ mrr_amount        │     │ usage_count      │
│ plan_tier     │     │ churn_flag        │     │ error_count      │
│ churn_flag    │     │ billing_frequency │     │ usage_duration   │
│ seats         │     │ start_date        │     │ usage_date       │
│ signup_date   │     │ end_date          │     │ is_beta_feature  │
│ is_trial      │     │ auto_renew_flag   │     └──────────────────┘
│ referral_source│    │ upgrade_flag      │
└───────┬───────┘     │ downgrade_flag    │
        │             └──────────────────┘
        │                      │
        │             ┌──────────────────┐     ┌──────────────────┐
        │             │  support_tickets  │     │  churn_events    │
        │             │──────────────────│     │──────────────────│
        │────→        │ account_id FK     │     │ account_id FK    │
                     │ ticket_id PK      │     │ churn_event_id PK│
                     │ priority          │     │ reason_code      │
                     │ satisfaction_score│     │ churn_date       │
                     │ resolution_time   │     │ refund_amount    │
                     │ escalation_flag   │     │ feedback_text    │
                     │ first_response_time│    │ preceding_upgrade│
                     └──────────────────┘     │ preceding_downgrade│
                                              │ is_reactivation   │
                                              └──────────────────┘
```

### 3.2 Account View (Tabela Unificada)

```yaml
account_view:
  description: >
    Tabela única por account_id com features de todas as entidades.
    É o input para todas as análises (SPEC-4 até SPEC-9).
  grain: "1 linha = 1 account"
  partition: "account_id"

  columns:
    # De accounts
    - name: account_id
      type: string
      description: "Chave primária"

    - name: industry
      type: categorical
      values: ["EdTech", "FinTech", "DevTools", "HealthTech", "Cybersecurity"]

    - name: country
      type: categorical

    - name: churn_flag
      type: boolean
      description: "True se a conta já churnou"

    - name: plan_tier
      type: categorical
      values: ["Basic", "Pro", "Enterprise"]

    - name: seats
      type: integer

    # Feature engineering (derivadas)
    - name: tenure_days
      type: integer
      description: "Dias desde signup até churn (ou até hoje se não churnou)"
      derivation: "(churn_date OR today) - signup_date"

    - name: usage_avg_30d
      type: float
      description: "Média de uso nos últimos 30 dias"

    - name: usage_trend_90d
      type: float
      description: "Inclinação da reta de uso nos últimos 90 dias (positivo = crescendo)"
      derivation: "LinearRegression(usage ~ day).slope"

    - name: support_ticket_count_90d
      type: integer

    - name: support_escalation_rate
      type: float
      description: "Proporção de tickets escalados"

    - name: support_avg_satisfaction
      type: float

    - name: support_avg_resolution_hours
      type: float

    - name: mrr_amount
      type: integer

    - name: billing_frequency
      type: categorical
      values: ["monthly", "annual", "quarterly"]

    - name: payment_risk_flag
      type: boolean
      description: "True se já teve falha de pagamento (se dado disponível)"

    - name: churn_reason_primary
      type: categorical
      description: "Motivo principal (se churnou)"

    - name: churn_type
      type: categorical
      values: ["voluntary", "involuntary", "unknown", "not_churned"]
      description: "Churn voluntário (decisão) vs involuntário (pagamento)"
```

### 3.3 Data Quality Gates

```yaml
REQ-3-001: "account_view DEVE ter exatamente 1 linha por account_id"
REQ-3-002: "Churn_flag DEVE ser booleano, sem nulos"
REQ-3-003: "MRR_amount DEVE ser >= 0"
REQ-3-004: "support_avg_satisfaction DEVE estar entre 1 e 5"
REQ-3-005: "Tenure_days DEVE ser >= 0"
REQ-3-006: "Usage_avg_30d DEVE ser >= 0"  
REQ-3-007: "Churn_rate geral DEVE estar entre 0 e 1"
REQ-3-008: "Toda conta com churn_flag=True DEVE ter churn_reason_primary preenchido"
```

---

## SPEC-4: Segmentação e Análise Descritiva

```yaml
spec:
  id: "SPEC-4"
  title: "Segmentação e Análise Descritiva"
  status: "Draft"
  owner: "Data Analyst"
  depends_on: ["SPEC-3"]
```

### 4.1 Contexto

Análise descritiva de churn por segmentos, identificação de padrões e
geração de hipóteses. É o "O quê?" e "Onde?" do churn.

### 4.2 Segmentos Obrigatórios

```yaml
segments:
  - name: "by_industry"
    description: "Indústria do cliente"
    churn_rate_min_variance: 0.05
    # Se a diferença entre maior e menor for <5%, não é segmento relevante

  - name: "by_plan_tier"
    description: "Plano contratado"

  - name: "by_country"
    description: "País"
    min_sample: 10

  - name: "by_acquisition_channel"
    description: "Canal de aquisição"

  - name: "by_tenure_cohort"
    description: "Cohort por mês de signup"
    min_sample: 5

  - name: "by_mrr_band"
    description: "Faixa de MRR (Q1/Q2/Q3/Q4)"

  - name: "by_seats_band"
    description: "Faixa de usuários (Q1/Q2/Q3/Q4)"

  - name: "by_billing_frequency"
    description: "Mensal vs Anual vs Trimestral"

  - name: "by_churn_reason"
    description: "Motivo declarado de churn"
```

### 4.3 Análises Obrigatórias

```yaml
REQ-4-001: "churn_rate_by_segment — taxa de churn absoluta por segmento"
  output: "tabela segmento | churn_rate | count | %_of_total_churn"
  verification: "automated"

REQ-4-002: "churn_impact_by_segment — MRR perdido por segmento"
  output: "tabela segmento | total_mrr_lost | avg_mrr_lost | %_of_total_mrr_lost"
  verification: "automated"

REQ-4-003: "retention_curve_by_cohort — curva de retenção por cohort mensal"
  output: "Gráfico cohort_month | month_1..N com proporção retida"
  min_months: 6
  verification: "automated"

REQ-4-004: "churn_reason_distribution — distribuição de motivos"
  output: "gráfico + tabela com n e %"
  verification: "automated"

REQ-4-005: "voluntary_vs_involuntary_split — separação por tipo"
  output: "churn_type | count | % | total_mrr_lost"
  verification: "automated"
  # P0: taxonomy baseada em reason_code
  # P2: validação com feedback_text NLP

REQ-4-006: "simpson_paradox_detection — detecção de paradoxo de Simpson"
  description: >
    Identificar casos onde a média agregada esconde tendências opostas
    em subgrupos. Ex: "churn geral caiu, mas subiu em 3 dos 5 segmentos".
  output: "Lista de métricas com paradoxo identificado"
  verification: "automated"
```

### 4.4 Harness

```bash
# Cada segmento tem teste de contrato:
test_segment_by_industry() {
    local result=$(python -m src.analysis.segmentation --segment industry --output /tmp/segments.json)
    assert_equal $(echo "$result" | jq '.data | length') 5 "5 indústrias esperadas"
    local churn_sum=$(echo "$result" | jq '[.data[].churned] | add')
    assert_equal $churn_sum 110 "Soma de churn deve ser 110"
}
```

---

## SPEC-5: Health Score

```yaml
spec:
  id: "SPEC-5"
  title: "Health Score e Scoring de Risco"
  status: "Draft"
  owner: "Data Scientist"
  depends_on: ["SPEC-3", "SPEC-4"]
```

### 5.1 Modelo de Score

```yaml
REQ-5-001: "health_score DEVE ser calculado como média ponderada de 4 pilares:"
  pillars:
    - name: "Usage"
      weight: 0.35  # 35%
      signals:
        - "usage_trend_90d"  # tendência de uso
        - "usage_avg_30d"    # nível absoluto
        - "feature_adoption_rate"  # % de features usadas
        - "error_rate_trend"  # erros crescendo?

    - name: "Support"
      weight: 0.25  # 25%
      signals:
        - "ticket_volume_trend"
        - "escalation_rate"
        - "avg_satisfaction"
        - "first_response_time"

    - name: "Engagement"
      weight: 0.20  # 20%
      signals:
        - "login_frequency"
        - "days_since_last_login"
        - "beta_feature_adoption"

    - name: "Financial"
      weight: 0.20  # 20%
      signals:
        - "payment_delinquency"
        - "downgrade_flag"
        - "billing_frequency"  # monthly = mais risco
        - "mrr_trend"

REQ-5-002: "Score DEVE ser normalizado entre 0 (pior) e 100 (melhor)"
  tiers:
    - range: [0, 40]
      label: "Critical"
    - range: [41, 60]
      label: "At Risk"
    - range: [61, 75]
      label: "Neutral"
    - range: [76, 90]
      label: "Healthy"
    - range: [91, 100]
      label: "Champion"

REQ-5-003: "Score DEVE ser recalibrado trimestralmente contra churn real"
  recalibration:
    method: "Logistic regression weights optimization"
    metric: "AUC-ROC"
    target: "AUC > 0.80"
    schedule: "quarterly"

REQ-5-004: "Delta score (variação em 30 dias) DEVE ser calculado"
  alert_threshold: -15
  # Se score caiu 15+ pontos em 30 dias → alerta automático
```

### 5.2 Validação

```yaml
REQ-5-005: "Distribuição do score DEVE ser aproximadamente normal"
  test: "Se >50% das contas estão em 'Critical', pesos estão errados"
  acceptance: "Máximo 10% em Critical, máximo 15% em Champion"

REQ-5-006: "Accounts churned DEVM ter score médio menor que não-churned"
  test: "t-test: média score_churned < média_score_retained, p < 0.01"

REQ-5-007: "Precisão do tier: >60% dos accounts em 'Critical' DEVM churnar em 90d"
  test: "Backtest com dados históricos"
```

---

## SPEC-6: Modelagem Preditiva

```yaml
spec:
  id: "SPEC-6"
  title: "Modelagem Preditiva — Quem vai churnar"
  status: "Draft"
  owner: "Data Scientist"
  depends_on: ["SPEC-3", "SPEC-5"]
```

### 6.1 Modelo Base

```yaml
REQ-6-001: "Modelo base DEVE ser ensemble de Gradient Boosted Trees"
  algorithm: "XGBoost or LightGBM"
  target: "churn_flag"
  train_window: "dados até mês M-1"
  test_window: "churns no mês M"
  features: "todas as colunas de account_view (excluindo pós-churn)"

REQ-6-002: "Treino DEVE usar dados balanceados"
  method: "SMOTE ou class_weight='balanced'"
  evaluation:
    primary: "AUC-ROC"
    secondary: "Precision@P90 (precisão no decil mais arriscado)"
    target_auc: 0.85
    min_precision_p90: 0.60

REQ-6-003: "Validação temporal (não aleatória)"
  method: >
    Treinar com meses 1-6, testar com mês 7.
    Depois treinar 1-7, testar 8. Walk-forward.
  min_windows: 4
```

### 6.2 Explainability

```yaml
REQ-6-004: "Toda predição DEVE vir acompanhada de explicação SHAP"
  output: |
    Para cada account:
    - score de churn (0-1)
    - top 3 features que MAIS contribuíram para o risco
    - top 3 features que MAIS contribuíram contra o risco
    - valor atual vs mediana do mercado para cada feature

REQ-6-005: "Global feature importance DEVE ser reportada"
  output: "Gráfico SHAP summary + tabela ranked por impacto médio"
```

### 6.3 Voluntary vs Involuntary

```yaml
REQ-6-006: "Modelo DEVE ser treinado separadamente para voluntary e involuntary"
  rationale: >
    Os preditores são diferentes: involuntary depende de billing,
    voluntary depende de uso/suporte/produto.
  models:
    - model_voluntary: { target: "churn_type == 'voluntary'", features: all }
    - model_involuntary: { target: "churn_type == 'involuntary'", features: billing_only }
```

### 6.4 Harness

```bash
# harness/spec-6.test.sh
test_model_trains() {
    python -m src.predictive.train --config config/ravenstack.yaml
    assert_file_exists "output/models/model_voluntary.pkl"
    assert_file_exists "output/models/model_involuntary.pkl"
}

test_auc_threshold() {
    local auc=$(python -m src.predictive.evaluate --model output/models/model_voluntary.pkl | jq '.auc')
    assert_greater_than $auc 0.80 "AUC deve ser > 0.80"
}

test_shap_output() {
    python -m src.predictive.explain --model output/models/model_voluntary.pkl --output /tmp/shap
    assert_file_exists "/tmp/shap/top_accounts_risk.json"
    assert_equal $(cat /tmp/shap/top_accounts_risk.json | jq '.accounts[0] | has("top_features")') true
}
```

---

## SPEC-7: Survival Analysis

```yaml
spec:
  id: "SPEC-7"
  title: "Survival Analysis — Quando vai churnar"
  status: "Draft"
  owner: "Data Scientist"
  depends_on: ["SPEC-3"]
```

### 7.1 Modelos

```yaml
REQ-7-001: "Kaplan-Meier estimator por segmento obrigatório"
  segments:
    - "industry"
    - "plan_tier"
    - "billing_frequency"
    - "country"
  output: "Curva de sobrevivência S(t) para cada segmento com IC 95%"

REQ-7-002: "Cox Proportional Hazards model"
  features: "todas as colunas numéricas de account_view"
  output: |
    - hazard ratios para cada feature (com IC 95%)
    - p-values (teste de Wald)
    - teste de proporcionalidade (Schoenfeld residuals)
  acceptance: "Todas as features com p < 0.05 são reportadas como significativas"

REQ-7-003: "Predição de tempo até churn por conta"
  output: |
    - expected_time_to_churn (dias)
    - survival_probability_at_90d
    - survival_probability_at_180d
    - survival_probability_at_365d
  format: "adicionado ao account_view como colunas survival_*"
```

### 7.2 Validação

```yaml
REQ-7-004: "Calibração: concordance_index (C-index) > 0.70"
  method: "Harrell's C-index"
  target: 0.70
```

---

## SPEC-8: Causal Inference e Uplift Modeling

```yaml
spec:
  id: "SPEC-8"
  title: "Uplift Modeling — Quem pode ser salvo"
  status: "Draft"
  owner: "Data Scientist"
  depends_on: ["SPEC-3", "SPEC-6"]
```

### 8.1 Uplift Model

```yaml
REQ-8-001: "Modelo DEVE classificar contas em 4 categorias de persuasão:"
  categories:
    - "Persuadable"  # Intervenção reduz churn significativamente
    - "Sure Thing"    # Não vai churnar, independente de intervenção
    - "Lost Cause"    # Vai churnar independente de intervenção
    - "Sleeping Dog"  # Intervenção pode AUMENTAR churn (incômodo)

REQ-8-002: "Algoritmo: Causal Forest (ou Two-Model approach)"
  method: "CausalForest from causalml or econml"
  treatment: "teve intervenção de CS nos últimos 60 dias"
  outcome: "churn_flag nos 90 dias seguintes"
  features: "account_view columns"
  output: |
    - uplift_score: redução esperada na probabilidade de churn
    - persuasability_category: uma das 4 categorias
    - confidence: nível de confiança da classificação
```

### 8.2 Validação

```yaml
REQ-8-003: "Qini curve: uplift model DEVE superar baseline aleatório"
  metric: "Qini coefficient > 0.20"
  acceptance: "Modelo identifica pelo menos 30% mais persuadables que aleatório"
```

---

## SPEC-9: Intervention Playbook

```yaml
spec:
  id: "SPEC-9"
  title: "Intervention Playbook — O que fazer"
  status: "Draft"
  owner: "Product Manager"
  depends_on: ["SPEC-5", "SPEC-6", "SPEC-7", "SPEC-8"]
```

### 9.1 Catálogo de Intervenções

```yaml
REQ-9-001: "Playbook DEVE conter catálogo de intervenções com:"
  interventions:
    - id: "INT-001"
      name: "Executive Outreach"
      trigger: "health_score < 40 OR churn_probability > 0.7"
      channel: "email + phone"
      owner: "CRO / VP CS"
      cost_estimate_usd: 500
      expected_impact: "30-50% reduction in critical churn"
      roi_estimate: "15x-25x"
    
    - id: "INT-002"
      name: "CSM Intensive"
      trigger: "health_score 41-60 OR churn_probability 0.5-0.7"
      channel: "email + in-app"
      owner: "CSM assigned"
      cost_estimate_usd: 200
      actions:
        - "Schedule diagnostic call within 48h"
        - "Create get-well plan with milestones"
        - "Offer training session"
    
    - id: "INT-003"
      name: "Automated Re-engagement"
      trigger: "health_score 61-75 AND usage_trend < -20%"
      channel: "in-app + email"
      owner: "Automated"
      cost_estimate_usd: 5
      actions:
        - "Send usage tips email"
        - "In-app nudge to use unused features"
        - "Case study of similar company success"
    
    - id: "INT-004"
      name: "Involuntary Churn Recovery"
      trigger: "churn_type == 'involuntary'"
      channel: "dunning email + SMS"
      owner: "Automated + Billing team"
      cost_estimate_usd: 1
      actions:
        - "Smart retry (3 attempts, different times)"
        - "Email with update payment method link"
        - "Offer invoice/boleto alternative"
      expected_impact: "20-40% recovery"
      roi_estimate: "100x+ (zero cost, high return)"

REQ-9-002: "Playbook DEVE mapear segmento x intervenção"
  logic: "Decision tree ou lookup table: industry + plan + health_tier → recommended interventions"
  format: "JSON editável (não hardcoded)"
```

### 9.2 ROI Estimation

```yaml
REQ-9-003: "Para cada conta em risco, calcular ROI estimado de cada intervenção:"
  formula: |
    roi = (churn_probability * intervention_effectiveness * account_mrr * 12) - intervention_cost
  output: "Tabela: account_id | intervention_id | estimated_roi | priority_score"
```

### 9.3 Playbook Engine

```yaml
REQ-9-004: "Playbook engine DEVE gerar plano de ação semanal:"
  format: |
    [
      {
        "account_id": "A-12345",
        "risk_score": 82,
        "churn_probability": 0.73,
        "predicted_churn_date": "2026-09-15",
        "top_reason": "feature_gap",
        "recommended_intervention": "INT-002",
        "estimated_roi": 45000,
        "next_best_action": "Schedule diagnostic call",
        "csm_owner": "carla.silva@ravenstack.com"
      },
      ...
    ]
```

---

## SPEC-10: Dashboard, API e Visualização

```yaml
spec:
  id: "SPEC-10"
  title: "Dashboard, API e Visualização"
  status: "Implemented"
  owner: "Fullstack Engineer"
  depends_on: ["SPEC-2", "SPEC-3", "SPEC-4", "SPEC-5", "SPEC-11", "SPEC-12"]
```

### 10.1 Views

```yaml
REQ-10-001: "Executive View (para CRO/CEO)"
  sections:
    - "Churn KPI bar: churn_rate, mrr_lost, arr_at_risk, nrr_trend"
    - "ARR em risco por segmento (treemap)"
    - "Trend de churn rate (últimos 12 meses)"
    - "Health score distribution (histograma)"
    - "Top 10 contas em risco com ROI estimado"

REQ-10-002: "CS Team View (para operação semanal)"
  sections:
    - "Lista priorizada de contas (sorted by risk_score desc)"
    - "Filtros por: industry, plan, country, health_tier"
    - "Detalhe da conta: score breakdown, SHAP reasons, playbook"
    - "Ações pendentes e histórico de intervenções"
    - "Gráfico de curva de sobrevivência da conta vs segmento"

REQ-10-003: "Product View (para time de produto)"
  sections:
    - "Feature usage heatmap (features x churn rate)"
    - "Feature gap analysis: features ausentes vs. competitors"
    - "Error rate correlation with churn"
    - "Beta feature adoption impact on retention"
```

### 10.2 Output Formats

```yaml
REQ-10-004: "Report HTML auto-contido (sem dependências externas)"
  description: >
    Gera um único arquivo HTML com tudo inline (CSS, JS, dados).
    Plotly.js opcional (carregado via CDN, com fallback para tabelas).
  acceptance: "Arquivo < 1MB, abre offline sem problemas"

REQ-10-005: "Data Export em formato aberto"
  formats: ["JSON", "Parquet", "CSV"]
  acceptance: "Todos os dados do dashboard exportáveis com 1 clique"
```

### 10.3 REST API Layer (para deploy Railway)

```yaml
REQ-10-006: "API FastAPI com 4 endpoints principais:"
  endpoints:
    - method: "POST /api/v1/run"
      description: "Executa o pipeline completo e retorna run_id assíncrono"
      input: "JSON com config_path opcional"
      output: |
        {
          "run_id": "uuid",
          "status": "processing",
          "estimated_seconds": 30
        }
    
    - method: "GET /api/v1/runs/{run_id}"
      description: "Status e resultados de uma execução"
      output: |
        {
          "run_id": "uuid",
          "status": "completed" | "processing" | "failed",
          "pipeline_version": "0.1.0",
          "results": {
            "overall_stats": {...},
            "segments": [...],
            "health_distribution": {...}
          },
          "output_paths": {
            "report": "/output/report.html",
            "data": "/output/account_view.parquet"
          }
        }
    
    - method: "GET /api/v1/accounts/risk"
      description: "Lista priorizada de contas em risco"
      query_params:
        - "tier: Critical | At Risk | Neutral"
        - "industry: EdTech | FinTech | ..."
        - "min_score: int"
        - "limit: int (default 50)"
        - "llm_explain: boolean (default true) — se true, inclui narrativa LLM"
      output: |
        {
          "accounts": [
            {
              "account_id": "A-12345",
              "health_score": 35,
              "health_tier": "Critical",
              "mrr_amount": 5000,
              "industry": "FinTech",
              "top_risk_factors": ["usage_drop_40pct", "3_escalations", "champion_inactive"],
              "llm_narrative": "Esta conta apresenta queda de 40% no uso...",
              "recommended_action": "INT-002",
              "estimated_save_roi": "$34,000"
            }
          ],
          "total_at_risk": 85,
          "total_mrr_at_risk": 425000,
          "generated_at": "2026-07-16T11:00:00Z"
        }
    
    - method: "GET /api/v1/accounts/{account_id}/explain"
      description: "Explicação narrativa LLM para uma conta específica (SPEC-12)"
      query_params:
        - "depth: short | detailed (default: detailed)"
      output: |
        {
          "account_id": "A-12345",
          "narrative": "...",
          "risk_factors": [...],
          "recommended_actions": [...],
          "model": "deepseek-v4-flash-free",
          "generated_at": "..."
        }

REQ-10-007: "Run report como HTML servido estaticamente"
  description: >
    Após POST /run, o report.html gerado fica acessível em
    GET /output/{run_id}/report.html — sem necessidade de rebuild.

REQ-10-008: "Cron job semanal automático no Railway"
  schedule: "0 9 * * 1"  # toda segunda 9h
  action: "POST /api/v1/run"
  outputs:
    - "Relatório semanal atualizado"
    - "Lista de contas em risco atualizada"
    - "Notificação no Slack (se configurado)"
```

---

## SPEC-11: Infraestrutura & Deploy (Railway)

```yaml
spec:
  id: "SPEC-11"
  title: "Infraestrutura & Deploy (Railway)"
  status: "Draft"
  owner: "DevOps"
  depends_on: ["SPEC-1", "SPEC-10"]
```

### 11.1 Contexto

A plataforma deve ser implantada no **Railway** como um web service FastAPI
com build detectado automaticamente (Python buildpack). O pipeline roda
on-demand via API e em schedule semanal via cron jobs Railway.

### 11.2 Arquitetura de Deploy

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Repository                         │
│  main ──push──▶ Railway auto-deploy                              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Railway Web Service                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  FastAPI App (uvicorn)                                   │   │
│  │  Port 8080                                               │   │
│  │                                                          │   │
│  │  GET /health          → "ok"                             │   │
│  │  POST /api/v1/run     → Executa pipeline (assíncrono)    │   │
│  │  GET /api/v1/runs/    → Lista execuções anteriores       │   │
│  │  GET /api/v1/accounts → Contas em risco + LLM explain    │   │
│  │  GET /output/{id}/*   → Artefatos estáticos (report)     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Cron: weekly-run (seg 09:00)                            │   │
│  │  → POST /api/v1/run + Slack notification                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Ephemeral Storage (/output)                             │   │
│  │  • account_view.parquet                                  │   │
│  │  • scored_accounts.parquet                               │   │
│  │  • analysis_results.json                                 │   │
│  │  • report.html                                           │   │
│  │  • dqr.json                                              │   │
│  │  ⚠ Volátil: backup via export JSON nos logs              │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 11.3 Dockerfile

```dockerfile
REQ-11-001: "Dockerfile DEVE ser multi-stage com runtime otimizado:"
  FROM python:3.14-slim AS builder
  WORKDIR /app
  COPY pyproject.toml .
  RUN pip install --no-cache-dir .
  COPY src/churn_platform/ ./src/churn_platform/
  COPY config/ ./config/
  COPY run.py .

  FROM python:3.14-slim AS runtime
  WORKDIR /app
  COPY --from=builder /app /app
  COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
  EXPOSE 8080
  CMD ["uvicorn", "churn_platform.api:app", "--host", "0.0.0.0", "--port", "8080"]
  acceptance: "docker build -t churn-platform . && docker run -p 8080:8080 churn-platform responde em /health"
```

### 11.4 railway.json

```yaml
REQ-11-002: "railway.json DEVE configurar build e deploy:"
  {
    "build": {
      "builder": "DOCKERFILE",
      "dockerfilePath": "Dockerfile"
    },
    "deploy": {
      "restartPolicyType": "ON_FAILURE",
      "restartPolicyMaxRetries": 3,
      "healthcheckPath": "/health",
      "healthcheckTimeout": 10
    }
  }
```

### 11.5 Configuração Railway

```yaml
REQ-11-003: "Variáveis de ambiente Railway:"
  variables:
    PIPELINE_CONFIG: "config/ravenstack.yaml"
    OUTPUT_DIR: "/app/output"
    OPENCODE_API_KEY: "${{ secrets.OPENCODE_API_KEY }}"  # SPEC-12
    LOG_LEVEL: "INFO"
    CRON_SCHEDULE: "0 9 * * 1"
    
REQ-11-004: "Service config Railway:"
  service:
    name: "churn-platform-api"
    source: "https://github.com/generalrodolfao/ai-master-challenge"
    branch: "main"
    auto_deploy: true
    domains:
      - "churn-platform.up.railway.app"
```

### 11.6 Cron Jobs

```yaml
REQ-11-005: "Cron Job semanal: run + report + notify"
  jobs:
    - id: "weekly-churn-run"
      schedule: "0 9 * * 1"  # toda segunda 9h BRT
      command: "curl -X POST https://churn-platform.up.railway.app/api/v1/run -H 'Content-Type: application/json' -d '{\"cron\": true}'"
      timeout: 300  # 5 min max

REQ-11-006: "Health check endpoint obrigatório"
  endpoint: "GET /health"
  response: |
    {
      "status": "ok",
      "version": "0.1.0",
      "spec_version": "1.0",
      "last_run": "2026-07-16T11:00:00Z",
      "uptime_seconds": 3600
    }
```

### 11.7 Custos Estimados Railway

```yaml
REQ-11-007: "Custo mensal estimado:"
  breakdown:
    web_service:
      cpu: "0.5 vCPU"
      ram: "512 MB"
      cost: "$5.00/mês"
    ephemeral_storage: "$0.00 (incluído)"
    network_egress: "$0.50/mês (estimado)"
    cron_jobs: "$0.00 (incluído no web service)"
    total_estimated: "$5.50 - $7.00/mês"
  
  scaling:
    - "Até 10 runs simultâneas sem degradação"
    - "Acima disso, subir para 1 vCPU / 1 GB (+$5/mês)"
```

---

## SPEC-12: LLM Integration (OpenCode on-demand)

```yaml
spec:
  id: "SPEC-12"
  title: "LLM Integration — OpenCode on-demand"
  status: "Draft"
  owner: "AI Engineer"
  depends_on: ["SPEC-5", "SPEC-10", "SPEC-11"]
```

### 12.1 Contexto

O diferencial competitivo identificado na pesquisa de mercado foi a
**explicabilidade em linguagem natural**. Enquanto consultorias entregam
SHAP plots e tabelas, um AI Master entrega **narrativa compreensível**
para cada conta em risco — explicando o cenário, o que mudou e o que fazer.

A integração com OpenCode permite usar LLM **on-demand**, apenas quando
o CS team precisa de contexto adicional, sem custo fixo de API.

### 12.2 Fluxo de Chamada

```
POST /api/v1/accounts/{id}/explain
         │
         ▼
   ┌─────────────────┐
   │  Buscar dados    │
   │  da conta no     │
   │  account_view    │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │  Montar prompt   │
   │  estruturado     │
   │  com contexto    │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │  Chamar OpenCode │
   │  (subprocess)    │
   │  com timeout 30s │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │  Parse resposta  │
   │  + cache por 24h │
   └────────┬────────┘
            │
            ▼
   JSON Response
```

### 12.3 Prompt Template

```yaml
REQ-12-001: "Prompt template estruturado DEVE conter:"
  system_prompt: >
    Você é um analista de Customer Success especializado em churn para SaaS B2B.
    Sua função é gerar explicações claras e acionáveis para o time de CS sobre
    por que uma conta específica está em risco de churn.
    
    Regras:
    1. Seja específico com dados, não genérico
    2. Destaque o que MUDOU (tendência), não apenas o estado atual
    3. Termine com a ação mais importante que o CSM deve tomar
    4. Use linguagem que um CSM (não data scientist) entenda
    5. NÃO invente dados — use apenas o que foi fornecido
    6. Seja direto: máximo 4 parágrafos

  user_prompt_template: >
    ## Dados da Conta
    - ID: {account_id}
    - Indústria: {industry}
    - Plano: {plan_tier}
    - MRR: ${mrr_amount}/mês
    - Seats: {seats} usuários
    
    ## Health Score: {health_score}/100 ({health_tier})
    
    ## Pilares
    - Usage:   {pillar_usage:.0f}/100 — {usage_context}
    - Support: {pillar_support:.0f}/100 — {support_context}
    - Engagement: {pillar_engagement:.0f}/100 — {engagement_context}
    - Financial: {pillar_financial:.0f}/100 — {financial_context}
    
    ## Tendências (últimos 90 dias)
    - Uso total: {usage_count_total} (mudança: {usage_trend})
    - Erros: {error_count_total} (mudança: {error_trend})
    - Tickets de suporte: {ticket_count} (mudança: {ticket_trend})
    - Escalações: {escalation_count}
    - Satisfação média: {avg_satisfaction}
    
    ## Motivo principal de risco
    - {top_risk_factor_1}
    - {top_risk_factor_2}
    - {top_risk_factor_3}
    
    Gere uma análise de 2-3 parágrafos explicando:
    1. Por que esta conta está em risco
    2. O que mudou nas últimas semanas
    3. Ação recomendada com justificativa
```

### 12.4 Cache Strategy

```yaml
REQ-12-002: "Cache de explicações DEVE evitar chamadas repetidas:"
  key: "explain:{account_id}:{date}"
  ttl: "24 horas"
  storage: "dicionário em memória (volátil) + fallback JSON file em /output/cache/"
  invalidation: "nova execução do pipeline limpa cache"
  
REQ-12-003: "Timeout DEVE ser de 30 segundos por chamada:"
  implementation: |
    try:
        with timeout(30):
            result = subprocess.run(["opencode", ...], capture_output=True, text=True)
    except TimeoutError:
        result = {"narrative": "Indisponível no momento. Tente novamente mais tarde.",
                  "fallback": true}
```

### 12.5 Modelo e Custo

```yaml
REQ-12-004: "Modelo: deepseek-v4-flash-free (padrão do OpenCode):"
  characteristics:
    model: "deepseek-v4-flash-free"
    provider: "OpenCode"
    cost_per_call: "$0.00 (incluído no OpenCode)"
    avg_tokens_per_explain: 800-1200
    avg_latency: "5-15 segundos"
    max_concurrent: 5

  cost_projection:
    - "50 CSMs × 10 contas/semana = 500 chamadas/semana"
    - "≈ 2.000 chamadas/mês"
    - "Custo OpenCode: $0.00 (já incluso na assinatura)"
    - "Custo de tempo de CI: insignificante"
```

### 12.6 Quality Gates

```yaml
REQ-12-005: "Qualidade da explicação DEVE ser validada:"
  automated_checks:
    - "Não contém linguagem hedging ('pode ser', 'talvez', 'potencialmente')"
    - "Contém pelo menos 1 dado numérico específico"
    - "Contém pelo menos 1 ação concreta"
    - "Máximo 4 parágrafos"
    
  manual_validation:
    - "Revisão semanal por amostragem (10% das explicações)"
    - "CSM pode marcar como 'útil' ou 'não útil'"
    - "Feedback loop: prompts ajustados com base em rejeições"

REQ-12-006: "Fallback sem LLM:"
  description: >
    Se LLM estiver indisponível, o endpoint retorna explicação template
    baseada em regras: "Conta em risco por {fatores}. Scores: {pillares}."
  acceptance: "Endpoint nunca falha — no máximo retorna fallback semântico"
```

### 12.7 OpenCode Integration Module

```python
REQ-12-007: "Módulo DEVE ser implementado como:"
  # src/churn_platform/llm/engine.py

  class LLMExplainer:
      def __init__(self, cache_ttl: int = 86400):
          self.cache = {}
          self.cache_ttl = cache_ttl

      async def explain(self, account: dict, depth: str = "detailed") -> dict:
          """Gera explicação narrativa via OpenCode."""
          ...

      def _build_prompt(self, account: dict, depth: str) -> str:
          """Monta prompt estruturado com dados da conta."""
          ...

      def _call_opencode(self, prompt: str) -> str:
          """subprocess opencode --prompt \"...\" com timeout."""
          ...

      def _fallback_explain(self, account: dict) -> dict:
          """Explicação template sem LLM."""
          ...
```

```yaml
harness:
  test_1: "POST /api/v1/accounts/A-2e4581/explain → retorna 200 com narrative não vazia"
  test_2: "Chamada repetida em <24h → retorna do cache (mesmo narrative)"
  test_3: "LLM indisponível → retorna fallback semântico"
  test_4: "Prompt contém dados reais da conta (verificar account_id no texto)"
```

## Apêndice A: Glossário

| Termo | Definição |
|-------|-----------|
| **Churn** | Cliente que cancela ou não renova assinatura |
| **Voluntary Churn** | Cliente decide ativamente cancelar |
| **Involuntary Churn** | Falha de pagamento, cartão expirado, etc. |
| **NRR** | Net Revenue Retention — receita retida de base existente |
| **GRR** | Gross Revenue Retention — NRR excluindo expansão |
| **LTV** | Lifetime Value — receita total esperada de um cliente |
| **CAC** | Customer Acquisition Cost |
| **Health Score** | Métrica composta (0-100) de risco de churn |
| **Survival Analysis** | Técnica estatística para modelar tempo até evento |
| **Hazard Ratio** | Risco relativo de churn entre grupos |
| **Uplift Modeling** | Técnica causal para estimar efeito de intervenção |
| **SHAP** | Shapley Additive Explanations — explicabilidade de modelo |
| **Cox PH** | Cox Proportional Hazards — modelo de sobrevivência |
| **Kaplan-Meier** | Estimador não-paramétrico de curva de sobrevivência |
| **Playbook** | Conjunto de ações recomendadas para cada perfil de risco |
| **Simpson's Paradox** | Tendência que aparece em grupos mas desaparece ou inverte no agregado |
| **Railway** | Plataforma de deploy serverless (Docker-first) para web services |
| **OpenCode** | Assistente de codificação via CLI com LLM on-demand (deepseek-v4-flash-free) |
| **FastAPI** | Framework Python para APIs REST assíncronas |
| **LLM Narrative** | Explicação em linguagem natural gerada por modelo de linguagem |
| **Health Endpoint** | Endpoint REST (GET /health) para verificação de uptime e versão |
| **Ephemeral Storage** | Armazenamento temporário Railway, resetado a cada deploy |
| **Cron Job** | Tarefa agendada (Railway cron) para execução semanal automática |

---

## Apêndice B: Estrutura de Diretórios Esperada

```
src/
├── __init__.py
├── pipeline/
│   ├── load.py          # SPEC-2
│   ├── clean.py         # SPEC-2
│   ├── merge.py         # SPEC-2
│   └── validate.py      # SPEC-2 (schema + quality)
├── datamodel/
│   └── account_view.py  # SPEC-3
├── analysis/
│   ├── segmentation.py  # SPEC-4
│   └── descriptive.py   # SPEC-4
├── scoring/
│   ├── health_score.py  # SPEC-5
│   └── calibrate.py     # SPEC-5
├── predictive/
│   ├── train.py         # SPEC-6
│   ├── predict.py       # SPEC-6
│   └── explain.py       # SPEC-6 (SHAP)
├── survival/
│   ├── km_estimator.py  # SPEC-7
│   ├── cox_ph.py        # SPEC-7
│   └── predict_time.py  # SPEC-7
├── causal/
│   └── uplift.py        # SPEC-8
├── playbook/
│   ├── engine.py        # SPEC-9
│   └── interventions.yaml  # SPEC-9
├── api/
│   ├── __init__.py       # SPEC-10 (FastAPI app)
│   ├── routes_runs.py   # SPEC-10
│   ├── routes_accounts.py # SPEC-10 + SPEC-12
│   └── health.py        # SPEC-11
├── llm/
│   ├── __init__.py       # SPEC-12
│   └── engine.py        # SPEC-12 (OpenCode integration)
├── dashboard/
│   ├── executive.py     # SPEC-10
│   ├── cs_team.py       # SPEC-10
│   └── product.py       # SPEC-10
│
├── config/
│   ├── ravenstack.yaml
│   └── schemas/
│
├── run.py               # SPEC-1 entry point (CLI)
├── api.py               # SPEC-10 entry point (FastAPI)
├── Dockerfile           # SPEC-11
├── railway.json         # SPEC-11
│
harness/
├── spec-2.test.sh       # Pipeline tests
├── spec-3.test.sh       # Data model tests
├── spec-4.test.sh       # Segmentation tests
├── spec-5.test.sh       # Health score tests
├── spec-6.test.sh       # Predictive tests
├── spec-7.test.sh       # Survival tests
├── spec-8.test.sh       # Uplift tests
├── spec-9.test.sh       # Playbook tests
├── spec-10.test.sh      # Dashboard tests
└── run_all.sh           # Executa todos os harnesses

test/
└── fixtures/
    ├── config_minima.yaml
    ├── accounts_3_rows.csv
    ├── subscriptions_10_rows.csv
    └── expected_account_view.parquet
```

---

## Instruções de Uso

### Para implementar uma spec:

1. Crie branch `impl/SPEC-N-nome`
2. Implemente o código em `src/`
3. Implemente o harness em `harness/spec-N.test.sh`
4. Execute o harness: `bash harness/spec-N.test.sh`
5. Se passar → PR para `main`
6. Se falhar → corrija e repita

### Para validar o sistema completo:

```bash
bash harness/run_all.sh  # Executa todos os testes
# Saída esperada:
# ✓ SPEC-2: Pipeline (3/3 tests passed)
# ✓ SPEC-3: Data Model (8/8 tests passed)
# ✓ SPEC-4: Segmentation (6/6 tests passed)
# ✓ SPEC-5: Health Score (4/4 tests passed)
# ✓ SPEC-6: Predictive (3/3 tests passed)
# ✓ SPEC-7: Survival (2/2 tests passed)
# ✓ SPEC-8: Uplift (1/1 tests passed)
# ✓ SPEC-9: Playbook (2/2 tests passed)
# ✓ SPEC-10: Dashboard (2/2 tests passed)
# Result: 31/31 tests passed
```

---

*Spec-Driven Development · v1.0 · Gerado a partir de pesquisa de mercado com
McKinsey, BCG, Deloitte, Accenture, Bain, KPMG, Falconi e benchmarks globais.*

*Deploy: [Railway](https://railway.app) · LLM on-demand via [OpenCode](https://opencode.ai) · Modelo: deepseek-v4-flash-free*

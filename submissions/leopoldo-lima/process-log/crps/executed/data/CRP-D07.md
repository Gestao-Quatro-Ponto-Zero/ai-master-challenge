# CRP-D07 — Camada de features para scoring

## Objetivo
Desacoplar o motor de score do CSV e preparar explainability de verdade.

## Features mínimas sugeridas
- `days_since_engage`
- `has_account`
- `has_close_date`
- `is_open`
- `is_won`
- `is_lost`
- `account_revenue_band`
- `employee_band`
- `product_series`
- `product_price`
- `regional_office`
- `manager_name`
- `stage_rank`
- `pipeline_age_bucket`

## Saídas
- `docs/FEATURE_CATALOG.md`
- módulo de feature engineering
- testes de transformação

## Definition of Done
- o score consome features, não colunas cruas
- toda feature tem definição e racional
- existem testes para features derivadas de datas e estágio

## Prompt para o Cursor
```text
Implemente o CRP-D07: camada de features do scoring.

Tarefa:
1. Criar um módulo de feature engineering a partir dos modelos core.
2. Produzir OpportunityFeatureSet.
3. Incluir features temporais, de stage, de produto, de conta e de equipe.
4. Criar docs/FEATURE_CATALOG.md com:
   - nome da feature
   - definição
   - origem
   - regra de cálculo
   - risco/interpretação
5. Adicionar testes cobrindo:
   - stage
   - datas
   - joins
   - nulls
6. Atualizar LOG.md.

Critérios:
- Não misturar feature engineering com API/UI
- Priorizar features interpretáveis
- Preparar a base para explainability
```

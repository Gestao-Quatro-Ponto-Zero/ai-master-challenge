# Feature catalog

Camada de feature engineering implementada em `src/features/engineering.py`.

## Features mínimas

| Feature | Definição | Origem | Regra de cálculo | Risco/interpretação |
|---|---|---|---|---|
| `days_since_engage` | dias desde `engage_date` até referência | `Opportunity.engage_date` | `reference_date - engage_date` | datas inválidas viram `0` |
| `has_account` | oportunidade com conta preenchida | `Opportunity.account` | bool non-empty | conta vazia não bloqueia, mas reduz score |
| `has_close_date` | possui data de fechamento | `Opportunity.close_date` | bool non-empty | fechamento pode estar atrasado |
| `is_open` | estado em aberto | `Opportunity.deal_stage` | `Prospecting`/`Engaging` | depende de taxonomia correta |
| `is_won` | estado ganho | `Opportunity.deal_stage` | igualdade com `Won` | idem acima |
| `is_lost` | estado perdido | `Opportunity.deal_stage` | igualdade com `Lost` | idem acima |
| `account_revenue_band` | faixa de receita da conta | `Account.revenue` | `small/mid/enterprise` | depende de parsing numérico |
| `employee_band` | faixa de colaboradores | `Account.employees` | `small/medium/large` | depende de qualidade da dimensão |
| `product_series` | série comercial do produto | `Product.series` | cópia direta | `unknown` sem join |
| `product_price` | preço de tabela | `Product.sales_price` | parse float | inválido vira `0` |
| `regional_office` | escritório regional do agente | `SalesAgent.regional_office` | cópia direta | `unknown` sem join |
| `manager_name` | gestor do agente | `SalesAgent.manager` | cópia direta | `unknown` sem join |
| `stage_rank` | rank ordinal de stage | `Opportunity.deal_stage` | map (`Lost=0`, `Prospecting=1`, `Engaging=2`, `Won=3`) | stages novos caem em `0` |
| `pipeline_age_bucket` | bucket de idade do pipeline | `days_since_engage` | `fresh/active/stale` | sem `engage_date`, vira `fresh` por default de 0 dias |

## Testes
- `tests/test_features.py`
- Execução:

```powershell
python -m pytest -q tests/test_features.py
```

## Impacto no scoring
O motor de score consome `OpportunityFeatureSet` (não colunas cruas), permitindo explainability mais estável entre dados, scoring e API.

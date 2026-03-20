# Prompt 001b — Leitura do schema oficial

**Data:** 2026-03-20
**Agent:** Schema Reader
**Ferramenta:** Claude Code
**Executado por:** Lucas Reis

---

## Prompt enviado ao Claude Code

> Contexto: projeto G4 AI Master Challenge — Challenge 001 Diagnóstico de Churn.
> Leia o CLAUDE.md na raiz antes de começar.
>
> **PROMPT 001b — Leitura do schema oficial**
>
> Antes de qualquer análise, preciso entender o schema oficial dos dados.
>
> **TAREFA 1** — Leia o arquivo submissions/lucas-reis/solution/data/README.md e extraia:
> - Nome de cada coluna por tabela
> - Tipo de dado esperado
> - Descrição de negócio de cada campo
> - Relacionamentos entre tabelas (chaves primárias e estrangeiras)
> - Qualquer nota especial sobre os dados
>
> **TAREFA 2** — Salve o resultado em submissions/lucas-reis/docs/data_dictionary.md com
> uma tabela markdown por dataset.
>
> **TAREFA 3** — Liste: colunas mais relevantes para churn, joins possíveis, o que não é óbvio no README.
>
> **TAREFA 4** — Registre em process-log/prompts/prompt_001b_schema.md este prompt literal,
> conteúdo extraído e observações sobre o schema.

---

## Conteúdo extraído do README

### Metadados do dataset
- **Autor:** River @ Rivalytics
- **Licença:** MIT-like (sintético, sem PII)
- **Complexidade:** Capstone-level (multi-table, event-driven, time-sensitive)
- **Geração:** Python com pandas, numpy, uuid; lógica temporal validada

### Volumes
| Tabela | Registros |
|--------|-----------|
| accounts | 500 |
| subscriptions | 5.000 |
| feature_usage | 25.000 |
| support_tickets | 2.000 |
| churn_events | 600 |

### Relacionamentos (do README)
```
accounts (PK: account_id)
│
├── subscriptions (FK → accounts.account_id)
│   └── feature_usage (FK → subscriptions.subscription_id)
│
├── support_tickets (FK → accounts.account_id)
└── churn_events (FK → accounts.account_id)
```

### Schemas extraídos

**accounts.csv:** account_id, account_name, industry, country, signup_date, referral_source, plan_tier, seats, is_trial, churn_flag

**subscriptions.csv:** subscription_id, account_id, start_date, end_date, plan_tier, seats, mrr_amount, arr_amount, is_trial, upgrade_flag, downgrade_flag, churn_flag, billing_frequency, auto_renew_flag

**feature_usage.csv:** usage_id, subscription_id, usage_date, feature_name, usage_count, **usage_duration_secs**, error_count, is_beta_feature

**support_tickets.csv:** ticket_id, account_id, submitted_at, closed_at, resolution_time_hours, priority (low/medium/high/**urgent**), first_response_time_minutes, satisfaction_score, escalation_flag

**churn_events.csv:** churn_event_id, account_id, churn_date, reason_code, refund_amount_usd, preceding_upgrade_flag, preceding_downgrade_flag, **is_reactivation**, feedback_text

---

## Observações críticas sobre o schema

### Erros no código gerado anteriormente (a corrigir)

| Problema | Onde | Correção |
|---------|------|---------|
| `usage_duration_min` não existe | 02_cross_table_agent.py, 03_hypothesis_agent.py | Usar `usage_duration_secs`, converter para min dividindo por 60 |
| `company_size` não existe | 02_cross_table_agent.py, 04_predictive_agent.py | Substituir por `seats` como proxy |
| `contract_value` não existe | 02_cross_table_agent.py, 03_hypothesis_agent.py, 04_predictive_agent.py | Substituir por `mrr_amount` de subscriptions |
| `priority = 'high'` incompleto | 02_cross_table_agent.py | Incluir `urgent`: `priority IN ('high', 'urgent')` |
| JOIN em churn_events sem deduplicação | 02_cross_table_agent.py | Adicionar `QUALIFY ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY churn_date DESC) = 1` |

### Insights analíticos não óbvios

1. **`satisfaction_score` null é sinal ativo** — não imputar, criar flag `satisfaction_is_null`
2. **`preceding_upgrade_flag` em churn_events** — churnou após upgrade = "buyer's remorse"
3. **`is_beta_feature`** — controlar ao calcular `error_count` (beta features têm mais erros por natureza)
4. **`auto_renew_flag = False`** nos 20% de subs — pré-churn signal potente
5. **`feedback_text`** — campo livre com NLP potential para além do `reason_code`
6. **Dois `plan_tier`** — accounts (signup) vs subscriptions (atual) — comparar para detectar trajetória do cliente

### Decisões estratégicas para os agents

**Agent 02 (cross_table):** Reformular a query mestre com:
- Agregação de `mrr_amount` (não `contract_value`)
- Contagem de `priority IN ('high', 'urgent')` (não só 'high')
- Deduplicação de churn_events com `ROW_NUMBER()` ou MAX(churn_date)
- `usage_duration_secs / 60` ao calcular duração de sessão
- `seats` como proxy de tamanho da empresa

**Agent 03 (hypothesis):** Reformular hipóteses com:
- H4: usar `mrr_amount` em vez de `contract_value`
- Adicionar H6: `auto_renew_flag = False → maior churn`
- Adicionar H7: `preceding_downgrade_flag = True → maior churn na sequência`

**Agent 04 (model):** Remover `company_size` e `contract_value` das FEATURE_COLS, adicionar:
- `mrr_amount_mean` (média por conta)
- `auto_renew_false_count`
- `escalation_flag_count`
- `satisfaction_null_rate`

---

## Output gerado nesta sessão

- `submissions/lucas-reis/docs/data_dictionary.md` — dicionário completo com 5 tabelas, joins, colunas relevantes e 10 observações não óbvias
- `submissions/lucas-reis/process-log/prompts/prompt_001b_schema.md` — este arquivo

## Próximo passo

Corrigir `02_cross_table_agent.py` e `04_predictive_agent.py` com o schema real antes de executar o pipeline com os dados reais.

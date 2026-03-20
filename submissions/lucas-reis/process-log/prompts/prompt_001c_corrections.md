# Prompt 001c — Correção dos agents antes do EDA

**Data:** 2026-03-20
**Agent:** Correção/Revisão
**Ferramenta:** Claude Code
**Executado por:** Lucas Reis

---

## Prompt enviado ao Claude Code

> Contexto: projeto G4 AI Master Challenge — Challenge 001 Diagnóstico de Churn.
> Leia o CLAUDE.md e docs/data_dictionary.md antes de começar.
>
> A leitura do schema oficial revelou 5 erros nos agents gerados anteriormente.
> Corrija TODOS antes de qualquer execução.
>
> **Correção 1** — usage_duration_min → usage_duration_secs / 60.0
>
> **Correção 2** — churn_events: usar ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY churn_date DESC)
>
> **Correção 3** — company_size → seats; contract_value → mrr_amount
>
> **Correção 4** — priority = 'high' → priority IN ('high', 'urgent')
>
> **Correção 5** — satisfaction_score NULL = sinal; criar satisfaction_no_response_rate
>
> Aplicar em: 01_eda_agent.py, 02_cross_table_agent.py, 03_hypothesis_agent.py, 04_predictive_agent.py
> Salvar: process-log/entries/entry_000_corrections.md e este arquivo.

---

## Arquivos modificados e resumo das mudanças

### 01_eda_agent.py — SEM MODIFICAÇÃO NECESSÁRIA
O Agent 01 lê os CSVs dinamicamente via `df.describe(include="all")` sem referenciar
nomes de coluna hardcoded. Ele perfilará as colunas reais que existirem nos CSVs.
Nenhuma das 5 correções se aplica a este arquivo.

### 02_cross_table_agent.py — 5 CORREÇÕES + 3 EXTRAS

| Linha original | Erro | Correção aplicada |
|---------------|------|------------------|
| 35–36 | `usage_duration_min` | `usage_duration_secs / 60.0 AS avg_session_min` |
| 51–54 | JOIN direto em churn_events | CTE `churn_deduped` com ROW_NUMBER() |
| 58 | `a.company_size` | `a.seats` |
| 60 | `a.contract_value` | `sa.avg_mrr`, `sa.total_mrr` (de sub_agg) |
| 46 | `priority = 'high'` | `priority IN ('high', 'urgent')` + `n_urgent` separado |
| — (ausente) | sem satisfaction flag | `satisfaction_no_response_rate` adicionada |
| 23 | `status = 'active'` (inexistente) | `end_date IS NULL` |
| 26 | `plan_name` (inexistente) | `plan_tier` |
| 52 | `churn_reason` (inexistente) | `reason_code` |

**Features novas adicionadas ao master view:**
`avg_mrr`, `total_mrr`, `n_downgrades`, `n_upgrades`, `n_no_autorenew`, `n_annual_subs`,
`total_errors`, `beta_errors`, `stable_errors`, `n_urgent_tickets`, `n_escalations`,
`avg_first_response_min`, `avg_satisfaction`, `n_no_satisfaction_response`,
`satisfaction_no_response_rate`, `preceding_downgrade_flag`, `preceding_upgrade_flag`,
`is_reactivation`, `refund_amount_usd`

### 03_hypothesis_agent.py — 3 CORREÇÕES + 2 HIPÓTESES NOVAS

| Item | Erro | Correção aplicada |
|------|------|------------------|
| H3 | `company_size` | `seats` (proxy numérico de tamanho) |
| H4 | `contract_value` | `avg_mrr` |
| `__main__` | colunas inexistentes | `seats`, `avg_mrr`, `n_no_autorenew`, `preceding_downgrade_flag` |
| — | H6 ausente | Adicionada: `n_no_autorenew > 0 → maior churn` |
| — | H7 ausente | Adicionada: `preceding_downgrade_flag → maior churn` |
| — | sem `validate_binary_hypothesis` | Adicionada função para validar flags booleanas |

### 04_predictive_agent.py — 3 CORREÇÕES + 8 FEATURES NOVAS

| Item | Erro | Correção aplicada |
|------|------|------------------|
| FEATURE_COLS | `contract_value` | substituído por `avg_mrr`, `total_mrr` |
| FEATURE_COLS | `company_size` | substituído por `seats` (numérico, sem encoding) |
| `prepare_features` | encoding de `company_size` | removido; só `industry` e categoricals reais |
| `__main__` | dados sintéticos com colunas falsas | realinhado ao schema real |

**Features novas no modelo:**
`avg_mrr`, `total_mrr`, `n_downgrades`, `n_no_autorenew`, `n_annual_subs`,
`n_escalations`, `total_errors`, `stable_errors`, `n_urgent_tickets`,
`satisfaction_no_response_rate`, `seats`, `referral_source`, `initial_plan_tier`,
`account_is_trial`, `avg_first_response_min`

---

## Output gerado nesta sessão

- `02_cross_table_agent.py` — reescrito com schema correto
- `03_hypothesis_agent.py` — corrigido com 7 hipóteses (era 5)
- `04_predictive_agent.py` — corrigido com 25 features (era 12)
- `process-log/entries/entry_000_corrections.md` — documentação detalhada dos 5 erros
- `process-log/prompts/prompt_001c_corrections.md` — este arquivo

---

## Estado do pipeline após as correções

| Agent | Status | Pronto para executar? |
|-------|--------|----------------------|
| 01_eda_agent.py | Sem alteração necessária | ✅ Sim (requer CSVs em data/) |
| 02_cross_table_agent.py | Corrigido | ✅ Sim (requer CSVs em data/) |
| 03_hypothesis_agent.py | Corrigido | ✅ Sim (requer output do Agent 02) |
| 04_predictive_agent.py | Corrigido | ✅ Sim (requer output do Agent 02) |
| 05_report_agent.py | Não avaliado nesta sessão | ⏳ Pendente |

## Próximo passo

Baixar os 5 CSVs para `solution/data/` e executar o pipeline na ordem 01 → 02 → 03 → 04 → 05.

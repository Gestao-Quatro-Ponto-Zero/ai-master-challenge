# Contrato de dados — Fase 1

> **Status geral:** `VALIDATED_WITH_WARNINGS`. Os cinco arquivos foram lidos em UTF-8, os schemas foram observados diretamente e os relacionamentos mínimos têm cobertura referencial completa. A identidade de eventos de uso, a precedência do target e regras temporais permanecem abertas para a Fase 2.

## Inventário validado

| Tabela | Arquivo real | Registros | Granularidade observada | Chave | Chaves estrangeiras | Campos temporais | Status |
|---|---|---:|---|---|---|---|---|
| Contas | `ravenstack_accounts.csv` | 500 | uma linha por `account_id` no snapshot | `account_id` — `CANDIDATE` | nenhuma | `signup_date` | `VALIDATED_WITH_WARNINGS` |
| Assinaturas | `ravenstack_subscriptions.csv` | 5.000 | uma linha por `subscription_id` no snapshot | `subscription_id` — `CANDIDATE` | `account_id` → contas | `start_date`, `end_date` | `VALIDATED_WITH_WARNINGS` |
| Uso de funcionalidades | `ravenstack_feature_usage.csv` | 25.000 | evento de uso; identidade definitiva não provada | `usage_id` — `INVALID`; composto testado — `INVALID` | `subscription_id` → assinaturas | `usage_date` | `INCONCLUSIVE` |
| Tickets de suporte | `ravenstack_support_tickets.csv` | 2.000 | uma linha por `ticket_id` no snapshot | `ticket_id` — `CANDIDATE` | `account_id` → contas | `submitted_at`, `closed_at` | `VALIDATED_WITH_WARNINGS` |
| Eventos de churn | `ravenstack_churn_events.csv` | 600 | uma linha por `churn_event_id` no snapshot | `churn_event_id` — `CANDIDATE` | `account_id` → contas | `churn_date` | `VALIDATED_WITH_WARNINGS` |

`CANDIDATE` significa completo e único neste snapshot. Estabilidade entre snapshots depende de evidência de governança da fonte.

## Contrato por tabela

### Contas

- **Arquivo:** `ravenstack_accounts.csv`.
- **Registros/colunas:** 500/10; nenhuma linha completamente duplicada.
- **Campos:** `account_id` (str), `account_name` (str), `industry` (str), `country` (str), `signup_date` (str), `referral_source` (str), `plan_tier` (str), `seats` (int64), `is_trial` (bool), `churn_flag` (bool).
- **Granularidade/chave:** uma conta por `account_id`; 500 valores não nulos e únicos.
- **Temporal:** `signup_date`, formato `YYYY-MM-DD`, intervalo 2023-01-02 a 2024-12-31, sem inválidos e sem timezone declarado.
- **Financeiro:** nenhum campo monetário; `seats` é medida operacional.
- **Texto:** `account_name`; somente estatísticas agregadas podem sair da zona bruta.
- **Leakage:** `churn_flag` é explícito e proibido como feature anterior ao churn.
- **Qualidade:** 277 contas têm evento de churn com flag falsa; 35 têm flag verdadeira sem evento.
- **Status:** `VALIDATED_WITH_WARNINGS`.

### Assinaturas

- **Arquivo:** `ravenstack_subscriptions.csv`.
- **Registros/colunas:** 5.000/14; nenhuma linha completamente duplicada.
- **Campos:** `subscription_id`, `account_id`, `start_date`, `end_date`, `plan_tier`, `seats`, `mrr_amount`, `arr_amount`, `is_trial`, `upgrade_flag`, `downgrade_flag`, `churn_flag`, `billing_frequency`, `auto_renew_flag`.
- **Granularidade/chave:** uma assinatura por `subscription_id`; completa e única no snapshot.
- **Relacionamento:** `account_id` cobre 100% das linhas; zero órfãos; 2–19 assinaturas por conta, mediana 10.
- **Temporal:** `start_date` e `end_date`; 4.514 `end_date` ausentes; datas válidas, sem end anterior ao start.
- **Financeiro:** `mrr_amount` e `arr_amount`; zero valores negativos e zero divergências de `ARR = MRR × 12` no snapshot.
- **Texto:** nenhum texto livre.
- **Leakage:** `churn_flag` é explícito; `end_date` é proxy; demais campos exigem corte as-of quando mutáveis.
- **Qualidade:** relação um-para-muitos infla o grão de contas em 10× se unida sem agregação.
- **Status:** `VALIDATED_WITH_WARNINGS`.

### Uso de funcionalidades

- **Arquivo:** `ravenstack_feature_usage.csv`.
- **Registros/colunas:** 25.000/8; nenhuma linha completamente duplicada.
- **Campos:** `usage_id`, `subscription_id`, `usage_date`, `feature_name`, `usage_count`, `usage_duration_secs`, `error_count`, `is_beta_feature`.
- **Granularidade/chave:** `usage_id` tem 21 duplicatas excedentes/42 linhas afetadas; o composto `subscription_id + usage_date + feature_name` tem 3 excedentes/6 linhas afetadas. Identidade final `INCONCLUSIVE`.
- **Relacionamento:** `subscription_id` cobre 100% das linhas; zero órfãos; 33 assinaturas sem uso; 0–16 eventos por assinatura, mediana 5.
- **Temporal:** `usage_date`, formato `YYYY-MM-DD`, 2023-01-01 a 2024-12-31, sem inválidos; 19.142 registros (76,568%) antecedem o início da assinatura e 290 (1,16%) sucedem o fim.
- **Financeiro/texto:** sem campo monetário ou texto livre; `feature_name` é categórico.
- **Leakage:** `usage_date` e medidas somente podem ser usados com corte as-of e vínculo temporal válido.
- **Qualidade:** identidade duplicada e cronologia incompatível exigem quarentena ou regra explícita na Fase 2.
- **Status:** `INCONCLUSIVE` para a chave; `VALIDATED_WITH_WARNINGS` para schema e relacionamento.

### Tickets de suporte

- **Arquivo:** `ravenstack_support_tickets.csv`.
- **Registros/colunas:** 2.000/9; nenhuma linha completamente duplicada.
- **Campos:** `ticket_id`, `account_id`, `submitted_at`, `closed_at`, `resolution_time_hours`, `priority`, `first_response_time_minutes`, `satisfaction_score`, `escalation_flag`.
- **Granularidade/chave:** uma linha por `ticket_id`; completa e única no snapshot.
- **Relacionamento:** `account_id` cobre 100% das linhas; zero órfãos; 8 contas sem ticket; 0–11 tickets por conta, mediana 4.
- **Temporal:** `submitted_at` é data e `closed_at` é datetime sem timezone declarado; zero datas inválidas e zero encerramentos anteriores à abertura.
- **Financeiro/texto:** sem campos monetários e sem texto livre no schema real.
- **Leakage:** fechamento, duração, primeira resposta, satisfação e escalonamento dependem do tempo de disponibilidade e exigem corte as-of.
- **Qualidade:** 825 valores de satisfação ausentes; 1.077 tickets (53,85%) antecedem o signup; 386 de 1.395 tickets em contas com churn ocorrem após o primeiro churn e são ocorrências a investigar.
- **Status:** `VALIDATED_WITH_WARNINGS`.

### Eventos de churn

- **Arquivo:** `ravenstack_churn_events.csv`.
- **Registros/colunas:** 600/9; nenhuma linha completamente duplicada.
- **Campos:** `churn_event_id`, `account_id`, `churn_date`, `reason_code`, `refund_amount_usd`, `preceding_upgrade_flag`, `preceding_downgrade_flag`, `is_reactivation`, `feedback_text`.
- **Granularidade/chave:** um evento por `churn_event_id`; completa e única no snapshot.
- **Relacionamento:** `account_id` cobre 100% das linhas; zero órfãos; 0–5 eventos por conta, mediana 1.
- **Temporal:** `churn_date`, formato `YYYY-MM-DD`, 2023-01-25 a 2024-12-31, sem inválidos; 53 eventos (8,8333%) antecedem a primeira assinatura; 55 não encontram assinatura ativa.
- **Financeiro:** `refund_amount_usd`, sem valores negativos.
- **Texto:** `feedback_text`, 148 ausentes; nenhum texto bruto é reproduzido nos artefatos.
- **Leakage:** todos os campos da tabela, exceto a identidade relacional usada para auditoria, são proibidos como features anteriores ao desfecho.
- **Qualidade:** 148 contas sem churn, 177 com um evento e 175 com múltiplos; máximo 5; 61 eventos têm reativação explícita.
- **Status:** `VALIDATED_WITH_WARNINGS`.

## Relacionamentos e política de join

As quatro relações mínimas têm taxa de match de 100%, zero chaves estrangeiras nulas e zero órfãos. Todas são um-para-muitos e `UNSAFE_WITHOUT_AGGREGATION`. Simulações key-only mediram multiplicadores de 10×, 5,0066×, 4,016× e 1,496×. O encadeamento ingênuo alcançou 147.896 linhas a partir de 500 contas (295,792×).

É proibido materializar uma mega-tabela. A Fase 2 deve normalizar eventos por fonte e unir somente dimensões ou agregados as-of no grão explicitamente escolhido.

## Testes obrigatórios recorrentes

1. unicidade e não nulidade das chaves candidatas;
2. duplicidade de `usage_id` e do composto de uso;
3. integridade referencial e taxa de match;
4. missingness, strings vazias e sentinelas;
5. domínios, valores negativos e reconciliação financeira;
6. parsing, intervalos e ordem temporal;
7. inflação de joins e preservação de entidades;
8. conflitos entre flags de churn e eventos;
9. leakage por disponibilidade temporal;
10. regex agregada de privacidade sem reprodução de texto;
11. churn recorrente e reativação.

## Gate para a Fase 2

**`PASS_WITH_WARNINGS`**. Chaves relacionais, cobertura e campos temporais permitem construir um event log, desde que a Fase 2: defina identidade substituta para uso; não use `accounts.churn_flag` como fonte soberana sem regra de precedência; mantenha fontes em grãos separados; aplique corte as-of; marque ou coloque em quarentena eventos temporalmente impossíveis; e preserve churn recorrente e reativação sem colapsá-los.

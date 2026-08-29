# Dados processados — base account-month

Gerado por `solution/src/02_reconcile_churn.py` (Iteração 02; offline e determinístico).

## `account_month.csv` — grão-mestre account × mês

- Linhas: 5807 (uma por account_id × mês; 500 contas; janela do mês do signup até 2024-12).
- Estado no FIM do mês; regra do winner conforme contrato `solution/docs/analytical-contract.md` §6.
- Checksum MD5 (esta versão): `b718c4f842609ee14eb56d5d4edcf012`

## Colunas

| Coluna | Semântica |
|---|---|
| `account_id` | chave da conta |
| `month` | mês `YYYY-MM` (estado no fim do mês) |
| `month_end` | último dia do mês (data) |
| `months_since_signup` | meses desde o mês do signup (0 = mês do signup) |
| `status` | `active`/`inactive` pela lente de assinatura (winner) |
| `n_active_subs` | nº de assinaturas ativas no fim do mês |
| `winner_subscription_id` | assinatura vencedora (vazia se inativa) |
| `winner_mrr` | MRR do winner (0 se inativa) |
| `winner_plan_tier`, `winner_seats`, `winner_is_trial`, `winner_billing_frequency` | atributos do winner |
| `mrr_sum_naive` | soma ingênua do MRR das ativas (auditoria; NÃO usar como métrica) |
| `mrr_ended_in_month` | soma do MRR das assinaturas com `end_date` no mês (lente R1 — gross ending MRR; reconciliada à fonte por G14); DESFECHO do mês, PROIBIDA como feature do próprio mês (contrato §8) |
| `n_ended_in_month` | nº de assinaturas com `end_date` no mês (trials têm MRR 0, por isso a contagem é separada); DESFECHO do mês, PROIBIDA como feature do próprio mês (contrato §8) |
| `churn_event_in_month` | 1 se ≥1 evento de churn no mês (lente de eventos) |
| `n_events_in_month` | nº de eventos no mês |
| `usage_rows_month` | linhas de uso no mês (bruto, sem filtro de janela) |
| `usage_rows_in_window_month` | linhas de uso no mês dentro de [start, end] da assinatura |
| `tickets_month` | tickets abertos no mês |
| `csat_mean_month` | média de CSAT dos tickets do mês (vazio se nenhum) |
| `churn_flag_snapshot_2024_12_31` | rótulo do corte (`accounts.churn_flag`); PROIBIDO em features de risco (contrato §8) |

## Uso

- Esta base é regenerável: `python3 solution/src/02_reconcile_churn.py`.
- Nunca editar manualmente; alterações quebram o checksum e os invariantes G1–G15.

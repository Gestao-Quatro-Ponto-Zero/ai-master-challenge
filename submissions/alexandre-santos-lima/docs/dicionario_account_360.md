# Dicionário — account_360.csv

Uma linha por conta (500). Colunas agrupadas por categoria.


## perfil — fonte: `accounts` (10 colunas)

| coluna | tipo | nulos | exemplo |
|---|---|---|---|
| `perfil_account_name` | str | 0 | Company_0 |
| `perfil_industry` | str | 0 | EdTech |
| `perfil_country` | str | 0 | US |
| `perfil_referral_source` | str | 0 | partner |
| `perfil_plan_tier` | str | 0 | Basic |
| `perfil_seats` | int64 | 0 | 9 |
| `perfil_is_trial` | bool | 0 | False |
| `perfil_signup_date` | datetime64[us] | 0 | 2024-10-16 00:00:00 |
| `perfil_coorte_signup` | str | 0 | 2024Q4 |
| `perfil_dias_desde_signup` | int64 | 0 | 76 |

## receita — fonte: `subscriptions` (18 colunas)

| coluna | tipo | nulos | exemplo |
|---|---|---|---|
| `receita_assinaturas` | int64 | 0 | 10 |
| `receita_assinaturas_ativas` | int64 | 0 | 10 |
| `receita_assinaturas_encerradas` | int64 | 0 | 0 |
| `receita_assinaturas_trial` | int64 | 0 | 2 |
| `receita_mrr_ativo` | int64 | 0 | 12603 |
| `receita_mrr_perdido` | int64 | 0 | 0 |
| `receita_mrr_medio_assinatura` | float64 | 0 | 1260.3 |
| `receita_seats_ativos` | int64 | 0 | 312 |
| `receita_pct_anual` | float64 | 0 | 0.3 |
| `receita_pct_auto_renew` | float64 | 0 | 0.8 |
| `receita_upgrades` | int64 | 0 | 1 |
| `receita_downgrades` | int64 | 0 | 0 |
| `receita_primeira_assinatura` | datetime64[us] | 0 | 2024-10-20 00:00:00 |
| `receita_arr_ativo` | int64 | 0 | 151236 |
| `receita_pct_mrr_perdido` | float64 | 0 | 0.0 |
| `receita_pct_assin_basic` | float64 | 0 | 0.3 |
| `receita_pct_assin_pro` | float64 | 0 | 0.5 |
| `receita_pct_assin_enterprise` | float64 | 0 | 0.2 |

## uso — fonte: `feature_usage → subscriptions` (16 colunas)

| coluna | tipo | nulos | exemplo |
|---|---|---|---|
| `uso_registros` | int64 | 0 | 55 |
| `uso_eventos` | int64 | 0 | 535 |
| `uso_duracao_h` | float64 | 0 | 42.316 |
| `uso_erros` | int64 | 0 | 38 |
| `uso_registros_com_erro` | int64 | 0 | 16 |
| `uso_features_distintas` | int64 | 0 | 27 |
| `uso_registros_beta` | int64 | 0 | 4 |
| `uso_ultimo_registro` | datetime64[us] | 0 | 2024-12-10 00:00:00 |
| `uso_taxa_erro` | float64 | 0 | 0.071 |
| `uso_pct_registros_com_erro` | float64 | 0 | 0.291 |
| `uso_pct_beta` | float64 | 0 | 0.073 |
| `uso_duracao_media_min` | float64 | 0 | 46.163 |
| `uso_eventos_2023` | int64 | 0 | 207 |
| `uso_eventos_2024` | int64 | 0 | 328 |
| `uso_variacao_2024_vs_2023` | float64 | 0 | 0.585 |
| `uso_dias_desde_ultimo` | int64 | 0 | 21 |

## suporte — fonte: `support_tickets` (10 colunas)

| coluna | tipo | nulos | exemplo |
|---|---|---|---|
| `suporte_tickets` | float64 | 0 | 2.0 |
| `suporte_pct_urgente_alta` | float64 | 8 | 1.0 |
| `suporte_resolucao_media_h` | float64 | 8 | 23.0 |
| `suporte_resolucao_max_h` | float64 | 8 | 27.0 |
| `suporte_primeira_resposta_media_min` | float64 | 8 | 91.0 |
| `suporte_escalonamentos` | float64 | 0 | 0.0 |
| `suporte_satisfacao_media` | float64 | 34 | 3.0 |
| `suporte_pct_sem_nota` | float64 | 8 | 0.5 |
| `suporte_ultimo_ticket` | datetime64[us] | 8 | 2024-12-10 00:00:00 |
| `suporte_pct_escalonados` | float64 | 8 | 0.0 |

## churn — fonte: `churn_events + accounts.churn_flag` (17 colunas)

| coluna | tipo | nulos | exemplo |
|---|---|---|---|
| `churn_eventos` | float64 | 0 | 2.0 |
| `churn_primeiro` | datetime64[us] | 148 | 2024-11-23 00:00:00 |
| `churn_ultimo` | datetime64[us] | 148 | 2024-12-05 00:00:00 |
| `churn_reembolso_total` | float64 | 0 | 0.0 |
| `churn_reativacoes` | float64 | 0 | 0.0 |
| `churn_upgrade_previo` | float64 | 0 | 1.0 |
| `churn_downgrade_previo` | float64 | 0 | 0.0 |
| `churn_motivo_ultimo` | str | 148 | competitor |
| `churn_feedback_ultimo` | str | 202 | switched to competitor |
| `churn_motivo_n_budget` | float64 | 0 | 1.0 |
| `churn_motivo_n_competitor` | float64 | 0 | 1.0 |
| `churn_motivo_n_features` | float64 | 0 | 0.0 |
| `churn_motivo_n_pricing` | float64 | 0 | 0.0 |
| `churn_motivo_n_support` | float64 | 0 | 0.0 |
| `churn_motivo_n_unknown` | float64 | 0 | 0.0 |
| `churn_flag_conta` | bool | 0 | False |
| `churn_tem_evento` | bool | 0 | True |

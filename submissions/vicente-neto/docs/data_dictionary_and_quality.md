# RavenStack — Fase 1 (qualidade dos dados) + Fase 2 (dicionário da tabela mestre)

Crédito do dataset: River @ Rivalytics (sintético, licença MIT-like). Janela observada: 2023-01-01 a 2024-12-31.

## 1. Estrutura e chaves (validado)
| Tabela | Linhas | Granularidade | Chaves |
|---|---|---|---|
| accounts | 500 | 1 por conta | sem duplicatas |
| subscriptions | 5.000 | ~10 por conta (2 a 19) | 0 órfãs |
| feature_usage | 25.000 | por assinatura/dia/feature | 0 órfãs; 4.967 de 5.000 assinaturas têm uso |
| support_tickets | 2.000 | 492 de 500 contas têm ticket | 0 órfãos |
| churn_events | 600 | 352 contas (1 a 5 eventos) | 0 órfãos |

Reconciliação master × bruto: assinaturas 5.000 ✔, linhas de uso 25.000 ✔, soma usage_count 250.525 ✔, tickets 2.000 ✔, eventos de churn 600 ✔, refund US$ 8.652,25 ✔, MRR ativo US$ 10.159.608 ✔.

## 2. Problemas encontrados (e a decisão tomada)
1. **`accounts.churn_flag` (110 contas) não bate com `churn_events` (352 contas).** Só 75 contas estão nos dois. A cruzada mostra praticamente zero relação entre os dois. → **Definição adotada: `has_churn_event`** (352 contas, 70,4%). O flag da tabela accounts ficou como `churn_flag_account`, só para referência.
2. **Todas as 500 contas têm ≥2 assinaturas "ativas" (sem end_date).** Não existe conta 100% encerrada pelas assinaturas. Assinaturas se sobrepõem (média 9 ativas por conta) e se comportam como linhas de produto, não como renovações sequenciais. → MRR da conta = soma das assinaturas pagantes ativas (`mrr_active_sum`). Média de US$ 20 mil por conta, **inflado** vs. um SaaS real; use como peso relativo, não como receita absoluta.
3. **Churn_events tem contas com até 5 eventos e 61 marcados `is_reactivation`.** → Ficam `n_churn_events`, `first_churn_date` e flags. O corte para features é o **primeiro** churn.
4. **77% das linhas de uso têm data anterior ao start_date da assinatura, e 52,9% do volume de uso é anterior ao cadastro da própria conta** (94,6% no 1T23, 6,0% no 4T24). → Uso é agregado por conta (via subscription_id). Nas análises de uso, conta só o **uso válido** (`usage_date >= signup_date`); o total registrado não mede crescimento.
5. **`usage_id` repete em 21 pares** (conteúdos diferentes, não são linhas duplicadas). → Mantidas todas as linhas; chave própria criada no script.
6. **Satisfação:** só valores 3, 4 e 5 (nunca 1 ou 2); 41,3% dos tickets sem nota (825/2.000).
7. `plan_tier` e `seats` da assinatura diferem do da conta em 67% e 48% dos casos. → Mantidos os dois (`plan_tier_account`, `dominant_plan_tier`).
8. MRR = seats × preço fixo (Basic 19, Pro 49, Enterprise 199) em 100% das linhas; ARR = 12 × MRR; trials têm MRR 0 (778 assinaturas).
9. `reason_code` e `feedback_text` são independentes (ex.: "pricing" tem feedback "missing features" tanto quanto "too expensive"; qui-quadrado p = 0,99). → O motivo declarado é pouco confiável.
10. **A flag `is_trial` da conta (97 contas) não bate com as assinaturas de trial (403 contas).** Em 311 contas a primeira assinatura paga começa antes do trial. → Não tratar trial → paga como funil de conversão.
11. **28% do uso e 27,7% dos tickets das contas churnadas acontecem depois da data de churn.** → Variáveis de modelo usam só dados até o corte (sufixo `_pre`).

## 3. Sinais revisados (após as Fases 3 e 4)
- **"Churn subiu" = verdadeiro:** 6 eventos no 1T23 → 251 no 4T24. Sobre as contas já ativas no início do período, a taxa trimestral de primeiro churn vai de 18,5% (4T23) para 32,2% (4T24), e a mensal de ~4–7% (2023) para 18,4% (dez/24). A versão anterior deste documento (22,5% em dez/24) somava ao numerador contas que entraram no próprio mês.
- **"Uso cresceu" = não se sustenta:** o total registrado subiu 2,6% em 8 trimestres, mas mais da metade dele é anterior ao cadastro. O uso válido por conta ativa foi de 54,3 para 55,5 por trimestre em 2024 (+2,3%), sem diferença significativa entre segmentos (Kruskal p de 0,13 a 0,91).
- **"Satisfação ok" = verdadeiro, mas frágil:** CSAT médio ~4,0, estável no tempo, com 41% sem nota e escala truncada em 3–5.
- **Churnadas e retidas são quase idênticas** em seats, MRR, uso válido, erros por uso (mediana 4,29 vs 4,44 por 100 nos 90 dias antes do corte), beta, tickets, CSAT, escalações e resolução. A exceção é o canal: **ads retém mais** (sobrevivência em 365 dias de 41% vs 26% nos demais; log-rank p = 0,005).
- Diferenças de `tenure_days_at_cutoff`, `mrr_at_cutoff` e de uso em janelas fixas antes do corte entre os grupos são artefato do desenho (corte no primeiro churn vs. fim da janela; contas jovens têm menos histórico), não achado.

## 4. Dicionário da tabela `accounts_master` (106 colunas, 1 linha/conta)
Gerada por `build_accounts_master.sql` (PostgreSQL/Supabase).
**Identificação (accounts):** account_id, account_name, industry, country, signup_date, referral_source, plan_tier_account, seats_account, is_trial_account, churn_flag_account, signup_quarter, size_band (1-5, 6-20, 21-50, 50+).

**Alvo e churn (churn_events):** `has_churn_event` (alvo recomendado), churn_status (churned/retained), n_churn_events, first/last_churn_date, churn_quarter, first_churn_reason, top_churn_reason, first_churn_feedback, total_refund_usd, churn_any_reactivation, churn_any_preceding_downgrade, churn_any_preceding_upgrade.

**Corte temporal:** `cutoff_date` = primeiro churn (churnadas) ou 2024-12-31 (retidas); tenure_days_at_cutoff; observation_end. Colunas com sufixo `_pre` usam só dados até o corte (seguras para modelo).

**Assinaturas:** n_subs, n_subs_active, n_subs_ended, n_subs_trial, n_upgrades, n_downgrades, n_upgrades_pre, n_downgrades_pre, n_subs_auto_renew_off, pct_subs_annual, pct_mrr_annual, first/last_sub_start, last_sub_end, dominant_plan_tier, n_enterprise_subs, **mrr_active_sum**, arr_active_sum, seats_active_sum, n_subs_active_paying, mrr_active_annual, mrr_ended_sum, mrr_avg_per_paying_sub, **mrr_at_cutoff** (MRR vivo no corte, peso do churn), n_subs_live_at_cutoff, mrr_band.

**Uso** (atenção: estas colunas somam **todo** o uso registrado, inclusive o anterior ao cadastro; para análise, recalcule só com o uso válido, como em `evidence.py`): usage_rows, usage_count, usage_hours, error_count, error_per_100_uses, distinct_features, beta_usage_count, beta_share (versões `_pre` também), last_usage_date_pre, days_since_last_usage_at_cutoff, usage_last90 / usage_prev90 / **usage_trend_pct** (90 dias antes do corte vs. 90 anteriores; vazio quando prev90=0), has_usage.

**Suporte:** n_tickets, n_tickets_rated, pct_tickets_rated, avg_csat, min_csat, n_tickets_escalated, pct_tickets_escalated, n_tickets_urgent_high, avg/max_resolution_hours, avg_first_response_min, last_ticket_date, has_ticket (versões `_pre` também).

**Dia 30 e trial:** data_dia_30 (cadastro + 30 dias), churn_ate_d30, paga_vigente_d30, status_d30 ("churnou ate dia 30", "efetiva (paga ativa dia 30)", "sem pagamento ativo no dia 30"), churn_apos_d30, dias_ate_primeira_paga, dias_ate_primeiro_trial, sequencia_trial_paga ("trial antes da paga", "paga antes do trial", "mesmo dia", "sem trial").

## 5. Tabela auxiliar `monthly_trend` (24 linhas)
Gerada por `build_monthly_trend.py`. Por mês: signups, contas_ativas_inicio (base da taxa), churn_events, contas_primeiro_churn, primeiro_churn_da_base, **taxa_primeiro_churn_pct** (primeiro churn entre contas já ativas no início do mês; vazia enquanto a base tem menos de 30 contas), refund_usd, uso_registrado, uso_valido, pct_uso_antes_cadastro, contas_ativas_no_mes, uso_valido_por_conta_ativa, erros_por_100_usos_validos, tickets, avg_csat, pct_tickets_com_nota, pct_escalados.

## 6. Cuidados para as próximas fases
- Nulos são significativos (sem ticket, sem uso, CSAT ausente): não imputar com média.
- Não use `tenure_days_at_cutoff`, `mrr_at_cutoff` nem uso em janelas fixas antes do corte (`usage_last90`, usos por 30 dias) como variável de modelo: refletem o tempo de vida da conta, não o comportamento.
- Taxas de churn: a base é sempre o conjunto de contas já ativas no início do período; contas que entram no período não entram no numerador.
- Uso: filtre `usage_date >= signup_date` antes de qualquer soma ou tendência.
- Churn em MRR: use `mrr_active_sum` ou `mrr_at_cutoff`, sempre declarando a limitação do item 2.

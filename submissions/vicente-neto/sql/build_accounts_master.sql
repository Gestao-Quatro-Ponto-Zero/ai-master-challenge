-- ============================================================================
-- RavenStack | Challenge 001 | Tabela mestre (1 linha por conta)
-- Compatível com PostgreSQL / Supabase. Rode tudo no SQL Editor, na ordem.
--
-- Passo 1: cria as 5 tabelas brutas
-- Passo 2: importe os CSVs (Table Editor > Import data from CSV), na mesma ordem
-- Passo 3: cria accounts_master (bloco final)
-- ============================================================================

-- ---------- PASSO 1: tabelas brutas ----------------------------------------
drop table if exists public.churn_events, public.support_tickets, public.feature_usage,
                     public.subscriptions, public.accounts cascade;

create table public.accounts (
  account_id text primary key, account_name text, industry text, country text,
  signup_date date, referral_source text, plan_tier text, seats integer,
  is_trial boolean, churn_flag boolean);

create table public.subscriptions (
  subscription_id text primary key, account_id text references public.accounts(account_id),
  start_date date, end_date date, plan_tier text, seats integer, mrr_amount numeric,
  arr_amount numeric, is_trial boolean, upgrade_flag boolean, downgrade_flag boolean,
  churn_flag boolean, billing_frequency text, auto_renew_flag boolean);

-- usage_id tem 21 valores repetidos no arquivo original: sem chave primária
create table public.feature_usage (
  usage_id text, subscription_id text references public.subscriptions(subscription_id),
  usage_date date, feature_name text, usage_count integer, usage_duration_secs integer,
  error_count integer, is_beta_feature boolean);

create table public.support_tickets (
  ticket_id text primary key, account_id text references public.accounts(account_id),
  submitted_at timestamp, closed_at timestamp, resolution_time_hours numeric,
  priority text, first_response_time_minutes numeric, satisfaction_score numeric,
  escalation_flag boolean);

create table public.churn_events (
  churn_event_id text primary key, account_id text references public.accounts(account_id),
  churn_date date, reason_code text, refund_amount_usd numeric,
  preceding_upgrade_flag boolean, preceding_downgrade_flag boolean,
  is_reactivation boolean, feedback_text text);

-- Importe nesta ordem: accounts, subscriptions, feature_usage, support_tickets, churn_events
-- Conferência: select count(*) from accounts -> 500; subscriptions -> 5000;
--              feature_usage -> 25000; support_tickets -> 2000; churn_events -> 600


-- ---------- PASSO 3: tabela mestre ----------------------------------------
drop table if exists public.accounts_master;

create table public.accounts_master as
with
-- data de corte: primeiro churn, ou fim da janela observada para as contas retidas
params as (select date '2024-12-31' as observation_end),

-- ---- churn_events -> 1 linha por conta
ch_base as (
  select account_id, churn_date, churn_event_id, reason_code, feedback_text,
         refund_amount_usd, is_reactivation, preceding_downgrade_flag, preceding_upgrade_flag
  from public.churn_events),
ch as (
  select account_id,
    count(*)                 as n_churn_events,
    min(churn_date)          as first_churn_date,
    max(churn_date)          as last_churn_date,
    -- primeiro valor não nulo, na ordem cronológica (pandas .first())
    (array_agg(reason_code  order by churn_date, churn_event_id) filter (where reason_code is not null))[1] as first_churn_reason,
    (array_agg(feedback_text order by churn_date, churn_event_id) filter (where feedback_text is not null))[1] as first_churn_feedback,
    round(coalesce(sum(refund_amount_usd),0), 2) as total_refund_usd,
    bool_or(is_reactivation)              as churn_any_reactivation,
    bool_or(preceding_downgrade_flag)     as churn_any_preceding_downgrade,
    bool_or(preceding_upgrade_flag)       as churn_any_preceding_upgrade
  from ch_base group by account_id),
-- motivo mais frequente; empate -> ordem alfabética (igual ao pandas .mode().iloc[0])
ch_top as (
  select account_id, reason_code as top_churn_reason from (
    select account_id, reason_code,
           row_number() over (partition by account_id order by count(*) desc, reason_code) as rn
    from ch_base where reason_code is not null group by account_id, reason_code) x
  where rn = 1),

-- ---- conta base + corte
base as (
  select a.account_id, a.account_name, a.industry, a.country, a.signup_date,
         a.referral_source, a.plan_tier as plan_tier_account, a.seats as seats_account,
         a.is_trial as is_trial_account, a.churn_flag as churn_flag_account,
         ch.n_churn_events, ch.first_churn_date, ch.last_churn_date,
         ch.first_churn_reason, ch_top.top_churn_reason, ch.first_churn_feedback,
         ch.total_refund_usd, ch.churn_any_reactivation, ch.churn_any_preceding_downgrade,
         ch.churn_any_preceding_upgrade,
         coalesce(ch.first_churn_date, p.observation_end) as cutoff_date,
         p.observation_end
  from public.accounts a
  cross join params p
  left join ch on ch.account_id = a.account_id
  left join ch_top on ch_top.account_id = a.account_id),

-- ---- assinaturas -> por conta
sa as (
  select account_id,
    count(*) as n_subs,
    count(*) filter (where end_date is null)      as n_subs_active,
    count(*) filter (where end_date is not null)  as n_subs_ended,
    count(*) filter (where is_trial)              as n_subs_trial,
    count(*) filter (where upgrade_flag)          as n_upgrades,
    count(*) filter (where downgrade_flag)        as n_downgrades,
    count(*) filter (where not auto_renew_flag)   as n_subs_auto_renew_off,
    round(avg(case when billing_frequency = 'annual' then 1.0 else 0.0 end), 3) as pct_subs_annual,
    min(start_date) as first_sub_start,
    max(start_date) as last_sub_start,
    max(end_date)   as last_sub_end,
    sum(mrr_amount) filter (where end_date is null and not is_trial)                       as mrr_active_sum,
    sum(arr_amount) filter (where end_date is null and not is_trial)                       as arr_active_sum,
    sum(seats)      filter (where end_date is null and not is_trial)                       as seats_active_sum,
    count(*)        filter (where end_date is null and not is_trial)                       as n_subs_active_paying,
    sum(mrr_amount) filter (where end_date is null and not is_trial and billing_frequency = 'annual') as mrr_active_annual,
    sum(mrr_amount) filter (where end_date is not null and not is_trial)                   as mrr_ended_sum,
    count(*)        filter (where plan_tier = 'Enterprise')                                as n_enterprise_subs,
    round(avg(mrr_amount) filter (where not is_trial), 1)                                  as mrr_avg_per_paying_sub
  from public.subscriptions group by account_id),

dom as (
  select account_id, plan_tier as dominant_plan_tier from (
    select account_id, plan_tier,
           row_number() over (partition by account_id order by sum(mrr_amount) desc, plan_tier) as rn
    from public.subscriptions where not is_trial group by account_id, plan_tier) x
  where rn = 1),

-- MRR vivo no momento do corte (peso do churn; NÃO usar como variável de modelo)
live as (
  select b.account_id,
    sum(s.mrr_amount) as mrr_at_cutoff,
    count(*)          as n_subs_live_at_cutoff
  from base b join public.subscriptions s on s.account_id = b.account_id
  where not s.is_trial
    and s.start_date <= b.cutoff_date
    and (s.end_date is null or s.end_date > b.cutoff_date)
  group by b.account_id),

-- upgrades/downgrades iniciados até o corte (todas as assinaturas)
pre_s as (
  select b.account_id,
    count(*) filter (where s.downgrade_flag) as n_downgrades_pre,
    count(*) filter (where s.upgrade_flag)   as n_upgrades_pre
  from base b join public.subscriptions s on s.account_id = b.account_id
  where s.start_date <= b.cutoff_date
  group by b.account_id),

-- ---- uso (feature_usage -> subscriptions -> conta), com e sem corte
uj as (
  select s.account_id, b.cutoff_date, f.usage_date, f.feature_name, f.usage_count,
         f.usage_duration_secs, f.error_count, f.is_beta_feature
  from public.feature_usage f
  join public.subscriptions s on s.subscription_id = f.subscription_id
  join base b on b.account_id = s.account_id),

ua as (
  select account_id,
    count(*)                                   as usage_rows,
    sum(usage_count)                           as usage_count,
    round(sum(usage_duration_secs) / 3600.0, 2) as usage_hours,
    sum(error_count)                           as error_count,
    count(distinct feature_name)               as distinct_features,
    coalesce(sum(usage_count) filter (where is_beta_feature), 0) as beta_usage_count
  from uj group by account_id),

ua_pre as (
  select account_id,
    count(*)                                   as usage_rows_pre,
    sum(usage_count)                           as usage_count_pre,
    round(sum(usage_duration_secs) / 3600.0, 2) as usage_hours_pre,
    sum(error_count)                           as error_count_pre,
    count(distinct feature_name)               as distinct_features_pre,
    coalesce(sum(usage_count) filter (where is_beta_feature), 0) as beta_usage_count_pre,
    max(usage_date)                            as last_usage_date_pre
  from uj where usage_date <= cutoff_date group by account_id),

-- tendência: 90 dias antes do corte vs os 90 dias anteriores
trend as (
  select account_id,
    coalesce(sum(usage_count) filter (where (cutoff_date - usage_date) >= 0  and (cutoff_date - usage_date) < 90),  0) as usage_last90,
    coalesce(sum(usage_count) filter (where (cutoff_date - usage_date) >= 90 and (cutoff_date - usage_date) < 180), 0) as usage_prev90
  from uj group by account_id),

-- ---- tickets -> por conta, com e sem corte
tk as (
  select account_id,
    count(*)                                           as n_tickets,
    count(satisfaction_score)                          as n_tickets_rated,
    round(avg(satisfaction_score), 2)                  as avg_csat,
    min(satisfaction_score)                            as min_csat,
    count(*) filter (where escalation_flag)            as n_tickets_escalated,
    count(*) filter (where priority in ('urgent','high')) as n_tickets_urgent_high,
    round(avg(resolution_time_hours), 1)               as avg_resolution_hours,
    max(resolution_time_hours)                         as max_resolution_hours,
    round(avg(first_response_time_minutes), 1)         as avg_first_response_min,
    max(submitted_at)::date                            as last_ticket_date
  from public.support_tickets group by account_id),

tk_pre as (
  select t.account_id,
    count(*)                                           as n_tickets_pre,
    count(t.satisfaction_score)                        as n_tickets_rated_pre,
    round(avg(t.satisfaction_score), 2)                as avg_csat_pre,
    min(t.satisfaction_score)                          as min_csat_pre,
    count(*) filter (where t.escalation_flag)          as n_tickets_escalated_pre,
    count(*) filter (where t.priority in ('urgent','high')) as n_tickets_urgent_high_pre,
    round(avg(t.resolution_time_hours), 1)             as avg_resolution_hours_pre,
    max(t.resolution_time_hours)                       as max_resolution_hours_pre,
    round(avg(t.first_response_time_minutes), 1)       as avg_first_response_min_pre
  from public.support_tickets t join base b on b.account_id = t.account_id
  where t.submitted_at <= b.cutoff_date::timestamp
  group by t.account_id),

-- ---- dia 30 após o cadastro (efetivação) e sequência trial -> paga
d30_pag as (
  select s.account_id,
    bool_or(s.start_date <= (b.signup_date + 30) and (s.end_date is null or s.end_date > (b.signup_date + 30)))
      filter (where not s.is_trial)                  as paga_vigente_d30,
    min(s.start_date) filter (where not s.is_trial)  as primeira_paga_inicio,
    min(s.start_date) filter (where s.is_trial)      as primeiro_trial_inicio
  from public.subscriptions s join public.accounts b on b.account_id = s.account_id
  group by s.account_id, b.signup_date),

d30_churn as (
  select c.account_id, bool_or(c.churn_date <= (a.signup_date + 30)) as churn_ate_d30
  from public.churn_events c join public.accounts a on a.account_id = c.account_id
  group by c.account_id)

-- ---- montagem final -------------------------------------------------------
select
  b.account_id, b.account_name, b.industry, b.country, b.signup_date, b.referral_source,
  b.plan_tier_account, b.seats_account, b.is_trial_account, b.churn_flag_account,
  to_char(b.signup_date, 'YYYY"Q"Q')                 as signup_quarter,
  coalesce(b.n_churn_events, 0)                      as n_churn_events,
  b.first_churn_date, b.last_churn_date,
  to_char(b.first_churn_date, 'YYYY"Q"Q')            as churn_quarter,
  b.first_churn_reason, b.top_churn_reason, b.first_churn_feedback,
  coalesce(b.total_refund_usd, 0)                    as total_refund_usd,
  b.churn_any_reactivation, b.churn_any_preceding_upgrade, b.churn_any_preceding_downgrade,
  coalesce(b.n_churn_events, 0) > 0                  as has_churn_event,
  b.cutoff_date,
  (b.cutoff_date - b.signup_date)                    as tenure_days_at_cutoff,
  -- assinaturas
  sa.n_subs, sa.n_subs_active, sa.n_subs_ended, sa.n_subs_trial,
  sa.n_upgrades, sa.n_downgrades, sa.n_subs_auto_renew_off, sa.pct_subs_annual,
  sa.first_sub_start, sa.last_sub_start, sa.last_sub_end,
  dom.dominant_plan_tier,
  coalesce(sa.n_enterprise_subs, 0)                  as n_enterprise_subs,
  coalesce(sa.mrr_active_sum, 0)                     as mrr_active_sum,
  coalesce(sa.arr_active_sum, 0)                     as arr_active_sum,
  coalesce(sa.seats_active_sum, 0)                   as seats_active_sum,
  coalesce(sa.n_subs_active_paying, 0)               as n_subs_active_paying,
  coalesce(sa.mrr_active_annual, 0)                  as mrr_active_annual,
  round(coalesce(sa.mrr_active_annual,0) / nullif(sa.mrr_active_sum, 0), 3) as pct_mrr_annual,
  coalesce(sa.mrr_ended_sum, 0)                      as mrr_ended_sum,
  sa.mrr_avg_per_paying_sub,
  coalesce(live.mrr_at_cutoff, 0)                    as mrr_at_cutoff,
  coalesce(live.n_subs_live_at_cutoff, 0)            as n_subs_live_at_cutoff,
  coalesce(pre_s.n_downgrades_pre, 0)                as n_downgrades_pre,
  coalesce(pre_s.n_upgrades_pre, 0)                  as n_upgrades_pre,
  -- uso
  (ua.usage_rows is not null)                        as has_usage,
  coalesce(ua.usage_rows, 0)                         as usage_rows,
  coalesce(ua.usage_count, 0)                        as usage_count,
  coalesce(ua.usage_hours, 0)                        as usage_hours,
  coalesce(ua.error_count, 0)                        as error_count,
  coalesce(ua.distinct_features, 0)                  as distinct_features,
  coalesce(ua.beta_usage_count, 0)                   as beta_usage_count,
  coalesce(round(100.0 * ua.error_count / nullif(ua.usage_count, 0), 2), 0) as error_per_100_uses,
  coalesce(round(1.0 * ua.beta_usage_count / nullif(ua.usage_count, 0), 3), 0) as beta_share,
  coalesce(ua_pre.usage_rows_pre, 0)                 as usage_rows_pre,
  coalesce(ua_pre.usage_count_pre, 0)                as usage_count_pre,
  coalesce(ua_pre.usage_hours_pre, 0)                as usage_hours_pre,
  coalesce(ua_pre.error_count_pre, 0)                as error_count_pre,
  coalesce(ua_pre.distinct_features_pre, 0)          as distinct_features_pre,
  coalesce(ua_pre.beta_usage_count_pre, 0)           as beta_usage_count_pre,
  coalesce(round(100.0 * ua_pre.error_count_pre / nullif(ua_pre.usage_count_pre, 0), 2), 0) as error_per_100_uses_pre,
  coalesce(round(1.0 * ua_pre.beta_usage_count_pre / nullif(ua_pre.usage_count_pre, 0), 3), 0) as beta_share_pre,
  ua_pre.last_usage_date_pre,
  (b.cutoff_date - ua_pre.last_usage_date_pre)       as days_since_last_usage_at_cutoff,
  coalesce(trend.usage_last90, 0)                    as usage_last90,
  coalesce(trend.usage_prev90, 0)                    as usage_prev90,
  round((trend.usage_last90 - trend.usage_prev90) / nullif(trend.usage_prev90, 0)::numeric, 3) as usage_trend_pct,
  -- suporte
  (tk.n_tickets is not null)                         as has_ticket,
  coalesce(tk.n_tickets, 0)                          as n_tickets,
  coalesce(tk.n_tickets_rated, 0)                    as n_tickets_rated,
  round(coalesce(tk.n_tickets_rated,0) / nullif(tk.n_tickets, 0)::numeric, 3) as pct_tickets_rated,
  tk.avg_csat, tk.min_csat,
  coalesce(tk.n_tickets_escalated, 0)                as n_tickets_escalated,
  round(coalesce(tk.n_tickets_escalated,0) / nullif(tk.n_tickets, 0)::numeric, 3) as pct_tickets_escalated,
  coalesce(tk.n_tickets_urgent_high, 0)              as n_tickets_urgent_high,
  tk.avg_resolution_hours, tk.max_resolution_hours, tk.avg_first_response_min,
  tk.last_ticket_date,
  coalesce(tk_pre.n_tickets_pre, 0)                  as n_tickets_pre,
  coalesce(tk_pre.n_tickets_rated_pre, 0)            as n_tickets_rated_pre,
  tk_pre.avg_csat_pre, tk_pre.min_csat_pre,
  coalesce(tk_pre.n_tickets_escalated_pre, 0)        as n_tickets_escalated_pre,
  coalesce(tk_pre.n_tickets_urgent_high_pre, 0)      as n_tickets_urgent_high_pre,
  tk_pre.avg_resolution_hours_pre, tk_pre.max_resolution_hours_pre, tk_pre.avg_first_response_min_pre,
  -- faixas e rótulos
  case when b.n_churn_events > 0 then 'churned' else 'retained' end as churn_status,
  case when b.seats_account <= 5 then '1-5' when b.seats_account <= 20 then '6-20'
       when b.seats_account <= 50 then '21-50' else '50+' end as size_band,
  case when coalesce(sa.mrr_active_sum,0) <= 5000 then '<5k'
       when coalesce(sa.mrr_active_sum,0) <= 15000 then '5-15k'
       when coalesce(sa.mrr_active_sum,0) <= 30000 then '15-30k'
       else '30k+' end as mrr_band,
  b.observation_end,
  -- efetivação no dia 30 após o cadastro
  (b.signup_date + 30)                               as data_dia_30,
  coalesce(dc.churn_ate_d30, false)                  as churn_ate_d30,
  coalesce(dp.paga_vigente_d30, false)               as paga_vigente_d30,
  case when coalesce(dc.churn_ate_d30, false) then 'churnou ate dia 30'
       when coalesce(dp.paga_vigente_d30, false) then 'efetiva (paga ativa dia 30)'
       else 'sem pagamento ativo no dia 30' end       as status_d30,
  (coalesce(b.n_churn_events, 0) > 0 and not coalesce(dc.churn_ate_d30, false)) as churn_apos_d30,
  (dp.primeira_paga_inicio - b.signup_date)          as dias_ate_primeira_paga,
  (dp.primeiro_trial_inicio - b.signup_date)         as dias_ate_primeiro_trial,
  case when dp.primeiro_trial_inicio is null then 'sem trial'
       when dp.primeira_paga_inicio is null then 'so trial'
       when dp.primeiro_trial_inicio < dp.primeira_paga_inicio then 'trial antes da paga'
       when dp.primeiro_trial_inicio > dp.primeira_paga_inicio then 'paga antes do trial'
       else 'mesmo dia' end                          as sequencia_trial_paga
from base b
left join sa      on sa.account_id = b.account_id
left join dom     on dom.account_id = b.account_id
left join live    on live.account_id = b.account_id
left join pre_s   on pre_s.account_id = b.account_id
left join ua      on ua.account_id = b.account_id
left join ua_pre  on ua_pre.account_id = b.account_id
left join trend   on trend.account_id = b.account_id
left join tk      on tk.account_id = b.account_id
left join tk_pre  on tk_pre.account_id = b.account_id
left join d30_pag   dp on dp.account_id = b.account_id
left join d30_churn dc on dc.account_id = b.account_id
order by coalesce(sa.mrr_active_sum, 0) desc, b.account_id;

alter table public.accounts_master add primary key (account_id);

create index if not exists idx_am_status on public.accounts_master (churn_status);
create index if not exists idx_am_mrr    on public.accounts_master (mrr_active_sum desc);

-- Segurança: leitura pública (dados sintéticos). Ajuste se usar Auth.
alter table public.accounts_master enable row level security;
create policy "read accounts_master" on public.accounts_master for select using (true);

-- ---------- Conferência (esperado) -----------------------------------------
-- select count(*) n, sum(mrr_active_sum) mrr, count(*) filter (where has_churn_event) churned
-- from public.accounts_master;      -- 500 | 10159608 | 352

-- Gold (2/3): views de KPI. Fórmulas = dicionário da skill churn-business-analyst.

-- Receita e logos por mês ------------------------------------------------------------
create view gold.kpi_revenue_monthly with (security_invoker = true) as
with m as (
  select f.*,
         lag(f.mrr_end) over (partition by f.account_id order by f.month_start) as mrr_prev
  from gold.fct_account_month f
), agg as (
  select month_start,
         to_char(month_start, 'YYYY"Q"Q') as quarter,
         count(*) filter (where active_at_start) as active_accounts_start,
         count(*) filter (where active_at_end) as active_accounts_end,
         count(*) filter (where churn_events > 0 and active_at_start) as churned_accounts,
         sum(churn_events) as churn_events,
         sum(mrr_prev) filter (where active_at_start) as mrr_start,
         sum(mrr_end) as mrr_end,
         sum(mrr_churned) as mrr_churned,
         sum(greatest(mrr_end - mrr_prev, 0)) filter (where active_at_start and active_at_end) as mrr_expansion,
         sum(greatest(mrr_prev - mrr_end, 0)) filter (where active_at_start and active_at_end) as mrr_contraction
  from m
  group by month_start
)
select a.*,
       round(a.mrr_end * 12, 2) as arr_end,
       round(100.0 * a.churned_accounts / nullif(a.active_accounts_start, 0), 2) as logo_churn_pct,
       round(100.0 * (a.mrr_churned + a.mrr_contraction) / nullif(a.mrr_start, 0), 2) as gross_mrr_churn_pct,
       round(100.0 * (a.mrr_start - a.mrr_churned - a.mrr_contraction) / nullif(a.mrr_start, 0), 2) as grr_pct,
       round(100.0 * (a.mrr_start + a.mrr_expansion - a.mrr_churned - a.mrr_contraction) / nullif(a.mrr_start, 0), 2) as nrr_pct,
       round(a.mrr_end / nullif(a.active_accounts_end, 0), 2) as arpa
from agg a;
comment on view gold.kpi_revenue_monthly is
  'KPIs mensais de logos e receita (MRR, ARR, logo churn, gross MRR churn, GRR, NRR, ARPA). Ressalva: churn e assinaturas são desacoplados na origem; KPIs de receita são aproximados.';

-- Hazard por trimestre × tempo de casa (o gráfico central do diagnóstico) ------------
create view gold.kpi_tenure_hazard with (security_invoker = true) as
select quarter,
       tenure_bucket,
       count(*) as account_months,
       sum(churn_events) as churn_events,
       round(100.0 * sum(churn_events) / count(*), 2) as churn_per_100_account_months,
       sum(mrr_churned) as mrr_churned
from gold.fct_account_month
group by quarter, tenure_bucket;
comment on view gold.kpi_tenure_hazard is
  'Churns por 100 contas-mês por trimestre e faixa de tempo de casa (exposição = todos os meses desde o cadastro, como no diagnóstico H8).';

-- Coortes de cadastro ---------------------------------------------------------------
create view gold.kpi_cohort with (security_invoker = true) as
with first_churn as (
  select account_id, min(tenure_months_at_churn) as first_churn_months
  from gold.fct_churn_event group by account_id
)
select to_char(a.signup_date, 'YYYY"Q"Q') as signup_cohort,
       count(*) as accounts,
       count(*) filter (where gold.as_of_date() - a.signup_date >= 92) as accounts_with_3m,
       count(*) filter (where gold.as_of_date() - a.signup_date >= 183) as accounts_with_6m,
       round(100.0 * count(*) filter (where fc.first_churn_months < 3 and gold.as_of_date() - a.signup_date >= 92)
             / nullif(count(*) filter (where gold.as_of_date() - a.signup_date >= 92), 0), 1) as churn_3m_pct,
       round(100.0 * count(*) filter (where fc.first_churn_months < 6 and gold.as_of_date() - a.signup_date >= 183)
             / nullif(count(*) filter (where gold.as_of_date() - a.signup_date >= 183), 0), 1) as churn_6m_pct
from silver.accounts a
left join first_churn fc using (account_id)
group by 1;
comment on view gold.kpi_cohort is '% de contas da coorte com primeiro churn em 3 e 6 meses (só contas com tempo de observação suficiente).';

-- Churn por segmento (exposição em contas-mês) ---------------------------------------
create view gold.kpi_churn_by_segment with (security_invoker = true) as
with base as (
  select f.account_id, f.churn_events, f.mrr_churned, d.industry, d.country, d.referral_source,
         d.initial_plan, d.initial_trial::text as initial_trial, f.plan_tier as plan_in_month,
         f.billing_frequency as billing_in_month
  from gold.fct_account_month f join gold.dim_account d using (account_id)
), long as (
  select 'industry' as segment_type, industry as segment_value, * from base
  union all select 'country', country, * from base
  union all select 'referral_source', referral_source, * from base
  union all select 'initial_plan', initial_plan, * from base
  union all select 'initial_trial', initial_trial, * from base
  union all select 'plan_in_month', plan_in_month, * from base
  union all select 'billing_in_month', billing_in_month, * from base
)
select segment_type, coalesce(segment_value, '(sem assinatura)') as segment_value,
       count(distinct account_id) as accounts,
       count(*) as account_months,
       sum(churn_events) as churn_events,
       round(100.0 * sum(churn_events) / count(*), 2) as churn_per_100_account_months,
       sum(mrr_churned) as mrr_churned,
       round(100.0 * sum(mrr_churned) / nullif(sum(sum(mrr_churned)) over (partition by segment_type), 0), 1) as pct_mrr_churned
from long
group by segment_type, segment_value;
comment on view gold.kpi_churn_by_segment is
  'Churn e MRR perdido por segmento, com exposição em contas-mês. Nenhum segmento de cadastro foi significativo após Bonferroni (H6).';

-- Concentração de perda ---------------------------------------------------------------
create view gold.kpi_loss_concentration with (security_invoker = true) as
with ranked as (
  select churn_quarter, mrr_at_churn,
         ntile(10) over (partition by churn_quarter order by mrr_at_churn desc) as decile_q,
         ntile(10) over (order by mrr_at_churn desc) as decile_all
  from gold.fct_churn_event where mrr_at_churn is not null
)
select 'total' as period, count(*) as churn_events, sum(mrr_at_churn) as mrr_churned,
       round(100.0 * sum(mrr_at_churn) filter (where decile_all = 1) / sum(mrr_at_churn), 1) as top10pct_share_pct
from ranked
union all
select churn_quarter, count(*), sum(mrr_at_churn),
       round(100.0 * sum(mrr_at_churn) filter (where decile_q = 1) / sum(mrr_at_churn), 1)
from ranked group by churn_quarter;
comment on view gold.kpi_loss_concentration is '% do MRR perdido vindo dos 10% maiores churns (total e por trimestre).';

-- Tipos de churn (novo × repetido) ----------------------------------------------------
create view gold.kpi_churn_type with (security_invoker = true) as
select churn_quarter, churn_type, count(*) as churn_events, coalesce(sum(mrr_at_churn), 0) as mrr_churned
from gold.fct_churn_event group by churn_quarter, churn_type;
comment on view gold.kpi_churn_type is 'Eventos e MRR perdido por trimestre e tipo de churn (primeiro em 0-3m, primeiro depois de 3m, repetido).';

-- Reativação -------------------------------------------------------------------------
create view gold.kpi_reactivation with (security_invoker = true) as
with ev as (
  select e.account_id, e.churn_date,
         (select min(s.start_date) from silver.subscriptions s
           where s.account_id = e.account_id and s.start_date > e.churn_date) as next_start,
         lead(e.churn_date) over (partition by e.account_id order by e.churn_date) as next_churn
  from silver.churn_events e
)
select count(*) as churn_events,
       count(*) filter (where next_start is not null) as followed_by_new_subscription,
       round(100.0 * count(*) filter (where next_start is not null) / count(*), 1) as reactivation_pct,
       percentile_cont(0.25) within group (order by next_start - churn_date) as days_to_reactivate_p25,
       percentile_cont(0.5) within group (order by next_start - churn_date) as days_to_reactivate_median,
       percentile_cont(0.75) within group (order by next_start - churn_date) as days_to_reactivate_p75,
       percentile_cont(0.5) within group (order by next_churn - churn_date) as days_between_churns_median
from ev;
comment on view gold.kpi_reactivation is 'Taxa de reativação (churn seguido de nova assinatura) e intervalos até reativar e até o próximo churn.';

-- Suporte: quem sai × quem fica ------------------------------------------------------
create view gold.kpi_support_health with (security_invoker = true) as
with t as (
  select t.*, (exists (select 1 from silver.churn_events e where e.account_id = t.account_id)) as account_churned
  from silver.support_tickets t
)
select case when account_churned then 'churnou' else 'nunca churnou' end as account_group,
       count(*) as tickets,
       count(distinct account_id) as accounts,
       round(avg(satisfaction_score), 2) as csat_avg,
       round(100.0 * count(satisfaction_score) / count(*), 1) as csat_response_pct,
       min(satisfaction_score) as csat_min_observed,
       max(satisfaction_score) as csat_max_observed,
       round(100.0 * avg(escalation_flag::int), 1) as escalated_pct,
       percentile_cont(0.5) within group (order by first_response_time_minutes) as frt_median_minutes,
       percentile_cont(0.5) within group (order by resolution_time_hours) as resolution_median_hours
from t group by 1;
comment on view gold.kpi_support_health is
  'Saúde do suporte de contas que churnaram × nunca churnaram: são iguais (H1). CSAT só vai de 3 a 5 e 41% sem resposta.';

create view gold.kpi_silent_churn with (security_invoker = true) as
select f.churn_quarter,
       count(*) as churn_events,
       count(*) filter (where not exists (
         select 1 from silver.support_tickets t
          where t.account_id = f.account_id
            and t.submitted_at >= f.churn_date - 90 and t.submitted_at < f.churn_date)) as without_ticket_90d,
       round(100.0 * count(*) filter (where not exists (
         select 1 from silver.support_tickets t
          where t.account_id = f.account_id
            and t.submitted_at >= f.churn_date - 90 and t.submitted_at < f.churn_date)) / count(*), 1) as silent_pct
from gold.fct_churn_event f group by f.churn_quarter;
comment on view gold.kpi_silent_churn is 'Churn silencioso: eventos sem nenhum ticket nos 90 dias anteriores (o CS não vê).';

-- Uso ---------------------------------------------------------------------------------
create view gold.kpi_usage_segment_monthly with (security_invoker = true) as
select to_char(u.usage_date, 'YYYY"Q"Q') as quarter,
       d.current_plan as plan,
       d.industry,
       sum(u.usage_count) as usage_events,
       count(distinct u.account_id) as accounts_with_usage,
       round(sum(u.usage_count)::numeric / nullif(count(distinct u.account_id), 0), 1) as usage_per_account,
       round(sum(u.error_count)::numeric / nullif(sum(u.usage_count), 0), 4) as error_rate,
       round(100.0 * avg(u.is_beta_feature::int), 1) as beta_pct,
       round(100.0 * avg((u.usage_date < d.signup_date)::int), 1) as pct_before_signup
from silver.feature_usage u join gold.dim_account d using (account_id)
group by 1, 2, 3;
comment on view gold.kpi_usage_segment_monthly is
  'Uso por trimestre, plano e indústria. O uso é plano (~63/conta) e 53% tem data anterior ao cadastro: o log não está ancorado no tempo (H2).';

create view gold.kpi_feature_health with (security_invoker = true) as
with churned as (select distinct account_id from silver.churn_events)
select u.feature_name,
       bool_or(u.is_beta_feature) as is_beta,
       count(distinct u.account_id) as accounts,
       round(100.0 * count(distinct u.account_id) / (select count(*) from silver.accounts), 1) as adoption_pct,
       sum(u.usage_count) as usage_events,
       round(sum(u.error_count)::numeric / nullif(sum(u.usage_count), 0), 4) as error_rate,
       round(100.0 * count(distinct u.account_id) filter (where c.account_id is not null)
             / nullif(count(distinct u.account_id), 0), 1) as pct_users_who_churned
from silver.feature_usage u left join churned c using (account_id)
group by u.feature_name;
comment on view gold.kpi_feature_health is 'Adoção, taxa de erro e % de usuários que churnaram por feature.';

-- Motivo declarado × comportamento ----------------------------------------------------
create view gold.churn_reason_vs_behavior with (security_invoker = true) as
select f.churn_event_id, f.account_id, f.churn_date, f.reason_code, f.mrr_at_churn, f.plan_at_churn,
       f.refund_amount_usd, f.preceding_downgrade_flag, f.churn_type,
       (select coalesce(sum(u.usage_count), 0) from silver.feature_usage u
         where u.account_id = f.account_id and u.usage_date >= f.churn_date - 90 and u.usage_date < f.churn_date) as usage_90d,
       (select coalesce(sum(u.error_count), 0) from silver.feature_usage u
         where u.account_id = f.account_id and u.usage_date >= f.churn_date - 90 and u.usage_date < f.churn_date) as errors_90d,
       (select count(*) from silver.support_tickets t
         where t.account_id = f.account_id and t.submitted_at >= f.churn_date - 90 and t.submitted_at < f.churn_date) as tickets_90d,
       (select round(avg(t.satisfaction_score), 2) from silver.support_tickets t
         where t.account_id = f.account_id and t.submitted_at >= f.churn_date - 90 and t.submitted_at < f.churn_date) as csat_90d
from gold.fct_churn_event f;
comment on view gold.churn_reason_vs_behavior is 'Cada churn com o motivo declarado e o comportamento real nos 90 dias anteriores (H4).';

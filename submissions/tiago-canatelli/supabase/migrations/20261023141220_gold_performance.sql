-- Gold (4/4): desempenho. Funções SQL com search_path fixo não são "inlined" pelo Postgres, então
-- views que chamam gold.as_of_date()/is_churned_on() por linha estouravam o timeout. Materializamos
-- dim_account e dim_customer_persona (atualizadas em gold.refresh) e calculamos a data de referência
-- uma vez por consulta. As definições são as mesmas das migrations anteriores.

drop view gold.account_360;
drop view gold.kpi_persona_summary;
drop view gold.kpi_usage_segment_monthly;
drop view gold.kpi_churn_by_segment;
drop view gold.dim_customer_persona;
drop view gold.dim_account;

create materialized view gold.dim_account as
select a.account_id,
       a.account_name,
       a.industry,
       a.country,
       a.referral_source,
       a.plan_tier as initial_plan,
       a.is_trial as initial_trial,
       a.seats as initial_seats,
       a.signup_date,
       to_char(a.signup_date, 'YYYY"Q"Q') as signup_cohort,
       ((gold.as_of_date() - a.signup_date) / 30.44)::numeric(6, 1) as tenure_months,
       s.plan_tier as current_plan,
       s.billing_frequency as current_billing,
       s.seats as current_seats,
       s.auto_renew_flag as current_auto_renew,
       case when gold.is_churned_on(a.account_id, gold.as_of_date()) then 0 else s.mrr_amount end as current_mrr,
       not gold.is_churned_on(a.account_id, gold.as_of_date()) as is_active,
       (select count(*) from silver.churn_events e where e.account_id = a.account_id)::integer as churn_count,
       (select max(e.churn_date) from silver.churn_events e where e.account_id = a.account_id) as last_churn_date
from silver.accounts a
left join lateral gold.subscription_at(a.account_id, gold.as_of_date()) s on true;
create unique index dim_account_pk on gold.dim_account (account_id);
comment on materialized view gold.dim_account is 'Contas com atributos de cadastro e estado atual (plano, MRR vigente, ativa ou não) na data de referência.';
comment on column gold.dim_account.account_id is 'Conta.';
comment on column gold.dim_account.account_name is 'Nome fictício.';
comment on column gold.dim_account.industry is 'Indústria.';
comment on column gold.dim_account.country is 'País.';
comment on column gold.dim_account.referral_source is 'Canal de aquisição.';
comment on column gold.dim_account.initial_plan is 'Plano no cadastro.';
comment on column gold.dim_account.initial_trial is 'Trial no cadastro.';
comment on column gold.dim_account.initial_seats is 'Licenças no cadastro.';
comment on column gold.dim_account.signup_date is 'Data de cadastro.';
comment on column gold.dim_account.signup_cohort is 'Coorte de cadastro (trimestre).';
comment on column gold.dim_account.tenure_months is 'Meses de casa na data de referência.';
comment on column gold.dim_account.current_plan is 'Plano vigente.';
comment on column gold.dim_account.current_billing is 'Cobrança vigente.';
comment on column gold.dim_account.current_seats is 'Licenças vigentes.';
comment on column gold.dim_account.current_auto_renew is 'Renovação automática vigente.';
comment on column gold.dim_account.current_mrr is 'MRR vigente (0 se churnada).';
comment on column gold.dim_account.is_active is 'Ativa na data de referência.';
comment on column gold.dim_account.churn_count is 'Quantas vezes a conta churnou.';
comment on column gold.dim_account.last_churn_date is 'Último churn.';

create materialized view gold.dim_customer_persona as
with d as (
  select d.*,
         exists (select 1 from silver.subscriptions s where s.account_id = d.account_id
                  and s.downgrade_flag and s.start_date > gold.as_of_date() - 90) as downgrade_90d,
         exists (select 1 from silver.subscriptions s where s.account_id = d.account_id
                  and s.upgrade_flag and s.start_date > gold.as_of_date() - 90) as upgrade_90d,
         coalesce((select s.is_trial from gold.subscription_at(d.account_id, gold.as_of_date()) x
                    join silver.subscriptions s using (subscription_id)), false) as current_trial
  from gold.dim_account d
  where d.is_active
)
select account_id,
       case
         when churn_count >= 2 then 'reincidente'
         when downgrade_90d or not current_auto_renew then 'em_retracao'
         when tenure_months < 3 or current_trial then 'recem_chegado'
         when upgrade_90d then 'em_expansao'
         when current_plan = 'Enterprise' and current_billing = 'annual' then 'ancora_enterprise'
         when current_plan in ('Enterprise', 'Pro') and current_billing = 'monthly' then 'grande_sem_compromisso'
         when current_plan = 'Pro' then 'pro_anual'
         else 'pequeno_basic'
       end as persona,
       downgrade_90d, upgrade_90d, current_trial, 'v1'::text as rule_version
from d;
create unique index dim_customer_persona_pk on gold.dim_customer_persona (account_id);
comment on materialized view gold.dim_customer_persona is
  'Persona de cliente das contas ativas, por regra explícita com precedência (reincidente → em retração → recém-chegado → em expansão → âncora Enterprise → grande sem compromisso → Pro anual → pequeno Basic).';


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


-- Resumo por persona -----------------------------------------------------------------
create view gold.kpi_persona_summary with (security_invoker = true) as
select p.persona, pc.label, count(*) as accounts,
       sum(r.mrr) as mrr,
       round(100.0 * sum(r.mrr) / sum(sum(r.mrr)) over (), 1) as pct_mrr,
       round(avg(r.probability_90d), 3) as avg_probability_90d,
       sum(r.mrr_at_risk_90d) as mrr_at_risk_90d,
       round(100.0 * sum(r.mrr_at_risk_90d) / sum(sum(r.mrr_at_risk_90d)) over (), 1) as pct_mrr_at_risk,
       pc.why_it_matters, pc.recommended_play
from gold.dim_customer_persona p
join gold.risk_scores r on r.account_id = p.account_id
  and r.scored_at = (select max(scored_at) from gold.risk_scores)
join gold.persona_catalog pc on pc.persona = p.persona
group by p.persona, pc.label, pc.why_it_matters, pc.recommended_play;
comment on view gold.kpi_persona_summary is 'Contas, MRR e MRR em risco (90 dias) por persona de cliente.';


-- Visão 360 da conta -----------------------------------------------------------------
create view gold.account_360 with (security_invoker = true) as
select d.*,
       p.persona,
       r.probability_90d, r.mrr_at_risk_90d, r.driver_1, r.driver_2, r.driver_3, r.suggested_action,
       (select count(*) from silver.support_tickets t where t.account_id = d.account_id) as tickets_total,
       (select count(*) from silver.support_tickets t where t.account_id = d.account_id
         and t.submitted_at >= ref.as_of - 90) as tickets_90d,
       (select round(avg(t.satisfaction_score), 2) from silver.support_tickets t where t.account_id = d.account_id) as csat_avg,
       (select coalesce(sum(u.usage_count), 0) from silver.feature_usage u where u.account_id = d.account_id
         and u.usage_date >= ref.as_of - 90) as usage_90d,
       (select e.reason_code from silver.churn_events e where e.account_id = d.account_id
         order by e.churn_date desc limit 1) as last_churn_reason
from gold.dim_account d
cross join (select gold.as_of_date() as as_of) ref
left join gold.dim_customer_persona p using (account_id)
left join gold.risk_scores r on r.account_id = d.account_id and r.scored_at = ref.as_of;
comment on view gold.account_360 is 'Visão 360 por conta: cadastro, estado atual, persona, risco e drivers, suporte, uso e último motivo de churn.';


-- Coortes de cadastro ---------------------------------------------------------------
create or replace view gold.kpi_cohort with (security_invoker = true) as
with first_churn as (
  select account_id, min(tenure_months_at_churn) as first_churn_months
  from gold.fct_churn_event group by account_id
)
select to_char(a.signup_date, 'YYYY"Q"Q') as signup_cohort,
       count(*) as accounts,
       count(*) filter (where ref.as_of - a.signup_date >= 92) as accounts_with_3m,
       count(*) filter (where ref.as_of - a.signup_date >= 183) as accounts_with_6m,
       round(100.0 * count(*) filter (where fc.first_churn_months < 3 and ref.as_of - a.signup_date >= 92)
             / nullif(count(*) filter (where ref.as_of - a.signup_date >= 92), 0), 1) as churn_3m_pct,
       round(100.0 * count(*) filter (where fc.first_churn_months < 6 and ref.as_of - a.signup_date >= 183)
             / nullif(count(*) filter (where ref.as_of - a.signup_date >= 183), 0), 1) as churn_6m_pct
from silver.accounts a
cross join (select gold.as_of_date() as as_of) ref
left join first_churn fc using (account_id)
group by 1;
comment on view gold.kpi_cohort is '% de contas da coorte com primeiro churn em 3 e 6 meses (só contas com tempo de observação suficiente).';


-- Refresh do gold (chamado pelo pipeline depois da qualidade) ---------------------------
create or replace function gold.refresh(p_run_id uuid default null) returns integer
language plpgsql set search_path = '' as $$
declare
  v_t0 timestamptz := clock_timestamp();
  v_scores integer;
begin
  refresh materialized view gold.fct_churn_event;
  refresh materialized view gold.fct_account_month;
  refresh materialized view gold.dim_account;
  refresh materialized view gold.dim_customer_persona;
  v_scores := gold.refresh_risk_scores();
  if p_run_id is not null then
    insert into ops.ingestion_steps (run_id, dataset, layer, rows_loaded, status, started_at, finished_at, duration_ms)
    values (p_run_id, 'all', 'gold', v_scores, 'success', v_t0, clock_timestamp(),
            (extract(epoch from clock_timestamp() - v_t0) * 1000)::integer);
  end if;
  return v_scores;
end $$;
comment on function gold.refresh(uuid) is 'Atualiza as materialized views do gold e o score de risco; registra a etapa gold do run.';


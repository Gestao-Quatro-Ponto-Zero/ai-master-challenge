-- Gold (1/3): data de referência, regras de base e fatos.
-- Regras (skills churn-data-scientist / churn-business-analyst):
--   churn = evento em silver.churn_events;
--   MRR vigente = assinatura ativa mais recente na data (fallback: a última iniciada antes);
--   conta "churnada" numa data = teve churn até a data e nenhuma assinatura iniciada depois dele.

create function gold.as_of_date() returns date
language sql stable set search_path = '' as $$
  select greatest(
    (select max(churn_date) from silver.churn_events),
    (select max(start_date) from silver.subscriptions),
    (select max(signup_date) from silver.accounts)
  )
$$;
comment on function gold.as_of_date() is 'Data de referência dos dados (último dia com evento). Hoje: 2024-12-31.';

create function gold.is_churned_on(p_account_id text, p_date date) returns boolean
language sql stable set search_path = '' as $$
  select exists (
    select 1
    from (select max(e.churn_date) as last_churn
            from silver.churn_events e
           where e.account_id = p_account_id and e.churn_date <= p_date) lc
    where lc.last_churn is not null
      and not exists (select 1 from silver.subscriptions s
                       where s.account_id = p_account_id
                         and s.start_date > lc.last_churn and s.start_date <= p_date)
  )
$$;
comment on function gold.is_churned_on(text, date) is
  'true se a conta churnou até a data e não iniciou nenhuma assinatura depois do último churn.';

create function gold.subscription_at(p_account_id text, p_date date)
returns table (subscription_id text, plan_tier text, billing_frequency text, seats integer,
               mrr_amount numeric, auto_renew_flag boolean)
language sql stable set search_path = '' as $$
  select s.subscription_id, s.plan_tier, s.billing_frequency, s.seats, s.mrr_amount, s.auto_renew_flag
  from silver.subscriptions s
  where s.account_id = p_account_id and s.start_date <= p_date
  order by (s.end_date is null or s.end_date >= p_date) desc, s.start_date desc, s.subscription_id desc
  limit 1
$$;
comment on function gold.subscription_at(text, date) is
  'Assinatura vigente da conta na data: a ativa mais recente; se nenhuma ativa, a última iniciada antes.';

-- Fato: eventos de churn enriquecidos ------------------------------------------------
create materialized view gold.fct_churn_event as
select e.churn_event_id,
       e.account_id,
       e.churn_date,
       date_trunc('month', e.churn_date)::date as churn_month,
       to_char(e.churn_date, 'YYYY"Q"Q') as churn_quarter,
       e.reason_code,
       e.refund_amount_usd,
       e.preceding_upgrade_flag,
       e.preceding_downgrade_flag,
       e.is_reactivation,
       s.plan_tier as plan_at_churn,
       s.billing_frequency as billing_at_churn,
       s.mrr_amount as mrr_at_churn,
       row_number() over (partition by e.account_id order by e.churn_date, e.churn_event_id) as nth_churn,
       round((e.churn_date - a.signup_date) / 30.44, 2) as tenure_months_at_churn,
       case
         when row_number() over (partition by e.account_id order by e.churn_date, e.churn_event_id) > 1
           then 'repetido'
         when (e.churn_date - a.signup_date) / 30.44 < 3 then 'primeiro_0_3m'
         else 'primeiro_3m_mais'
       end as churn_type
from silver.churn_events e
join silver.accounts a using (account_id)
left join lateral gold.subscription_at(e.account_id, e.churn_date) s on true;
create unique index fct_churn_event_pk on gold.fct_churn_event (churn_event_id);
comment on materialized view gold.fct_churn_event is 'Um evento de churn por linha, com MRR, plano e tempo de casa na data do churn.';
comment on column gold.fct_churn_event.churn_event_id is 'Evento de churn.';
comment on column gold.fct_churn_event.account_id is 'Conta.';
comment on column gold.fct_churn_event.churn_date is 'Data do churn.';
comment on column gold.fct_churn_event.churn_month is 'Mês do churn.';
comment on column gold.fct_churn_event.churn_quarter is 'Trimestre do churn (AAAAQn).';
comment on column gold.fct_churn_event.reason_code is 'Motivo declarado.';
comment on column gold.fct_churn_event.refund_amount_usd is 'Refund (US$).';
comment on column gold.fct_churn_event.preceding_upgrade_flag is 'Upgrade nos 90 dias anteriores.';
comment on column gold.fct_churn_event.preceding_downgrade_flag is 'Downgrade nos 90 dias anteriores.';
comment on column gold.fct_churn_event.is_reactivation is 'Flag de reativação da origem.';
comment on column gold.fct_churn_event.plan_at_churn is 'Plano vigente na data do churn.';
comment on column gold.fct_churn_event.billing_at_churn is 'Cobrança vigente na data do churn.';
comment on column gold.fct_churn_event.mrr_at_churn is 'MRR vigente na data do churn = MRR perdido (US$); nulo se não havia assinatura.';
comment on column gold.fct_churn_event.nth_churn is 'Ordem do churn na vida da conta (1 = primeiro).';
comment on column gold.fct_churn_event.tenure_months_at_churn is 'Meses desde o cadastro até o churn.';
comment on column gold.fct_churn_event.churn_type is 'primeiro_0_3m, primeiro_3m_mais ou repetido.';

-- Fato: conta × mês -----------------------------------------------------------------
create materialized view gold.fct_account_month as
with months as (
  select m::date as month_start, (m + interval '1 month - 1 day')::date as month_end
  from generate_series(
         (select date_trunc('month', min(signup_date)) from silver.accounts),
         date_trunc('month', gold.as_of_date()), interval '1 month') m
), am as (
  select a.account_id, m.month_start, m.month_end,
         ((extract(year from m.month_start) - extract(year from a.signup_date)) * 12
           + extract(month from m.month_start) - extract(month from a.signup_date))::integer as tenure_months
  from silver.accounts a
  join months m on m.month_start >= date_trunc('month', a.signup_date)
)
select am.account_id,
       am.month_start,
       am.month_end,
       to_char(am.month_start, 'YYYY"Q"Q') as quarter,
       am.tenure_months,
       case when am.tenure_months < 3 then '0-3m' when am.tenure_months < 6 then '3-6m'
            when am.tenure_months < 12 then '6-12m' else '12m+' end as tenure_bucket,
       (am.month_start > a.signup_date and not gold.is_churned_on(am.account_id, am.month_start - 1)) as active_at_start,
       not gold.is_churned_on(am.account_id, am.month_end) as active_at_end,
       (select count(*) from silver.churn_events e
         where e.account_id = am.account_id and e.churn_date < am.month_start)::integer as prior_churns,
       (select count(*) from silver.churn_events e
         where e.account_id = am.account_id and e.churn_date between am.month_start and am.month_end)::integer as churn_events,
       (select coalesce(sum(f.mrr_at_churn), 0) from gold.fct_churn_event f
         where f.account_id = am.account_id and f.churn_month = am.month_start) as mrr_churned,
       s.plan_tier, s.billing_frequency, s.seats, s.auto_renew_flag,
       case when gold.is_churned_on(am.account_id, am.month_end) then 0 else coalesce(s.mrr_amount, 0) end as mrr_end
from am
join silver.accounts a using (account_id)
left join lateral gold.subscription_at(am.account_id, am.month_end) s on true;
create unique index fct_account_month_pk on gold.fct_account_month (account_id, month_start);
comment on materialized view gold.fct_account_month is 'Uma linha por conta × mês desde o cadastro: estado, MRR vigente no fim do mês e churns do mês.';
comment on column gold.fct_account_month.account_id is 'Conta.';
comment on column gold.fct_account_month.month_start is 'Primeiro dia do mês.';
comment on column gold.fct_account_month.month_end is 'Último dia do mês.';
comment on column gold.fct_account_month.quarter is 'Trimestre (AAAAQn).';
comment on column gold.fct_account_month.tenure_months is 'Meses completos desde o cadastro.';
comment on column gold.fct_account_month.tenure_bucket is 'Faixa de tempo de casa: 0-3m, 3-6m, 6-12m, 12m+.';
comment on column gold.fct_account_month.active_at_start is 'Conta ativa no início do mês (cadastrada antes e não churnada).';
comment on column gold.fct_account_month.active_at_end is 'Conta ativa no fim do mês.';
comment on column gold.fct_account_month.prior_churns is 'Churns da conta antes do mês.';
comment on column gold.fct_account_month.churn_events is 'Eventos de churn no mês.';
comment on column gold.fct_account_month.mrr_churned is 'MRR perdido nos churns do mês (US$).';
comment on column gold.fct_account_month.plan_tier is 'Plano vigente no fim do mês.';
comment on column gold.fct_account_month.billing_frequency is 'Cobrança vigente no fim do mês.';
comment on column gold.fct_account_month.seats is 'Licenças vigentes no fim do mês.';
comment on column gold.fct_account_month.auto_renew_flag is 'Renovação automática vigente no fim do mês.';
comment on column gold.fct_account_month.mrr_end is 'MRR vigente no fim do mês (0 se churnada).';

-- Dimensão conta (estado atual na data de referência) --------------------------------
create view gold.dim_account with (security_invoker = true) as
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
comment on view gold.dim_account is 'Contas com atributos de cadastro e estado atual (plano, MRR vigente, ativa ou não) na data de referência.';
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

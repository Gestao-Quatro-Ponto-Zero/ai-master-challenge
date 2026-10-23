-- Gold (3/3): correção da receita, personas de cliente, score de risco, visão 360 e refresh.

-- Receita: churn de MRR por estado (conta ativa no início e churnada no fim do mês), sem dupla
-- contagem de quem churna e volta no mesmo mês. O MRR dos eventos fica como coluna separada.
drop view gold.kpi_revenue_monthly;
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
         count(*) filter (where active_at_start and not active_at_end) as lost_accounts,
         count(*) filter (where churn_events > 0) as accounts_with_churn_event,
         sum(churn_events) as churn_events,
         coalesce(sum(mrr_prev) filter (where active_at_start), 0) as mrr_start,
         sum(mrr_end) as mrr_end,
         coalesce(sum(mrr_end) filter (where not active_at_start), 0) as mrr_new_or_returning,
         coalesce(sum(mrr_prev) filter (where active_at_start and not active_at_end), 0) as mrr_lost,
         coalesce(sum(greatest(mrr_end - mrr_prev, 0)) filter (where active_at_start and active_at_end), 0) as mrr_expansion,
         coalesce(sum(greatest(mrr_prev - mrr_end, 0)) filter (where active_at_start and active_at_end), 0) as mrr_contraction,
         sum(mrr_churned) as mrr_in_churn_events
  from m
  group by month_start
)
select a.*,
       round(a.mrr_end * 12, 2) as arr_end,
       round(100.0 * a.lost_accounts / nullif(a.active_accounts_start, 0), 2) as logo_churn_pct,
       round(100.0 * a.accounts_with_churn_event / nullif(a.active_accounts_start, 0), 2) as churn_event_rate_pct,
       round(100.0 * (a.mrr_lost + a.mrr_contraction) / nullif(a.mrr_start, 0), 2) as gross_mrr_churn_pct,
       round(100.0 * (a.mrr_start - a.mrr_lost - a.mrr_contraction) / nullif(a.mrr_start, 0), 2) as grr_pct,
       round(100.0 * (a.mrr_start + a.mrr_expansion - a.mrr_lost - a.mrr_contraction) / nullif(a.mrr_start, 0), 2) as nrr_pct,
       round(a.mrr_end / nullif(a.active_accounts_end, 0), 2) as arpa
from agg a;
comment on view gold.kpi_revenue_monthly is
  'KPIs mensais: logos e MRR por estado (ativa no início × no fim do mês), GRR/NRR, ARPA, e taxa de eventos de churn. Ressalva: churn e assinaturas são desacoplados na origem (87% dos churns têm nova assinatura depois, mediana 16 dias) — KPIs de receita são aproximados.';

-- Personas de cliente (skill churn-business-analyst §3.2, ajustada aos dados) -----------
-- Reincidente = 2+ churns: churnar uma vez e voltar acontece em 87% dos eventos, não distingue.
create view gold.dim_customer_persona with (security_invoker = true) as
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
comment on view gold.dim_customer_persona is
  'Persona de cliente das contas ativas, por regra explícita com precedência (reincidente → em retração → recém-chegado → em expansão → âncora Enterprise → grande sem compromisso → Pro anual → pequeno Basic).';

create view gold.persona_catalog with (security_invoker = true) as
select * from (values
  ('reincidente', 'Reincidente', 'Já churnou 2+ vezes e voltou', 'Ciclo sai-volta: custo de reaquisição e receita instável', 'Plano de sucesso antes de aceitar a volta; dono de conta nomeado'),
  ('em_retracao', 'Em retração', 'Downgrade nos últimos 90 dias ou renovação automática desligada', 'Sinal de saída já declarado no contrato', 'Contato do CS em 7 dias com revisão de valor e plano'),
  ('recem_chegado', 'Recém-chegado / trial', 'Menos de 3 meses de casa ou em trial', 'Fase de maior risco: 46,5 churns por 100 contas-mês em 2024Q4', 'Onboarding guiado nos primeiros 90 dias com marcos de ativação'),
  ('em_expansao', 'Em expansão', 'Upgrade nos últimos 90 dias', 'Expectativa alta: se o valor não vier, a queda é rápida', 'Check-in de valor 30 dias após o upgrade'),
  ('ancora_enterprise', 'Âncora Enterprise', 'Enterprise com cobrança anual', 'Maior MRR por conta; Enterprise é 77% do MRR perdido', 'QBR trimestral e plano de renovação 90 dias antes'),
  ('grande_sem_compromisso', 'Grande sem compromisso', 'Enterprise ou Pro com cobrança mensal', 'Receita alta que pode sair em qualquer mês', 'Oferta de migração para anual com contrapartida de sucesso'),
  ('pro_anual', 'Pro anual', 'Pro com cobrança anual', 'Base estável de médio porte', 'Acompanhamento padrão; atenção à renovação'),
  ('pequeno_basic', 'Pequeno (Basic)', 'Plano Basic', 'Volume de logos, pouco MRR', 'Jornada digital (low-touch) e conteúdo de ativação')
) as t(persona, label, rule, why_it_matters, recommended_play);
comment on view gold.persona_catalog is 'Ficha de cada persona de cliente: regra, por que importa e jogada recomendada.';

-- Score de risco ---------------------------------------------------------------------
create table gold.risk_scores (
  account_id         text not null references silver.accounts (account_id),
  scored_at          date not null,
  model_version      text not null,
  persona            text,
  tenure_bucket_next text not null,
  prior_churns       integer not null,
  monthly_rate       numeric(8, 5) not null,
  probability_90d    numeric(6, 4) not null,
  mrr                numeric(12, 2) not null,
  mrr_at_risk_90d    numeric(12, 2) not null,
  driver_1           text,
  driver_2           text,
  driver_3           text,
  suggested_action   text,
  primary key (account_id, scored_at, model_version)
);
alter table gold.risk_scores enable row level security;
comment on table  gold.risk_scores is 'Risco de churn em 90 dias por conta ativa: taxa empírica do último trimestre por faixa de tempo de casa × churn anterior (modelo do diagnóstico H8, em SQL).';
comment on column gold.risk_scores.account_id is 'Conta.';
comment on column gold.risk_scores.scored_at is 'Data de referência do score.';
comment on column gold.risk_scores.model_version is 'Versão do modelo.';
comment on column gold.risk_scores.persona is 'Persona de cliente na data.';
comment on column gold.risk_scores.tenure_bucket_next is 'Faixa de tempo de casa no próximo mês.';
comment on column gold.risk_scores.prior_churns is 'Churns anteriores da conta.';
comment on column gold.risk_scores.monthly_rate is 'Taxa mensal esperada de churn (eventos por conta-mês).';
comment on column gold.risk_scores.probability_90d is 'Probabilidade de churn em 90 dias = 1 − exp(−3 × taxa mensal).';
comment on column gold.risk_scores.mrr is 'MRR vigente (US$).';
comment on column gold.risk_scores.mrr_at_risk_90d is 'Probabilidade × MRR (US$).';
comment on column gold.risk_scores.driver_1 is 'Principal fator de risco (texto para o CS).';
comment on column gold.risk_scores.driver_2 is 'Segundo fator.';
comment on column gold.risk_scores.driver_3 is 'Terceiro fator.';
comment on column gold.risk_scores.suggested_action is 'Jogada recomendada (da persona).';

create function gold.refresh_risk_scores() returns integer
language plpgsql set search_path = '' as $$
declare
  v_asof date := gold.as_of_date();
  v_q text := to_char(gold.as_of_date(), 'YYYY"Q"Q');
  v_version text := 'hazard-v1-' || to_char(gold.as_of_date(), 'YYYY"Q"Q');
  v_mrr_p90 numeric;
  v_rows integer;
begin
  select percentile_cont(0.9) within group (order by current_mrr) into v_mrr_p90
  from gold.dim_account where is_active;

  delete from gold.risk_scores where scored_at = v_asof and model_version = v_version;

  with cells as (   -- taxa empírica do trimestre de referência por faixa × churn anterior
    select tenure_bucket, (prior_churns > 0) as has_prior,
           sum(churn_events)::numeric as ev, count(*)::numeric as exp
    from gold.fct_account_month where quarter = v_q group by 1, 2
  ), bucket as (
    select tenure_bucket, sum(ev) / sum(exp) as rate from cells group by 1
  ), rates as (     -- encolhe células pequenas para a taxa da faixa (k = 30 contas-mês)
    select c.tenure_bucket, c.has_prior, (c.ev + 30 * b.rate) / (c.exp + 30) as rate
    from cells c join bucket b using (tenure_bucket)
  ), acc as (
    select d.account_id, d.current_mrr, d.current_plan, d.current_billing, d.current_auto_renew,
           d.tenure_months, d.churn_count, p.persona, p.downgrade_90d,
           case when d.tenure_months + 1 < 3 then '0-3m' when d.tenure_months + 1 < 6 then '3-6m'
                when d.tenure_months + 1 < 12 then '6-12m' else '12m+' end as bucket_next
    from gold.dim_account d join gold.dim_customer_persona p using (account_id)
    where d.is_active
  ), scored as (
    select a.*, r.rate, 1 - exp(-3 * r.rate) as prob,
           array_remove(array[
             case when a.tenure_months < 6 then 'conta nova (' || floor(a.tenure_months) || ' meses de casa)' end,
             case when a.churn_count > 0 then 'já churnou ' || a.churn_count || 'x' end,
             case when a.current_mrr >= v_mrr_p90 then 'MRR no top 10% (US$ ' || round(a.current_mrr) || ')' end,
             case when not a.current_auto_renew then 'renovação automática desligada' end,
             case when a.downgrade_90d then 'downgrade nos últimos 90 dias' end,
             case when a.current_billing = 'monthly' and a.current_plan <> 'Basic' then 'plano ' || a.current_plan || ' mensal' end
           ], null) as drivers
    from acc a join rates r on r.tenure_bucket = a.bucket_next and r.has_prior = (a.churn_count > 0)
  )
  insert into gold.risk_scores
    (account_id, scored_at, model_version, persona, tenure_bucket_next, prior_churns, monthly_rate,
     probability_90d, mrr, mrr_at_risk_90d, driver_1, driver_2, driver_3, suggested_action)
  select s.account_id, v_asof, v_version, s.persona, s.bucket_next, s.churn_count, s.rate, s.prob,
         coalesce(s.current_mrr, 0), coalesce(s.current_mrr, 0) * s.prob,
         s.drivers[1], s.drivers[2], s.drivers[3], pc.recommended_play
  from scored s left join gold.persona_catalog pc using (persona);
  get diagnostics v_rows = row_count;
  return v_rows;
end $$;
comment on function gold.refresh_risk_scores() is 'Recalcula gold.risk_scores para a data de referência (substitui o score da mesma data e versão).';

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
  and r.scored_at = gold.as_of_date()
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
         and t.submitted_at >= gold.as_of_date() - 90) as tickets_90d,
       (select round(avg(t.satisfaction_score), 2) from silver.support_tickets t where t.account_id = d.account_id) as csat_avg,
       (select coalesce(sum(u.usage_count), 0) from silver.feature_usage u where u.account_id = d.account_id
         and u.usage_date >= gold.as_of_date() - 90) as usage_90d,
       (select e.reason_code from silver.churn_events e where e.account_id = d.account_id
         order by e.churn_date desc limit 1) as last_churn_reason
from gold.dim_account d
left join gold.dim_customer_persona p using (account_id)
left join gold.risk_scores r on r.account_id = d.account_id and r.scored_at = gold.as_of_date();
comment on view gold.account_360 is 'Visão 360 por conta: cadastro, estado atual, persona, risco e drivers, suporte, uso e último motivo de churn.';

-- Refresh do gold (chamado pelo pipeline depois da qualidade) ---------------------------
create function gold.refresh(p_run_id uuid default null) returns integer
language plpgsql set search_path = '' as $$
declare
  v_t0 timestamptz := clock_timestamp();
  v_scores integer;
begin
  refresh materialized view gold.fct_churn_event;
  refresh materialized view gold.fct_account_month;
  v_scores := gold.refresh_risk_scores();
  if p_run_id is not null then
    insert into ops.ingestion_steps (run_id, dataset, layer, rows_loaded, status, started_at, finished_at, duration_ms)
    values (p_run_id, 'all', 'gold', v_scores, 'success', v_t0, clock_timestamp(),
            (extract(epoch from clock_timestamp() - v_t0) * 1000)::integer);
  end if;
  return v_scores;
end $$;
comment on function gold.refresh(uuid) is 'Atualiza as materialized views do gold e o score de risco; registra a etapa gold do run.';

revoke execute on function gold.refresh(uuid) from public, anon, authenticated;
revoke execute on function gold.refresh_risk_scores() from public, anon, authenticated;

select gold.refresh_risk_scores();

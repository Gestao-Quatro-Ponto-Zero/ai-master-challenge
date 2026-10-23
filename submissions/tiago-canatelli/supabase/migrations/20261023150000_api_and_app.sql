-- Camada api (só leitura, consumida pela API Python, pelo painel e pelo MCP) e app (prompts e perfis).

create schema if not exists api;
comment on schema api is 'Interface de leitura do lake: views e funções usadas por painel, assistente e MCP.';
revoke all on schema api from public, anon, authenticated;

create view api.kpi_overview with (security_invoker = true) as
select (select count(*) from gold.dim_account where is_active) as active_accounts,
       (select sum(current_mrr) from gold.dim_account where is_active) as active_mrr,
       (select sum(mrr_at_risk_90d) from gold.risk_scores where scored_at = gold.as_of_date()) as mrr_at_risk_90d,
       (select count(*) from gold.fct_churn_event where churn_quarter = to_char(gold.as_of_date(), 'YYYY"Q"Q')) as churn_events_last_quarter,
       (select count(*) from gold.fct_churn_event where churn_quarter = '2023Q4') as churn_events_2023q4,
       (select churn_per_100_account_months from gold.kpi_tenure_hazard where quarter = '2024Q4' and tenure_bucket = '0-3m') as hazard_new_accounts,
       (select churn_per_100_account_months from gold.kpi_tenure_hazard where quarter = '2024Q4' and tenure_bucket = '12m+') as hazard_tenured_accounts,
       (select churn_6m_pct from gold.kpi_cohort where signup_cohort = '2023Q2') as churn_6m_cohort_2023q2,
       (select churn_6m_pct from gold.kpi_cohort where signup_cohort = '2024Q2') as churn_6m_cohort_2024q2,
       (select round(avg(satisfaction_score), 2) from silver.support_tickets) as csat_avg,
       (select round(100.0 * count(satisfaction_score) / count(*), 1) from silver.support_tickets) as csat_response_pct,
       (select round(100.0 * sum(without_ticket_90d) / sum(churn_events), 1) from gold.kpi_silent_churn) as silent_churn_pct,
       (select round(100.0 * sum(mrr_at_churn) filter (where plan_at_churn = 'Enterprise') / sum(mrr_at_churn), 1) from gold.fct_churn_event) as enterprise_pct_mrr_lost,
       (select top10pct_share_pct from gold.kpi_loss_concentration where period = 'total') as top10_pct_mrr_lost,
       gold.as_of_date() as as_of_date;

create view api.revenue_monthly with (security_invoker = true) as select * from gold.kpi_revenue_monthly;
create view api.tenure_hazard with (security_invoker = true) as select * from gold.kpi_tenure_hazard;
create view api.cohort with (security_invoker = true) as select * from gold.kpi_cohort;
create view api.churn_type with (security_invoker = true) as select * from gold.kpi_churn_type;
create view api.churn_by_segment with (security_invoker = true) as select * from gold.kpi_churn_by_segment;
create view api.support_health with (security_invoker = true) as select * from gold.kpi_support_health;
create view api.silent_churn with (security_invoker = true) as select * from gold.kpi_silent_churn;
create view api.reactivation with (security_invoker = true) as select * from gold.kpi_reactivation;
create view api.loss_concentration with (security_invoker = true) as select * from gold.kpi_loss_concentration;
create view api.feature_health with (security_invoker = true) as select * from gold.kpi_feature_health;
create view api.persona_summary with (security_invoker = true) as select * from gold.kpi_persona_summary;
create view api.persona_catalog with (security_invoker = true) as select * from gold.persona_catalog;
create view api.churn_reason_vs_behavior with (security_invoker = true) as select * from gold.churn_reason_vs_behavior;
create view api.usage_quarterly with (security_invoker = true) as
select quarter, sum(usage_events) as usage_events, sum(accounts_with_usage) as accounts_with_usage,
       round(sum(usage_events)::numeric / nullif(sum(accounts_with_usage), 0), 1) as usage_per_account
from gold.kpi_usage_segment_monthly group by quarter;
create view api.account_360 with (security_invoker = true) as select * from gold.account_360;
create view api.risk_queue with (security_invoker = true) as
select r.account_id, d.account_name, d.industry, d.current_plan, d.current_billing, r.persona,
       r.mrr, r.probability_90d, r.mrr_at_risk_90d, r.driver_1, r.driver_2, r.driver_3,
       r.suggested_action, d.tenure_months, d.churn_count
from gold.risk_scores r join gold.dim_account d using (account_id)
where r.scored_at = gold.as_of_date();
create view api.ingestion_runs with (security_invoker = true) as select * from ops.ingestion_runs;
create view api.ingestion_steps with (security_invoker = true) as select * from ops.ingestion_steps;
create view api.dq_results with (security_invoker = true) as select * from ops.dq_results;
create view api.catalog_tables with (security_invoker = true) as select * from ops.catalog_tables;
create view api.catalog_columns with (security_invoker = true) as select * from ops.catalog_columns;

comment on view api.kpi_overview is 'Números do painel geral (CEO) numa linha.';
comment on view api.risk_queue is 'Fila do CS: contas ativas ordenadas por MRR em risco em 90 dias.';
comment on view api.usage_quarterly is 'Uso total e por conta por trimestre (é plano).';

-- Consulta livre só-leitura para a IA (tool query_analytics) --------------------------
create function api.run_readonly_query(p_sql text) returns jsonb
language plpgsql set search_path = '' as $$
declare
  v_sql text := btrim(p_sql);
  v_result jsonb;
begin
  v_sql := regexp_replace(v_sql, ';\s*$', '');
  if v_sql ~ ';' then
    raise exception 'apenas uma instrução é permitida';
  end if;
  if v_sql !~* '^\s*(select|with)\s' then
    raise exception 'apenas SELECT/WITH é permitido';
  end if;
  if v_sql ~* '\m(insert|update|delete|drop|alter|create|grant|revoke|truncate|copy|call|do|execute|set|reset|lock|vacuum|refresh|comment)\M' then
    raise exception 'comando não permitido';
  end if;
  if v_sql ~* '\m(bronze|silver|gold|ops|app|public|auth|storage|pg_catalog|information_schema|extensions|vault)\s*\.' then
    raise exception 'só objetos do schema api podem ser consultados';
  end if;
  set local statement_timeout = '5s';
  set local search_path = api;
  execute format('select coalesce(jsonb_agg(t), ''[]''::jsonb) from (select * from (%s) q limit 500) t', v_sql)
    into v_result;
  return v_result;
end $$;
comment on function api.run_readonly_query(text) is
  'Executa um único SELECT sobre o schema api (timeout 5 s, máx. 500 linhas). O chamador abre a transação como READ ONLY.';
revoke execute on function api.run_readonly_query(text) from public, anon, authenticated;

-- App: prompts e perfis de análise ---------------------------------------------------
create table app.prompt_templates (
  slug            text primary key,
  title           text not null,
  profile_slug    text not null,
  description     text,
  body            text not null,
  default_body    text not null,
  variables       jsonb not null default '[]'::jsonb,
  version         integer not null default 1,
  updated_at      timestamptz not null default now()
);
comment on table app.prompt_templates is 'Prompts prontos do assistente (editáveis; default_body permite restaurar o padrão).';

create table app.analysis_profiles (
  slug          text primary key,
  name          text not null,
  question      text not null,
  instructions  text not null,
  default_instructions text not null,
  version       integer not null default 1,
  updated_at    timestamptz not null default now()
);
comment on table app.analysis_profiles is 'Perfis de análise por área (lente do assistente); editáveis com restauração do padrão.';

create table app.ai_runs (
  id           bigint generated always as identity primary key,
  created_at   timestamptz not null default now(),
  profile_slug text,
  prompt_slug  text,
  question     text not null,
  answer       text,
  model        text,
  tool_calls   jsonb,
  input_tokens integer,
  output_tokens integer,
  latency_ms   integer,
  error        text
);
comment on table app.ai_runs is 'Auditoria de cada resposta do assistente (pergunta, tools, resposta, tokens).';

alter table app.prompt_templates enable row level security;
alter table app.analysis_profiles enable row level security;
alter table app.ai_runs enable row level security;

create view api.prompts with (security_invoker = true) as
select slug, title, profile_slug, description, body, variables, version, updated_at,
       body <> default_body as is_customized from app.prompt_templates;
create view api.profiles with (security_invoker = true) as
select slug, name, question, instructions, version, updated_at,
       instructions <> default_instructions as is_customized from app.analysis_profiles;

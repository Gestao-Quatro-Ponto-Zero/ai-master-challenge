-- App Vercel (PRD v1.1, ADR-0014): limites de uso, métricas por triagem e resultados da análise para leitura.
-- Aplicada via MCP supabase-g4 (apply_migration "app"). Tudo com RLS ligado e sem policy: só o servidor (service role) lê e grava.

-- 1. Eventos de uso das rotas /api/* do app (limites e monitoramento, PRD §8 e §8.1)
create table if not exists public.usage_events (
  id             bigint generated always as identity primary key,
  ts             timestamptz not null default now(),
  route          text not null,                         -- ex.: /api/triage
  action         text not null check (action in ('triage_free_text', 'triage_holdout', 'hitl', 'inbox', 'demo_reset', 'heartbeat')),
  ip_hash        text not null,                         -- SHA-256(IP + IP_HASH_SALT); o IP nunca é gravado
  ua             text,                                  -- user agent resumido
  outcome        text not null check (outcome in ('ok', 'rate_limited', 'client_error', 'server_error', 'offline', 'disabled')),
  status_code    smallint,
  latency_ms     integer,
  triage_run_id  bigint references public.triage_runs (id) on delete set null,
  flag           text                                   -- ex.: 'prompt_injection'
);
create index if not exists usage_events_action_ip_ts_idx on public.usage_events (action, ip_hash, ts desc);
create index if not exists usage_events_ts_idx on public.usage_events (ts desc);
create index if not exists usage_events_triage_idx on public.usage_events (triage_run_id);
alter table public.usage_events enable row level security;

-- 2. Alertas de uso na caixa (Slack simulado)
alter table public.notifications drop constraint if exists notifications_kind_check;
alter table public.notifications add constraint notifications_kind_check
  check (kind in ('level3_alert', 'heartbeat_failure', 'usage_alert'));
alter table public.notifications add column if not exists assigned_to text;
alter table public.notifications add column if not exists assigned_at timestamptz;

-- 3. Custo e tempo por triagem (gravados pelo fluxo 1 do n8n)
alter table public.triage_runs add column if not exists tokens_in integer;
alter table public.triage_runs add column if not exists tokens_out integer;
alter table public.triage_runs add column if not exists cost_usd numeric(10, 6);
alter table public.triage_runs add column if not exists latency_ms integer;
alter table public.triage_runs add column if not exists step_ms jsonb;   -- { embedding, rag, solucoes, llm, ... } em ms

-- 4. Resultados da análise (calculados pelos scripts de solution/analysis/, carregados por scripts/load_analysis.py)
create table if not exists public.analysis_diagnostic_cuts (
  dimension              text not null,
  value                  text not null,
  n                      integer not null,
  pct_open               real,
  pct_pending            real,
  n_closed               integer,
  csat_mean              real,
  csat_ci_low            real,
  csat_ci_high           real,
  hours_median_coherent  real,
  pct_incoherent         real,
  primary key (dimension, value)
);
create table if not exists public.analysis_metrics (
  key          text primary key,          -- nome do arquivo de saída sem extensão (ex.: app_summary, rag_only_policy)
  payload      jsonb not null,
  source_file  text not null,
  loaded_at    timestamptz not null default now()
);
create table if not exists public.analysis_examples (
  ds2_id  integer primary key references public.ds2_tickets (id),
  kind    text not null check (kind in ('sensitive_hr', 'sensitive_admin')),
  note    text
);
alter table public.analysis_diagnostic_cuts enable row level security;
alter table public.analysis_metrics enable row level security;
alter table public.analysis_examples enable row level security;

-- 5. Views de leitura do app
create or replace view public.v_ds1_status with (security_invoker = true) as
  select ticket_status as status, count(*)::int as n,
         round(count(*)::numeric / sum(count(*)) over (), 4) as share
  from public.ds1_tickets group by ticket_status;

create or replace view public.v_ops_summary with (security_invoker = true) as
  select
    count(*)::int                                                                  as triagens,
    count(*) filter (where level = 1 and status = 'auto_answered')::int            as automaticas,
    count(*) filter (where level = 2)::int                                         as revisao_humana,
    count(*) filter (where level = 3)::int                                         as somente_humano,
    count(*) filter (where t.ds2_id is not null)::int                              as holdout_total,
    count(*) filter (where t.ds2_id is not null and t.category = d.topic_group)::int as holdout_acertos,
    percentile_cont(0.5) within group (order by t.latency_ms)                      as latencia_p50_ms,
    percentile_cont(0.95) within group (order by t.latency_ms)                     as latencia_p95_ms,
    coalesce(sum(t.cost_usd), 0)                                                   as custo_usd_total,
    (select count(*) from public.hitl_queue where status = 'approved')::int        as hitl_aprovadas,
    (select count(*) from public.hitl_queue where status = 'edited')::int          as hitl_editadas,
    (select count(*) from public.hitl_queue where status = 'rejected')::int        as hitl_rejeitadas,
    (select count(*) from public.hitl_queue where status = 'pending')::int         as hitl_pendentes,
    (select avg(extract(epoch from (decided_at - created_at)))
       from public.hitl_queue where decided_at is not null)                        as hitl_tempo_medio_s,
    (select count(*) from public.validated_resolutions where active and source = 'playbook')::int as base_playbook,
    (select count(*) from public.validated_resolutions where active and source = 'hitl')::int     as base_aprendidas
  from public.triage_runs t
  left join public.ds2_tickets d on d.id = t.ds2_id
  where t.status <> 'error';

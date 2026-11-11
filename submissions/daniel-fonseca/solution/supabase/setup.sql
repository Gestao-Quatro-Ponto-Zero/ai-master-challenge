-- setup.sql — banco completo do case num projeto Supabase novo.
-- GERADO por scripts/setup_supabase.py --gerar-sql a partir de solution/supabase/migrations/ (não editar à mão).
-- Uso: cole no SQL Editor do Supabase e rode, ou deixe o scripts/setup_supabase.py aplicar.
-- 8 migrations, na ordem: 20261109000001_raw_datasets, 20261109000002_rag, 20261110000003_ops, 20261110000004_rest_wrappers, 20261110000005_app, 20261110000006_console_helpers, 20261110000007_usage_monitor, 20261110000008_tickets

-- ===================== 20261109000001_raw_datasets.sql =====================
-- Dados brutos dos dois datasets do Challenge 002, fiéis ao CSV original.
-- Nenhuma limpeza aqui: transformações ficam em views/consultas para manter rastreabilidade.

-- DS1 — Customer Support Ticket Dataset (sintético; ver context/data-findings.md)
create table if not exists public.ds1_tickets (
  ticket_id            integer primary key,
  customer_name        text,
  customer_email       text,
  customer_age         smallint,
  customer_gender      text,
  product_purchased    text,
  date_of_purchase     date,
  ticket_type          text not null,
  ticket_subject       text,
  ticket_description   text,
  ticket_status        text not null,
  resolution           text,
  ticket_priority      text not null,
  ticket_channel       text not null,
  first_response_at    timestamp,   -- coluna "First Response Time" (é timestamp, não duração)
  resolved_at          timestamp,   -- coluna "Time to Resolution" (é timestamp, não duração)
  csat                 smallint check (csat between 1 and 5)
);

comment on table public.ds1_tickets is
  'DS1 Kaggle suraj520/customer-support-ticket-dataset (CC0). 8.469 tickets. Sintético: variáveis independentes entre si.';

-- DS2 — IT Service Ticket Classification Dataset
create table if not exists public.ds2_tickets (
  id           integer primary key,          -- posição da linha no CSV original (0-based)
  document     text not null,
  topic_group  text not null,
  split        text not null check (split in ('train', 'test'))  -- holdout estratificado 80/20, seed 42
);

comment on table public.ds2_tickets is
  'DS2 Kaggle adisongoh/it-service-ticket-classification-dataset (CC0). 47.837 tickets reais, texto pré-processado, 8 categorias, sem resolução.';

create index if not exists ds1_tickets_dims_idx on public.ds1_tickets (ticket_status, ticket_channel, ticket_priority, ticket_type);
create index if not exists ds2_tickets_split_topic_idx on public.ds2_tickets (split, topic_group);

-- Segurança: RLS ligado e nenhuma policy para anon/authenticated.
-- O app lê por rotas de servidor (service role) ou por views específicas, definidas depois.
alter table public.ds1_tickets enable row level security;
alter table public.ds2_tickets enable row level security;

-- ===================== 20261109000002_rag.sql =====================
-- RAG por similaridade (ADR-0004 e ADR-0010): embeddings do DS2 + função de classificação por voto dos vizinhos.
-- Aplicada via MCP supabase-g4 (apply_migration "rag"). Os vetores são carregados por scripts/load_embeddings.py.

-- pgvector fica no schema "extensions" (recomendação do Supabase: nada de extensão no schema public).
create extension if not exists vector with schema extensions;

-- 512 dims de text-embedding-3-small (truncado + renormalizado = parâmetro "dimensions" da API),
-- em halfvec (16 bits): ~49 MB de vetores, cabe com folga nos 500 MB do plano free (ADR-0004).
create table if not exists public.ds2_embeddings (
  id         integer primary key references public.ds2_tickets (id) on delete cascade,
  embedding  extensions.halfvec(512) not null
);

comment on table public.ds2_embeddings is
  'Embeddings text-embedding-3-small (512 dims, normalizados) dos tickets do DS2. Memória de casos parecidos do RAG (ADR-0004/0010).';

-- Índice aproximado (HNSW) por cosseno. O loader recria este índice depois do COPY (mais rápido que indexar linha a linha).
create index if not exists ds2_embeddings_hnsw_idx
  on public.ds2_embeddings using hnsw (embedding extensions.halfvec_cosine_ops);

alter table public.ds2_embeddings enable row level security;

-- Classificação por voto ponderado dos vizinhos (ADR-0010):
--   - 50 vizinhos mais próximos, SÓ do split de treino (o teste fica fora para a avaliação ser honesta);
--   - peso de cada vizinho = similaridade^16 (similaridade negativa vira 0);
--   - confiança = fração ponderada dos votos da categoria vencedora;
--   - sensitive_share = fração dos votos em categorias sensíveis (HR Support, Administrative rights).
-- A política de 3 níveis (≥ 0,9 automático; sensível, ≥ 30% sensível ou < 0,5 só humano) é aplicada no n8n.
-- hnsw.iterative_scan: como o filtro de treino descarta ~20% dos vizinhos, a busca continua até achar 50.
create or replace function public.classify_ticket(query extensions.halfvec(512))
returns table (
  category         text,
  confidence       double precision,
  sensitive_share  double precision,
  votes            jsonb,
  similar_cases    jsonb
)
language sql
stable
set search_path = public, extensions, pg_temp
set hnsw.ef_search = 100
set hnsw.iterative_scan = strict_order
as $$
  with neighbors as (
    select e.id, t.topic_group, t.document, 1 - (e.embedding <=> query) as sim
    from public.ds2_embeddings e
    join public.ds2_tickets t on t.id = e.id
    where t.split = 'train'
    order by e.embedding <=> query
    limit 50
  ),
  weighted as (
    select topic_group, sum(power(greatest(sim, 0), 16)) as w
    from neighbors
    group by topic_group
  ),
  shares as (
    select topic_group, w / nullif(sum(w) over (), 0) as share
    from weighted
  )
  select
    (select s.topic_group from shares s order by s.share desc nulls last limit 1),
    (select max(s.share) from shares s),
    coalesce((select sum(s.share) from shares s
              where s.topic_group in ('HR Support', 'Administrative rights')), 0),
    (select jsonb_object_agg(s.topic_group, round(s.share::numeric, 4)) from shares s),
    (select jsonb_agg(jsonb_build_object(
                'id', n.id,
                'category', n.topic_group,
                'similarity', round(n.sim::numeric, 4),
                'snippet', left(n.document, 280)
              ) order by n.sim desc)
       from (select * from neighbors order by sim desc limit 5) n)
$$;

comment on function public.classify_ticket(extensions.halfvec) is
  'RAG (ADR-0010): voto dos 50 vizinhos de treino, peso sim^16. Retorna categoria, confiança, fração sensível, votos e os 5 casos mais parecidos.';

-- Só o backend (n8n via Postgres / service role) chama a função; anon e authenticated não.
revoke execute on function public.classify_ticket(extensions.halfvec) from public, anon, authenticated;
grant execute on function public.classify_ticket(extensions.halfvec) to service_role;

-- ===================== 20261110000003_ops.sql =====================
-- Tabelas operacionais dos fluxos n8n (docs/n8n-flows.md, ADR-0004/0007/0010/0012).
-- Aplicada via MCP supabase-g4 (apply_migration "ops"). RLS ligado sem policy: só backend (n8n via Postgres, app via service role).

-- Soluções validadas: playbook-semente por categoria + respostas aprovadas no HITL (ADR-0004)
create table if not exists public.validated_resolutions (
  id               bigint generated always as identity primary key,
  category         text not null,
  problem_text     text not null,                      -- ticket (ou descrição do playbook) que originou a solução
  resolution_text  text not null,                      -- texto aprovado por humano
  embedding        extensions.halfvec(512) not null,   -- embedding do problema (mesmo espaço do DS2)
  source           text not null check (source in ('playbook', 'hitl')),
  hitl_id          bigint,                             -- FK adicionada após hitl_queue
  approved_by      text,
  active           boolean not null default true,
  created_at       timestamptz not null default now()
);
create index if not exists validated_resolutions_hnsw_idx
  on public.validated_resolutions using hnsw (embedding extensions.halfvec_cosine_ops);
create index if not exists validated_resolutions_category_idx
  on public.validated_resolutions (category) where active;

-- Toda decisão da IA (trilha de auditoria; alimenta o console e o dashboard)
create table if not exists public.triage_runs (
  id               bigint generated always as identity primary key,
  created_at       timestamptz not null default now(),
  source           text not null check (source in ('console', 'holdout')),
  ds2_id           integer references public.ds2_tickets (id),   -- sorteado do holdout: permite conferir o rótulo real
  ticket_text      text not null,
  embedding        extensions.halfvec(512),
  category         text,
  confidence       real,
  sensitive_share  real,
  votes            jsonb,
  similar_cases    jsonb,
  blocked          boolean,                            -- termo da lista de bloqueio (ADR-0012)
  level            smallint check (level between 1 and 3),
  level_reason     text,
  status           text not null default 'received' check (status in
                     ('received', 'auto_answered', 'pending_review', 'awaiting_human',
                      'answered_after_review', 'rejected', 'error')),
  response_text    text,
  resolution_id    bigint references public.validated_resolutions (id),
  updated_at       timestamptz not null default now()
);
create index if not exists triage_runs_created_idx on public.triage_runs (created_at desc);
create index if not exists triage_runs_status_idx on public.triage_runs (status);
create index if not exists triage_runs_resolution_idx on public.triage_runs (resolution_id);
create index if not exists triage_runs_ds2_idx on public.triage_runs (ds2_id);

-- Fila de revisão humana (nível 2)
create table if not exists public.hitl_queue (
  id               bigint generated always as identity primary key,
  triage_run_id    bigint not null unique references public.triage_runs (id) on delete cascade,
  draft_text       text not null,
  checks           jsonb,                              -- o que o revisor deve conferir (saída do LLM)
  status           text not null default 'pending' check (status in ('pending', 'approved', 'edited', 'rejected')),
  final_text       text,
  final_category   text,
  reviewer         text,
  review_note      text,
  created_at       timestamptz not null default now(),
  decided_at       timestamptz
);
create index if not exists hitl_queue_status_idx on public.hitl_queue (status, created_at);

do $$ begin
  alter table public.validated_resolutions
    add constraint validated_resolutions_hitl_fk foreign key (hitl_id) references public.hitl_queue (id);
exception when duplicate_object then null; end $$;
create index if not exists validated_resolutions_hitl_idx on public.validated_resolutions (hitl_id);

-- Caixa de mensagens do painel (ADR-0007): o mesmo texto que iria para o Slack
create table if not exists public.notifications (
  id               bigint generated always as identity primary key,
  triage_run_id    bigint references public.triage_runs (id) on delete cascade,
  kind             text not null check (kind in ('level3_alert', 'heartbeat_failure')),
  channel_intended text not null default 'slack',
  title            text not null,
  body             text not null,
  payload          jsonb,
  delivered_slack  boolean not null default false,
  read_at          timestamptz,
  created_at       timestamptz not null default now()
);
create index if not exists notifications_unread_idx on public.notifications (created_at desc) where read_at is null;
create index if not exists notifications_triage_idx on public.notifications (triage_run_id);

-- Keep-alive (ADR-0006)
create table if not exists public.heartbeat (
  id      bigint generated always as identity primary key,
  ran_at  timestamptz not null default now(),
  source  text not null check (source in ('vercel-cron', 'n8n', 'n8n-fallback')),
  ok      boolean not null default true,
  detail  text
);
create index if not exists heartbeat_ran_idx on public.heartbeat (ran_at desc);

-- Soluções validadas mais parecidas dentro da categoria (nó "Buscar soluções validadas" do fluxo 1)
create or replace function public.match_resolutions(query extensions.halfvec(512), p_category text, k int default 3)
returns table (id bigint, resolution_text text, similarity double precision, source text)
language sql
stable
set search_path = public, extensions, pg_temp
as $$
  select r.id, r.resolution_text, 1 - (r.embedding <=> query), r.source
  from public.validated_resolutions r
  where r.active and r.category = p_category
  order by r.embedding <=> query
  limit k
$$;
revoke execute on function public.match_resolutions(extensions.halfvec, text, int) from public, anon, authenticated;
grant execute on function public.match_resolutions(extensions.halfvec, text, int) to service_role;

alter table public.validated_resolutions enable row level security;
alter table public.triage_runs          enable row level security;
alter table public.hitl_queue           enable row level security;
alter table public.notifications        enable row level security;
alter table public.heartbeat            enable row level security;

-- ===================== 20261110000004_rest_wrappers.sql =====================
-- Fluxos n8n com nós nativos do Supabase (ADR-0013): as funções do RAG são chamadas pela API REST
-- (POST /rest/v1/rpc/<função>) com a credencial Supabase do n8n.
-- O HTTP Request do n8n transforma uma lista JSON em vários itens e, se ela vier vazia, o fluxo para.
-- Este wrapper devolve sempre UM objeto { "resolutions": [...] }, mesmo sem nenhuma solução validada.
-- Aplicada via MCP supabase-g4 (apply_migration "rest_wrappers").

create or replace function public.match_resolutions_json(query extensions.halfvec(512), p_category text, k int default 3)
returns jsonb
language sql
stable
set search_path = public, extensions, pg_temp
as $$
  select jsonb_build_object(
    'resolutions',
    coalesce((select jsonb_agg(to_jsonb(r) order by r.similarity desc)
              from public.match_resolutions(query, p_category, k) r), '[]'::jsonb)
  )
$$;

comment on function public.match_resolutions_json(extensions.halfvec, text, int) is
  'Mesmo resultado de match_resolutions, embrulhado em { resolutions: [...] } para chamada via REST no n8n.';

revoke execute on function public.match_resolutions_json(extensions.halfvec, text, int) from public, anon, authenticated;
grant execute on function public.match_resolutions_json(extensions.halfvec, text, int) to service_role;

-- O playbook-semente foi revisado e validado pelo Daniel em 2026-11-10 (ADR-0004).
update public.validated_resolutions
set approved_by = 'Daniel (revisão do playbook, 2026-11-10)'
where source = 'playbook' and approved_by is null;

-- ===================== 20261110000005_app.sql =====================
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

-- ===================== 20261110000006_console_helpers.sql =====================
-- Funções de apoio ao Console (PRD v1.1 §4.4 e §4.5). Só service role executa.
-- Aplicada via MCP supabase-g4 (apply_migration "console_helpers").

-- Carrega a biblioteca do pgvector (registra hnsw.*) antes do CREATE FUNCTION com SET hnsw.*;
-- sem isso o Supabase recusa o SET ("permission denied to set parameter hnsw.ef_search").
select '[1,2]'::extensions.halfvec;

-- Sorteia um ticket do holdout (split de teste), opcionalmente de uma categoria real.
-- Devolve só id e texto: o rótulo real é revelado pelo app depois da triagem.
create or replace function public.random_holdout_ticket(p_category text default null)
returns table (id integer, document text)
language sql
volatile
set search_path = public, pg_temp
as $$
  select t.id, t.document
  from public.ds2_tickets t
  where t.split = 'test'
    and (p_category is null or t.topic_group = p_category)
    and array_length(regexp_split_to_array(t.document, '\s+'), 1) between 8 and 120
  order by random()
  limit 1
$$;

-- Efeito "aprendeu" (PRD §4.5): o ticket do holdout mais parecido com o de uma triagem já decidida,
-- excluindo o próprio ticket. Usa o embedding gravado em triage_runs.
create or replace function public.nearest_holdout_ticket(p_triage_run_id bigint)
returns table (id integer, document text, similarity double precision)
language sql
stable
set search_path = public, extensions, pg_temp
set hnsw.ef_search = 100
set hnsw.iterative_scan = strict_order
as $$
  select t.id, t.document, 1 - (e.embedding <=> r.embedding) as similarity
  from public.triage_runs r
  join public.ds2_embeddings e on true
  join public.ds2_tickets t on t.id = e.id and t.split = 'test'
  where r.id = p_triage_run_id
    and r.embedding is not null
    and (r.ds2_id is null or t.id <> r.ds2_id)
  order by e.embedding <=> r.embedding
  limit 1
$$;

revoke execute on function public.random_holdout_ticket(text) from public, anon, authenticated;
revoke execute on function public.nearest_holdout_ticket(bigint) from public, anon, authenticated;
grant execute on function public.random_holdout_ticket(text) to service_role;
grant execute on function public.nearest_holdout_ticket(bigint) to service_role;

-- Modo offline do Console (PRD §4.4): classifica um ticket do holdout direto no banco, sem n8n e sem LLM.
-- Aplicada como migration separada no MCP ("console_offline").
create or replace function public.classify_holdout_ticket(p_ds2_id integer)
returns table (category text, confidence double precision, sensitive_share double precision, votes jsonb, similar_cases jsonb)
language sql
stable
set search_path = public, extensions, pg_temp
as $$
  select c.* from public.ds2_embeddings e
  join public.ds2_tickets t on t.id = e.id and t.split = 'test'
  cross join lateral public.classify_ticket(e.embedding) c
  where e.id = p_ds2_id
$$;
revoke execute on function public.classify_holdout_ticket(integer) from public, anon, authenticated;
grant execute on function public.classify_holdout_ticket(integer) to service_role;

-- ===================== 20261110000007_usage_monitor.sql =====================
-- Monitor de uso (PRD v1.1 §8.1). Camada determinística chamada pelo fluxo n8n "Monitor de uso" a cada 15 min.
-- A função só calcula e devolve os sinais; quem grava o alerta na caixa é o n8n.
-- Regra de conduta: observar e alertar. Nenhuma ação contra abuso acontece aqui.
-- Aplicada via MCP supabase-g4 (apply_migration "usage_monitor").

create or replace function public.usage_monitor_check()
returns jsonb
language plpgsql
stable
set search_path = public, pg_temp
as $$
declare
  v_now      timestamptz := now();
  v_hour     timestamptz := now() - interval '1 hour';
  v_day      timestamptz := date_trunc('day', now() at time zone 'America/Sao_Paulo') at time zone 'America/Sao_Paulo';
  v_signals  jsonb := '[]'::jsonb;
  v_alerts   jsonb := '[]'::jsonb;
  v_sig      jsonb;
  v_last     timestamptz;
  v_dedup    interval;
  -- valores
  v_ip_tri   record;
  v_ip_hitl  record;
  v_rl       integer;
  v_global   integer;
  v_cost     numeric;
  v_err      integer;
  v_inj      integer;
  v_inj_from timestamptz;
  v_db_mb    numeric;
begin
  -- 1. Um IP com muitas triagens (> 10 em 1 h)
  select ip_hash, count(*) as n into v_ip_tri
  from usage_events
  where ts >= v_hour and action in ('triage_free_text', 'triage_holdout') and outcome in ('ok', 'offline')
  group by ip_hash order by n desc limit 1;

  -- 2. Respostas 429 (> 20 em 1 h)
  select count(*) into v_rl from usage_events where ts >= v_hour and outcome = 'rate_limited';

  -- 3. Volume global de triagens (> 100 em 1 h)
  select count(*) into v_global
  from usage_events
  where ts >= v_hour and action in ('triage_free_text', 'triage_holdout') and outcome in ('ok', 'offline');

  -- 4. Custo OpenAI do dia, horário de São Paulo (> US$ 0,50)
  select coalesce(sum(cost_usd), 0) into v_cost from triage_runs where created_at >= v_day;

  -- 5. Erros do servidor ou n8n fora do ar (> 5 em 1 h)
  select count(*) into v_err from usage_events where ts >= v_hour and outcome in ('server_error', 'offline');

  -- 6. Padrão de prompt injection: qualquer ocorrência desde o último alerta desse sinal (janela máxima de 1 h)
  select max(created_at) into v_last from notifications where kind = 'usage_alert' and payload->>'signal' = 'prompt_injection';
  v_inj_from := greatest(coalesce(v_last, v_hour), v_hour);
  select count(*) into v_inj from usage_events where ts > v_inj_from and flag is not null;

  -- 7. Ações em massa na fila por IP (> 30 em 1 h)
  select ip_hash, count(*) as n into v_ip_hitl
  from usage_events where ts >= v_hour and action = 'hitl'
  group by ip_hash order by n desc limit 1;

  -- 8. Banco perto do limite do plano free (> 400 MB de 500)
  v_db_mb := round(pg_database_size(current_database()) / 1024.0 / 1024.0, 1);

  v_signals := jsonb_build_array(
    jsonb_build_object('signal', 'ip_triage', 'label', 'Triagens de um único IP na última hora',
      'value', coalesce(v_ip_tri.n, 0), 'threshold', 10, 'breached', coalesce(v_ip_tri.n, 0) > 10,
      'ip', left(coalesce(v_ip_tri.ip_hash, ''), 8), 'dedup_min', 60),
    jsonb_build_object('signal', 'rate_limited', 'label', 'Respostas 429 na última hora',
      'value', v_rl, 'threshold', 20, 'breached', v_rl > 20, 'dedup_min', 60),
    jsonb_build_object('signal', 'global_volume', 'label', 'Triagens no app na última hora',
      'value', v_global, 'threshold', 100, 'breached', v_global > 100, 'dedup_min', 60),
    jsonb_build_object('signal', 'daily_cost', 'label', 'Custo OpenAI do dia (US$)',
      'value', round(v_cost, 4), 'threshold', 0.5, 'breached', v_cost > 0.5, 'dedup_min', 720),
    jsonb_build_object('signal', 'server_errors', 'label', 'Erros do servidor ou n8n fora do ar na última hora',
      'value', v_err, 'threshold', 5, 'breached', v_err > 5, 'dedup_min', 60),
    jsonb_build_object('signal', 'prompt_injection', 'label', 'Textos com padrão de prompt injection',
      'value', v_inj, 'threshold', 0, 'breached', v_inj > 0, 'dedup_min', 0),
    jsonb_build_object('signal', 'hitl_mass', 'label', 'Decisões na fila de um único IP na última hora',
      'value', coalesce(v_ip_hitl.n, 0), 'threshold', 30, 'breached', coalesce(v_ip_hitl.n, 0) > 30,
      'ip', left(coalesce(v_ip_hitl.ip_hash, ''), 8), 'dedup_min', 60),
    jsonb_build_object('signal', 'db_size', 'label', 'Tamanho do banco (MB de 500)',
      'value', v_db_mb, 'threshold', 400, 'breached', v_db_mb > 400, 'dedup_min', 1440)
  );

  -- Só vira alerta o sinal acima do limite que não foi alertado dentro da janela de repetição.
  for v_sig in select * from jsonb_array_elements(v_signals) loop
    continue when not (v_sig->>'breached')::boolean;
    v_dedup := make_interval(mins => (v_sig->>'dedup_min')::int);
    if v_dedup > interval '0' and exists (
      select 1 from notifications
      where kind = 'usage_alert' and payload->>'signal' = v_sig->>'signal' and created_at >= v_now - v_dedup
    ) then
      continue;
    end if;
    v_alerts := v_alerts || jsonb_build_object(
      'signal', v_sig->>'signal',
      'title', 'Uso do app: ' || lower(v_sig->>'label') || ' = ' || (v_sig->>'value') || ' (limite ' || (v_sig->>'threshold') || ')',
      'body', (v_sig->>'label') || ': ' || (v_sig->>'value') || ', acima do limite de ' || (v_sig->>'threshold') || '.'
        || case when coalesce(v_sig->>'ip', '') <> '' then ' IP (hash): ' || (v_sig->>'ip') || '….' else '' end
        || ' O monitor só registra e alerta; qualquer ação fica com o Daniel.',
      'payload', v_sig || jsonb_build_object('checked_at', v_now)
    );
  end loop;

  return jsonb_build_object(
    'checked_at', v_now,
    'signals', v_signals,
    'alerts', v_alerts,
    'alert_count', jsonb_array_length(v_alerts)
  );
end;
$$;

revoke execute on function public.usage_monitor_check() from public, anon, authenticated;
grant execute on function public.usage_monitor_check() to service_role;

-- ===================== 20261110000008_tickets.sql =====================
-- Tickets em formato de conversa (ADR-0015).
-- - client_token: o navegador do visitante busca só os próprios tickets (uuid aleatório, nunca o id sequencial).
-- - is_demo: tickets de demonstração, compartilhados entre os visitantes (reset_demo.py e /api/demo/reset).
-- - human_summary, alert_title, alert_body: nota interna em pt-BR e texto do Slack simulado, gravados pelo
--   fluxo 1 no caminho "Somente humano" (o fluxo deixou de gravar em notifications).
-- - human_reply: resposta escrita pelo atendente (Revisão humana = rascunho recusado; Somente humano).

alter table public.triage_runs
  add column if not exists client_token   uuid,
  add column if not exists is_demo        boolean not null default false,
  add column if not exists human_summary  jsonb,
  add column if not exists alert_title    text,
  add column if not exists alert_body     text,
  add column if not exists human_reply    text check (human_reply is null or char_length(human_reply) <= 4000),
  add column if not exists human_reply_at timestamptz;

create unique index if not exists triage_runs_client_token_idx on public.triage_runs (client_token) where client_token is not null;
create index if not exists triage_runs_demo_idx on public.triage_runs (created_at desc) where is_demo;


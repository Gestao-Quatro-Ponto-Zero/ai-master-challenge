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

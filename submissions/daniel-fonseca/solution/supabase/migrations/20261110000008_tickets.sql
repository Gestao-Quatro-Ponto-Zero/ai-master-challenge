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

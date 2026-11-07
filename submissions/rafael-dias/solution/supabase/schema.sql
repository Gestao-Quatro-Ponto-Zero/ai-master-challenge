-- Public CC0 demonstration snapshot only. No anonymous database access.
create table if not exists public.lead_opportunities (
 opportunity_id text primary key,
 payload jsonb not null,
 imported_at timestamptz not null default now()
);
alter table public.lead_opportunities enable row level security;
revoke all on public.lead_opportunities from anon, authenticated;
-- The application reads on the server with a secret service-role key.

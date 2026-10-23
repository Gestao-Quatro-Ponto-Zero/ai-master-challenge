-- Ingestão agendada sem custo: o pg_cron do Supabase chama a API no Render a cada 15 min
-- (pg_net), que verifica a versão do dataset no Kaggle MCP e roda o pipeline se houver mudança.
-- Cada chamada aparece em ops.ingestion_runs (trigger = 'cron') e no painel "Ingestão e catálogo".
-- O token fica no Supabase Vault (segredo 'ravenstack_cron_token'), gravado por scripts/setup_cron.py.

create extension if not exists pg_net;
create extension if not exists pg_cron;

create or replace function ops.trigger_cloud_ingest() returns bigint
language sql security definer set search_path = '' as $$
  select net.http_post(
    url := 'https://ravenstack-api.onrender.com/ingest/cron',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'X-Cron-Token', (select decrypted_secret from vault.decrypted_secrets where name = 'ravenstack_cron_token')
    ),
    body := '{}'::jsonb,
    timeout_milliseconds := 60000
  )
$$;
comment on function ops.trigger_cloud_ingest() is
  'Chama POST /ingest/cron da API no Render (agendado pelo pg_cron a cada 15 min).';
revoke execute on function ops.trigger_cloud_ingest() from public, anon, authenticated;

select cron.schedule('ravenstack-ingest-15min', '*/15 * * * *', $$select ops.trigger_cloud_ingest()$$);

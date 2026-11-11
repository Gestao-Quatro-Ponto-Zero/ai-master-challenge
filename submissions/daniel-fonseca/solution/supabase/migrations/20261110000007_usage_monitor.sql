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

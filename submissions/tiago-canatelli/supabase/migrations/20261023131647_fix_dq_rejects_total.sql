-- Corrige o total da checagem linhas_rejeitadas: linhas lidas pelo silver no run (antes somava só 2 tabelas).

-- Roda todas as checagens; devolve quantas checagens de severidade "error" falharam.
create or replace function ops.run_dq(p_run_id uuid) returns integer
language plpgsql set search_path = '' as $$
declare
  v_t0 timestamptz := clock_timestamp();
  v_errors integer;
begin
  delete from ops.dq_results where run_id = p_run_id;

  -- Integridade (error: bloqueia o gold)
  perform ops._dq(p_run_id, 'linhas_rejeitadas', 'silver._rejects', 'error',
    'Linhas do bronze que não entraram no silver nesta execução.',
    format('select reject_id::text as id from silver._rejects where run_id = %L', p_run_id),
    'select coalesce(sum(rows_read), 0)::integer from ops.ingestion_steps where layer = ''silver'' and run_id = '
      || quote_literal(p_run_id));
  perform ops._dq(p_run_id, 'assinatura_termina_antes_de_comecar', 'silver.subscriptions', 'error',
    'end_date anterior a start_date.',
    'select subscription_id as id from silver.subscriptions where end_date < start_date',
    'select count(*) from silver.subscriptions');
  perform ops._dq(p_run_id, 'mrr_negativo', 'silver.subscriptions', 'error',
    'MRR negativo.',
    'select subscription_id as id from silver.subscriptions where mrr_amount < 0',
    'select count(*) from silver.subscriptions');
  perform ops._dq(p_run_id, 'ticket_fecha_antes_de_abrir', 'silver.support_tickets', 'error',
    'closed_at anterior a submitted_at.',
    'select ticket_id as id from silver.support_tickets where closed_at < submitted_at',
    'select count(*) from silver.support_tickets');

  -- Consistência (warning: vira achado no relatório)
  perform ops._dq(p_run_id, 'churn_antes_do_cadastro', 'silver.churn_events', 'warning',
    'Churn com data anterior ao cadastro da conta.',
    'select e.churn_event_id as id from silver.churn_events e join silver.accounts a using (account_id) where e.churn_date < a.signup_date',
    'select count(*) from silver.churn_events');
  perform ops._dq(p_run_id, 'flag_churn_sem_evento', 'silver.accounts', 'warning',
    'accounts.churn_flag = true sem nenhum evento em churn_events.',
    'select a.account_id as id from silver.accounts a where a.churn_flag and not exists (select 1 from silver.churn_events e where e.account_id = a.account_id)',
    'select count(*) from silver.accounts');
  perform ops._dq(p_run_id, 'evento_churn_com_flag_falsa', 'silver.accounts', 'warning',
    'Conta com evento de churn mas accounts.churn_flag = false.',
    'select a.account_id as id from silver.accounts a where not a.churn_flag and exists (select 1 from silver.churn_events e where e.account_id = a.account_id)',
    'select count(*) from silver.accounts');
  perform ops._dq(p_run_id, 'churn_sem_fim_de_assinatura', 'silver.churn_events', 'warning',
    'Churn cuja data não coincide com o fim de nenhuma assinatura da conta (churn e assinaturas desacoplados).',
    'select e.churn_event_id as id from silver.churn_events e where not exists (select 1 from silver.subscriptions s where s.account_id = e.account_id and s.end_date = e.churn_date)',
    'select count(*) from silver.churn_events');
  perform ops._dq(p_run_id, 'uso_fora_da_assinatura', 'silver.feature_usage', 'warning',
    'Uso com data fora do período da assinatura.',
    'select usage_key as id from silver.feature_usage where not is_within_subscription',
    'select count(*) from silver.feature_usage');
  perform ops._dq(p_run_id, 'usage_id_colidindo', 'silver.feature_usage', 'warning',
    'Mesmo usage_id em eventos diferentes (mantidos com sufixo #n).',
    'select usage_key as id from silver.feature_usage where has_id_collision',
    'select count(*) from silver.feature_usage');
  perform ops._dq(p_run_id, 'arr_diferente_de_12x_mrr', 'silver.subscriptions', 'warning',
    'arr_amount diferente de 12 × mrr_amount.',
    'select subscription_id as id from silver.subscriptions where abs(arr_amount - 12 * mrr_amount) >= 1',
    'select count(*) from silver.subscriptions');
  perform ops._dq(p_run_id, 'contas_com_varias_assinaturas_abertas', 'silver.subscriptions', 'warning',
    'Contas com mais de uma assinatura sem end_date ao mesmo tempo (MRR vigente precisa de regra).',
    'select account_id as id from silver.subscriptions where end_date is null group by account_id having count(*) > 1',
    'select count(*) from silver.accounts');
  perform ops._dq(p_run_id, 'csat_escala_incompleta', 'silver.support_tickets', 'warning',
    'Notas de satisfação abaixo de 3 nunca aparecem (escala 1–5).',
    'select v::text as id from generate_series(1, 5) v where not exists (select 1 from silver.support_tickets t where t.satisfaction_score = v)',
    'select 5');

  -- Perfil (info)
  perform ops._dq(p_run_id, 'csat_sem_resposta', 'silver.support_tickets', 'info',
    'Tickets sem nota de satisfação (cliente não respondeu).',
    'select ticket_id as id from silver.support_tickets where satisfaction_score is null',
    'select count(*) from silver.support_tickets');
  perform ops._dq(p_run_id, 'assinatura_sem_uso', 'silver.subscriptions', 'info',
    'Assinaturas sem nenhum registro de uso.',
    'select s.subscription_id as id from silver.subscriptions s where not exists (select 1 from silver.feature_usage u where u.subscription_id = s.subscription_id)',
    'select count(*) from silver.subscriptions');
  perform ops._dq(p_run_id, 'feedback_pouco_variado', 'silver.churn_events', 'info',
    'Textos distintos de feedback_text (pouca variedade = pouca informação).',
    'select distinct feedback_text as id from silver.churn_events where feedback_text is not null',
    'select count(*) from silver.churn_events where feedback_text is not null');

  select count(*) into v_errors from ops.dq_results
   where run_id = p_run_id and severity = 'error' and status = 'fail';

  insert into ops.ingestion_steps (run_id, dataset, layer, rows_read, rows_loaded, rows_rejected,
                                   status, started_at, finished_at, duration_ms, error)
  select p_run_id, 'all', 'dq', count(*), count(*) filter (where status = 'pass'),
         count(*) filter (where status = 'fail'),
         case when v_errors > 0 then 'failed' else 'success' end, v_t0, clock_timestamp(),
         (extract(epoch from clock_timestamp() - v_t0) * 1000)::integer,
         case when v_errors > 0 then v_errors || ' checagem(ns) de erro falharam' end
  from ops.dq_results where run_id = p_run_id;

  return v_errors;
end $$;


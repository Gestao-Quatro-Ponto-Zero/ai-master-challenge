-- Qualidade de dados e catálogo. Lógica no banco: o pipeline só chama as funções.

-- Registra uma checagem a partir de uma consulta que devolve as linhas que falham (coluna "id").
create function ops._dq(
  p_run_id uuid, p_check text, p_table text, p_severity text, p_details text,
  p_failing_sql text, p_total_sql text
) returns void
language plpgsql set search_path = '' as $$
declare
  v_fail integer;
  v_total integer;
  v_sample jsonb;
begin
  execute format('select count(*), (select jsonb_agg(x.id) from (select id from (%s) f limit 5) x) from (%s) q',
                 p_failing_sql, p_failing_sql)
    into v_fail, v_sample;
  execute p_total_sql into v_total;
  insert into ops.dq_results
    (run_id, check_name, table_name, severity, status, failing_rows, total_rows, details, sample)
  values
    (p_run_id, p_check, p_table, p_severity, case when v_fail = 0 then 'pass' else 'fail' end,
     v_fail, v_total, p_details, v_sample);
end $$;

-- Roda todas as checagens; devolve quantas checagens de severidade "error" falharam.
create function ops.run_dq(p_run_id uuid) returns integer
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
    'select (select count(*) from bronze.accounts) + (select count(*) from bronze.subscriptions)');
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

comment on function ops.run_dq(uuid) is
  'Roda as checagens de qualidade (error/warning/info) e grava em ops.dq_results; devolve o número de checagens "error" que falharam.';

-- Catálogo: tabelas e colunas de bronze/silver/gold/ops/app, com descrições e estatísticas.
create function ops.refresh_catalog(p_run_id uuid default null) returns integer
language plpgsql set search_path = '' as $$
declare
  t record;
  c record;
  v_t0 timestamptz := clock_timestamp();
  v_rows bigint;
  v_nulls bigint;
  v_distinct bigint;
  v_tables integer := 0;
begin
  delete from ops.catalog_tables;

  for t in
    select n.nspname as schema_name, k.relname as table_name, obj_description(k.oid, 'pg_class') as description
    from pg_class k join pg_namespace n on n.oid = k.relnamespace
    where n.nspname in ('bronze', 'silver', 'gold', 'ops', 'app')
      and k.relkind in ('r', 'v', 'm')
  loop
    execute format('select count(*) from %I.%I', t.schema_name, t.table_name) into v_rows;
    insert into ops.catalog_tables (schema_name, table_name, layer, description, row_count, column_count)
    values (t.schema_name, t.table_name, t.schema_name, t.description, v_rows, 0);
    v_tables := v_tables + 1;

    for c in
      select a.attname as column_name, a.attnum as ordinal,
             format_type(a.atttypid, a.atttypmod) as data_type,
             col_description(a.attrelid, a.attnum) as description,
             exists (select 1 from pg_index i where i.indrelid = a.attrelid and i.indisprimary
                     and a.attnum = any (i.indkey)) as is_key
      from pg_attribute a
      where a.attrelid = format('%I.%I', t.schema_name, t.table_name)::regclass
        and a.attnum > 0 and not a.attisdropped
      order by a.attnum
    loop
      v_nulls := null; v_distinct := null;
      if t.schema_name in ('silver', 'gold') and v_rows > 0 and c.data_type not in ('jsonb', 'json') then
        execute format('select count(*) filter (where %1$I is null), count(distinct %1$I) from %2$I.%3$I',
                       c.column_name, t.schema_name, t.table_name)
          into v_nulls, v_distinct;
      end if;
      insert into ops.catalog_columns
        (schema_name, table_name, column_name, ordinal, data_type, description, is_key, is_pii,
         null_pct, distinct_count)
      values
        (t.schema_name, t.table_name, c.column_name, c.ordinal, c.data_type, c.description, c.is_key,
         c.column_name in ('account_name'),
         case when v_nulls is not null then round(100.0 * v_nulls / v_rows, 2) end, v_distinct);
    end loop;
  end loop;

  update ops.catalog_tables ct
     set column_count = (select count(*) from ops.catalog_columns cc
                          where cc.schema_name = ct.schema_name and cc.table_name = ct.table_name);

  if p_run_id is not null then
    insert into ops.ingestion_steps (run_id, dataset, layer, rows_loaded, status, started_at,
                                     finished_at, duration_ms)
    values (p_run_id, 'all', 'catalog', v_tables, 'success', v_t0, clock_timestamp(),
            (extract(epoch from clock_timestamp() - v_t0) * 1000)::integer);
  end if;
  return v_tables;
end $$;

comment on function ops.refresh_catalog(uuid) is
  'Reconstrói o catálogo (tabelas, colunas, descrições, % nulos e distintos em silver/gold).';

revoke execute on function ops._dq(uuid, text, text, text, text, text, text) from public, anon, authenticated;
revoke execute on function ops.run_dq(uuid) from public, anon, authenticated;
revoke execute on function ops.refresh_catalog(uuid) from public, anon, authenticated;
revoke execute on function silver.refresh(uuid) from public, anon, authenticated;
revoke execute on function silver._log_step(uuid, text, text, integer, integer, integer, timestamptz) from public, anon, authenticated;

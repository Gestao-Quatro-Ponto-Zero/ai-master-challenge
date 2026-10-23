-- Silver: dados tipados, deduplicados e com chaves validadas.
-- Cada refresh reconstrói o silver a partir do arquivo mais recente de cada dataset no bronze
-- (o Kaggle entrega snapshots completos). Linhas inválidas vão para silver._rejects, nunca somem.

-- Conversões seguras: devolvem nulo em vez de quebrar a carga.
create function silver.try_date(v text) returns date
language plpgsql immutable parallel safe set search_path = '' as $$
begin
  return nullif(btrim(v), '')::date;
exception when others then
  return null;
end $$;

create function silver.try_timestamptz(v text) returns timestamptz
language plpgsql immutable parallel safe set search_path = '' as $$
begin
  return (nullif(btrim(v), '')::timestamp) at time zone 'UTC';
exception when others then
  return null;
end $$;

create function silver.try_numeric(v text) returns numeric
language plpgsql immutable parallel safe set search_path = '' as $$
begin
  return nullif(btrim(v), '')::numeric;
exception when others then
  return null;
end $$;

create function silver.try_int(v text) returns integer
language plpgsql immutable parallel safe set search_path = '' as $$
begin
  return nullif(btrim(v), '')::numeric::integer;
exception when others then
  return null;
end $$;

create function silver.try_bool(v text) returns boolean
language sql immutable parallel safe set search_path = '' as $$
  select case lower(btrim(v))
           when 'true' then true when 't' then true when '1' then true
           when 'false' then false when 'f' then false when '0' then false
         end
$$;

comment on function silver.try_date(text) is 'Converte texto em date; nulo se inválido.';
comment on function silver.try_timestamptz(text) is 'Converte texto em timestamptz (UTC); nulo se inválido.';
comment on function silver.try_numeric(text) is 'Converte texto em numeric; nulo se inválido.';
comment on function silver.try_int(text) is 'Converte texto em integer (aceita "3.0"); nulo se inválido.';
comment on function silver.try_bool(text) is 'Converte True/False/1/0 em boolean; nulo se inválido.';

create table silver.accounts (
  account_id      text primary key,
  account_name    text not null,
  industry        text not null,
  country         text not null,
  signup_date     date not null,
  referral_source text not null,
  plan_tier       text not null,
  seats           integer not null,
  is_trial        boolean not null,
  churn_flag      boolean not null,
  _file_sha256    text not null,
  _row_number     integer not null,
  _refreshed_at   timestamptz not null default now()
);
comment on table  silver.accounts is 'Contas (clientes) da RavenStack. Uma linha por conta.';
comment on column silver.accounts.account_id is 'Identificador da conta.';
comment on column silver.accounts.account_name is 'Nome fictício da empresa.';
comment on column silver.accounts.industry is 'Indústria (DevTools, FinTech, Cybersecurity, HealthTech, EdTech).';
comment on column silver.accounts.country is 'País (ISO-2).';
comment on column silver.accounts.signup_date is 'Data de cadastro da conta.';
comment on column silver.accounts.referral_source is 'Canal de aquisição (organic, ads, event, partner, other).';
comment on column silver.accounts.plan_tier is 'Plano INICIAL da conta (o atual vem de subscriptions).';
comment on column silver.accounts.seats is 'Licenças contratadas no cadastro.';
comment on column silver.accounts.is_trial is 'Conta em trial no cadastro.';
comment on column silver.accounts.churn_flag is 'Flag de churn da origem — NÃO é a definição de churn (usar churn_events); conflita com os eventos.';
comment on column silver.accounts._file_sha256 is 'Arquivo de origem.';
comment on column silver.accounts._row_number is 'Linha no arquivo de origem.';
comment on column silver.accounts._refreshed_at is 'Momento do refresh do silver.';

create table silver.subscriptions (
  subscription_id   text primary key,
  account_id        text not null references silver.accounts (account_id),
  start_date        date not null,
  end_date          date,
  plan_tier         text not null,
  seats             integer not null,
  mrr_amount        numeric(12, 2) not null,
  arr_amount        numeric(14, 2) not null,
  is_trial          boolean not null,
  upgrade_flag      boolean not null,
  downgrade_flag    boolean not null,
  churn_flag        boolean not null,
  billing_frequency text not null,
  auto_renew_flag   boolean not null,
  _file_sha256      text not null,
  _row_number       integer not null,
  _refreshed_at     timestamptz not null default now()
);
create index subscriptions_account_id_idx on silver.subscriptions (account_id);
comment on table  silver.subscriptions is 'Assinaturas. Uma conta tem várias, muitas sobrepostas (todas as contas têm 2+ abertas).';
comment on column silver.subscriptions.subscription_id is 'Identificador da assinatura.';
comment on column silver.subscriptions.account_id is 'Conta dona da assinatura.';
comment on column silver.subscriptions.start_date is 'Início da assinatura.';
comment on column silver.subscriptions.end_date is 'Fim da assinatura; nulo = ativa.';
comment on column silver.subscriptions.plan_tier is 'Plano no faturamento (Basic, Pro, Enterprise).';
comment on column silver.subscriptions.seats is 'Licenças da assinatura.';
comment on column silver.subscriptions.mrr_amount is 'Receita mensal recorrente (US$).';
comment on column silver.subscriptions.arr_amount is 'Receita anual recorrente (US$) = 12 × MRR.';
comment on column silver.subscriptions.is_trial is 'Assinatura em trial.';
comment on column silver.subscriptions.upgrade_flag is 'Teve upgrade no meio do ciclo.';
comment on column silver.subscriptions.downgrade_flag is 'Teve downgrade no meio do ciclo.';
comment on column silver.subscriptions.churn_flag is 'Assinatura encerrada (origem) — não usar como definição de churn.';
comment on column silver.subscriptions.billing_frequency is 'Cobrança: monthly ou annual.';
comment on column silver.subscriptions.auto_renew_flag is 'Renovação automática ligada.';
comment on column silver.subscriptions._file_sha256 is 'Arquivo de origem.';
comment on column silver.subscriptions._row_number is 'Linha no arquivo de origem.';
comment on column silver.subscriptions._refreshed_at is 'Momento do refresh do silver.';

create table silver.feature_usage (
  usage_key              text primary key,
  usage_id               text not null,
  subscription_id        text not null references silver.subscriptions (subscription_id),
  account_id             text not null references silver.accounts (account_id),
  usage_date             date not null,
  feature_name           text not null,
  usage_count            integer not null,
  usage_duration_secs    integer not null,
  error_count            integer not null,
  is_beta_feature        boolean not null,
  is_within_subscription boolean not null,
  has_id_collision       boolean not null,
  _file_sha256           text not null,
  _row_number            integer not null,
  _refreshed_at          timestamptz not null default now()
);
create index feature_usage_account_date_idx on silver.feature_usage (account_id, usage_date);
create index feature_usage_subscription_id_idx on silver.feature_usage (subscription_id);
comment on table  silver.feature_usage is 'Uso diário por feature. 77% das linhas têm data fora do período da assinatura (ver is_within_subscription).';
comment on column silver.feature_usage.usage_key is 'Chave única: usage_id, com sufixo #n quando o mesmo usage_id aparece em eventos diferentes.';
comment on column silver.feature_usage.usage_id is 'Identificador de origem (21 ids colidem entre eventos diferentes).';
comment on column silver.feature_usage.subscription_id is 'Assinatura do uso.';
comment on column silver.feature_usage.account_id is 'Conta do uso (derivada via subscriptions).';
comment on column silver.feature_usage.usage_date is 'Data do uso.';
comment on column silver.feature_usage.feature_name is 'Feature usada (40 features).';
comment on column silver.feature_usage.usage_count is 'Quantidade de eventos de uso.';
comment on column silver.feature_usage.usage_duration_secs is 'Tempo de uso em segundos.';
comment on column silver.feature_usage.error_count is 'Erros registrados.';
comment on column silver.feature_usage.is_beta_feature is 'Feature em beta.';
comment on column silver.feature_usage.is_within_subscription is 'usage_date dentro de [start_date, end_date] da assinatura.';
comment on column silver.feature_usage.has_id_collision is 'O usage_id de origem se repete em outro evento.';
comment on column silver.feature_usage._file_sha256 is 'Arquivo de origem.';
comment on column silver.feature_usage._row_number is 'Linha no arquivo de origem.';
comment on column silver.feature_usage._refreshed_at is 'Momento do refresh do silver.';

create table silver.support_tickets (
  ticket_id                   text primary key,
  account_id                  text not null references silver.accounts (account_id),
  submitted_at                timestamptz not null,
  closed_at                   timestamptz,
  resolution_time_hours       numeric(10, 2),
  priority                    text not null,
  first_response_time_minutes integer,
  satisfaction_score          smallint check (satisfaction_score between 1 and 5),
  escalation_flag             boolean not null,
  _file_sha256                text not null,
  _row_number                 integer not null,
  _refreshed_at               timestamptz not null default now()
);
create index support_tickets_account_id_idx on silver.support_tickets (account_id);
comment on table  silver.support_tickets is 'Tickets de suporte.';
comment on column silver.support_tickets.ticket_id is 'Identificador do ticket.';
comment on column silver.support_tickets.account_id is 'Conta que abriu o ticket.';
comment on column silver.support_tickets.submitted_at is 'Abertura (a origem só traz a data; hora = 00:00 UTC).';
comment on column silver.support_tickets.closed_at is 'Fechamento.';
comment on column silver.support_tickets.resolution_time_hours is 'Tempo de resolução em horas.';
comment on column silver.support_tickets.priority is 'Prioridade: low, medium, high, urgent.';
comment on column silver.support_tickets.first_response_time_minutes is 'Tempo até a primeira resposta, em minutos.';
comment on column silver.support_tickets.satisfaction_score is 'CSAT 1–5; nulo = cliente não respondeu.';
comment on column silver.support_tickets.escalation_flag is 'Ticket escalado.';
comment on column silver.support_tickets._file_sha256 is 'Arquivo de origem.';
comment on column silver.support_tickets._row_number is 'Linha no arquivo de origem.';
comment on column silver.support_tickets._refreshed_at is 'Momento do refresh do silver.';

create table silver.churn_events (
  churn_event_id           text primary key,
  account_id               text not null references silver.accounts (account_id),
  churn_date               date not null,
  reason_code              text not null,
  refund_amount_usd        numeric(12, 2) not null,
  preceding_upgrade_flag   boolean not null,
  preceding_downgrade_flag boolean not null,
  is_reactivation          boolean not null,
  feedback_text            text,
  _file_sha256             text not null,
  _row_number              integer not null,
  _refreshed_at            timestamptz not null default now()
);
create index churn_events_account_date_idx on silver.churn_events (account_id, churn_date);
comment on table  silver.churn_events is 'Eventos de churn — FONTE DE VERDADE do churn (decisão 2026-10-23). Uma conta pode churnar várias vezes.';
comment on column silver.churn_events.churn_event_id is 'Identificador do evento.';
comment on column silver.churn_events.account_id is 'Conta que churnou.';
comment on column silver.churn_events.churn_date is 'Data do churn.';
comment on column silver.churn_events.reason_code is 'Motivo declarado (pricing, support, features, budget, competitor, unknown).';
comment on column silver.churn_events.refund_amount_usd is 'Valor devolvido (US$).';
comment on column silver.churn_events.preceding_upgrade_flag is 'Teve upgrade nos 90 dias anteriores.';
comment on column silver.churn_events.preceding_downgrade_flag is 'Teve downgrade nos 90 dias anteriores.';
comment on column silver.churn_events.is_reactivation is 'A conta já tinha churnado antes.';
comment on column silver.churn_events.feedback_text is 'Comentário do cliente (só 4 textos distintos na origem).';
comment on column silver.churn_events._file_sha256 is 'Arquivo de origem.';
comment on column silver.churn_events._row_number is 'Linha no arquivo de origem.';
comment on column silver.churn_events._refreshed_at is 'Momento do refresh do silver.';

create table silver._rejects (
  reject_id   bigint generated always as identity primary key,
  run_id      uuid not null references ops.ingestion_runs (run_id) on delete cascade,
  dataset     text not null,
  file_sha256 text not null,
  row_number  integer not null,
  reason      text not null,
  payload     jsonb not null,
  rejected_at timestamptz not null default now()
);
create index rejects_run_id_idx on silver._rejects (run_id);
comment on table  silver._rejects is 'Linhas que não entraram no silver, com o motivo e o conteúdo original.';
comment on column silver._rejects.reject_id is 'Identificador.';
comment on column silver._rejects.run_id is 'Execução que rejeitou.';
comment on column silver._rejects.dataset is 'Dataset de origem.';
comment on column silver._rejects.file_sha256 is 'Arquivo de origem.';
comment on column silver._rejects.row_number is 'Linha no arquivo.';
comment on column silver._rejects.reason is 'Motivo da rejeição.';
comment on column silver._rejects.payload is 'Linha original (bronze).';
comment on column silver._rejects.rejected_at is 'Quando foi rejeitada.';

alter table silver.accounts        enable row level security;
alter table silver.subscriptions   enable row level security;
alter table silver.feature_usage   enable row level security;
alter table silver.support_tickets enable row level security;
alter table silver.churn_events    enable row level security;
alter table silver._rejects        enable row level security;

-- Registra uma etapa "silver" em ops.ingestion_steps.
create function silver._log_step(
  p_run_id uuid, p_dataset text, p_sha text, p_read integer, p_loaded integer,
  p_rejected integer, p_started timestamptz
) returns void
language sql set search_path = '' as $$
  insert into ops.ingestion_steps
    (run_id, dataset, layer, file_sha256, rows_read, rows_loaded, rows_rejected,
     status, started_at, finished_at, duration_ms)
  values
    (p_run_id, p_dataset, 'silver', p_sha, p_read, p_loaded, p_rejected, 'success',
     p_started, clock_timestamp(),
     (extract(epoch from clock_timestamp() - p_started) * 1000)::integer)
$$;

-- Reconstrói o silver inteiro a partir do arquivo mais recente de cada dataset no bronze.
create function silver.refresh(p_run_id uuid)
returns table (dataset text, rows_read integer, rows_loaded integer, rows_rejected integer)
language plpgsql set search_path = '' as $$
#variable_conflict use_column
declare
  v_sha text;
  v_t0 timestamptz;
  v_read integer;
  v_ok integer;
  v_rej integer;
begin
  truncate silver.feature_usage, silver.support_tickets, silver.churn_events,
           silver.subscriptions, silver.accounts;

  -- accounts -------------------------------------------------------------
  v_t0 := clock_timestamp();
  select b._file_sha256 into v_sha from bronze.accounts b order by b._ingested_at desc limit 1;
  with src as (
    select b._file_sha256 as sha, b._row_number as rn_file,
           to_jsonb(b) - '{_run_id,_file_sha256,_row_number,_row_hash,_ingested_at}'::text[] as payload,
           nullif(btrim(b.account_id), '') as account_id,
           nullif(btrim(b.account_name), '') as account_name,
           nullif(btrim(b.industry), '') as industry,
           nullif(btrim(b.country), '') as country,
           silver.try_date(b.signup_date) as signup_date,
           nullif(btrim(b.referral_source), '') as referral_source,
           nullif(btrim(b.plan_tier), '') as plan_tier,
           silver.try_int(b.seats) as seats,
           silver.try_bool(b.is_trial) as is_trial,
           silver.try_bool(b.churn_flag) as churn_flag
    from bronze.accounts b where b._file_sha256 = v_sha
  ), chk as (
    select s.*,
           concat_ws('; ',
             case when s.account_id is null then 'account_id vazio' end,
             case when s.signup_date is null then 'signup_date inválida' end,
             case when s.seats is null then 'seats inválido' end,
             case when s.is_trial is null or s.churn_flag is null then 'booleano inválido' end,
             case when s.account_name is null or s.industry is null or s.country is null
                    or s.referral_source is null or s.plan_tier is null then 'campo obrigatório vazio' end
           ) as reason,
           row_number() over (partition by s.account_id order by s.rn_file desc) as dup_rank
    from src s
  ), rej as (
    insert into silver._rejects (run_id, dataset, file_sha256, row_number, reason, payload)
    select p_run_id, 'accounts', c.sha, c.rn_file,
           case when c.reason <> '' then c.reason else 'account_id duplicado' end, c.payload
    from chk c where c.reason <> '' or c.dup_rank > 1
    returning 1
  ), ins as (
    insert into silver.accounts
      (account_id, account_name, industry, country, signup_date, referral_source, plan_tier,
       seats, is_trial, churn_flag, _file_sha256, _row_number)
    select c.account_id, c.account_name, c.industry, c.country, c.signup_date, c.referral_source,
           c.plan_tier, c.seats, c.is_trial, c.churn_flag, c.sha, c.rn_file
    from chk c where c.reason = '' and c.dup_rank = 1
    returning 1
  )
  select (select count(*) from src), (select count(*) from ins), (select count(*) from rej)
    into v_read, v_ok, v_rej;
  perform silver._log_step(p_run_id, 'accounts', v_sha, v_read, v_ok, v_rej, v_t0);
  dataset := 'accounts'; rows_read := v_read; rows_loaded := v_ok; rows_rejected := v_rej; return next;

  -- subscriptions --------------------------------------------------------
  v_t0 := clock_timestamp();
  select b._file_sha256 into v_sha from bronze.subscriptions b order by b._ingested_at desc limit 1;
  with src as (
    select b._file_sha256 as sha, b._row_number as rn_file,
           to_jsonb(b) - '{_run_id,_file_sha256,_row_number,_row_hash,_ingested_at}'::text[] as payload,
           nullif(btrim(b.subscription_id), '') as subscription_id,
           nullif(btrim(b.account_id), '') as account_id,
           silver.try_date(b.start_date) as start_date,
           silver.try_date(b.end_date) as end_date,
           nullif(btrim(b.end_date), '') is not null as has_end_text,
           nullif(btrim(b.plan_tier), '') as plan_tier,
           silver.try_int(b.seats) as seats,
           silver.try_numeric(b.mrr_amount) as mrr_amount,
           silver.try_numeric(b.arr_amount) as arr_amount,
           silver.try_bool(b.is_trial) as is_trial,
           silver.try_bool(b.upgrade_flag) as upgrade_flag,
           silver.try_bool(b.downgrade_flag) as downgrade_flag,
           silver.try_bool(b.churn_flag) as churn_flag,
           nullif(btrim(b.billing_frequency), '') as billing_frequency,
           silver.try_bool(b.auto_renew_flag) as auto_renew_flag
    from bronze.subscriptions b where b._file_sha256 = v_sha
  ), chk as (
    select s.*,
           concat_ws('; ',
             case when s.subscription_id is null then 'subscription_id vazio' end,
             case when s.account_id is null
                    or not exists (select 1 from silver.accounts a where a.account_id = s.account_id)
                  then 'conta inexistente' end,
             case when s.start_date is null then 'start_date inválida' end,
             case when s.has_end_text and s.end_date is null then 'end_date inválida' end,
             case when s.seats is null or s.mrr_amount is null or s.arr_amount is null then 'número inválido' end,
             case when s.is_trial is null or s.upgrade_flag is null or s.downgrade_flag is null
                    or s.churn_flag is null or s.auto_renew_flag is null then 'booleano inválido' end,
             case when s.plan_tier is null or s.billing_frequency is null then 'campo obrigatório vazio' end
           ) as reason,
           row_number() over (partition by s.subscription_id order by s.rn_file desc) as dup_rank
    from src s
  ), rej as (
    insert into silver._rejects (run_id, dataset, file_sha256, row_number, reason, payload)
    select p_run_id, 'subscriptions', c.sha, c.rn_file,
           case when c.reason <> '' then c.reason else 'subscription_id duplicado' end, c.payload
    from chk c where c.reason <> '' or c.dup_rank > 1
    returning 1
  ), ins as (
    insert into silver.subscriptions
      (subscription_id, account_id, start_date, end_date, plan_tier, seats, mrr_amount, arr_amount,
       is_trial, upgrade_flag, downgrade_flag, churn_flag, billing_frequency, auto_renew_flag,
       _file_sha256, _row_number)
    select c.subscription_id, c.account_id, c.start_date, c.end_date, c.plan_tier, c.seats,
           c.mrr_amount, c.arr_amount, c.is_trial, c.upgrade_flag, c.downgrade_flag, c.churn_flag,
           c.billing_frequency, c.auto_renew_flag, c.sha, c.rn_file
    from chk c where c.reason = '' and c.dup_rank = 1
    returning 1
  )
  select (select count(*) from src), (select count(*) from ins), (select count(*) from rej)
    into v_read, v_ok, v_rej;
  perform silver._log_step(p_run_id, 'subscriptions', v_sha, v_read, v_ok, v_rej, v_t0);
  dataset := 'subscriptions'; rows_read := v_read; rows_loaded := v_ok; rows_rejected := v_rej; return next;

  -- churn_events ---------------------------------------------------------
  v_t0 := clock_timestamp();
  select b._file_sha256 into v_sha from bronze.churn_events b order by b._ingested_at desc limit 1;
  with src as (
    select b._file_sha256 as sha, b._row_number as rn_file,
           to_jsonb(b) - '{_run_id,_file_sha256,_row_number,_row_hash,_ingested_at}'::text[] as payload,
           nullif(btrim(b.churn_event_id), '') as churn_event_id,
           nullif(btrim(b.account_id), '') as account_id,
           silver.try_date(b.churn_date) as churn_date,
           nullif(btrim(b.reason_code), '') as reason_code,
           coalesce(silver.try_numeric(b.refund_amount_usd), case when nullif(btrim(b.refund_amount_usd), '') is null then 0 end) as refund_amount_usd,
           silver.try_bool(b.preceding_upgrade_flag) as preceding_upgrade_flag,
           silver.try_bool(b.preceding_downgrade_flag) as preceding_downgrade_flag,
           silver.try_bool(b.is_reactivation) as is_reactivation,
           nullif(btrim(b.feedback_text), '') as feedback_text
    from bronze.churn_events b where b._file_sha256 = v_sha
  ), chk as (
    select s.*,
           concat_ws('; ',
             case when s.churn_event_id is null then 'churn_event_id vazio' end,
             case when s.account_id is null
                    or not exists (select 1 from silver.accounts a where a.account_id = s.account_id)
                  then 'conta inexistente' end,
             case when s.churn_date is null then 'churn_date inválida' end,
             case when s.reason_code is null then 'reason_code vazio' end,
             case when s.refund_amount_usd is null then 'refund inválido' end,
             case when s.preceding_upgrade_flag is null or s.preceding_downgrade_flag is null
                    or s.is_reactivation is null then 'booleano inválido' end
           ) as reason,
           row_number() over (partition by s.churn_event_id order by s.rn_file desc) as dup_rank
    from src s
  ), rej as (
    insert into silver._rejects (run_id, dataset, file_sha256, row_number, reason, payload)
    select p_run_id, 'churn_events', c.sha, c.rn_file,
           case when c.reason <> '' then c.reason else 'churn_event_id duplicado' end, c.payload
    from chk c where c.reason <> '' or c.dup_rank > 1
    returning 1
  ), ins as (
    insert into silver.churn_events
      (churn_event_id, account_id, churn_date, reason_code, refund_amount_usd,
       preceding_upgrade_flag, preceding_downgrade_flag, is_reactivation, feedback_text,
       _file_sha256, _row_number)
    select c.churn_event_id, c.account_id, c.churn_date, c.reason_code, c.refund_amount_usd,
           c.preceding_upgrade_flag, c.preceding_downgrade_flag, c.is_reactivation, c.feedback_text,
           c.sha, c.rn_file
    from chk c where c.reason = '' and c.dup_rank = 1
    returning 1
  )
  select (select count(*) from src), (select count(*) from ins), (select count(*) from rej)
    into v_read, v_ok, v_rej;
  perform silver._log_step(p_run_id, 'churn_events', v_sha, v_read, v_ok, v_rej, v_t0);
  dataset := 'churn_events'; rows_read := v_read; rows_loaded := v_ok; rows_rejected := v_rej; return next;

  -- support_tickets ------------------------------------------------------
  v_t0 := clock_timestamp();
  select b._file_sha256 into v_sha from bronze.support_tickets b order by b._ingested_at desc limit 1;
  with src as (
    select b._file_sha256 as sha, b._row_number as rn_file,
           to_jsonb(b) - '{_run_id,_file_sha256,_row_number,_row_hash,_ingested_at}'::text[] as payload,
           nullif(btrim(b.ticket_id), '') as ticket_id,
           nullif(btrim(b.account_id), '') as account_id,
           silver.try_timestamptz(b.submitted_at) as submitted_at,
           silver.try_timestamptz(b.closed_at) as closed_at,
           nullif(btrim(b.closed_at), '') is not null as has_closed_text,
           silver.try_numeric(b.resolution_time_hours) as resolution_time_hours,
           nullif(btrim(b.priority), '') as priority,
           silver.try_int(b.first_response_time_minutes) as first_response_time_minutes,
           silver.try_int(b.satisfaction_score) as satisfaction_score,
           nullif(btrim(b.satisfaction_score), '') is not null as has_score_text,
           silver.try_bool(b.escalation_flag) as escalation_flag
    from bronze.support_tickets b where b._file_sha256 = v_sha
  ), chk as (
    select s.*,
           concat_ws('; ',
             case when s.ticket_id is null then 'ticket_id vazio' end,
             case when s.account_id is null
                    or not exists (select 1 from silver.accounts a where a.account_id = s.account_id)
                  then 'conta inexistente' end,
             case when s.submitted_at is null then 'submitted_at inválido' end,
             case when s.has_closed_text and s.closed_at is null then 'closed_at inválido' end,
             case when s.has_score_text and (s.satisfaction_score is null
                    or s.satisfaction_score not between 1 and 5) then 'satisfaction_score fora de 1–5' end,
             case when s.priority is null then 'priority vazia' end,
             case when s.escalation_flag is null then 'booleano inválido' end
           ) as reason,
           row_number() over (partition by s.ticket_id order by s.rn_file desc) as dup_rank
    from src s
  ), rej as (
    insert into silver._rejects (run_id, dataset, file_sha256, row_number, reason, payload)
    select p_run_id, 'support_tickets', c.sha, c.rn_file,
           case when c.reason <> '' then c.reason else 'ticket_id duplicado' end, c.payload
    from chk c where c.reason <> '' or c.dup_rank > 1
    returning 1
  ), ins as (
    insert into silver.support_tickets
      (ticket_id, account_id, submitted_at, closed_at, resolution_time_hours, priority,
       first_response_time_minutes, satisfaction_score, escalation_flag, _file_sha256, _row_number)
    select c.ticket_id, c.account_id, c.submitted_at, c.closed_at, c.resolution_time_hours,
           c.priority, c.first_response_time_minutes, c.satisfaction_score::smallint,
           c.escalation_flag, c.sha, c.rn_file
    from chk c where c.reason = '' and c.dup_rank = 1
    returning 1
  )
  select (select count(*) from src), (select count(*) from ins), (select count(*) from rej)
    into v_read, v_ok, v_rej;
  perform silver._log_step(p_run_id, 'support_tickets', v_sha, v_read, v_ok, v_rej, v_t0);
  dataset := 'support_tickets'; rows_read := v_read; rows_loaded := v_ok; rows_rejected := v_rej; return next;

  -- feature_usage --------------------------------------------------------
  -- usage_id colide em 21 casos com eventos DIFERENTES: mantemos todos com usage_key = usage_id#n.
  v_t0 := clock_timestamp();
  select b._file_sha256 into v_sha from bronze.feature_usage b order by b._ingested_at desc limit 1;
  with src as (
    select b._file_sha256 as sha, b._row_number as rn_file,
           to_jsonb(b) - '{_run_id,_file_sha256,_row_number,_row_hash,_ingested_at}'::text[] as payload,
           nullif(btrim(b.usage_id), '') as usage_id,
           nullif(btrim(b.subscription_id), '') as subscription_id,
           silver.try_date(b.usage_date) as usage_date,
           nullif(btrim(b.feature_name), '') as feature_name,
           silver.try_int(b.usage_count) as usage_count,
           silver.try_int(b.usage_duration_secs) as usage_duration_secs,
           silver.try_int(b.error_count) as error_count,
           silver.try_bool(b.is_beta_feature) as is_beta_feature
    from bronze.feature_usage b where b._file_sha256 = v_sha
  ), chk as (
    select s.*, sub.account_id, sub.start_date, sub.end_date,
           concat_ws('; ',
             case when s.usage_id is null then 'usage_id vazio' end,
             case when sub.subscription_id is null then 'assinatura inexistente' end,
             case when s.usage_date is null then 'usage_date inválida' end,
             case when s.feature_name is null then 'feature_name vazia' end,
             case when s.usage_count is null or s.usage_duration_secs is null
                    or s.error_count is null then 'número inválido' end,
             case when s.is_beta_feature is null then 'booleano inválido' end
           ) as reason,
           count(*) over (partition by s.usage_id) as id_count,
           row_number() over (partition by s.usage_id order by s.rn_file) as id_rank
    from src s
    left join silver.subscriptions sub on sub.subscription_id = s.subscription_id
  ), rej as (
    insert into silver._rejects (run_id, dataset, file_sha256, row_number, reason, payload)
    select p_run_id, 'feature_usage', c.sha, c.rn_file, c.reason, c.payload
    from chk c where c.reason <> ''
    returning 1
  ), ins as (
    insert into silver.feature_usage
      (usage_key, usage_id, subscription_id, account_id, usage_date, feature_name, usage_count,
       usage_duration_secs, error_count, is_beta_feature, is_within_subscription,
       has_id_collision, _file_sha256, _row_number)
    select case when c.id_count > 1 then c.usage_id || '#' || c.id_rank else c.usage_id end,
           c.usage_id, c.subscription_id, c.account_id, c.usage_date, c.feature_name,
           c.usage_count, c.usage_duration_secs, c.error_count, c.is_beta_feature,
           c.usage_date between c.start_date and coalesce(c.end_date, 'infinity'::date),
           c.id_count > 1, c.sha, c.rn_file
    from chk c where c.reason = ''
    returning 1
  )
  select (select count(*) from src), (select count(*) from ins), (select count(*) from rej)
    into v_read, v_ok, v_rej;
  perform silver._log_step(p_run_id, 'feature_usage', v_sha, v_read, v_ok, v_rej, v_t0);
  dataset := 'feature_usage'; rows_read := v_read; rows_loaded := v_ok; rows_rejected := v_rej; return next;
end $$;

comment on function silver.refresh(uuid) is
  'Reconstrói o silver a partir do arquivo mais recente de cada dataset no bronze; rejeitados vão para silver._rejects; registra etapas em ops.ingestion_steps.';

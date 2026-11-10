-- 0023_atividades.sql  [LOTE 2 — decisão 37]
-- Ao dar ✓ nas Prioridades do dia, o vendedor registra o que foi feito: tipo de atividade (lista fixa),
-- comentário obrigatório e o horário real (acao_registros.criado_em). O ✗ continua sem registro obrigatório.
-- O ✓ com tipo de atividade conta como contato e atualiza core_deals.ultimo_contato_em.

create table config_tipos_atividade (
  codigo             text primary key check (codigo ~ '^[a-z][a-z_]*$'),
  rotulo             text not null check (char_length(btrim(rotulo)) between 1 and 40),
  conta_como_contato boolean not null default true,
  ordem              smallint not null default 0,
  ativo              boolean not null default true
);

create trigger config_tipos_atividade_auditar after insert or update on config_tipos_atividade
  for each row execute function system_auditar('codigo');

select set_config('app.usuario_id', '1', true), set_config('app.correlation_id', '00000000-0000-4000-8000-000000000023', true);
insert into config_tipos_atividade (codigo, rotulo, ordem) values
  ('ligacao', 'Ligação', 1),
  ('email', 'E-mail', 2),
  ('mensagem', 'Mensagem', 3),
  ('reuniao', 'Reunião', 4),
  ('proposta_enviada', 'Proposta enviada', 5),
  ('requalificado', 'Requalificado', 6),
  ('sem_resposta', 'Sem resposta', 7)
on conflict do nothing;
select set_config('app.usuario_id', '', true), set_config('app.correlation_id', '', true);

-- O registro do ✓ ganha o tipo e o vínculo com o item da lista do dia
alter table acao_registros
  add column tipo_atividade text references config_tipos_atividade (codigo) on delete restrict,
  add column prioridade_id  bigint references acao_prioridades (id) on delete restrict,
  add constraint acao_registros_feita_completa_chk check (
    acao <> 'prioridade_feita' or (tipo_atividade is not null and nullif(btrim(nota), '') is not null));
create index acao_registros_tipo_atividade_idx on acao_registros (tipo_atividade);
create index acao_registros_prioridade_id_idx on acao_registros (prioridade_id);

-- ✓ / ✗ com o registro da atividade. Para ✓, tipo e comentário são obrigatórios.
create or replace function acao_marcar_prioridade(
  p_usuario_id     bigint,
  p_correlation_id uuid,
  p_opportunity_id text,
  p_resultado      text,
  p_tipo_atividade text,
  p_comentario     text
) returns acao_registros
language plpgsql set search_path = public as $$
declare
  u           config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id);
  r           acao_registros;
  v_item      bigint;
  v_tipo      text := nullif(btrim(p_tipo_atividade), '');
  v_coment    text := nullif(btrim(p_comentario), '');
begin
  if p_resultado not in ('feita', 'pulada') then
    raise exception 'Use feita (✓) ou pulada (✗).' using errcode = 'GS400';
  end if;
  if p_resultado = 'feita' then
    if v_tipo is null or not exists (select 1 from config_tipos_atividade where codigo = v_tipo and ativo) then
      raise exception 'Escolha o tipo de atividade.' using errcode = 'GS400';
    end if;
    if v_coment is null then
      raise exception 'Escreva um comentário sobre o que foi feito.' using errcode = 'GS400';
    end if;
  elsif v_tipo is not null and not exists (select 1 from config_tipos_atividade where codigo = v_tipo and ativo) then
    raise exception 'Tipo de atividade desconhecido.' using errcode = 'GS400';
  end if;
  if char_length(v_coment) > 280 or v_coment ~ '<[a-zA-Z/!]' then
    raise exception 'Comentário de até 280 caracteres, sem HTML.' using errcode = 'GS400';
  end if;

  select id into v_item from acao_prioridades
   where usuario_id = u.id and dia = system_dia_real() and opportunity_id = p_opportunity_id;
  if v_item is null then
    raise exception 'Este deal não está na sua lista de hoje.' using errcode = 'GS404';
  end if;
  if exists (select 1 from acao_registros
              where opportunity_id = p_opportunity_id and usuario_id = u.id and desfeita_em is null
                and acao in ('prioridade_feita', 'prioridade_pulada')
                and (criado_em at time zone coalesce(config_texto('fuso_horario'), 'UTC'))::date = system_dia_real()) then
    raise exception 'Este item já foi marcado hoje.' using errcode = 'GS422';
  end if;
  if not exists (select 1 from core_deals where opportunity_id = p_opportunity_id and estagio in ('Prospecting', 'Engaging')) then
    raise exception 'Este deal já foi encerrado.' using errcode = 'GS422';
  end if;

  insert into acao_registros (opportunity_id, usuario_id, papel, execucao_id, acao, nota, data_negocio,
                              tipo_atividade, prioridade_id)
  values (p_opportunity_id, u.id, u.papel, score_execucao_ativa(), 'prioridade_' || p_resultado,
          v_coment, system_data_negocio(), v_tipo, v_item)
  returning * into r;
  return r;
end $$;

-- A assinatura antiga (sem tipo) continua para o ✗; o ✓ por ela é recusado (falta o tipo e o comentário).
create or replace function acao_marcar_prioridade(
  p_usuario_id     bigint,
  p_correlation_id uuid,
  p_opportunity_id text,
  p_resultado      text,
  p_nota           text default null
) returns acao_registros
language sql set search_path = public as $$
  select acao_marcar_prioridade(p_usuario_id, p_correlation_id, p_opportunity_id, p_resultado,
                                null::text, p_nota)
$$;

-- Último contato: ações de contato (acoes_contato) e o ✓ com tipo de atividade que conta como contato
create or replace function acao_atualizar_ultimo_contato() returns trigger
language plpgsql set search_path = public as $$
declare
  v_ultimo date;
begin
  select max(r.data_negocio) into v_ultimo
    from acao_registros r
    left join config_tipos_atividade t on t.codigo = r.tipo_atividade
   where r.opportunity_id = new.opportunity_id
     and r.desfeita_em is null
     and (r.acao = any (config_lista('acoes_contato')) or coalesce(t.conta_como_contato, false));
  update core_deals
     set ultimo_contato_em = v_ultimo
   where opportunity_id = new.opportunity_id
     and ultimo_contato_em is distinct from v_ultimo;
  return new;
end $$;

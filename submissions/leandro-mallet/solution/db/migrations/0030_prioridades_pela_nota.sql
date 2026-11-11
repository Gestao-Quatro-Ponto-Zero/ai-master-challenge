-- 0030_prioridades_pela_nota.sql  [O-24 — Prioridades do dia seguem a nota]
-- A lista do dia passa a seguir a nota da execução de score ativa, para todos os papéis:
--   1) no topo, o lead novo (criado no CRM há até 1 dia, sem contato registrado) com FIT >= fit_furar_fila;
--      acima de tudo, os marcados "atendimento atrasado" (esse mesmo lead, passado 1 dia sem contato);
--   2) depois, pela nota;
--   3) no empate, maior HEAT;
--   4) por fim, opportunity_id.
-- O valor esperado sai da ordem (decisões 28 e 29: o valor não entra na nota).
-- A lista guarda a execução usada. Se a execução ativa muda no meio do dia, os itens ainda não marcados
-- saem da lista (substituida_em preenchida, nunca DELETE) e entram os da ordem nova; os marcados ficam.
-- Manager e admin: mesmo escopo de antes (time do manager; todos para o admin). Quais itens entram é o
-- parâmetro prioridades_gestor (icone | atencao | todos). Padrão "atencao" (decisão do Leandro, O-25: "só o que
-- pede ação"): atendimento atrasado, lead novo com FIT alto e em risco de esfriar. O super hot sai da lista do gestor.
-- Ícone super hot: sai o critério de ticket (preco_min_quente = null). Fica a janela de 15 a 106 dias.
-- Trava de contexto, limites, auditoria e permissões seguem como estão.

select system_iniciar_contexto_sistema('00000000-0000-4000-8000-000000000030'::uuid);

-- 1. Ícone super hot sem o critério de ticket ------------------------------------------------------------

create or replace function core_icone(p_estagio text, p_dias integer, p_preco integer, p_dias_sem_contato integer) returns text
language sql stable set search_path = public as $$
  select case
           when p_estagio <> 'Engaging' or p_dias is null then null
           when p_dias > (c ->> 'dias_max_risco')::integer then 'esfriou'
           when p_dias > (c ->> 'dias_max_quente')::integer then 'em_risco'
           when p_dias_sem_contato is not null
                and p_dias_sem_contato >= coalesce(config_inteiro('dias_sem_contato_risco'), 14) then 'em_risco'
           when p_dias >= (c ->> 'dias_min_quente')::integer
                and (c ->> 'preco_min_quente' is null or p_preco >= (c ->> 'preco_min_quente')::integer) then 'super_hot'
           else null
         end
    from (select coalesce(config_valor('icone_cortes'),
                          '{"dias_min_quente": 15, "dias_max_quente": 106, "dias_max_risco": 138, "preco_min_quente": null}'::jsonb) as c) x
$$;

update config_parametros
   set valor = jsonb_set(valor, '{preco_min_quente}', 'null'::jsonb),
       descricao = 'Cortes dos ícones em dias de negociação. preco_min_quente null = super hot sem critério de ticket (O-24).',
       atualizado_em = now()
 where chave = 'icone_cortes';

insert into config_parametros (chave, valor, descricao) values
  ('prioridades_gestor', '{"filtro": "atencao"}'::jsonb,
   'Itens das Prioridades do dia do manager (time) e do admin (todos). icone = super hot ou em risco; atencao = atendimento atrasado, lead novo com FIT alto ou em risco; todos = todos os abertos do escopo. A ordem é a mesma do vendedor.')
on conflict do nothing;

-- 2. A lista guarda a execução usada e a substituição -----------------------------------------------------

alter table acao_prioridades
  add column execucao_id    bigint references score_execucoes (id) on delete restrict,
  add column substituida_em timestamptz;
create index acao_prioridades_execucao_id_idx on acao_prioridades (execucao_id);
create index acao_prioridades_ativas_idx on acao_prioridades (usuario_id, dia) where substituida_em is null;

-- 3. Peças da ordem -----------------------------------------------------------------------------------------

-- FIT usado na ordem: o da nota; sem nota (lead criado depois da execução), o do vendedor no cohort do lead.
create or replace function acao_fit_para_ordem(p_fit smallint, p_vendedor text, p_produto text, p_conta text) returns smallint
language sql stable set search_path = public as $$
  select coalesce(p_fit,
                  (select f.fit from score_fit_vendedores f
                    where f.execucao_id = score_execucao_ativa() and f.vendedor_nome = p_vendedor
                      and f.cohort = score_chave_cohort(p_produto, p_conta)))
$$;

-- Grupo do item: 0 = atendimento atrasado; 1 = lead novo (até 1 dia, sem contato) com FIT alto; 2 = os demais.
-- Lead novo = criado no CRM (os deals do dataset não têm criado_em). Contato = core_deals.ultimo_contato_em.
create or replace function acao_grupo_prioridade(p_criado_em timestamptz, p_ultimo_contato_em date, p_fit smallint, p_marcadores text[])
returns smallint
language sql stable set search_path = public as $$
  select (case
            when p_ultimo_contato_em is not null then 2
            when 'atendimento_atrasado' = any (coalesce(p_marcadores, '{}'::text[])) then 0
            when p_criado_em is null or coalesce(p_fit, 0) < coalesce(config_inteiro('fit_furar_fila'), 75) then 2
            when system_dia_real() - (p_criado_em at time zone coalesce(config_texto('fuso_horario'), 'UTC'))::date > 1 then 0
            else 1
          end)::smallint
$$;

-- Item marcado hoje (✓, ✗ ou contato registrado por este usuário, não desfeito): fica na lista.
create or replace function acao_item_marcado(p_usuario_id bigint, p_opportunity_id text, p_dia date) returns boolean
language sql stable set search_path = public as $$
  select exists (select 1 from acao_registros r
                  where r.opportunity_id = p_opportunity_id and r.usuario_id = p_usuario_id and r.desfeita_em is null
                    and (r.criado_em at time zone coalesce(config_texto('fuso_horario'), 'UTC'))::date = p_dia)
$$;

-- 4. Montar: mesma ordem para todos os papéis, sem valor esperado ------------------------------------------

create or replace function acao_montar_prioridades(p_usuario config_usuarios, p_quantidade integer) returns integer
language plpgsql set search_path = public as $$
declare
  v_dia       date := system_dia_real();
  v_exec      bigint := score_execucao_ativa();
  v_filtro    text := coalesce(config_valor('prioridades_gestor') ->> 'filtro', 'atencao');
  v_max_pos   integer;
  v_inseridos integer;
begin
  select coalesce(max(posicao), 0) into v_max_pos from acao_prioridades where usuario_id = p_usuario.id and dia = v_dia;
  insert into acao_prioridades as p (usuario_id, dia, posicao, opportunity_id, execucao_id)
  select p_usuario.id, v_dia, v_max_pos + x.n, x.opportunity_id, v_exec
    from (
      select c.opportunity_id,
             row_number() over (order by c.grupo, c.score desc nulls last, c.heat desc nulls last, c.opportunity_id) as n
        from (
          select v.opportunity_id, v.score, v.heat, v.icone,
                 acao_grupo_prioridade(d.criado_em, d.ultimo_contato_em,
                                       acao_fit_para_ordem(v.fit, v.vendedor_nome, v.produto_nome, v.conta_nome),
                                       v.marcadores) as grupo
            from core_deals_visao v
            join core_deals d on d.opportunity_id = v.opportunity_id
           where v.estagio in ('Prospecting', 'Engaging')
             and case p_usuario.papel
                   when 'vendedor' then v.vendedor_nome = p_usuario.vendedor_nome
                   when 'manager'  then v.manager_nome = p_usuario.manager_nome
                   when 'admin'    then true
                   else false
                 end
             and not exists (select 1 from acao_prioridades q
                              where q.usuario_id = p_usuario.id and q.dia = v_dia and q.opportunity_id = v.opportunity_id
                                and q.substituida_em is null)
             and not acao_item_marcado(p_usuario.id, v.opportunity_id, v_dia)
        ) c
       where p_usuario.papel = 'vendedor'
          or v_filtro = 'todos'
          or (v_filtro = 'icone' and c.icone in ('super_hot', 'em_risco'))
          or (v_filtro not in ('todos', 'icone') and (c.grupo < 2 or c.icone = 'em_risco'))
    ) x
   where x.n <= greatest(p_quantidade, 0)
  -- o deal que já esteve na lista de hoje e foi substituído volta na posição nova (a linha é reaproveitada)
  on conflict (usuario_id, dia, opportunity_id) do update
     set posicao = excluded.posicao, execucao_id = excluded.execucao_id, substituida_em = null
   where p.substituida_em is not null;
  get diagnostics v_inseridos = row_count;
  return v_inseridos;
end $$;

-- 5. Refazer quando a execução ativa muda -------------------------------------------------------------------

-- Lista de hoje montada com outra execução: os itens não marcados saem (substituida_em) e entram os da ordem
-- nova, na mesma quantidade; os marcados ficam. Devolve quantos itens saíram.
create or replace function acao_atualizar_prioridades(p_usuario config_usuarios) returns integer
language plpgsql set search_path = public as $$
declare
  v_dia  date := system_dia_real();
  v_exec bigint := score_execucao_ativa();
  v_sai  integer;
begin
  perform pg_advisory_xact_lock(30030, p_usuario.id::integer);   -- uma atualização por usuário de cada vez
  update acao_prioridades p
     set substituida_em = now()
   where p.usuario_id = p_usuario.id and p.dia = v_dia and p.substituida_em is null
     and p.execucao_id is distinct from v_exec
     and not acao_item_marcado(p_usuario.id, p.opportunity_id, v_dia);
  get diagnostics v_sai = row_count;
  if v_sai > 0 then
    perform acao_montar_prioridades(p_usuario, v_sai);
  end if;
  return v_sai;
end $$;

-- Há item não marcado de outra execução na lista de hoje?
create or replace function acao_lista_desatualizada(p_usuario_id bigint) returns boolean
language sql stable set search_path = public as $$
  select exists (select 1 from acao_prioridades p
                  where p.usuario_id = p_usuario_id and p.dia = system_dia_real() and p.substituida_em is null
                    and p.execucao_id is distinct from score_execucao_ativa()
                    and not acao_item_marcado(p_usuario_id, p.opportunity_id, p.dia))
$$;

-- 6. Listar: só as linhas não substituídas; lista desatualizada volta vazia (quem chama monta de novo) -------

create or replace function acao_listar_prioridades(p_usuario_id bigint)
returns table (posicao smallint, opportunity_id text, nome text, vendedor_nome text, produto_nome text, conta_nome text,
               score smallint, faixa_nota text, icone text, valor_esperado integer, marcada text, pulado_dias_seguidos integer)
language sql stable set search_path = public as $$
  select p.posicao, p.opportunity_id, v.nome, v.vendedor_nome, v.produto_nome, v.conta_nome,
         v.score, v.faixa_nota, v.icone, v.valor_esperado,
         (select case r.acao when 'prioridade_feita' then 'feita' when 'prioridade_pulada' then 'pulada' else 'contato' end
            from acao_registros r
           where r.opportunity_id = p.opportunity_id and r.usuario_id = p.usuario_id and r.desfeita_em is null
             and (r.criado_em at time zone coalesce(config_texto('fuso_horario'), 'UTC'))::date = p.dia
           order by r.criado_em desc limit 1),
         (select count(distinct (r.criado_em at time zone coalesce(config_texto('fuso_horario'), 'UTC'))::date)::integer
            from acao_registros r
           where r.opportunity_id = p.opportunity_id and r.usuario_id = p.usuario_id
             and r.acao = 'prioridade_pulada' and r.desfeita_em is null
             and (r.criado_em at time zone coalesce(config_texto('fuso_horario'), 'UTC'))::date
                 between p.dia - (coalesce(config_inteiro('dias_pulado_alerta'), 3) - 1) and p.dia)
    from acao_prioridades p
    join core_deals_visao v on v.opportunity_id = p.opportunity_id
   where p.usuario_id = p_usuario_id and p.dia = system_dia_real() and p.substituida_em is null
     and not acao_lista_desatualizada(p_usuario_id)
   order by p.posicao
$$;

-- 7. Lista do dia e "puxar mais": atualizam antes, se a execução mudou --------------------------------------

create or replace function acao_prioridades_do_dia(p_usuario_id bigint, p_correlation_id uuid)
returns table (posicao smallint, opportunity_id text, nome text, vendedor_nome text, produto_nome text, conta_nome text,
               score smallint, faixa_nota text, icone text, valor_esperado integer, marcada text, pulado_dias_seguidos integer)
language plpgsql set search_path = public as $$
declare
  u config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id, false);
begin
  perform pg_advisory_xact_lock(30030, u.id::integer);
  if not exists (select 1 from acao_prioridades p where p.usuario_id = u.id and p.dia = system_dia_real() and p.substituida_em is null) then
    perform acao_montar_prioridades(u, coalesce(config_inteiro('meta_prioridades_dia'), 10));
  else
    perform acao_atualizar_prioridades(u);
  end if;
  return query select * from acao_listar_prioridades(u.id);
end $$;

create or replace function acao_puxar_mais_prioridades(p_usuario_id bigint, p_correlation_id uuid, p_quantidade integer default 5)
returns table (posicao smallint, opportunity_id text, nome text, vendedor_nome text, produto_nome text, conta_nome text,
               score smallint, faixa_nota text, icone text, valor_esperado integer, marcada text, pulado_dias_seguidos integer)
language plpgsql set search_path = public as $$
declare
  u config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id, false);
begin
  perform acao_atualizar_prioridades(u);
  perform acao_montar_prioridades(u, least(greatest(p_quantidade, 1), 20));
  return query select * from acao_listar_prioridades(u.id);
end $$;

-- 8. ✓ / ✗: só no item ativo da lista (o resto da regra de 0023 segue igual) -------------------------------

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
   where usuario_id = u.id and dia = system_dia_real() and opportunity_id = p_opportunity_id and substituida_em is null;
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

-- 9. Permissões das funções novas, como as demais: app e carga executam; public, anon e authenticated não ----

do $$
declare
  f text;
  r text;
begin
  foreach f in array array[
    'acao_fit_para_ordem(smallint, text, text, text)',
    'acao_grupo_prioridade(timestamptz, date, smallint, text[])',
    'acao_item_marcado(bigint, text, date)',
    'acao_atualizar_prioridades(config_usuarios)',
    'acao_lista_desatualizada(bigint)'
  ] loop
    execute format('revoke execute on function %s from public', f);
    foreach r in array array['anon', 'authenticated'] loop
      if exists (select 1 from pg_roles where rolname = r) then
        execute format('revoke execute on function %s from %I', f, r);
      end if;
    end loop;
    foreach r in array array['service_role', 'system_carga'] loop
      if exists (select 1 from pg_roles where rolname = r) then
        execute format('grant execute on function %s to %I', f, r);
      end if;
    end loop;
  end loop;
end $$;

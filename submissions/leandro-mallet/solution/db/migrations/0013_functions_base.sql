-- 0013_functions_base.sql  [LOTE 2]
-- (system_iniciar_contexto e system_iniciar_contexto_sistema estão em 0005, lote 1)
-- Cria as funções de apoio usadas pelas views e pelas funções de escrita: contexto de quem escreve
-- (usuário, correlation_id, lote, limite de escritas), checagem de papel, eventos, geração de id,
-- execução de score ativa, chave de cohort, nome padrão do deal, faixa da nota, ícone e escopo do perfil.

create or replace function system_exigir_papel(p_usuario config_usuarios, p_papeis text[]) returns void
language plpgsql as $$
begin
  if not (p_usuario.papel = any (p_papeis)) then
    raise exception 'Esta ação é feita por: %.', array_to_string(p_papeis, ', ') using errcode = 'GS403';
  end if;
end $$;

create or replace function system_registrar_evento(p_tipo text, p_detalhe jsonb default '{}'::jsonb) returns void
language sql set search_path = public as $$
  insert into system_eventos (tipo, detalhe, usuario_id, correlation_id)
  values (p_tipo, coalesce(p_detalhe, '{}'::jsonb),
          nullif(current_setting('app.usuario_id', true), '')::bigint,
          nullif(current_setting('app.correlation_id', true), '')::uuid)
$$;

create or replace function core_gerar_opportunity_id() returns text
language plpgsql set search_path = public as $$
declare
  c constant text := 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  v text;
begin
  loop
    select string_agg(substr(c, 1 + floor(random() * 36)::integer, 1), '') into v from generate_series(1, 8);
    exit when not exists (select 1 from core_deals where opportunity_id = v);
  end loop;
  return v;
end $$;

create or replace function score_execucao_ativa() returns bigint
language sql stable set search_path = public as $$
  select nullif(config_texto('execucao_ativa'), '')::bigint
$$;

-- Chave do cohort de um lead, pelas dimensões configuradas (ex.: ["produto"] ou ["produto", "setor"]).
-- A definição do cohort é do score (Python); aqui só se monta a mesma chave para o roteamento.
create or replace function score_chave_cohort(p_produto text, p_conta text) returns text
language sql stable set search_path = public as $$
  select string_agg(
           x.d || '=' || coalesce(
             case x.d
               when 'produto' then p_produto
               when 'serie'   then (select serie from core_produtos where nome = p_produto)
               when 'setor'   then (select setor from core_contas where nome = p_conta)
               when 'porte'   then (select porte from core_contas where nome = p_conta)
             end, '-'),
           '|' order by x.ord)
    from unnest(config_lista('cohort_dimensoes')) with ordinality as x(d, ord)
$$;

create or replace function core_nome_padrao(p_conta text, p_produto text) returns text
language sql immutable as $$
  select coalesce(nullif(btrim(p_conta), ''), 'Sem empresa') || ' · ' || p_produto
$$;

create or replace function core_rotulo_estagio(p_estagio text) returns text
language sql immutable as $$
  select case p_estagio
           when 'Prospecting' then 'Prospecção'
           when 'Engaging' then 'Em negociação'
           when 'Won' then 'Ganho'
           when 'Lost' then 'Perdido'
           else p_estagio
         end
$$;

create or replace function core_faixa_nota(p_score integer) returns text
language sql stable set search_path = public as $$
  select case
           when p_score is null then null
           when p_score >= coalesce((config_valor('faixas_nota') ->> 'alta')::integer, 70) then 'alta'
           when p_score >= coalesce((config_valor('faixas_nota') ->> 'media')::integer, 40) then 'media'
           else 'baixa'
         end
$$;

-- Ícone do cartão (ESPEC-TELAS 2.4). Cortes em config_parametros.icone_cortes.
-- p_dias_sem_contato considera só contatos registrados no CRM.
create or replace function core_icone(p_estagio text, p_dias integer, p_preco integer, p_dias_sem_contato integer) returns text
language sql stable set search_path = public as $$
  select case
           when p_estagio <> 'Engaging' or p_dias is null then null
           when p_dias > (c ->> 'dias_max_risco')::integer then 'esfriou'
           when p_dias > (c ->> 'dias_max_quente')::integer then 'em_risco'
           when p_dias_sem_contato is not null
                and p_dias_sem_contato >= coalesce(config_inteiro('dias_sem_contato_risco'), 14) then 'em_risco'
           when p_dias >= (c ->> 'dias_min_quente')::integer
                and p_preco >= (c ->> 'preco_min_quente')::integer then 'super_hot'
           else null
         end
    from (select coalesce(config_valor('icone_cortes'),
                          '{"dias_min_quente": 15, "dias_max_quente": 106, "dias_max_risco": 138, "preco_min_quente": 3000}'::jsonb) as c) x
$$;

-- Escopo do perfil: {"papel":"vendedor","vendedor":"..."} · {"papel":"manager","manager":"...","vendedor"?}
-- · {"papel":"admin","regiao"?,"manager"?,"vendedor"?}. Organiza a tela; não é controle de acesso (decisão 16).
create or replace function core_no_escopo(p_escopo jsonb, p_vendedor text, p_manager text, p_escritorio text) returns boolean
language sql immutable as $$
  select case p_escopo ->> 'papel'
           when 'vendedor' then p_vendedor = p_escopo ->> 'vendedor'
           when 'manager' then p_manager = p_escopo ->> 'manager'
                               and (p_escopo ->> 'vendedor' is null or p_vendedor = p_escopo ->> 'vendedor')
           when 'admin' then (p_escopo ->> 'regiao' is null or p_escritorio = p_escopo ->> 'regiao')
                             and (p_escopo ->> 'manager' is null or p_manager = p_escopo ->> 'manager')
                             and (p_escopo ->> 'vendedor' is null or p_vendedor = p_escopo ->> 'vendedor')
           else false
         end
$$;

-- Trava o deal para escrita e confere a versão enviada pela tela (conflito de edição = GS409)
create or replace function core_travar_deal(p_opportunity_id text, p_versao timestamptz) returns core_deals
language plpgsql set search_path = public as $$
declare
  d      core_deals;
  v_quem text;
begin
  select * into d from core_deals where opportunity_id = p_opportunity_id for update;
  if not found then
    raise exception 'Deal % não encontrado.', p_opportunity_id using errcode = 'GS404';
  end if;
  if p_versao is not null and d.atualizado_em is distinct from p_versao then
    select nome_exibicao into v_quem from config_usuarios where id = d.atualizado_por;
    raise exception 'Este deal foi alterado por outra pessoa.' using
      errcode = 'GS409',
      detail = jsonb_build_object('alterado_por', coalesce(v_quem, 'sistema'), 'alterado_em', d.atualizado_em)::text;
  end if;
  return d;
end $$;

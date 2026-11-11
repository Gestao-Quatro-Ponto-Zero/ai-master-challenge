-- 0018_functions_acao.sql  [LOTE 2]
-- Cria as funções de escrita do que as pessoas registram (acao_ e config_tags):
--   ações (Liguei, Requalifiquei, Desisti) e desfazer;
--   comentários: postar, editar, apagar (remoção lógica) e restaurar;
--   tags: criar, arquivar, aplicar e remover (remoção lógica);
--   prioridades do dia: montar e listar a lista do dia, puxar mais, marcar ✓ (feita) ou ✗ (pulada).

-- Ações ------------------------------------------------------------------------------------------------

create or replace function acao_registrar(
  p_usuario_id     bigint,
  p_correlation_id uuid,
  p_opportunity_id text,
  p_acao           text,
  p_nota           text default null
) returns acao_registros
language plpgsql set search_path = public as $$
declare
  u        config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id);
  v_estagio text;
  r        acao_registros;
begin
  if p_acao not in ('liguei', 'requalifiquei', 'desisti') then
    raise exception 'Ação desconhecida.' using errcode = 'GS400';
  end if;
  select estagio into v_estagio from core_deals where opportunity_id = p_opportunity_id;
  if not found then
    raise exception 'Deal não encontrado.' using errcode = 'GS404';
  end if;
  if v_estagio not in ('Prospecting', 'Engaging') then
    raise exception 'Só é possível registrar ação em deal aberto.' using errcode = 'GS422';
  end if;
  insert into acao_registros (opportunity_id, usuario_id, papel, execucao_id, acao, nota, data_negocio)
  values (p_opportunity_id, u.id, u.papel, score_execucao_ativa(), p_acao, nullif(btrim(p_nota), ''), system_data_negocio())
  returning * into r;
  return r;
end $$;

create or replace function acao_desfazer(p_usuario_id bigint, p_correlation_id uuid, p_acao_id bigint) returns acao_registros
language plpgsql set search_path = public as $$
declare
  u config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id);
  r acao_registros;
begin
  select * into r from acao_registros where id = p_acao_id for update;
  if not found then
    raise exception 'Registro não encontrado.' using errcode = 'GS404';
  end if;
  if r.desfeita_em is not null then
    raise exception 'Este registro já foi desfeito.' using errcode = 'GS422';
  end if;
  if r.usuario_id <> u.id then
    raise exception 'Só quem registrou pode desfazer.' using errcode = 'GS403';
  end if;
  if r.criado_em < now() - make_interval(secs => coalesce(config_inteiro('segundos_desfazer'), 60)) then
    raise exception 'O prazo para desfazer passou.' using errcode = 'GS422';
  end if;
  update acao_registros set desfeita_em = now(), desfeita_por = u.id where id = p_acao_id returning * into r;
  return r;
end $$;

-- Comentários --------------------------------------------------------------------------------------------

create or replace function acao_comentar(p_usuario_id bigint, p_correlation_id uuid, p_opportunity_id text, p_texto text)
returns acao_comentarios
language plpgsql set search_path = public as $$
declare
  u config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id);
  c acao_comentarios;
begin
  if not exists (select 1 from core_deals where opportunity_id = p_opportunity_id) then
    raise exception 'Deal não encontrado.' using errcode = 'GS404';
  end if;
  if p_texto ~ '<[a-zA-Z/!]' then
    raise exception 'O comentário não pode ter HTML.' using errcode = 'GS400';
  end if;
  insert into acao_comentarios (opportunity_id, usuario_id, texto, data_negocio)
  values (p_opportunity_id, u.id, btrim(p_texto), system_data_negocio())
  returning * into c;
  return c;
end $$;

create or replace function acao_editar_comentario(p_usuario_id bigint, p_correlation_id uuid, p_comentario_id bigint, p_texto text)
returns acao_comentarios
language plpgsql set search_path = public as $$
declare
  u config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id);
  c acao_comentarios;
begin
  select * into c from acao_comentarios where id = p_comentario_id for update;
  if not found or c.removido_em is not null then
    raise exception 'Comentário não encontrado.' using errcode = 'GS404';
  end if;
  if c.usuario_id <> u.id then
    raise exception 'Só o autor edita o comentário.' using errcode = 'GS403';
  end if;
  if p_texto ~ '<[a-zA-Z/!]' then
    raise exception 'O comentário não pode ter HTML.' using errcode = 'GS400';
  end if;
  update acao_comentarios set texto = btrim(p_texto), editado_em = now() where id = p_comentario_id returning * into c;
  return c;
end $$;

-- "Apagar" na tela = remoção lógica: some da tela e da linha do tempo, fica no banco e na auditoria
create or replace function acao_remover_comentario(p_usuario_id bigint, p_correlation_id uuid, p_comentario_id bigint)
returns acao_comentarios
language plpgsql set search_path = public as $$
declare
  u config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id);
  c acao_comentarios;
begin
  select * into c from acao_comentarios where id = p_comentario_id for update;
  if not found or c.removido_em is not null then
    raise exception 'Comentário não encontrado.' using errcode = 'GS404';
  end if;
  if c.usuario_id <> u.id and u.papel not in ('manager', 'admin') then
    raise exception 'Só o autor, o manager ou o admin apagam o comentário.' using errcode = 'GS403';
  end if;
  update acao_comentarios set removido_em = now(), removido_por = u.id where id = p_comentario_id returning * into c;
  return c;
end $$;

-- Restaurar: "Desfazer" de quem apagou (janela curta) ou, a qualquer momento, o admin
create or replace function acao_restaurar_comentario(p_usuario_id bigint, p_correlation_id uuid, p_comentario_id bigint)
returns acao_comentarios
language plpgsql set search_path = public as $$
declare
  u config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id);
  c acao_comentarios;
begin
  select * into c from acao_comentarios where id = p_comentario_id for update;
  if not found or c.removido_em is null then
    raise exception 'Não há comentário apagado com este código.' using errcode = 'GS404';
  end if;
  if not (u.papel = 'admin'
          or (c.removido_por = u.id
              and c.removido_em > now() - make_interval(secs => coalesce(config_inteiro('segundos_desfazer'), 60)))) then
    raise exception 'O prazo para desfazer passou; peça ao admin.' using errcode = 'GS403';
  end if;
  update acao_comentarios set removido_em = null, removido_por = null where id = p_comentario_id returning * into c;
  return c;
end $$;

-- Tags -----------------------------------------------------------------------------------------------------

create or replace function config_criar_tag(p_usuario_id bigint, p_correlation_id uuid, p_nome text, p_cor_token text)
returns config_tags
language plpgsql set search_path = public as $$
declare
  u config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id);
  t config_tags;
begin
  perform system_exigir_papel(u, config_lista('papeis_criar_tag'));
  if exists (select 1 from config_tags where lower(btrim(nome)) = lower(btrim(p_nome))) then
    raise exception 'Já existe uma tag com esse nome.' using errcode = 'GS422';
  end if;
  insert into config_tags (nome, cor_token, criada_por) values (btrim(p_nome), p_cor_token, u.id) returning * into t;
  return t;
end $$;

create or replace function config_arquivar_tag(p_usuario_id bigint, p_correlation_id uuid, p_tag_id bigint, p_ativa boolean default false)
returns config_tags
language plpgsql set search_path = public as $$
declare
  u config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id);
  t config_tags;
begin
  perform system_exigir_papel(u, config_lista('papeis_criar_tag'));
  update config_tags set ativa = p_ativa where id = p_tag_id returning * into t;
  if not found then
    raise exception 'Tag não encontrada.' using errcode = 'GS404';
  end if;
  return t;
end $$;

create or replace function acao_aplicar_tag(p_usuario_id bigint, p_correlation_id uuid, p_opportunity_id text, p_tag_id bigint)
returns acao_deal_tags
language plpgsql set search_path = public as $$
declare
  u  config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id);
  dt acao_deal_tags;
begin
  if not exists (select 1 from core_deals where opportunity_id = p_opportunity_id) then
    raise exception 'Deal não encontrado.' using errcode = 'GS404';
  end if;
  if not exists (select 1 from config_tags where id = p_tag_id and ativa) then
    raise exception 'Tag não encontrada ou arquivada.' using errcode = 'GS404';
  end if;
  select * into dt from acao_deal_tags
   where opportunity_id = p_opportunity_id and tag_id = p_tag_id and removida_em is null;
  if found then
    return dt;                                  -- já aplicada: nada a fazer
  end if;
  insert into acao_deal_tags (opportunity_id, tag_id, usuario_id) values (p_opportunity_id, p_tag_id, u.id)
  returning * into dt;
  return dt;
end $$;

create or replace function acao_remover_tag(p_usuario_id bigint, p_correlation_id uuid, p_opportunity_id text, p_tag_id bigint)
returns acao_deal_tags
language plpgsql set search_path = public as $$
declare
  u  config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id);
  dt acao_deal_tags;
begin
  update acao_deal_tags set removida_em = now(), removida_por = u.id
   where opportunity_id = p_opportunity_id and tag_id = p_tag_id and removida_em is null
  returning * into dt;
  if not found then
    raise exception 'Este deal não tem essa tag.' using errcode = 'GS404';
  end if;
  return dt;
end $$;

-- Prioridades do dia ------------------------------------------------------------------------------------

-- Acrescenta até p_quantidade itens à lista do dia do usuário (dia real, no fuso configurado).
-- Vendedor: deals abertos dele, pela nota (sem nota: super hot, em risco, maior preço).
-- Manager e admin: deals do escopo em risco ou super hot, pelo maior valor.
-- Ficam fora: deals já na lista de hoje e deals com ação ou contato registrados hoje por este usuário.
create or replace function acao_montar_prioridades(p_usuario config_usuarios, p_quantidade integer) returns integer
language plpgsql set search_path = public as $$
declare
  v_dia      date := system_dia_real();
  v_max_pos  integer;
  v_inseridos integer;
begin
  select coalesce(max(posicao), 0) into v_max_pos from acao_prioridades where usuario_id = p_usuario.id and dia = v_dia;
  insert into acao_prioridades (usuario_id, dia, posicao, opportunity_id)
  select p_usuario.id, v_dia, v_max_pos + row_number() over (), x.opportunity_id
    from (
      select v.opportunity_id
        from core_deals_visao v
       where v.estagio in ('Prospecting', 'Engaging')
         and case p_usuario.papel
               when 'vendedor' then v.vendedor_nome = p_usuario.vendedor_nome
               when 'manager'  then v.manager_nome = p_usuario.manager_nome and v.icone in ('super_hot', 'em_risco')
               when 'admin'    then v.icone in ('super_hot', 'em_risco')
               else false
             end
         and not exists (select 1 from acao_prioridades p
                          where p.usuario_id = p_usuario.id and p.dia = v_dia and p.opportunity_id = v.opportunity_id)
         and not exists (select 1 from acao_registros r
                          where r.opportunity_id = v.opportunity_id and r.usuario_id = p_usuario.id
                            and r.desfeita_em is null
                            and (r.criado_em at time zone coalesce(config_texto('fuso_horario'), 'UTC'))::date = v_dia)
       order by
         case when p_usuario.papel = 'vendedor' then v.score end desc nulls last,
         case when p_usuario.papel = 'vendedor' then
           case v.icone when 'super_hot' then 1 when 'em_risco' then 2 else 3 end end asc,
         v.valor_esperado desc nulls last,
         v.score desc nulls last,
         v.opportunity_id
       limit greatest(p_quantidade, 0)
    ) x;
  get diagnostics v_inseridos = row_count;
  return v_inseridos;
end $$;

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
   where p.usuario_id = p_usuario_id and p.dia = system_dia_real()
   order by p.posicao
$$;

-- Lista do dia: na primeira chamada do dia monta a meta (padrão 10); depois só lista
create or replace function acao_prioridades_do_dia(p_usuario_id bigint, p_correlation_id uuid)
returns table (posicao smallint, opportunity_id text, nome text, vendedor_nome text, produto_nome text, conta_nome text,
               score smallint, faixa_nota text, icone text, valor_esperado integer, marcada text, pulado_dias_seguidos integer)
language plpgsql set search_path = public as $$
declare
  u config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id, false);
begin
  if not exists (select 1 from acao_prioridades where usuario_id = u.id and dia = system_dia_real()) then
    perform acao_montar_prioridades(u, coalesce(config_inteiro('meta_prioridades_dia'), 10));
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
  perform acao_montar_prioridades(u, least(greatest(p_quantidade, 1), 20));
  return query select * from acao_listar_prioridades(u.id);
end $$;

-- ✓ (feita) ou ✗ (pulada): grava em acao_registros e aparece na linha do tempo do lead; não muda o deal
create or replace function acao_marcar_prioridade(
  p_usuario_id     bigint,
  p_correlation_id uuid,
  p_opportunity_id text,
  p_resultado      text,
  p_nota           text default null
) returns acao_registros
language plpgsql set search_path = public as $$
declare
  u config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id);
  r acao_registros;
begin
  if p_resultado not in ('feita', 'pulada') then
    raise exception 'Use feita (✓) ou pulada (✗).' using errcode = 'GS400';
  end if;
  if not exists (select 1 from acao_prioridades
                  where usuario_id = u.id and dia = system_dia_real() and opportunity_id = p_opportunity_id) then
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
  insert into acao_registros (opportunity_id, usuario_id, papel, execucao_id, acao, nota, data_negocio)
  values (p_opportunity_id, u.id, u.papel, score_execucao_ativa(), 'prioridade_' || p_resultado,
          nullif(btrim(p_nota), ''), system_data_negocio())
  returning * into r;
  return r;
end $$;

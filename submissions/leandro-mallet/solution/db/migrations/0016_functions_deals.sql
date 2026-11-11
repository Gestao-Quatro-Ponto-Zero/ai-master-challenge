-- 0016_functions_deals.sql  [LOTE 2]
-- Cria as funções de escrita do deal (core_):
--   roteamento de lead novo (maior FIT no cohort, com teto de abertos e mínimo de casos),
--   cadastro, mudança de estágio (arrastar ou seletor), encerrar, reabrir, editar nome/empresa/contato,
--   salvar contato, reatribuir (manager e admin) e desfazer a última alteração (janela curta).
-- Toda função de escrita recebe p_usuario_id e p_correlation_id e passa pela auditoria (0008).

-- Candidatos ao roteamento: vendedores ativos (no time do manager, se informado), abertos e FIT no cohort
create or replace function core_rotear_candidatos(p_cohort text, p_manager text default null)
returns table (vendedor_nome text, abertos bigint, fit smallint, casos integer)
language sql stable set search_path = public as $$
  select v.nome,
         (select count(*) from core_deals d
           where d.vendedor_nome = v.nome and d.estagio in ('Prospecting', 'Engaging')),
         f.fit,
         f.casos
    from core_vendedores v
    join config_usuarios u on u.vendedor_nome = v.nome and u.ativo
    left join score_fit_vendedores f
           on f.vendedor_nome = v.nome and f.execucao_id = score_execucao_ativa() and f.cohort = p_cohort
   where p_manager is null or v.manager_nome = p_manager
$$;

-- Escolhe o vendedor de um lead novo. Regras, em ordem:
--   maior_fit     — maior FIT no cohort, com casos >= minimo_casos e abertos < teto_abertos;
--   menos_abertos — ninguém com FIT válido: o vendedor com menos deals abertos abaixo do teto;
--   todos_no_teto — todos no teto: o com menos abertos.
create or replace function core_rotear_lead(p_produto text, p_conta text, p_manager text default null) returns jsonb
language plpgsql stable set search_path = public as $$
declare
  v_cfg     jsonb := coalesce(config_valor('roteamento'), '{}'::jsonb);
  v_teto    integer := coalesce((v_cfg ->> 'teto_abertos')::integer, 200);
  v_min     integer := coalesce((v_cfg ->> 'minimo_casos')::integer, 10);
  v_cohort  text := score_chave_cohort(p_produto, p_conta);
  v_nome    text;
  v_fit     smallint;
  v_regra   text;
  v_cand    jsonb;
begin
  select c.vendedor_nome, c.fit into v_nome, v_fit
    from core_rotear_candidatos(v_cohort, p_manager) c
   where c.fit is not null and c.casos >= v_min and c.abertos < v_teto
   order by c.fit desc, c.abertos, c.vendedor_nome
   limit 1;
  v_regra := 'maior_fit';
  if v_nome is null then
    select c.vendedor_nome, c.fit into v_nome, v_fit
      from core_rotear_candidatos(v_cohort, p_manager) c
     where c.abertos < v_teto
     order by c.abertos, c.vendedor_nome
     limit 1;
    v_regra := 'menos_abertos';
  end if;
  if v_nome is null then
    select c.vendedor_nome, c.fit into v_nome, v_fit
      from core_rotear_candidatos(v_cohort, p_manager) c
     order by c.abertos, c.vendedor_nome
     limit 1;
    v_regra := 'todos_no_teto';
  end if;
  if v_nome is null then
    raise exception 'Nenhum vendedor ativo para receber o lead.' using errcode = 'GS422';
  end if;
  select coalesce(jsonb_agg(to_jsonb(x)), '[]'::jsonb) into v_cand
    from (select c.vendedor_nome, c.abertos, c.fit, c.casos
            from core_rotear_candidatos(v_cohort, p_manager) c
           order by c.fit desc nulls last, c.abertos, c.vendedor_nome
           limit 5) x;
  return jsonb_build_object('vendedor', v_nome, 'regra', v_regra, 'fit', v_fit, 'cohort', v_cohort,
                            'execucao_id', score_execucao_ativa(), 'candidatos', v_cand);
end $$;

-- Novo lead (cadastro). Sem vendedor informado: vendedor = ele mesmo; manager e admin = roteamento.
create or replace function core_criar_deal(
  p_usuario_id     bigint,
  p_correlation_id uuid,
  p_produto        text,
  p_conta          text default null,
  p_vendedor       text default null,
  p_estagio        text default 'Prospecting',
  p_data_abertura  date default null,
  p_nome           text default null,
  p_contato_id     bigint default null
) returns core_deals
language plpgsql set search_path = public as $$
declare
  u          config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id);
  v_vendedor text := nullif(btrim(p_vendedor), '');
  v_conta    text := nullif(btrim(p_conta), '');
  v_rota     jsonb;
  v_regra    text := 'escolhido';
  d          core_deals;
begin
  if p_estagio not in ('Prospecting', 'Engaging') then
    raise exception 'Um lead novo entra em Prospecção ou Em negociação.' using errcode = 'GS422';
  end if;
  if not exists (select 1 from core_produtos where nome = p_produto) then
    raise exception 'Produto não encontrado no catálogo.' using errcode = 'GS400';
  end if;
  if v_conta is not null and not exists (select 1 from core_contas where nome = v_conta) then
    raise exception 'Empresa não cadastrada.' using errcode = 'GS400';
  end if;
  if v_vendedor is null and u.papel = 'vendedor' then
    v_vendedor := u.vendedor_nome;
  end if;
  if v_vendedor is null then
    v_rota := core_rotear_lead(p_produto, v_conta, case when u.papel = 'manager' then u.manager_nome end);
    v_vendedor := v_rota ->> 'vendedor';
    v_regra := v_rota ->> 'regra';
  elsif not exists (select 1 from core_vendedores where nome = v_vendedor) then
    raise exception 'Vendedor não encontrado no time.' using errcode = 'GS400';
  end if;

  insert into core_deals (opportunity_id, nome, vendedor_nome, produto_nome, conta_nome, contato_id,
                          estagio, data_abertura, criado_em, criado_por)
  values (core_gerar_opportunity_id(),
          coalesce(nullif(btrim(p_nome), ''), core_nome_padrao(v_conta, p_produto)),
          v_vendedor, p_produto, v_conta, p_contato_id, p_estagio,
          case when p_estagio = 'Engaging' then coalesce(p_data_abertura, system_data_negocio()) end,
          now(), u.id)
  returning * into d;

  insert into system_roteamentos (opportunity_id, vendedor_nome, regra, execucao_id, cohort, fit, candidatos, usuario_id, correlation_id)
  values (d.opportunity_id, v_vendedor, v_regra, (v_rota ->> 'execucao_id')::bigint, v_rota ->> 'cohort',
          (v_rota ->> 'fit')::smallint, coalesce(v_rota -> 'candidatos', '[]'::jsonb), u.id, p_correlation_id);
  return d;
end $$;

-- Mudança de estágio: arrastar entre colunas ou seletor do cartão (ESPEC-TELAS 2.6)
create or replace function core_mudar_estagio(
  p_usuario_id      bigint,
  p_correlation_id  uuid,
  p_opportunity_id  text,
  p_versao          timestamptz,
  p_para            text,
  p_valor           integer default null,
  p_data_abertura   date default null,
  p_motivo          text default null,
  p_motivo_detalhe  text default null
) returns core_deals
language plpgsql set search_path = public as $$
declare
  u      config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id);
  d      core_deals;
  v_hoje date := system_data_negocio();
begin
  d := core_travar_deal(p_opportunity_id, p_versao);
  if d.estagio = p_para then
    raise exception 'O deal já está neste estágio.' using errcode = 'GS422';
  end if;

  if d.estagio = 'Prospecting' and p_para = 'Engaging' then
    update core_deals set estagio = 'Engaging', data_abertura = coalesce(p_data_abertura, v_hoje)
     where opportunity_id = p_opportunity_id;

  elsif d.estagio = 'Engaging' and p_para = 'Won' then
    if p_valor is null or p_valor <= 0 then
      raise exception 'Informe o valor de fechamento (maior que zero).' using errcode = 'GS400';
    end if;
    update core_deals
       set estagio = 'Won', close_date = v_hoje, close_value = p_valor, motivo_perda = null, motivo_perda_detalhe = null
     where opportunity_id = p_opportunity_id;

  elsif d.estagio in ('Prospecting', 'Engaging') and p_para = 'Lost' then
    if p_motivo is null and config_booleano('motivo_perda_obrigatorio') then
      raise exception 'Escolha o motivo da perda.' using errcode = 'GS400';
    end if;
    update core_deals
       set estagio = 'Lost', close_date = v_hoje, close_value = 0,
           motivo_perda = p_motivo, motivo_perda_detalhe = nullif(btrim(p_motivo_detalhe), '')
     where opportunity_id = p_opportunity_id;

  elsif d.estagio in ('Won', 'Lost') and p_para = 'Engaging' then
    perform system_exigir_papel(u, config_lista('papeis_reabrir'));
    update core_deals
       set estagio = 'Engaging', close_date = null, close_value = null, motivo_perda = null, motivo_perda_detalhe = null,
           data_abertura = coalesce(data_abertura, v_hoje)
     where opportunity_id = p_opportunity_id;

  else
    raise exception 'Mudar de % para % não é permitido.', core_rotulo_estagio(d.estagio), core_rotulo_estagio(p_para)
      using errcode = 'GS422';
  end if;

  select * into d from core_deals where opportunity_id = p_opportunity_id;
  return d;
end $$;

create or replace function core_encerrar_deal(
  p_usuario_id     bigint,
  p_correlation_id uuid,
  p_opportunity_id text,
  p_versao         timestamptz,
  p_resultado      text,                 -- 'ganho' ou 'perdido'
  p_valor          integer default null,
  p_motivo         text default null,
  p_motivo_detalhe text default null
) returns core_deals
language plpgsql set search_path = public as $$
begin
  if p_resultado not in ('ganho', 'perdido') then
    raise exception 'Resultado deve ser ganho ou perdido.' using errcode = 'GS400';
  end if;
  return core_mudar_estagio(p_usuario_id, p_correlation_id, p_opportunity_id, p_versao,
                            case p_resultado when 'ganho' then 'Won' else 'Lost' end,
                            p_valor, null, p_motivo, p_motivo_detalhe);
end $$;

create or replace function core_reabrir_deal(p_usuario_id bigint, p_correlation_id uuid, p_opportunity_id text, p_versao timestamptz)
returns core_deals
language sql set search_path = public as $$
  select core_mudar_estagio(p_usuario_id, p_correlation_id, p_opportunity_id, p_versao, 'Engaging')
$$;

-- Nome, empresa e contato principal
create or replace function core_atualizar_deal(
  p_usuario_id      bigint,
  p_correlation_id  uuid,
  p_opportunity_id  text,
  p_versao          timestamptz,
  p_nome            text default null,
  p_conta           text default null,
  p_contato_id      bigint default null,
  p_remover_contato boolean default false
) returns core_deals
language plpgsql set search_path = public as $$
declare
  u       config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id);
  d       core_deals;
  v_conta text := nullif(btrim(p_conta), '');
begin
  d := core_travar_deal(p_opportunity_id, p_versao);
  if v_conta is not null and not exists (select 1 from core_contas where nome = v_conta) then
    raise exception 'Empresa não cadastrada.' using errcode = 'GS400';
  end if;
  update core_deals
     set nome       = coalesce(nullif(btrim(p_nome), ''), nome),
         conta_nome = coalesce(v_conta, conta_nome),
         contato_id = case when p_remover_contato then null else coalesce(p_contato_id, contato_id) end
   where opportunity_id = p_opportunity_id
  returning * into d;
  return d;
end $$;

-- Adicionar ou editar um contato; opcionalmente, torná-lo o contato principal do deal
create or replace function core_salvar_contato(
  p_usuario_id     bigint,
  p_correlation_id uuid,
  p_contato_id     bigint,
  p_conta          text,
  p_nome           text,
  p_cargo          text default null,
  p_email          text default null,
  p_telefone       text default null,
  p_opportunity_id text default null,
  p_versao         timestamptz default null
) returns core_contatos
language plpgsql set search_path = public as $$
declare
  u config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id);
  c core_contatos;
  d core_deals;
begin
  if p_contato_id is null then
    insert into core_contatos (conta_nome, nome, cargo, email, telefone, criado_por)
    values (nullif(btrim(p_conta), ''), btrim(p_nome), nullif(btrim(p_cargo), ''),
            nullif(btrim(p_email), ''), nullif(btrim(p_telefone), ''), u.id)
    returning * into c;
  else
    update core_contatos
       set nome = btrim(p_nome),
           cargo = nullif(btrim(p_cargo), ''),
           email = nullif(btrim(p_email), ''),
           telefone = nullif(btrim(p_telefone), ''),
           conta_nome = coalesce(nullif(btrim(p_conta), ''), conta_nome)
     where id = p_contato_id and inativo_em is null
    returning * into c;
    if not found then
      raise exception 'Contato não encontrado.' using errcode = 'GS404';
    end if;
  end if;
  if p_opportunity_id is not null then
    d := core_travar_deal(p_opportunity_id, p_versao);
    update core_deals set contato_id = c.id where opportunity_id = p_opportunity_id;
  end if;
  return c;
end $$;

-- Passar o deal para outro vendedor (manager e admin); fica em acao_reatribuicoes e na auditoria
create or replace function core_reatribuir_deal(
  p_usuario_id     bigint,
  p_correlation_id uuid,
  p_opportunity_id text,
  p_versao         timestamptz,
  p_para_vendedor  text,
  p_motivo         text default null
) returns core_deals
language plpgsql set search_path = public as $$
declare
  u config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id);
  d core_deals;
begin
  perform system_exigir_papel(u, array['manager', 'admin']);
  d := core_travar_deal(p_opportunity_id, p_versao);
  if d.estagio not in ('Prospecting', 'Engaging') then
    raise exception 'Só deals abertos podem ser passados para outro vendedor.' using errcode = 'GS422';
  end if;
  if not exists (select 1 from core_vendedores where nome = p_para_vendedor) then
    raise exception 'Vendedor não encontrado no time.' using errcode = 'GS400';
  end if;
  if p_para_vendedor = d.vendedor_nome then
    raise exception 'O deal já é deste vendedor.' using errcode = 'GS422';
  end if;
  insert into acao_reatribuicoes (opportunity_id, de_vendedor, para_vendedor, usuario_id, motivo)
  values (p_opportunity_id, d.vendedor_nome, p_para_vendedor, u.id, nullif(btrim(p_motivo), ''));
  update core_deals set vendedor_nome = p_para_vendedor where opportunity_id = p_opportunity_id
  returning * into d;
  return d;
end $$;

-- "Desfazer" (janela curta, pelo próprio autor): devolve o deal ao estado anterior a uma alteração.
-- Cadastro desfeito vira Perdido com motivo "cadastro_desfeito" (não há DELETE).
create or replace function core_desfazer_alteracao(p_usuario_id bigint, p_correlation_id uuid, p_correlation_original uuid)
returns jsonb
language plpgsql set search_path = public as $$
declare
  u            config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id);
  a            record;
  v_restaurados integer := 0;
  v_pulados    integer := 0;
begin
  for a in
    select * from system_auditoria
     where correlation_id = p_correlation_original
       and usuario_id = u.id
       and tabela = 'core_deals'
       and criado_em > now() - make_interval(secs => coalesce(config_inteiro('segundos_desfazer'), 60))
     order by id desc
  loop
    if a.operacao = 'update' then
      update core_deals
         set estagio              = a.antes ->> 'estagio',
             data_abertura        = (a.antes ->> 'data_abertura')::date,
             close_date           = (a.antes ->> 'close_date')::date,
             close_value          = (a.antes ->> 'close_value')::integer,
             motivo_perda         = a.antes ->> 'motivo_perda',
             motivo_perda_detalhe = a.antes ->> 'motivo_perda_detalhe',
             nome                 = a.antes ->> 'nome',
             conta_nome           = a.antes ->> 'conta_nome',
             contato_id           = (a.antes ->> 'contato_id')::bigint,
             vendedor_nome        = a.antes ->> 'vendedor_nome'
       where opportunity_id = a.registro_id
         and atualizado_em = (a.depois ->> 'atualizado_em')::timestamptz;
    else
      update core_deals
         set estagio = 'Lost', close_date = system_data_negocio(), close_value = 0, motivo_perda = 'cadastro_desfeito'
       where opportunity_id = a.registro_id
         and estagio in ('Prospecting', 'Engaging')
         and atualizado_em = (a.depois ->> 'atualizado_em')::timestamptz;
    end if;
    if found then
      v_restaurados := v_restaurados + 1;
    else
      v_pulados := v_pulados + 1;
    end if;
  end loop;
  if v_restaurados + v_pulados = 0 then
    raise exception 'O prazo para desfazer passou.' using errcode = 'GS422';
  end if;
  return jsonb_build_object('restaurados', v_restaurados, 'pulados', v_pulados);
end $$;

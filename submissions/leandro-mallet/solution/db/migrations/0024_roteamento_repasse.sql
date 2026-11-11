-- 0024_roteamento_repasse.sql  [LOTE 2 — decisões 35 e 38]
-- Roteamento sem teto, repasse de lead e mini penalidade no roteamento.
--   * Sem teto de abertos (roteamento.teto_abertos = null). A distribuição equilibrada do recálculo de domingo
--     (cada lead para quem tem mais chance de fechá-lo, ponderando pela carga) é feita pelo score, em Python,
--     e gravada pelo papel de carga com core_repassar_deal.
--   * Repasse só quando a troca é clara: o lead entra no top N do novo vendedor, com FIT do novo >= fit_minimo
--     e no máximo max_abaixo_do_dono pontos abaixo do FIT do dono atual. No repasse por mudança de janela,
--     o lead está sem contato registrado.
--   * Quem perde lead por repasse de janela recebe uma penalidade temporária no roteamento de leads novos
--     (os pontos saem do FIT na escolha do vendedor; a nota dos deals não muda).
--   * FIT >= fit_furar_fila: lead novo que fura a fila nas prioridades (regra usada pelo score e pela lista).
-- Os números ficam em config_parametros. O que ainda não foi decidido fica null: sem penalidade e sem
-- limite de repasses até a regra do score fechar esses valores.

-- 1. Reatribuições ganham a origem e os números do repasse -----------------------------------------------

alter table acao_reatribuicoes
  add column origem      text not null default 'manager'
                         check (origem in ('manager', 'repasse_janela', 'redistribuicao')),
  add column execucao_id bigint references score_execucoes (id) on delete restrict,
  add column fit_dono    smallint check (fit_dono between 0 and 100),
  add column fit_novo    smallint check (fit_novo between 0 and 100),
  add column posicao_top smallint check (posicao_top > 0),
  add column faixa_heat  text check (char_length(faixa_heat) <= 40);
create index acao_reatribuicoes_execucao_id_idx on acao_reatribuicoes (execucao_id);
create index acao_reatribuicoes_origem_idx on acao_reatribuicoes (opportunity_id, origem);

-- 2. Penalidades no roteamento ---------------------------------------------------------------------------

create table system_penalidades (
  id               bigint generated always as identity primary key,
  vendedor_nome    text not null references core_vendedores (nome) on delete restrict,
  pontos           numeric(5, 2) not null check (pontos > 0),
  inicio           timestamptz not null default now(),
  fim              timestamptz not null,
  opportunity_id   text not null references core_deals (opportunity_id) on delete restrict,  -- deal de origem
  reatribuicao_id  bigint not null references acao_reatribuicoes (id) on delete restrict,
  correlation_id   uuid not null,
  criado_em        timestamptz not null default now(),
  constraint system_penalidades_periodo_chk check (fim > inicio)
);
create index system_penalidades_vendedor_fim_idx on system_penalidades (vendedor_nome, fim desc);
create index system_penalidades_opportunity_id_idx on system_penalidades (opportunity_id);
create index system_penalidades_reatribuicao_id_idx on system_penalidades (reatribuicao_id);
create trigger system_penalidades_auditar after insert or update on system_penalidades
  for each row execute function system_auditar('id');

-- 3. Parâmetros ------------------------------------------------------------------------------------------

select set_config('app.usuario_id', '1', true), set_config('app.correlation_id', '00000000-0000-4000-8000-000000000024', true);
update config_parametros
   set valor = jsonb_set(valor, '{teto_abertos}', 'null'::jsonb),
       descricao = 'Lead novo vai ao vendedor de maior FIT no cohort (menos a penalidade ativa), com o mínimo de casos; sem teto (decisão 38).',
       atualizado_em = now()
 where chave = 'roteamento';
insert into config_parametros (chave, valor, descricao) values
  ('fit_furar_fila', '75'::jsonb, 'FIT a partir do qual o lead novo fura a fila nas prioridades (decisão 35).'),
  ('repasse', '{"fit_minimo": 75, "max_abaixo_do_dono": 3, "top_n": 5, "max_repasses_por_lead": null}'::jsonb,
   'Repasse só com FIT do novo >= fit_minimo, até max_abaixo_do_dono pontos abaixo do dono e com o lead no top N do novo (decisão 38). max_repasses_por_lead null = sem limite.'),
  ('penalidade_roteamento', '{"pontos": null, "dias": null}'::jsonb,
   'Mini penalidade para quem perde lead por repasse de janela: pontos descontados do FIT no roteamento por N dias. null = sem penalidade até a regra fechar os números.')
on conflict do nothing;
select set_config('app.usuario_id', '', true), set_config('app.correlation_id', '', true);

-- 4. Roteamento com penalidade e sem teto -----------------------------------------------------------------

create or replace function core_penalidade_ativa(p_vendedor text) returns numeric
language sql stable set search_path = public as $$
  select coalesce(sum(pontos), 0) from system_penalidades
   where vendedor_nome = p_vendedor and now() >= inicio and now() < fim
$$;

create or replace function core_rotear_lead(p_produto text, p_conta text, p_manager text default null) returns jsonb
language plpgsql stable set search_path = public as $$
declare
  v_cfg     jsonb := coalesce(config_valor('roteamento'), '{}'::jsonb);
  v_teto    integer := (v_cfg ->> 'teto_abertos')::integer;          -- null = sem teto
  v_min     integer := coalesce((v_cfg ->> 'minimo_casos')::integer, 10);
  v_cohort  text := score_chave_cohort(p_produto, p_conta);
  v_nome    text;
  v_fit     smallint;
  v_regra   text;
  v_cand    jsonb;
begin
  select c.vendedor_nome, c.fit into v_nome, v_fit
    from core_rotear_candidatos(v_cohort, p_manager) c
   where c.fit is not null and c.casos >= v_min and (v_teto is null or c.abertos < v_teto)
   order by c.fit - core_penalidade_ativa(c.vendedor_nome) desc, c.abertos, c.vendedor_nome
   limit 1;
  v_regra := 'maior_fit';
  if v_nome is null then
    select c.vendedor_nome, c.fit into v_nome, v_fit
      from core_rotear_candidatos(v_cohort, p_manager) c
     where v_teto is null or c.abertos < v_teto
     order by c.abertos, core_penalidade_ativa(c.vendedor_nome), c.vendedor_nome
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
    from (select c.vendedor_nome, c.abertos, c.fit, c.casos, core_penalidade_ativa(c.vendedor_nome) as penalidade
            from core_rotear_candidatos(v_cohort, p_manager) c
           order by c.fit - core_penalidade_ativa(c.vendedor_nome) desc nulls last, c.abertos, c.vendedor_nome
           limit 5) x;
  return jsonb_build_object('vendedor', v_nome, 'regra', v_regra, 'fit', v_fit, 'cohort', v_cohort,
                            'execucao_id', score_execucao_ativa(), 'candidatos', v_cand);
end $$;

-- 5. Repasse (só o papel de carga, no recálculo do score) ---------------------------------------------------

create or replace function core_repassar_deal(
  p_correlation_id uuid,
  p_opportunity_id text,
  p_para_vendedor  text,
  p_origem         text,          -- 'repasse_janela' ou 'redistribuicao'
  p_execucao_id    bigint,
  p_fit_dono       smallint,
  p_fit_novo       smallint,
  p_posicao_top    smallint,
  p_faixa_heat     text default null
) returns acao_reatribuicoes
language plpgsql set search_path = public as $$
declare
  u        config_usuarios := system_iniciar_contexto_sistema(p_correlation_id);   -- recusa o app (GS403)
  d        core_deals;
  r        acao_reatribuicoes;
  v_rep    jsonb := coalesce(config_valor('repasse'), '{}'::jsonb);
  v_pen    jsonb := coalesce(config_valor('penalidade_roteamento'), '{}'::jsonb);
  v_qtd    integer;
begin
  if p_origem not in ('repasse_janela', 'redistribuicao') then
    raise exception 'Origem do repasse inválida.' using errcode = 'GS400';
  end if;
  select * into d from core_deals where opportunity_id = p_opportunity_id for update;
  if not found then
    raise exception 'Deal % não encontrado.', p_opportunity_id using errcode = 'GS404';
  end if;
  if d.estagio not in ('Prospecting', 'Engaging') then
    raise exception 'Só deal aberto é repassado.' using errcode = 'GS422';
  end if;
  if d.vendedor_nome = p_para_vendedor then
    raise exception 'O lead já é deste vendedor.' using errcode = 'GS422';
  end if;
  if not exists (select 1 from core_vendedores v join config_usuarios cu on cu.vendedor_nome = v.nome and cu.ativo
                  where v.nome = p_para_vendedor) then
    raise exception 'Vendedor % não está ativo.', p_para_vendedor using errcode = 'GS422';
  end if;
  -- travas da decisão 38 (números em config_parametros.repasse)
  if p_fit_novo is null or p_fit_novo < coalesce((v_rep ->> 'fit_minimo')::integer, 75) then
    raise exception 'FIT do novo vendedor abaixo do mínimo para repasse.' using errcode = 'GS422';
  end if;
  if p_fit_dono is not null and p_fit_novo < p_fit_dono - coalesce((v_rep ->> 'max_abaixo_do_dono')::integer, 3) then
    raise exception 'FIT do novo vendedor muito abaixo do dono atual.' using errcode = 'GS422';
  end if;
  if p_posicao_top is null or p_posicao_top > coalesce((v_rep ->> 'top_n')::integer, 5) then
    raise exception 'O lead não entra no top do novo vendedor.' using errcode = 'GS422';
  end if;
  if p_origem = 'repasse_janela' and d.ultimo_contato_em is not null then
    raise exception 'Lead com contato registrado não é repassado por mudança de janela.' using errcode = 'GS422';
  end if;
  if (v_rep ->> 'max_repasses_por_lead') is not null then
    select count(*) into v_qtd from acao_reatribuicoes
     where opportunity_id = p_opportunity_id and origem in ('repasse_janela', 'redistribuicao');
    if v_qtd >= (v_rep ->> 'max_repasses_por_lead')::integer then
      raise exception 'Este lead já atingiu o máximo de repasses.' using errcode = 'GS422';
    end if;
  end if;

  update core_deals set vendedor_nome = p_para_vendedor where opportunity_id = p_opportunity_id;
  insert into acao_reatribuicoes (opportunity_id, de_vendedor, para_vendedor, usuario_id, motivo, origem,
                                  execucao_id, fit_dono, fit_novo, posicao_top, faixa_heat)
  values (p_opportunity_id, d.vendedor_nome, p_para_vendedor, u.id,
          case p_origem when 'repasse_janela' then 'Lead sem contato mudou de faixa.' else 'Redistribuição do recálculo.' end,
          p_origem, p_execucao_id, p_fit_dono, p_fit_novo, p_posicao_top, p_faixa_heat)
  returning * into r;

  if p_origem = 'repasse_janela' and (v_pen ->> 'pontos') is not null and (v_pen ->> 'dias') is not null then
    insert into system_penalidades (vendedor_nome, pontos, fim, opportunity_id, reatribuicao_id, correlation_id)
    values (d.vendedor_nome, (v_pen ->> 'pontos')::numeric, now() + make_interval(days => (v_pen ->> 'dias')::integer),
            p_opportunity_id, r.id, p_correlation_id);
  end if;
  return r;
end $$;

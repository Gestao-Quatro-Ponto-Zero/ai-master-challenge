-- 0007_views: fontes de leitura das telas.
--   score_deals_atuais  notas da execução ativa (config_parametros.execucao_ativa)
--   core_deals_visao    o deal pronto para Pipeline e Leads (equipe, perfil, nota, faixa, ícone, tags, comentários)
--   core_painel_janelas números do Painel por vendedor nas janelas hoje, 30 dias e 30 dias antes
-- Todas com security_invoker: valem as mesmas permissões das tabelas (só a service role lê).
-- Cortes de ícone e faixas de nota vêm de config_parametros (icone_cortes, faixas_nota, dias_sem_contato_risco).

create view score_deals_atuais with (security_invoker = true) as
select s.execucao_id,
       s.opportunity_id,
       s.vendedor_nome,
       s.score,
       s.fit,
       s.heat,
       s.acao_sugerida,
       s.dias_no_pipeline,
       s.valor_esperado,
       s.marcadores,
       e.gerado_em,
       e.reference_date,
       e.versao
  from score_deals s
  join score_execucoes e on e.id = s.execucao_id
 where s.execucao_id = config_execucao_ativa();

create view core_deals_visao with (security_invoker = true) as
with p as (
  select config_data_negocio() as hoje,
         coalesce(config_valor('icone_cortes'), '{}'::jsonb) as ic,
         coalesce(config_valor('faixas_nota'), '{}'::jsonb) as fx,
         config_inteiro('dias_sem_contato_risco', 14) as dias_contato_risco,
         coalesce((config_valor('risco_por_contato_ativo') #>> '{}')::boolean, false) as risco_contato,
         (select gerado_em from score_execucoes where id = config_execucao_ativa()) as nota_gerada_em
),
base as (
  select d.*,
         v.manager_nome,
         m.escritorio_nome as regiao,
         pr.serie,
         pr.preco as preco_tabela,
         c.setor,
         c.porte,
         c.pais,
         ct.nome as contato_nome,
         ct.cargo as contato_cargo,
         ct.email as contato_email,
         ct.telefone as contato_telefone,
         s.score,
         s.fit,
         s.heat,
         s.acao_sugerida,
         s.marcadores,
         s.valor_esperado as valor_esperado_nota,
         case when d.estagio in ('Prospecting', 'Engaging') and d.data_abertura is not null
              then p.hoje - d.data_abertura end as dias_abertura,
         p.hoje - d.ultimo_contato_em as dias_sem_contato,
         p.ic, p.fx, p.dias_contato_risco, p.risco_contato, p.nota_gerada_em
    from core_deals d
    join core_vendedores v on v.nome = d.vendedor_nome
    join core_managers m on m.nome = v.manager_nome
    join core_produtos pr on pr.nome = d.produto_nome
    left join core_contas c on c.nome = d.conta_nome
    left join core_contatos ct on ct.id = d.contato_id
    left join score_deals_atuais s on s.opportunity_id = d.opportunity_id
   cross join p
)
select b.opportunity_id,
       b.nome,
       b.estagio,
       b.estagio in ('Prospecting', 'Engaging') as aberto,
       b.vendedor_nome,
       b.manager_nome,
       b.regiao,
       b.produto_nome,
       b.serie,
       b.preco_tabela,
       b.conta_nome,
       b.setor,
       b.porte,
       b.pais,
       b.contato_id,
       b.contato_nome,
       b.contato_cargo,
       b.contato_email,
       b.contato_telefone,
       b.engage_date,
       b.data_abertura,
       b.dias_abertura,
       b.ultimo_contato_em,
       b.dias_sem_contato,
       b.close_date,
       b.close_value,
       b.motivo_perda,
       b.motivo_perda_detalhe,
       b.score,
       b.fit,
       b.heat,
       case when b.score is null then null
            when b.score >= coalesce((b.fx->>'alta_min')::integer, 70) then 'alta'
            when b.score >= coalesce((b.fx->>'media_min')::integer, 40) then 'media'
            else 'baixa' end as faixa_nota,
       b.acao_sugerida,
       coalesce(b.marcadores, '{}') as marcadores,
       case when b.estagio in ('Prospecting', 'Engaging')
            then coalesce(b.valor_esperado_nota, b.preco_tabela) end as valor_esperado,
       (b.estagio in ('Prospecting', 'Engaging') and b.valor_esperado_nota is null) as valor_pelo_preco_tabela,
       case when b.estagio <> 'Engaging' or b.dias_abertura is null then null
            when b.dias_abertura > coalesce((b.ic->>'esfriou_dias_apos')::integer, 138) then 'esfriou'
            when b.dias_abertura between coalesce((b.ic->>'risco_dias_min')::integer, 107)
                                     and coalesce((b.ic->>'risco_dias_max')::integer, 138) then 'em_risco'
            when b.risco_contato and b.dias_sem_contato >= b.dias_contato_risco then 'em_risco'
            when b.dias_abertura between coalesce((b.ic->>'super_hot_dias_min')::integer, 15)
                                     and coalesce((b.ic->>'super_hot_dias_max')::integer, 106)
                 and b.preco_tabela >= coalesce((b.ic->>'super_hot_preco_min')::integer, 3000) then 'super_hot'
            end as icone,
       coalesce(tg.tags, '[]'::jsonb) as tags,
       coalesce(cm.comentarios, 0) as comentarios,
       (b.nota_gerada_em is not null and b.atualizado_em > b.nota_gerada_em) as atualizado_depois_da_nota,
       b.criado_em,
       b.criado_por,
       b.importacao_id,
       b.atualizado_em,
       b.atualizado_por
  from base b
  left join lateral (
    select jsonb_agg(jsonb_build_object('id', t.id, 'nome', t.nome, 'cor_token', t.cor_token) order by dt.criado_em) as tags
      from acao_deal_tags dt
      join config_tags t on t.id = dt.tag_id
     where dt.opportunity_id = b.opportunity_id and dt.removida_em is null
  ) tg on true
  left join lateral (
    select count(*)::integer as comentarios
      from acao_comentarios co
     where co.opportunity_id = b.opportunity_id and co.removido_em is null
  ) cm on true;

create view core_painel_janelas with (security_invoker = true) as
with p as (select config_data_negocio() as hoje)
select v.vendedor_nome,
       v.manager_nome,
       v.regiao,
       count(*) filter (where v.data_abertura = p.hoje)                                        as leads_novos_hoje,
       count(*) filter (where v.data_abertura between p.hoje - 29 and p.hoje)                  as leads_novos_30d,
       count(*) filter (where v.data_abertura between p.hoje - 59 and p.hoje - 30)             as leads_novos_30d_antes,
       count(*) filter (where v.estagio = 'Engaging')                                          as em_negociacao_qtd,
       coalesce(sum(v.valor_esperado) filter (where v.estagio = 'Engaging'), 0)                as em_negociacao_valor,
       count(*) filter (where v.estagio = 'Won' and v.close_date = p.hoje)                     as ganhos_hoje_qtd,
       coalesce(sum(v.close_value) filter (where v.estagio = 'Won' and v.close_date = p.hoje), 0) as ganhos_hoje_valor,
       count(*) filter (where v.estagio = 'Won' and v.close_date between p.hoje - 29 and p.hoje) as ganhos_30d_qtd,
       coalesce(sum(v.close_value) filter (where v.estagio = 'Won' and v.close_date between p.hoje - 29 and p.hoje), 0) as ganhos_30d_valor,
       count(*) filter (where v.estagio = 'Won' and v.close_date between p.hoje - 59 and p.hoje - 30) as ganhos_30d_antes_qtd,
       coalesce(sum(v.close_value) filter (where v.estagio = 'Won' and v.close_date between p.hoje - 59 and p.hoje - 30), 0) as ganhos_30d_antes_valor,
       count(*) filter (where v.estagio = 'Lost' and v.close_date between p.hoje - 29 and p.hoje) as perdidos_30d_qtd,
       count(*) filter (where v.estagio = 'Lost' and v.close_date between p.hoje - 59 and p.hoje - 30) as perdidos_30d_antes_qtd,
       coalesce(sum(v.valor_esperado) filter (where v.aberto), 0)                              as pipeline_aberto_valor,
       bool_or(v.valor_pelo_preco_tabela)                                                      as pipeline_pelo_preco_tabela,
       count(*)                                                                                as total_leads,
       count(*) filter (where v.icone = 'em_risco')                                            as em_risco_qtd,
       count(*) filter (where v.icone = 'esfriou')                                             as esfriou_qtd,
       p.hoje                                                                                  as data_referencia
  from core_deals_visao v
 cross join p
 group by v.vendedor_nome, v.manager_nome, v.regiao, p.hoje;

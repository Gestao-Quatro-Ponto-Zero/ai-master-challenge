-- 0014_views.sql  [LOTE 2]
-- Cria as views de leitura das telas:
--   score_deals_atuais  — notas da execução ativa;
--   core_deals_visao    — o deal completo para Pipeline e Leads (nome, contato, equipe, perfil, nota, faixa,
--                         ícone, tags, comentários, "atualizado depois da nota");
--   core_painel_janelas — o deal com as marcas de janela do Painel (hoje, 30 dias, 30 dias antes).
-- Todas com security_invoker: a view respeita o RLS de quem consulta (sem isso, ela leria como dona).

create view score_deals_atuais with (security_invoker = true) as
select s.*
  from score_deals s
 where s.execucao_id = score_execucao_ativa();

create view core_deals_visao with (security_invoker = true) as
select
  d.opportunity_id,
  d.nome,
  d.estagio,
  d.vendedor_nome,
  v.manager_nome,
  m.escritorio_nome,
  d.produto_nome,
  p.serie,
  p.preco,
  d.conta_nome,
  c.setor,
  c.porte,
  d.contato_id,
  ct.nome  as contato_nome,
  ct.cargo as contato_cargo,
  d.data_abertura,
  case when d.data_abertura is not null and d.estagio in ('Prospecting', 'Engaging')
       then system_data_negocio() - d.data_abertura end                          as dias_desde_abertura,
  coalesce(d.ultimo_contato_em,
           case when config_booleano('usar_abertura_como_primeiro_contato') and d.estagio = 'Engaging'
                then d.data_abertura end)                                           as ultimo_contato,
  d.ultimo_contato_em                                                               as ultimo_contato_crm,
  d.close_date,
  d.close_value,
  d.motivo_perda,
  s.execucao_id,
  s.fit,
  s.heat,
  s.bonus,
  s.score,
  core_faixa_nota(s.score)                                                          as faixa_nota,
  s.acao_sugerida,
  coalesce(s.marcadores, '{}'::text[])                                              as marcadores,
  case when d.estagio in ('Prospecting', 'Engaging') then coalesce(s.valor_esperado, p.preco) end as valor_esperado,
  (d.estagio in ('Prospecting', 'Engaging') and s.valor_esperado is null)            as valor_pelo_preco_de_tabela,
  core_icone(d.estagio,
             case when d.data_abertura is not null then system_data_negocio() - d.data_abertura end,
             p.preco,
             case when d.ultimo_contato_em is not null then system_data_negocio() - d.ultimo_contato_em end) as icone,
  coalesce(t.tags, '{}'::text[])                                                    as tags,
  coalesce(k.qtd, 0)                                                                as qtd_comentarios,
  (e.gerado_em is not null and d.atualizado_em > e.gerado_em)                       as atualizado_depois_da_nota,
  d.criado_em,
  d.importacao_id,
  d.atualizado_em,
  d.atualizado_por
from core_deals d
join core_vendedores v on v.nome = d.vendedor_nome
join core_managers m   on m.nome = v.manager_nome
join core_produtos p   on p.nome = d.produto_nome
left join core_contas c    on c.nome = d.conta_nome
left join core_contatos ct on ct.id = d.contato_id
left join score_deals s    on s.opportunity_id = d.opportunity_id and s.execucao_id = score_execucao_ativa()
left join score_execucoes e on e.id = s.execucao_id
left join lateral (
  select array_agg(tg.nome order by tg.nome) as tags
    from acao_deal_tags dt
    join config_tags tg on tg.id = dt.tag_id
   where dt.opportunity_id = d.opportunity_id and dt.removida_em is null
) t on true
left join lateral (
  select count(*) as qtd
    from acao_comentarios cm
   where cm.opportunity_id = d.opportunity_id and cm.removido_em is null
) k on true;

create view core_painel_janelas with (security_invoker = true) as
select
  v.opportunity_id,
  v.vendedor_nome,
  v.manager_nome,
  v.escritorio_nome,
  v.estagio,
  v.icone,
  v.preco,
  v.valor_esperado,
  v.valor_pelo_preco_de_tabela,
  v.close_value,
  coalesce(v.data_abertura = h.hoje, false)                                              as abriu_hoje,
  coalesce(v.data_abertura between h.hoje - (h.j - 1) and h.hoje, false)                 as abriu_janela,
  coalesce(v.data_abertura between h.hoje - (2 * h.j - 1) and h.hoje - h.j, false)       as abriu_janela_anterior,
  coalesce(v.close_date = h.hoje, false)                                                 as fechou_hoje,
  coalesce(v.close_date between h.hoje - (h.j - 1) and h.hoje, false)                    as fechou_janela,
  coalesce(v.close_date between h.hoje - (2 * h.j - 1) and h.hoje - h.j, false)          as fechou_janela_anterior
from core_deals_visao v
cross join (select system_data_negocio() as hoje,
                   coalesce(config_inteiro('janela_painel_dias'), 30) as j) h;

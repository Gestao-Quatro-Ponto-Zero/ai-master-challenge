-- 0006_config_inicial.sql  [LOTE 1]
-- Usuários 'sistema' (1) e 'admin' (2) e os parâmetros do CRM. Assinado pelo usuário 'sistema' (auditado).
-- GERADO por db/gerar_seed.py. Não editar à mão. Os usuários do time vêm do seed (seed/seed_dataset.sql).

select set_config('app.usuario_id', '1', false), set_config('app.correlation_id', '00000000-0000-4000-8000-000000000006', false),
       set_config('app.lote_id', '', false);

insert into config_usuarios (id, papel, nome_exibicao) values
  (1, 'sistema', 'Sistema'),
  (2, 'admin', 'Admin')
on conflict do nothing;
select setval(pg_get_serial_sequence('config_usuarios', 'id'), greatest(2, (select max(id) from config_usuarios)));

insert into config_parametros (chave, valor, descricao) values
  ('modo_demonstracao', 'true'::jsonb, 'Relógio do CRM: com true, ''hoje'' é a data de referência (P6).'),
  ('data_referencia', '"2017-12-31"'::jsonb, 'Último dia com registro no dataset; ''hoje'' no modo demonstração.'),
  ('fuso_horario', '"America/Sao_Paulo"'::jsonb, 'Fuso do dia real (lista de prioridades e prazos).'),
  ('execucao_ativa', 'null'::jsonb, 'Execução de score em uso; definida por score_ativar_execucao.'),
  ('pesos_score', '{"fit": 0.7, "heat": 0.3}'::jsonb, 'SCORE = 0,70 × FIT + 0,30 × HEAT (+ bonus, lote 2); a fórmula fica no score.'),
  ('cohort_dimensoes', '["produto"]'::jsonb, 'Dimensões da chave de cohort usada no roteamento; definidas pelo score.'),
  ('roteamento', '{"teto_abertos": 200, "minimo_casos": 10}'::jsonb, 'Lead novo vai ao vendedor de maior FIT no cohort, abaixo do teto de abertos e com o mínimo de casos.'),
  ('faixas_nota', '{"alta": 70, "media": 40}'::jsonb, 'Cortes das faixas da nota (barra do cartão).'),
  ('icone_cortes', '{"dias_min_quente": 15, "dias_max_quente": 106, "dias_max_risco": 138, "preco_min_quente": 3000}'::jsonb, 'Cortes dos ícones super hot, em risco e esfriou (ESPEC-TELAS 2.4).'),
  ('dias_sem_contato_risco', '14'::jsonb, 'Dias sem contato registrado no CRM que também marcam risco.'),
  ('acoes_contato', '["liguei", "requalifiquei"]'::jsonb, 'Ações que contam como contato (P5).'),
  ('usar_abertura_como_primeiro_contato', 'false'::jsonb, 'P5: usar a abertura como primeiro contato dos deals em negociação.'),
  ('motivo_perda_obrigatorio', 'false'::jsonb, 'P14: exigir motivo ao perder ou descartar.'),
  ('limite_escritas_por_minuto', '30'::jsonb, 'Limite de escritas por usuário por minuto (BE-06).'),
  ('limite_lote', '500'::jsonb, 'Máximo de deals por ação em lote.'),
  ('limite_linhas_importacao', '10000'::jsonb, 'Máximo de linhas por arquivo importado.'),
  ('max_tags_por_deal', '10'::jsonb, 'Máximo de tags ativas por deal.'),
  ('segundos_desfazer', '60'::jsonb, 'Prazo do ''Desfazer'' no servidor (a tela mostra 10 s).'),
  ('horas_desfazer_lote', '24'::jsonb, 'Prazo do ''Desfazer este lote''.'),
  ('prioridades_visiveis', '5'::jsonb, 'Itens visíveis no bloco Prioridades do dia.'),
  ('meta_prioridades_dia', '10'::jsonb, 'Meta diária de itens nas Prioridades do dia.'),
  ('dias_pulado_alerta', '3'::jsonb, 'Dias seguidos pulado até perguntar ''Requalificar ou encerrar?''.'),
  ('janela_painel_dias', '30'::jsonb, 'Janela dos cartões do Painel.'),
  ('papeis_importacao', '["manager", "admin"]'::jsonb, 'Quem importa CSV.'),
  ('papeis_criar_tag', '["manager", "admin"]'::jsonb, 'Quem cria e arquiva tags (P7).'),
  ('papeis_lote', '["vendedor", "manager", "admin"]'::jsonb, 'Quem usa ações em lote (P8).'),
  ('papeis_reabrir', '["manager", "admin"]'::jsonb, 'Quem reabre deal encerrado (P10).')
on conflict do nothing;

select set_config('app.usuario_id', '', false), set_config('app.correlation_id', '', false);

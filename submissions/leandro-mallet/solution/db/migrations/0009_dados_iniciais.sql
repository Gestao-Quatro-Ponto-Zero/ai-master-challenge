-- 0009_dados_iniciais: parâmetros, motivos de perda, time do dataset e config_usuarios.
-- GERADO por db/gerar_dados_iniciais.py a partir de data/clean/sales_teams.csv. Não editar à mão.
-- 3 escritórios, 6 managers, 35 vendedores; 43 usuários (1 sistema, 1 admin, 6 managers, 35 vendedores).
-- Idempotente (on conflict do nothing). Assinado pelo usuário sistema (id 1) para a auditoria.
-- Contas, produtos, deals e notas vêm da carga em Python (on conflict do nothing), fora das migrations.

select set_config('app.usuario_id', '1', false);
select set_config('app.correlation_id', '00000000-0000-4000-8000-000000000009', false);
select set_config('app.lote_id', '', false);

-- usuários sem vínculo com o time primeiro (a auditoria precisa do usuário sistema)
insert into config_usuarios (id, papel, nome_exibicao, vendedor_nome, manager_nome) overriding system value values
  (1, 'sistema', 'Sistema (cargas e rodadas do score)', null, null),
  (2, 'admin', 'Administrador', null, null)
on conflict (id) do nothing;

insert into core_escritorios (nome) values
  ('Central'),
  ('East'),
  ('West')
on conflict (nome) do nothing;

insert into core_managers (nome, escritorio_nome) values
  ('Cara Losch', 'East'),
  ('Celia Rouche', 'West'),
  ('Dustin Brinkmann', 'Central'),
  ('Melvin Marxen', 'Central'),
  ('Rocco Neubert', 'East'),
  ('Summer Sewald', 'West')
on conflict (nome) do nothing;

insert into core_vendedores (nome, manager_nome) values
  ('Anna Snelling', 'Dustin Brinkmann'),
  ('Boris Faz', 'Rocco Neubert'),
  ('Carl Lin', 'Summer Sewald'),
  ('Carol Thompson', 'Celia Rouche'),
  ('Cassey Cress', 'Rocco Neubert'),
  ('Cecily Lampkin', 'Dustin Brinkmann'),
  ('Corliss Cosme', 'Cara Losch'),
  ('Daniell Hammack', 'Rocco Neubert'),
  ('Darcel Schlecht', 'Melvin Marxen'),
  ('Donn Cantrell', 'Rocco Neubert'),
  ('Elease Gluck', 'Celia Rouche'),
  ('Elizabeth Anderson', 'Cara Losch'),
  ('Garret Kinder', 'Cara Losch'),
  ('Gladys Colclough', 'Melvin Marxen'),
  ('Hayden Neloms', 'Celia Rouche'),
  ('James Ascencio', 'Summer Sewald'),
  ('Jonathan Berthelot', 'Melvin Marxen'),
  ('Kami Bicknell', 'Summer Sewald'),
  ('Kary Hendrixson', 'Summer Sewald'),
  ('Lajuana Vencill', 'Dustin Brinkmann'),
  ('Markita Hansen', 'Celia Rouche'),
  ('Marty Freudenburg', 'Melvin Marxen'),
  ('Maureen Marcano', 'Summer Sewald'),
  ('Mei-Mei Johns', 'Melvin Marxen'),
  ('Moses Frase', 'Dustin Brinkmann'),
  ('Natalya Ivanova', 'Rocco Neubert'),
  ('Niesha Huffines', 'Melvin Marxen'),
  ('Reed Clapper', 'Rocco Neubert'),
  ('Rosalina Dieter', 'Celia Rouche'),
  ('Rosie Papadopoulos', 'Cara Losch'),
  ('Versie Hillebrand', 'Dustin Brinkmann'),
  ('Vicki Laflamme', 'Celia Rouche'),
  ('Violet Mclelland', 'Cara Losch'),
  ('Wilburn Farren', 'Cara Losch'),
  ('Zane Levy', 'Summer Sewald')
on conflict (nome) do nothing;

insert into config_usuarios (id, papel, nome_exibicao, vendedor_nome, manager_nome) overriding system value values
  (3, 'manager', 'Cara Losch', null, 'Cara Losch'),
  (4, 'manager', 'Celia Rouche', null, 'Celia Rouche'),
  (5, 'manager', 'Dustin Brinkmann', null, 'Dustin Brinkmann'),
  (6, 'manager', 'Melvin Marxen', null, 'Melvin Marxen'),
  (7, 'manager', 'Rocco Neubert', null, 'Rocco Neubert'),
  (8, 'manager', 'Summer Sewald', null, 'Summer Sewald'),
  (9, 'vendedor', 'Anna Snelling', 'Anna Snelling', null),
  (10, 'vendedor', 'Boris Faz', 'Boris Faz', null),
  (11, 'vendedor', 'Carl Lin', 'Carl Lin', null),
  (12, 'vendedor', 'Carol Thompson', 'Carol Thompson', null),
  (13, 'vendedor', 'Cassey Cress', 'Cassey Cress', null),
  (14, 'vendedor', 'Cecily Lampkin', 'Cecily Lampkin', null),
  (15, 'vendedor', 'Corliss Cosme', 'Corliss Cosme', null),
  (16, 'vendedor', 'Daniell Hammack', 'Daniell Hammack', null),
  (17, 'vendedor', 'Darcel Schlecht', 'Darcel Schlecht', null),
  (18, 'vendedor', 'Donn Cantrell', 'Donn Cantrell', null),
  (19, 'vendedor', 'Elease Gluck', 'Elease Gluck', null),
  (20, 'vendedor', 'Elizabeth Anderson', 'Elizabeth Anderson', null),
  (21, 'vendedor', 'Garret Kinder', 'Garret Kinder', null),
  (22, 'vendedor', 'Gladys Colclough', 'Gladys Colclough', null),
  (23, 'vendedor', 'Hayden Neloms', 'Hayden Neloms', null),
  (24, 'vendedor', 'James Ascencio', 'James Ascencio', null),
  (25, 'vendedor', 'Jonathan Berthelot', 'Jonathan Berthelot', null),
  (26, 'vendedor', 'Kami Bicknell', 'Kami Bicknell', null),
  (27, 'vendedor', 'Kary Hendrixson', 'Kary Hendrixson', null),
  (28, 'vendedor', 'Lajuana Vencill', 'Lajuana Vencill', null),
  (29, 'vendedor', 'Markita Hansen', 'Markita Hansen', null),
  (30, 'vendedor', 'Marty Freudenburg', 'Marty Freudenburg', null),
  (31, 'vendedor', 'Maureen Marcano', 'Maureen Marcano', null),
  (32, 'vendedor', 'Mei-Mei Johns', 'Mei-Mei Johns', null),
  (33, 'vendedor', 'Moses Frase', 'Moses Frase', null),
  (34, 'vendedor', 'Natalya Ivanova', 'Natalya Ivanova', null),
  (35, 'vendedor', 'Niesha Huffines', 'Niesha Huffines', null),
  (36, 'vendedor', 'Reed Clapper', 'Reed Clapper', null),
  (37, 'vendedor', 'Rosalina Dieter', 'Rosalina Dieter', null),
  (38, 'vendedor', 'Rosie Papadopoulos', 'Rosie Papadopoulos', null),
  (39, 'vendedor', 'Versie Hillebrand', 'Versie Hillebrand', null),
  (40, 'vendedor', 'Vicki Laflamme', 'Vicki Laflamme', null),
  (41, 'vendedor', 'Violet Mclelland', 'Violet Mclelland', null),
  (42, 'vendedor', 'Wilburn Farren', 'Wilburn Farren', null),
  (43, 'vendedor', 'Zane Levy', 'Zane Levy', null)
on conflict (id) do nothing;
select setval(pg_get_serial_sequence('config_usuarios', 'id'), (select max(id) from config_usuarios));

insert into config_motivos_perda (codigo, rotulo, exige_detalhe, ordem, ativo) values
  ('preco', 'Preço', false, 1, true),
  ('concorrente', 'Concorrente', false, 2, true),
  ('sem_orcamento', 'Sem orçamento', false, 3, true),
  ('sem_resposta', 'Sem resposta', false, 4, true),
  ('outro', 'Outro', true, 5, true),
  ('cadastro_desfeito', 'Cadastro desfeito', false, 90, true),
  ('importacao_desfeita', 'Importação desfeita', false, 91, true)
on conflict (codigo) do nothing;

insert into config_parametros (chave, valor, descricao, atualizado_por) values
  ('data_referencia', '"2017-12-31"'::jsonb, 'Relógio do CRM em modo demonstração (P6). null = data real.', 1),
  ('execucao_ativa', 'null'::jsonb, 'Id da score_execucoes em uso. null até a primeira carga do score.', 1),
  ('acoes_desde', 'null'::jsonb, 'Data de corte para esconder ações antigas da demonstração (reset sem DELETE).', 1),
  ('score_pesos', '{"fit": 0.7, "heat": 0.3}'::jsonb, 'Pesos da nota (informativo; a execução grava os pesos usados).', 1),
  ('faixas_nota', '{"alta_min": 70, "media_min": 40}'::jsonb, 'Faixas da barra da nota.', 1),
  ('icone_cortes', '{"super_hot_dias_min": 15, "super_hot_dias_max": 106, "super_hot_preco_min": 3000, "risco_dias_min": 107, "risco_dias_max": 138, "esfriou_dias_apos": 138}'::jsonb, 'Cortes dos ícones (ESPEC 2.4, P13), medidos nos dados.', 1),
  ('dias_sem_contato_risco', '14'::jsonb, 'Dias sem contato que contam como risco quando risco_por_contato_ativo = true.', 1),
  ('risco_por_contato_ativo', 'false'::jsonb, 'Liga o risco por falta de contato (depois que o CRM tiver uso).', 1),
  ('acoes_contato', '["liguei", "requalifiquei"]'::jsonb, 'Ações que contam como contato (P5).', 1),
  ('motivo_perda_obrigatorio', 'true'::jsonb, 'Pede o motivo ao perder ou descartar (P14).', 1),
  ('limite_lote', '500'::jsonb, 'Máximo de deals por lote.', 1),
  ('lote_desfazer_horas', '24'::jsonb, 'Prazo para desfazer um lote.', 1),
  ('desfazer_segundos', '10'::jsonb, 'Prazo do Desfazer de uma mudança no deal.', 1),
  ('max_tags_por_deal', '10'::jsonb, 'Tags ativas por deal.', 1),
  ('tag_cores', '["marinho", "dourado", "dourado-medio", "dourado-claro", "bronze", "bronze-escuro"]'::jsonb, 'Tokens de cor aceitos nas tags (FE-03). Conferir com o tema.', 1),
  ('prioridades_visiveis', '5'::jsonb, 'Itens visíveis nas Prioridades do dia.', 1),
  ('meta_prioridades_dia', '10'::jsonb, 'Meta diária de marcações.', 1),
  ('prioridades_fila_max', '50'::jsonb, 'Tamanho máximo da fila do dia.', 1),
  ('dias_pulado_alerta', '3'::jsonb, 'Dias seguidos pulado até o alerta de requalificar.', 1),
  ('limite_por_minuto', '60'::jsonb, 'Pedidos de escrita por usuário por minuto.', 1),
  ('importacao_max_linhas', '10000'::jsonb, 'Linhas por arquivo CSV.', 1),
  ('importacao_grafias', '{"GTXPro": "GTX Pro"}'::jsonb, 'Grafias conhecidas corrigidas na importação (igual à limpeza).', 1),
  ('roteamento_min_casos', '10'::jsonb, 'Mínimo de deals do vendedor no cohort, na janela de 3 meses, para receber lead pelo FIT.', 1),
  ('roteamento_teto_abertos', '200'::jsonb, 'Teto de deals abertos por vendedor para receber lead novo.', 1)
on conflict (chave) do nothing;

select set_config('app.usuario_id', '', false);
select set_config('app.correlation_id', '', false);

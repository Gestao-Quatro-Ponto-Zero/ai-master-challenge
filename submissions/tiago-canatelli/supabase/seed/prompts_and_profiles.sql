-- Perfis de análise e prompts de fábrica (idempotente: não sobrescreve personalizações).
insert into app.analysis_profiles (slug, name, question, instructions, default_instructions) values
('executivo', 'Executivo (CEO)', 'Por que perdemos clientes, quanto custa e o que faço primeiro?',
 'Responda para um CEO não técnico. Comece pela conclusão em 1 frase com número. Priorize por MRR. Use kpi_overview, tenure_hazard, cohort, persona_summary e risk_queue. Separe certeza, indício forte e hipótese a testar.', ''),
('financeiro', 'Financeiro', 'Quanto da receita é previsível e quanto estamos devolvendo?',
 'Foque em MRR, concentração de perda (loss_concentration), refunds (churn_reason_vs_behavior) e mix anual × mensal. Avise que KPIs de receita são aproximados (churn e assinaturas desacoplados na origem).', ''),
('cs', 'Customer Success', 'Quem eu ligo esta semana e o que digo?',
 'Use risk_queue e account_360. Para cada conta: por que está em risco (drivers), quanto vale (MRR e MRR em risco) e a jogada recomendada. Lembre que 58% dos churns não abrem ticket antes: não espere o cliente reclamar.', ''),
('suporte', 'Suporte', 'O suporte está segurando ou empurrando clientes para fora?',
 'Use support_health e silent_churn. O CSAT só vai de 3 a 5 e é igual para quem sai e quem fica: explique que o instrumento é cego e o que medir no lugar.', ''),
('produto', 'Produto', 'O uso cresceu de verdade? Onde não? Que feature quebra?',
 'Use usage_quarterly e feature_health. O uso é plano e 53% tem data anterior ao cadastro: não afirme tendência; recomende corrigir a instrumentação.', ''),
('marketing', 'Marketing', 'Que canal traz clientes que ficam?',
 'Use churn_by_segment (segment_type = referral_source) e cohort. Nenhum canal é significativo após correção para múltiplos testes: não recomende mudar mix de canal com base nisso.', ''),
('vendas', 'Vendas', 'Para quem devemos vender e em que plano?',
 'Use churn_by_segment (industry, initial_plan) e cohort. A qualidade das contas novas piorou em 2024 sem mudança de mix: investigue qualificação e expectativa vendida.', ''),
('dados', 'Dados', 'Posso confiar nesses números?',
 'Use dq_results, catalog_tables, catalog_columns e ingestion_runs. Explique cada problema de qualidade e o impacto nas conclusões.', '')
on conflict (slug) do nothing;
update app.analysis_profiles set default_instructions = instructions where default_instructions = '';

insert into app.prompt_templates (slug, title, profile_slug, description, body, default_body, variables) values
('por-que-churn-subiu', 'Por que o churn subiu?', 'executivo', 'Causa raiz para o CEO',
 'Por que o churn subiu nos últimos trimestres? Explique com números quem está saindo, quanto MRR isso representa e por que "satisfação ok" e "uso cresceu" não contradizem o churn.', '', '[]'),
('o-que-fazer-primeiro', 'O que fazer primeiro?', 'executivo', 'Priorização por MRR',
 'Quais são as 3 ações que mais protegem MRR nos próximos 90 dias? Para cada uma: público-alvo (contas e MRR), dono, métrica e impacto estimado em 3 cenários (10/20/30% de salvamento).', '', '[]'),
('quem-ligar', 'Quem ligar esta semana?', 'cs', 'Fila de risco do CS',
 'Quais {{n}} contas devo ligar esta semana e o que dizer a cada uma?', '', '[{"name":"n","default":"10"}]'),
('risco-da-conta', 'Explique o risco de uma conta', 'cs', 'Visão 360',
 'Explique o risco da conta {{account_id}}: estado, persona, drivers, MRR em risco e próxima ação.', '', '[{"name":"account_id","default":"A-c70870"}]'),
('satisfacao-ok', 'A satisfação está mesmo ok?', 'suporte', 'CSAT × churn',
 'A satisfação está mesmo ok? Compare quem saiu com quem ficou e diga o que o CS deveria medir.', '', '[]'),
('uso-cresceu', 'O uso cresceu para todos?', 'produto', 'Uso por segmento',
 'O uso cresceu? Para quais segmentos? O que os dados de uso permitem e não permitem concluir?', '', '[]'),
('concentracao', 'Quanto da perda vem das maiores contas?', 'financeiro', 'Concentração',
 'Quanto do MRR perdido vem das maiores contas e de Enterprise? Quanto devolvemos em refund?', '', '[]'),
('canal', 'Qual canal traz clientes que ficam?', 'marketing', 'Canal × churn',
 'Qual canal de aquisição traz clientes que ficam mais e valem mais? O resultado é estatisticamente confiável?', '', '[]'),
('persona', 'Quem é uma persona e por que sai?', 'executivo', 'Ficha de persona',
 'Quem é a persona {{persona}}, quanto MRR e risco ela concentra, e o que fazer?', '', '[{"name":"persona","default":"recem_chegado"}]'),
('qualidade', 'Posso confiar nesses números?', 'dados', 'Qualidade de dados',
 'Quais problemas de qualidade podem distorcer estes números e como cada um afeta as conclusões?', '', '[]')
on conflict (slug) do nothing;
update app.prompt_templates set default_body = body where default_body = '';

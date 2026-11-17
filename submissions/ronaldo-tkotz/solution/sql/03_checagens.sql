-- Checagens de qualidade. Cada linha de dq_checks diz quantos registros violam a regra.
-- bloqueante: falha estrutural (a carga não é aceita se > 0). alerta: inconsistência contada, dado mantido. info: contagem de cobertura.
-- Nada aqui altera dado; só mede. A reconciliação raw -> tipada (contagens e perdas na conversão)
-- é gravada pelo script de carga com o prefixo E0.

DELETE FROM dq_checks WHERE check_id NOT LIKE 'E0%';

INSERT INTO dq_checks (check_id, camada, tabela, regra, severidade, violacoes, base, tratamento)
-- ---------- Estrutura ----------
SELECT 'E10','estrutura','todas','datas fora do padrão YYYY-MM-DD HH:MM:SS','bloqueante',
  (SELECT count(*) FROM (
     SELECT signup_date d FROM accounts UNION ALL SELECT start_date FROM subscriptions
     UNION ALL SELECT end_date FROM subscriptions WHERE end_date IS NOT NULL
     UNION ALL SELECT usage_date FROM feature_usage UNION ALL SELECT submitted_at FROM support_tickets
     UNION ALL SELECT closed_at FROM support_tickets WHERE closed_at IS NOT NULL
     UNION ALL SELECT churn_date FROM churn_events)
   WHERE d NOT GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9]' OR d <> datetime(d)),
  (SELECT (SELECT count(*) FROM accounts) + (SELECT count(*) + count(end_date) FROM subscriptions)
        + (SELECT count(*) FROM feature_usage) + (SELECT count(*) + count(closed_at) FROM support_tickets)
        + (SELECT count(*) FROM churn_events)), 'padronizadas na carga'
UNION ALL SELECT 'E11','estrutura','todas','datas fora da janela 2023-01-01 a 2024-12-31 23:59:59','alerta',
  (SELECT count(*) FROM (
     SELECT signup_date d FROM accounts UNION ALL SELECT start_date FROM subscriptions
     UNION ALL SELECT end_date FROM subscriptions WHERE end_date IS NOT NULL
     UNION ALL SELECT usage_date FROM feature_usage UNION ALL SELECT submitted_at FROM support_tickets
     UNION ALL SELECT closed_at FROM support_tickets WHERE closed_at IS NOT NULL
     UNION ALL SELECT churn_date FROM churn_events)
   WHERE d < '2023-01-01 00:00:00' OR d > '2024-12-31 23:59:59'), NULL, NULL
UNION ALL SELECT 'E12','estrutura','todas','chaves estrangeiras órfãs (PRAGMA foreign_key_check)','bloqueante',
  (SELECT count(*) FROM pragma_foreign_key_check), NULL, 'FK imposta pelo banco'
UNION ALL SELECT 'E13','estrutura','feature_usage','usage_id repetido (conteúdo diferente nas duas linhas)','alerta',
  (SELECT count(*) FROM (SELECT usage_id FROM feature_usage GROUP BY usage_id HAVING count(*) > 1)),
  (SELECT count(DISTINCT usage_id) FROM feature_usage),
  'mantidas as 2 linhas de cada id; chave substituta usage_pk + chave natural (usage_id, subscription_id)'
UNION ALL SELECT 'E14','estrutura','feature_usage','linhas idênticas em todos os campos exceto usage_id','bloqueante',
  (SELECT count(*) - count(DISTINCT subscription_id||'|'||usage_date||'|'||feature_name||'|'||usage_count||'|'||usage_duration_secs||'|'||error_count||'|'||is_beta_feature) FROM feature_usage),
  (SELECT count(*) FROM feature_usage), NULL
-- ---------- Cobertura dos relacionamentos ----------
UNION ALL SELECT 'R01','cobertura','accounts','contas sem nenhuma assinatura','info',
  (SELECT count(*) FROM accounts a WHERE NOT EXISTS (SELECT 1 FROM subscriptions s WHERE s.account_id = a.account_id)),
  (SELECT count(*) FROM accounts), NULL
UNION ALL SELECT 'R02','cobertura','accounts','contas sem nenhum ticket','info',
  (SELECT count(*) FROM accounts a WHERE NOT EXISTS (SELECT 1 FROM support_tickets t WHERE t.account_id = a.account_id)),
  (SELECT count(*) FROM accounts), NULL
UNION ALL SELECT 'R03','cobertura','accounts','contas sem evento de churn','info',
  (SELECT count(*) FROM accounts a WHERE NOT EXISTS (SELECT 1 FROM churn_events c WHERE c.account_id = a.account_id)),
  (SELECT count(*) FROM accounts), NULL
UNION ALL SELECT 'R04','cobertura','subscriptions','assinaturas sem nenhum registro de uso','info',
  (SELECT count(*) FROM subscriptions s WHERE NOT EXISTS (SELECT 1 FROM feature_usage u WHERE u.subscription_id = s.subscription_id)),
  (SELECT count(*) FROM subscriptions), NULL
UNION ALL SELECT 'R05','cobertura','churn_events','contas com mais de um evento de churn','info',
  (SELECT count(*) FROM (SELECT account_id FROM churn_events GROUP BY account_id HAVING count(*) > 1)),
  (SELECT count(DISTINCT account_id) FROM churn_events), NULL
-- ---------- Tempo ----------
UNION ALL SELECT 'T01','tempo','subscriptions','end_date anterior a start_date','bloqueante',
  (SELECT count(*) FROM subscriptions WHERE end_date < start_date), (SELECT count(end_date) FROM subscriptions), NULL
UNION ALL SELECT 'T02','tempo','support_tickets','closed_at anterior a submitted_at','bloqueante',
  (SELECT count(*) FROM support_tickets WHERE closed_at < submitted_at), (SELECT count(closed_at) FROM support_tickets), NULL
UNION ALL SELECT 'T03','tempo','support_tickets','submitted_at sem hora no CSV (vira 00:00:00)','alerta',
  (SELECT count(*) FROM raw_support_tickets WHERE length(submitted_at) = 10), (SELECT count(*) FROM support_tickets),
  NULL
UNION ALL SELECT 'T04','tempo','support_tickets','closed_at = submitted_at + resolution_time_hours exatamente','alerta',
  (SELECT count(*) FROM support_tickets
    WHERE closed_at = datetime(submitted_at, '+' || CAST(resolution_time_hours AS INTEGER) || ' hours')),
  (SELECT count(closed_at) FROM support_tickets), NULL
UNION ALL SELECT 'T05','tempo','support_tickets','primeira resposta depois da resolução','alerta',
  (SELECT count(*) FROM support_tickets WHERE first_response_time_minutes > resolution_time_hours * 60),
  (SELECT count(*) FROM support_tickets), NULL
UNION ALL SELECT 'T06','tempo','feature_usage','uso fora do período da assinatura','alerta',
  (SELECT count(*) FROM feature_usage u JOIN subscriptions s USING (subscription_id)
    WHERE u.usage_date < s.start_date OR (s.end_date IS NOT NULL AND u.usage_date > s.end_date)),
  (SELECT count(*) FROM feature_usage), NULL
UNION ALL SELECT 'T07','tempo','subscriptions','assinatura iniciada antes do cadastro da conta','alerta',
  (SELECT count(*) FROM subscriptions s JOIN accounts a USING (account_id) WHERE s.start_date < a.signup_date),
  (SELECT count(*) FROM subscriptions), NULL
UNION ALL SELECT 'T08','tempo','support_tickets','ticket aberto antes do cadastro da conta','alerta',
  (SELECT count(*) FROM support_tickets t JOIN accounts a USING (account_id) WHERE t.submitted_at < a.signup_date),
  (SELECT count(*) FROM support_tickets), NULL
UNION ALL SELECT 'T09','tempo','churn_events','churn antes do cadastro da conta','alerta',
  (SELECT count(*) FROM churn_events c JOIN accounts a USING (account_id) WHERE c.churn_date < a.signup_date),
  (SELECT count(*) FROM churn_events), NULL
-- ---------- Consistência entre campos e tabelas ----------
UNION ALL SELECT 'N01','consistencia','subscriptions','arr_amount diferente de 12 x mrr_amount','alerta',
  (SELECT count(*) FROM subscriptions WHERE arr_amount <> 12 * mrr_amount), (SELECT count(*) FROM subscriptions), NULL
UNION ALL SELECT 'N02','consistencia','subscriptions','churn_flag = 1 sem end_date','alerta',
  (SELECT count(*) FROM subscriptions WHERE churn_flag = 1 AND end_date IS NULL), (SELECT sum(churn_flag) FROM subscriptions), NULL
UNION ALL SELECT 'N03','consistencia','subscriptions','end_date preenchida com churn_flag = 0','alerta',
  (SELECT count(*) FROM subscriptions WHERE churn_flag = 0 AND end_date IS NOT NULL), (SELECT count(end_date) FROM subscriptions), NULL
UNION ALL SELECT 'N04','consistencia','accounts','churn_flag = 1 sem evento em churn_events','alerta',
  (SELECT count(*) FROM accounts a WHERE churn_flag = 1 AND NOT EXISTS (SELECT 1 FROM churn_events c WHERE c.account_id = a.account_id)),
  (SELECT sum(churn_flag) FROM accounts), NULL
UNION ALL SELECT 'N05','consistencia','accounts','evento de churn com churn_flag = 0 na conta','alerta',
  (SELECT count(*) FROM accounts a WHERE churn_flag = 0 AND EXISTS (SELECT 1 FROM churn_events c WHERE c.account_id = a.account_id)),
  (SELECT count(DISTINCT account_id) FROM churn_events), NULL
UNION ALL SELECT 'N06','consistencia','accounts','churn_flag = 1 com assinatura ainda ativa (end_date nula)','alerta',
  (SELECT count(*) FROM accounts a WHERE churn_flag = 1 AND EXISTS (SELECT 1 FROM subscriptions s WHERE s.account_id = a.account_id AND s.end_date IS NULL)),
  (SELECT sum(churn_flag) FROM accounts), NULL
UNION ALL SELECT 'N07','consistencia','subscriptions','plan_tier da assinatura diferente do plan_tier da conta','info',
  (SELECT count(*) FROM subscriptions s JOIN accounts a USING (account_id) WHERE s.plan_tier <> a.plan_tier),
  (SELECT count(*) FROM subscriptions), NULL
UNION ALL SELECT 'N08','consistencia','subscriptions','assinatura trial com mrr_amount > 0','info',
  (SELECT count(*) FROM subscriptions WHERE is_trial = 1 AND mrr_amount > 0), (SELECT sum(is_trial) FROM subscriptions), NULL
UNION ALL SELECT 'N09','consistencia','subscriptions','assinaturas com mrr_amount = 0','info',
  (SELECT count(*) FROM subscriptions WHERE mrr_amount = 0), (SELECT count(*) FROM subscriptions), NULL;

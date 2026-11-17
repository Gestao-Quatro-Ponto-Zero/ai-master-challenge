-- 20: validação das relações (cardinalidade) e teste de consulta multi-tabela tipo tabela dinâmica.
-- Uso: sqlite3 -readonly data/db/ravenstack.db < 20_relacoes_e_pivo.sql
.mode column
.headers on

SELECT '1) FK checadas de novo, independente da carga' AS etapa;
SELECT count(*) AS fk_orfas FROM pragma_foreign_key_check;
SELECT m.name AS tabela, f."table" AS referencia, f."from" AS coluna, f."to" AS chave_pai
FROM sqlite_master m, pragma_foreign_key_list(m.name) f WHERE m.type='table' ORDER BY 1;

SELECT '2) Cardinalidade de cada relação (filhos por pai, incluindo pais com 0 filhos)' AS etapa;
WITH c AS (
  SELECT 'accounts -> subscriptions' rel, (SELECT count(*) FROM subscriptions s WHERE s.account_id=a.account_id) n FROM accounts a
  UNION ALL SELECT 'subscriptions -> feature_usage', (SELECT count(*) FROM feature_usage u WHERE u.subscription_id=s.subscription_id) FROM subscriptions s
  UNION ALL SELECT 'accounts -> support_tickets', (SELECT count(*) FROM support_tickets t WHERE t.account_id=a.account_id) FROM accounts a
  UNION ALL SELECT 'accounts -> churn_events', (SELECT count(*) FROM churn_events e WHERE e.account_id=a.account_id) FROM accounts a)
SELECT rel AS relacao, count(*) AS pais, sum(n) AS filhos, min(n) AS min, max(n) AS max, round(avg(n),2) AS media,
       sum(n=0) AS pais_sem_filho FROM c GROUP BY rel;

SELECT '3) Armadilha do JOIN direto: dois filhos 1:N do mesmo pai multiplicam linhas' AS etapa;
SELECT (SELECT sum(mrr_amount) FROM subscriptions) AS mrr_real,
       (SELECT sum(s.mrr_amount) FROM subscriptions s JOIN support_tickets t USING(account_id)) AS mrr_join_direto_com_tickets,
       (SELECT count(*) FROM subscriptions s JOIN support_tickets t USING(account_id)) AS linhas_join_direto;

SELECT '4) Tabela dinâmica correta: agrega cada filho no grão da conta antes de juntar' AS etapa;
CREATE TEMP VIEW conta AS
WITH s AS (SELECT account_id, count(*) n_assinaturas, sum(mrr_amount) mrr, sum(end_date IS NULL) assinaturas_sem_fim
           FROM subscriptions GROUP BY account_id),
     u AS (SELECT s.account_id, count(*) n_uso, sum(u.error_count) erros
           FROM feature_usage u JOIN subscriptions s USING(subscription_id) GROUP BY s.account_id),
     t AS (SELECT account_id, count(*) n_tickets FROM support_tickets GROUP BY account_id),
     e AS (SELECT account_id, count(*) n_eventos_churn FROM churn_events GROUP BY account_id)
SELECT a.account_id, a.industry, a.country, a.plan_tier,
       coalesce(s.n_assinaturas,0) n_assinaturas, coalesce(s.mrr,0) mrr, coalesce(s.assinaturas_sem_fim,0) assinaturas_sem_fim,
       coalesce(u.n_uso,0) n_uso, coalesce(u.erros,0) erros, coalesce(t.n_tickets,0) n_tickets, coalesce(e.n_eventos_churn,0) n_eventos_churn
FROM accounts a LEFT JOIN s USING(account_id) LEFT JOIN u USING(account_id) LEFT JOIN t USING(account_id) LEFT JOIN e USING(account_id);

SELECT industry, count(*) contas,
  sum(CASE plan_tier WHEN 'Basic' THEN 1 ELSE 0 END) basic, sum(CASE plan_tier WHEN 'Pro' THEN 1 ELSE 0 END) pro,
  sum(CASE plan_tier WHEN 'Enterprise' THEN 1 ELSE 0 END) enterprise,
  sum(n_assinaturas) assinaturas, sum(mrr) mrr, sum(n_uso) registros_uso, sum(n_tickets) tickets, sum(n_eventos_churn) eventos_churn
FROM conta GROUP BY industry
UNION ALL
SELECT 'TOTAL', count(*), sum(plan_tier='Basic'), sum(plan_tier='Pro'), sum(plan_tier='Enterprise'),
  sum(n_assinaturas), sum(mrr), sum(n_uso), sum(n_tickets), sum(n_eventos_churn) FROM conta;

SELECT '5) Reconciliação: totais da tabela dinâmica = totais das tabelas de origem (1 = bate)' AS etapa;
SELECT (SELECT count(*) FROM conta) = (SELECT count(*) FROM accounts) contas,
       (SELECT sum(n_assinaturas) FROM conta) = (SELECT count(*) FROM subscriptions) assinaturas,
       (SELECT sum(mrr) FROM conta) = (SELECT sum(mrr_amount) FROM subscriptions) mrr,
       (SELECT sum(n_uso) FROM conta) = (SELECT count(*) FROM feature_usage) uso,
       (SELECT sum(erros) FROM conta) = (SELECT sum(error_count) FROM feature_usage) erros,
       (SELECT sum(n_tickets) FROM conta) = (SELECT count(*) FROM support_tickets) tickets,
       (SELECT sum(n_eventos_churn) FROM conta) = (SELECT count(*) FROM churn_events) eventos_churn;

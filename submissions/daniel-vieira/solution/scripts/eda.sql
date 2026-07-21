-- eda.sql --- Analise exploratoria dos dados brutos do dataset CRM (DuckDB).
--
-- Executar a partir da raiz do projeto:
--   duckdb -markdown < scripts/eda.sql
--
-- Consulta a fonte normalizada em 'data/normalized/' (gerada por
-- 'scripts/normalize.sql'), sem carga nem persistencia. Os achados e as suas
-- implicacoes para a modelagem estao consolidados em
-- 'docs/analise-exploratoria.md'; este arquivo e a fonte canonica das
-- consultas que os produzem.
--
-- A normalizacao (por exemplo, 'GTXPro' para 'GTX Pro') reside na fonte
-- 'data/normalized/', de modo que as consultas leem dados ja limpos e nao
-- aplicam correcoes em linha. A data de referencia ('as of') para leads
-- abertos e a maxima close_date do dataset, 2017-12-31.


-- 1. Distribuicao de deal_stage.
SELECT deal_stage, COUNT(*) AS n,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM 'data/normalized/sales_pipeline.csv'
GROUP BY deal_stage
ORDER BY n DESC;


-- 2. close_value por deal_stage: preenchimento, zeros e faixa.
SELECT deal_stage,
       COUNT(*) AS n,
       COUNT(close_value) AS com_valor,
       SUM(CASE WHEN close_value = 0 THEN 1 ELSE 0 END) AS zeros,
       MIN(close_value) AS minimo,
       MAX(close_value) AS maximo,
       ROUND(AVG(close_value), 0) AS media,
       ROUND(MEDIAN(close_value), 0) AS mediana
FROM 'data/normalized/sales_pipeline.csv'
GROUP BY deal_stage
ORDER BY n DESC;


-- 3. Preenchimento de engage_date e close_date por estagio.
SELECT deal_stage,
       COUNT(*) AS n,
       COUNT(engage_date) AS tem_engage,
       COUNT(close_date) AS tem_close
FROM 'data/normalized/sales_pipeline.csv'
GROUP BY deal_stage
ORDER BY n DESC;


-- 4. Tempo de ciclo (dias) de engage_date a close_date, por desfecho.
SELECT deal_stage,
       COUNT(*) AS n,
       MIN(DATE_DIFF('day', engage_date::DATE, close_date::DATE)) AS min_dias,
       ROUND(AVG(DATE_DIFF('day', engage_date::DATE, close_date::DATE)), 1) AS media_dias,
       MEDIAN(DATE_DIFF('day', engage_date::DATE, close_date::DATE)) AS mediana_dias,
       MAX(DATE_DIFF('day', engage_date::DATE, close_date::DATE)) AS max_dias
FROM 'data/normalized/sales_pipeline.csv'
WHERE deal_stage IN ('Won', 'Lost')
GROUP BY deal_stage;


-- 5. Integridade referencial: orfaos no pipeline e account nulo. As subconsultas
-- de NOT IN filtram nulos para evitar a logica de tres valores do SQL.
SELECT
  (SELECT COUNT(*) FROM 'data/normalized/sales_pipeline.csv' AS p
     WHERE p.account IS NOT NULL
       AND p.account NOT IN (
         SELECT a.account FROM 'data/normalized/accounts.csv' AS a
         WHERE a.account IS NOT NULL)) AS acct_orfaos,
  (SELECT COUNT(*) FROM 'data/normalized/sales_pipeline.csv' AS p
     WHERE p.product NOT IN (
       SELECT c.product FROM 'data/normalized/products.csv' AS c
       WHERE c.product IS NOT NULL)) AS prod_orfaos,
  (SELECT COUNT(*) FROM 'data/normalized/sales_pipeline.csv' AS p
     WHERE p.sales_agent NOT IN (
       SELECT t.sales_agent FROM 'data/normalized/sales_teams.csv' AS t
       WHERE t.sales_agent IS NOT NULL)) AS agent_orfaos,
  (SELECT COUNT(*) FROM 'data/normalized/sales_pipeline.csv' AS p
     WHERE p.account IS NULL) AS account_nulo;


-- 6. Produtos: nomes distintos no pipeline (orfaos) versus catalogo.
SELECT p.product, COUNT(*) AS n
FROM 'data/normalized/sales_pipeline.csv' AS p
WHERE p.product NOT IN (
  SELECT c.product FROM 'data/normalized/products.csv' AS c
  WHERE c.product IS NOT NULL)
GROUP BY p.product;


-- 7. account nulo por estagio.
SELECT deal_stage, COUNT(*) AS n,
       SUM(CASE WHEN account IS NULL THEN 1 ELSE 0 END) AS account_nulo
FROM 'data/normalized/sales_pipeline.csv'
GROUP BY deal_stage
ORDER BY n DESC;


-- 8. Produto: win rate, valor medio de ganho e preco de tabela (nome normalizado).
WITH p AS (
  SELECT product, deal_stage, close_value
  FROM 'data/normalized/sales_pipeline.csv'
)
SELECT p.product,
       c.sales_price AS preco_tabela,
       COUNT(*) FILTER (WHERE p.deal_stage IN ('Won', 'Lost')) AS fechados,
       ROUND(100.0 * COUNT(*) FILTER (WHERE p.deal_stage = 'Won')
             / NULLIF(COUNT(*) FILTER (WHERE p.deal_stage IN ('Won', 'Lost')), 0), 1)
         AS win_pct,
       ROUND(AVG(p.close_value) FILTER (WHERE p.deal_stage = 'Won'), 0) AS valor_medio_won,
       COUNT(*) FILTER (WHERE p.deal_stage IN ('Engaging', 'Prospecting')) AS abertos
FROM p
JOIN 'data/normalized/products.csv' AS c ON c.product = p.product
GROUP BY p.product, c.sales_price
ORDER BY win_pct DESC;


-- 9. Escritorio regional: volume e win rate.
SELECT t.regional_office,
       COUNT(*) FILTER (WHERE p.deal_stage IN ('Won', 'Lost')) AS fechados,
       ROUND(100.0 * COUNT(*) FILTER (WHERE p.deal_stage = 'Won')
             / NULLIF(COUNT(*) FILTER (WHERE p.deal_stage IN ('Won', 'Lost')), 0), 1)
             AS win_pct,
       COUNT(*) FILTER (WHERE p.deal_stage IN ('Engaging', 'Prospecting')) AS abertos
FROM 'data/normalized/sales_pipeline.csv' AS p
JOIN 'data/normalized/sales_teams.csv' AS t ON t.sales_agent = p.sales_agent
GROUP BY t.regional_office
ORDER BY win_pct DESC;


-- 10. Agentes: dispersao do win rate e da carga (fechados).
WITH a AS (
  SELECT p.sales_agent,
         COUNT(*) FILTER (WHERE p.deal_stage IN ('Won', 'Lost')) AS fechados,
         100.0 * COUNT(*) FILTER (WHERE p.deal_stage = 'Won')
           / NULLIF(COUNT(*) FILTER (WHERE p.deal_stage IN ('Won', 'Lost')), 0) AS win_pct,
         COUNT(*) FILTER (WHERE p.deal_stage IN ('Engaging', 'Prospecting')) AS abertos
  FROM 'data/normalized/sales_pipeline.csv' AS p
  GROUP BY p.sales_agent
)
SELECT COUNT(*) AS agentes,
       ROUND(MIN(win_pct), 1) AS win_min,
       ROUND(MEDIAN(win_pct), 1) AS win_mediana,
       ROUND(MAX(win_pct), 1) AS win_max,
       ROUND(STDDEV(win_pct), 1) AS win_desvio,
       MIN(fechados) AS carga_min,
       MAX(fechados) AS carga_max
FROM a;


-- 11. Setor da conta (deals fechados com conta): win rate e valor.
SELECT c.sector,
       COUNT(*) AS fechados,
       ROUND(100.0 * COUNT(*) FILTER (WHERE p.deal_stage = 'Won') / COUNT(*), 1) AS win_pct,
       ROUND(AVG(p.close_value) FILTER (WHERE p.deal_stage = 'Won'), 0) AS valor_medio_won
FROM 'data/normalized/sales_pipeline.csv' AS p
JOIN 'data/normalized/accounts.csv' AS c ON c.account = p.account
WHERE p.deal_stage IN ('Won', 'Lost')
GROUP BY c.sector
ORDER BY fechados DESC;


-- 12. Janela temporal do dataset.
SELECT MIN(engage_date::DATE) AS min_engage,
       MAX(engage_date::DATE) AS max_engage,
       MIN(close_date::DATE) AS min_close,
       MAX(close_date::DATE) AS max_close
FROM 'data/normalized/sales_pipeline.csv';


-- 13. Idade dos leads Engaging na data de referencia (asof = max close_date).
-- Compara a idade desde o engajamento com a mediana (57 dias) e o maximo (138
-- dias) do ciclo historico, expondo a estagnacao dos leads abertos.
WITH ref AS (SELECT MAX(close_date::DATE) AS asof FROM 'data/normalized/sales_pipeline.csv')
SELECT COUNT(*) AS engaging,
       ROUND(AVG(DATE_DIFF('day', p.engage_date::DATE, ref.asof)), 1) AS idade_media,
       MEDIAN(DATE_DIFF('day', p.engage_date::DATE, ref.asof)) AS idade_mediana,
       MAX(DATE_DIFF('day', p.engage_date::DATE, ref.asof)) AS idade_max,
       SUM(CASE WHEN DATE_DIFF('day', p.engage_date::DATE, ref.asof) > 57 THEN 1 ELSE 0 END)
         AS acima_mediana_won_57d,
       SUM(CASE WHEN DATE_DIFF('day', p.engage_date::DATE, ref.asof) > 138 THEN 1 ELSE 0 END)
         AS acima_ciclo_max_138d
FROM 'data/normalized/sales_pipeline.csv' AS p, ref
WHERE p.deal_stage = 'Engaging';


-- 14. Oportunidade economica aberta por estagio (valor ~ preco de tabela).
WITH p AS (
  SELECT deal_stage, product
  FROM 'data/normalized/sales_pipeline.csv'
  WHERE deal_stage IN ('Engaging', 'Prospecting')
)
SELECT p.deal_stage,
       COUNT(*) AS leads,
       SUM(c.sales_price) AS valor_tabela_total,
       ROUND(AVG(c.sales_price), 0) AS valor_tabela_medio
FROM p
JOIN 'data/normalized/products.csv' AS c ON c.product = p.product
GROUP BY p.deal_stage
ORDER BY leads DESC;


-- 15. Agentes ociosos (no time, sem qualquer negocio) e total de agentes ativos.
SELECT
  (SELECT COUNT(*) FROM 'data/normalized/sales_teams.csv') AS agentes_no_time,
  (SELECT COUNT(DISTINCT p.sales_agent)
   FROM 'data/normalized/sales_pipeline.csv' AS p) AS agentes_com_deals,
  (SELECT COUNT(*) FROM 'data/normalized/sales_teams.csv' AS t
     WHERE t.sales_agent NOT IN (
       SELECT DISTINCT p.sales_agent FROM 'data/normalized/sales_pipeline.csv' AS p
       WHERE p.sales_agent IS NOT NULL)) AS agentes_idle;


-- 16. Distribuicao atual dos leads abertos entre agentes.
WITH a AS (
  SELECT sales_agent, COUNT(*) AS abertos
  FROM 'data/normalized/sales_pipeline.csv'
  WHERE deal_stage IN ('Engaging', 'Prospecting')
  GROUP BY sales_agent
)
SELECT COUNT(*) AS agentes_com_abertos,
       SUM(abertos) AS total_abertos,
       MIN(abertos) AS minimo,
       ROUND(AVG(abertos), 1) AS media,
       MEDIAN(abertos) AS mediana,
       MAX(abertos) AS maximo
FROM a;


-- 17. Gerente: win rate e carga de leads abertos.
SELECT t.manager,
       ROUND(100.0 * COUNT(*) FILTER (WHERE p.deal_stage = 'Won')
             / NULLIF(COUNT(*) FILTER (WHERE p.deal_stage IN ('Won', 'Lost')), 0), 1)
             AS win_pct,
       COUNT(*) FILTER (WHERE p.deal_stage IN ('Engaging', 'Prospecting')) AS abertos
FROM 'data/normalized/sales_pipeline.csv' AS p
JOIN 'data/normalized/sales_teams.csv' AS t ON t.sales_agent = p.sales_agent
GROUP BY t.manager
ORDER BY win_pct DESC;


-- ===========================================================================
-- Analise aprofundada: perfil de cliente, especializacao de agente e recompra.
-- As views a seguir persistem pelo restante do script.
-- ===========================================================================

CREATE OR REPLACE TEMP VIEW pipe AS
  SELECT account, sales_agent, product,
         deal_stage, close_value, engage_date, close_date
  FROM 'data/normalized/sales_pipeline.csv';
CREATE OR REPLACE TEMP VIEW cat AS
  SELECT product, series, sales_price FROM 'data/normalized/products.csv';
CREATE OR REPLACE TEMP VIEW acct AS
  SELECT account, sector, revenue, employees, office_location, subsidiary_of,
         NTILE(3) OVER (ORDER BY revenue) AS banda
  FROM 'data/normalized/accounts.csv';


-- 18. Porte (terco de receita) x consumo: win rate, ticket e receita.
SELECT ac.banda,
       COUNT(DISTINCT ac.account) AS contas,
       ROUND(MIN(ac.revenue), 0) AS rev_min,
       ROUND(MAX(ac.revenue), 0) AS rev_max,
       COUNT(*) FILTER (WHERE p.deal_stage = 'Won') AS won,
       ROUND(100.0 * COUNT(*) FILTER (WHERE p.deal_stage = 'Won')
             / COUNT(*) FILTER (WHERE p.deal_stage IN ('Won', 'Lost')), 1) AS win_pct,
       ROUND(AVG(p.close_value) FILTER (WHERE p.deal_stage = 'Won'), 0) AS ticket_medio,
       SUM(p.close_value) FILTER (WHERE p.deal_stage = 'Won') AS receita
FROM acct AS ac
JOIN pipe AS p ON p.account = ac.account
GROUP BY ac.banda
ORDER BY ac.banda;


-- 19. Localizacao e pertencimento x desempenho.
SELECT CASE WHEN ac.office_location = 'United States' THEN 'EUA' ELSE 'Outros' END AS local,
       CASE WHEN ac.subsidiary_of IS NULL THEN 'independente' ELSE 'subsidiaria' END AS tipo,
       COUNT(DISTINCT ac.account) AS contas,
       ROUND(100.0 * COUNT(*) FILTER (WHERE p.deal_stage = 'Won')
             / COUNT(*) FILTER (WHERE p.deal_stage IN ('Won', 'Lost')), 1) AS win_pct,
       ROUND(AVG(p.close_value) FILTER (WHERE p.deal_stage = 'Won'), 0) AS ticket_medio
FROM acct AS ac
JOIN pipe AS p ON p.account = ac.account
GROUP BY 1, 2
ORDER BY 1, 2;


-- 20. Especializacao por agente: linha, ticket mediano e ciclo.
SELECT p.sales_agent,
       COUNT(*) FILTER (WHERE p.deal_stage = 'Won') AS won,
       ROUND(100.0 * COUNT(*) FILTER (WHERE p.deal_stage = 'Won')
             / COUNT(*) FILTER (WHERE p.deal_stage IN ('Won', 'Lost')), 0) AS win_pct,
       ROUND(MEDIAN(p.close_value) FILTER (WHERE p.deal_stage = 'Won'), 0) AS ticket_med,
       MEDIAN(DATE_DIFF('day', p.engage_date::DATE, p.close_date::DATE))
         FILTER (WHERE p.deal_stage = 'Won') AS ciclo,
       ROUND(100.0 * COUNT(*) FILTER (WHERE p.deal_stage = 'Won' AND c.series = 'GTX')
             / COUNT(*) FILTER (WHERE p.deal_stage = 'Won'), 0) AS gtx_pct,
       ROUND(100.0 * COUNT(*) FILTER (WHERE p.deal_stage = 'Won' AND c.series = 'MG')
             / COUNT(*) FILTER (WHERE p.deal_stage = 'Won'), 0) AS mg_pct,
       COUNT(*) FILTER (WHERE p.deal_stage = 'Won' AND c.series = 'GTK') AS gtk
FROM pipe AS p
JOIN cat AS c ON c.product = p.product
GROUP BY p.sales_agent
HAVING COUNT(*) FILTER (WHERE p.deal_stage IN ('Won', 'Lost')) > 0
ORDER BY won DESC;


-- 21. Produto: win rate, ticket e ciclo de fechamento.
SELECT c.series, p.product, c.sales_price AS preco,
       COUNT(*) FILTER (WHERE p.deal_stage = 'Won') AS won,
       ROUND(100.0 * COUNT(*) FILTER (WHERE p.deal_stage = 'Won')
             / COUNT(*) FILTER (WHERE p.deal_stage IN ('Won', 'Lost')), 1) AS win_pct,
       MEDIAN(DATE_DIFF('day', p.engage_date::DATE, p.close_date::DATE))
         FILTER (WHERE p.deal_stage = 'Won') AS ciclo_won
FROM pipe AS p
JOIN cat AS c ON c.product = p.product
GROUP BY c.series, p.product, c.sales_price
ORDER BY c.sales_price DESC;


-- 22. Estrutura oportunidade-centrica: agentes distintos por conta (Won).
SELECT MIN(n) AS min_agentes, ROUND(AVG(n), 1) AS media,
       MEDIAN(n) AS mediana, MAX(n) AS max_agentes
FROM (SELECT account, COUNT(DISTINCT sales_agent) AS n
      FROM pipe WHERE deal_stage = 'Won' AND account IS NOT NULL
      GROUP BY account);


-- 23. Saturacao de cross-sell: linhas distintas compradas por conta (Won).
WITH ac AS (
  SELECT p.account, COUNT(DISTINCT c.series) AS linhas
  FROM pipe AS p JOIN cat AS c ON c.product = p.product
  WHERE p.deal_stage = 'Won' AND p.account IS NOT NULL
  GROUP BY p.account
)
SELECT linhas AS linhas_distintas, COUNT(*) AS contas
FROM ac GROUP BY linhas ORDER BY linhas;


-- 24. Recompra: intervalo entre Won consecutivos do mesmo produto por conta.
CREATE OR REPLACE TEMP VIEW recompra AS
  SELECT product, account,
         DATE_DIFF('day',
                   LAG(close_date::DATE) OVER (PARTITION BY account, product
                                               ORDER BY close_date::DATE),
                   close_date::DATE) AS gap
  FROM pipe
  WHERE deal_stage = 'Won' AND account IS NOT NULL;

SELECT c.series, r.product, c.sales_price AS preco,
       COUNT(r.gap) AS intervalos,
       ROUND(AVG(r.gap), 0) AS media_dias,
       MEDIAN(r.gap) AS mediana_dias
FROM recompra AS r
JOIN cat AS c ON c.product = r.product
WHERE r.gap IS NOT NULL
GROUP BY c.series, r.product, c.sales_price
ORDER BY mediana_dias;


-- 25. Produto premium GTK 500: quem ganha e que contas compram.
SELECT sales_agent, COUNT(*) FILTER (WHERE deal_stage = 'Won') AS gtk_won
FROM pipe
WHERE product = 'GTK 500'
GROUP BY sales_agent
HAVING COUNT(*) FILTER (WHERE deal_stage = 'Won') > 0
ORDER BY gtk_won DESC;


-- ===========================================================================
-- Robustez e testes de confundimento: separar sinal de ruido.
-- ===========================================================================

-- 26. Sinal do agente no win rate: dispersao observada vs esperada por ruido.
-- Se a observada nao supera a esperada, a diferenca de win rate entre agentes
-- e majoritariamente ruido amostral.
WITH a AS (
  SELECT sales_agent,
         COUNT(*) FILTER (WHERE deal_stage IN ('Won', 'Lost')) AS n,
         COUNT(*) FILTER (WHERE deal_stage = 'Won') AS w
  FROM pipe GROUP BY sales_agent
  HAVING COUNT(*) FILTER (WHERE deal_stage IN ('Won', 'Lost')) > 0
),
ci AS (SELECT n, w::DOUBLE / n AS p,
              1.96 * SQRT((w::DOUBLE / n) * (1 - w::DOUBLE / n) / n) AS moe FROM a)
SELECT ROUND(100 * AVG(p), 1) AS win_medio_pct,
       ROUND(100 * STDDEV_SAMP(p), 2) AS sd_observado_pp,
       ROUND(100 * SQRT(AVG(p * (1 - p) / n)), 2) AS sd_esperado_ruido_pp,
       SUM(CASE WHEN p - moe > 0.631 OR p + moe < 0.631 THEN 1 ELSE 0 END) AS agentes_signif
FROM ci;


-- 27. Sinal do agente na linha (GTX%): observado vs ruido. Espera-se sinal real.
WITH agln AS (
  SELECT p.sales_agent, COUNT(*) AS n,
         COUNT(*) FILTER (WHERE c.series = 'GTX') AS gtx
  FROM pipe AS p JOIN cat AS c ON c.product = p.product
  WHERE p.deal_stage = 'Won'
  GROUP BY p.sales_agent HAVING COUNT(*) >= 20
),
g AS (SELECT n, gtx::DOUBLE / n AS pg,
             1.96 * SQRT((gtx::DOUBLE / n) * (1 - gtx::DOUBLE / n) / n) AS moe FROM agln)
SELECT ROUND(100 * (SELECT SUM(agln.gtx)::DOUBLE / SUM(agln.n) FROM agln), 1) AS gtx_global_pct,
       ROUND(100 * STDDEV_SAMP(pg), 1) AS sd_observado_pp,
       ROUND(100 * SQRT(AVG(pg * (1 - pg) / n)), 1) AS sd_esperado_ruido_pp,
       SUM(CASE WHEN pg - moe > (SELECT SUM(agln.gtx)::DOUBLE / SUM(agln.n) FROM agln)
                  OR pg + moe < (SELECT SUM(agln.gtx)::DOUBLE / SUM(agln.n) FROM agln)
                THEN 1 ELSE 0 END) AS agentes_signif
FROM g;


-- 28. Concentracao do GTK 500 por agente: observado vs esperado se aleatorio.
WITH ag AS (
  SELECT sales_agent,
         COUNT(*) FILTER (WHERE deal_stage = 'Won') AS won_total,
         COUNT(*) FILTER (WHERE deal_stage = 'Won' AND product = 'GTK 500') AS gtk
  FROM pipe GROUP BY sales_agent
),
r AS (SELECT SUM(gtk)::DOUBLE / SUM(won_total) AS pgtk FROM ag)
SELECT sales_agent, won_total, gtk AS gtk_observado,
       ROUND((SELECT r.pgtk FROM r) * won_total, 2) AS gtk_esperado_aleatorio
FROM ag WHERE gtk > 0 ORDER BY gtk DESC;


-- 29. Ciclo: efeito produto vs efeito agente. Dispersao dos ciclos entre agentes
-- dentro de cada produto (efeito agente controlado por produto).
WITH pa AS (
  SELECT product, sales_agent,
         MEDIAN(DATE_DIFF('day', engage_date::DATE, close_date::DATE)) AS ciclo
  FROM pipe WHERE deal_stage = 'Won'
  GROUP BY product, sales_agent HAVING COUNT(*) >= 8
)
SELECT product, COUNT(*) AS agentes,
       MIN(ciclo) AS ag_min, MAX(ciclo) AS ag_max,
       MAX(ciclo) - MIN(ciclo) AS spread_agentes
FROM pa GROUP BY product ORDER BY spread_agentes DESC;


-- 30. Consistencia do ciclo do agente entre produtos (GTX Basic vs GTX Pro).
-- Correlacao proxima de zero indica que a velocidade do agente nao e estavel.
WITH pa AS (
  SELECT sales_agent, product,
         MEDIAN(DATE_DIFF('day', engage_date::DATE, close_date::DATE)) AS ciclo
  FROM pipe WHERE deal_stage = 'Won'
  GROUP BY sales_agent, product HAVING COUNT(*) >= 8
),
c AS (
  SELECT b.sales_agent, b.ciclo AS ciclo_basic, p.ciclo AS ciclo_pro
  FROM (SELECT * FROM pa WHERE product = 'GTX Basic') AS b
  JOIN (SELECT * FROM pa WHERE product = 'GTX Pro') AS p ON p.sales_agent = b.sales_agent
)
SELECT COUNT(*) AS agentes, ROUND(CORR(ciclo_basic, ciclo_pro), 3) AS corr_entre_produtos
FROM c;


-- 31. Porte por funcionarios: correlacao com receita e consumo por banda.
SELECT ROUND(CORR(revenue, employees), 3) AS corr_receita_funcionarios
FROM 'data/normalized/accounts.csv';

WITH ae AS (
  SELECT account, employees, NTILE(3) OVER (ORDER BY employees) AS banda
  FROM 'data/normalized/accounts.csv'
)
SELECT ae.banda, COUNT(DISTINCT ae.account) AS contas,
       MIN(ae.employees) AS emp_min, MAX(ae.employees) AS emp_max,
       ROUND(100.0 * COUNT(*) FILTER (WHERE p.deal_stage = 'Won')
             / COUNT(*) FILTER (WHERE p.deal_stage IN ('Won', 'Lost')), 1) AS win_pct,
       ROUND(AVG(p.close_value) FILTER (WHERE p.deal_stage = 'Won'), 0) AS ticket
FROM ae JOIN pipe AS p ON p.account = ae.account
GROUP BY ae.banda ORDER BY ae.banda;


-- 32. Setor x preferencia de linha (Q11).
SELECT ac.sector,
       ROUND(100.0 * COUNT(*) FILTER (WHERE p.deal_stage = 'Won' AND c.series = 'GTX')
             / COUNT(*) FILTER (WHERE p.deal_stage = 'Won'), 0) AS gtx_pct,
       ROUND(100.0 * COUNT(*) FILTER (WHERE p.deal_stage = 'Won' AND c.series = 'MG')
             / COUNT(*) FILTER (WHERE p.deal_stage = 'Won'), 0) AS mg_pct
FROM acct AS ac JOIN pipe AS p ON p.account = ac.account JOIN cat AS c ON c.product = p.product
WHERE p.deal_stage IN ('Won', 'Lost')
GROUP BY ac.sector ORDER BY gtx_pct DESC;


-- 33. Afinidade agente-cliente (Q5): ticket tipico do agente vs porte do cliente.
-- Correlacao nula indica especializacao por produto, ortogonal ao cliente.
WITH ag AS (
  SELECT p.sales_agent,
         MEDIAN(p.close_value) FILTER (WHERE p.deal_stage = 'Won') AS ticket_agente,
         MEDIAN(a.revenue) AS receita_cliente
  FROM pipe AS p JOIN 'data/normalized/accounts.csv' AS a ON a.account = p.account
  WHERE p.deal_stage = 'Won'
  GROUP BY p.sales_agent
)
SELECT COUNT(*) AS agentes, ROUND(CORR(ticket_agente, receita_cliente), 3) AS corr_ticket_porte
FROM ag;


-- 34. Inventario aberto por linha e estagnacao dos Engaging (asof = max close_date).
SELECT
    CASE WHEN c.series = 'GTX' THEN 'GTX' WHEN c.series = 'MG' THEN 'MG' ELSE 'GTK' END
        AS linha,
       COUNT(*) AS leads, SUM(c.sales_price) AS valor_tabela
FROM pipe AS p JOIN cat AS c ON c.product = p.product
WHERE p.deal_stage IN ('Engaging', 'Prospecting')
GROUP BY 1 ORDER BY leads DESC;

WITH ref AS (SELECT MAX(close_date::DATE) AS asof FROM pipe)
SELECT COUNT(*) AS engaging,
       SUM(CASE WHEN DATE_DIFF('day', p.engage_date::DATE, ref.asof) <= 138 THEN 1 ELSE 0 END)
         AS viaveis_ate_138d,
       SUM(CASE WHEN DATE_DIFF('day', p.engage_date::DATE, ref.asof) BETWEEN 139 AND 250
                THEN 1 ELSE 0 END) AS estagnados_139_250,
       SUM(CASE WHEN DATE_DIFF('day', p.engage_date::DATE, ref.asof) > 250 THEN 1 ELSE 0 END)
         AS estagnados_251_mais
FROM pipe AS p, ref WHERE p.deal_stage = 'Engaging';


-- 35. Precedente de fechamento tardio: teto de ciclo dos fechados (expiracao ~138d).
SELECT deal_stage, COUNT(*) AS n,
       MAX(DATE_DIFF('day', engage_date::DATE, close_date::DATE)) AS ciclo_max,
       SUM(CASE WHEN DATE_DIFF('day', engage_date::DATE, close_date::DATE) > 90
                THEN 1 ELSE 0 END) AS acima_90d,
       SUM(CASE WHEN DATE_DIFF('day', engage_date::DATE, close_date::DATE) > 138
                THEN 1 ELSE 0 END) AS acima_138d
FROM pipe WHERE deal_stage IN ('Won', 'Lost')
GROUP BY deal_stage;


-- 36. Habilidade de recuperador: share de Won tardio (>90d) por agente, sinal vs ruido.
WITH ag AS (
  SELECT sales_agent, COUNT(*) AS won,
         COUNT(*) FILTER (WHERE DATE_DIFF('day', engage_date::DATE, close_date::DATE) > 90)
           AS tardios
  FROM pipe WHERE deal_stage = 'Won'
  GROUP BY sales_agent HAVING COUNT(*) >= 20
),
gg AS (SELECT SUM(tardios)::DOUBLE / SUM(won) AS pg FROM ag),
g AS (SELECT won, tardios::DOUBLE / won AS p,
             1.96 * SQRT((tardios::DOUBLE / won) * (1 - tardios::DOUBLE / won) / won) AS moe
      FROM ag)
SELECT ROUND(100 * (SELECT gg.pg FROM gg), 1) AS tardio_global_pct,
       ROUND(100 * STDDEV_SAMP(p), 1) AS sd_observado_pp,
       ROUND(100 * SQRT(AVG(p * (1 - p) / won)), 1) AS sd_esperado_ruido_pp,
       SUM(CASE WHEN p - moe > (SELECT gg.pg FROM gg) OR p + moe < (SELECT gg.pg FROM gg)
                THEN 1 ELSE 0 END) AS agentes_signif
FROM g;


-- 37. Curva de decaimento de momentum: fracao dos Won com ciclo >= idade (CCDF).
-- Serve como peso de momentum por idade de engajamento, sem parametro arbitrario.
WITH w AS (
  SELECT DATE_DIFF('day', engage_date::DATE, close_date::DATE) AS c
  FROM pipe WHERE deal_stage = 'Won'
),
t(idade) AS (VALUES (0), (30), (57), (68), (90), (120), (138))
SELECT t.idade AS idade_dias,
       ROUND(t.idade / 57.0, 2) AS multiplo_mediana,
       ROUND(100.0 * (SELECT COUNT(*) FROM w WHERE w.c >= t.idade)
             / (SELECT COUNT(*) FROM w), 1) AS pct_won_restante
FROM t ORDER BY t.idade;


-- ===========================================================================
-- Descritores e concentracao: consultas que sustentam os numeros do documento.
-- ===========================================================================

-- 38. Descritores da base de contas: contagem, setores, paises, EUA, matrizes.
SELECT COUNT(*) AS contas,
       COUNT(DISTINCT a.sector) AS setores,
       COUNT(DISTINCT a.office_location) AS paises,
       ROUND(100.0 * COUNT(*) FILTER (WHERE a.office_location = 'United States')
             / COUNT(*), 1) AS eua_pct,
       COUNT(a.subsidiary_of) AS com_matriz
FROM 'data/normalized/accounts.csv' AS a;


-- 39. Porte: medianas de receita e de funcionarios das contas.
SELECT ROUND(MEDIAN(a.revenue), 1) AS receita_mediana,
       MEDIAN(a.employees) AS funcionarios_mediana
FROM 'data/normalized/accounts.csv' AS a;


-- 40. Concentracao de receita: participacao dos 20% maiores clientes (Won).
WITH ac AS (
  SELECT p.account, SUM(p.close_value) AS receita
  FROM pipe AS p
  WHERE p.deal_stage = 'Won' AND p.account IS NOT NULL
  GROUP BY p.account
),
r AS (SELECT receita, ROW_NUMBER() OVER (ORDER BY receita DESC) AS pos,
             COUNT(*) OVER () AS n FROM ac)
SELECT ROUND(100.0 * SUM(r.receita) FILTER (WHERE r.pos <= CEIL(r.n * 0.2))
             / SUM(r.receita), 1) AS top20_pct_receita
FROM r;


-- 41. Participacao da linha nas vendas: quantidade e receita de Won por serie.
SELECT c.series,
       COUNT(*) FILTER (WHERE p.deal_stage = 'Won') AS won,
       ROUND(100.0 * COUNT(*) FILTER (WHERE p.deal_stage = 'Won')
             / SUM(COUNT(*) FILTER (WHERE p.deal_stage = 'Won')) OVER (), 1) AS won_qtd_pct,
       ROUND(100.0 * SUM(p.close_value) FILTER (WHERE p.deal_stage = 'Won')
             / SUM(SUM(p.close_value) FILTER (WHERE p.deal_stage = 'Won')) OVER (), 1)
         AS won_receita_pct
FROM pipe AS p JOIN cat AS c ON c.product = p.product
GROUP BY c.series ORDER BY won_receita_pct DESC;


-- 42. Sequencia de up-sell GTX: 1o topo antes ou depois do 1o produto de entrada.
WITH ww AS (
  SELECT p.account, p.product, p.close_date::DATE AS d
  FROM pipe AS p WHERE p.deal_stage = 'Won' AND p.account IS NOT NULL
),
f AS (
  SELECT ww.account,
         MIN(ww.d) FILTER (WHERE ww.product = 'GTX Basic') AS entrada,
         MIN(ww.d) FILTER (WHERE ww.product IN ('GTX Pro', 'GTX Plus Pro')) AS topo
  FROM ww GROUP BY ww.account
)
SELECT COUNT(*) FILTER (WHERE f.entrada IS NOT NULL AND f.topo IS NOT NULL) AS contas,
       COUNT(*) FILTER (WHERE f.topo > f.entrada) AS topo_depois,
       COUNT(*) FILTER (WHERE f.topo <= f.entrada) AS topo_antes_ou_junto
FROM f;

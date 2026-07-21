-- modeling.sql --- Constroi a base de modelagem do scoring de leads (DuckDB).
--
-- Le a fonte normalizada em 'data/normalized/' e escreve os artefatos empiricos
-- e a base de features em 'data/derived/', a camada regeneravel consumida pelo
-- composto em Common Lisp (Fase 4 da tarefa 3RJ8). A metodologia esta em
-- 'docs/metodologia-scoring.md' (ADR C4X9); os achados, em
-- 'docs/analise-exploratoria.md'.
--
-- Esta fase entrega os valores brutos das dimensoes e os parametros empiricos,
-- nao o score: a normalizacao por percentil, os pesos e o composto ficam na
-- Fase 4. O portao de elegibilidade (conta existente; iniciadas com idade de
-- engajamento <= 138 dias) e aplicado aqui, na geracao.
--
-- O diretorio de saida deve existir. Executar a partir da raiz do projeto:
--   mkdir -p data/derived && duckdb < scripts/modeling.sql
--
-- A data de referencia ('as of') e a maxima close_date do dataset, 2017-12-31,
-- pelo mesmo padrao da EDA. As views base e a view 'recompra' reproduzem as da
-- EDA. SQL especifico do DuckDB: COPY ... TO, range/UNNEST, arg_max, MEDIAN.

CREATE OR REPLACE TEMP VIEW pipe AS
  SELECT account, sales_agent, product, deal_stage, close_value, engage_date, close_date
  FROM 'data/normalized/sales_pipeline.csv';
CREATE OR REPLACE TEMP VIEW cat AS
  SELECT product, series, sales_price FROM 'data/normalized/products.csv';
CREATE OR REPLACE TEMP VIEW acct AS
  SELECT account, sector FROM 'data/normalized/accounts.csv';
CREATE OR REPLACE TEMP VIEW ref AS
  SELECT MAX(close_date::DATE) AS asof FROM pipe;

-- Recompra: intervalo entre Won consecutivos do mesmo par conta-produto.
CREATE OR REPLACE TEMP VIEW recompra AS
  SELECT product, account,
         DATE_DIFF('day',
                   LAG(close_date::DATE) OVER (PARTITION BY account, product
                                               ORDER BY close_date::DATE),
                   close_date::DATE) AS gap
  FROM pipe
  WHERE deal_stage = 'Won' AND account IS NOT NULL;

-- Cadencia por produto: mediana do intervalo de recompra e contagem de intervalos.
CREATE OR REPLACE TEMP VIEW cadence AS
  SELECT product, MEDIAN(gap) AS cadence_days, COUNT(gap) AS n_intervals
  FROM recompra
  WHERE gap IS NOT NULL
  GROUP BY product;

-- Ciclo de engajamento a fechamento dos Won, insumo da curva de decaimento.
CREATE OR REPLACE TEMP VIEW won_cycle AS
  SELECT DATE_DIFF('day', engage_date::DATE, close_date::DATE) AS cycle
  FROM pipe
  WHERE deal_stage = 'Won';

-- Historico de Won por par conta-produto: contagem (afinidade), ultimo
-- fechamento, valor da compra mais recente (diagnostico) e ticket medio do par
-- (media de close_value), o insumo economico do Retorno. Consumido pelas listas.
-- ARG_MAX ordena por um struct (data, valor) para desempatar de modo
-- deterministico os Won com a mesma data de fechamento; sem o desempate, o
-- valor escolhido varia entre execucoes.
CREATE OR REPLACE TEMP VIEW pair_won AS
  SELECT account, product, COUNT(*) AS won_count,
         MAX(close_date::DATE) AS last_close,
         ARG_MAX(close_value, {'d': close_date::DATE, 'v': close_value})
           AS last_close_value,
         AVG(close_value) AS pair_won_avg
  FROM pipe
  WHERE deal_stage = 'Won' AND account IS NOT NULL
  GROUP BY account, product;

-- Media de Won do par por setor e produto, entre as contas do setor que compram
-- o produto (media entre compradores): recuo da afinidade onde o par tem pouca
-- historia, como prior de consumo tipico.
CREATE OR REPLACE TEMP VIEW sector_avg AS
  SELECT ac.sector, pw.product, AVG(pw.won_count) AS sector_won_avg
  FROM pair_won AS pw
  JOIN acct AS ac ON ac.account = pw.account
  GROUP BY ac.sector, pw.product;

-- Ticket medio de Won por setor e produto (media de close_value por transacao Won
-- do setor): recuo economico do Retorno onde o par nao tem historico de venda.
CREATE OR REPLACE TEMP VIEW sector_ticket AS
  SELECT ac.sector, p.product, AVG(p.close_value) AS sector_ticket_avg
  FROM pipe AS p
  JOIN acct AS ac ON ac.account = p.account
  WHERE p.deal_stage = 'Won' AND p.account IS NOT NULL
  GROUP BY ac.sector, p.product;


-- 1. cadence.csv: cadencia mediana de recompra por produto.
COPY (
  SELECT c.product, c.series, c.sales_price AS list_price,
         cad.cadence_days, cad.n_intervals
  FROM cadence AS cad
  JOIN cat AS c ON c.product = cad.product
  ORDER BY cad.cadence_days
) TO 'data/derived/cadence.csv' (HEADER, DELIMITER ',');


-- 2. decay.csv: CCDF pos-engajamento, a fracao de Won com ciclo >= idade, por
-- idade de 0 a 138 dias. E o peso de decaimento das iniciadas.
COPY (
  WITH ages AS (SELECT UNNEST(RANGE(0, 139)) AS age)
  SELECT a.age AS age_days,
         ROUND(AVG(CASE WHEN w.cycle >= a.age THEN 1.0 ELSE 0.0 END), 4) AS win_fraction
  FROM ages AS a
  CROSS JOIN won_cycle AS w
  GROUP BY a.age
  ORDER BY a.age
) TO 'data/derived/decay.csv' (HEADER, DELIMITER ',');


-- 3. adherence.csv: por agente e produto, os Won no produto e na serie (recuo).
-- A grade cobre os 35 agentes do time, inclusive os sem historico (contagem 0).
COPY (
  WITH won_ap AS (
    SELECT sales_agent, product, COUNT(*) AS won_product
    FROM pipe
    WHERE deal_stage = 'Won'
    GROUP BY sales_agent, product
  ),
  won_as AS (
    SELECT p.sales_agent, c.series, COUNT(*) AS won_series
    FROM pipe AS p
    JOIN cat AS c ON c.product = p.product
    WHERE p.deal_stage = 'Won'
    GROUP BY p.sales_agent, c.series
  ),
  agents AS (SELECT sales_agent FROM 'data/normalized/sales_teams.csv')
  SELECT ag.sales_agent, c.product, c.series,
         COALESCE(wa.won_product, 0) AS won_product,
         COALESCE(ws.won_series, 0) AS won_series
  FROM agents AS ag
  CROSS JOIN cat AS c
  LEFT JOIN won_ap AS wa ON wa.sales_agent = ag.sales_agent AND wa.product = c.product
  LEFT JOIN won_as AS ws ON ws.sales_agent = ag.sales_agent AND ws.series = c.series
  ORDER BY ag.sales_agent, c.product
) TO 'data/derived/adherence.csv' (HEADER, DELIMITER ',');


-- 4. potentials_base.csv: a grade contas conhecidas x produtos, menos os pares
-- atualmente em engajamento (iniciados). Nao engaging (inclusive Prospecting e
-- so-historico) permanece potencial. Features do par: preco de tabela e o ticket
-- medio do par com recuo por setor (economico), Won do par (afinidade) com media
-- de setor (recuo), dias desde o ultimo fechamento e cadencia (maturidade), e o
-- valor da compra mais recente (diagnostico).
COPY (
  WITH engaged_pairs AS (
    SELECT DISTINCT account, product
    FROM pipe
    WHERE deal_stage = 'Engaging' AND account IS NOT NULL
  )
  SELECT ac.account, ac.sector, c.product, c.series,
         c.sales_price AS list_price,
         ROUND(COALESCE(pw.pair_won_avg, st.sector_ticket_avg, c.sales_price), 2)
           AS economic_value,
         pw.last_close_value,
         cad.cadence_days,
         COALESCE(pw.won_count, 0) AS pair_won_count,
         ROUND(COALESCE(sa.sector_won_avg, 0), 3) AS sector_won_avg,
         DATE_DIFF('day', pw.last_close, r.asof) AS days_since_last_close
  FROM acct AS ac
  CROSS JOIN cat AS c
  CROSS JOIN ref AS r
  LEFT JOIN pair_won AS pw ON pw.account = ac.account AND pw.product = c.product
  LEFT JOIN sector_avg AS sa ON sa.sector = ac.sector AND sa.product = c.product
  LEFT JOIN sector_ticket AS st ON st.sector = ac.sector AND st.product = c.product
  LEFT JOIN cadence AS cad ON cad.product = c.product
  WHERE NOT EXISTS (
    SELECT 1 FROM engaged_pairs AS op
    WHERE op.account = ac.account AND op.product = c.product)
  ORDER BY ac.account, c.product
) TO 'data/derived/potentials_base.csv' (HEADER, DELIMITER ',');


-- 5. initiated_base.csv: as oportunidades Engaging com conta e idade de
-- engajamento <= 138 dias (o portao), insumo de decaimento das iniciadas.
COPY (
  SELECT p.opportunity_id, p.account, ac.sector, p.product, p.sales_agent,
         c.sales_price AS list_price,
         ROUND(COALESCE(pw.pair_won_avg, st.sector_ticket_avg, c.sales_price), 2)
           AS economic_value,
         COALESCE(pw.won_count, 0) AS pair_won_count,
         ROUND(COALESCE(sa.sector_won_avg, 0), 3) AS sector_won_avg,
         DATE_DIFF('day', p.engage_date::DATE, r.asof) AS engagement_age_days
  FROM 'data/normalized/sales_pipeline.csv' AS p
  CROSS JOIN ref AS r
  JOIN cat AS c ON c.product = p.product
  LEFT JOIN acct AS ac ON ac.account = p.account
  LEFT JOIN pair_won AS pw ON pw.account = p.account AND pw.product = p.product
  LEFT JOIN sector_avg AS sa ON sa.sector = ac.sector AND sa.product = p.product
  LEFT JOIN sector_ticket AS st ON st.sector = ac.sector AND st.product = p.product
  WHERE p.deal_stage = 'Engaging'
    AND p.account IS NOT NULL
    AND DATE_DIFF('day', p.engage_date::DATE, r.asof) BETWEEN 0 AND 138
  ORDER BY engagement_age_days
) TO 'data/derived/initiated_base.csv' (HEADER, DELIMITER ',');


-- 6. Assercoes, fail-closed: 0 linhas = aprovado. Cada ramo retorna uma linha
-- apenas quando o derivado diverge de um valor canonico da EDA.
WITH decay_pts AS (
  SELECT ages.age, AVG(CASE WHEN w.cycle >= ages.age THEN 1.0 ELSE 0.0 END) AS f
  FROM won_cycle AS w
  CROSS JOIN (SELECT UNNEST([57, 68, 90, 138]) AS age) AS ages
  GROUP BY ages.age
),
eng AS (
  SELECT COUNT(*) AS n
  FROM 'data/normalized/sales_pipeline.csv' AS p
  CROSS JOIN ref AS r
  WHERE p.deal_stage = 'Engaging'
    -- Verifica o valor canonico da EDA (298 de 1.589 Engaging dentro de 138
    -- dias, sem filtro de conta; ver 'docs/analise-exploratoria.md'). NAO e um
    -- espelho da emissao de 'initiated_base', que e a subpopulacao com conta.
    AND DATE_DIFF('day', p.engage_date::DATE, r.asof) <= 138
),
gtk AS (
  SELECT COUNT(DISTINCT sales_agent) AS n
  FROM pipe
  WHERE product = 'GTK 500' AND deal_stage = 'Won'
)
SELECT 'cadence_out_of_range' AS chk, cad.product || '=' || cad.cadence_days AS detail
FROM cadence AS cad
WHERE cad.n_intervals >= 30 AND (cad.cadence_days < 12 OR cad.cadence_days > 32)
UNION ALL
SELECT 'gtk_agents_not_3' AS chk, gtk.n::VARCHAR AS detail
FROM gtk WHERE gtk.n <> 3
UNION ALL
SELECT 'decay_point_off' AS chk,
       decay_pts.age || '=' || ROUND(decay_pts.f, 3) AS detail
FROM decay_pts
WHERE (decay_pts.age = 57 AND ABS(decay_pts.f - 0.50) > 0.05)
   OR (decay_pts.age = 68 AND ABS(decay_pts.f - 0.43) > 0.05)
   OR (decay_pts.age = 90 AND ABS(decay_pts.f - 0.24) > 0.05)
   OR (decay_pts.age = 138 AND decay_pts.f > 0.02)
UNION ALL
SELECT 'engaging_within_138_not_298' AS chk, eng.n::VARCHAR AS detail
FROM eng WHERE eng.n <> 298
UNION ALL
SELECT 'accounts_not_85' AS chk, (SELECT COUNT(*) FROM acct)::VARCHAR AS detail
WHERE (SELECT COUNT(*) FROM acct) <> 85
UNION ALL
SELECT 'products_not_7' AS chk, (SELECT COUNT(*) FROM cat)::VARCHAR AS detail
WHERE (SELECT COUNT(*) FROM cat) <> 7;

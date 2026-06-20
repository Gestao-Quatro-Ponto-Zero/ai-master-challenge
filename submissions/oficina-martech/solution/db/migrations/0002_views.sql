-- 0002_views — Views auditáveis (a lógica de negócio fica legível em SQL)
-- O scoring final (smoothing bayesiano, pesos) é em Python; estas views dão
-- transparência e facilitam validação direta no banco pelo avaliador.

-- Deals abertos = universo a priorizar (Prospecting + Engaging)
DROP VIEW IF EXISTS v_open_deals;
CREATE VIEW v_open_deals AS
SELECT
    p.opportunity_id,
    p.sales_agent,
    t.manager,
    t.regional_office,
    p.product,
    pr.series,
    pr.sales_price,
    p.account,
    a.sector,
    p.deal_stage,
    p.engage_date,
    -- Ancorado à ÚLTIMA data do dataset (não 'now'): o dataset é histórico (~2017),
    -- usar a data atual faria todo deal parecer ter milhares de dias. (ver process-log G3)
    CAST(julianday((SELECT MAX(close_date) FROM sales_pipeline)) - julianday(p.engage_date) AS INTEGER) AS days_open  -- NULL p/ Prospecting
FROM sales_pipeline p
JOIN sales_teams t ON t.sales_agent = p.sales_agent
JOIN products    pr ON pr.product   = p.product
LEFT JOIN accounts a ON a.account    = p.account
WHERE p.deal_stage IN ('Prospecting','Engaging');

-- Win-rate histórico por vendedor (sinal primário do scoring, auditável)
DROP VIEW IF EXISTS v_agent_winrate;
CREATE VIEW v_agent_winrate AS
SELECT
    sales_agent,
    SUM(CASE WHEN deal_stage = 'Won' THEN 1 ELSE 0 END)                         AS wins,
    SUM(CASE WHEN deal_stage IN ('Won','Lost') THEN 1 ELSE 0 END)               AS closed,
    ROUND(1.0 * SUM(CASE WHEN deal_stage = 'Won' THEN 1 ELSE 0 END)
            / NULLIF(SUM(CASE WHEN deal_stage IN ('Won','Lost') THEN 1 ELSE 0 END), 0), 4) AS win_rate
FROM sales_pipeline
GROUP BY sales_agent;

-- Saúde do pipeline (painel RevOps)
DROP VIEW IF EXISTS v_pipeline_health;
CREATE VIEW v_pipeline_health AS
SELECT
    (SELECT COUNT(*) FROM sales_pipeline)                                              AS total_deals,
    (SELECT COUNT(*) FROM sales_pipeline WHERE deal_stage IN ('Prospecting','Engaging')) AS open_deals,
    (SELECT COUNT(*) FROM sales_pipeline WHERE account IS NULL)                         AS deals_sem_conta,
    (SELECT ROUND(AVG(julianday(close_date) - julianday(engage_date)))
       FROM sales_pipeline WHERE deal_stage = 'Won')                                   AS ciclo_medio_won_dias;

-- 0004_refine_datas — âncora de datas robusta + as_of_date explícito
-- Motivo (ver process-log G3 / decisoes V7): o dataset é histórico (~2017);
-- "hoje" real (2026) é inútil — o "hoje" do universo dos dados é a data do
-- ÚLTIMO evento observado. A âncora anterior (MAX(close_date)) funcionava, mas
-- geraria days_open NEGATIVO se algum deal fosse engajado APÓS o último
-- fechamento (risco real num refresco/reload dos dados).
-- Âncora robusta = MAX de qualquer evento (close OU engage) = ponto exato em
-- que o dataset congela. as_of_date é exposto para a UI mostrar "avaliado em
-- {data}", deixando explícito que o "hoje" é o fim do dataset — não a data
-- real — e preservando a honestidade do modelo temporal.
-- Views são derivadas (sem dados próprios): recriar é seguro e idempotente.

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
    -- Âncora = último evento de TODO o pipeline (close de fechados OU engage de
    -- abertos). Nunca negativo: nenhum deal é engajado depois do congelamento.
    CAST(julianday((SELECT MAX(COALESCE(close_date, engage_date)) FROM sales_pipeline))
         - julianday(p.engage_date) AS INTEGER) AS days_open  -- NULL p/ Prospecting
FROM sales_pipeline p
JOIN sales_teams t ON t.sales_agent = p.sales_agent
JOIN products    pr ON pr.product   = p.product
LEFT JOIN accounts a ON a.account    = p.account
WHERE p.deal_stage IN ('Prospecting','Engaging');

DROP VIEW IF EXISTS v_pipeline_health;
CREATE VIEW v_pipeline_health AS
SELECT
    (SELECT MAX(COALESCE(close_date, engage_date)) FROM sales_pipeline)                 AS as_of_date,
    (SELECT COUNT(*) FROM sales_pipeline)                                              AS total_deals,
    (SELECT COUNT(*) FROM sales_pipeline WHERE deal_stage IN ('Prospecting','Engaging')) AS open_deals,
    (SELECT COUNT(*) FROM sales_pipeline WHERE account IS NULL)                         AS deals_sem_conta,
    (SELECT ROUND(AVG(julianday(close_date) - julianday(engage_date)))
       FROM sales_pipeline WHERE deal_stage = 'Won')                                   AS ciclo_medio_won_dias;

-- 0005_health_sem_conta_abertos — coerência do indicador "sem conta"
-- Antes: deals_sem_conta contava TODO o pipeline (8800). Como o app divide por
-- open_deals (2089) para mostrar "% sem conta", numerador e denominador ficavam
-- em universos diferentes. Na prática os 1425 deals sem conta JÁ são todos
-- abertos (Won/Lost têm conta 100% preenchida), então o número não muda — mas
-- tornar o filtro explícito deixa o SQL autoexplicativo e à prova de regressão.
-- Views são derivadas (sem dados próprios): recriar é seguro e idempotente.

DROP VIEW IF EXISTS v_pipeline_health;
CREATE VIEW v_pipeline_health AS
SELECT
    (SELECT MAX(COALESCE(close_date, engage_date)) FROM sales_pipeline)                 AS as_of_date,
    (SELECT COUNT(*) FROM sales_pipeline)                                              AS total_deals,
    (SELECT COUNT(*) FROM sales_pipeline WHERE deal_stage IN ('Prospecting','Engaging')) AS open_deals,
    -- numerador e denominador ambos sobre ABERTOS (mesmo universo do %)
    (SELECT COUNT(*) FROM sales_pipeline
       WHERE deal_stage IN ('Prospecting','Engaging')
         AND (account IS NULL OR TRIM(account) = ''))                                  AS deals_sem_conta,
    (SELECT ROUND(AVG(julianday(close_date) - julianday(engage_date)))
       FROM sales_pipeline WHERE deal_stage = 'Won')                                   AS ciclo_medio_won_dias;

-- ============================================================
-- IMPORT: Mapear staging (nomes texto) → sales_pipeline (IDs)
-- Executar APÓS importar os 4 CSVs:
--   1. accounts.csv → accounts
--   2. products.csv → products
--   3. sales_teams.csv → sales_teams
--   4. sales_pipeline.csv → sales_pipeline_staging
-- ============================================================

-- Inserir na tabela definitiva mapeando nomes → IDs
INSERT INTO sales_pipeline (
  opportunity_id,
  sales_agent_id,
  product_id,
  account_id,
  deal_stage,
  engage_date,
  close_date,
  close_value
)
SELECT
  s.opportunity_id,
  st.id AS sales_agent_id,
  p.id AS product_id,
  a.id AS account_id,
  s.deal_stage,
  s.engage_date,
  s.close_date,
  s.close_value
FROM sales_pipeline_staging s
JOIN sales_teams st ON st.sales_agent = s.sales_agent
JOIN products p ON p.name = s.product
JOIN accounts a ON a.name = s.account;

-- Verificar se todos os registros foram mapeados
DO $$
DECLARE
  staging_count integer;
  pipeline_count integer;
BEGIN
  SELECT count(*) INTO staging_count FROM sales_pipeline_staging;
  SELECT count(*) INTO pipeline_count FROM sales_pipeline;

  IF staging_count != pipeline_count THEN
    RAISE EXCEPTION 'MISMATCH: staging=%, pipeline=%. Verificar dados não mapeados.',
      staging_count, pipeline_count;
  ELSE
    RAISE NOTICE 'OK: % registros importados com sucesso.', pipeline_count;
  END IF;
END $$;

-- Limpar tabela de staging
DROP TABLE sales_pipeline_staging;

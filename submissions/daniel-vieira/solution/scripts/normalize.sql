-- normalize.sql --- Gera a fonte CSV normalizada do dataset CRM (DuckDB).
--
-- Le os CSV brutos imutaveis em 'data/' e escreve copias normalizadas em
-- 'data/normalized/', a fonte canonica consumida pela EDA e pela modelagem.
-- Este script e a fonte unica de verdade das correcoes de limpeza.
--
-- O diretorio de saida deve existir. Executar a partir da raiz do projeto:
--   mkdir -p data/normalized && duckdb < scripts/normalize.sql
--
-- Correcoes aplicadas por igualdade exata (CASE), para nao afetar por engano
-- valores que contenham o token como subcadeia:
--   sales_pipeline.product   : 'GTXPro'     -> 'GTX Pro'     (alinha ao catalogo)
--   accounts.sector          : 'technolgy'  -> 'technology'  (grafia)
--   accounts.office_location : 'Philipines' -> 'Philippines' (grafia)
-- Os demais arquivos sao copiados sem alteracao, para que 'data/normalized/'
-- seja a fonte completa.
--
-- SQL especifico do DuckDB: SELECT * REPLACE e COPY ... TO com opcoes.

COPY (
  SELECT * REPLACE (
    CASE WHEN product = 'GTXPro' THEN 'GTX Pro' ELSE product END AS product)
  FROM 'data/sales_pipeline.csv'
) TO 'data/normalized/sales_pipeline.csv' (HEADER, DELIMITER ',');

COPY (
  SELECT * REPLACE (
    CASE WHEN sector = 'technolgy' THEN 'technology' ELSE sector END AS sector,
    CASE WHEN office_location = 'Philipines' THEN 'Philippines'
         ELSE office_location END AS office_location)
  FROM 'data/accounts.csv'
) TO 'data/normalized/accounts.csv' (HEADER, DELIMITER ',');

COPY (SELECT * FROM 'data/products.csv')
  TO 'data/normalized/products.csv' (HEADER, DELIMITER ',');
COPY (SELECT * FROM 'data/sales_teams.csv')
  TO 'data/normalized/sales_teams.csv' (HEADER, DELIMITER ',');
COPY (SELECT * FROM 'data/metadata.csv')
  TO 'data/normalized/metadata.csv' (HEADER, DELIMITER ',');

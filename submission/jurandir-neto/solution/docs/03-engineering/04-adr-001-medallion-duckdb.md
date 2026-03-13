# ADR-001: Arquitetura Medallion com DuckDB e Parquet

**Status:** Aceito
**Data:** 2026-03-11

## Contexto

Os dados são cinco arquivos CSV estáticos (Kaggle). O pipeline precisa: (1) preservar os dados brutos, (2) transformá-los em um modelo dimensional confiável, (3) produzir tabelas otimizadas para o dashboard e o agente, e (4) ser re-executável diariamente de forma simples.

## Decisão

Adotar a arquitetura Medallion em três camadas (bronze → silver → gold), com DuckDB como motor de transformação e Parquet como formato de armazenamento em cada camada.

## Motivação

**DuckDB:**
- Roda in-process em Python — sem servidor, sem infraestrutura externa
- Lê e escreve Parquet nativamente
- SQL analítico completo (window functions, CTEs, lateral joins)
- Performance adequada para o volume dos dados (~30K linhas)

**Parquet:**
- Formato colunar — leitura seletiva de colunas (eficiente para Streamlit)
- Preserva tipos corretamente (datas, booleans, floats)
- Leve e portátil

**Medallion:**
- Bronze: rastreabilidade — sempre é possível reprocessar a partir dos dados brutos
- Silver: separação de responsabilidades — limpeza e modelagem num único lugar
- Gold: queries simples no Streamlit — sem joins no tempo de renderização

## Consequências

- O re-processamento completo (raw → gold) deve durar menos de 60 segundos
- Arquivos Parquet não são commitados no git — apenas os scripts de transformação
- Se a fonte de dados mudar (ex: API em vez de CSV), apenas `pipeline/bronze/run_bronze.py` precisa ser alterado
- Silver e gold são sempre recalculados do zero a cada execução (sem upserts incrementais nessa fase)

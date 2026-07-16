## Why

O time comercial de 35 vendedores gerencia ~8.800 oportunidades no pipeline sem critério objetivo de priorização. Deals quentes esfriam enquanto vendedores perdem tempo em oportunidades de baixo potencial. A Head de RevOps precisa de uma ferramenta funcional — não um modelo num notebook — que o vendedor abra na segunda-feira e saiba onde focar.

## What Changes

- Aplicação web funcional (Streamlit) com scoring de leads baseado em regras + heurísticas extraídas dos dados históricos
- Pipeline visual com filtros por vendedor, manager e região
- Score explicável: vendedor vê quais fatores contribuíram para cada nota
- Priorização automática: deals ordenados por score, destacando os top N para ação imediata
- Relatório executivo com métricas agregadas do pipeline

## Capabilities

### New Capabilities
- `lead-scoring-engine`: Core de scoring com regras baseadas em deal stage, tempo no pipeline, fit da conta, histórico do vendedor e produto
- `pipeline-dashboard`: Interface interativa com pipeline filtrado, ordenado por score, com cards de deal expansíveis
- `deal-explainability`: Breakdown visual de cada fator que compõe o score de um deal
- `sales-analytics`: Métricas agregadas (win rate por vendedor, tempo médio por estágio, valor total do pipeline)

### Modified Capabilities

*(nenhuma — mudança greenfield)*

## Impact

- Novo diretório `src/` com código da aplicação Streamlit
- Dependências: streamlit, pandas, plotly (para gráficos)
- Dados: usa os 4 CSVs existentes em `data/`
- Sem impacto em sistemas existentes — solução autônoma

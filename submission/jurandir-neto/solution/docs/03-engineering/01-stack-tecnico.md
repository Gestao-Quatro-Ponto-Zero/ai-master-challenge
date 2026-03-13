# Stack Técnico

## Visão geral

| Camada | Tecnologia | Papel |
|--------|-----------|-------|
| Ingestão | CSV (Kaggle) | Fonte dos dados brutos |
| Processamento | Python + DuckDB | Transformações bronze → silver → gold |
| Armazenamento | Parquet (local) | Formato de saída de cada camada |
| Dashboard | Streamlit | Interface visual com filtros e chat do agente |
| Agente | Agno + Claude Sonnet 4.6 | Diagnóstico, interpretação e planos de ação |
| LLM | Anthropic API (`claude-sonnet-4-6`) | Modelo subjacente do agente |

## Detalhes de cada componente

### Python + DuckDB

DuckDB é o motor de transformação em todas as camadas. Roda in-process (sem servidor), lê e escreve Parquet nativamente, e suporta SQL analítico completo (window functions, CTEs, aggregations).

Cada camada tem seu script de transformação em `/pipeline/`:

```
pipeline/
├── bronze/   run_bronze.py   — carrega CSVs brutos, salva Parquet sem alteração
├── silver/   run_silver.py   — limpa, tipifica, cria fatos e dimensões
└── gold/     run_gold.py     — agrega, calcula scores, monta tabelas de consumo
```

### Streamlit

Interface do dashboard. Consome exclusivamente tabelas do `/data/gold/`. Atualização diária via reexecução do pipeline completo (bronze → silver → gold).

### Agno + Claude Sonnet 4.6

Framework de agente com tools tipadas em Python. O agente roda dentro do Streamlit (componente de chat). Acessa o gold layer via tools e consulta o playbook de CS via leitura de arquivo Markdown.

## Restrições

- O dashboard consome apenas tabelas gold — nunca silver ou bronze
- O agente acessa dados apenas via suas tools — sem queries diretas ad hoc
- Os arquivos Parquet ficam em `/data/{camada}/` — nunca commitados no git (`.gitignore`)
- Os CSVs brutos ficam em `/data/raw/` — também ignorados no git

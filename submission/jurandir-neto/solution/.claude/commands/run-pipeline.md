# /run-pipeline

Executa o pipeline completo de transformação de dados: Bronze → Silver → Gold.

## Sequência de execução

```bash
# 1. Bronze — ingestão dos CSVs raw para Parquet particionado
python pipeline/bronze/ingest.py

# 2. Silver — limpeza, tipagem e enriquecimento
python pipeline/silver/transform.py

# 3. Gold — métricas agregadas para o dashboard e agente
python pipeline/gold/aggregate.py
```

## O que verificar em cada etapa

### Bronze
- Os 5 arquivos Parquet foram criados em `data/bronze/`
- Nenhum erro de schema (colunas ausentes, tipos incompatíveis)
- Contagem de registros deve bater com os CSVs originais em `data/raw/`

### Silver
- Tabelas limpas em `data/silver/` — sem nulos em campos obrigatórios
- `churn_flag` é boolean consistente em accounts e subscriptions
- Datas foram parseadas corretamente (sem strings onde deveria haver date)
- `mrr_amount` e `arr_amount` são float, nunca negativos

### Gold
- Tabelas de métricas em `data/gold/` criadas com sucesso
- `churn_rate_by_segment.parquet` — churn rate por industry, plan_tier, country
- `risk_scores.parquet` — score de risco por account_id
- `feature_impact.parquet` — correlação de uso de features com churn
- `support_impact.parquet` — correlação de tickets com churn

## Como saber se teve sucesso

```bash
# Verifica existência e tamanho dos Parquets gerados
python -c "
import os, glob
for layer in ['bronze', 'silver', 'gold']:
    files = glob.glob(f'data/{layer}/*.parquet')
    print(f'{layer}: {len(files)} arquivo(s)')
    for f in files:
        size = os.path.getsize(f)
        print(f'  {os.path.basename(f)}: {size:,} bytes')
"
```

Se todos os layers tiverem arquivos e os tamanhos forem maiores que zero, o pipeline rodou com sucesso.

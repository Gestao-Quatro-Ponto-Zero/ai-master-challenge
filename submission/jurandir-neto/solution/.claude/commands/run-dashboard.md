# /run-dashboard

Inicia o dashboard Streamlit de análise de churn da RavenStack.

## Pré-condições

Antes de iniciar, verificar se as gold tables existem:

```bash
python -c "
import glob
gold_files = glob.glob('data/gold/*.parquet')
if not gold_files:
    print('ERRO: Gold tables não encontradas. Execute /run-pipeline primeiro.')
else:
    print(f'OK: {len(gold_files)} gold table(s) disponível(is)')
    for f in gold_files:
        print(f'  {f}')
"
```

Se as gold tables não existirem, execute `/run-pipeline` antes de continuar.

## Instalação de dependências

```bash
pip install streamlit duckdb pandas plotly altair
```

Ou com uv:

```bash
uv pip install streamlit duckdb pandas plotly altair
```

## Iniciar o dashboard

```bash
streamlit run app/dashboard/main.py
```

O Streamlit abrirá automaticamente em `http://localhost:8501`.

## O que o dashboard mostra

- **Visão geral**: MRR total, churn rate do período, número de churns, seats em risco
- **Segmentação**: churn por industry, plan_tier, country, referral_source
- **Risco de contas**: ranking de contas com maior risco de churn (score + motivos)
- **Impacto de features**: features com maior correlação positiva/negativa com retenção
- **Suporte**: correlação entre tickets e churn (prioridade, satisfaction_score)
- **Diagnóstico**: respostas às 3 perguntas estratégicas com dados

## Parâmetros de filtro disponíveis

O dashboard aceita filtros na sidebar:
- Período (data início / data fim)
- Industry
- Plan tier
- País

# Solution — Diagnóstico de Churn RavenStack

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `diagnostico_churn_ravenstack.md` | Relatório completo respondendo as 3 perguntas do briefing |
| `contas_alto_risco.csv` | Lista de 81 contas para ação imediata de CS |
| `analise_exploratoria.py` | Código Python reproduzível |
| `requirements.txt` | Dependências Python |

## Como Executar

### Setup

```bash
# Criar ambiente virtual (opcional)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
```

### Executar Análise

```bash
# Colocar os CSVs em uma pasta ravenstack_data/
# Ajustar DATA_PATH no script se necessário

python analise_exploratoria.py
```

### Output

O script irá:
1. Carregar os 5 datasets
2. Calcular métricas básicas de churn
3. Analisar churn por segmento
4. Identificar core features
5. Calcular risk scores
6. Exportar lista de contas de alto risco

## Dados Esperados

O script espera os seguintes arquivos na pasta `ravenstack_data/`:

- `ravenstack_accounts.csv`
- `ravenstack_subscriptions.csv`
- `ravenstack_feature_usage.csv`
- `ravenstack_support_tickets.csv`
- `ravenstack_churn_events.csv`

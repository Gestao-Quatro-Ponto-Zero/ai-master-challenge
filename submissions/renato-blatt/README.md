# 🎯 Lead Scorer — Challenge 003

## O que é

Uma ferramenta que substitui o "feeling" na priorização de deals por inteligência baseada em dados reais do CRM. O vendedor abre o app, recebe um briefing personalizado gerado por IA e vê o pipeline ordenado por score — com explicação em português do motivo de cada prioridade.

## Por que funciona

A maioria das ferramentas de scoring ordena por valor. Essa não. Os dois critérios com maior peso são:
- **Winrate histórico do vendedor naquele perfil de conta** (35%) — vendedor errado mata o deal
- **Match produto × setor da conta** (30%) — produto certo para o setor é o maior sinal de fechamento

Completado por frescor do deal (20%) e valor (15%).

## Funcionalidades

- **Briefing de segunda-feira**: gerado por IA ao abrir o app, personalizado por vendedor
- **Pipeline priorizado**: todos os deals ordenados por score com explicação em linguagem natural
- **Agente de chat**: vendedor pergunta sobre qualquer deal e recebe resposta baseada nos dados reais
- **Visão do manager**: pipeline consolidado do time, winrate por vendedor, receita esperada

## Setup

### Pré-requisitos
- Python 3.9+
- Chave OpenAI (gpt-4o-mini)
- Dataset: [CRM Sales Predictive Analytics](https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics)

### Instalação
```bash
git clone <repo>
cd lead_scorer
python3 -m venv venv
source venv/bin/activate
pip install streamlit pandas plotly openai python-dotenv kagglehub
```

### Configuração
```bash
cp .env.example .env
# Edite .env e adicione sua chave OpenAI
```

### Download dos dados
```bash
python3 -c "import kagglehub; kagglehub.dataset_download('agungpambudi/crm-sales-predictive-analytics')"
```

### Rodar
```bash
streamlit run app.py
```

Acesse: `http://localhost:8501`

## Lógica de Scoring

| Critério | Peso | Justificativa |
|---|---|---|
| Winrate do vendedor no perfil | 35% | Performance histórica é o maior preditor de fechamento |
| Match produto × setor | 30% | Produto certo para o setor aumenta conversão significativamente |
| Frescor do deal | 20% | Deal parado esfria — penalização progressiva a partir de 60 dias |
| Valor do deal | 15% | Desempata deals similares |

## Limitações

- **Dados estáticos**: a solução lê CSVs locais. Para uso em produção, conectar via API do CRM
- **Datas do dataset**: o dataset original é de 2017/2018 — dias calculados relativamente à data máxima do dataset
- **Sem ML preditivo**: o scoring é baseado em regras e heurísticas. Um modelo XGBoost treinado no histórico Won/Lost poderia aumentar a acurácia
- **Chave de API**: cada usuário precisa de sua própria chave OpenAI

## Stack

Python · Streamlit · Pandas · Plotly · OpenAI API

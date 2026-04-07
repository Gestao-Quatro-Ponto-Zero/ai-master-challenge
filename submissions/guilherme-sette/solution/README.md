# Solution

## O que esta aqui

- `dashboard/app.py`: interface Streamlit
- `dashboard/analytics.py`: leitura dos dados e logica de scoring
- `dashboard/styles.css`: estilos da interface
- `.streamlit/config.toml`: tema e configuracao base
- `requirements.txt`: dependencias Python
- `data/`: os 4 CSVs usados pela aplicacao

## Como rodar

```bash
cd .../submissions/guilherme-sette/solution
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run dashboard/app.py
```

## Lógica resumida

- `Deal Forecast`
  - produto
  - conta
  - setor
  - revenue band
  - idade relativa do deal

- `Seller Fit`
  - fit contextual por conta/produto/setor/revenue band
  - fallback conservador por histórico do seller

- `Owner movement`
  - usado na visão da liderança para sugerir movimentação de carteira
  - vendedor vê apenas que recebeu o deal e o racional da mudança

## Limitações

- Sem dados de atividade ou `next_step`
- Sem margem, estoque ou lead time
- Muita ausência de `account` no pipeline aberto

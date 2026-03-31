# Setup — Como rodar a solução

## Pré-requisitos

- Python 3.9+
- pip

## Instalação

```bash
# 1. Navegue até a pasta da solução
cd submissions/Pedro-henrique-sonda/solution

# 2. Instale as dependências
pip install streamlit pandas

# 3. Rode a aplicação
streamlit run app.py
```

A aplicação abrirá automaticamente no navegador em `http://localhost:8501`.

## Estrutura dos dados

Os 4 CSVs do dataset já estão na pasta `data/`:
- `accounts.csv` — 85 contas
- `products.csv` — 7 produtos
- `sales_pipeline.csv` — ~8.800 oportunidades
- `sales_teams.csv` — 35 vendedores

Não é necessário baixar nada adicional.

## Uso

1. Abra a aplicação no navegador
2. Na barra lateral, selecione a faixa de valor desejada (Premium, Médio, Básico ou Todos)
3. Filtre por escritório, manager e/ou vendedor
4. Veja os Top 5 deals prioritários e marque o status de cada um conforme for trabalhando
5. Use a planilha Pipeline Completo para ver todos os deals, com checkbox para pontuação detalhada
6. Clique em "Como funciona o Score?" para entender a lógica completa

## Observações

- Os dados são de 2016-2017. A aplicação calcula automaticamente a data de referência (2017-12-22) ao invés de usar a data atual.
- O arquivo `data/deal_status.csv` é gerado automaticamente pela aplicação quando o vendedor marca status dos deals. Ele persiste entre sessões.
- A aplicação foi testada com Python 3.9 e Streamlit 1.50.0 no macOS.

# G4 | Lead Scorer — Local Setup

Aplicação Streamlit que transforma as oportunidades abertas do dataset **CRM Sales Predictive Analytics** em uma fila de decisões explicável.

## 1. Pré-requisitos

- Ubuntu, macOS ou Windows com Python 3.11+;
- repositório `ai-master-challenge` clonado;
- dataset baixado do Kaggle: `agungpambudi/crm-sales-predictive-analytics`.

## 2. Dataset local

O repositório ignora `datasets/`, portanto os CSVs **não fazem parte da submissão**.

Estrutura recomendada a partir da raiz do repositório:

```text
ai-master-challenge/
├── datasets/
│   └── crm-sales-predictive-analytics/
│       ├── accounts.csv
│       ├── metadata.csv
│       ├── products.csv
│       ├── sales_pipeline.csv
│       └── sales_teams.csv
└── submissions/
    └── lucio-castilho/
        └── solution/
```

A aplicação também aceita os quatro CSVs obrigatórios diretamente em `datasets/`.

Como alternativa, aponte qualquer pasta local com:

```bash
export CRM_DATA_DIR=/caminho/para/os/csvs
```

Arquivos obrigatórios:

- `accounts.csv`
- `products.csv`
- `sales_pipeline.csv`
- `sales_teams.csv`

`metadata.csv` é opcional para execução e serve como dicionário de dados.

## 3. Ambiente virtual

Na raiz do repositório:

```bash
cd submissions/lucio-castilho/solution
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Validação antes de iniciar o app

```bash
python -m compileall app.py src tests
pytest -q
```

Com o dataset disponível, os testes de integração validam inclusive:

- exatamente 2.089 oportunidades abertas;
- somente `Prospecting` e `Engaging` no ranking;
- scores entre 0 e 100;
- ausência de efeito de `close_date` e `close_value` no score das oportunidades abertas;
- scoring funcional mesmo sem `account`;
- ausência de CSVs dentro da pasta da solução.

## 5. Executar

```bash
streamlit run app.py
```

Abra o endereço indicado pelo Streamlit, normalmente:

```text
http://localhost:8501
```

## 6. Smoke test manual

1. Sem filtros, confirme `Open Deals = 2.089`.
2. Filtre por `Gerente`, `Agente de Vendas` e `Regional`.
3. Confirme que o filtro de vendedor respeita o gerente selecionado.
4. Abra um deal em `Focus Now` e confira score, fit, attention, evidence e recomendação.
5. Confirme que `Prospecting` mostra `Timeline unavailable`.
6. Exporte Excel e abra as abas `Prioritized Pipeline` e `Scoring Guide`.
7. Exporte PDF e confira filtros, resumo e prioridades.
8. Confirme que nenhum score é descrito como probabilidade de fechamento.

## 7. Problemas comuns

### `Dataset not found`

Confira a estrutura de `datasets/` ou defina `CRM_DATA_DIR`.

### Porta 8501 ocupada

```bash
streamlit run app.py --server.port 8502
```

### Ambiente virtual não ativo

```bash
source .venv/bin/activate
```

A metodologia detalhada está em `../docs/methodology.md`.

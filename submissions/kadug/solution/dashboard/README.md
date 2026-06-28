# Dashboard Streamlit

Este dashboard e minimo e deve funcionar como camada de apresentacao dos achados principais. Ele nao deve conter a logica analitica principal.

## Direcao

- Streamlit app em Python.
- Entrada por exports gerados pela analise (`JSON`/`CSV`).
- Sem duplicar joins, regras de risco ou calculos principais.
- Saida focada em stakeholders:
  - resumo executivo;
  - segmentos em risco;
  - contas prioritarias;
  - recomendacoes.

## Escopo minimo

- Ler exports estaticos gerados pela analise.
- Mostrar top 3 findings executivos.
- Mostrar segmentos em risco.
- Mostrar contas prioritarias.
- Mostrar backlog de acoes por stakeholder.

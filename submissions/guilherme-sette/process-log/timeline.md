# Timeline do desenvolvimento

## Fase 1 — Entendimento do problema

- leitura do README do challenge
- entendimento de que o deliverable principal precisava ser software funcional
- decisão de trabalhar com dados reais do dataset

## Fase 2 — Exploração dos dados

- leitura de `accounts.csv`, `products.csv`, `sales_teams.csv` e `sales_pipeline.csv`
- análise de:
  - produtos e famílias
  - ticket médio e distribuição
  - performance do time
  - cadência de pipeline
  - relação deals x clientes x vendedores
- identificação de problemas de higiene de CRM no pipeline aberto

## Fase 3 — Formulação da lógica

- decisão de modelar a solução em duas camadas:
  - `Deal Forecast`
  - `Seller Fit`
- normalização de `GTX Pro` e `GTXPro`
- decisão de manter explainability e evitar um modelo opaco de ML

## Fase 4 — Construção da dashboard

- implementação da solução em Streamlit
- criação das visões:
  - `VENDEDOR`
  - `HEAD`
- definição da lógica de priorização e explicação dos deals

## Fase 5 — Refinos de produto e UX

- simplificação da experiência do vendedor
- separação entre ação comercial e higiene de CRM
- decisão de que movimentação de owner deveria ser responsabilidade da liderança
- reforço da clareza na visão da `HEAD`

## Fase 6 — Debugging e estabilização

- correção de escala e exibição de forecast
- correção de gráfico da `HEAD`
- correção de strings HTML renderizadas como texto
- remoção de warnings de Plotly/Streamlit

## Fase 7 — Empacotamento da submissão

- criação da estrutura em `submissions/guilherme-sette/`
- cópia da solução para pasta autocontida
- montagem do README principal
- organização do process log
- limpeza do repositório para manter o PR aderente ao `CONTRIBUTING.md`

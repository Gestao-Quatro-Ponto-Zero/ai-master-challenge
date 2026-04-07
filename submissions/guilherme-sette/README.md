# Submissao — Guilherme Sette — Challenge 003

## Sobre mim

- **Nome:** Guilherme Sette
- **LinkedIn:** https://www.linkedin.com/in/guilhermesette/
- **Challenge escolhido:** Challenge 003 — Lead Scorer

---

## Executive Summary

Construí uma dashboard funcional em Streamlit para priorização comercial usando os dados reais do challenge. A solução combina `Deal Forecast` com uma lógica de `Seller Fit` explicável para orientar foco de vendas, apoiar movimentação de owners pela liderança e expor problemas de higiene de CRM que reduzem a confiabilidade do pipeline. A ferramenta foi desenhada para uso real: o vendedor abre a fila e entende o que atacar, enquanto a head de RevOps enxerga o forecast, a movimentação de carteira e os gaps de dados que travam a operação. A principal recomendação é usar a solução como cockpit operacional simples e explicável, em vez de depender de um modelo opaco ou de priorização “no feeling”.

---

## Solucao

### Abordagem

Comecei entendendo o dataset e a operação comercial antes de desenhar qualquer interface. A partir da exploração dos CSVs, ficou claro que o pipeline aberto estava envelhecido, com muitos deals sem `account` e forte concentração por produto. Em vez de perseguir um modelo de ML opaco, optei por uma solução útil e explicável:

1. estimar a qualidade do deal com base em produto, conta, setor, faixa de receita e idade relativa do deal;
2. estimar o fit do vendedor por contexto;
3. separar a experiência em duas visões:
   - `VENDEDOR`: foco operacional e clareza do que fazer;
   - `HEAD`: visão macro, movimentação de owners e gestão do pipeline.

### Resultados / Findings

O projeto entregue é uma dashboard funcional em Streamlit.

**Principais funcionalidades**

- Fila operacional para o vendedor com ações claras:
  - `Prioridade comercial`
  - `Completar CRM`
  - `Retomar ou encerrar`
- Explicação do porquê um deal entrou na mão do vendedor quando houve movimentação de owner.
- Visão `HEAD` com:
  - forecast por família
  - ações recomendadas
  - histórico de movimentação de owners
  - board de vendedores
  - forecast por owner atual e por owner sugerido

**O que a solução entrega na prática**

- Um vendedor consegue abrir a ferramenta e saber:
  - o que vender agora
  - o que corrigir no CRM sem confundir isso com prioridade comercial
  - quando um negócio entrou na sua mão e por quê
- A liderança consegue:
  - enxergar concentração de carteira
  - ver histórico de movimentação de owner
  - acompanhar forecast agregado
  - identificar problemas de higiene de pipeline

**Lógica de scoring**

- `Deal Forecast`
  - usa produto, conta, setor, revenue band e idade relativa do deal
- `Seller Fit`
  - compara o vendedor com a baseline do contexto
- `Rebalanceamento conservador`
  - não sacrifica materialmente o resultado
  - deals com CRM incompleto permanecem com o owner atual até correção do dado

**Como o `Deal Forecast` foi calculado**

O score do deal procura responder: *"vale a pena focar neste negócio agora?"*

Ele combina sinais que realmente existem no dataset:

- histórico do `produto`
- histórico do `setor`
- histórico da `conta`, quando existe volume suficiente
- `revenue band` da conta
- `idade relativa` do deal versus o comportamento histórico de deals ganhos daquele produto

A ideia aqui não foi estimar um valor "mágico", e sim criar uma probabilidade explicável baseada em:

- contexto comercial do deal
- potencial econômico
- penalidade por envelhecimento do pipeline
- penalidade por falta de dado (`account` e `engage_date`)

**Como o `Seller Fit` foi calculado**

O `Seller Fit` procura responder: *"quem tem mais aderência para capturar este tipo de deal?"*

Em vez de usar `win rate` geral do vendedor, a lógica compara o vendedor contra a **baseline do contexto**. Isso foi importante porque vendedores diferentes operam:

- produtos diferentes
- contas diferentes
- setores diferentes
- faixas de negócio diferentes

O cálculo usa, em ordem de força do sinal:

- `seller-account fit`
- `seller-product fit`
- `seller-sector fit`
- `seller-revenue band fit`

Quando existe histórico suficiente, o fit do vendedor naquele contexto é calculado como um **lift** sobre a baseline:

- se o contexto já converte bem, eu olho quem fica acima da média desse contexto
- se o contexto já converte mal, eu evito premiar simplesmente o vendedor com taxa absoluta mais alta em outro tipo de deal

Isso evita uma distorção comum: comparar vendedores em carteiras muito diferentes como se todos estivessem jogando o mesmo jogo.

**Por que isso importa na prática**

Essa lógica permite separar três coisas que normalmente ficam misturadas:

1. `Deal ruim`
2. `Deal bom com owner pouco aderente`
3. `Deal bom com owner aderente`

Na dashboard, isso aparece de forma operacional:

- o vendedor vê quando um deal veio parar na sua mão e por quê
- a liderança enxerga o histórico de movimentação de owner com racional
- a alocação não depende só de “quem vende mais”, mas de quem performa melhor naquele contexto

**Como o rebalanceamento foi controlado**

Havia um risco claro de a lógica de fit concentrar demais a carteira em poucos vendedores especialistas. Para evitar isso, o projeto usa um rebalanceamento conservador:

- não move deals com CRM incompleto
- tolera pequenas perdas de fit quando o ganho de distribuição compensa
- protege mais os deals de maior valor esperado
- mantém a liderança como responsável pela movimentação de owner

Ou seja: o objetivo não foi maximizar fit teórico a qualquer custo, mas maximizar utilidade operacional sem sacrificar materialmente o resultado.

**Leituras importantes do dataset**

- O pipeline aberto tem forte problema de higiene:
  - muitos deals sem `account`
  - muitos deals sem `engage_date`
- A concentração de carteira ideal não vem só de “melhor vendedor”, mas também da concentração do pipeline em poucos produtos.
- Em vários casos, o problema principal não é forecasting e sim falta de contexto mínimo para priorização confiável.

**Por que essa abordagem foi escolhida**

- O challenge pede software funcional e útil, não um notebook ou um modelo bonito sem adoção.
- O dataset não suporta bem um motor sofisticado de atividade comercial porque faltam campos importantes como `next_step`, atividade recente e histórico de mudança de estágio.
- Por isso, a decisão foi usar uma lógica heurística, explicável e operacionalmente defensável.

### Recomendacoes

- Usar a visão `VENDEDOR` como ferramenta diária de foco comercial.
- Usar a visão `HEAD` para governar movimentação de owner, e não delegar isso ao vendedor.
- Tratar `Completar CRM` como ação de higiene operacional paralela, sem deixar isso dominar a fila comercial.
- Evoluir a solução com campos adicionais de CRM se existirem no futuro:
  - `next_step`
  - atividade recente
  - histórico de mudança de estágio
  - motivo de perda

### Limitacoes

- A base não traz histórico de atividades, `next_step`, push de close date, margem, estoque ou lead time.
- Parte relevante dos deals abertos está sem `account`, o que reduz a capacidade de contextualização.
- O modelo é heurístico e explicável, não supervisionado.
- A simulação de movimentação de owner é útil como apoio de gestão, mas não substitui uma regra operacional real de capacidade/território.
- O process log desta submissão está estruturado em formato narrativo e pode ser complementado com screenshots e exports conforme necessário.

---

## Process Log — Como usei IA

> **Este bloco e obrigatorio.** Sem ele, a submissão é desclassificada.

### Ferramentas usadas

| Ferramenta | Para que usei |
|------------|--------------|
| Codex | Exploração dos dados, construção da dashboard, iteração de UI/UX e debugging |
| Python / pandas via terminal | Validação dos achados e agregações analíticas |
| Streamlit | Implementação da interface funcional |

### Workflow

1. Li o README do challenge e identifiquei que o deliverable principal precisava ser software funcional, não só análise.
2. Explorei os CSVs para entender produto, time, ticket, performance e cadência do pipeline.
3. Modelei a solução em duas camadas:
   - `Deal Forecast`
   - `Seller Fit`
4. Construí a primeira dashboard em Streamlit.
5. Refinei a experiência do vendedor e da liderança com várias iterações de usabilidade.
6. Ajustei bugs de visualização, bugs de Plotly/Streamlit e inconsistências de campos.
7. Reorganizei a entrega no formato aceito pelo repositório para submissão.

**Resumo das iterações**

- Iteração 1: exploração dos CSVs e formulação do problema.
- Iteração 2: definição do scoring base em `Deal Forecast + Seller Fit`.
- Iteração 3: primeira dashboard funcional em Streamlit.
- Iteração 4: refino da UX do vendedor para separar venda de higiene de CRM.
- Iteração 5: refino da `HEAD` para suportar movimentação de owner e leitura macro.
- Iteração 6: correções finais de bugs, consistência visual e empacotamento da submissão.
- Iteração 7: reforço das evidências com screenshots das sessões, screenshots da ferramenta funcionando e índice auditável do processo.

### Onde a IA errou e como corrigi

- A primeira versão avançou para um escopo maior do que o pedido original. Reorientei o trabalho para seguir estritamente a intenção funcional do challenge.
- Em alguns momentos a interface do vendedor ficou “dashboard demais” e pouco operacional. Corrigi simplificando a fila principal e separando higiene de CRM.
- Houve bugs de exibição:
  - `Forecast` com escala errada
  - gráfico da `HEAD` usando coluna errada (`best_owner` vs `suggested_owner`)
  - HTML de card renderizando como texto literal
  Esses pontos foram identificados e corrigidos iterativamente.
- Houve também risco de interpretação errada do papel de realocação: a ação de mover owner saiu da mão do vendedor e foi tratada como responsabilidade da liderança.
- O process log inicialmente estava forte em narrativa, mas ainda fraco em auditabilidade.
  - Corrigi adicionando screenshots reais das sessões com IA, screenshots da ferramenta final e um índice explícito das evidências.

### O que eu adicionei que a IA sozinha nao faria

- Julgamento de produto sobre o que devia ser ação do vendedor versus ação da liderança.
- Decisão de manter explainability acima de complexidade de ML.
- Interpretação do problema de concentração de carteira como mistura de fit + concentração estrutural do pipeline, e não só “vendedor bom vs ruim”.
- Priorização de utilidade real para RevOps em vez de sofisticação estatística pela sofisticação.
- Ajuste fino de UX para não deixar `Completar CRM` sequestrar a fila comercial do vendedor.

---

## Evidencias

- [x] Screenshots das conversas com IA
- [ ] Screen recording do workflow
- [x] Chat exports
- [x] Git history (se construi codigo)
- [x] Screenshots da ferramenta funcionando
- [x] Outro: narrativa escrita do processo

### Onde as evidências estão

- Process log principal:
  - [process-log/README.md](./process-log/README.md)
- Índice das evidências:
  - [process-log/evidence-index.md](./process-log/evidence-index.md)
- Export da conversa:
  - [process-log/chat-exports/conversation-history.md](./process-log/chat-exports/conversation-history.md)
- Screenshots das sessões com IA e da dashboard funcionando:
  - [process-log/screenshots](./process-log/screenshots)

### Preview da solução funcionando

![Dashboard vendedor/head 1](./process-log/screenshots/dash_01.png)
![Dashboard vendedor/head 2](./process-log/screenshots/dash_02.png)

---

_Submissao enviada em: 2026-04-06_

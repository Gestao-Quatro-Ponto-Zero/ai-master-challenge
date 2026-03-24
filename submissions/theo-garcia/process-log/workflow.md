# Process Log — Theo Garcia — Challenge 001

## Ferramentas Utilizadas

| Ferramenta | Para que usei | Por que essa e nao outra |
|---|---|---|
| Claude Code (Opus 4.6) | Analise exploratoria, feature engineering, construcao do dashboard, iteracao em tempo real | Terminal interativo com acesso direto ao filesystem — permite iterar sobre dados sem trocar de contexto |
| Python 3.11 | Runtime para toda a analise | Ecossistema de dados maduro |
| Pandas | Manipulacao de dados, merges cross-table, feature engineering | Padrao da industria para dados tabulares |
| Plotly | Visualizacoes interativas no dashboard | Interatividade nativa (hover, zoom, filtros) vs matplotlib estatico |
| Streamlit | Dashboard web com 3 abas | Deploy rapido, integra com Plotly, CEO consegue usar |
| Scikit-learn | Random Forest, K-Means, StandardScaler | Biblioteca padrao de ML |

---

## Workflow Passo a Passo

### Fase 1: Entendendo o Problema (antes de qualquer codigo)

Antes de pedir qualquer analise para a IA, li o briefing inteiro do challenge. O CEO da RavenStack diz que churn aumentou mas uso cresceu e satisfacao esta ok. Isso e uma contradicao — e contradicoes sao onde os insights moram.

**Minha decisao inicial:** o formato seria dashboard interativo (nao PDF nem notebook). Por que? Porque o challenge valoriza "algo que o CS pudesse usar amanha". Um PDF ninguem usa. Um dashboard com filtros e drill-down, sim.

**O que defini ANTES de comecar:**
- 5 "leis" de qualidade (cruzar tabelas, numeros verificaveis, recomendacoes acionaveis, separar correlacao de causalidade, CEO entende)
- Plano de 6 partes sequenciais
- Formato: Streamlit com 3 abas (Diagnostico, Preditiva, Recomendacoes)

### Fase 2: Ingestao e Validacao (notebooks/01_data_exploration.py)

Pedi para a IA carregar os 5 CSVs e me mostrar shapes, dtypes, nulls e distribuicoes. Isso e mecanico — a IA faz bem.

**O que EU fiz que a IA nao faria sozinha:**
- Verifiquei integridade referencial entre TODAS as tabelas (FKs batem? Tem orphans?)
- Descobri o GAP entre churn_flag (110 contas = 22%) e churn_events (352 contas = 70%). A IA mostrou os numeros, mas EU percebi que 277 contas reativaram e que o CEO esta vendo so 22% quando 70% ja churnearam

### Fase 3: Integracao Cross-Table (notebooks/02_data_integration.py)

Criei a master table cruzando as 5 tabelas por account_id. 500 rows x 55 colunas.

**Correcao 1 — Agregacao de subscricoes:**
A IA sugeriu usar apenas a ultima subscricao de cada conta. Rejeitei. Se um cliente fez upgrade > downgrade > churn, perder esse historico e perder o sinal mais importante. Agreguei TODAS as subscricoes com medias, totais, contagens de up/downgrade, e criei net_plan_movement.

**Correcao 2 — Imputacao de satisfaction_score:**
41.6% dos scores sao null. A IA sugeriu imputar com a media. Rejeitei por non-response bias — clientes insatisfeitos tendem a nao responder pesquisas de satisfacao. Imputar com a media seria dizer "quem nao respondeu esta na media", o que provavelmente e falso. Mantive como NaN.

### Fase 4: Analise de Causa Raiz (notebooks/03_root_cause_analysis.py)

Aqui e onde o julgamento humano fez a diferenca. A IA pode calcular qualquer metrica que eu peca. Mas EU decidi O QUE perguntar.

**Minha hipotese:** "Se as medias sao iguais entre churned e retidos, o problema esta nos segmentos."

Testei sistematicamente:
1. Churn por industria → DevTools = 31% (2x a media)
2. Churn por canal → Eventos = 30% (2x partners)
3. Churn por MRR tier → Mid-market ($1K-2.5K) = 26%, 55% da base
4. Churn temporal → Aceleracao de 42x em 2 anos (6 → 251 eventos/trimestre)

**Validacao do claim do CEO:**
O CEO disse "uso cresceu". EU decidi testar isso segmentando por account e por semestre. Resultado: uso per-account CAIU ligeiramente no H2/2024. O time de Produto provavelmente olha uso agregado (mais contas = mais uso total). A IA nao questionaria a premissa do CEO por conta propria — isso foi julgamento meu.

**Interpretacao do paradoxo de satisfacao:**
A IA flagou que churned (4.01) > retidos (3.97) em satisfacao. A interpretacao de que isso indica churn por fatores exogenos (pricing/competitive) e nao por insatisfacao com suporte foi minha. O CS esta tecnicamente certo — mas esta medindo a variavel errada.

### Fase 5: Segmentacao de Risco (notebooks/04_risk_segmentation.py)

**Correcao 3 — Rule-based vs ML:**
O modelo Random Forest deu F1 = 0.098. A tentacao e tunar hiperparametros ate o modelo parecer bom. Rejeitei. O baixo F1 e um INSIGHT, nao um bug: features comportamentais (uso, tickets, satisfacao) sao quase identicas entre churned e retidos. O churn e driven por fatores estruturais.

**Minha decisao:** construir risk scoring baseado nos achados da Parte 3, nao em ML. Pesos:
- Industria (25%) — DevTools = risco alto (comprovado: 31% churn)
- Canal (25%) — Eventos = risco alto (comprovado: 30% churn)
- MRR tier (25%) — Mid-market = risco alto (comprovado: 26% churn)
- Escalacoes (15%) — sinal de problemas graves
- Historico churn (10%) — ja cancelou antes

**Resultado:** Critico = 50% churn real vs Baixo = 11%. Separacao de 4.5x — muito superior ao RF. Rule-based > ML quando os segmentos tem poder discriminativo e as features comportamentais nao.

### Fase 6: Dashboard (app.py)

3 abas construidas iterativamente:
1. **Diagnostico:** KPIs, churn por segmento (industria, canal, MRR, pais), timeline mensal + aceleracao trimestral, validacao dos 3 claims do CEO, drill-down por conta
2. **Preditiva:** Matriz de risco (scatter plot risk_score x MRR com 4 quadrantes), top 20 contas em risco, RF como complementar, consulta individual
3. **Recomendacoes:** 5 acoes priorizadas com impacto em $ e prazo

---

## Onde a IA Errou e Como Corrigi

| # | O que a IA fez | O que eu corrigi | Por que |
|---|---|---|---|
| 1 | Sugeriu usar apenas a ultima subscricao | Agreguei TODAS as subscricoes | Perder historico de up/downgrade e perder sinal critico |
| 2 | Sugeriu imputar satisfaction com a media | Mantive como NaN | Non-response bias: insatisfeitos nao respondem pesquisas |
| 3 | Modelo RF deu F1=0.098, poderia ter forçado overfit | Mantive como complementar, criei risk scoring rule-based | F1 baixo e insight, nao bug. Segmentos discriminam melhor que features comportamentais |

---

## O que EU Adicionei que a IA Sozinha Nao Faria

1. **Validacao do claim do CEO:** A IA analisa o que eu peco. Mas a decisao de TESTAR se "uso cresceu" segmentando por account e por semestre foi minha. Ela nao questionaria a premissa do CEO espontaneamente.

2. **Interpretacao do paradoxo de satisfacao:** Satisfacao churned > retidos parece estranho. A interpretacao de que churn por pricing/competition e compativel com satisfacao alta com suporte requer contexto de negocio, nao estatistica.

3. **Decisao de nao forcar o modelo:** F1 = 0.098 seria "resultado ruim" para quem quer um modelo bonito. Reconhecer que isso e um dado sobre a natureza do dataset requer maturidade analitica.

4. **Priorizacao das recomendacoes:** A IA pode listar acoes. Mas priorizar por impacto em MRR vs esforco vs prazo, e decidir que "ligar para as 20 contas de maior risco em 48h" tem mais valor imediato que "criar um tier Growth em 120 dias", e julgamento de negocio.

5. **Arquitetura da analise:** A decisao de comecar por validar claims do CEO (em vez de ir direto para ML), e de usar segmentos como base do risk scoring (em vez de forcar ML), definiu a qualidade de toda a analise.

---

## Iteracoes e Evolucao

O git history mostra a evolucao real:
- `feat: add humanized EDA` — primeira exploracao
- `feat: cross-table integration` — master table
- `feat: root cause analysis` — 7 findings
- `docs: add MEU_PROCESSO.md` — documentacao dual (leigo + tecnico)
- `feat: complete Parts 4 & 5` — risk scoring + dashboard upgrade

Nao foi um prompt unico → resposta unica. Foram multiplas sessoes de trabalho, com correcoes, decisoes e refinamentos em cada etapa.

---

## Quantas Iteracoes?

- **Parte 1 (EDA):** ~3 iteracoes (carregar dados, validar integridade, documentar)
- **Parte 2 (Integracao):** ~5 iteracoes (merge, feature engineering, 2 correcoes de abordagem)
- **Parte 3 (Causa Raiz):** ~7 iteracoes (7 findings, cada um com hipotese → teste → interpretacao)
- **Parte 4 (Risco):** ~4 iteracoes (clustering, scoring, validacao, top 20)
- **Parte 5 (Dashboard):** ~6 iteracoes (3 abas + risk matrix + CEO claims + refinamentos)
- **Parte 6 (Documentacao):** ~2 iteracoes (process log + PR)

Total: ~27 iteracoes significativas ao longo de multiplas sessoes.

---

*Process log atualizado em: 2026-03-21*

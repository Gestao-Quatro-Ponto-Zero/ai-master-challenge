# Process Log — Lead Scoring IA

## 1. Visão geral

Este documento registra o processo de construção da solução, evidenciando:

- raciocínio de negócio
- decisões técnicas
- uso de IA durante o desenvolvimento

O objetivo não foi apenas "fazer funcionar", mas construir uma solução:

- explicável
- aplicável no dia a dia comercial
- aderente aos requisitos do desafio

---

## 2. Entendimento do problema

Inicialmente, o desafio foi interpretado como um sistema de scoring baseado em inputs manuais (ex: icp_fit, urgency).

Após análise mais cuidadosa, ficou claro que:

- o desafio exige uso dos dados reais do CRM
- o scoring deve ser derivado dos dados disponíveis
- o valor está em transformar dados brutos em decisão comercial

Isso levou à reconstrução da solução.

---

## 3. Uso dos dados do CRM

Foram utilizados diretamente os datasets fornecidos:

- `sales_pipeline.csv` → oportunidades
- `accounts.csv` → contexto das contas

Os dados foram integrados via:

- `account` como chave de relacionamento

Isso permitiu enriquecer cada oportunidade com contexto de negócio.

---

## 4. Construção da lógica de scoring

A lógica foi construída com base em proxies reais de decisão comercial:

- ICP → aproximado pela receita da empresa (`revenue`)
- Impacto financeiro → valor do deal (`close_value`)
- Timing → tempo entre `engage_date` e `close_date`
- Estágio → avanço no funil (`deal_stage`)

O objetivo não foi prever com ML, mas priorizar oportunidades acionáveis.

---

## 5. Uso da IA no processo

A IA (ChatGPT) foi utilizada como ferramenta de apoio para:

- interpretar o desafio
- estruturar a solução
- revisar decisões técnicas
- melhorar clareza da implementação

Abaixo estão exemplos representativos das interações.

---

### Prompt 1 — Entendimento do desafio

> "Preciso usar os datasets do CRM ou posso criar inputs manuais para o scoring?"

**Resposta (resumo):**
- é obrigatório usar os dados reais do CRM  
- inputs manuais não atendem ao desafio  

**Decisão:**
Refatorei a solução para usar diretamente:
- sales_pipeline.csv  
- accounts.csv  

---

### Prompt 2 — Construção do scoring

> "Como transformar dados do CRM em score sem usar campos como icp_fit ou urgency?"

**Resposta (resumo):**
- usar proxies de negócio:
  - revenue → ICP
  - close_value → impacto
  - datas → timing
  - stage → avanço

**Resposta da IA (trecho real):**

> "Você pode usar proxies de negócio para construir o score:
> - revenue como indicador de ICP
> - close_value como impacto financeiro
> - datas para calcular o ciclo de vendas
> - estágio como indicador de maturidade do deal"

**Decisão:**
Implementei scoring baseado nessas variáveis reais.

---

### Prompt 3 — Estrutura do código

> "Depois do merge dos dados, faz sentido separar deal e account?"

**Resposta (resumo):**
- não  
- usar um único objeto simplifica  

**Decisão:**
Refatorei para:

```python

6. Exploração dos dados (análise inicial)

Antes de consolidar a lógica de scoring, foi realizada uma análise exploratória dos dados do CRM para entender padrões relevantes.

Principais observações:

O valor do deal (close_value) apresenta alta variação e é um forte indicador de impacto financeiro
A receita das contas (revenue) permite segmentar empresas em diferentes níveis de potencial
O estágio do funil (deal_stage) indica claramente o nível de maturidade da oportunidade
O tempo entre engage_date e close_date permite inferir urgência e velocidade do ciclo de venda

7. Ajustes após review

Após a nova revisão, refinei a modelagem para torná-la mais aderente ao comportamento real do pipeline.

### Ajuste 1 — Remoção do proxy de timing

Inicialmente, utilizei `close_date - engage_date` como proxy de urgência.

Após o feedback, reconheci que essa variável não representa urgência real do cliente. Ela pode refletir apenas uma data estimada ou preenchida manualmente no CRM, sem evidência de comportamento comercial.

**Decisão:**
Removi timing do score nesta versão.

### Ajuste 2 — Exclusão de `Won` e `Lost` da priorização ativa

A primeira versão atribuía pontuação a estágios finais como `Won` e `Lost`.

Após revisão, ficou claro que isso misturava oportunidades encerradas com deals ativos, prejudicando a priorização operacional.

**Decisão:**
Mantive `Won` e `Lost` apenas como contexto do dataset, mas removi esses estágios do ranking final de deals a priorizar.

### Ajuste 3 — Substituição de limiares fixos por calibração nos dados

A primeira versão usava cortes fixos para `revenue` e `close_value`.

Após o feedback, refatorei a solução para calibrar os thresholds com base na distribuição real do dataset, usando percentis.

**Decisão:**
Passei a usar:
- percentil 75 → faixa alta
- percentil 40 → faixa intermediária
- abaixo disso → faixa baixa

Isso deixou o score menos arbitrário e mais defensável com base nos próprios dados do challenge.

Essa análise orientou a construção do modelo de scoring, garantindo que as regras fossem baseadas em padrões observáveis nos dados reais.

Decisão:

A lógica de scoring foi estruturada a partir dessas variáveis, priorizando interpretabilidade e aplicabilidade no contexto comercial.

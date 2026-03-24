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
calculate_score(row)

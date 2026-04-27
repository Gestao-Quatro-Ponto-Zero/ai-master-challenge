# PROCESS_LOG.md 📝

Este documento detalha o processo de co-criação do **Sales Priority OS** entre o Engineer (Humano) e a IA (Antigravity).

---

## 🤖 Ferramentas de IA Utilizadas

- **Antigravity (Google DeepMind)**  
  Utilizada como ambiente de desenvolvimento assistido, responsável por acelerar construção de código, testes e iterações.

- **Motivo**  
  Capacidade de operar diretamente sobre arquivos, executar código e iterar rapidamente em uma aplicação real (Streamlit), permitindo um fluxo de “vibe coding” com validação contínua.

---

## 🧠 Decomposição do Problema

Antes de iniciar o desenvolvimento, o problema foi estruturado da seguinte forma:

> O time comercial não falha por falta de leads,  
> mas por **má priorização e desperdício de atenção**.

A solução foi dividida em camadas:

1. **Priorização** → quais oportunidades importam  
2. **Execução** → o que fazer agora  
3. **Gestão** → onde o time está errando  
4. **Impacto financeiro** → quanto dinheiro está sendo perdido  

---

## 🔄 Iterações do Processo

### Iteração 1 — Base funcional
- carregamento e merge dos dados  
- criação do scoring inicial  
- dashboard analítico  

👉 Limitação: solução informativa, não acionável  

---

### Iteração 2 — Camada operacional
- criação da aba **Monday Morning Plan**  
- priorização por vendedor  
- próxima ação e mensagens sugeridas  

👉 Resultado: ferramenta passa a ser utilizável no dia a dia  

---

### Iteração 3 — Camada de gestão
- criação do **Manager Command Center**  
- ranking de vendedores  
- recomendações de coaching  

👉 Resultado: solução passa a atender decisão gerencial  

---

### Iteração 4 — Evolução analítica
- inclusão de win rate histórico  
- ajuste de scoring  
- melhoria de explicabilidade  

👉 Resultado: maior consistência nas decisões  

---

### Iteração 5 — Correção de comportamento
- identificação de **deals being ignored**  
- criação de **opportunity pressure**  
- detecção de inércia no pipeline  

👉 Resultado: sistema começa a identificar falhas de execução  

---

### Iteração 6 — Impacto financeiro
- criação de métricas como:
  - revenue_at_risk_now  
  - should_be_closing_now  
  - lost_attention_flag  
- identificação de receita esquecida  

👉 Resultado: solução passa a quantificar perda de dinheiro  

---

### Iteração 7 — Linguagem executiva
- reescrita do AI Decision Memo  
- geração de insights estratégicos  
- comunicação orientada à decisão  

👉 Resultado: saída compreensível para C-level  

---

## ⚠️ Onde a IA errou e como foi corrigido

- **Erro de Cache (KeyError)**  
  A IA tentou acessar colunas não atualizadas no cache do Streamlit  

  → Correção: implementação de cache bust e uso de `.get()`  

- **Lógica inicial genérica**  
  O scoring inicial era superficial  

  → Correção: inclusão de regras baseadas em contexto comercial  

- **Linguagem robótica**  
  Os outputs eram descritivos, não acionáveis  

  → Correção: reescrita manual para formato executivo  

- **Ausência de impacto financeiro**  
  A IA não trouxe naturalmente o conceito de receita  

  → Correção: inclusão manual de ROI e métricas de perda  

---

## 🎨 Decisões Humanas Críticas

- não utilizar modelo de ML (priorizar explicabilidade)  
- transformar score em ação prática  
- criar rotina real de uso (Monday Morning Plan)  
- adicionar visão de gestão (Command Center)  
- incluir camada financeira (não apenas análise)  
- expor erros do processo comercial, não apenas dados  

---

## 🔁 Iterações e Validação

- Foram realizadas múltiplas iterações incrementais  
- Cada evolução foi validada com execução real da aplicação  
- Testes realizados via:
  - execução do app Streamlit  
  - validação visual da interface  
  - inspeção de dados e scoring  

---

## 🎯 Conclusão do Processo

A IA atuou como acelerador de desenvolvimento.

Mas:

> As decisões críticas de produto, lógica e posicionamento foram humanas.

O resultado final não é apenas um modelo de priorização.

👉 É um sistema de correção de comportamento comercial, orientado a execução e impacto financeiro.
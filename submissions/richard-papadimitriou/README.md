# Submissão — Richard — Challenge 003

---
**Richard W. Papadimitriou**  
[LinkedIn](https://www.linkedin.com/in/richard-w-papadimitriou-b40a3a189/)  
**Challenge 003 — Lead Scorer**

[![Live Demo](https://img.shields.io/badge/Streamlit-Live%20Demo-FF4B4B?style=for-the-badge&logo=Streamlit)](https://ai-master-challenge-69kcdbc99vbtnzpewryhuj.streamlit.app/)

---

## Sobre mim

Atuo como AI Engineer com foco em Revenue Operations, utilizando IA como sistema operacional para resolver problemas reais de negócio.

Meu trabalho não é construir modelos — é transformar dados em decisões acionáveis que impactam diretamente a receita.

Tenho experiência estruturando soluções que:
- reduzem desperdício comercial ao priorizar corretamente oportunidades
- transformam pipelines em sistemas de decisão
- conectam análise de dados com execução prática do time de vendas

Neste challenge, tratei o problema não como um exercício de scoring, mas como uma falha de comportamento comercial — e construí uma solução para corrigir isso.

---

## 🧠 Tese Central

O problema do time não é falta de leads.

É desperdício de atenção.

Deals com alta probabilidade e alto valor estão sendo ignorados, enquanto o time trabalha oportunidades com baixa chance de fechamento.

Essa solução não é um modelo de previsão.

É um sistema de correção de comportamento comercial.

---

## Executive Summary

O **Sales Priority OS** é uma aplicação funcional desenvolvida para transformar um pipeline de vendas em um sistema de decisão operacional.

A solução processa ~8.800 oportunidades e identifica:
- quais deals devem ser priorizados imediatamente
- onde o time está perdendo dinheiro
- quais oportunidades deveriam estar fechando agora, mas estão sendo ignoradas

Ao invés de apresentar apenas um score, a ferramenta entrega:
- priorização clara
- explicação do contexto
- recomendação de ação
- impacto financeiro associado

O resultado é um aumento direto na eficiência comercial e na previsibilidade de receita.

---

## Solução

### Abordagem

A solução foi estruturada em quatro camadas:

1. **Integração de Dados**  
   Consolidação das tabelas de pipeline, contas, produtos e vendedores em uma base única.

2. **Motor de Decisão**  
   Sistema de scoring baseado em:
   - estágio do deal  
   - tempo no pipeline  
   - histórico de ganho (win rate)  
   - perfil da conta  
   - produto  
   - risco de inércia  

3. **Camada Operacional (Vendedor)**  
   Interface focada na execução:
   - Monday Morning Plan  
   - priorização dos top deals  
   - próxima ação sugerida  
   - mensagens prontas para contato  

4. **Camada Executiva (Manager / RevOps)**  
   Visão de controle e impacto:
   - receita em risco  
   - deals ignorados  
   - oportunidades que deveriam estar fechando  
   - recomendações de intervenção  

---

## Principais Resultados

- **Priorização real**  
  Identificação automática das oportunidades que realmente merecem atenção

- **Redução de desperdício**  
  Separação clara entre:
  - deals com potencial real  
  - oportunidades estagnadas (zombie deals)

- **Identificação de falha de execução**  
  Detecção de oportunidades com:
  - alta probabilidade  
  - alto valor  
  - baixa ação  

- **Impacto financeiro visível**  
  Quantificação de:
  - receita em risco  
  - oportunidades sendo ignoradas  
  - valor parado no pipeline  

---

## Como Usar

### Vendedores

Utilizar a aba **Monday Morning Plan** para:

- identificar os deals prioritários do dia  
- entender o contexto de cada oportunidade  
- executar ações imediatas com base nas sugestões  

---

### Managers

Utilizar o **Manager Command Center** para:

- identificar gargalos no pipeline  
- entender onde o time está errando  
- direcionar coaching com base em dados  
- agir sobre oportunidades críticas  

---

### RevOps

- manter a higiene do pipeline  
- eliminar oportunidades sem tração  
- monitorar concentração de risco  
- ajustar estratégia de priorização  

---

## Limitações

- O valor dos deals é baseado no preço de tabela (`sales_price`)  
- Descontos comerciais não são considerados  
- O modelo depende da qualidade histórica dos dados (Won/Lost)  
- Não considera interações externas (ex: e-mails, reuniões reais)

---

## Process Log — Uso de IA

### Ferramentas

- **Antigravity (Google DeepMind)**  
  Utilizada como ambiente de desenvolvimento assistido, permitindo iteração rápida, construção de código e validação contínua da aplicação.

---

### Workflow

O desenvolvimento foi conduzido em ciclos iterativos:

1. estruturação do problema  
2. construção da base funcional  
3. criação da camada operacional  
4. expansão para visão gerencial  
5. inclusão de impacto financeiro  
6. refinamento da linguagem executiva  

---

### Onde a IA errou e como foi corrigido

- **Gerenciamento de estado (cache)**  
  Erro ao acessar colunas não atualizadas  
  → corrigido com controle de cache e acesso seguro  

- **Scoring inicial genérico**  
  → refinado com lógica de negócio  

- **Saída pouco acionável**  
  → reescrita para foco em decisão  

- **Ausência de impacto financeiro**  
  → inclusão de ROI e métricas de receita em risco  

---

### Decisões Humanas Críticas

- não utilizar modelo de ML (priorizar explicabilidade)  
- transformar score em ação prática  
- criar rotina real de uso para vendedores  
- incluir camada de gestão  
- trazer impacto financeiro para o centro da decisão  
- expor falhas de execução do time  

---

## Evidências

- Código completo disponível na pasta `/solution`  
- Aplicação funcional via Streamlit  
- Instruções de execução no README da pasta solution  

---

## Conclusão

A IA foi utilizada como acelerador de desenvolvimento.

Mas:

> as decisões críticas de produto, lógica e estratégia foram humanas.

O resultado não é apenas uma ferramenta de análise.

É um sistema de decisão comercial, orientado à execução e impacto direto na receita.

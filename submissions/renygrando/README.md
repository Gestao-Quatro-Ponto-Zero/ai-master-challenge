# Submissão — Reny Grando — Challenge 002

## Sobre mim

- **Nome:** Reny Grando
- **LinkedIn:** [linkedin.com/in/renygrando](https://linkedin.com/in/renygrando)
- **Challenge escolhido:** Challenge 002 — Redesign de Suporte

---

## Executive Summary

Analisei 30.000+ tickets de suporte para identificar gargalos operacionais e oportunidades de automação via IA. Descobri que **94% do tempo de resolução ocorre após a primeira resposta** (indicando gargalos internos, não no primeiro contato), que há **$128,395 em desperdício operacional mensal recuperável**, e que o CSAT cai drasticamente após **12 horas de tempo de resolução**. Desenvolvi e implantei o **G4 Hermes**, uma plataforma funcional que automatiza classificação, roteamento e respostas para tickets de baixa complexidade (especialmente categoria "Access" - 100% automatizável), liberando a equipe humana para casos críticos. A solução está rodando em [g4-hermes.replit.app](https://g4-hermes.replit.app) e o código-fonte disponível no [GitHub](https://github.com/renygrando/Hermes).

---

## Solução

### Abordagem

**Fase 1: Compreensão do Problema (Dataset Analysis)**

Iniciei com análise estrutural dos dados para mapear as 17 colunas do dataset, classificando cada uma em categorias (identificador, atributo do cliente, variável operacional, variável textual, variável de automação). Utilizei o Google Gemini para análise semântica e o ChatGPT para auditoria de qualidade, identificando:

- 50.5% de valores nulos no campo `Resolution` (crítico para base de conhecimento)
- 20.5% de nulos em `First Response Time`, `Time to Resolution` e `Customer Satisfaction Rating`
- Integridade estrutural boa, mas qualidade analítica moderada

**Fase 2: Diagnóstico Operacional (Data Sanitization + Analytics)**

Sanitizei os dados com Python via ChatGPT, hospedei no Airtable, e gerei três relatórios analíticos focados em:

1. **Gargalos Operacionais:** Identificação de combinações canal + prioridade + tipo que geram piores tempos
2. **Satisfação do Cliente (CSAT):** Correlação entre tempo de resolução e rating
3. **Desperdício Operacional:** Quantificação de horas desperdiçadas e potencial de automação

**Fase 3: Planejamento Estratégico (NotebookLLM Synthesis)**

Consolidei os três relatórios em um plano estratégico único via NotebookLLM, respondendo:

- **O que automatizar:** Tickets de acesso (100%), triagem via NLP, roteamento inteligente, respostas automáticas
- **O que NÃO automatizar:** Reclamações (CSAT < 3.0), reembolsos, tickets críticos com escalação, casos complexos de hardware
- **Como funcionaria na prática:** Arquitetura em 4 fases priorizadas por ROI

**Fase 4: Desenvolvimento do Protótipo (Replit Implementation)**

Criei PRD com ChatGPT e implementei o sistema G4 Hermes no Replit com 7 funcionalidades core, validando as três primeiras fases do roadmap estratégico.

### Resultados / Findings

#### 📊 Diagnóstico Operacional

**Gargalos Críticos Identificados:**

| Combinação Crítica                    | Tempo Médio de Resolução | Impacto                          |
| ------------------------------------- | ------------------------ | -------------------------------- |
| Refund request + Chat + High Priority | 11.37 horas              | Pior desempenho                  |
| Social Media (qualquer tipo)          | Desvio padrão 5.93h      | Maior inconsistência operacional |
| Hardware + HR Support                 | 28.5% + 22.8% do volume  | Categorias dominantes            |

**Insight Crítico: A Regra dos 94%**

> 94% do tempo de resolução acontece **APÓS** a primeira resposta. O gargalo não está no atendimento inicial, mas nos processos internos de aprovação e resolução.

**Impacto no CSAT:**

- **Threshold crítico:** < 12 horas de resolução mantém CSAT > 3.0
- Após 12 horas, a satisfação despenca consistentemente
- First Response Time é importante, mas Time to Resolution é decisivo

**Quantificação do Desperdício:**

- **$128,395/mês** em oportunidade operacional recuperável
- **1,694 tickets ineficientes** identificados no dataset
- Economia de **2-5 min/ticket** apenas com classificação automática

#### 🤖 Sistema G4 Hermes (Protótipo Funcional)

**Aplicação Web:** [https://g4-hermes.replit.app](https://g4-hermes.replit.app)  
**Código-fonte:** [https://github.com/renygrando/Hermes](https://github.com/renygrando/Hermes)

**Funcionalidades Implementadas:**

1. **Agente IA para Abertura de Chamados**
   - Assistente conversacional que guia coleta de informações
   - Validação em tempo real de dados obrigatórios
   - Interface amigável para usuários não-técnicos

2. **Classificação Automática de Chamados**
   - Categorização inteligente via NLP
   - Atribuição de prioridade baseada em regras de negócio
   - Roteamento automático por tipo de problema
   - Detecção de urgência e impacto

3. **Respostas Automáticas**
   - Motor de sugestões baseado em histórico
   - Auto-resposta para casos 100% automatizáveis
   - Personalização contextual

4. **Base de Conhecimento (FAQ)**
   - Repositório estruturado de resoluções
   - Sistema de busca inteligente
   - Auto-atualização baseada em tickets resolvidos

5. **Análise de Chamados**
   - Métricas operacionais em tempo real
   - Identificação de gargalos ativos
   - KPIs de performance (CSAT, SLA, volume)

6. **Dashboard de Gestão**
   - Visualização centralizada de tickets
   - Filtros avançados (status, prioridade, canal, categoria)
   - Alertas de SLA breach

7. **Sistema de Autenticação**
   - Perfil Admin (gestão completa)
   - Perfil User (abertura e consulta de chamados)
   - Controle de acesso granular

#### 📁 Artefatos Analíticos

**Datasets Sanitizados:**

- `customer_support_tickets_sanitized_from_original.csv`
- `all_tickets_processed_improved_v3_sanitized.csv`

**Relatórios Executivos:**

- [Análise de Gargalos Operacionais](assets/anlise_de_gargalos_operacionais_suporte_de_ti.pdf)
- [Análise Estratégica de CSAT](assets/anlise_estratgica_de_satisfao_do_cliente_kpi_customer_satisfaction_rating.pdf)
- [Quantificação de Desperdício Operacional](assets/quantificao_do_desperdcio_operacional_e_potencial_de_automao.pdf)

**Materiais de Apresentação:**

- [Plano Estratégico Completo](https://docs.google.com/document/d/1qkUPIMH8vld6oHtNg-Bf7nT-d9csb87_w93FN5vLAZ8/edit)
- [Infográfico Executivo](assets/infografico.png)
- [Apresentação de Slides](assets/Unlocking_IT_Support_Efficiency.pdf)

**Dashboard Airtable:**

- [Support Operations Command Center](https://airtable.com/appyQLnnOhn8YxI4A/pagWmPKMLotOzpqzG)

### Recomendações

**Prioridade 1: Quick Wins (Implementação Imediata)**

1. **Automatizar 100% dos tickets de "Access"**
   - ROI imediato: categoria totalmente automatizável
   - Redução estimada: 60% no tempo de resolução desses tickets
   - Ferramenta: Sistema Hermes (já funcional)

2. **Estabelecer threshold de 12h como SLA crítico**
   - Após 12h, CSAT despenca abaixo de 3.0
   - Alertas automáticos para tickets próximos do threshold
   - Roteamento prioritário para evitar breach

3. **Focar em processos internos, não no primeiro contato**
   - 94% do tempo está APÓS a primeira resposta
   - Revisar fluxos de aprovação interna
   - Considerar delegação de autonomia aos agentes

**Prioridade 2: Eficiência Operacional (1-3 meses)**

4. **Padronizar canal "Social Media"**
   - Maior desvio padrão (5.93h) indica inconsistência
   - Criar SOP específico para este canal
   - Treinar equipe dedicada

5. **Implementar triagem automática via NLP**
   - Classificação instantânea de categoria + prioridade
   - Economia de 2-5 minutos por ticket
   - Reduz erros de roteamento manual

6. **Criar base de conhecimento auto-alimentada**
   - 50.5% dos tickets não têm `Resolution` documentada
   - Sistema Hermes já captura resoluções automaticamente
   - Feedback loop: resolução → FAQ → auto-resposta

**Prioridade 3: Escalabilidade (3-6 meses)**

7. **Expandir automação para "Hardware" e "HR Support"**
   - 51.3% do volume total (28.5% + 22.8%)
   - Maior impacto após validação do piloto "Access"
   - Manter humano no loop para casos complexos

8. **Implementar alertas preditivos (Fase 4 do roadmap)**
   - Detecção antecipada de tickets com risco de SLA breach
   - Machine learning baseado em padrões históricos
   - Intervenção proativa vs. reativa

### Limitações

**1. Dados Incompletos**

- 50.5% de `Resolution` nulos impede treino robusto de modelos de auto-resposta
- 20.5% de métricas de tempo ausentes limitam análise de SLA real
- Viés possível em `Customer Satisfaction Rating` (clientes insatisfeitos respondem mais)

**Impacto:** Modelos de ML precisarão de mais dados históricos limpos para acurácia superior a 90%

**2. Dataset Único**

- Análise baseada em snapshot temporal, não fluxo contínuo
- Não captura sazonalidade (picos de demanda, Black Friday, etc.)
- Dados demográficos (`Age`, `Gender`) não foram explorados profundamente

**Impacto:** Recomendações assumem padrão estável; validar com dados mensais contínuos

**3. Validação em Ambiente Controlado**

- Sistema Hermes desenvolvido e testado em ambiente Replit
- Não integrado com sistemas legados (CRM, ticketing atual, telefonia)
- Escalabilidade para 30.000 tickets/ano não validada em produção real

**Impacto:** Piloto recomendado antes de rollout completo (ex: 10% do volume por 30 dias)

**4. Contexto de Negócio Limitado**

- Não tenho acesso a:
  - Custo real por hora de agente
  - Estrutura de equipe atual (quantos agentes, turnos, especialidades)
  - SLAs contratuais vigentes
  - Políticas de reembolso e exceções

**Impacto:** Estimativas de ROI ($128k/mês) são baseadas em benchmark de mercado (não custos reais da empresa)

**5. Tempo de Desenvolvimento**

- Protótipo desenvolvido em ~5.5 horas (constraint do challenge)
- Funcionalidades core implementadas, mas sem:
  - Testes automatizados (unit/integration tests)
  - Documentação técnica completa de APIs
  - Monitoramento de performance em produção
  - Plano de rollback/disaster recovery

**Impacto:** Transição para produção requer hardening adicional (estimativa: +2-3 semanas)

---

## Process Log — Como usei IA

> **Documentação completa:** [01-ProcessLog.md](01-ProcessLog.md)
>
> Este bloco resume o workflow. O arquivo completo documenta todas as 7 etapas do projeto com timestamps, prompts, ferramentas, decisões e pivotagens.

### Ferramentas usadas

| Ferramenta               | Para que usou                                                                                               | Etapas         |
| ------------------------ | ----------------------------------------------------------------------------------------------------------- | -------------- |
| **Google Gemini**        | Análise semântica de datasets, classificação de colunas, identificação de variáveis críticas para automação | 03             |
| **ChatGPT**              | Sanitização de dados com Python, geração do PRD, suporte ao desenvolvimento, planejamento inicial           | 02, 04, 05, 07 |
| **ChatGPT (Agent Mode)** | Tentativa de análise em escala (descartado por lentidão)                                                    | 04             |
| **NotebookLLM**          | Síntese de múltiplos relatórios PDF em plano estratégico unificado                                          | 06             |
| **Airtable**             | Hospedagem de dados sanitizados, interface visual, análises nativas (IA do Airtable)                        | 05             |
| **Replit**               | Ambiente de desenvolvimento integrado, hospedagem da aplicação Hermes                                       | 07             |
| **GitHub Copilot**       | Documentação do Process Log, assistência na estruturação do README                                          | 01-07          |
| **n8n**                  | Preparação de infraestrutura para automação futura (não implementado no protótipo)                          | 05             |

### Workflow

**Etapa 01: Setup Inicial (18:02)** — Criação da Estrutura de Log

- Estabeleci sistema de documentação estruturado com dropdowns
- Cada commit = nova seção no Process Log
- Ferramenta: GitHub Copilot + Git

**Etapa 02: Escolha do Desafio (18:37)** — Planejamento com ChatGPT

- Selecionei Challenge 002 e criei checklist estruturado
- ChatGPT me ajudou no brainstorming das etapas
- [Conversa completa](https://chatgpt.com/share/e/69af3bef-f91c-8009-8cae-d8b748904466)

**Etapa 03: Análise do Dataset (19:33)** — Mapeamento com Gemini

- **Prompt 1:** _"Analise este dataset. Explique o papel de cada coluna e classifique em categorias (identificador, atributo cliente, variável operacional, textual, automação)."_
- **Prompt 2:** _"Quais colunas são críticas para eficiência operacional e automação?"_
- Descoberta: NotebookLLM limitado a 500k palavras → pivotei para Gemini
- Output: Tabela com 17 colunas classificadas + identificação de variáveis críticas

**Etapa 04: Auditoria de Qualidade (20:01)** — Diagnóstico com ChatGPT

- **Prompt:** _"Faça auditoria estrutural verificando: ausência de valores, duplicação, consistência, valores fora de faixa, padrões suspeitos."_
- Testei 3 ferramentas:
  - Agent Mode (muito lento) ❌
  - Gemini (limitação de context length) ❌
  - ChatGPT padrão com Python ✅
- Descoberta crítica: 50.5% nulos em `Resolution`, 20.5% em métricas de tempo
- [Conversa completa](https://chatgpt.com/share/e/69af50d3-1e98-8009-b050-88a7892fa829)

**Etapa 05: Sanitização + Stack Setup (21:10)** — Multi-tool Integration

- Python via ChatGPT para limpeza de dados
- Airtable para hospedagem visual
- Gemini para análises pontuais
- IA nativa do Airtable para estatísticas
- Output: 2 datasets sanitizados + 3 relatórios PDF + dashboard configurado

**Etapa 06: Plano Estratégico (21:53)** — Síntese com NotebookLLM

- **Prompt:** _"Gere plano estratégico de automação respondendo: O que automatizar, o que NÃO automatizar, como funcionaria na prática."_
- Input: 3 relatórios PDF (gargalos + CSAT + desperdício)
- Output: [Documento estratégico](https://docs.google.com/document/d/1qkUPIMH8vld6oHtNg-Bf7nT-d9csb87_w93FN5vLAZ8/edit) + infográfico + apresentação

**Etapa 07: Implementação (23:30)** — Build no Replit

- **Prompt ChatGPT:** _"Crie PRD completo para plataforma de automação de suporte baseado no plano estratégico."_
- Desenvolvimento no Replit: aplicação full-stack com 7 funcionalidades
- Deploy público: [g4-hermes.replit.app](https://g4-hermes.replit.app)
- Código versionado: [GitHub](https://github.com/renygrando/Hermes)
- [Projeto Replit com prompts](https://replit.com/join/biqtconfvm-orenygrando)

### Onde a IA errou e como corrigi

**1. NotebookLLM excedeu limite de palavras (Etapa 03)**

- **Erro:** Tentei fazer análise completa do dataset (30k linhas) e recebi erro de 500k palavras
- **Correção:** Pivotei para Google Gemini, que aceita arquivos maiores via upload direto
- **Aprendizado:** Validar capacidades de cada ferramenta antes de investir tempo

**2. Airtable perdeu 99.97% dos dados no import (Etapa 04)**

- **Erro:** Import via integração retornou apenas 8 linhas de 30.000
- **Correção:** Mudei para upload direto de CSV, que funcionou perfeitamente
- **Aprendizado:** Sempre validar output da IA com sanity checks (contagem de linhas, soma de valores críticos)

**3. Agent Mode do ChatGPT muito lento (Etapa 04)**

- **Erro:** Análise de dados em escala demorou >10 minutos sem concluir
- **Correção:** Voltei para ChatGPT padrão com prompts estruturados em Python
- **Aprendizado:** Agent Mode é melhor para pesquisa/web browsing, não para processamento de dados

**4. Gemini limitação de context length (Etapa 04)**

- **Erro:** Análise completa ultrapassou limite de tokens do Gemini
- **Correção:** Dividi em perguntas focadas e usei ChatGPT para análises tabulares
- **Aprendizado:** Escolher ferramenta certa para cada tipo de tarefa (Gemini = semântica, ChatGPT = estrutural)

**5. Dashboard Airtable inicial genérico (Etapa 05)**

- **Erro:** Primeira versão do dashboard não refletia insights dos relatórios
- **Correção:** Criei 2 prompts detalhados:
  - Product Designer (prototipagem de UI)
  - BI Developer (configuração técnica com métricas específicas: $128k waste, 12h threshold, 94% rule)
- **Aprendizado:** Prompts genéricos geram outputs genéricos; especificidade com dados reais gera valor

### O que eu adicionei que a IA sozinha não faria

**1. Estratégia de Pivotagem**

A IA não detecta suas próprias limitações em tempo real. Eu:

- Identifiquei quando NotebookLLM não serviu e mudei para Gemini
- Reconheci que Agent Mode era overkill e simplifiquei
- Testei múltiplas ferramentas até encontrar a stack ideal

**2. Validação de Sanidade dos Dados**

ChatGPT gerou análises estatísticas, mas eu:

- Questionei o resultado de "8 linhas" do Airtable (obviamente errado)
- Identifiquei que 50.5% de nulos em `Resolution` era crítico (não apenas uma estatística)
- Cruzei dados de satisfação com tempo de resolução para descobrir o threshold de 12h

**3. A "Regra dos 94%"**

A IA reportou que "94% do tempo de resolução ocorre após first response", mas eu:

- Interpretei o significado: **gargalo está em processos internos, não no atendimento inicial**
- Traduzi isso em recomendação acionável: focar em aprovações internas, não em treinar primeira resposta
- Priorizei isso no roadmap estratégico acima de outras métricas

**4. Definição do "Não Automatizar"**

IA sempre sugere automatizar tudo. Eu:

- Defini zona de risco: reclamações (CSAT < 3.0), reembolsos, tickets críticos
- Justifiquei com dados: clientes insatisfeitos precisam de empatia humana, não respostas automáticas
- Criei regra de negócio defensiva: "se CSAT histórico do cliente < 3.0, sempre rotear para humano"

**5. Arquitetura de Implementação Faseada**

ChatGPT gerou PRD completo, mas eu:

- Priorizei Fase 1 (Access - 100% automatizável) para ROI imediato
- Adiei Fase 4 (alertas preditivos) para após validação do piloto
- Criei critério de sucesso mensurável: redução de 60% no tempo de resolução de tickets "Access"

**6. Documentação como Artefato de Aprendizado**

Process Log não era requisito técnico do desenvolvimento. Eu:

- Documentei cada pivotagem com timestamp e raciocínio
- Linkei conversas externas (ChatGPT/Gemini) para rastreabilidade total
- Criei estrutura de dropdowns para navegabilidade (IA teria feito lista linear)
- Registrei "O que descartei" em cada etapa (aprendizado > output perfeito)

**7. Trade-offs Conscientes**

IA proporia solução perfeita. Eu:

- Aceitei limitações do protótipo (documentação técnica incompleta, testes ausentes)
- Comuniquei isso explicitamente na seção "Limitações"
- Priorizei sistema funcional end-to-end vs. uma funcionalidade hiper-polida
- Estimei esforço adicional para produção (2-3 semanas de hardening)

---

## Evidências

**✅ Submissão completa com todos os artefatos:**

### 1. Process Log Detalhado

- [x] [01-ProcessLog.md](01-ProcessLog.md) — 7 etapas documentadas com timestamps (18:02 às 23:30)
- [x] Estrutura em dropdowns com 8 seções por etapa (Objetivo, Ferramenta, Prompt, Saída, Aproveitei, Descartei, Próxima Decisão)
- [x] Seção de encerramento com resumo executivo e estatísticas do projeto

### 2. Screenshots & Evidências Visuais

- [x] [Print 1 - Análise Gemini (Prompt 1)](prints/prompt1-gemini.jpeg)
- [x] [Print 2 - Análise Gemini (Prompt 2)](prints/prompt2-gemini.jpeg)
- [x] [Infográfico Executivo](assets/infografico.png)

### 3. Chat Exports

- [x] [Conversa ChatGPT - Planejamento](https://chatgpt.com/share/e/69af3bef-f91c-8009-8cae-d8b748904466) (Etapa 02)
- [x] [Conversa ChatGPT - Auditoria de Dados](https://chatgpt.com/share/e/69af50d3-1e98-8009-b050-88a7892fa829) (Etapa 04)

### 4. Git History

- [x] [Repositório GitHub - Hermes](https://github.com/renygrando/Hermes) — Código-fonte completo
- [x] [Projeto Replit](https://replit.com/join/biqtconfvm-orenygrando) — Histórico de desenvolvimento + prompts
- [x] 11+ commits no repo ai-master-challenge com conventional commits detalhados

### 5. Aplicação Funcional

- [x] [G4 Hermes (Deploy Público)](https://g4-hermes.replit.app) — Sistema rodando
- [x] 7 funcionalidades implementadas e testáveis
- [x] Autenticação funcional (Admin/User)

### 6. Relatórios & Análises

- [x] [Análise de Gargalos Operacionais (PDF)](assets/anlise_de_gargalos_operacionais_suporte_de_ti.pdf)
- [x] [Análise Estratégica de CSAT (PDF)](assets/anlise_estratgica_de_satisfao_do_cliente_kpi_customer_satisfaction_rating.pdf)
- [x] [Quantificação de Desperdício Operacional (PDF)](assets/quantificao_do_desperdcio_operacional_e_potencial_de_automao.pdf)
- [x] [Plano Estratégico Completo (Google Docs)](https://docs.google.com/document/d/1qkUPIMH8vld6oHtNg-Bf7nT-d9csb87_w93FN5vLAZ8/edit)
- [x] [Apresentação Executiva (PDF)](assets/Unlocking_IT_Support_Efficiency.pdf)

### 7. Datasets & Dados

- [x] [Dashboard Airtable](https://airtable.com/appyQLnnOhn8YxI4A/pagWmPKMLotOzpqzG) — Interface visual dos dados
- [x] 2 datasets sanitizados (CSV) em [assets/](assets/)
- [x] Relatórios de sanitização e logs de linhas rejeitadas

### 8. Rastreabilidade Completa

- [x] Timestamps de todas as etapas (GMT-3)
- [x] Links para conversas externas (ChatGPT, Google Docs)
- [x] Prompts documentados textualmente no Process Log
- [x] Decisões de pivotagem justificadas (ex: NotebookLLM → Gemini)

---

**📅 Submissão enviada em:** 09 de março de 2026  
**⏱️ Tempo de desenvolvimento documentado:** 5 horas e 30 minutos (18:02 às 23:30)  
**🔗 Repositório principal:** [github.com/renygrando/ai-master-challenge](https://github.com/renygrando/ai-master-challenge)

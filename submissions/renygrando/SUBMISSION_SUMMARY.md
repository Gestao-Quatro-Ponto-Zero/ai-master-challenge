# Submissão — Reny Grando — Challenge 002

## Sobre mim

- **Nome:** Reny Grando
- **LinkedIn:** https://linkedin.com/in/renygrando
- **Challenge escolhido:** Challenge 002 — Redesign de Suporte

---

## Executive Summary

Analisei 30.000+ tickets de suporte para identificar gargalos operacionais e oportunidades de automação com IA. Descobri que **94% do tempo de resolução ocorre após a primeira resposta** (indicando gargalos internos), identifiquei **$128,395 em desperdício operacional mensal recuperável**, e encontrei o **threshold de 12 horas como crítico para CSAT**. Desenvolvi e implantei o **G4 Hermes**, uma plataforma web funcional que automatiza classificação, roteamento e respostas, liberando a equipe humana para casos críticos.

---

## Solução

### Abordagem

**Fase 1: Análise do Dataset**

- Mapeamento das 17 colunas e classificação em categorias (identificador, operacional, textual, automação)
- Uso de Google Gemini para análise semântica

**Fase 2: Auditoria de Qualidade**

- Diagnóstico estrutural com ChatGPT + Python
- Identificação de problemas críticos (50.5% nulos em Resolution, 20.5% em métricas de tempo)

**Fase 3: Jornada de Dados**

- Sanitização completa com Python
- Hospedagem no Airtable
- Geração de 3 relatórios PDF analíticos

**Fase 4: Planejamento Estratégico**

- Síntese via NotebookLLM dos 3 relatórios
- Definição clara: O que automatizar vs. NÃO automatizar
- Roadmap de 4 fases priorizadas por ROI

**Fase 5: Construção do Protótipo**

- PRD gerado com ChatGPT
- Sistema completo desenvolvido no Replit
- Deploy público funcional

### Resultados / Findings

#### 🔍 Diagnóstico Operacional

**Gargalos Críticos:**
| Combinação | Tempo de Resolução | Impacto |
|-----------|------------------|---------|
| Refund request + Chat + High Priority | 11.37 horas | Pior desempenho |
| Social Media | Desvio padrão 5.93h | Maior inconsistência |

**Insight Crítico — A Regra dos 94%:**
94% do tempo de resolução acontece **APÓS** a primeira resposta. O gargalo não está no atendimento inicial, mas nos processos internos.

**CSAT Critical Threshold:**

- Após **12 horas** de resolução, CSAT despenca abaixo de 3.0
- Categoria "Hardware" + "HR Support" = 51.3% do volume total

**Quantificação do Desperdício:**

- **$128,395/mês** em oportunidade operacional recuperável
- **1,694 tickets ineficientes** identificados
- Economia de **2-5 min/ticket** apenas com classificação automática

#### 🚀 Sistema G4 Hermes Funcional

**Demo ao vivo:** https://g4-hermes.replit.app  
**Código-fonte:** https://github.com/renygrando/Hermes

**7 Funcionalidades Implementadas:**

1. Agente IA para abertura de chamados (conversacional)
2. Classificação automática de tickets (NLP)
3. Respostas automáticas (baseado em histórico)
4. Base de conhecimento estruturada (FAQ)
5. Análise de chamados (métricas em tempo real)
6. Dashboard de gestão (filtros, alertas SLA)
7. Autenticação (Admin/User roles)

**Validação do Roadmap:**

- ✅ Implementa Fase 1: Automação de tickets de acesso (100% automatizável)
- ✅ Implementa Fase 2: Triagem e roteamento inteligente
- ✅ Implementa Fase 3: Respostas automáticas baseadas em histórico
- ⚠️ Fase 4: Sistema de alertas preditivos (preparado para expansão)

#### 📊 Artefatos Entregues

**Análises Executivas (PDFs):**

- https://github.com/renygrando/ai-master-challenge/raw/submission/renygrando/submissions/renygrando/assets/anlise_de_gargalos_operacionais_suporte_de_ti.pdf
- https://github.com/renygrando/ai-master-challenge/raw/submission/renygrando/submissions/renygrando/assets/anlise_estratgica_de_satisfao_do_cliente_kpi_customer_satisfaction_rating.pdf
- https://github.com/renygrando/ai-master-challenge/raw/submission/renygrando/submissions/renygrando/assets/quantificao_do_desperdcio_operacional_e_potencial_de_automao.pdf

**Plano Estratégico:**

- https://docs.google.com/document/d/1qkUPIMH8vld6oHtNg-Bf7nT-d9csb87_w93FN5vLAZ8/edit?usp=sharing

**Apresentação Executiva:**

- https://github.com/renygrando/ai-master-challenge/raw/submission/renygrando/submissions/renygrando/assets/Unlocking_IT_Support_Efficiency.pdf

**Infográfico:**

- https://github.com/renygrando/ai-master-challenge/raw/submission/renygrando/submissions/renygrando/assets/infografico.png

**Dashboard Airtable:**

- https://airtable.com/appyQLnnOhn8YxI4A/pagWmPKMLotOzpqzG

### Recomendações

**Prioridade 1: Quick Wins (Implementação Imediata)**

1. **Automatizar 100% dos tickets de "Access"**
   - ROI imediato; categoria totalmente automatizável com IA
   - Redução estimada: 60% no tempo de resolução desses tickets
   - Ferramenta: Sistema Hermes (já funcional em https://g4-hermes.replit.app)

2. **Estabelecer threshold de 12h como SLA crítico**
   - Após 12h, CSAT cai abaixo de 3.0
   - Implementar alertas automáticos e roteamento prioritário

3. **Focar em processos internos (não primeiro contato)**
   - 94% do tempo está APÓS primeira resposta
   - Revisar fluxos de aprovação interna
   - Aumentar autonomia dos agentes

**Prioridade 2: Eficiência Operacional (1-3 meses)**

4. **Padronizar canal "Social Media"** (maior desvio padrão 5.93h)
5. **Implementar triagem automática via NLP** (economia 2-5 min/ticket)
6. **Criar base de conhecimento auto-alimentada** (captura automática de resoluções)

**Prioridade 3: Escalabilidade (3-6 meses)**

7. **Expandir automação para "Hardware" + "HR Support"** (51.3% do volume)
8. **Implementar alertas preditivos** (ML baseado em padrões históricos)

### Limitações

1. **Dados Incompletos:** 50.5% de Resolution nulos, 20.5% de métricas de tempo ausentes
2. **Dataset Único:** Snapshot temporal, não fluxo contínuo; não captura sazonalidade
3. **Validação em Ambiente Controlado:** Replit, não integrado com sistemas legados reais
4. **Contexto de Negócio:** Sem acesso a custos reais de agentes, SLAs contratuais, estrutura da equipe
5. **Tempo de Desenvolvimento:** Protótipo em 5.5h; faltam testes automatizados e documentação técnica completa

---

## Process Log — Como usei IA

📋 **Process Log Completo Detalhado:**  
https://github.com/renygrando/ai-master-challenge/blob/submission/renygrando/submissions/renygrando/01-ProcessLog.md

### Ferramentas usadas

| Ferramenta         | Para que usou                                                                                                          |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| **Google Gemini**  | Análise semântica de datasets, classificação de colunas, identificação de variáveis críticas para automação (Etapa 03) |
| **ChatGPT**        | Sanitização com Python, geração do PRD, suporte ao desenvolvimento, planejamento inicial (Etapas 02, 04, 05, 07)       |
| **NotebookLLM**    | Síntese de múltiplos relatórios PDF (gargalos + CSAT + desperdício) em plano estratégico unificado (Etapa 06)          |
| **Airtable**       | Hospedagem de dados sanitizados, interface visual, análises nativas com IA do Airtable (Etapa 05)                      |
| **Replit**         | Ambiente de desenvolvimento integrado, hospedagem da aplicação G4 Hermes (Etapa 07)                                    |
| **GitHub Copilot** | Documentação do Process Log, assistência na estruturação do README (Etapas 01-07)                                      |
| **n8n**            | Preparação de infraestrutura para automação futura (Etapa 05)                                                          |

### Workflow

1. **Etapa 01 (18:02):** Setup inicial com GitHub Copilot — estrutura de log em dropdowns
2. **Etapa 02 (18:37):** Planejamento com ChatGPT — escolha do desafio e checklist
3. **Etapa 03 (19:33):** Análise com Google Gemini — mapeamento de 17 colunas + categorização
4. **Etapa 04 (20:01):** Auditoria com ChatGPT + Python — diagnóstico de qualidade de dados
5. **Etapa 05 (21:10):** Sanitização multi-tool — ChatGPT (Python) + Airtable + Gemini
6. **Etapa 06 (21:53):** Síntese com NotebookLLM — consolidação de 3 PDFs em plano estratégico
7. **Etapa 07 (23:30):** Desenvolvimento com Replit + ChatGPT — implementação do sistema funcional

### Onde a IA errou e como corrigi

1. **NotebookLLM excedeu limite de palavras** → Pivotei para Google Gemini (suporta mais dados)
2. **Airtable perdeu 99.97% dos dados no import** → Mudei para upload direto de CSV ✓
3. **ChatGPT Agent Mode muito lento** → Voltei para ChatGPT padrão com prompts estruturados em Python ✓
4. **Gemini limitação de context length** → Dividi em perguntas focadas + ChatGPT para análises tabulares ✓
5. **Dashboard Airtable genérico** → Criei 2 prompts detalhados (Product Designer + BI Developer) com métricas específicas ✓

### O que eu adicionei que a IA sozinha não faria

1. **Estratégia de Pivotagem:** Identifiquei limitações de ferramentas e adaptei o stack em tempo real
2. **Validação de Sanidade:** Questionei resultado errado de "8 linhas" do Airtable; investigar causas
3. **A Regra dos 94%:** Interpretei dados em insight acionável (gargalo está em processos internos, não first touch)
4. **Zona de Não-Automatizar:** Defini casos que precisam de humano (CSAT < 3.0, reclamações, reembolsos)
5. **Arquitetura Faseada:** Priorizei Fase 1 para ROI imediato vs. implementar tudo de uma vez
6. **Documentação como Aprendizado:** Process Log não era requisito, mas criei para rastreabilidade total
7. **Trade-offs Conscientes:** Identifiquei limitações do protótipo e comuniquei explicitamente (faltam testes, documentação técnica)

---

## Evidências

- [x] **Screenshots das conversas com IA:** https://github.com/renygrando/ai-master-challenge/tree/submission/renygrando/submissions/renygrando/prints
- [x] **Chat exports:**
  - https://chatgpt.com/share/e/69af3bef-f91c-8009-8cae-d8b748904466 (Etapa 02)
  - https://chatgpt.com/share/e/69af50d3-1e98-8009-b050-88a7892fa829 (Etapa 04)
- [x] **Git history:** https://github.com/renygrando/ai-master-challenge/commits/submission/renygrando (11+ commits versionados)
- [x] **Código funcional:** https://github.com/renygrando/Hermes (repositório dedicado do Hermes)
- [x] **Aplicação rodando:** https://g4-hermes.replit.app (deploy públi que demonstra o sistema)
- [x] **Process Log detalhado:** https://github.com/renygrando/ai-master-challenge/blob/submission/renygrando/submissions/renygrando/01-ProcessLog.md (7 etapas, 5.5h documentadas)

---

**📅 Submissão enviada em:** 10 de março de 2026  
**🔗 Pasta de submissão:** https://github.com/renygrando/ai-master-challenge/tree/submission/renygrando/submissions/renygrando

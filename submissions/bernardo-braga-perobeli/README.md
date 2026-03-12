# Submissão — Bernardo Braga Perobeli — Challenge 002

## Sobre mim

- **Nome: Bernardo Braga Perobeli**
- **Idade: 19 anos**
- **LinkedIn: https://www.linkedin.com/in/bernardo-perobeli/**
- **Challenge escolhido: Challenge 002 — Redesign de Suporte**

---

## Executive Summary

Analisei os dados de suporte (Quase 8.5K tickets operacionais + 48K tickets IT) e identifiquei que **67% dos tickets ficam sem resolução** e a satisfação média é 3.0/5.0. Construí a ferramenta **G4 IA Inteligência de Suporte**, um sistema completo de triagem inteligente que usa **Gemini 3.1 Flash Lite** (classificação, resumo, soluções) e **Gemini 2 Embedding** (RAG com quase 56.500 tickets + detecção de duplicatas). O sistema visa resolver automaticamente **28% dos tickets totais (30k por ano)** (85% dos Low + 55% dos Medium simples), sugere respostas para tickets de nível médio, e fornece resumo + 3 potenciais soluções para tickets críticos. **Automação de quase 28% economiza ~5.400 horas/mês e ~R$ 1.950.000/ano** (base R$ 30/hora, custo IA +R$ 300/ano).

---

## Solução

### Abordagem

1. **Diagnóstico operacional** — PDF com todo o resumos do notebook EDA realizado com os dois datasets e visão da operação, junto com perspectiva da solução IA
2. **Proposta de automação** — Documento executivo para C-level com fluxo proposto, o que automatizar vs manter humano e ROI projetado
3. **Protótipo funcional** — Ferramenta web completa (FastAPI + Next.js) com:
   - Classificação via LLM (Gemini 3.1 Flash Lite) com contexto RAG
   - Triagem automática de 3 níveis (baixo/médio/crítico)
   - Resumo + 3 soluções geradas por IA para todos os tickets
   - Detecção de duplicatas via similaridade semântica
   - Auto-assignment de tickets por carga (least-loaded)
   - Painel do agente (operação) e painel do gestor (governança)
   - CRUD de usuários, alertas em tempo real, upload de dados (CSV/XLSX)
   - Webhook genérico para integração com CRMs

### Resultados / Findings

**Diagnóstico (Dataset 1):**
- 8.469 tickets, 5.700 sem resolução (67% backlog)
- Tempo médio de tratamento: 7.7h
- Satisfação: 3.0/5.0 (nota mais impactada pelo tipo de ticket e tempo de tratamento)
- ~28% dos tickets são automatizáveis com LLM + RAG (85% Low + 55% Medium simples)

**Dataset 2:**
- 47.837 tickets IT em 8 categorias
- Desbalanceamento de 7.7x (Hardware: 13.6K vs Administrative rights: 1.7K)
- Mediana de 26 palavras por ticket

**Ferramenta:**
- 25 endpoints REST (autenticação JWT, triagem, métricas, CRUD, webhook)
- Pipeline Gemini com fallback automático para DeBERTa + templates
- Base RAG indexa ambos os datasets (até ~56.5K docs) com cache em disco
- Frontend Next.js com 12 páginas (login, fila de tickets, detalhe, sugestor, dashboard, volume, motivos, alertas, agentes, equipe, importar, diagnóstico)

### Recomendações

1. **Curto prazo**: Configurar API key Gemini e alimentar com tickets reais da empresa via upload CSV
2. **Médio prazo**: Integrar com CRM existente via webhook; treinar equipe nas duas interfaces (Agente suporte e gerência)
3. **Longo prazo**: Substituir base in-memory por PostgreSQL; adicionar métricas de acurácia do classificador

### Limitações

- O Dataset 1 é sintético (distribuições uniformes) — os números absolutos devem ser relativizados
- A base RAG depende da qualidade dos dados históricos; textos template do DS1 limitam o valor semântico
- O protótipo usa banco in-memory (dados não persistem entre reinicializações)
- Auto-assignment assume agentes online; em produção, integração com status real seria necessária
- Tentei conectar API versão paga mas o Google Cloud retornou erro diversas vezes e não consegui (Afeta rate limit)

---

## Process Log — Como usei IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada.

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Cursor (Claude Opus 4.6 & GPT 5.3 Codex Ultra High) | Desenvolvimento completo: planejamento, análise de dados, backend FastAPI, frontend Next.js, integração Gemini, documentação, revisão, segurança |
| Google Gemini 3.1 Flash Lite | Motor LLM do protótipo: classificação, resumo, soluções, respostas |
| Google Gemini 2 Embedding | Embeddings para RAG e detecção de duplicatas |

### Workflow

1. **Planejamento**: Li os READMEs do desafio e discuti 3 hipóteses de solução com a IA. Escolhi combinar dashboard + API técnica.
2. **Iteração do escopo**: Refinei requisitos em múltiplas conversas, adicionei sistema de 3 níveis, governança, alertas, duas interfaces diferentes e muito mais.
3. **Backend v1**: Construí API FastAPI com classificação HuggingFace (DeBERTa) e frontend Streamlit
4. **Frontend refactor**: Migrei para Next.js por melhor UX a IA ajudou na criação das páginas.
5. **Integração Gemini**: Substituí HuggingFace pelo Gemini como motor principal, mantendo fallback
6. **Notebook**: Criei diagnóstico operacional com EDA completa, a IA sugeriu análises e verifiquei cada insight
7. **Produção**: Adicionei CRUD, upload, webhook, auto-assignment para tornar viável com dados reais
8. **Documentação**: Gerei proposta executiva e README com base nos dados do diagnóstico para realizar entrega final

### Onde a IA errou e como corrigi

- **Errou ao mensurar impactos para empresa**: Não conseguiu captar muito bem números de impactos e gastos 
- **Modelos antigos e errados**: Confundiu modelos utilizados com modelos LLM e embeddings mais antigos
- **Bug de filtro**: Frontend crashava ao filtrar tickets por nível médio ou crítico faltava um import de ícone (`Inbox`)

### O que eu adicionei que a IA sozinha não faria

- **Decisão de usar LLM + RAG**: Escolha baseada em IA generativa avançada e em custo-benefício real (~R$ 0,035/ticket vs modelos maiores)
- **Sistema de 3 níveis**: Conceito de "onde IA resolve, onde IA auxilia, onde humano decide" — a IA tenderia a automatizar tudo
- **Sistema de login**: Sistema de login e proteção de cada conta segmentando acesso de diferentes pessoas a diferentes dados
- **Governança com alertas**: Ideia de notificar gestores quando volume sobre tickets específicos excedem limites
- **Interpretação dos dados e impacto**: IA não conseguiu concluir muito bem sobre mensurar impacto e custos, acabei fazendo eu mesmo e passando para ela
- **Raciocinio sobre processos da empresa**: Por mais que a IA tente, ela ainda não consegue entender e captar 100% de um processo diário real dentro de uma empresa por não conseguir viver de forma física (Ainda)

---

*Submissão enviada em: 11 de Março 2026*

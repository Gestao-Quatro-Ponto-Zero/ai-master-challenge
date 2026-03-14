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
- Tentei conectar API versão paga mas o Google Cloud retornou erro diversas vezes e não consegui (Afeta rate limit do uso)

---

## Process Log — Como usei IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada.

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Google AI Studio | Utilizei para gerar hipóteses iniciais de como resolver o problema do desafio mas não ajudou muito |
| Cursor (Claude Opus 4.6 & GPT 5.3 Codex Ultra High) | Desenvolvimento completo: planejamento, análise de dados, backend FastAPI, frontend Next.js, integração Gemini, documentação, revisão, segurança |
| Google Gemini 3.1 Flash Lite | Motor LLM do protótipo: classificação, resumo, soluções, respostas |
| Google Gemini 2 Embedding | Embeddings para RAG e detecção de duplicatas |

### Workflow

1. **Planejamento**: Li os READMEs do desafio e do Challenge 02 e discuti 3 hipóteses de solução dentro do Cursor para gerar o plano (Depois de ter gerado algumas ideias dentro do Google AI Studio). Escolhi combinar dashboard + API técnica que foi uma ideia que sugeri junto com uma outra que a IA citou (Google AI Studio não agregou muito mas iniciou a tração na ideia).
2. **Iteração do escopo**: Refinei requisitos em múltiplas conversas, adicionei sistema de 3 níveis, governança, alertas, duas interfaces diferentes e muito mais.
3. **Backend v1**: Construí API FastAPI com classificação HuggingFace (DeBERTa) e frontend (Não ficou bom por conta da usabilidade e delay, qualidade ruim).
4. **Frontend refactor v2**: Migrei para Next.js por melhor UX a IA ajudou na criação das páginas mas a solução não estava completa ainda, era um esqueleto que poderia ser adaptado conforme o worfklow do Desafio.
5. **Integração Gemini**: Substituí HuggingFace pelo Gemini como motor LLM principal, mantendo fallback em caso de problemas (Mitigar)
6. **Notebook EDA dos dados**: Criei diagnóstico operacional com EDA completa, a IA gerou análises e verifiquei cada insight encontrado no cruzamento dos dois datasets (Tempo médio de atendimento, meios de comunicação, quantidade de tickets, níveis de complexidade) e foi assim que vislumbrei 100% a ideia da plataforma que citei nos passos 3 e 4 (Confirmou ainda mais a ideia).
7. **Produção & Adaptação**: Adicionei CRUD, upload, webhook, auto-assignment para tornar viável com dados reais com dados de arquivos CSV & XLSX ou de ferramentas como SalesForce ou Zendesk (Fácil migração).
8. **Documentação final**: Gerei proposta de automação e diagnóstico final e README com base nos dados do notebook EDA para realizar entrega final e reforçar minhas decisões do porque a automação era uma potencial solução para o problema (Data-backed).

### Onde a IA errou e como corrigi

- **Decisão sobre o que criar e hipotéses iniciais**: No inicio, acabei lendo os documentos disponíveis no repo do Desafio AI Master, para compreender mais a fundo o objetivo do desafio e especificamente sobre o Challenge 02 (No qual eu selecionei para resolver) sobre qual solução eu poderia construir para resolver o problema. Não comecei a construir diretamente no Cursor pois eu queria utilizar esse "recuo mental" para avaliar a situação antes de tentar construir algo sem sentido. Como já tenho experiência com projetos e soluções de IA para empresas, não foi muito dificil surgir a ideia de ter uma ferramenta com dashboard de volume de tickets, diferentes níveis de acesso e automação de tickets nível "LOW" (Wedge case) com IA e tickets nível "Medium" mais simples com IA + aviso para agente de suporte.
- **Decisão sobre automação (O que automatizar vs o que NÃO automatizar)**: A IA não compreendeu muito bem o potencial de automação dos problemas de suporte ao cliente nos dados providenciados (Dataset), foi onde analisei mais profundamente para encontrar um margem de automação que fosse o mais proximo da realidade e o que deve ser automatizado e o que não deve. Utilizando principíos da estratégia "Wedge case" para automações, onde o foco inicial para ter o maior impacto (ROI) e de forma mais rapida são **tarefas de baixo nível de complexidade mas que possuem alto volume**, como tickets de suporte nivel "Low" (Fontes para referência: https://www.linkedin.com/posts/jasonshuman_great-ai-wedges-dont-need-to-be-hard-to-activity-7343254072042438658-AedB/, https://www.gladly.ai/blog/customer-service-automation-a-complete-guide/, https://get.mem.ai/blog/automation-of-tasks-how-to-be-more-efficient-at-work)
- **Errou ao mensurar impactos para a empresa**: Não conseguiu captar muito bem números de impactos e gastos e assim tive que utilizar minha experiência e intuição de análise de problemas e soluções para empresas para estimar melhor os impactos, evitando projeções muito agressivas e irreais mas também nem tão pessimistas (Utilizei dados comuns do mercado para a especifidade de automação para suporte ao cliente). 
- **Modelos antigos e errados**: Confundiu modelos utilizados com modelos LLM e embeddings mais antigos e assim tive que corrigir e esterçar a IA para os modelos mais recentes e com melhor qualidade (Gemini 2 Embedding que está sendo utilizado lançou no mesmo dia que entreguei meu projeto).
- **Bug de filtro**: Frontend crashava ao filtrar tickets por nível médio ou crítico faltava um import de ícone (`Inbox`) e para resolver, esterçei a IA para corrigir o bug e tudo funcionou sem problemas após o resultado final e adiante.

### O que eu adicionei que a IA sozinha não faria

**Pivotação da solução**: Após a primeira versão do esqueleto da solução (Nem perto da entrega final) acabei percebendo que não daria certo por conta de problemas na usabilidade, delay, qualidade técnica em geral (Versão com Streamlit). Assim, decidi pivotar e construir uma solução mais elevada tecnicamente e com outros frameworks (Next.Js e FastAPI) que facilitaria a versão esqueleto estar mais "robusta" para ser lapidada daquele momento e adiante de acordo com novas ideias e relacionar com os dados do que automatizar (Como um módulo pronto para ser adaptado para o objetivo).
- **Decisão de usar LLM + RAG**: Escolha baseada em IA generativa avançada e em custo-benefício real (~R$ 0,035/ticket vs modelos maiores)
- **Sistema de 3 níveis**: Conceito de "onde IA resolve, onde IA auxilia, onde humano decide", a IA tenderia a automatizar tudo
- **Sistema de login**: Sistema de login e proteção de cada conta segmentando acesso de diferentes pessoas a diferentes dados
- **Governança com alertas**: Ideia de notificar gestores quando volume sobre tickets específicos excedem limites
- **Interpretação dos dados e impacto**: IA não conseguiu concluir muito bem sobre mensurar impacto e custos, acabei fazendo eu mesmo e passando para ela de acordo com minha experiência em projetos de IA com empresas.
- **Raciocinio sobre processos da empresa na parte de suporte ao cliente**: Por mais que a IA tente, ela ainda não conseguiu entender e captar 100% de um processo diário real dentro de uma empresa por não conseguir viver de forma física e captar essas especifidades de interações humanas (Ainda)

---

*Submissão enviada em: 11 de Março 2026*

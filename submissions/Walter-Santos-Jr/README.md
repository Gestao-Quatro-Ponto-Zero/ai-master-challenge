# Submissão — Walter Santos Jr. — Challenge 003

## Sobre mim
- **Nome:** Walter José dos Santos Júnior
- **LinkedIn:** https://www.linkedin.com/in/demandsupplychain
- **Challenge escolhido:** Build 003 — Lead Scorer

## Executive Summary
O **Sales Execution Cockpit RC4** transforma dados históricos de CRM em uma experiência de execução comercial para Head de RevOps, Manager e Seller. Reúne KPIs, segmentação, scoring heurístico explicável, qualificação, Next Best Action, fila de Rework e fechamento Won/Lost com persistência SQLite. A solução responde à necessidade de priorizar o tempo comercial e evitar perda de foco, sem alegar previsão probabilística ou impacto financeiro ainda não medido.

## Solução
A aplicação está em [`solution/`](solution/). Inicie com **Python 3.10+** e `python solution/app.py` (ou execute dentro da pasta `solution`); acesse `http://127.0.0.1:8050`. Para testes isolados, defina `G4_DB_PATH` apontando para SQLite temporário. Veja [instruções completas](solution/README.md).

### Abordagem
**BIOS / Business First:** diagnóstico da dor RevOps → decomposição e hipóteses → auditoria dos dados → comparação de alternativas → decisão de scoring heurístico → produto operacional → verificação e homologação. O método e suas limitações estão em [BIOS Methodology](docs/BIOS_METHODOLOGY.md).

### Resultados / Findings
- Cockpit Head / Manager / Seller com score e ações explicáveis.
- Suíte de **101 testes aprovados** na auditoria de 26/10/2026; ver [relatórios de auditoria](docs/).
- Reconciliação histórica reportada em 126 escopos e 1.638 comparações sem divergência, limitada às métricas auditadas.
- **12 capturas UAT** disponíveis em [`solution/docs/uat_evidencias/`](solution/docs/uat_evidencias/), com a jornada de Rework.

### Recomendações
Adotar como MVP de apoio à execução, validar desempenho e adoção em piloto controlado, instrumentar outcomes e revisar periodicamente as políticas de priorização antes de qualquer evolução preditiva.

### Limitações
Demo local; sem autenticação corporativa, CRM externo integrado ou experimento causal de uplift. **Score não é probabilidade calibrada**. Datas históricas não provam urgência atual. O arquivo SQLite incluído é snapshot de demonstração.

## Workflow — Da ambiguidade à execução validada

O projeto seguiu um processo iterativo orientado pela **BIOS**, com decisões humanas, uso crítico de IA e evidências de engenharia. As etapas abaixo representam o encadeamento metodológico; não devem ser interpretadas como uma execução estritamente linear ou como prova de técnicas não documentadas.

| Etapa | Objetivo e decisão | Evidência |
|---|---|---|
| 1. Business Problem Framing | Traduzir a dor do Head de RevOps em priorização comercial e apoio à execução, antes de escolher a tecnologia. | [BIOS Methodology](docs/BIOS_METHODOLOGY.md), [prompts literais](process-log/PROMPT_EVIDENCE_REGISTER.md) |
| 2. Structured Thinking & Problem Solving | Decompor o problema, formular hipóteses e explorar dados históricos; separar observações de possíveis causas. | [BIOS Methodology](docs/BIOS_METHODOLOGY.md), [trilha de decisões](process-log/BIOS_DECISION_TRACE.md) |
| 3. BIOS Reasoning & Capability Model | Relacionar necessidades de negócio às capacidades de análise, priorização, ação e acompanhamento por persona. | [BIOS Methodology](docs/BIOS_METHODOLOGY.md) |
| 4. Decision Intelligence & AI Design | Avaliar alternativas; adotar scoring heurístico explicável em vez de alegar probabilidade de conversão não calibrada. | [Política de scoring](solution/SCORING_POLICY_V3.md), [Process Log](solution/PROCESS_LOG.md) |
| 5. Architecture & Engineering | Implementar cockpit Head/Manager/Seller, persistência operacional SQLite e abordagem independente de fornecedor de CRM. | [Arquitetura](solution/ARCHITECTURE.md), [guia de execução](solution/README.md) |
| 6. Closed-Loop Execution | Conectar análise, Next Best Action, qualificação, Rework e fechamento Won/Lost com registro de ações. | [Guia do usuário](solution/USER_GUIDE.md), [UAT](solution/UAT_EVIDENCE.md) |
| 7. Verification, Validation & Evidence | Executar testes, reconciliar KPIs, inspecionar evidências UAT e registrar limitações e decisões de release. | [UAT](solution/UAT_EVIDENCE.md), [auditoria de KPIs](docs/KPI_RECONCILIATION.md) |

**Fluxo resumido:** Problema ambíguo → hipóteses e diagnóstico → capacidades e alternativas → decisões de scoring/arquitetura → implementação incremental → ação em closed loop → testes e homologação.

**Rastreabilidade:** o [registro de prompts](process-log/PROMPT_EVIDENCE_REGISTER.md) preserva intervenções humanas literais selecionadas; o [adendo histórico](process-log/BIOS_PROCESS_LOG_HISTORICAL_ADDENDUM.md) distingue evidência documental de interpretação retrospectiva. Não se afirma que todas as ferramentas de Lean Six Sigma tenham sido executadas, nem que haja uplift financeiro causalmente comprovado.

## Ferramentas de IA utilizadas

| Ferramenta | Uso | Controle humano |
|---|---|---|
| ChatGPT | Estruturação BIOS, exploração de dados, alternativas, implementação, testes e documentação | Diretrizes, críticas, decisões e aceite do candidato |
| Gemini | Contraponto comparativo de proposta | Análise crítica; hipóteses e alegações não validadas foram rejeitadas |

## Process Log — Como usei IA
- **Ferramentas:** ChatGPT para estruturação do problema, análise de dados, engenharia, testes e documentação; Gemini utilizado como contraponto independente na avaliação de alternativas.
- **Workflow:** prompts orientadores humanos → hipóteses → exploração de dados → comparação heurística versus ML → versões incrementais → testes e UAT.
- **Erros e correções:** política inicial com viés contra Prospecting; pressuposto indevido de Salesforce em proposta comparativa; necessidade de distinguir prioridade comercial de probabilidade e de qualidade dos dados.
- **Contribuição humana:** princípios Business First, Visual First / Decision Driven, decisões de trade-off, crítica ao Gemini, preservação da arquitetura CRM-agnostic e aprovação de aceitação.

**Evidências:** [Process Log histórico](solution/PROCESS_LOG.md), [adendo](process-log/BIOS_PROCESS_LOG_HISTORICAL_ADDENDUM.md), [prompts literais](process-log/PROMPT_EVIDENCE_REGISTER.md), [rastreabilidade](process-log/BIOS_DECISION_TRACE.md) e [UAT](solution/UAT_EVIDENCE.md).

**Status:** candidato de revisão, **não enviado**. Aprovação humana final e PR pendentes.

## Onde a IA errou e como corrigi
- A proposta inicial de pesos/prioridades apresentou viés de estágio; a avaliação humana impediu a interpretação do score como probabilidade de conversão e motivou política explicável e sinalização independente de confiança dos dados.
- Uma proposta comparativa presumiu Salesforce sem que o case o especificasse; o candidato rejeitou essa premissa e manteve arquitetura CRM-agnostic.
- Projeções de uplift e métricas preditivas sem validação adequada não foram apresentadas como resultados demonstrados.

## O que eu adicionei ao processo
- Formulação Business First do problema, critérios de aceite e direcionamento da BIOS.
- Diretriz Visual First, Decision Driven, Simple by Design e decisões de UX e Closed-Loop.
- Análise crítica das alternativas, solicitação de histogramas, correções, UAT e decisão de congelamento RC4.

## Evidências e rastreabilidade
- [Metodologia BIOS](docs/BIOS_METHODOLOGY.md)
- [Process Log](solution/PROCESS_LOG.md) e [adendo histórico](process-log/BIOS_PROCESS_LOG_HISTORICAL_ADDENDUM.md)
- [Registro de prompts humanos literais](process-log/PROMPT_EVIDENCE_REGISTER.md)
- [Trilha de decisões](process-log/BIOS_DECISION_TRACE.md)
- [Evidências UAT](solution/UAT_EVIDENCE.md) e [reconciliação de KPIs](docs/KPI_RECONCILIATION.md)

**Governança de publicação:** a autorização de preparação não equivale à aprovação para abertura do Pull Request.

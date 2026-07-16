# Submissão — Rodolfo — Challenge 001 — Diagnóstico de Churn

## Sobre mim

- **Nome:** Rodolfo
- **Email:** rodolfo@dtsqd.com
- **Challenge escolhido:** 001 — Diagnóstico de Churn (Dados / Analytics)

---

## Executive Summary

Construí uma **plataforma completa de diagnóstico de churn** para a RavenStack — não apenas uma análise, mas um sistema em produção com pipeline ETL, API REST, dashboard corporativo (identidade visual G4) e integração com LLM para explicações narrativas. A RavenStack tem **22% de churn rate** ($255k/mês de MRR perdido) e **85 contas em risco ativo**. A plataforma está deployada no Railway e acessível via browser, permitindo que o time de CS priorize contas, entenda causas e aja preventivamente.

**Link do dashboard:** https://churn-platform-production-8bea.up.railway.app

---

## Solução

### Abordagem

Usei **Spec-Driven Development**: cada componente foi especificado em um documento (SPEC-v1) antes de ser implementado. Cada spec tem um harness de validação automatizado. Isso garantiu que:

1. O problema fosse entendido antes de qualquer código
2. Cada funcionalidade tivesse critérios de aceitação claros
3. O progresso fosse mensurável (19 testes passando)

A arquitetura segue 3 estágios:
- **Descritivo** → O que aconteceu (pipeline ETL + análise segmentada)
- **Creditivo** → O que vai acontecer (especificado, não implementado: XGBoost)
- **Prescritivo** → O que fazer (Health Score + playbook)

### Resultados / Findings

**Pipeline de Dados**
- 5 fontes integradas (Accounts, Subscriptions, Feature Usage, Support Tickets, Churn Events)
- Schema validation com DQR (Data Quality Report)
- Account View unificada: 500 contas, 36 colunas

**Health Score**
- 4 pilares: Usage (35%), Support (25%), Engagement (20%), Financial (20%)
- 5 tiers: Champion → Healthy → Neutral → At Risk → Critical
- **85 contas em risco** (At Risk) = **$4.400/mês de MRR ameaçado**

**Churn por Indústria**

| Indústria | Churn | Impacto MRR |
|---|---|---|
| DevTools | 31% | $67k |
| FinTech | 22% | $77k |
| HealthTech | 22% | $58k |
| EdTech | 16% | $22k |
| Cybersecurity | 16% | $30k |

**REST API em Produção**
- `POST /api/v1/run` — Executa o pipeline completo
- `GET /api/v1/accounts/risk` — Lista contas em risco com filtros
- `GET /api/v1/accounts/{id}/explain` — Narrativa LLM da conta

**Dashboard**
- Tema dark premium com identidade visual G4
- KPIs executivos em tempo real
- Distribuição de Health Score
- Tabela priorizada com filtros
- Explicador narrativo por conta

### Recomendações

1. **Priorizar as 85 contas At Risk** — Iniciar programa de reengajamento com foco nas de maior MRR
2. **Implementar modelo preditivo (SPEC-6)** — XGBoost para prever churn com 30+ dias de antecedência
3. **Automatizar playbook (SPEC-9)** — Cada tier de risco deve disparar ações automáticas no CRM
4. **Cron semanal** — Configurar no Railway para executar pipeline toda segunda-feira 9h
5. **LLM real** — Substituir fallback por OpenAI/Anthropic com chave via env var

### Limitações

- **Modelos preditivos** não implementados (XGBoost, Survival, Uplift) — especificados mas sem código
- **OpenCode** não disponível no Railway — fallback semântico usado em vez de LLM real
- **Dados sintéticos** — os padrões identificados podem não refletir comportamento real de churn
- **Cron job** precisa ser configurado manualmente no Railway dashboard (sem CLI disponível)

---

## Process Log — Como usei IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada.

### Ferramentas usadas

| Ferramenta | Para que usou |
|---|---|
| **Claude Code (opencode)** | Agente principal — spec writing, implementação, debugging, deploy |
| **Claude Web Fetch** | Pesquisa de mercado (McKinsey, BCG, Gartner benchmarks) |
| **Bash** | Execução de comandos, testes, deploy Railway |
| **Git/GitHub** | Versionamento, PR management |

### Workflow

1. **Pesquisa de mercado** (4 agentes paralelos) → benchmarks de churn analytics
2. **Spec-Driven** → SPEC-v1 com 10+ specs, cada uma com harness de teste
3. **Pipeline ETL** → load, clean, merge, validate, account_view
4. **Health Score** → 4 pilares com pesos configuráveis via YAML
5. **Análise** → segmentação por indústria/plano/país/canal
6. **API** → FastAPI com 5 endpoints + documentação automática
7. **LLM** → OpenCode integration com cache + fallback
8. **Dashboard** → HTML/CSS/JS com identidade G4
9. **Deploy** → Railway (Docker) — 3 iterações de debugging
10. **Testes** → 19 harness tests automatizados

### Onde a IA errou e como corrigi

| Erro | Correção |
|---|---|
| numpy serialization na API | Adicionei `_convert_numpy()` |
| `asyncio.run()` em rota async | Troquei por `await` |
| pip install -e . falhou no Docker | Mudei para requirements.txt |
| pyarrow ausente no Railway | Adicionei ao requirements.txt |
| Root "/" retornando 404 | Adicionei dashboard HTML na raiz |
| .venv (983MB) enviado ao Railway | Adicionei `.railwayignore` |

### O que eu adicionei que a IA sozinha não faria

1. **Arquitetura Spec-Driven** — especificar antes de implementar, com validação automatizada
2. **Pesquisa de mercado** — benchmarks reais para fundamentar a abordagem
3. **Visão de produto** — arquitetura 3 estágios + diferencial de explicabilidade
4. **Identidade visual G4** — design intencional, não genérico
5. **Julgamento de deploy** — fallback semântico vs LLM real, simplificação do Dockerfile
6. **Curadoria da submissão** — o que é relevante destacar para o avaliador

---

## Evidências

- [x] **Git history**: branch `submission/rodolfo` com ~30 commits
- [x] **Código funcional em produção**: [churn-platform-production-8bea.up.railway.app](https://churn-platform-production-8bea.up.railway.app)
- [x] **Testes automatizados**: `bash harness/run_all.sh` — 19/19 passando
- [x] **Spec document**: `SPEC-v1-churn-platform.md`
- [x] **Process log**: `process-log/process-log.md`
- [x] **Plano estratégico**: `plano-estrategico-churn.md`

---

_Submissão enviada em: 16/07/2026_

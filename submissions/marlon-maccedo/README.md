# Submissão — Marlon Maccedo — Challenges 001–004

## Sobre mim

- **Nome:** Marlon Maccedo
- **LinkedIn:** https://www.linkedin.com/in/marlonmaccedo/
- **Challenges entregues:** data-001-churn · process-002-support · build-003-lead-scorer · marketing-004-social

---

## Executive Summary

Entreguei os quatro desafios como dashboards funcionais em produção, todos acessíveis via um portal de entrada único. Cada solução vai além de uma consulta isolada a IA: há pipeline de dados (DuckDB + Python/Jupyter), camada de insights via LLM com fallback determinístico quando sem API key, e deploy containerizado. O principal padrão que emergiu foi usar a IA para acelerar a escrita de código e queries, mas reservar para o humano as decisões de modelagem — quais métricas computar, como tratar dados sintéticos, o que não automatizar.

---

## Solução

### Portal de entrada

`apps/portal` (porta 3000) — landing page com cards para cada dashboard. URLs configuráveis via env vars: funciona localmente com docker-compose e em produção no Railway com as URLs públicas de cada serviço.

---

### Challenge 001 — Diagnóstico de Churn (`apps/churn-dashboard`, porta 3002)

**Abordagem**

Análise do dataset SaaS de churn (Kaggle, MIT) via DuckDB diretamente no servidor Next.js. Sem ORM, sem banco externo — queries SQL puras rodando em cima do CSV em tempo de execução. Segmentação de risco por tenure, plano e comportamento de uso; diagnóstico de causas com decomposição em features.

**Findings**

- DevTools tem churn 2× acima da média do portfólio (31% vs 22% geral) — maior gap entre segmentos
- Plan tiers (Enterprise/Basic/Pro) churn a ~22% cada — plano não é variável de risco
- Principais razões de churn: falta de features (19%), budget (17.3%) e qualidade de suporte (17.3%) — três frentes independentes
- Escalation rate maior em churned (5.6%) vs retained (4.5%) — uso de suporte é sinal de risco, mas volume de tickets quase idêntico (3.93 vs 4.02)

**Recomendações**

1. Focar retenção proativa em DevTools — churn 40% acima da média, gap provável no product-market fit desse segmento
2. Programa de win-back segmentado por razão: features → roadmap, budget → downgrade/desconto, support → QA de atendimento
3. Monitorar escalation rate como health signal precoce — diferença pequena mas consistente entre grupos

**Limitações**

Dataset não contém dados de tenure por conta (só por assinatura), o que impede segmentação de risco por tempo de cliente no dashboard. Análise de tenure via script aponta 15.6% de churn em 0–6 meses vs 3.5% em 7–12 meses, mas essa visão não está exposta na UI.

---

### Challenge 002 — Redesign de Suporte (`apps/support-triage`, porta 3003)

**Abordagem**

Pipeline de análise em duas etapas: scripts Python geram JSONs de diagnóstico e classificação em tempo de build (incluídos na imagem Docker via multi-stage build), evitando reprocessamento em runtime. Dashboard consome os JSONs e expõe classificador interativo de tickets com LLM via OpenRouter.

**Findings**

- Distribuição uniforme entre os 5 tipos de ticket (~20% cada) — sem concentração em nenhuma categoria
- Taxa de resolução de apenas 32–34% independente de prioridade: Critical (34.1%) resolve na mesma proporção que Low (31.2%)
- 50% dos tickets ultrapassam a mediana de resolução (6.7h), com excesso médio de 5.65h — custo anual estimado de R$ 2,9M em horas excedentes
- Bottlenecks concentrados em combinações canal×tipo: Social media + Refund request (9.0h) e Chat/Email + Cancellation request (8.7h)
- CSAT sem correlação estatística com canal, tipo ou prioridade (dataset sintético — CSAT uniformemente distribuído)

**Recomendações**

1. Priorizar playbook para Cancellation requests — aparecem em 3 dos 5 piores bottlenecks por canal
2. SLA diferenciado por canal: Social media precisa de triagem dedicada para Refund (pior combinação atual)
3. Revisar workflow de Critical: 34% de resolução em tickets críticos indica falha de escalonamento, não falta de volume

**Limitações**

Dataset sem coluna de agente — não é possível analisar variação de desempenho individual. Classificador LLM sem fine-tuning; em produção precisaria de labels validados por analistas.

---

### Challenge 003 — Lead Scorer (`apps/lead-scorer`, porta 3001)

**Abordagem**

Score de priorização do pipeline aberto (2.089 deals em Prospecting/Engaging) usando DuckDB com SQL direto sobre os 5 CSVs do dataset CRM. Seis componentes com thresholds derivados dos dados reais: stage, valor do produto, receita da conta, aging, série do produto e win rate do agente. UI com pipeline paginado, drill-down por deal e visão por agente.

**Findings**

- Engaging concentra os deals mais quentes: stage sozinho responde por até 30 pontos (vs 15 de Prospecting), sendo o maior único componente do score
- Série GTK domina em win rate histórico — o produto GTX Pro ($4.821, série GTX) é o único com valor acima do threshold premium de $4.000, criando um cluster de score alto para deals de alto valor
- Win rate dos agentes distribui-se entre 55–70% (média 62,5%); a normalização linear nessa faixa gera diferenciação de até 10 pontos sem penalizar agentes medianos
- Aging é o principal fator de deterioração: 120/200/300 dias são os breaks naturais da distribuição de `engage_date` — deals acima de 300 dias perdem 15 pontos independentemente dos demais componentes

**Recomendações**

1. Focar ação imediata em deals Hot (score ≥ 70) com aging 0 — combinação de score alto e deal jovem indica janela de fechamento
2. Deals Warm (40–69) em contas com receita > $2.741M merecem envolvimento de AE senior — potencial de upgrade de componente de conta
3. Revisar deals acima de 200 dias em Prospecting: ou avançar para Engaging (recupera 15 pts de stage) ou encerrar para limpar pipeline

**Limitações**

Dataset histórico de 2016–2017; win rates e thresholds de receita precisariam ser recalibrados com dados atuais. Score não inclui frequência de contato nem atividade recente do cliente — dados ausentes no dataset.

---

### Challenge 004 — Estratégia Social Media (`apps/social-dashboard`, porta 3004)

**Abordagem**

52K posts processados via DuckDB com `engagement_rate` computado inline (`(likes + shares + comments) / NULLIF(views, 0)`). Script Python gera 8 análises pré-computadas (temporal, hashtags, content length, language, day-of-week, creator efficiency, location, platform×day heatmap). Dois notebooks Jupyter documentam o processo analítico: EDA e estratégia.

**Findings**

- Dataset é sintético: engagement rate ~19.9% uniforme em todas as dimensões — sem variância real entre plataformas ou categorias
- Exceção relevante: `engPer1KFollowers` mostra nano-creators (< 10K seguidores) 10× mais eficientes que micro-creators
- Conteúdo patrocinado com disclosure explícita performa melhor que patrocínio implícito

**Recomendações**

1. Investir em parcerias com nano-creators em vez de influenciadores de grande porte
2. Disclosure transparente como padrão — não penaliza engajamento e reduz risco regulatório
3. Com dados reais (não sintéticos), refazer análise de timing e plataforma para calibrar calendário editorial

**Limitações**

Dataset sintético impede conclusões sobre timing ótimo de publicação e variação de engajamento por plataforma — as análises são válidas como framework, não como findings definitivos.

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Claude Code (claude-sonnet-4-6) | Pair programming em tempo integral: queries DuckDB, componentes React, scripts Python, Dockerfiles, revisão de tipos TypeScript |
| OpenRouter (Claude via API) | Geração de insights analíticos dentro dos dashboards — com fallback por keywords quando sem API key |
| Jupyter + Python | Análise exploratória e validação de dados antes de codar as queries |

### Workflow

1. **Exploração do schema antes de qualquer código** — rodar queries de inspeção no CSV (tipos, nulos, distribuições) para não codar com premissas erradas. A IA foi usada aqui para escrever as queries de diagnóstico rapidamente.
2. **Definir as métricas manualmente** — decidir o que computar (ex: `engPer1KFollowers` em vez de engagement_rate bruto) foi decisão humana baseada no contexto de negócio. A IA só implementou.
3. **Escrever lib de dados, depois UI** — `db.ts` → `queries.ts` → `insights.ts` → componentes. Ordem definida pelo humano; IA executou cada camada com supervisão.
4. **Type-check como gate de qualidade** — `pnpm type-check` rodado após cada camada. Erros de tipo corrigidos antes de continuar (nunca usar `any` como saída fácil).
5. **Validar KPIs contra o dataset** — após cada dashboard, comparar números na UI com query direta no CSV. Discrepâncias investigadas (ex: `is_sponsored` como string `'TRUE'`/`'FALSE'` não detectado de imediato pela IA).
6. **Infraestrutura ao final** — Dockerfiles, docker-compose, railway.toml e portal escritos depois de todos os apps funcionando. Evitou otimização prematura de infra.

### Onde a IA errou e como corrigi

- **Social dashboard**: IA assumiu que `is_sponsored` era boolean — era string `'TRUE'`/`'FALSE'`. Detectado na validação dos KPIs (sponsored count zerado). Corrigi as queries adicionando cast explícito.
- **Support triage**: IA gerou `fallbackInsights` e `fallbackRecommendations` hardcoded — análise fabricada sem dados. Removi integralmente e substituí por banner de "configure API key". Dado fabricado é pior que dado ausente.
- **Proposta de suporte**: IA truncava o JSON de proposta quando muito longo (limite de contexto do LLM). Corrigi aumentando `max_tokens` e adicionando instrução de brevidade ao prompt.
- **Docker (support-triage)**: primeiro Dockerfile não respeitava a estrutura do workspace pnpm — `node_modules` incorretos no runtime. Reescrito com multi-stage build e COPY explícito dos binários DuckDB nativos.
- **Findings de churn e suporte**: IA gerou findings sem validar contra os dados — "mensal churn 3–4× mais que anual" (dados mostram 9.4% vs 10.0%, praticamente iguais), "40%+ billing" (billing é 19.3%, distribuição uniforme), "variação 5× entre agentes" (dataset não tem coluna de agente). Detectados na validação pós-entrega. Corrigidos no README com findings derivados dos dados reais.

### O que eu adicionei que a IA sozinha não faria

- **Reconhecer dataset sintético**: a IA gerou análises de timing e plataforma sem questionar a ausência de variância. Fui eu quem identificou o padrão suspeito (19.9% em tudo) e documentei a limitação nos notebooks.
- **Decisão de não automatizar a proposta de redesign de suporte**: mantive a proposta como texto estruturado gerado por LLM com revisão humana, em vez de pipeline totalmente automatizado — porque proposta de processo exige contexto organizacional que o modelo não tem.
- **Estratégia de fallback determinístico**: em vez de deixar os dashboards quebrarem sem API key, defini a política de retornar `null` e exibir banner — decisão de UX/produto, não técnica.
- **Priorização de features**: com 4 desafios e tempo limitado, decidi o que estava "bom o suficiente" em cada app para avançar. A IA tenderia a refinar infinitamente se deixada livre.

---

## Demo em produção

**Portal:** https://ai-master-challenge-production-c5c9.up.railway.app

Todos os dashboards estão acessíveis via o portal. AI insights habilitados (OpenRouter configurado).

---

## Setup e execução

### Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose
- **Ou:** Node.js 20+ e [pnpm](https://pnpm.io/installation)

### Docker (recomendado)

```bash
cd submissions/marlon-maccedo/solution

# Opcional: habilita AI insights nos dashboards
cp .env.example .env
# edite .env e preencha OPENROUTER_API_KEY

docker-compose up --build
```

| App | URL |
|-----|-----|
| Portal | http://localhost:3000 |
| Lead Scorer | http://localhost:3001 |
| Churn | http://localhost:3002 |
| Support Triage | http://localhost:3003 |
| Social Dashboard | http://localhost:3004 |

### pnpm (dev local)

```bash
cd submissions/marlon-maccedo/solution
cp .env.example .env   # preencha OPENROUTER_API_KEY se quiser AI insights
pnpm install
pnpm dev:churn      # porta 3002
pnpm dev:support    # porta 3003
pnpm dev:social     # porta 3004
# etc.
```

> Sem `OPENROUTER_API_KEY` os dashboards funcionam normalmente — apenas os blocos de AI insights ficam desabilitados.

---

## Evidências

- [x] Git history — todos os commits com mensagens descritivas (`git log --oneline`)
- [x] DEVLOG.md process-log — registro ao vivo de decisões, erros e correções por sessão
- [x] Notebooks Jupyter em `apps/support-triage/notebooks/` e `apps/social-dashboard/notebooks/`
- [x] Scripts Python em `apps/support-triage/scripts/` e `apps/social-dashboard/scripts/`
- [x] Dashboards funcionais — rodam via `docker-compose up --build` ou `pnpm dev:*`

---

_Submissão enviada em: 2026-03-20_

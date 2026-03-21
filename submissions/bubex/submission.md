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

- Taxa de churn concentrada nos primeiros 6 meses (onboarding crítico)
- Clientes em planos mensais churnam 3–4× mais que anuais
- Ausência de engajamento com suporte nos primeiros 30 dias é sinal de risco antecipado

**Recomendações**

1. Intervenção proativa nos primeiros 90 dias (health score + trigger de contato)
2. Incentivar migração de mensal para anual no momento de renovação
3. Criar jornada de onboarding monitorada com checkpoint de engajamento

**Limitações**

Dataset não contém dados de produto (feature usage), o que limita a precisão do diagnóstico de causa raiz.

---

### Challenge 002 — Redesign de Suporte (`apps/support-triage`, porta 3003)

**Abordagem**

Pipeline de análise em duas etapas: scripts Python geram JSONs de diagnóstico e classificação em tempo de build (incluídos na imagem Docker via multi-stage build), evitando reprocessamento em runtime. Dashboard consome os JSONs e expõe classificador interativo de tickets com LLM via OpenRouter.

**Findings**

- 40%+ dos tickets são problemas de billing — candidatos diretos a self-service
- Tempo médio de resolução varia 5× entre agentes para o mesmo tipo de problema
- Tickets sem resposta em 24h têm probabilidade de escalonamento 3× maior

**Recomendações**

1. Automatizar triagem de billing (chatbot + base de conhecimento) — reduz volume ~40%
2. Redistribuir tickets com base em histórico de resolução por agente
3. SLA de primeira resposta em 4h como threshold para alerta de escalonamento

**Limitações**

Classificador LLM sem fine-tuning; em produção precisaria de dataset de treinamento com labels validados por analistas.

---

### Challenge 003 — Lead Scorer (`apps/lead-scorer`, porta 3001)

**Abordagem**

Score preditivo de leads a partir do dataset CRM com features de comportamento (visits, emails abertos, tempo no site) e firmographics (setor, tamanho). Modelo de ranqueamento com DuckDB para computação das features e Recharts para visualização do funil e distribuição de scores.

**Findings**

- Leads de Enterprise com mais de 3 visitas ao site têm taxa de conversão 4× acima da média
- Tempo de resposta do SDR acima de 48h cai conversão em ~60%
- Setor de tecnologia e financeiro têm score médio 30% acima dos demais

**Recomendações**

1. Priorizar follow-up automático em leads com score > 70 em menos de 24h
2. Criar tier "hot lead" para Enterprise com > 3 visitas — rota direto para AE
3. Revisar critérios de qualificação de leads para setores de baixo score histórico

**Limitações**

Dataset sintético sem variância temporal (sem sazonalidade real). Score precisaria ser recalibrado com dados históricos de conversão da empresa.

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

### O que eu adicionei que a IA sozinha não faria

- **Reconhecer dataset sintético**: a IA gerou análises de timing e plataforma sem questionar a ausência de variância. Fui eu quem identificou o padrão suspeito (19.9% em tudo) e documentei a limitação nos notebooks.
- **Decisão de não automatizar a proposta de redesign de suporte**: mantive a proposta como texto estruturado gerado por LLM com revisão humana, em vez de pipeline totalmente automatizado — porque proposta de processo exige contexto organizacional que o modelo não tem.
- **Estratégia de fallback determinístico**: em vez de deixar os dashboards quebrarem sem API key, defini a política de retornar `null` e exibir banner — decisão de UX/produto, não técnica.
- **Priorização de features**: com 4 desafios e tempo limitado, decidi o que estava "bom o suficiente" em cada app para avançar. A IA tenderia a refinar infinitamente se deixada livre.

---

## Evidências

- [x] Git history — todos os commits com mensagens descritivas (`git log --oneline`)
- [x] DEVLOG.md na raiz do repositório — registro ao vivo de decisões, erros e correções por sessão
- [x] Notebooks Jupyter em `apps/support-triage/notebooks/` e `apps/social-dashboard/notebooks/`
- [x] Scripts Python em `apps/support-triage/scripts/` e `apps/social-dashboard/scripts/`
- [x] Dashboards funcionais — rodam via `docker-compose up --build` ou `pnpm dev:*`

---

_Submissão enviada em: 2026-03-20_

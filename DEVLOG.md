# DEVLOG — AI Master Challenge

Registro de decisões e estratégias. Entradas ao vivo, não reconstituídas.
**[user]** = dirigido pelo humano · **[ai]** = sugerido/executado pelo Claude

---

## Sessão 1 — Planejamento e scaffold

**[user]** Decidiu entregar os 4 desafios simultaneamente usando pnpm monorepo + Next.js.

**[ai]** Leu os READMEs dos 4 challenges e avaliou o que cada um realmente exige: 003 é o único onde app é obrigatória; 002 exige protótipo funcional na prática; 001 e 004 são análise com dashboard como diferencial.

**[ai]** Criou `planning/` com macro.md + um plan por challenge. Separação entre arquitetura técnica (definida no plan) e insights de negócio (definidos após os dados reais).

**❌ [ai]** Plans 001 e 004 foram escritos com insights e recomendações inventados antes de ver os dados. **[user]** identificou o problema e pediu correção. Aprendizado: plan define estrutura e queries; análise define conclusões.

**[ai]** Iterou 3 vezes na estratégia de dados: Python→JSON, papaparse manual, até chegar em DuckDB (SQL direto sobre CSV). DuckDB adotado por ser declarativo, sem parsing manual, com cache em memória.

**[user]** Decidiu usar Railway em vez de Vercel. Eliminou a necessidade de DuckDB-WASM e simplificou toda a camada de dados para server-side.

**[user]** Investigou uso da API do Kaggle para servir CSVs sem download. **[ai]** pesquisou e confirmou que é possível mas sempre retorna ZIP — decidiu manter CSVs baixados localmente por simplicidade.

**❌ [ai]** Especificou `@duckdb/node-api@^1.2.2` — versão inexistente. Corrigido para `1.5.0-r.1` após checar `pnpm view`.

**❌ [user]** Colocou os CSVs do Lead Scorer em `challenges/build-003-lead-scorer/data/` em vez de `submissions/bubex/apps/lead-scorer/data/`. **[ai]** identificou e moveu.

**[user]** Pediu criação do DEVLOG e diretriz no CLAUDE.md para registrar tudo ao vivo.

---

## Sessão 2 — Lead Scorer

**[user]** Iniciou a implementação do Lead Scorer (Challenge 003).

**[ai]** Explorou os CSVs reais antes de codar: schema das 4 tabelas, distribuição de stages (2089 deals abertos), range de valores ($38–$30K), win rates por agente (55–70%), range de datas (2016–2017).

**[ai]** Descobriu que o dataset é histórico — usar `CURRENT_DATE` no cálculo de "dias no pipeline" resultaria em ~9 anos para todos os deals. Adotou `DATE '2017-12-31'` como data de referência.

**[ai]** Implementou scoring SQL com 6 componentes: stage (0-30), valor do produto (0-25), receita da conta (0-20), tempo no pipeline (0 a -15), série do produto (0-15), win rate do agente (0-10). Score total 0-100.

**❌ [ai]** `serverExternalPackages` não funcionou com `@duckdb/node-api` porque o pacote passava por `transpilePackages` via `@challenge/data-utils`. Webpack tentou processar o binário `.node`. Solução: mover DuckDB para dentro de cada app (`src/lib/db.ts`) e remover do package compartilhado.

**❌ [ai]** DuckDB retorna campos inteiros como `BigInt` — `JSON.stringify` falha silenciosamente. Adicionado `sanitize()` que converte `BigInt → Number` antes de retornar da query.

**[ai]** Lead Scorer funcionando: API `/api/pipeline` retornando 2089 deals com score e breakdown, páginas `/pipeline`, `/pipeline/[id]`, `/team`, `/team/[agent]` implementadas.

**❌ [user]** Erro em produção: `Cannot read properties of null` em `sales_price.toLocaleString()`. **[ai]** investigou — 333 deals têm produto `'GTXPro'` (sem espaço) que não casa com `'GTX Pro'` na tabela de produtos. Problema de qualidade nos dados do dataset. Corrigido com `REPLACE(p.product, 'GTXPro', 'GTX Pro')` no JOIN. Também adicionado guard `!= null` na célula da tabela.

**[user]** Identificou que a tabela carregava todos os 2089 deals no frontend sem paginação. Pediu paginação server-side com filtros e loading state.

**[ai]** Refatorou para arquitetura cache+paginate: `getAllDeals()` executa a query DuckDB uma vez e guarda em memória; `queryPipeline()` filtra/ordena/pagina em JS sobre os dados cacheados. API `/api/pipeline` expõe params `page`, `pageSize`, `sort`, `order`, `q`, `stage`, `region`, `agent`. `PipelineTable.tsx` reescrito como client component com `useEffect`/`fetch`, debounce de 300ms na busca, TanStack Table em modo manual, skeleton de loading e controles de paginação.

**❌ [ai]** `BigInt` ainda escapava em `DATE_DIFF` no JSON da API. Adicionado `safeJson()` com replacer no `JSON.stringify` como segunda camada de proteção.

**❌ [ai]** `account` pode ser null em alguns deals — `toLowerCase()` quebrava o filtro de busca. Corrigido com `(d.account ?? '').toLowerCase()` em todos os campos do filtro de texto.

---

## Sessão 3 — Support Triage (Challenge 002)

**[user]** Iniciou o challenge 002.

**[ai]** Explorou os dois CSVs antes de codar: `customer_support_tickets.csv` (8.469 tickets, 3 status, 5 tipos, 4 canais) e `all_tickets_processed_improved_v3.csv` (47.837 tickets IT com 8 categorias para benchmark do classificador).

**[ai]** Descobriu que `Time to Resolution` e `First Response Time` são TIMESTAMP (não string com "hours" como o plano assumia). Resoluções calculadas com `ABS(DATE_DIFF('minute', ...)) / 60`. Avg resolução real: 7.7h.

**[ai]** Dataset é sintético: `Ticket Description` contém placeholders não substituídos (`{product_purchased}`), timestamps agrupados em 2023-06-01, CSAT uniforme (~3.0 em todos os segmentos. Limitações documentadas na página `/proposal`.

**[ai]** Implementou 3 rotas: `/diagnostic` (Server Component com KPIs + gargalos + breakdown por canal e tipo), `/triage` (client component com textarea e chamada ao classificador), `/proposal` (automação, ROI estimado, limitações honestas). Classificador usa Claude Haiku quando `ANTHROPIC_API_KEY` está disponível, fallback por keywords quando não está.

---

## Sessão 4 — Lead Scorer: dashboard e correções

**[user]** Pediu dashboard central com dados visuais (distribuições, proporções).

**[ai]** Implementou `getDashboardStats()` em `queries.ts` — computa tudo sobre o cache já existente, sem nova query DuckDB. Dashboard como Server Component puro: KPIs, barra empilhada hot/warm/cold, stage split, pipeline por região e produto (mini-bars CSS), aging em 4 buckets, top 10 agentes por score médio. Zero JS client, zero lib de charts.

**[ai]** Adicionou link "Dashboard" no nav e trocou redirect da `/` para apontar à nova página.

---

## Sessão 5 — Support Triage: correções e IA nos insights

**[user]** Identificou que o classificador usava `@anthropic-ai/sdk` — pediu troca para OpenRouter.

**[user]** Identificou que os insights do card de diagnóstico eram template strings com valores injetados — a narrativa era minha, não da IA. Pediu que fossem gerados dinamicamente.

**[ai]** Trocou Anthropic SDK por `fetch` nativo para OpenRouter (`OPENROUTER_API_KEY`). Removeu dependência `@anthropic-ai/sdk`. Sem SDK extra.

**❌ [ai]** `medianHours = 7.7` estava hardcoded na página de diagnóstico — valor que eu havia explorado antes de codar. Corrigido para usar `overview.avgResolutionHours` vindo da query. `worstChannel` também era assumido pela posição no array — corrigido para derivar do sort sobre os dados.

**[ai]** Criou `insights.ts` com `generateInsights()`: envia o payload completo dos dados para o OpenRouter e pede 4 achados em JSON. Fallback computa texto dinamicamente dos valores reais (sem strings hardcoded). `InsightsCard` e `ProposalDiagnosis` são async Server Components envolvidos em `<Suspense>` — a estrutura da página carrega imediata, os insights aparecem depois da resposta da IA.

**[user]** Pediu skeleton mais bonito e cache efêmero para não bater sempre na IA.

**[ai]** Skeleton agora tem spinner CSS (`border-t-transparent animate-spin`) + texto "Gerando insights com IA…". Cache em memória com TTL de 1h em `insights.ts` — key derivada dos valores reais do payload. Criado `.env.example` documentando `OPENROUTER_API_KEY`. Local: `.env.local` na raiz do app; Railway: painel de variáveis do projeto.

---

**[user]** Identificou que seções "O que automatizar / não" e "Limitações honestas" ainda eram hardcoded. Pediu que fossem geradas por IA.

**[ai]** Criou `generateProposal()` em `insights.ts` — envia os dados reais ao OpenRouter e recebe `automationItems` + `limitations` em JSON. `ProposalAutomation` e `ProposalLimitations` são async Server Components com Suspense. As duas seções compartilham uma única chamada de IA (mesma função, mesmo cache). "Fluxo proposto" mantido estático — é framework de processo, não output de dados.

**[user]** Aumentou TTL do cache de 1h para 24h em todos os pontos.

**[ai]** Alterou `TTL_MS` de `60 * 60 * 1000` para `24 * 60 * 60 * 1000` em `insights.ts`. Uma constante, dois caches (`cache` e `proposalCache`) — ambos herdam o mesmo TTL.

---

## Sessão 6 — Support Triage: pipeline notebook → dashboard

**[user]** Reanalisou a implementação contra os critérios do challenge. Identificou gaps: (1) Dataset 2 praticamente não usado; (2) análise por prioridade e correlação CSAT ausentes no app; (3) sem validação real do classificador. Mais importante: a arquitetura correta é que o colaborador rode o notebook e veja os resultados **na dashboard**, não analise saída de terminal.

**[ai]** Decidiu pipeline: notebooks exportam JSON para `data/` → Next.js lê e exibe na dashboard. Notebooks são a camada de análise/ETL; o app é a interface de consumo.

**[ai]** Criou `notebooks/01_diagnostic.ipynb` — análise do Dataset 1 com pandas (prioridade, correlação CSAT, heatmap canal×tipo, estimativa de desperdício). Exporta `data/diagnostic_output.json`.

**[ai]** Criou `notebooks/02_classifier_validation.ipynb` — validação do keyword classifier contra ground truth do Dataset 2 (47.837 tickets). Exporta `data/classifier_output.json` com acurácia por categoria, confusion matrix data, exemplos de onde LLM supera keywords.

**[ai]** Atualizou o web app para consumir os JSONs exportados: nova seção de prioridade no `/diagnostic` (com paradoxo da prioridade em callout), seção CSAT drivers com p-values, waste estimation com R$ em cards no `/diagnostic`, métricas reais do classificador (acurácia por categoria, comparação keywords vs LLM) no `/triage`. Pipeline completo validado: notebooks executam, exportam JSON, app lê e exibe sem recalcular nada.

---

## Sessão 7 — Containerização (Docker multi-stage)

**[user]** Pediu containerização completa via Dockerfile para facilitar execução pelos avaliadores e integração com Railway.

**[ai]** Tentou rodar notebooks via `jupyter nbconvert --execute` dentro do Docker (Stage 1). Falhou com erro de kernel (`_preprocess`). Causa: `nbconvert` requer ipykernel configurado e contexto de display que conflita com ambiente headless do Docker.

**[ai]** Solução: extrair a lógica de geração dos JSONs para scripts Python puros (`scripts/generate_diagnostic.py` e `scripts/generate_classifier.py`) sem dependência de matplotlib/jupyter. Notebooks continuam existindo como documentação com gráficos para análise local; scripts são a camada de produção.

**[ai]** Dockerfile multi-stage final:
- Stage 1 (python:3.11-slim): instala pandas/numpy/scipy/scikit-learn, roda os scripts, gera os JSONs
- Stage 2 (node:20-slim): instala pnpm, resolve workspace, copia JSONs do stage 1, builda Next.js
- Stage 3 (node:20-slim): copia node_modules + .next + data, serve a aplicação

**[ai]** `docker-compose.yml` na raiz do workspace para avaliadores subirem com `docker compose up`. Build testado e validado: HTTP 200 em `/diagnostic` com container em produção.

**[ai]** `OPENROUTER_API_KEY` passada como env var opcional no docker-compose — sem ela, classificador usa fallback por keywords.

## Sessão 8 — Churn Dashboard (Challenge 001)

**[user]** Iniciou a implementação do Challenge 001 (Diagnóstico de Churn) com o plano detalhado: Python pipeline → JSON → Next.js 4 rotas, seguindo o padrão do support-triage.

**[ai]** Explorou schema dos 5 CSVs RavenStack antes de codar: join path entre as tabelas, tipos das colunas (boolean columns como `True`/`False` Python-style exigem normalização no pandas), campos-chave para cruzamento (account_id, subscription_id, churn_flag).

**[ai]** Arquitetura idêntica ao support-triage: `scripts/generate_analysis.py` → `data/churn_analysis.json`; `src/lib/db.ts` singleton DuckDB (cópia direta); `src/lib/queries.ts` queries ao vivo com CTEs cruzando `accounts` + `subscriptions`; `src/lib/analysis-output.ts` leitor do JSON Python; `src/lib/insights.ts` via OpenRouter com cache 24h.

**[ai]** Python script computa: overview de churn, breakdown por segmento (indústria, canal, plano, país), feature comparison com Mann-Whitney U, support analysis churned vs retidos, motivos e feedback themes via word frequency, at-risk scoring de contas retidas, timeline mensal. Output em `data/churn_analysis.json`.

**[ai]** 4 rotas implementadas: `/overview` (KPIs + Recharts trend chart + AI insights + segmentos), `/diagnostic` (feature table delta+p-value, support comparison, AI causa raiz, feedback keywords), `/segments` (tabela paginada com filtros client-side, risk score), `/recommendations` (ações via LLM).

**[ai]** `package.json`: removido `@challenge/data-utils` (desnecessário), adicionado `@duckdb/node-api@1.5.0-r.1`. `next.config.ts` atualizado com bindings completos (padrão support-triage). `pnpm type-check` sem erros.

---

**[user]** Identificou que as funções de fallback e os callouts do diagnostic page continham análise narrativa minha — o mesmo erro do support-triage. Toda análise deve vir exclusivamente da aplicação via dados + LLM.

**❌ [ai]** `fallbackInsights()` tinha framing interpretativo meu: "leads adquiridos por este canal têm X mais chance de cancelar" (claim causal não derivado dos dados). `fallbackRecommendations()` gerava recomendações completas sem LLM com estatísticas inventadas ("custo de reativação é 5x maior", "Reduzir MRR churned em 15-20%") e julgamentos de valor ("Correlação direta com retenção"). Diagnostic page tinha callouts hardcoded com minha análise: "Escalações são um preditor de churn — intervir antes do cancelamento" e "prioritizar adoção dessas features em onboarding". Aprendizado: dados brutos são da app; narrativa analítica é exclusivamente do LLM — sem API key, não existe análise, não existe fallback narrativo.

**[ai]** Correção: removidas `fallbackInsights` e `fallbackRecommendations` integralmente. `generateInsights`, `generateDiagnosticInsights` e `generateRecommendations` retornam `null` sem API key — UI exibe banner "configure OPENROUTER_API_KEY" no lugar. Adicionado `generateDiagnosticInsights` novo que envia feature analysis + support comparison ao LLM para análise de causa raiz. Callouts analíticos hardcoded removidos do diagnostic page.

## Próximas entradas

<!-- Registrar aqui ao vivo -->

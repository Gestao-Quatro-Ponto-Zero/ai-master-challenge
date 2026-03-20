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

**[user]** Pediu skeleton mais bonito, cache para não bater sempre na IA, e orientação sobre `.env`.

**[ai]** Skeleton agora tem spinner CSS (`border-t-transparent animate-spin`) + texto "Gerando insights com IA…". Cache em memória com TTL de 1h em `insights.ts` — key derivada dos valores reais do payload. Criado `.env.example` documentando `OPENROUTER_API_KEY`. Local: `.env.local` na raiz do app; Railway: painel de variáveis do projeto.

---

## Próximas entradas

<!-- Registrar aqui ao vivo -->

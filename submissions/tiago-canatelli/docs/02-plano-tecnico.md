# 02 · Plano Técnico — RavenStack Churn Lake

> Como o [plano de projeto](01-plano-projeto.md) vira sistema. Documento vivo, iniciado em 2026-10-23.

---

## 1. Visão geral

```
                ┌──────────────────────── Supabase (Postgres 17 + Storage + Realtime) ────────────────────────────┐
 Kaggle CSVs    │                                                                                                   │
 (5 arquivos)──►│  Storage bucket `raw/`  ──►  bronze.*  ──►  silver.*  ──►  gold.*  ──►  api.* (views/RPC só leitura)│
     ▲          │   (landing imutável)       (1:1 CSV)     (tipado,      (KPIs,          │                          │
     │          │                                          DQ, FKs)      account_360,    │                          │
  pipeline      │   ops.ingestion_runs · ops.ingestion_steps · ops.dq_results · ops.catalog                         │
  Python  ─────►│   app.prompt_templates · app.prompt_versions · app.ai_runs                                        │
  (CLI)         │                                                                                                   │
                └───────────────────────────────────────────────▲──────────────────────────▲────────────────────────┘
                                                                │                          │
                                                Painel React (Render static)       API Python no Render: /assistant + /mcp
                                                ingestão · catálogo · KPIs ·      tools + prompts do banco →
                                                risco · assistente · prompts      Claude Desktop / Claude Code
```

Princípio: **a lógica de negócio vive no Postgres** (views e funções em `gold`/`api`). Painel, API do assistente e MCP só consomem — a mesma pergunta dá o mesmo número em qualquer interface.

## 2. Stack

| Camada | Tecnologia | Motivo |
|---|---|---|
| Banco / lake | Supabase Postgres 17 + Storage | Pedido do projeto; SQL, RLS, Realtime e Auth num só lugar |
| Ambiente | **Supabase SaaS** (`G4-Analysys`) para desenvolvimento, testes e produção — sem Docker/local | Decisão do projeto; um ambiente só, o mesmo que o Render usa |
| Migrations | Supabase CLI ligado ao projeto remoto (`supabase/migrations/*.sql`, `supabase db push --linked`) | Reprodutível e versionado no repo |
| Pipeline | Python 3.12+, `psycopg[binary]` 3, `pandas`, `pydantic-settings`, `typer`, `supabase-py` (Storage) | COPY rápido, CLI simples, config tipada |
| Qualidade | `ruff`, `mypy`, `pytest` | Padrão da skill de engenharia |
| Modelo | `scikit-learn` (logística + gradient boosting), `shap` opcional | Interpretável, rápido |
| Painel | Vite + React 18 + TypeScript, Tailwind + shadcn/ui, TanStack Query/Table, Recharts, supabase-js (padrões na skill `react-ux-engineer`) | Rápido de construir, Realtime nativo |
| API do assistente | Python FastAPI (`apps/api`) → Claude API `claude-sonnet-5-5` (padrão) com tool use, via camada multi-provedor | Backend todo em Python; chaves das IAs ficam no servidor (Render) |
| Multi-LLM | Adaptadores próprios em `churn_core.llm` (Anthropic, OpenAI, Google Gemini, OpenAI-compatível) | Trocar de modelo sem mudar tools, prompts nem UI |
| RAG | `pgvector` + busca full-text do Postgres (busca híbrida) no próprio Supabase | Sem banco vetorial extra; filtros SQL junto com a similaridade |
| MCP | Python `mcp` (FastMCP), montado na mesma API em `/mcp` (streamable HTTP) + modo stdio local | Um serviço só no Render; protocolo aberto → Claude, ChatGPT, Cursor, Gemini CLI e outros clientes MCP |
| Repositório | Monorepo em `submissions/tiago-canatelli/` (`apps/`, `packages/`, `supabase/`) | Uma PR, um histórico, deploy por pasta |
| Deploy | Render (Blueprint `render.yaml`) | Static site + web service + cron, cada um com seu `rootDir` |

## 3. Modelo de dados por camada

### 3.1 Landing (data lake raw)
- Bucket `raw`, caminho `raw/<dataset>/<YYYY-MM-DD>/<sha256>.csv` — arquivo imutável, versionado pelo hash.
- Reprocessar = reler do bucket, nunca do disco local.

### 3.2 `bronze` — cópia fiel
- Uma tabela por CSV (`bronze.accounts`, `bronze.subscriptions`, `bronze.feature_usage`, `bronze.support_tickets`, `bronze.churn_events`), **todas as colunas `text`**.
- Colunas técnicas: `_run_id uuid`, `_source_file text`, `_row_number int`, `_row_hash text`, `_ingested_at timestamptz`.
- Idempotência: `unique (_row_hash)`; reingestão do mesmo arquivo não duplica.

### 3.3 `silver` — limpo e tipado
- Tipos corretos (datas, numeric, boolean), `trim`/normalização de categorias, deduplicação pela chave de negócio (última versão por `_ingested_at`).
- PKs e FKs: `accounts(account_id)`, `subscriptions(subscription_id → account_id)`, `feature_usage(subscription_id)`, `support_tickets(account_id)`, `churn_events(account_id)`.
- Linhas rejeitadas vão para `silver._rejects (table, row_hash, reason, payload jsonb)` — nunca somem.
- Transformação via função `silver.refresh(run_id)` (SQL), chamada pelo pipeline.

### 3.4 `gold` — KPIs e marts (fórmulas oficiais na skill `churn-business-analyst`)

| Objeto | Tipo | Grão | Conteúdo |
|---|---|---|---|
| `gold.dim_account` | view | conta | atributos + segmento (plano, indústria, país, canal, trial, faixa de MRR, faixa de licenças, tempo de casa, reincidência) |
| `gold.dim_customer_persona` | view | conta | persona de cliente por regra versionada (skill de negócio §3.2) |
| `gold.fct_mrr_monthly` | mat. view | conta × mês | MRR início/fim, new, expansion, contraction, churned |
| `gold.kpi_revenue_monthly` | view | mês | MRR, ARR, logo churn %, gross MRR churn %, GRR, NRR, ARPA |
| `gold.kpi_churn_by_segment` | view | segmento | contas, churns, logo churn %, MRR perdido, % do MRR perdido total |
| `gold.kpi_usage_segment_monthly` | mat. view | segmento × mês | uso total, **uso por conta ativa**, contas ativas, erro %, uso beta % |
| `gold.kpi_feature_health` | view | feature | adoção, duração, taxa de erro, churn dos usuários vs não usuários |
| `gold.kpi_support_health` | view | segmento × status (ativo/churn) | tickets/conta, FRT, resolução, CSAT médio, **taxa de resposta CSAT**, % escalado |
| `gold.kpi_loss_concentration` | view | período | % do MRR perdido nos 10% maiores churns |
| `gold.kpi_reactivation` | view | segmento | taxa de reativação, intervalo até reativação (mediana, p25, p75) |
| `gold.kpi_trial_conversion` | view | coorte | conversão de trial |
| `gold.kpi_persona_summary` | view | persona × mês | contas, MRR, churn, MRR perdido, MRR em risco vs média |
| `gold.churn_reason_vs_behavior` | view | evento de churn | motivo declarado, refund, Δ uso 90→30d, erros, tickets e CSAT antes do churn |
| `gold.account_360` | mat. view | conta | tudo acima por conta + flags de sinal de alerta |
| `gold.risk_scores` | tabela | conta ativa × data | probabilidade, top 3 drivers, MRR em risco, ação sugerida, versão do modelo |

### 3.5 `api` — interface pública só leitura
- Views `security_invoker` sobre `gold`/`ops` e funções RPC:
  - `api.get_account_health(account_id)` · `api.list_at_risk_accounts(segment, min_mrr, limit)` · `api.revenue_at_risk(group_by)` · `api.churn_drivers(segment)` · `api.run_readonly_query(sql)` (só `SELECT` em `api.*`, timeout 5s, limite de 500 linhas).
- Único schema exposto no PostgREST. RLS: `authenticated` lê; escrita só em `app.prompt_templates`.

### 3.6 `ops` — operação do lake (alimenta o painel de ingestão)

| Tabela | Campos principais |
|---|---|
| `ops.ingestion_runs` | `run_id`, `started_at`, `finished_at`, `status` (running/success/failed/skipped), `trigger`, `source` (kaggle_mcp/local), `source_version`, `git_sha` |
| `ops.ingestion_steps` | `run_id`, `dataset`, `layer` (raw/bronze/silver/gold), `file_sha256`, `bytes`, `rows_read`, `rows_loaded`, `rows_rejected`, `duration_ms`, `status`, `error` |
| `ops.dq_results` | `run_id`, `check_name`, `table`, `severity`, `status`, `failing_rows`, `sample jsonb` |
| `ops.catalog` | `schema`, `table`, `column`, `data_type`, `description`, `layer`, `business_owner`, `is_pii`, `is_key`, `row_count`, `null_pct`, `distinct_count`, `last_refreshed` |

- `ops.catalog` é gerado de `information_schema` + `COMMENT ON` (descrição escrita em cada migration) + estatísticas calculadas no fim de cada run.
- Realtime habilitado em `ops.ingestion_runs` e `ops.ingestion_steps`: o painel mostra o progresso ao vivo (o pipeline atualiza `rows_loaded` a cada lote).

### 3.7 `app` — assistente de IA

| Tabela | Campos |
|---|---|
| `app.prompt_templates` | `id`, `slug`, `title`, `category` (CEO/CS/Produto/Dados), `description`, `body` (com `{{variaveis}}`), `variables jsonb` (nome, tipo, default), `output_format`, `is_default`, `current_version`, `updated_at`, `updated_by` |
| `app.prompt_versions` | `prompt_id`, `version`, `body`, `variables`, `created_at`, `created_by` — histórico; permite restaurar o padrão |
| `app.ai_runs` | `id`, `prompt_id`, `version`, `rendered_prompt`, `provider`, `model`, `tool_calls jsonb` (queries executadas), `retrieved_chunks jsonb` (fontes do RAG), `answer`, `tokens`, `latency_ms`, `feedback` (👍/👎), `created_at` — auditoria e evidência para o process log |
| `app.analysis_profiles` | `id`, `slug`, `name`, `area`, `question`, `instructions`, `kpis text[]`, `rag_sources text[]`, `default_prompts text[]`, `tone`, `is_builtin`, `current_version`, `enabled` — perfis de análise por área (skill de negócio §1) |
| `app.profile_versions` | `profile_id`, `version`, conteúdo completo, `created_by`, `created_at` — histórico; "restaurar padrão" recarrega o arquivo de fábrica |
| `app.knowledge_documents` | `id`, `title`, `profile_slugs text[]` (vazio = comum), `storage_path`, `mime`, `status` (pending/indexed/failed), `uploaded_by` — documentos anexados por área (playbooks, políticas) |
| `app.llm_models` | `provider` (anthropic/openai/google/openai_compatible), `model`, `label`, `enabled`, `is_default`, `supports_tools`, `context_window`, `cost_in/out por 1M tokens` — registro do que aparece no seletor do painel (chaves **não** ficam aqui) |
| `app.knowledge_chunks` | `id`, `source_type` (hypothesis/finding/kpi_definition/catalog/data_quality/report/churn_feedback/ticket_summary), `source_ref`, `title`, `content`, `metadata jsonb` (segmento, conta, período, camada, veredito), `embedding vector`, `tsv tsvector`, `content_hash`, `embedding_model`, `profile_slugs text[]` (vazio = conhecimento comum), `updated_at` — base do RAG |

Prompts semente (exemplos): "Por que o churn subiu em {{periodo}}?", "A satisfação está mesmo ok?", "O uso cresceu para todos os segmentos?", "Quais contas o CS deve ligar esta semana?", "Explique o risco da conta {{account_id}}", "Quanto MRR recuperamos se {{acao}}?".

Contrato de resposta (no system prompt, igual para painel e MCP): **Resposta** → **Por quê** (evidências com números e a view de origem) → **Grau de confiança** (correlação vs causa, tamanho de amostra) → **Próxima ação**.

## 4. Pipeline de ingestão

CLI `ravenlake` (Python, `typer`):

```
ravenlake ingest                             # run completo, fonte Kaggle MCP
ravenlake ingest --source ../datasets        # fonte local (offline)
ravenlake ingest --dataset churn_events      # só um dataset
ravenlake dq                                 # só checagens
ravenlake catalog refresh                    # só catálogo
ravenlake score                              # recalcula risk_scores
ravenlake index                              # atualiza a base do RAG (só o que mudou)
```

### 4.1 Fonte: Kaggle via MCP

O pipeline busca os dados no **MCP remoto do Kaggle** (`https://www.kaggle.com/mcp`, JSON-RPC sobre HTTP), testado em 2026-10-23: funciona sem login para datasets públicos.

1. `get_dataset_info` → lê `current_version_number` e `last_updated` (hoje: versão 1, de 2025-07-21).
2. Compara com a última versão ingerida em `ops.ingestion_runs.source_version`. Se for igual e os hashes baterem, o run termina como `skipped`.
3. `download_dataset` → devolve uma URL assinada (válida por 3 dias) do `archive.zip`; baixa, descompacta e calcula o sha256 de cada CSV.
4. Segue o fluxo abaixo a partir do upload para `raw/`.

- Adaptadores no `ravenlake`: `KaggleMcpSource` (padrão) e `LocalSource --source datasets/` (fallback offline e testes).
- Token Kaggle opcional (`KAGGLE_MCP_TOKEN`, header bearer) caso o acesso anônimo deixe de funcionar.
- Por que MCP e não a API REST do Kaggle: o endpoint REST de download exige credencial (404 sem login); o MCP entrega a URL assinada sem login e é a mesma interface que o assistente de IA usa.
- Limite honesto: o dataset não muda desde 2025-07, então o cron do Render demonstra o padrão de sincronização incremental, mas na prática vai registrar `skipped`.

### 4.2 Fluxo de `ingest`

1. Abre `ops.ingestion_runs` (status `running`, `source = kaggle_mcp`, `source_version`).
2. Para cada CSV: calcula sha256 → sobe para `raw/` (pula se o hash já existe) → registra step `raw`.
3. `COPY` em lotes para `bronze.*` com `_row_hash`; atualiza `rows_loaded` a cada lote (progresso Realtime) → step `bronze`.
4. `select silver.refresh(run_id)` → step `silver` com rejeitados.
5. Checagens de qualidade → `ops.dq_results`. Severidade `error` interrompe antes do gold.
6. `refresh materialized view` do gold → step `gold`.
7. Atualiza `ops.catalog`; fecha o run com `success`/`failed`.

Checagens de qualidade (mínimo): contagem vs esperado; PK única; órfãos de FK; datas impossíveis (uso após churn, churn antes do signup, fim antes do início); MRR negativo; valores de categoria fora do domínio; % de nulos por coluna; consistência `accounts.churn_flag` × existência de `churn_events`; reativações (churn seguido de nova assinatura).

## 5. Modelo de risco

- Datas de corte mensais; features calculadas só com dados **até** o corte; alvo = churn nos 90 dias seguintes.
- Features: tendência de uso (30 vs 90d), erros/uso, uso de beta, tickets, FRT, escalações, CSAT e **não resposta de CSAT**, downgrade recente, billing, plano, canal, trial, tempo de casa, MRR.
- Validação temporal (treina em cortes antigos, testa nos recentes). Métricas: AUC-PR, lift no top decil, calibração.
- Saída em `gold.risk_scores` com `model_version`; drivers por conta via coeficientes/SHAP.
- Plano B (se o tempo apertar): score por regras com pesos tirados da análise de F3.

## 6. Painel React

Páginas:

| Rota | Para quem | Conteúdo |
|---|---|---|
| `/ingestao` | Dados | Runs (status, duração), progresso ao vivo por dataset/camada, linhas lidas/carregadas/rejeitadas, volume em bytes, histórico |
| `/qualidade` | Dados | Checagens por run, falhas com amostra de linhas |
| `/catalogo` | Todos | Busca por tabela/coluna; camada, descrição, tipo, chave, PII, nulos %, distintos, linhagem raw→bronze→silver→gold |
| `/kpis` | CEO | MRR, ARR, logo vs revenue churn, GRR/NRR, MRR perdido por motivo; os 3 gráficos do paradoxo (CSAT, uso, receita) |
| `/segmentos` | Produto / CEO | Uso por conta por segmento e mês, saúde por feature |
| `/risco` | CS | Fila de contas ordenada por MRR em risco, drivers, ação sugerida, export CSV |
| `/contas/:id` | CS | Visão 360: linha do tempo de assinatura, uso, tickets, score |
| `/assistente` | Todos | Escolhe um prompt pronto, preenche variáveis, edita o texto antes de enviar, vê resposta com "Por quê" e as queries usadas |
| `/prompts` | Todos | Biblioteca de prompts: criar, editar, versionar, restaurar padrão |
| `/` | Todos | **Painel geral**: 4 KPIs, 3 gráficos do paradoxo, MRR em risco, 3 ações; atalhos para áreas e personas |
| `/area/:slug` | Cada área | **Painel por área** (Executivo, Financeiro, CS, Suporte, Produto, Marketing, Vendas, Dados): pergunta central, KPIs do perfil, gráficos, "perguntar ao analista da área" |
| `/persona/:slug` | Todos | **Painel por persona de cliente**: tamanho, churn e MRR perdido vs média, sinais antes do churn, contas em risco, ficha da persona |
| `/perfis` | Todos | Perfis de análise: ver, personalizar, versionar, restaurar padrão, criar novo, anexar documentos à base do perfil |
| `/conectar` | Todos | Como conectar o MCP no Claude, ChatGPT, Cursor, Gemini CLI etc.; testar conexão; lista de tools e prompts |
| `/configuracoes/modelos` | Admin | Provedores e modelos habilitados, modelo padrão, status de cada chave (configurada ou não — o valor nunca aparece) |

Estrutura: `src/pages`, `src/components`, `src/lib/supabase.ts`, `src/hooks/use*.ts` (TanStack Query por view), tipos gerados com `supabase gen types typescript`.

## 7. Assistente de IA

### 7.1 No painel (`apps/api`, endpoint `POST /assistant`)
1. Painel envia `prompt_id`, `profile` (perfil de análise), variáveis e o texto (possivelmente editado), com o JWT do Supabase Auth (a API valida). As instruções do perfil entram no system prompt; o RAG filtra pelas fontes do perfil.
2. API renderiza o prompt, recupera contexto no RAG (§7.5), chama o modelo escolhido (padrão Claude `claude-sonnet-5-5`) via camada multi-provedor (§7.3) com tools: `get_kpi`, `get_account_health`, `list_at_risk_accounts`, `revenue_at_risk`, `churn_drivers`, `query_analytics` (executa `api.run_readonly_query`), `search_knowledge`.
3. Executa as tools via RPC `api.*` com role read-only; devolve o resultado ao modelo até a resposta final.
4. Grava `app.ai_runs` e devolve a resposta em streaming (SSE) com as queries e os trechos usados.

### 7.1.1 Análise 360 (`POST /assistant/360`)
1. Recebe a pergunta e os perfis envolvidos (padrão: todos os habilitados que tenham KPIs relevantes).
2. Roda cada perfil **em paralelo**, cada um com suas instruções, tools e base de RAG, com limite de tokens por perfil.
3. Um passo de **síntese** junta as respostas: concordâncias, **discordâncias entre áreas** (onde está o insight), ações por dono.
4. Painel mostra a síntese no topo e cada lente em abas; tudo gravado em `app.ai_runs` (um run pai + um filho por perfil).
5. Custo controlado: modelo menor nas lentes e o principal na síntese (configurável em `app.llm_models`).

### 7.2 MCP server (`apps/api`, Python FastMCP montado em `/mcp`)
- **Tools:** as mesmas 5 do painel, chamando as funções `api.*` (conexão com role `analyst_ro`). Tools e endpoint `/assistant` compartilham o mesmo módulo Python.
- **Transporte:** streamable HTTP no Render (protegido por bearer token `MCP_TOKEN`) e stdio para uso local.
- **Prompts MCP:** lidos de `app.prompt_templates` em tempo real — o prompt editado no painel aparece no Claude Desktop/Code sem redeploy.
- **Resources:** `catalog://{schema}/{table}` com descrição e colunas, para a IA saber o que pode consultar.
- **Tool extra:** `search_knowledge(query, source_type?, profile?, filtros?)` — busca no RAG (§7.5).
- **Perfis no MCP:** cada perfil vira um prompt MCP (`perfil-<slug>`) e um resource `profile://<slug>`; as tools aceitam `profile` opcional; tool `analyze_360(question, profiles?)` chama a mesma lógica do endpoint 360.
- Instalação: remoto `claude mcp add --transport http ravenstack-churn https://<api>.onrender.com/mcp --header "Authorization: Bearer <token>"`; local `claude mcp add ravenstack-churn -- uv run ravenstack-mcp` (documentado no README).

### 7.3 Multi-LLM (pronto para outros provedores)

- Interface única em `churn_core.llm`: `LLMProvider.chat(messages, tools, stream) -> eventos` e `embed(texts)`. Adaptadores: `AnthropicProvider` (padrão), `OpenAIProvider`, `GeminiProvider`, `OpenAICompatibleProvider` (Groq, Mistral, DeepSeek, OpenRouter, Ollama local — qualquer endpoint compatível com a API da OpenAI, via `base_url`).
- Tools definidas **uma vez** (JSON Schema) e convertidas para o formato de cada provedor pelo adaptador; o loop de tool use é o mesmo para todos.
- Chaves por env var no Render, todas opcionais exceto a padrão: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `OPENAI_COMPATIBLE_BASE_URL` + `OPENAI_COMPATIBLE_API_KEY`. Provedor sem chave fica oculto no seletor.
- `GET /models` devolve os modelos de `app.llm_models` cujo provedor tem chave configurada.
- Futuro (fora do escopo do desafio): chave do próprio usuário (BYOK) guardada no Supabase Vault.
- Avaliação: o mesmo conjunto de 10 perguntas com resposta conhecida (números do gold) roda em cada provedor; resultado vira tabela no process log (diferencial: comparar modelos com evidência).

### 7.4 MCP para Claude e outras IAs

O MCP é um protocolo aberto; o servidor em `/mcp` (streamable HTTP) serve qualquer cliente compatível:

| Cliente | Como conecta |
|---|---|
| Claude Code | `claude mcp add --transport http ravenstack-churn <url>/mcp --header "Authorization: Bearer <token>"` |
| Claude Desktop / claude.ai | Conector personalizado com a URL remota |
| ChatGPT | Conector MCP personalizado (modo desenvolvedor) |
| OpenAI / Anthropic API | Ferramenta "remote MCP" apontando para a URL |
| Cursor, Windsurf, VS Code, Gemini CLI | Configuração JSON de servidor MCP remoto |

- Autenticação: bearer token agora; alguns clientes só aceitam OAuth ou servidor sem autenticação → plano B é OAuth via Supabase Auth (registrar como limitação se não der tempo).
- Testar cada cliente usado de verdade e guardar print no process log; não afirmar compatibilidade não testada.
- A tela `/conectar` do painel gera as instruções prontas para copiar.

### 7.5 RAG sobre as análises

**Objetivo:** a IA responder com o que **já sabemos** (hipóteses testadas, definições, achados de qualidade, feedback de clientes) e não só com números soltos.

**Regra de ouro:** números vêm **sempre das tools** (consulta ao gold, ao vivo); o RAG traz **contexto e explicação**. Se um trecho recuperado traz um número, a resposta confere com uma tool antes de citar.

**RAG por perfil:** cada chunk tem `profile_slugs` (vazio = comum a todos). A busca de um perfil usa conhecimento comum + o da sua área + as fontes listadas em `rag_sources`. Documentos anexados no painel (`app.knowledge_documents`, bucket `knowledge`) são indexados só para os perfis escolhidos.

**O que é indexado (`app.knowledge_chunks`):**

| Fonte | Conteúdo | Atualização |
|---|---|---|
| `hypothesis` | cada hipótese do `process-log/hypotheses.md` com veredito e números | quando o arquivo muda |
| `kpi_definition` | dicionário de KPIs da skill de negócio | idem |
| `catalog` | descrição de tabelas e colunas (`ops.catalog`) | a cada ingestão |
| `data_quality` | achados de `docs/data-quality.md` e `ops.dq_results` | a cada ingestão |
| `report` | seções do relatório do CEO | quando o relatório muda |
| `profile` | instruções de cada perfil e fichas das personas de cliente | quando um perfil/persona muda |
| `area_document` | documentos anexados por área (playbooks, políticas) | no upload |
| `churn_feedback` | `churn_events.feedback_text` — **só 4 textos distintos no dataset**: indexar uma vez como referência, sem peso analítico | a cada ingestão |

**Como funciona ("inteligente"):**
1. **Indexação** no pipeline (`ravenlake index`): divide por seção (markdown) ou por registro (feedback), calcula `content_hash` e só gera embedding do que mudou.
2. **Busca híbrida:** similaridade vetorial (`pgvector`, índice HNSW) + full-text (`tsvector`), combinadas por Reciprocal Rank Fusion, numa função SQL `api.search_knowledge(query_embedding, query_text, filters, k)`.
3. **Filtros por metadados** antes do ranking (segmento, período, tipo de fonte, veredito) — "só hipóteses confirmadas sobre Enterprise".
4. **Reescrita da pergunta** pelo próprio LLM antes da busca (ex.: "por que os grandes saem?" → "churn contas Enterprise MRR alto motivo").
5. **Citações:** cada trecho usado aparece no "Por quê" com link para a fonte.
6. ~~Análise semântica do feedback~~ — descartada: o dataset tem só 4 textos de feedback distintos. A H4 (motivo declarado ≠ causa) será testada com comportamento (uso, erros, tickets), não com texto. O RAG fica focado no conhecimento gerado pelas análises.

**Embeddings:** via `LLMProvider.embed`. A Anthropic não oferece modelo de embedding; opções: Voyage AI (recomendado pela Anthropic), OpenAI `text-embedding-3-small`, ou modelo local (`fastembed`) só no pipeline. Dimensão fixada na migration conforme a escolha (decisão aberta).

**Avaliação:** 10 perguntas com fonte esperada; medir se a fonte certa aparece no top 5 (recall@5) e registrar no process log.

## 8. Segurança

| Item | Regra |
|---|---|
| `service_role` key | Só no pipeline local (`.env`), nunca no painel nem no git |
| Painel | `anon` key + login Supabase Auth; lê só `api.*` |
| Role `analyst_ro` | `SELECT` em `api.*`, `statement_timeout` 5s, sem acesso a bronze/silver |
| `run_readonly_query` | Rejeita qualquer coisa que não seja um único `SELECT`; roda em transação read-only |
| Chave Anthropic | Env var secreta do serviço `apps/api` no Render (`sync: false` no Blueprint); MCP usa o cliente do próprio usuário (Claude Desktop/Code) |
| MCP remoto | Bearer token `MCP_TOKEN` (gerado pelo Render com `generateValue`); OAuth como plano B |
| Chaves de outros LLMs | Só env vars no Render (`sync: false`); nunca no banco, no front ou em logs; `/models` só informa se existe |
| RAG | Conteúdo indexado é só leitura para a IA; trechos são tratados como dados, nunca como instruções (proteção contra prompt injection via `feedback_text`) |
| Advisors | Rodar `get_advisors` (security + performance) ao fim de F2 e F5 |

## 9. Estrutura do monorepo

A raiz do monorepo é `submissions/tiago-canatelli/` (a PR só pode alterar essa pasta).

```
submissions/tiago-canatelli/
├── README.md                         ← template de submissão + setup
├── render.yaml                       ← Blueprint do Render (todos os serviços)
├── .claude/skills/                   ← skills do projeto
├── apps/
│   ├── dashboard/                    ← React (Vite) → Render static site
│   └── api/                          ← FastAPI: /assistant + /mcp + /health → Render web service
├── packages/
│   ├── ravenlake/                    ← pipeline de ingestão (CLI) → Render cron job
│   └── churn_core/                   ← cliente do banco, tools, prompts, `llm/`, `rag/`, `profiles/` (8 perfis de fábrica em .md)
├── supabase/
│   ├── migrations/                   ← bronze, ops, silver, gold, api, app, roles
│   └── seed/prompts.sql
├── analysis/                         ← SQL/notebooks das hipóteses
├── model/                            ← treino e avaliação do score de risco
├── report/                           ← relatório do CEO (md + pdf)
├── process-log/                      ← journal, hipóteses, erros da IA, decisões, screenshots, chat exports
└── docs/                             ← planos, arquitetura, dicionário, qualidade
```

- Python: workspace `uv` na raiz (`pyproject.toml` com `[tool.uv.workspace] members = ["apps/api", "packages/*"]`), um `uv.lock` só.
- Node: só `apps/dashboard` (npm).
- O `.gitignore` do repositório ignora `submissions/` e `datasets/` → commitar com `git add -f submissions/tiago-canatelli`; CSVs ficam fora do git.

## 10. Deploy no Render

Blueprint em `submissions/tiago-canatelli/render.yaml`, conectado ao fork no GitHub, branch `submission/tiago-canatelli`. Como o arquivo não fica na raiz do repositório, o caminho do Blueprint é informado ao criar o Blueprint no Render; cada serviço usa `rootDir` e `buildFilter` para só redeployar quando a própria pasta muda.

| Serviço | Tipo Render | `rootDir` | Build / start | Env vars |
|---|---|---|---|---|
| `ravenstack-dashboard` | static site | `apps/dashboard` | `npm ci && npm run build` → publica `dist`; rewrite `/* → /index.html` | `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_URL` |
| `ravenstack-api` | web service (Python) | raiz do monorepo | `pip install uv && uv sync --frozen --package api` → `uv run uvicorn api.main:app --host 0.0.0.0 --port $PORT`; health check `/health` | `ANALYST_RO_DATABASE_URL`, `SUPABASE_URL` (JWKS para validar o JWT), `ANTHROPIC_API_KEY` (sync: false), `OPENAI_API_KEY`/`GOOGLE_API_KEY`/`OPENAI_COMPATIBLE_*`/`VOYAGE_API_KEY` (opcionais, sync: false), `MCP_TOKEN` (generateValue), `PYTHON_VERSION` |
| `ravenstack-ingest` | cron job (opcional) | raiz do monorepo | `uv run ravenlake ingest` (diário; checa versão no Kaggle MCP) | `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` |

- O banco continua no Supabase (`G4-Analysys`); o Render não hospeda Postgres.
- Conexão do Render ao Supabase via **pooler** (porta 6543, modo transaction) para não esgotar conexões.
- CORS da API liberado só para a URL do dashboard.
- Ordem de deploy: migrations aplicadas → API (`/health` verde) → dashboard → cron.
- Plano free do Render dorme após inatividade: a primeira chamada pode demorar ~1 min (registrar em Limitações).

## 11. Ordem de implementação

1. Migrations `bronze`, `ops`, `silver` + pipeline até silver + DQ → **M1**
2. Análise das hipóteses direto no silver (SQL/notebook) → **M2**
3. Views gold + `api` + catálogo
4. Painel: `/ingestao`, `/catalogo` → `/kpis`, `/risco` → `/assistente`, `/prompts`
5. `apps/api` (assistente + MCP, compartilham as funções `api.*`) → **M3**
5a. Perfis de análise de fábrica + endpoint 360 + painéis por área e por persona
5b. RAG: `pgvector`, `ravenlake index`, `api.search_knowledge`, tool `search_knowledge`
5c. Adaptadores multi-LLM + avaliação com 10 perguntas
5d. Deploy no Render (API → dashboard → cron)
6. Modelo de risco → `gold.risk_scores`
7. Relatório, README, PR → **M4**

## 12. Testes

Todos os testes rodam contra o **Supabase SaaS** (`G4-Analysys`): transação com rollback por padrão; testes que precisam de commit usam `run_id` de teste com limpeza automática (detalhes na skill `python-software-engineer` §11).

| O quê | Como |
|---|---|
| Pipeline | `pytest` com CSVs pequenos de fixture; teste de idempotência (rodar 2x = mesmas contagens) |
| KPIs | Para cada KPI do gold, um teste que recalcula em pandas a partir do CSV e compara |
| `api.run_readonly_query` | Testes negativos: `insert`, `;`, `drop`, acesso a `silver` → todos rejeitados |
| Painel | Smoke test manual no navegador + `tsc --noEmit` + lint |
| MCP | Chamar cada tool via MCP Inspector e registrar print no process log |

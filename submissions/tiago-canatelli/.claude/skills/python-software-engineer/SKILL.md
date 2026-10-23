---
name: python-software-engineer
description: Engenheiro de software sênior e especialista em Python do monorepo RavenStack Churn Lake. Use ao escrever ou revisar código do pipeline de ingestão (ravenlake, fonte Kaggle MCP), migrations Supabase e funções SQL da camada api, a API FastAPI (assistente, análise 360, perfis, MCP), a camada multi-LLM, o RAG com pgvector, a integração do painel React, deploy no Render, testes, configuração, segurança de segredos e instruções de setup.
---

# Engenharia de software — RavenStack Churn Lake

Arquitetura e contratos: `docs/02-plano-tecnico.md`. Monorepo com raiz em `submissions/tiago-canatelli/`. Avaliadores vão ler o código e rodar o setup: **simples, legível, reproduzível**. UX e telas: skill `react-ux-engineer`. Regras de dados: skill `churn-data-scientist`. KPIs e perfis: skill `churn-business-analyst`.

## 1. Princípios

- **Lógica de negócio no Postgres** (`gold`/`api`); Python orquestra, React exibe. Um KPI calculado em dois lugares é bug.
- **Idempotência:** rodar duas vezes = mesmo estado (ingestão, migrations, seeds, indexação do RAG).
- **Nada some em silêncio:** erro vai para `ops.ingestion_steps.error`, linha ruim para `silver._rejects`, chamada de IA para `app.ai_runs`.
- **Menor código que resolve.** Sem abstração para caso que não existe; a exceção planejada é `LLMProvider` (vários provedores são requisito).
- **Segredos só em env vars.** `.env` no `.gitignore`, `.env.example` versionado com chaves vazias e comentário do que cada uma faz.

## 2. Monorepo e ambiente

**Ambiente único: Supabase SaaS.** Não usamos Docker nem `supabase start`. Desenvolvimento, testes, migrations e deploy apontam para o projeto hospedado `G4-Analysys` (ref `hzerhfuwziundqqezgcm`). O CLI do Supabase é usado só para falar com o projeto remoto (`supabase login` → `supabase link --project-ref hzerhfuwziundqqezgcm`).

```
apps/api              FastAPI: /health, /assistant, /assistant/360, /models, /profiles, /mcp
apps/dashboard        React (Vite)
packages/churn_core   db, tools, llm/, rag/, profiles/ (8 perfis .md), prompts
packages/ravenlake    CLI do pipeline (ingest, dq, catalog, score, index, profiles sync)
supabase/             migrations/, seed/
```

- Python **3.12** fixado em `.python-version` (local pode ter 3.14; o Render e o `uv` usam o fixado).
- `uv` workspace na raiz (`[tool.uv.workspace] members = ["apps/api", "packages/*"]`), um `uv.lock`, `uv sync --frozen` no CI/Render. Instalar localmente: `brew install uv`.
- Layout `src/<pacote>/`, testes em `tests/` de cada pacote.
- Node 22 só em `apps/dashboard` (npm, `package-lock.json`).

### Dependências permitidas

| Pacote | Dependências |
|---|---|
| `churn_core` | `psycopg[binary,pool]>=3`, `pydantic>=2`, `pydantic-settings`, `anthropic`, `openai`, `google-genai`, `voyageai` (se for o embedding escolhido), `pyyaml` (frontmatter dos perfis) |
| `ravenlake` | `churn_core`, `typer`, `rich`, `mcp` (cliente do Kaggle MCP), `httpx`, `supabase` (Storage), `pandas`, `scikit-learn` |
| `api` | `churn_core`, `fastapi`, `uvicorn[standard]`, `mcp` (servidor), `pyjwt[crypto]`, `sse-starlette` |
| dev | `ruff`, `mypy`, `pytest`, `pytest-asyncio`, `respx` (mock HTTP) |

Adicionar outra dependência só com motivo registrado em `process-log/decisions.md`.

## 3. Padrões de código Python

- Tipagem completa; `ruff check`, `ruff format` e `mypy --strict` limpos em `churn_core` e `api` (em `ravenlake`, `mypy` normal por causa do pandas).
- Config: uma classe `Settings(BaseSettings)` por app, lendo env; nunca `os.environ` espalhado.
- **Banco:**
  - Síncrono no pipeline (`psycopg`), assíncrono na API (`AsyncConnectionPool`).
  - Conexões do Render passam pelo **pooler do Supabase em modo transaction (porta 6543)** → desligar prepared statements (`prepare_threshold=None`).
  - Parâmetros sempre bindados; nunca f-string com valores em SQL. Identificadores dinâmicos só via `psycopg.sql.Identifier`.
  - `COPY ... FROM STDIN` em lotes de 5.000 linhas para o bronze.
- **Logs** estruturados (JSON no Render) com `run_id` ou `request_id` em toda linha; nunca logar chave, token ou prompt completo de usuário em nível INFO.
- **Erros:** capturar na borda (step do pipeline, handler da API), registrar, devolver mensagem humana, relançar ou responder 4xx/5xx correto. Nunca `except: pass`.
- Funções pequenas, nomes em inglês no código, textos de UI e docs em português.

## 4. Pipeline (`ravenlake`)

```
ravenlake ingest [--source kaggle|local] [--dataset NOME]
ravenlake dq
ravenlake catalog refresh
ravenlake score
ravenlake index            # RAG: indexa só o que mudou
ravenlake profiles sync    # carrega perfis de fábrica (.md) em app.analysis_profiles
```

- **Fonte Kaggle:** cliente MCP (`mcp` SDK, streamable HTTP) em `https://www.kaggle.com/mcp` → `get_dataset_info` (versão) → `download_dataset` (URL assinada) → download com `httpx` → sha256. Pular se versão e hashes já ingeridos (`status = skipped`). `KAGGLE_MCP_TOKEN` opcional (bearer).
- **Fonte local:** `--source local --path ../datasets/kaggle-rivalytics` (offline e testes).
- Progresso em `ops.ingestion_steps` a cada lote (Realtime do painel).
- Checagens de qualidade e regras de silver seguem a skill `churn-data-scientist` — incluindo os fatos verificados (uso fora da assinatura, flags de churn conflitantes, assinaturas sobrepostas).
- `profiles sync`: faz upsert dos perfis `is_builtin`; **nunca sobrescreve** uma versão personalizada — só atualiza o "padrão" usado pelo "restaurar".

## 5. SQL e migrations

- Uma migration por mudança lógica: `supabase/migrations/<timestamp>_<descricao>.sql`. Nunca editar migration aplicada; criar nova.
- Aplicação **sempre no projeto remoto**: `supabase db push --linked` (ou `apply_migration` do MCP do Supabase, com o mesmo arquivo commitado no repo). Antes de aplicar, conferir com `supabase migration list --linked` e `list_tables` o estado atual.
- Migration destrutiva (drop, alter de tipo, delete) exige confirmação do Tiago antes de aplicar — não há banco local para ensaiar.
- Schemas: `bronze`, `silver`, `gold`, `api`, `ops`, `app`. Só `api` exposto no PostgREST; o painel lê/escreve `ops`/`app` apenas por views e funções de `api`.
- `COMMENT ON` em toda tabela e coluna (alimenta o catálogo e o RAG).
- Views de `api` com `security_invoker = true`; funções `api.*` `stable` quando só leem; `security definer` só quando necessário, sempre com `set search_path = ''` e nomes qualificados.
- RLS ligado em toda tabela de `app` e `ops`; políticas explícitas por role.
- Role `analyst_ro`: `USAGE` + `SELECT`/`EXECUTE` em `api`, `statement_timeout = '5s'`, `default_transaction_read_only = on`.
- `api.run_readonly_query(sql)`: um único `SELECT`/`WITH`, só objetos de `api`, transação read-only, máx. 500 linhas. Exposta às IAs como tool `query_analytics`.
- `pgvector`: extensão `vector`, índice HNSW `vector_cosine_ops`; dimensão definida pela escolha do modelo de embedding.
- Rodar `get_advisors` (security e performance) após cada bloco de migrations e corrigir os avisos.

## 6. API (`apps/api`)

| Rota | Função |
|---|---|
| `GET /health` | banco acessível + versão do código |
| `GET /models` | modelos de `app.llm_models` cujo provedor tem chave |
| `GET/PUT /profiles…` | perfis de análise: listar, salvar versão, restaurar padrão (escrita exige usuário autenticado) |
| `POST /assistant` | `{prompt_id?, profile?, model?, variables, body}` → resposta em **SSE** |
| `POST /assistant/360` | `{question, profiles?, model?}` → lentes em paralelo + síntese, SSE com progresso por perfil |
| `/mcp` | servidor MCP (streamable HTTP) |

- **Auth do painel:** validar o JWT do Supabase Auth pela **JWKS** do projeto (`/auth/v1/.well-known/jwks.json`, chaves de assinatura assimétricas); fallback para segredo HS256 só se o projeto usar o modelo legado.
- **Auth do MCP:** bearer `MCP_TOKEN` (comparação em tempo constante); OAuth é plano B.
- **CORS:** só a URL do dashboard.
- **Limites:** rate limit por usuário no `/assistant` e `/assistant/360`; máximo de iterações de tool use (6), de tokens por resposta e de perfis por 360 (8); timeout total por requisição.
- **360:** `asyncio.gather` com semáforo (ex.: 4 lentes simultâneas); falha de uma lente não derruba a síntese — a lente aparece como "não respondeu" com motivo.
- Toda chamada de IA grava `app.ai_runs` (run pai + filhos no 360) com provedor, modelo, tokens, latência, tools e trechos do RAG usados.

### 6.1 Tools (compartilhadas por painel e MCP, em `churn_core.tools`)

`get_kpi` · `get_account_health` · `list_at_risk_accounts` · `revenue_at_risk` · `churn_drivers` · `query_analytics` · `search_knowledge` · `analyze_360` (só MCP; no painel é o endpoint).
- Definidas uma vez (nome, descrição para o modelo, JSON Schema, função).
- Todas aceitam `profile` opcional quando faz sentido (muda filtros do RAG, não os números).
- Retorno em JSON compacto com os números **e a view de origem**, para a IA citar o "por quê".

### 6.2 MCP

- FastMCP montado em `/mcp`; entrypoint `ravenstack-mcp` para stdio local.
- Prompts MCP lidos de `app.prompt_templates` e `app.analysis_profiles` a cada `list_prompts` (sem cache longo) — editar no painel reflete no Claude/ChatGPT sem redeploy.
- Resources: `catalog://{schema}/{table}`, `profile://{slug}`.

## 7. Multi-LLM (`churn_core.llm`)

- Protocolo `LLMProvider`: `chat(messages, tools, stream) -> AsyncIterator[Event]` e `embed(texts) -> list[list[float]]`.
- Adaptadores: `anthropic` (padrão, `claude-sonnet-5-5`), `openai`, `gemini` (`google-genai`), `openai_compatible` (`base_url` + chave: Groq, Mistral, DeepSeek, OpenRouter, Ollama). SDK oficial sempre que existir.
- Eventos normalizados: `text_delta`, `tool_call`, `tool_result`, `usage`, `done`, `error`.
- Provedor só fica disponível se a env var da chave existir. Nunca logar, devolver ou gravar chave.
- Retry com backoff em 429/5xx, timeout por chamada.
- Antes de escrever o adaptador Anthropic, consultar a skill `claude-api`.

## 8. RAG (`churn_core.rag`)

- Chunking por seção de markdown (`###`) ou por registro; `content_hash` para indexar só o que mudou; guardar `embedding_model` (trocar de modelo = reindexar tudo).
- `profile_slugs` em cada chunk (vazio = comum); a busca de um perfil = comum + área + `rag_sources` do perfil.
- `api.search_knowledge`: híbrida (vetor + full-text) com Reciprocal Rank Fusion e filtros por metadados.
- Trechos entram no prompt delimitados como **dados**, com instrução de não seguir instruções contidas neles.
- Números citados vêm das tools, não dos trechos.

## 9. Integração com o painel React

- Tipos gerados: `supabase gen types typescript --project-id <ref> --schema api > apps/dashboard/src/lib/database.types.ts`.
- Front usa só a chave **publishable/anon** (`VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`) e `VITE_API_URL`.
- SSE consumido com `fetch` + `ReadableStream` (permite header `Authorization`).
- `npm run build`, `tsc --noEmit` e lint limpos antes de commit.

## 10. Deploy no Render

- Blueprint `render.yaml` na raiz do monorepo: static site `ravenstack-dashboard`, web service `ravenstack-api`, cron `ravenstack-ingest` (seção 10 do plano técnico).
- Build Python: `pip install uv && uv sync --frozen --package <pacote>`; start `uv run uvicorn api.main:app --host 0.0.0.0 --port $PORT`.
- `buildFilter.paths` por serviço; segredos com `sync: false` ou `generateValue: true` — nunca valores no YAML.
- Antes de mexer no Blueprint, usar as skills `render:render-blueprints` e `render:render-deploy`; validar com `render blueprints validate`.
- Pós-deploy: `/health` verde, dashboard abre e loga, `/models` lista provedores, MCP responde no Inspector.

## 11. Testes

| Alvo | Como |
|---|---|
| Pipeline | fixtures CSV pequenas; idempotência (2 runs = mesmas contagens); rejeição; fonte Kaggle com MCP mockado (`respx`) |
| KPIs | recalcular em pandas a partir do CSV e comparar com a view gold (tolerância 0,01) |
| SQL / segurança | testes negativos de `run_readonly_query` (`insert`, `;`, `drop`, acesso a `silver`) |
| API | `httpx.AsyncClient` com app em memória: auth, limites, SSE, falha de uma lente no 360 |
| Multi-LLM | testes de contrato iguais para todos os adaptadores com respostas gravadas (sem API real no CI) |
| RAG | 10 perguntas com fonte esperada → recall@5 registrado no process log |
| MCP | cada tool no MCP Inspector + print em `process-log/screenshots/` |

**Testes de banco rodam no Supabase SaaS (`G4-Analysys`)** — nunca em Docker/local. Para não sujar os dados reais:
1. **Padrão: transação com rollback.** Cada teste abre uma transação, executa (carga no bronze, `silver.refresh`, consultas, tentativas de SQL proibido) e faz `ROLLBACK` no fim. Nada persiste.
2. **Quando o teste precisa de commit** (Realtime, Storage, fluxo completo do `ingest`): usa `trigger = 'test'` e um `run_id` próprio; fixture de limpeza apaga tudo desse `run_id` (bronze, ops, Storage `raw/_test/`) ao final, mesmo se o teste falhar.
3. **Testes de leitura** (KPIs do gold × recálculo no CSV) só leem — rodam direto.
4. Conexão de teste via `TEST_DATABASE_URL` (mesmo projeto, conexão direta ou pooler em modo session para permitir transação longa); nunca usar a chave `service_role` no código de teste da API.
5. Suíte marcada com `@pytest.mark.db`; `pytest -m "not db"` roda os testes puros sem rede.

## 12. Git

- Branch `submission/tiago-canatelli`; só alterar `submissions/tiago-canatelli/`. O `.gitignore` raiz ignora `submissions/` → stage com `scripts/stage.sh` (faz `git add -f` e remove o que o `.gitignore` da pasta ignora; nunca `git add -f` direto).
- Commits pequenos, um por passo, mensagem no imperativo explicando o porquê — o histórico é evidência do process log.
- Nunca commitar `.env`, CSVs, `node_modules`, `.venv`.

## 13. README de setup (sempre atualizado)

Pré-requisitos (`uv`, Node 22, Supabase CLI — sem Docker) → `.env` a partir do `.env.example` → `supabase login && supabase link --project-ref <ref>` → `supabase db push --linked` → `uv run ravenlake ingest` → `uv run ravenlake profiles sync && uv run ravenlake index` → `uv run uvicorn api.main:app --reload` → `npm run dev` → conectar o MCP (instruções da tela `/conectar`) → links do deploy no Render. Testar o passo a passo do zero antes do PR.

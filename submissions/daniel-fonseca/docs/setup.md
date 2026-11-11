# Setup

Três níveis de teste, do mais rápido ao mais completo. Nenhum segredo neste arquivo: as chaves ficam no `.env` (ignorado pelo git) e nas credenciais do n8n.

| Nível | O que testa | O que precisa | Tempo |
|---|---|---|---|
| 1. Ver funcionando | app e vídeo | só o navegador | minutos |
| 2. Refazer a análise | números do diagnóstico, do classificador e do ROI | Python 3 | ~15 min |
| 3. Subir a stack inteira | banco, fluxos n8n e app com as suas contas | Supabase (free), chave da OpenAI, n8n e Node 20+ | ~1 h |

## 1. Ver funcionando
- App: https://triagem-case-ai-master-case-g4.vercel.app
- Vídeo (não listado): https://youtu.be/pLQ0Yh6tb64

## 2. Refazer a análise
Os datasets do Kaggle (CC0) baixam sem login.

```bash
bash scripts/download_data.sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python solution/analysis/00_data_profile.py
```

Os scripts `solution/analysis/00` a `12` geram os JSON de `solution/analysis/output/`, que já estão versionados para comparação. Os que avaliam o LLM (`04_zero_shot_eval.py` e `07_rag_llm_eval.py`) pedem `OPENAI_API_KEY` no `.env`. Os que usam embeddings leem `data/embeddings/ds2_te3s_1536.npy`, gerado por `scripts/embed_ds2.py` (~US$ 0,04).

## 3. Subir a stack inteira

> O roteiro segue a ordem usada no projeto original. O `scripts/setup_supabase.py` foi escrito para um projeto novo e não foi rodado do zero; cada etapa que ele chama já foi usada no projeto do autor.

### 3.1 Contas
- **Supabase:** projeto novo no plano free (o banco do case ocupa ~150 MB dos 500 MB). Em Connect, copie a URI do **Session pooler**; em Settings → API, a URL do projeto e a `service_role` key.
- **OpenAI:** uma chave de API. Custo da montagem: ~US$ 0,05 de embeddings; cada triagem custa de US$ 0,0006 a 0,0014.
- **n8n:** n8n Cloud ou instalação própria, numa versão recente (os fluxos usam o nó OpenAI 2.3 e o Switch 3.4).

### 3.2 Banco (Supabase)
1. Copie `.env.example` para `.env` e preencha `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_DB_URL` e `OPENAI_API_KEY`.
   - `SUPABASE_DB_URL` é a URI do **Session pooler** (usuário `postgres.<ref>`, host `aws-*-<regiao>.pooler.supabase.com`, porta 5432). A conexão direta (`db.<ref>.supabase.co`) só tem IPv6. A senha entra sem os colchetes do placeholder.
2. Rode o script, que baixa os dados se faltarem, cria o schema e carrega tudo:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/setup_supabase.py
```

O schema completo está em [`solution/supabase/setup.sql`](../solution/supabase/setup.sql): as 8 migrations de [`solution/supabase/migrations/`](../solution/supabase/migrations/), em ordem, num arquivo só. Para aplicar pelo navegador, cole o arquivo no **SQL Editor** do Supabase, rode, e depois chame o script com `--sem-sql`.

| Etapa do script | O que carrega |
|---|---|
| banco | `setup.sql`: tabelas, pgvector, funções do RAG (`classify_ticket`, `match_resolutions_json`), console e monitor de uso |
| dados | `ds1_tickets` (8.469) e `ds2_tickets` (47.837, holdout 80/20 com seed 42) |
| embeddings | `ds2_embeddings` em `halfvec` 512 com índice HNSW |
| playbook | 14 soluções validadas em 6 categorias (`solution/supabase/seed/playbook.json`) |
| análises | tabelas `analysis_*` que o Painel lê |

### 3.3 Fluxos (n8n)
1. Crie 3 credenciais:

| Tipo no n8n | Conteúdo | Usada nos fluxos |
|---|---|---|
| Supabase API | URL do projeto e `service_role` key | 1, 2, 3 e 4 |
| OpenAI API | a chave da OpenAI | 1 |
| Header Auth | Name `X-Webhook-Secret`; Value = o mesmo `N8N_WEBHOOK_SECRET` do app (gere com `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`) | 1 e 2 (webhooks) |

2. Importe os 4 arquivos de [`solution/n8n/`](../solution/n8n/) (menu do workflow → **Import from File**):

| Arquivo | Fluxo | Gatilho |
|---|---|---|
| `01_triagem.json` | Triagem: RAG + 3 caminhos | webhook `POST /webhook/g4-support/triage` |
| `02_aprovacao_hitl.json` | Aprovação na fila (HITL) | webhook `POST /webhook/g4-support/hitl-decision` |
| `03_heartbeat.json` | Keep-alive do Supabase free | diário |
| `04_monitor_uso.json` | Monitor de uso (só alerta) | a cada 15 min |

3. Em cada nó com credencial, selecione a sua (o JSON traz as do projeto original, que não existem na sua instância).
4. Troque a URL do Supabase do projeto original pela do seu em 3 nós HTTP Request:
   - fluxo 1: **Classificar por casos parecidos (RAG)** e **Buscar soluções validadas**;
   - fluxo 4: **Calcular sinais de uso**.
5. Publique os fluxos 1 e 2; o 3 e o 4 são opcionais. O nó **Avisar no Slack** fica desativado; para usar, selecione uma credencial do Slack e o canal (ADR-0007).

Detalhes nó a nó em [`docs/n8n-flows.md`](n8n-flows.md).

### 3.4 App (Next.js)
```bash
cd solution/app
npm ci
```

Crie `solution/app/.env.local` com:

| Variável | Valor |
|---|---|
| `SUPABASE_URL` | URL do projeto |
| `SUPABASE_SERVICE_ROLE_KEY` | `service_role` key (fica só no servidor) |
| `N8N_BASE_URL` | URL base do seu n8n, sem barra no fim |
| `N8N_WEBHOOK_SECRET` | o mesmo valor da credencial Header Auth |
| `IP_HASH_SALT` | texto aleatório (mesmo comando do segredo acima) |
| `FREE_TEXT_ENABLED` | `true` |

Os limites de uso têm padrões em `solution/app/lib/env.ts` e mudam pelas variáveis `RATE_*`.

```bash
npm run dev    # http://localhost:3000
npm test       # 5 testes do ROI
```

**Vercel:** importe o repositório, defina o *Root Directory* como `submissions/daniel-fonseca/solution/app` e cadastre as mesmas variáveis.

### 3.5 Dados de demonstração
Com o fluxo 1 publicado, `N8N_BASE_URL` e `N8N_WEBHOOK_SECRET` no `.env` da raiz da submissão:

```bash
.venv/bin/python scripts/reset_demo.py
```

O script repovoa a fila com 6 tickets em Revisão humana, 2 em Somente humano e 2 respostas automáticas (~US$ 0,01). Também dá para rodar junto com o banco: `scripts/setup_supabase.py --demo`.

### 3.6 Sem n8n
Painel e Como foi feito leem só o Supabase. Em Tickets, a triagem dos exemplos do holdout tem modo offline, que classifica direto no banco (`classify_holdout_ticket`) quando o n8n não responde; pelo código, isso vale com `N8N_BASE_URL` apontando para um endereço fora do ar (ex.: `http://localhost:5678`). O texto livre e a fila de revisão precisam do n8n.

## 4. Ambiente de desenvolvimento com agentes de IA

### Claude Code
Abra o Claude Code dentro de `submissions/daniel-fonseca/`. O `.mcp.json` registra:
- `supabase-g4`: MCP hospedado do Supabase (OAuth). Acrescente `project_ref=<ref>` na URL para restringir o escopo a um único projeto.
- `vercel-g4`: MCP hospedado da Vercel (OAuth).

Na primeira vez: `/mcp` → autenticar cada um com a conta dedicada ao case.

**n8n (`n8n-g4`):** o MCP de instância do n8n exige um token de acesso, então ele fica fora do `.mcp.json` versionado. Gere o token no n8n (Settings → MCP / Instance-level MCP) e registre em escopo *local* (fica só na sua máquina, em `~/.claude.json`), rodando no terminal dentro desta pasta:

```bash
claude mcp add --scope local --transport http n8n-g4 "$N8N_BASE_URL/mcp-server/http" --header "Authorization: Bearer <TOKEN>"
```

A URL da VPS fica em `N8N_BASE_URL` (`.env`), fora do repositório.

### Codex
O Codex lê `AGENTS.md` nativamente. Para os MCPs, adicionar no `~/.codex/config.toml` (ou no `.codex/config.toml` do projeto, se a versão instalada suportar configuração por projeto; confirme com `codex mcp --help`):

```toml
[mcp_servers.supabase-g4]
url = "https://mcp.supabase.com/mcp?project_ref=<ref>"

[mcp_servers.vercel-g4]
url = "https://mcp.vercel.com"

[mcp_servers.n8n-g4]
url = "<N8N_BASE_URL>/mcp-server/http"
bearer_token_env_var = "N8N_MCP_TOKEN"
```

e autenticar com `codex mcp login supabase-g4` / `codex mcp login vercel-g4`.

## 5. Notas sobre o `.env`
- Não use comentários na mesma linha do valor: alguns leitores incluem o comentário no valor.
- **Slack / WhatsApp (ADR-0007):** as credenciais ficam no n8n, nos nós finais do fluxo. O app não fala com Slack nem WhatsApp, por isso não há variáveis para eles.
- `N8N_MCP_TOKEN` é opcional e só serve para o Codex.

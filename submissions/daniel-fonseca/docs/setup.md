# Setup

> Rascunho — será completado à medida que cada componente for construído. Nenhum segredo neste arquivo.

## 1. Para quem só quer ver funcionando
- App: _URL da Vercel (pendente)_
- Vídeo: _link (pendente)_

## 2. Ambiente de desenvolvimento com agentes de IA

### Claude Code
Abra o Claude Code dentro de `submissions/daniel-fonseca/`. O `.mcp.json` registra:
- `supabase-g4` — MCP hospedado do Supabase (OAuth). Depois de criar o projeto, acrescentar `project_ref=<ref>` na URL para restringir o escopo a um único projeto.
- `vercel-g4` — MCP hospedado da Vercel (OAuth).

Na primeira vez: `/mcp` → autenticar cada um **com a conta dedicada ao case**.

**n8n (`n8n-g4`)** — o MCP de instância do n8n exige um token de acesso, então ele **não** fica no `.mcp.json` versionado. Gere o token no n8n (Settings → MCP / Instance-level MCP) e registre em escopo *local* (fica só na sua máquina, em `~/.claude.json`), rodando no terminal dentro desta pasta:

```bash
claude mcp add --scope local --transport http n8n-g4 "$N8N_BASE_URL/mcp-server/http" --header "Authorization: Bearer <TOKEN>"
```

A URL da VPS fica em `N8N_BASE_URL` (`.env`), não no repositório público.

### Codex
O Codex lê `AGENTS.md` nativamente. Para os MCPs, adicionar no `~/.codex/config.toml` (ou no `.codex/config.toml` do projeto, se a versão instalada suportar configuração por projeto — confirmar com `codex mcp --help`):

```toml
[mcp_servers.supabase-g4]
url = "https://mcp.supabase.com/mcp?project_ref=<ref>"

[mcp_servers.vercel-g4]
url = "https://mcp.vercel.com"

[mcp_servers.n8n-g4]
url = "<N8N_BASE_URL>/mcp-server/http"
bearer_token_env_var = "N8N_MCP_TOKEN"
```

e autenticar com `codex mcp login supabase-g4` / `codex mcp login vercel-g4` (nomes de chave conforme a versão do Codex — confirmar com `codex mcp --help`).

## 3. Dados
```bash
bash scripts/download_data.sh            # baixa DS1 e DS2 do Kaggle para data/raw/
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python solution/analysis/00_data_profile.py
```

## 4. Variáveis de ambiente
Copie `.env.example` para `.env` e preencha. Nunca commitar `.env`.

- `SUPABASE_DB_URL` precisa ser a URI do **Session pooler** (usuário `postgres.<ref>`, host `aws-*-<regiao>.pooler.supabase.com`, porta 5432). A conexão direta (`db.<ref>.supabase.co`) só tem IPv6 e não resolve na maioria das redes domésticas. A senha entra **sem** os colchetes do placeholder `[YOUR-PASSWORD]`.
- `N8N_BASE_URL` + `N8N_WEBHOOK_SECRET`: o app da Vercel chama webhooks públicos do n8n (triagem/RAG, aprovação HITL). Sem segredo, qualquer pessoa que descobrisse a URL dispararia o workflow e gastaria créditos da OpenAI. No n8n, o nó Webhook usa **Header Auth** (credencial com header `X-Webhook-Secret` = valor do `.env`); na Vercel, o mesmo valor vai como variável de ambiente do servidor.
- **Slack / WhatsApp (ADR-0007):** as credenciais (token/Webhook do Slack, WAHA/Evolution) ficam **nas credenciais do n8n**, nos nós finais do workflow. O app não fala com Slack nem WhatsApp, por isso não há variáveis para eles aqui.
- `N8N_MCP_TOKEN` é opcional: só serve para o Codex. O Claude Code registra o `n8n-g4` em escopo local (seção 2).

## 5. Setup de backup para o G4 (a construir)
Objetivo: alguém do G4 sobe a solução com o mínimo de passos, usando as próprias chaves.
- Supabase: `solution/supabase/migrations/` + script de seed.
- n8n: workflows exportados em `solution/n8n/*.json` (Import from file) + `docker-compose.yml` com n8n.
- Notificações (ADR-0007): nó Slack no n8n + caixa de mensagens no painel (funciona sem Slack). WhatsApp (WAHA/Evolution) é troca do nó final.

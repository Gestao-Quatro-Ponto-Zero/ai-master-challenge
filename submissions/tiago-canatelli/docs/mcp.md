# MCP — análise de churn em qualquer IA

Servidor MCP remoto (streamable HTTP) que roda junto com a API no Render:

- **URL:** `https://ravenstack-api.onrender.com/mcp`
- **Autenticação:** header `Authorization: Bearer <MCP_TOKEN>`. O token fica no `.env`, gerado pelo `scripts/render_deploy.py`.
- **Dados:** só leitura, sobre as views `api.*` do lake no Supabase. Qualquer SQL passa pelo `api.run_readonly_query`: um único SELECT, só no schema `api`, com timeout de 5 s e no máximo 500 linhas.

## O que o servidor oferece

| Tipo | Nome | Para quê |
|---|---|---|
| Tool | `get_kpi_overview` | Números-chave (painel do CEO) |
| Tool | `get_kpi(view)` | Qualquer view de KPI: `tenure_hazard`, `cohort`, `persona_summary`, `support_health`… |
| Tool | `list_at_risk_accounts(limit, persona)` | Fila do CS por MRR em risco, com drivers e jogada recomendada |
| Tool | `get_account_health(account_id)` | Visão 360 da conta |
| Tool | `query_analytics(sql)` | SELECT livre, só leitura, sobre `api.*` |
| Prompts | 10 perguntas prontas (`por-que-churn-subiu`, `quem-ligar`…) | Lidos de `app.prompt_templates`, os mesmos do painel |
| Prompts | 8 perfis (`perfil-executivo`, `perfil-cs`…) | A lente de cada área, lida de `app.analysis_profiles` |

**Testado em produção (2026-10-23):** com o cliente MCP oficial em Python, conferi `initialize`, a listagem de tools e prompts, e chamadas a `list_at_risk_accounts` e `query_analytics`. Sem o token, a resposta é 401.

## Como conectar

> Troque `<MCP_TOKEN>` pelo valor do `.env`.

### Claude Code
```bash
claude mcp add --transport http ravenstack-churn https://ravenstack-api.onrender.com/mcp \
  --header "Authorization: Bearer <MCP_TOKEN>"
```

### Claude Desktop (via `mcp-remote`)
```json
{
  "mcpServers": {
    "ravenstack-churn": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://ravenstack-api.onrender.com/mcp",
               "--header", "Authorization: Bearer <MCP_TOKEN>"]
    }
  }
}
```

### Claude API (MCP connector)
Em `client.beta.messages.create`, passe `mcp_servers=[{"type": "url", "url": ".../mcp", "name": "ravenstack-churn", "authorization_token": "<MCP_TOKEN>"}]`, mais `tools=[{"type": "mcp_toolset", "mcp_server_name": "ravenstack-churn"}]` e a beta `mcp-client-2025-11-20`.

### OpenAI (Responses API)
Use a ferramenta `{"type": "mcp", "server_label": "ravenstack-churn", "server_url": ".../mcp", "headers": {"Authorization": "Bearer <MCP_TOKEN>"}, "require_approval": "never"}`.

### Gemini CLI (`~/.gemini/settings.json`)
```json
{ "mcpServers": { "ravenstack-churn": {
    "httpUrl": "https://ravenstack-api.onrender.com/mcp",
    "headers": { "Authorization": "Bearer <MCP_TOKEN>" } } } }
```

### Cursor / VS Code (`mcp.json`)
```json
{ "mcpServers": { "ravenstack-churn": {
    "url": "https://ravenstack-api.onrender.com/mcp",
    "headers": { "Authorization": "Bearer <MCP_TOKEN>" } } } }
```

### Local (stdio, sem rede)
```bash
claude mcp add ravenstack-churn -- uv run --directory /caminho/para/submissions/tiago-canatelli ravenstack-mcp
```

> **Honestidade:** apenas o cliente Python foi testado contra produção. As configurações dos outros clientes seguem o formato padrão de MCP remoto de cada um e ainda **não foram testadas** nesta entrega. Clientes que exigem OAuth (por exemplo, conectores do ChatGPT na interface web) não funcionam com bearer token. Para eles, o próximo passo seria OAuth via Supabase Auth.

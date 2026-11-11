@AGENTS.md

## Específico do Claude Code

- Abra o Claude Code **nesta pasta** (`submissions/daniel-fonseca/`) para que `.mcp.json`, `CLAUDE.md` e `AGENTS.md` sejam carregados.
- MCPs do projeto: `supabase-g4` e `vercel-g4` (autenticar via `/mcp` na primeira vez, logando com a **conta nova**). Confirme a conta antes de qualquer escrita.
- n8n: servidor MCP `n8n-g4` (escopo local com token, ver `docs/setup.md`) — não o `n8n-local` global. Workflows criados por MCP também devem ser exportados em JSON para `solution/n8n/` — o repositório precisa reproduzir o que roda na VPS.
- A memória canônica do projeto está no repositório (`context/`, `docs/decisions/`, `process-log/`), não na memória local do Claude — assim o Codex enxerga a mesma coisa.

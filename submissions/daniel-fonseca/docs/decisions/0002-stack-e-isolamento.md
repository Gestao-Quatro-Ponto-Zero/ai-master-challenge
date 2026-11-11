# 0002 — Stack Supabase + Vercel + n8n e isolamento de contas/MCP

- **Status:** Aceita
- **Data:** 2026-11-09
- **Origem:** Daniel

## Contexto
O Diretor de Operações do challenge quer "ver algo rodando". O Daniel quer deploy real e também um setup fácil de backup para alguém do G4 testar.

## Decisão
- **Supabase (conta nova, plano free):** Postgres com dados dos dois datasets, pgvector para RAG, tabelas de fila HITL, notificações e auditoria.
- **Vercel (conta nova):** dashboard de diagnóstico + console operacional (triagem/HITL).
- **n8n (VPS do Daniel):** orquestração — classificação, RAG, decisão de nível de automação, HITL, notificações.
- **OpenAI API:** embeddings e geração (Daniel custeia os créditos).
- **WhatsApp via WAHA** para o nível "só humano"; alternativas documentadas (Slack webhook, Evolution API, caixa de notificações no próprio dashboard).
- **MCPs do projeto** em `.mcp.json` com nomes próprios (`supabase-g4`, `vercel-g4`), para não tocar os conectores pessoais (`supabase`, `vercel`) configurados globalmente.

## Consequências
- O agente precisa confirmar a conta (ex.: `get_auth_user` no Vercel, `list_projects` no Supabase) antes de qualquer escrita.
- Workflows criados via MCP no n8n devem ser exportados em JSON para `solution/n8n/` para serem reproduzíveis.

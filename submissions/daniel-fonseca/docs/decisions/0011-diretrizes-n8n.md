# 0011 — Diretrizes para os fluxos n8n

- **Status:** Aceita
- **Data:** 2026-11-09
- **Origem:** Daniel

## Decisão
1. **Fluxos simples, fáceis de manter por pessoas não técnicas:** preferir **nós nativos do n8n** (Webhook, Supabase/Postgres, OpenAI, If/Switch, Set/Edit Fields, Slack, Schedule). Nó de código só quando não houver alternativa nativa, e com comentário explicando o porquê.
2. **Rascunho antes de construir:** para cada fluxo, a IA apresenta antes o rascunho nó a nó (nome, tipo, o que faz, entradas e saídas) para validação do Daniel. Só depois constrói via MCP.
3. **Documentação como parte da entrega:** cada fluxo final é exportado em JSON para `solution/n8n/` e documentado em `docs/n8n-flows.md` (objetivo, diagrama, papel de cada nó, credenciais necessárias, como importar e testar).

## Consequências
- A lógica pesada (voto do RAG) fica numa **função SQL no Supabase**, chamada por um nó nativo. O fluxo no n8n continua legível.
- Nomes de nós descritivos em português (ex.: "Buscar casos parecidos"), com notas nos nós explicando a regra de negócio.

# 0013 — Fluxos n8n com nós nativos do Supabase (no lugar do nó Postgres)

- **Status:** Aceita (Daniel, 2026-11-10)
- **Data:** 2026-11-10
- **Origem:** Daniel (sugestão: credencial do próprio Supabase, mais simples) · IA (viabilidade, teste da API REST e ajustes)

## Contexto
A primeira construção usava o nó Postgres, com a credencial do *Session pooler* (host, usuário e senha do banco). O Daniel perguntou se dava para trocar pelos nós nativos do Supabase, com uma credencial só (URL do projeto + service role key).

## Decisão
1. **Leitura e escrita de tabelas** (`triage_runs`, `hitl_queue`, `notifications`, `validated_resolutions`, `heartbeat`): **nó Supabase** (`create` / `update` / `getAll`), sem SQL dentro do nó.
2. **Funções do RAG** (`classify_ticket`, `match_resolutions_json`): o nó Supabase não chama funções, então elas são chamadas pelo **HTTP Request com a credencial Supabase** na API REST (`POST /rest/v1/rpc/<função>`). Teste antes da troca: mesma resposta da conexão direta, ~250 ms, e `anon` bloqueado (401).
3. **Wrapper `match_resolutions_json`** (migration `20261110000004_rest_wrappers.sql`): o HTTP Request do n8n transforma uma lista JSON em vários itens e, se ela vier vazia, o fluxo para. O wrapper devolve sempre um objeto `{ resolutions: [...] }`.
4. **Colunas JSON** (`votes`, `similar_cases`, `checks`, `payload`): gravadas com *auto-map* a partir de um Set que monta a linha exata. Testado: chegam como JSON de verdade.
5. A lógica que estava em SQL (`CASE`, `nullif`, `join`) foi para expressões nos nós. A busca do item pendente no fluxo 2 virou duas leituras.

## Consequências
- Credenciais do case no n8n: `G4 - Supabase`, `G4 - OpenAI`, `G4 - Segredo do webhookk`. A credencial Postgres deixa de existir.
- **Risco operacional registrado:** o n8n auto-atribui a credencial do mesmo tipo que já existe na instância (`Supabase – padaria-bi`, `Waha VPS`). Toda criação de workflow por MCP precisa ser seguida de `setNodeCredential` com os IDs G4 e de conferência. Isso foi feito e testado em 10/11.
- O `service_role` ignora o RLS, igual à conexão Postgres anterior. O nível de acesso é o mesmo, com uma credencial a menos para manter.

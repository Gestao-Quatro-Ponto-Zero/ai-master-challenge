# STATE — handoff entre sessões

> Atualize ao final de cada sessão. Qualquer agente (Claude Code, Codex…) deve conseguir continuar o trabalho só com este arquivo + AGENTS.md.

**Última atualização:** 2026-11-09 · Sessão 02 · Claude Code (Opus 5.5)

## Fase atual
**App Vercel: sessão base pronta** (plano aprovado em 10/11; ver `docs/prd/01-prd.md` e a ADR-0014). Próximo: frentes A (Painel + Como foi feito) e B (Console + APIs) em sessões paralelas a partir do commit da base; deploy quando o Daniel liberar o acesso do MCP `vercel-g4` ao time `case-g4`.

## Timebox (decisão do Daniel)
No máximo **dois turnos noturnos**: hoje (09/11) e amanhã (10/11), incluindo vídeo e PR. Se terminar hoje, melhor.

| Turno | Entregas |
|---|---|
| **1 — 09/11 noite** | Contas Supabase/Vercel + MCPs autenticados · schema + carga DS1/DS2 no Supabase · diagnóstico (agregados + testes + modelo de custo) · embeddings do DS2 + avaliação do classificador (baseline, kNN, zero-shot em amostra) → limiares dos 3 níveis |
| **2 — 10/11 noite** | Workflows n8n (triagem/RAG, HITL, Slack + caixa, heartbeat) · app Vercel (dashboard + console validador) + deploy + cron · README final, limpeza, vídeo, PR |

## Feito
- Fork clonado; branch `submission/daniel-fonseca`; remote `upstream` → `Gestao-Quatro-Ponto-Zero/ai-master-challenge`.
- Datasets perfilados (`00_data_profile.py`) e testados (`01_signal_tests.py`) → [`data-findings.md`](data-findings.md). **DS1 é sintético e sem sinal estatístico.**
- Estrutura de documentação e memória (AGENTS.md, CLAUDE.md, ADRs 0001–0008, process log, judgment log, docs).
- `.mcp.json` com `supabase-g4` e `vercel-g4`; `n8n-g4` em escopo local (token), conectado.
- Decisões do Daniel: notificações Slack + caixa no painel (0007), console como validador (0008), keep-alive via Vercel Cron + n8n (0006), timebox de 2 turnos.

## Status das integrações (09/11)
- ✔ Contas Supabase e Vercel criadas pelo Daniel.
- ✔ `n8n-g4` conectado (escopo local, testado com `claude mcp list` na pasta).
- ✔ `supabase-g4` (project ref `awiphrbtvgapuuebiouw`, região `sa-east-1`) e `vercel-g4` conectados (`claude mcp list` na pasta, 09/11).
- ✔ Banco carregado e verificado por conexão direta: `ds1_tickets` 8.469 · `ds2_tickets` 47.837 (9.567 teste / 38.270 treino) · RLS ligado (anon via REST recebe `[]`, service role lê) · Postgres 17 · banco com 33 MB · pgvector 0.8.2 disponível, ainda não instalado.
- ⚠ A migration foi aplicada fora do `apply_migration` → não aparece em `supabase_migrations.schema_migrations`. O arquivo SQL versionado é a fonte; as próximas devem ir pelo MCP.
- ✔ `.env` validado: URL, chaves anon/service e DB URL batem com o ref; `N8N_BASE_URL` preenchido; n8n `/healthz` 200.
- ✔ `OPENAI_API_KEY` corrigida pelo Daniel e testada (`/models` 200; embedding `text-embedding-3-small` com 1536 dims OK).

## Próximos passos (Turno 1)
1. ✔ Cortes do diagnóstico (`02_diagnostic_cuts.py` → `output/diagnostic_cuts.csv`); ADR-0003 reescrita com o direcionamento do Daniel.
2. ✔ Premissas de custo com fonte: `docs/premissas-de-custo.md` + `solution/analysis/cost_premises.json`. ADR-0003 aceita.
3. ✔ Embeddings do DS2 (`scripts/embed_ds2.py` → `data/embeddings/ds2_te3s_1536.npy`, local, 2,19M tokens ≈ US$ 0,04).
4. ✔ Avaliação (`03`–`08_*.py` → `output/*.json`). **Daniel escolheu o RAG como classificador único** (ADR-0010): 512 dims, k=50, peso sim¹⁶, acurácia 82,8%; níveis 31/28/41% (nível 1 com 98,8% de precisão). LLM só redige. RAG + LLM levou o LLM de 43% para 81%, mas não superou o voto.
5. ✔ (Sessão 02) Migration `20261109000002_rag.sql` via `apply_migration` (aparece em `list_migrations` como `rag`): pgvector no schema `extensions`, `ds2_embeddings` (halfvec 512, HNSW cosseno, RLS), função `classify_ticket` (50 vizinhos só do treino, peso sim¹⁶, `hnsw.iterative_scan`), execução só para `service_role`.
   - Carga: `scripts/load_embeddings.py` (COPY binário, 47.837 vetores em 5 s, índice em 33 s).
   - Validação: `solution/analysis/09_db_rag_validation.py` → 500 tickets de teste: banco 80,4% × cálculo exato local 80,2% (99,8% de concordância de categoria; 99,6% de nível). Amostra abaixo dos 82,8% do holdout inteiro por variação amostral (±1,8 p.p.). Latência p50 64 ms.
   - `get_advisors`: performance limpo; security só INFO "RLS sem policy" (intencional: acesso só pelo backend). Banco: 150 MB de 500.
6. ✔ (Sessão 02) Rascunhos dos 3 fluxos n8n nó a nó + schema proposto das tabelas de apoio em `docs/n8n-flows.md`. **Nada construído no n8n. Aguardando validação do Daniel.**
7. ✔ (Sessão 02) Daniel aprovou o rascunho v2. Migration `20261110000003_ops.sql` aplicada via MCP (`ops`): `validated_resolutions`, `triage_runs`, `hitl_queue`, `notifications`, `heartbeat` + `match_resolutions`; advisors só INFO. Playbook-semente (14 soluções, 6 categorias) em `solution/supabase/seed/playbook.json`, carregado por `scripts/seed_playbook.py`, **aguardando revisão do Daniel**.
8. ✔ (Sessão 02) Fluxos criados no n8n via MCP, **todos inativos**: Triagem `ML8nNXH22pSaDF09` (33 nós), Aprovação HITL `Mm1hZMJvQMQu1uQJ` (15), Heartbeat `RtQAhCEnwxEDQrd4` (6, timezone São Paulo). Fonte SDK versionada em `solution/n8n/*.sdk.ts`. Status e diferenças em relação ao rascunho em `docs/n8n-flows.md`.
   - (Resolvido em 10/11: versões arquivadas; as novas usam credenciais G4 por ID.)
9. ✔ (10/11) Daniel criou as credenciais (`G4 - Supabase`, `G4 - OpenAI`, `G4 - Segredo do webhookk`), validou o playbook e pediu nós nativos do Supabase (ADR-0013). Fluxos recriados: Triagem `msFVCvUdsmRq49pv`, HITL `FWb7G9cGmMC69Q6D`, Heartbeat `LpQK8XX5AZJrUCy8`; as versões Postgres foram arquivadas. Migration `…0004_rest_wrappers` (`match_resolutions_json` + playbook marcado como aprovado).
   - O n8n auto-atribuiu `Supabase – padaria-bi` e `Waha VPS` na criação. Tudo foi trocado pelos IDs G4 **antes** de qualquer execução; os dados do teste estão só no projeto G4.
   - **Teste ponta a ponta ✔** (tabela em `docs/n8n-flows.md`): nível 1, nível 2 e nível 3 (×2); HITL editar/rejeitar/409/400; aprendizado (solução #15 volta em 1º lugar); heartbeat no caminho de falha. Bug encontrado e corrigido: saída `json_schema` do OpenAI v2.3 vem como objeto.
10. ✔ (10/11) Daniel autorizou; fluxos 1 e 2 publicados. Webhook de produção testado: sem header ou com header errado 403; header certo 200 (triagem #6, nível 1, 3,5 s); texto vazio 400; HITL sem header 403; item já decidido 409.
   - Próximo: exportar os JSON para `solution/n8n/` (o Daniel pediu para fazer depois do app).
11a. (10/11) **PRD do app Vercel em construção colaborativa**: questionário da rodada 1 em `docs/prd/00-questionario.md` (≈ 90 perguntas com sugestão da IA, ★ nas que mudam escopo). ✔ Daniel respondeu → **PRD v1 em `docs/prd/01-prd.md`** + ADR-0014 (Proposta). Rodada 2 resolvida (10/11): **sem login**, com limites de uso e rotina de monitoramento que só alerta (PRD §8.1); Condução objetiva + ideação/estrutura do projeto no Claude Code; R2–R7 aceitas. **Construção NÃO iniciada (instrução do Daniel).** Pendências R8–R11 (canal e frequência dos alertas, limites, duração).
11. ✔ (10/11) Base do app:
   - commit `b893d65` (sessões 01–02) e push no fork;
   - migration `…0005_app` (`usage_events`, `usage_alert`, colunas de custo/tempo em `triage_runs`, tabelas `analysis_*`, views `v_ds1_status` e `v_ops_summary`);
   - `11_app_summary.py` + `load_analysis.py`;
   - fluxo 1 gravando tokens, custo e tempos (republicado e testado nos 3 caminhos);
   - `reset_demo.py` (fila com 6, caixa com 2, 2 automáticas);
   - `solution/app` com Next 16.4.6 (Cache Components), tokens Órbita, shell (top bar + barra mobile + toggles na URL + tema escuro), camada de dados no servidor, limites de uso, `/api/heartbeat` completo, stubs de `/api/triage`, `/api/hitl` e `/api/demo/reset`, `vercel.json` (gru1 + cron 12:00 UTC).
   - Build, lint e smoke test locais ok.
   - **Correção:** ponte do ROI de 23% → **18,7%** (~R$ 17 mil/ano; judgment #37).
   - ⏳ Projeto Vercel não criado: o MCP `vercel-g4` recebe 403 no time `case-g4` até o Daniel aprovar o link de acesso.
12. Turno 2: app Vercel (dashboard + console + `/api/heartbeat`) + deploy + ativar o fluxo 3 com a URL + vídeo + PR.

## Perguntas abertas para o Daniel
- [x] ADR-0010: RAG como classificador único (Daniel). ADR-0011: diretrizes do n8n (Daniel).
- [x] 6 decisões dos fluxos respondidas pelo Daniel → ADR-0012 (rascunho v2 em `docs/n8n-flows.md`).
- [x] OK final do rascunho v2 (Daniel, 09/11) → fluxos construídos.
- [x] Playbook-semente validado pelo Daniel (10/11).
- [x] Ativação dos fluxos 1 e 2 autorizada pelo Daniel (10/11).
- [x] Credenciais G4 criadas pelo Daniel (10/11). Falta só a `G4 – Cron da Vercel`, depois do deploy.
- [ ] Opcional: testar `text-embedding-3-large` (~US$ 0,30) para tentar subir o RAG alguns pontos.
- [x] ADR-0003 validada (09/11).
- [x] Premissas de custo: benchmarks com fonte (8,6 min/ticket MetricNet; R$ 21,30/h CAGED CBO 4223-20; volume 30K/ano do brief).
- [x] ADRs 0004, 0005 e 0009 validadas pelo Daniel (09/11). Categorias "só humano" conforme a proposta da 0005.
- [x] Slack: sem workspace → envio demonstrado pela caixa de mensagens do painel; nó Slack fica no workflow, documentado.

## Recursos (sem segredos)
| Recurso | Valor |
|---|---|
| Repo | https://github.com/danielcoelhof/ai-master-challenge (branch `submission/daniel-fonseca`) |
| Supabase project ref | `awiphrbtvgapuuebiouw` (sa-east-1) |
| Vercel project | _pendente_ |
| n8n | VPS do Daniel — URL em `N8N_BASE_URL` (`.env`), MCP em `/mcp-server/http` (exige token; endpoint respondeu 401 sem token em 09/11) |

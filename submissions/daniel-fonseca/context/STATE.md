# STATE — handoff entre sessões

> Atualize ao final de cada sessão. Qualquer agente (Claude Code, Codex…) deve conseguir continuar o trabalho só com este arquivo + AGENTS.md.

**Última atualização:** 2026-11-10 · Sessão 03 · Claude Code (Opus 5.5)

## Fase atual
**Sessão 03 (pente fino, 10/11 noite):** navegação de um nível com submenus, tela **Tickets** em formato de conversa, Slack simulado no navegador, Diagnóstico enxuto, "atendente" × "agente" e Proposta mais objetiva (ADR-0015, Proposta). Fluxo 1 sem a gravação na caixa, republicado. JSON dos 4 fluxos exportados. **Próximo:** deploy de produção + smoke test; revisão da documentação pedida pelo G4 (README final); vídeo (última etapa); PR manual pelo Daniel.

**App Vercel integrado e em produção** (https://triagem-case-ai-master-case-g4.vercel.app). Frentes A e B integradas na `submission/daniel-fonseca` com o OK do Daniel (10/11). Monitoramento de uso ativo (n8n a cada 15 min + tarefa local a cada 2 h). Próximo: credencial do fluxo 3 (Daniel) e ativação; revisão do app pelo Daniel; exportar os JSON do n8n; README final; vídeo; PR.

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
   - ✔ Projeto Vercel `triagem-case-ai-master` (prj_JsF7acFdxYDKOmKzNVG5Lxns7hqY, time case-g4) ligado ao fork, root `submissions/daniel-fonseca/solution/app`, Next.js, Node 24, funções em gru1. Variáveis importadas pelo Daniel via arquivo local (os segredos não passaram pela conversa; arquivo apagado em seguida).
   - Frentes A e B pausaram no limite de uso e foram retomadas por mensagem em 10/11.
   - ✔ **Produção no ar:** https://triagem-case-ai-master-case-g4.vercel.app (branch de produção = `submission/daniel-fonseca`, ajustada pelo Daniel no painel).
     - A proteção padrão do time (Vercel Authentication em `all_except_custom_domains`) bloqueava o domínio de produção. A IA mudou para `preview`, conforme a decisão de app público: a produção fica aberta e os previews protegidos.
     - Smoke test: 3 áreas 200; heartbeat 401 sem segredo e 200 com segredo; triage 501 (stub); nenhum segredo nem host do n8n nos 9 chunks do cliente.
   - Erro corrigido: os worktrees das frentes (`.claude/worktrees/`) entraram no commit `26ee06f` como repositórios embutidos (só ponteiros). Saíram no `8afee68`, e `.claude/worktrees/` foi para o `.gitignore`.
12. ✔ (10/11) **Integração das frentes**, com o OK do Daniel:
   - merges `7ee7de4` (Frente B: Console Triagem · Fila · Caixa, rotas `/api/triage`, `/api/triage/sample`, `/api/hitl`, `/api/inbox`, `/api/demo/reset`) e `8794b3d` (Frente A: Painel Diagnóstico · ROI · Operação, `lib/roi.ts` com 5 testes, Como foi feito Proposta · Decisões · Condução, `12_painel_extras.py`);
   - ajustes da base: `prebuild` gera `docs.generated.json` das ADRs e do judgment log; `npm test`; `.gitignore` (`data`/`.venv` sem barra, `*.tsbuildinfo`, `**/next-env.d.ts`);
   - lint, testes e build ok; nenhum segredo nem host do n8n em `.next/static`.
   - **Deploy:** os pushes geravam só previews (`target: null`), apesar da branch de produção ajustada antes. A IA criou o deploy de produção pelo MCP (`dpl_FV7YzF2jcCVCLBiERGtRBw9KiEBD`, commit `7a52743`). **Pendente (Daniel):** conferir em Settings → Environments → Production a branch rastreada, para os próximos pushes irem direto à produção.
   - **Teste ao vivo:** 9 rotas de página 200; heartbeat sem segredo 401; triagem pelo app nos 3 caminhos (Purchase 0,94 → Resposta automática; Hardware 0,62 → Revisão humana; HR Support → Somente humano), com tokens, custo (US$ 0,0006–0,0014) e tempos por etapa em `triage_runs`; texto curto 400; aprovação na fila 200 com solução aprendida #18 e vizinho sugerido (similaridade 0,84); aprovação repetida 409.
   - `reset_demo.py` rodado: fila com 6, caixa com 2, 2 respostas automáticas. As soluções aprendidas dos testes (#16, #17, #18) ficaram, conforme o script.
   - Sugestões das frentes para o Daniel decidir: esconder `usage_alert` da caixa pública; vizinho do efeito "aprendeu" filtrado pela categoria aprovada; glossário (PRD §6.1).
13. ✔ (10/11) **Monitoramento de uso**, com instrução do Daniel ("Ative o monitoramento"):
   - migration `…0007_usage_monitor`: função `usage_monitor_check()` com os 8 sinais do PRD §8.1 e repetição barrada por sinal;
   - fluxo n8n **G4 · Monitor de uso (alertas)** `xchzY3KKbsm0hzyG`, a cada 15 min, **publicado**; credencial `G4 - Supabase` vinculada por ID (o n8n tinha auto-atribuído `Supabase – padaria-bi`). Testado: alerta gravado na caixa (exec 248) e repetição barrada (exec 249);
   - tarefa agendada local `g4-monitor-uso-app` (a cada 2 h, até o Daniel mandar desligar): só leitura de Supabase, Vercel e n8n; reporta nesta sessão. Ela substitui o `scripts/monitor_usage.py` previsto no PRD. **Passo do Daniel:** abrir a tarefa no app e clicar em "Run now" uma vez para aprovar as ferramentas e definir o modo de permissão;
   - sobra do teste: 1 alerta de teste (`notifications` id 11) e 1 evento sinalizado (`usage_events` id 37). O comando de limpeza foi recusado; o `reset_demo.py` remove os dois.
14. Fluxo 3 (heartbeat): URL de produção e Header Auth configurados. **Passo do Daniel:** criar no n8n a credencial `G4 - Cron da Vercel` (Header Auth, Name `Authorization`, Value `Bearer ` + `CRON_SECRET` do `.env`). Depois a IA vincula pelo ID, testa e publica.
15. Turno 2: app Vercel (dashboard + console + `/api/heartbeat`) + deploy + ativar o fluxo 3 com a URL + vídeo + PR.

## Sessão 03 — notas para a próxima sessão
- Rotas novas: `/painel/diagnostico|roi|operacao`, `/tickets`, `/como-foi-feito/proposta|decisoes|conducao`; as antigas redirecionam (`next.config.ts`).
- Tickets: lista = `is_demo` (compartilhados) + `client_token` do navegador (`components/tickets/store.ts`, localStorage). `/api/hitl` e `/api/tickets/reply` só aceitam ticket de demonstração ou com o token.
- `reset_demo.py` marca tudo o que cria como `is_demo`; `/api/demo/reset` também.
- Migration `20261110000008_tickets` aplicada pela conexão do `.env` (os MCPs do projeto não carregaram nesta sessão) e registrada em `supabase_migrations.schema_migrations`.
- Testes de 10/11 deixaram as triagens #40–44 (não demo, invisíveis para outros navegadores) e uma solução aprendida a partir do ticket de demonstração #34.

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
| Vercel project | `triagem-case-ai-master` (prj_JsF7acFdxYDKOmKzNVG5Lxns7hqY, time case-g4) · https://triagem-case-ai-master-case-g4.vercel.app |
| n8n | VPS do Daniel — URL em `N8N_BASE_URL` (`.env`), MCP em `/mcp-server/http` (exige token; endpoint respondeu 401 sem token em 09/11) |

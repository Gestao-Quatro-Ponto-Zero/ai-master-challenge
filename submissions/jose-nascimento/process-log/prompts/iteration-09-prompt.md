# Prompt da Iteração 09 — QA final integral e prontidão de submissão

- **Iteração:** 09 (QA final integral e prontidão de submissão — gate de qualidade antes da It10)
- **Data:** 2026-08-29
- **Executor:** exatamente um subagente `deepseek-max` (DeepSeek V4 Flash, max reasoning, via OpenCode Go), sob orquestração do opencode (`openai/gpt-5.6-sol` — "GPT 5.6 Sol Max")
- **Transcrição fiel com paths operacionais normalizados:** este arquivo é a transcrição fiel do prompt recebido do orquestrador; não é o texto byte-a-byte do original — os únicos paths absolutos de máquina foram normalizados (nota abaixo).
- **Nota de normalização (política F2/It08, estendida à It09):** categorias normalizadas (2): (1) `<repo-workdir>` — path absoluto do repositório de trabalho, onde vive a branch `submission/jose-nascimento` e a pasta da submissão; (2) `<dados-externos>` — path absoluto do diretório externo com os 5 CSVs originais (não commitado; os CSVs commitados em `solution/data/raw/` são a fonte do pipeline). **Por quê:** a política F2 exige zero paths de máquina em documentos novos da pasta — o avaliador deve conseguir re-ler o prompt sem conhecer o ambiente do candidato, e nenhuma estrutura de diretórios pessoal deve vazar para o versionado. Os placeholders substituem **somente** esses paths; todo o restante — escopo, QA obrigatório, fix policy, validação final, git, aceitação, final — é transcrito fielmente.

---

Você é o AGENTE EXECUTOR ÚNICO da ITERAÇÃO 09 — QA final integral e prontidão de submissão — do G4 AI Master Challenge. Audite/fixe apenas defeitos comprovados, deixe o repo em estado iminente de submissão, mas NÃO preencha data final, NÃO faça o commit final de submissão, NÃO abra PR (It10 só após aviso ao candidato e auditoria 5x).

REPO
- `<repo-workdir>`, branch `submission/jose-nascimento`, pasta única `submissions/jose-nascimento/`, HEAD `c15a5dfcae010fb514a698d35bde4f2a7b41e604`.
- Leia integralmente instruções oficiais/template; plano/checklist; README; report; solution README/contract/evidence/tables/charts; process log; git history; verifier. Sem pesquisa externa/concorrentes.

QA OBRIGATÓRIO
1. **Git/escopo:** compare branch vs upstream/main e fork/main; toda mudança do candidato somente `submissions/jose-nascimento/`; branch correta; autoria; linear history; remote sync; file modes; nenhum secret; nenhum untracked/staged; nenhum binário proibido/cache/venv/db; root files intocados.
2. **Regras oficiais:** fork/branch/pasta/título planejado; 1 challenge; solution + process log; setup; não altera fora; formato; time/budget disclosure; process evidence; baseline/originalidade; checklist oficial mapeado item a item.
3. **Challenge 001:** prove que entrega responde (a) causa raiz cruzando 5 tabelas, (b) segmentos + contas específicas, (c) ações concretas priorizadas + impacto; dados verificáveis; correlação/causalidade; CEO-readable; 5 tabelas realmente usadas ou auditadas.
4. **Fresh clone real do origin branch:** ambiente isolado, sem `<dados-externos>`; `./run.sh` 2×, `make all`, CWD externo, direct verifier; bytes/modes/tree; exactly 6 PNG/26 tables/report; runtime; FAIL tests (raw/schema/value/evidence link/error ledger); zero stale/traceback onde contratado.
5. **Numeric claims:** recalcule independentemente âncoras executivas principais (lenses, dezembro, onboarding, usage/support, segments/accounts, impact/power). Compare README/report/evidence/tables; zero drift/rounding enganoso.
6. **Causal/semantic sweep:** 43 first events vs 117 episodes; R1 exposure vs loss; event/logo/subscription/status; range vs CI; lift vs causal effect; operational watchlist vs prediction; exposure-only vs risk; all-active; synthetic/censoring/power.
7. **Originalidade:** solution/report/README sem nomes/links/fraseado de outras submissões/benchmark interno; process log disclosure honesto sem usar benchmark como fonte. Busque tokens conhecidos dos research files apenas no contexto permitido; não esconda histórico.
8. **Markdown/UX:** todos links e imagens relativos resolvem no GitHub; anchors/headings/tables/fences; no truncamento; no absolute path; no placeholder falso; Português claro; word counts; 6 PNGs visual validator/layout; README primeira tela/links/checkboxes; LinkedIn `não informado` aceitável; data permanece `pendente` por instrução.
9. **Process log:** ferramentas/roles corretos; 8 erros; decisions/attribution; prompts/reports/reviews/hypotheses/assumptions; snapshots claramente datados; raw reviews externos não requeridos; zero falso chat-export/screenshot; budget range; gate It08 concluded.
10. **Security/license/repro:** Kaggle official link/MIT attribution, raw MD5, no PII/credentials, no network runtime, deps pins public, file sizes/repo reasonable.
11. **PR readiness sem abrir:** título exato planejado `[Submission] Jose Nascimento — Challenge 001`; base upstream main; body draft pode ser criado dentro de process-log/docs (não fora) se útil, mas NÃO chamar gh pr create; confirmar fork branch pública/acessível.
12. Re-derive snapshot process counts; em docs públicos evite total que envelhece. Atualize snapshot para "fechamento It09" somente onde necessário; final It10 rederivará. Corrija qualquer stale detectado.
13. Atualize `execution-plan.md`/checklist: It09 CONCLUDED após QA; gate 3x It09 PENDING; It10 PENDING; itens PR/data final permanecem PENDING. Crie `process-log/management/submission-readiness-checklist.md` com cada regra oficial status/evidência e apenas data/commit final/PR pendentes.
14. Arquive prompt `process-log/prompts/iteration-09-prompt.md`; report `process-log/reports/iteration-09-final-qa-report.md` com comandos/results/findings/fixes/snapshot/risks/handoff para gate3x e auditoria final5x.

FIX POLICY
- Corrija nesta iteração apenas bugs/stale/links/claims/hygiene comprovados. Não redesenhe análise/narrativa. Se mudança afeta números, BLOCKED e explique.

VALIDAÇÃO FINAL DESTA ETAPA
- Run/verifier pós-fix; link checker; `git diff --check`; remote; no placeholders exceto dois permitidos; no pr; branch public.

GIT
- Se houver docs/QA updates, commit `chore: complete pre-submission quality assurance`; só pasta; sem amend/force/config/destrutivo; push/local==remote/tree limpo. Este NÃO é o commit final da submissão; It10 ainda pendente.

ACEITAÇÃO
- Todos os itens oficiais/analíticos/process/repro PASS; pendências somente data final + final commit + PR; report QA prova isso.

FINAL
PASS/BLOCKED; hash/push; official checklist; runs/numeric audit/claims/originality/security; fixes; exact remaining pending; readiness verdict; handoff aos 3 reviewers It09. Não abrir PR.
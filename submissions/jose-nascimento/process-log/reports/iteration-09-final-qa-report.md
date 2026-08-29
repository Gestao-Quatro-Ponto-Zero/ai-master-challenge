# Report da Iteração 09 — QA final integral e prontidão de submissão

- **Iteração:** 09 · **Data:** 2026-08-29 · **Executor:** 1 subagente `deepseek-max` (DeepSeek V4 Flash, max reasoning, via OpenCode Go) · **Gate 3x da It09:** `PENDING` (a disparar após este commit)
- **Escopo:** auditoria integral da submissão contra instruções oficiais, checklist do orquestrador (A–F), contrato analítico e claims do relatório executivo — com re-execução limpa e re-derivação numérica independente.
- **Veredito:** **PASS** — nenhum defeito material; 4 fixos de hygiene/stale comprovados (ver §6); pendências exclusivamente de It10 (data final, commit final, PR).

---

## 1. Objetivo e método

Auditar/fixar apenas defeitos comprovados e deixar o repo em estado iminente de submissão, sem preencher data final, sem commit final e sem abrir PR (It10). Método: leitura integral de instruções/plano/checklist/READMEs/report/solution/contract/evidence/tables/charts/process log/git history/verifier; re-execução em clone fresco do origin; re-derivação numérica independente; varreduras de originalidade/links/markdown/hygiene.

## 2. QA git/escopo (comandos e resultados)

| Comando | Resultado |
|---|---|
| `git status` / `git log --oneline -15` | Branch `submission/jose-nascimento`, tree limpa, up-to-date com origin; HEAD `c15a5df` |
| `git remote -v` | `origin` = fork do candidato (GitHub); `upstream` = `Gestao-Quatro-Ponto-Zero/ai-master-challenge` (adicionado read-only para a auditoria) |
| `git fetch upstream main` + `git diff upstream/main origin/main` | **vazio** — `upstream/main` == `origin/main` == local `main` == `4aed364`; zero drift do fork |
| `git log --merges` | 0 merges — histórico linear |
| `git log --format='%an <%ae>'` | 31 commits do candidato (autor único verificado, sem alterar `git config`) + 5 de base do repo oficial |
| `git diff main...HEAD --name-only \| grep -v '^submissions/jose-nascimento/'` | zero ocorrências — 100% do escopo na pasta do candidato |
| `git ls-tree -r` (modes/binários) | único executável = `run.sh` (esperado); únicos binários = 6 PNGs em `out/charts/` (manifesto fechado); zero `.db/.duckdb/.sqlite/.pyc`/venv/cache/segredos |
| `git status --porcelain --ignored` | zero untracked/staged |
| Grep de segredos (password/api key/token/ghp_/AKIA/BEGIN PRIVATE) | zero em arquivos versionados (ocorrências são os padrões do próprio verificador) |
| Tamanhos | `.git` 7,2 MB; pasta 5,0 MB; maior arquivo 1,4 MB (CSV raw) — razoável |

**Veredito:** PASS.

## 3. QA regras oficiais

Mapeamento item a item em [`process-log/management/submission-readiness-checklist.md`](../management/submission-readiness-checklist.md) (30 regras + 3 pendências formais): fork/branch/pasta/título; 1 challenge; solution + process log; setup; zero alteração fora da pasta; template; time/budget disclosure honesto (~22–27h vs 4–6h oficiais, excedido por decisão consciente — F11); baseline/originalidade. **PASS** — pendências apenas: data final, commit final, PR (It10).

## 4. QA Challenge 001 (entrega)

- (a) **Causa raiz cruzando 5 tabelas:** churn precoce de onboarding — 43 primeiros eventos em dez/24 (22,51% dos 191 elegíveis vs mediana 13,01% dos 6 meses anteriores; razão 1,73), 83,7% do pico em contas 0–3m (36/43; razão 2,37), controle de composição de tenure (esperado 24,82, observado 43), 53,4% dos primeiros eventos ≤90d do signup (188/352), 68,4% da exposição R1 ≤90d (806.419/1.179.139). As 5 tabelas entram na análise (accounts: signup/coortes; subscriptions: R1/winner; churn_events: lente C; feature_usage: uso; support_tickets: CSAT/suporte) — gates G8-segments/G11-onboarding do evidence 03.
- (b) **Segmentos + contas específicas:** S1–S5 com N/MRR/lift (t15); watchlist top-20 = 392.030 US$/mês (10,7% da exposição de 3.668.852), 8 onboarding validadas + 12 exposure-only (t16/t21); 10 contas nomeadas no relatório §5 com MRR/evidência/limitação.
- (c) **Ações priorizadas + impacto:** ACT-01..04 com sequenciamento (ACT-03 → ACT-01 · ACT-02 paralelo · ACT-04 Later), owners, prazos, stop/go em 3 estados; impacto em faixa 2,7–13,0 eventos e 21.104–101.078 US$/90d com premissas nomeadas (t18/t19/t20).
- Verificável: apêndice §10 do relatório + 26 tabelas. Correlação vs causalidade rotulada (t09/t10). CEO-readable: 2.275 palavras, resposta primeiro, gate F4 (1.400–2.400).

**Veredito:** PASS.

## 5. QA numérico — re-derivação INDEPENDENTE (59/59)

Implementação própria (fora do repo, lendo somente os 5 CSVs brutos; sem importar scripts do pipeline nem tabelas derivadas) recalculou as âncoras executivas:

| Grupo | Âncoras (re-derivadas == claims) |
|---|---|
| Lentes | 110 (flag) · 486 assinaturas/312 contas · R1 1.179.139 · 600 eventos/352 contas |
| Dezembro | 43 primeiros · 117 episódios · 191 elegíveis · 22,51% · mediana 6m 13,01% · janela 7,42% · razões 1,73/3,03 |
| Pico | bucket 0–3m 36 (83,7%) · baseline 15,17 · razão 2,37 · controle tenure 24,82/1,73 |
| Onboarding | ≤30d 91 (25,9%) · ≤60d 150 (42,6%) · ≤90d 188 (53,4%) · R1 ≤90d 806.419 (68,4%) |
| Uso | 2.775→9.027 (+225,3%) · mediana conta-mês 2,0→2,0 · alinhado +883,3% · sensibilidade +1,1% |
| Suporte | tickets/conta 0,309 vs 0,349 · escalação 2,8% vs 5,1% · CSAT 4,0 vs 3,97 (pools 346/3.162) |
| Coortes/KM | churn KM t6 58,9% (2024Q1) e 69,2% (2024Q2) · taxa global 70,4% |
| Backtest D | lift 1,574/1,556/1,835 (precisão 0,3393/0,3846/0,5417; baselines 0,2155/0,2471/0,2952) |
| Watchlist | soma 392.030 · share 10,7% |
| Impacto | precisão pooled 83/193 = 0,4301 · eventos 34,4/6,9/2,7/13,0 · exposição 53.497/21.104/101.078 · Wilson 0,362–0,501 |
| Poder | MDE 68/51/37% (N/braço 34/68/136) · poder 11/31/61% (N de decisão 136) · P(falso GO) 23,7% |

**59/59 conferem — zero drift, zero rounding enganoso** (ex.: exposição base usa a fração exata 83/193, não o arredondamento 0,4301). Notas de método: (1) a re-derivação inicial com definição alternativa de elegibilidade do backtest divergia — a semântica do pipeline (elegíveis = signups ≤ cutoff, sem excluir churnados anteriores; outcome = qualquer evento na janela) foi confirmada como a correta e reproduz os valores; (2) poder por cenário usa o N de decisão (4 trimestres × 50/50 = 136/braço), documentado no report executivo §7.

**Veredito:** PASS.

## 6. Fixes aplicados (hygiene/stale comprovados — nenhum número de análise alterado)

| # | Defeito comprovado | Fix |
|---|---|---|
| F1 | `execution-plan.md` linha de status (It06): verificador "67 PASS" e outputs "46/46" stale vs evidência It06 (68 PASS após o fixer do gate; 45/45 = 40 derivados + 5 raw) | Corrigido para 68 PASS/45/45 com nota de que 67 era o estado pré-gate; status da versão estendido com It07/It08/It09 |
| F2 | `execution-plan.md`/checklist desatualizados para o fechamento It09 (It09 `PENDING`; sem readiness checklist; F11 sem a fatia It09) | It09 `CONCLUDED` com evidência; It10 `PENDING`; gate 3x It09 `PENDING`; F11 com fatia It09 e faixa honesta ~22–27h (soma bruta ≈ 26h10) |
| F3 | Verificador `06_verify_pipeline.py` esperava It09 `PENDING` (G10) e não conhecia os docs novos da It09 | G10 atualizado (It08/09 `CONCLUDED`; It10 `PENDING`; checklist com "It09 `CONCLUDED`" e "gate 3x da It09 `PENDING`"); `PL_PROMPTS`/`PL_REPORTS`/`NEW_PL_DOCS` estendidos (prompt It09, report It09, readiness checklist) — 88 checks, mesmo conjunto |
| F4 | Snapshots de contagem de docs públicos (README do process log §7, evidence-index, README da submissão) parados no fechamento It08 | Atualizados para o fechamento It09 (10 iterações, 21 prompts, 21 reports, 9 summaries, 32 commits, 126 arquivos, verifier 88 PASS) com instrução de re-derivação na It10 |

Sem mudanças em scripts de análise, tabelas, PNGs, report executivo ou qualquer claim numérico (md5 do report executivo inalterado — ver §8).

## 7. QA originalidade

Varredura por tokens de pesquisa interna/benchmark (nomes de arquivos de pesquisa, paths de máquina, termos) nas entregas: **zero ocorrências** fora do contexto permitido — os únicos usos são (a) prompts arquivados It00–03 citando paths de pesquisa interna como **proibição de uso** e transparência (exceção documentada E1/F2, decisão D-08: não sanitizar histórico), e (b) reports históricos It00–07 descrevendo sandboxes/validações (mesma exceção). A solução, o report executivo e o README não citam nenhuma fonte externa; "baseline" aparece apenas em acepções estatísticas (taxa de base); `rivalytics` apenas na atribuição oficial do dataset. Conclusões 100% re-derivadas dos 5 CSVs.

**Veredito:** PASS.

## 8. QA reprodutibilidade — clone fresco REAL do origin (ambiente isolado, sem `<dados-externos>`)

| Execução | Resultado |
|---|---|
| `git clone --branch submission/jose-nascimento --single-branch <origin>` | clone limpo em `<sandbox-dir>`; tree == origin HEAD `c15a5df` |
| `./run.sh` (1ª) | exit 0 · **88 PASS / 0 FAIL** · 65 s |
| `./run.sh` (2ª, determinismo) | exit 0 · 88 PASS · 65 s · **48 arquivos MD5-idênticos** à 1ª |
| `make all` | exit 0 · 88 PASS · 66 s · byte-idêntico |
| `run.sh` de CWD externo (`bash <path>/run.sh` de outro diretório) | exit 0 · 88 PASS · 64 s · byte-idêntico |
| verificador direto (raiz do repo e de CWD externo) | exit 0 · 88 PASS · **zero `__pycache__`/`.pyc`** após tudo |
| `git status` após os runs | zero modificados — outputs byte-idênticos ao commitado |
| FAIL tests (sandbox) | (1) coluna renomeada → exit 1, relatório regravado com FAILs "não executado (schema)", 0 tracebacks; (2) `churn_flag=TruX` → exit 1, "não executado (validação)", 0 tracebacks; (3) raw CSV removido → preflight útil, exit 1; (4) tabela derivada removida → verifier exit 1 com FAILs estruturados; (5) link interno corrompido → G3 exit 1 apontando o link. **Zero traceback, zero stale em todos os cenários contratados** |
| Artefatos | exatamente 6 PNGs / 26 tabelas / report executivo presentes (manifests A5/A7/F1) |

**Veredito:** PASS.

## 9. QA processo, markdown, security

- **Processo (QA9):** ferramentas/roles corretos (orquestrador `openai/gpt-5.6-sol` não implementa; executor/revisores/corretor `deepseek-max` via OpenCode Go); exatamente 8 erros E1–E8 com causa raiz/correção/commit (gate G2); decision ledger com 18 decisões atribuídas (nada de subagente atribuído ao candidato); 21 prompts/21 reports/9 summaries/1 hipóteses/6 decisões por iteração; snapshots datados ("fechamento da It08/It09"); raw reviews externos documentados como working artifacts não versionados; zero falso chat-export/screenshot (checkboxes honestos — G6); budget ~22–27h declarado honestamente; gate 3x da It08 `CONCLUDED` (G10). **PASS.**
- **Markdown/UX (QA8):** 244 links relativos em 27 arquivos .md — **0 quebrados** (incl. âncoras GitHub-style); fences balanceadas em todos os arquivos; tabelas do report íntegras (sem célula truncada); zero absolute path em docs novos; zero placeholder falso (gate G11 do verificador); 6 PNGs validados (não-brancos; dimensões 1170–1560 × 615–900 px; cores 258–848); word counts: README 1.583, report executivo 2.275 (budget 1.400–2.400), process log README 2.373; README primeira tela conforme template; LinkedIn `não informado` e data `pendente` mantidos por instrução. **PASS.**
- **Security/licença/repro (QA10):** Kaggle oficial + MIT atribuídos (solution README §11, data/raw README, README da submissão); MD5 dos 5 raw == manifesto commitado (gate C2); zero PII/credenciais; zero imports de rede (D4); pins públicos `pandas==3.0.5`/`matplotlib==3.11.1`; tamanhos razoáveis. **PASS.**

## 10. QA causal/semântico (sweep)

Todas as distinções contratadas presentes e consistentes entre README/report/evidence/tables: 43 primeiros eventos ≠ 117 episódios (hazard de 1º evento vs total; relatório §2); R1 exposição ≠ perda ("exposição, não perda" em §1/§2/§7/§9); eventos ≠ logos ≠ revenue churn (lentes §2; "afetados ≠ evitados"); faixa observada ≠ CI (Wilson 0,362–0,501 separado; disjoint verificado G13); lift ≠ efeito causal (backtest point-in-time; "lift é associação, não efeito"); watchlist = priorização operacional, nunca score/predição; exposure-only ≠ risco (t21: "NÃO rotular alto risco"); all-active no corte declarado (§9); base sintética/censura/poder declarados (§9, §3, §7). **PASS.**

## 11. Snapshot no fechamento da It09 (contagens derivadas por glob/git)

| Métrica | Valor (fechamento It09) |
|---|---|
| Iterações executadas | **10** (It00–09) — It09 com prompt/report arquivados |
| Review gates 3x concluídos | **9** (It00–08) — gate da It09 `PENDING` |
| Revisores (instâncias) | **27** (9 gates × 3) |
| Correções sequenciais commitadas | **10** (8 fixers de gate + correção visual It04 + fixer do gate It08) |
| Erros materiais registrados | **8** (E1–E8) |
| Prompts arquivados | **21** (20 It00–08 + `iteration-09-prompt.md`) |
| Reports versionados | **21** (20 It00–08 + `iteration-09-final-qa-report.md`) |
| Review summaries | **9** (It00–08) |
| Decisões / hipóteses | 6 arquivos + ledger / 1 arquivo (H1–H10) |
| Commits do candidato | **32** (31 no fechamento It08 + `chore: complete pre-submission quality assurance`) |
| Arquivos versionados na pasta | **126** (123 no fechamento It08 + 3 novos: prompt, report, readiness checklist) |
| Verificador | **88 PASS / 0 FAIL** (mesmo conjunto de checks; G10/inventário alinhados à It09) |
| Runtime do pipeline | ~64–66 s nesta máquina (faixa documentada ~65–75 s) |

> Re-derivar na It10 (globs/git são a fonte; nenhum total final estático deve ser mantido).

## 12. Riscos remanescentes e handoff

1. **Gate 3x da It09 `PENDING`:** disparar 3 revisores `deepseek-max` read-only em paralelo (mesmo prompt, contextos separados, sandboxes fora do repo) sobre este commit; fixer sequencial se findings materiais; ledger em `process-log/reviews/iteration-09-review-summary.md` (a criar no gate).
2. **Auditoria final 5x (It10):** re-auditoria integral antes do PR — re-derivar contagens; preencher data; commit final; abrir PR com título exato e base `upstream main`.
3. **Verificador acoplado aos estados:** o gate G10 exige "It09 `CONCLUDED`" + "gate 3x da It09 `PENDING`" no checklist e no plano — ao concluir o gate da It09, atualizar G10 para o novo estado esperado (mesmo padrão das iterações anteriores).
4. **Convenções de docs novos:** manter (a) zero paths de máquina (G4), (b) backtick+hex = hash de commit apenas (G9; MD5 nunca em backticks), (c) zero placeholders falsos (convenção do gate G11 do verificador), (d) sem o nome de usuário do candidato sem hífen como literal (token de path pessoal do G4).
5. **Word count do report executivo com margem ~125:** qualquer adição futura exige re-medição (G6/F4).
6. **Time budget:** faixa honesta ~22–27h no fechamento It09 (fatias `~` não aditivas; soma bruta ≈ 26h10) — excedido por decisão consciente; trims formais vigentes; re-derivar na It10.
7. **PR body:** rascunho de descrição do PR (resumo executivo + navegação dos artefatos) fica documentado neste report (apêndice A); será usado na It10 sem alterações de escopo.

## Apêndice A — Rascunho de descrição do PR (a usar na It10)

```markdown
## Resumo
Diagnóstico de churn da RavenStack (Challenge 001): a causa raiz é churn precoce de
onboarding (contas novas saindo nos primeiros 90 dias), não insatisfação geral nem uso.
Entrega: relatório executivo CEO-ready com 6 gráficos, 26 tabelas auditáveis, watchlist
operacional top-20 com contas específicas e plano de ações priorizadas com impacto em
faixa e premissas nomeadas — tudo reproduzível com 1 comando (`./run.sh`), offline e
determinístico (verificador com 88 checks).

## Navegação
- README da submissão: submissions/jose-nascimento/README.md
- Relatório executivo: submissions/jose-nascimento/solution/report-executivo.md
- Solução (pipeline + evidências + tabelas + gráficos): submissions/jose-nascimento/solution/
- Process log (prompts, reports, decisões, erros, revisões): submissions/jose-nascimento/process-log/
- Readiness checklist: submissions/jose-nascimento/process-log/management/submission-readiness-checklist.md

## Processo
Uma iteração por etapa (It00–09), revisão 3x read-only por etapa (27 revisões),
8 erros reais da IA documentados com causa raiz e correção, decisões com atribuição
candidato vs modelos, hipóteses/prémissas/narrativa pré-registradas antes do código.
```

## Apêndice B — Validações finais desta etapa (pós-fix)

- `./run.sh` + verificador pós-fix em clone fresco: **88 PASS / 0 FAIL**, byte-idêntico ao commitado (relatório executivo md5 inalterado — MD5 não citado em backticks por convenção G9);
- link checker independente: 244 links, 0 quebrados; fences/tabelas íntegras;
- `git diff --check` limpo; `git status` limpo; `origin/submission/jose-nascimento` == local;
- placeholders: somente os dois permitidos (`pendente` para data, `não informado` para LinkedIn);
- PR **não** aberto; fork/branch públicas (acesso anônimo confirmado); branch pronta para PR na It10.
# Report de Correção — Review Gate da Iteração 06 (fixer sequencial)

- **Data:** 2026-08-29
- **Agente:** corretor sequencial `deepseek-max` (DeepSeek V4 Flash, max reasoning, via OpenCode Go), sob orquestração do opencode
- **HEAD base:** `9357c202bbd4b5739fd8dc44420c66f2c9e4b9e6` (esperado no prompt) — confirmado no início (working tree limpo, branch `submission/jose-nascimento`)
- **Prompt integral:** `process-log/prompts/iteration-06-review-fix-prompt.md` (arquivado)
- **Tempo de relógio (F11):** ~1h50min (3 reports de revisão + correções do verificador/estágio 01/Makefile/run.sh/docs + validação em clone fresco + documentos) — acumulado analítico registrado no checklist F11

---

## 1. Status

**PASS** — invocação direta do verificador não gera mais `__pycache__` (prova: 2× em clone limpo, zero pyc, exit 0); valor categórico/booleano inválido (`churn_flag=TruX` em accounts e em subscriptions) vira FAIL estruturado "não executado (validação)" com relatório regravado e exit 1, sem traceback e sem stale; ambiente corrigido para Linux **aarch64**; contagens derivadas (`DERIVED`=40 via `$(words $(DERIVED))`; outputs regeneráveis=45 = 40 derivados + 5 raw; README estático separado; claims 41/46 removidas); uid `B4-md-README.md` corrigida para paths únicos + gate D7-uids (check nº 68, testado por injeção); `PYTHON ?= python3` no Makefile com override documentado e exit 2 do `make verify` documentado; runtime documentado como faixa observada ~65–75 s ("aproximação, não benchmark"); warnings pandas/matplotlib documentados como benignos (não suprimidos); mensagem de falha do `run.sh` qualificada. Revalidação completa em clone fresco: 45/45 outputs byte-idênticos, tree limpa, zero pycache, 68 PASS/0 FAIL, cenários de FAIL sem traceback/stale, run.sh propaga exit codes. Commit `fix: harden fresh-clone pipeline verification` e push concluídos; **gate It06 `CONCLUDED`**; It07 `PENDING` (não iniciada).

## 2. Correções (matriz finding → ação)

| # | Finding (revisores) | Correção | Onde |
|---|---|---|---|
| 1 | **F1 (review-18199ddc, MEDIUM):** valor categórico inválido (`churn_flag=TruX`, schema intacto) crashava `01_ingest_audit.py` com KeyError + traceback (`check_cross_tables`) e não regravava o relatório (stale) | **Guard mínimo de VALOR** — `BOOL_COLUMNS`/`bool_problems`/`guard_bools`: coluna booleana com valor fora do domínio canônico (True/False/0/1 + variantes string) registra **FAIL estruturado** "não executado (validação): valores não-booleanos: [...]" ANTES do masking e o check não executa; relatório regravado, exit 1, pipeline para. **Sem catch-all** (bug real continua propagando com traceback). Guardados: D04 (subs churn_flag), C01 (acc churn_flag), C02 (subs churn_flag), C03 (is_reactivation), C07 (is_trial), C08 (upgrade/downgrade_flag) + evidência `subscriptions.mrr` | `01_ingest_audit.py` (helpers após DOMAINS; guards em check_dates/check_cross_tables/collect_syntheticity_evidence) |
| 2 | **F1 (review-f1fa7caa, MÉDIO):** `python3 solution/src/06_verify_pipeline.py` criava `solution/src/__pycache__/*.pyc` (E2 via importlib) e D1 falhava na execução seguinte (9 FAILs reproduzidos) | `sys.dont_write_bytecode = True` no topo do verificador (antes de qualquer import via importlib); `PYTHONDONTWRITEBYTECODE=1` mantido no run.sh/Makefile (defesa em profundidade). Provado: invocação direta 2× em clone limpo → exit 0, zero `__pycache__`/`.pyc` | `06_verify_pipeline.py:37-41` |
| 3 | **F2 (review-18199ddc, MEDIUM) + F6 (review-f1fa7caa):** "Linux, x86_64" vs máquina real aarch64; runtime ~64–66 s vs 67–75 s observados | docs/report/requirements → **aarch64**; runtime → **faixa observada ~65–75 s**, rótulo "aproximação, não benchmark" | `requirements.txt:15`; `solution/README.md` §1/§6; report §3/§6; decisions D14 |
| 4 | **F2/F3 (3 revisores):** "41 arquivos" (clean-derived) e "46/46 outputs" | `DERIVED`=40 com contagem **derivada** `$(words $(DERIVED))` impressa pelo target; outputs regeneráveis=**45** (40 derivados + 5 raw); `solution/README.md` estático separado; claims 41/46 removidas de decisões/report/plano/checklist | `Makefile`; `solution/README.md` §4/§8; decisions D1/D4/D13; report §2/§4/§5; execution-plan; checklist |
| 5 | **F4 (review-18199ddc):** colisão de uid `B4-md-README.md` (raw/processado) | uids por **path relativo** (`B4-md-data/raw/README.md` etc.) + **gate D7-uids** (falha se id de check repetido; check nº 68 registrado por último) — testado por injeção (`A1-raw` detectado) | `06_verify_pipeline.py` (b_parseable; `check_uid_uniqueness`; main) |
| 6 | **F5/F3/F7 (3 revisores):** Makefile com `python3` fixo vs `$PYTHON` do run.sh | `PYTHON ?= python3` + `export PYTHON`; `verify`/`stage-01..05` usam `$(PYTHON)`; README documenta `PYTHON=... ./run.sh` / `make PYTHON=... verify`; exit 2 do `make verify` documentado (GNU make encapsula exit 1 do script) — sem forçar mudança de semântica | `Makefile:6-12,24-40`; `solution/README.md` §3/§7 |
| 7 | **F6 (review-18199ddc):** warnings pandas (numexpr/bottleneck) e matplotlib (Axes3D) no stderr | Verificado: originam-se de **dependências opcionais antigas do site-packages** (não de cache/diretório não gravável — nenhum cache local é necessário) → documentados como **benignos** no troubleshooting; nada é suprimido (nenhum warning analítico escondido) | `solution/README.md` §9; decisions D17 |
| 8 | **F1 (review-18199ddc) + F4 (review-4179846c):** mensagem de falha do run.sh superestimava "relatório regravado, exit 1, sem traceback" | Mensagem qualificada: falha tratada (schema/validação) → relatório regravado com FAILs; falha inesperada → diagnóstico pode ter traceback e relatório pode ficar stale ("corrija a causa e reexecute") | `run.sh:83-86` |
| 9 | **F4 (review-f1fa7caa):** D5 "promete mais do que executa" | Wording: extras são **informativos, não bloqueiam** (comportamento inalterado) | `06_verify_pipeline.py` D5 |

## 3. Validações pós-correção

**Clone fresco (isolado de `/tmp/opencode/ravendata`; árvore exata a commitar):**

| Execução | Exit | Verificador | Outputs vs baseline | pycache |
|---|---|---|---|---|
| `./run.sh` (1ª) | 0 | 68 PASS / 0 FAIL | 45/45 byte-idênticos | 0 |
| `./run.sh` (2ª, determinismo) | 0 | 68 PASS / 0 FAIL | 45/45 | 0 |
| `make all` | 0 | 68 PASS / 0 FAIL | 45/45 | 0 |
| `run.sh` de CWD externo (`/tmp`) | 0 | 68 PASS / 0 FAIL | 45/45 | 0 |
| verificador direto 1ª | 0 | 68 PASS / 0 FAIL | — | **0** |
| verificador direto 2ª | 0 | 68 PASS / 0 FAIL | — | **0** |
| `make verify` | 0 | 68 PASS / 0 FAIL | — | 0 |
| pós-`clean-derived` (regeneração) | 0 | 68 PASS / 0 FAIL | 45/45 | 0 |

- `clean-derived`: removeu **exatamente 40** arquivos (contagem derivada impressa pelo target); `data/raw/` (5 CSVs) e `process-log/` intactos; regeneração restaura 45/45 byte-idênticos; tree limpa.
- Runtime: 64–66 s nesta máquina (5 execuções completas); faixa geral observada ~65–75 s. Memória por estágio (ru_maxrss): 127,7 / 136,5 / 181,0 / 170,5 / 129,2 MB — bate com a tabela documentada (~125/134/176/167/126 MB).

**Cenários de FAIL (todos exit nonzero, diagnóstico útil, 0 tracebacks, sem stale):**

| Cenário | Resultado |
|---|---|
| python3 ausente (fake exit 127) | exit 1; "Python >= 3.11 exigido (testado em 3.12.3); encontrado: desconhecida." |
| deps ausentes (fake sem pandas) | exit 1; "dependências Python ausentes (pandas/matplotlib). Instale com: ... pip install -r requirements.txt" |
| dado ausente (`ravenstack_accounts.csv` removido) | exit 1; "dado bruto ausente ou vazio" + lista; nada executado |
| schema quebrado (`usage_date` renomeada) | exit 1; estágio 01 com 5 FAILs estruturados "não executado (schema)"; relatório **regravado** (FAIL=5); pipeline parado; 0 tracebacks |
| **categórico inválido accounts `churn_flag=TruX`** | exit 1; C01-churn **FAIL "não executado (validação): valores não-booleanos: ['churn_flag=['TruX']']"**; relatório regravado (FAIL=1); pipeline parado; **0 tracebacks; relatório NÃO stale** |
| **categórico inválido subscriptions `churn_flag=TruX`** | exit 1; D04-ravenstack_subscriptions + C02-churn **FAIL (validação)**; relatório regravado; 0 tracebacks |
| corrupção composta (t16 removida + PNG pruned recriado + panel `winner_mrr=-999` + raw alterado) | verificador direto exit 1 com **9 FAILs estruturados** (A5/A6/A7/B2-t16/C2/C3/C4/C5/C6), resumo 59 PASS/9 FAIL; `make verify` exit **2** (semântica make documentada); `run.sh` propaga exit 1 (gate interno do estágio 03 também pegou raw alterado antes do verificador final) |
| corrupção parcial (só t16 removida + pruned recriado + t14 `winner_mrr=-999`) | verificador direto exit 1 com **6 FAILs** (A5/A6/A7/B2-t16/C5/C6), resumo 62 PASS/6 FAIL — C2/C3/C4 corretamente PASS (raw e panel intactos) |

- **Gate D7-uids (teste por injeção):** duplicata `A1-raw` injetada → D7-uids FAIL com "ids duplicados=['A1-raw']".
- **Override PYTHON:** `make verify PYTHON=/tmp/opencode/fake_py` executou com o interpretador alternativo (exit 0, 68 PASS); `PATH` com fake `python3` → preflight exit 1 útil.
- **Estático:** `bash -n run.sh` OK; `compile()` dos scripts 01/06 sem escrita de bytecode; `git diff --check` limpo; escopo 100% `submissions/jose-nascimento/`; scan de segredos no diff vazio; link Kaggle (único link do README) HTTP 200; 44/44 arquivos de output rastreados + 2 READMEs byte-idênticos aos blobs commitados; 6 PNGs íntegros (manifesto fechado, 4 pruned ausentes).
- **Baseline analítico:** nenhum output mudou (regra 9) — as correções só emitem linhas novas quando há valor inválido; outputs das It03–05 permanecem válidos.

## 4. Git

- Commit `fix: harden fresh-clone pipeline verification` (escopo: só `submissions/jose-nascimento/`; 10 alterados + 3 novos: review-summary, fix-prompt, fix-report; adendos em decisions D11–D17 e report §10); sem amend/force/config/destrutivo; push validado (local == remote); tree limpa; autor do candidato.
- Post-push: clone fresco da branch (via origin) revalidado (2× `./run.sh` + verificador direto 2× + `clean-derived` + cenário categórico + byte-identidade vs blobs commitados) — resultados no relatório final desta iteração (resposta do executor).

## 5. Riscos remanescentes / handoff It07

1. **Pin exato (D1):** Python < 3.11 falha no preflight com mensagem clara (pretendido).
2. **Colunas booleanas não mascaradas** (ex.: `auto_renew_flag`) sem guard próprio — nenhum crash existe hoje (nenhum script as mascara); It09 pode estender o guard se desejado.
3. **Warnings pandas/matplotlib** em ambientes com deps opcionais antigas: benignos e documentados; não suprimidos.
4. **Falsos negativos da varredura D2** (tokens fixos): mitigado por re-checks por iteração (checklist F2).
5. **Time budget:** acumulado acima do gatilho (F11); decisão consciente registrada.
6. **It07:** relatório executivo pode citar `./run.sh`/`make all` como reprodução de 1 comando, os 45 outputs regeneráveis (40 derivados + 5 raw) e o verificador (68 checks, gate D7) como QA; nenhum número analítico mudou nesta correção.
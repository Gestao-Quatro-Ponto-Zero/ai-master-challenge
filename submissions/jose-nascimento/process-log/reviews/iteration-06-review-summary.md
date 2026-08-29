# Ledger de Revisão — Iteração 06 · Pipeline reproduzível em um comando (review gate 3x + correção sequencial)

- **Iteração revisada:** 06 (pipeline reproduzível: `run.sh`/`Makefile`/verificador/README)
- **Commit sob revisão:** `9357c202bbd4b5739fd8dc44420c66f2c9e4b9e6` (`build: one-command reproducible pipeline`); base `e0c6b7ec582aa1e356d8e05e3afb99edaebdbbd2`
- **Revisores:** 3 agentes `deepseek-max` independentes, modo read-only, em paralelo (2026-08-28/29) — sandboxes fora do repo (`/tmp/opencode/ai-master-review-sandbox/`, `iter06-*`); **repo intacto** (working tree limpo antes/depois; HEAD inalterado)
- **Relatórios dos revisores:** `/tmp/opencode/ai-master-review-reports/iteration-06/review-f1fa7caa.md` · `review-4179846c.md` · `review-18199ddc.md` (veredictos e evidências na íntegra)
- **Correção sequencial:** agente corretor (este) — commit `fix: harden fresh-clone pipeline verification`; ver `process-log/reports/iteration-06-review-fix-report.md` e prompt arquivado `process-log/prompts/iteration-06-review-fix-prompt.md`
- **Gate It06:** `CONCLUDED` (3 veredictos `PASS_WITH_FIXES`/`PASS`/`PASS_WITH_FIXES`; 2 findings MEDIUM convergentes — valor categórico inválido com KeyError+stale e claim de ambiente x86_64 vs aarch64 real — e findings de pycache/contagens/runtime/uid/Makefile/warnings corrigidos com revalidação completa em clone fresco: 2× `run.sh` + `make all` + CWD externo + verificador direto 2× + `clean-derived`, 45/45 outputs byte-idênticos, tree limpa, zero `__pycache__`, 68 PASS/0 FAIL, cenários de FAIL sem traceback e sem stale). Iteração 07 permanece `PENDING` (não iniciada).

---

## 1. Veredictos dos revisores

| Revisor | Veredicto | Findings |
|---|---|---|
| review-f1fa7caa | **PASS_WITH_FIXES** | F1 MÉDIO (invocação direta do verificador cria `solution/src/__pycache__/` e faz D1 falhar na execução seguinte — 9 FAILs reproduzidos); F2 BAIXO (clean-derived remove 40, docs dizem 41); F3 BAIXO (claim "46/46": pipeline regenera 45; 46º é o README estático); F4 INFO (D5 não aplica minimalismo — só informa); F5 INFO (Makefile `python3` fixo vs `$PYTHON` do run.sh); F6 INFO (runtime ~64–66 s vs 67–75 s medidos; aarch64 vs x86_64 documentado) |
| review-4179846c | **PASS** | F1 LOW (41 vs 40); F2 LOW (runtime 68–75 s vs ~64–66 s); F3 INFO (Makefile python3 fixo); F4 INFO (boilerplate da mensagem de falha do run.sh); F5 INFO (tokens fixos da varredura D2); F6 INFO (`make verify` exit 2); F7 INFO (C6 converte exceção em FAIL estruturado) |
| review-18199ddc | **PASS_WITH_FIXES** | F1 **MEDIUM** (valor categórico inválido `churn_flag=TruX` com schema intacto crasha o estágio 01 com KeyError + traceback em `check_cross_tables` e NÃO regrava o relatório — stale; mensagem do run.sh superestima "sem traceback"); F2 **MEDIUM** (claim factual "Linux, x86_64" vs máquina real aarch64); F3 LOW (46/46 vs 45; 41 vs 40); F4 LOW (colisão de uid `B4-md-README.md` emitido 2×); F5 LOW (`make verify` exit 2 não documentado); F6 LOW (warnings pandas/matplotlib no stderr não documentados); F7 LOW (`PYTHON=` não documentado; Makefile `python3` fixo) |

**Convergência:** os 3 revisores validaram de forma independente a entrega central
(clone fresco offline, determinismo 45/45 byte-idêntico em 7 execuções, verificador
67 PASS/0 FAIL, clean-derived seguro com regeneração byte-idêntica, dependências
mínimas com pins públicos, zero `__pycache__` nas rotas de 1 comando, memória
125/134/176/167/126 MB batendo com a documentada). Nenhum finding alterou outputs
analíticos. Findings materiais convergentes: **categórico inválido → crash+stale**
(review-18199ddc F1) e **ambiente aarch64 vs x86_64** (review-18199ddc F2,
reforçado por review-f1fa7caa F6).

## 2. Matriz finding → ação → arquivo:linha (pós-correção)

| # | Finding (revisores) | Ação | Arquivo:linha (pós-fix) |
|---|---|---|---|
| 1 | **Categórico inválido** (review-18199ddc F1, MEDIUM): `churn_flag=TruX` → KeyError + traceback + relatório stale | **Guard mínimo de VALOR** no estágio 01: `BOOL_COLUMNS` + `bool_problems` + `guard_bools` validam o domínio booleano ANTES de qualquer masking — valor inválido registra FAIL estruturado "não executado (validação): valores não-booleanos: ...", relatório regravado, exit 1, pipeline para; **sem catch-all** (bug real continua propagando). Guardados: D04, C01, C02, C03, C07, C08 + evidência `subscriptions.mrr` | `01_ingest_audit.py` (guard_bools após guard_columns; D04/C01/C02/C03/C07/C08; `collect_syntheticity_evidence`) |
| 2 | **pycache na invocação direta** (review-f1fa7caa F1, MÉDIO): `python3 solution/src/06_verify_pipeline.py` cria `solution/src/__pycache__/` (E2 via importlib) → D1 falha na execução seguinte | `sys.dont_write_bytecode = True` no topo do verificador (antes de qualquer import via importlib); `PYTHONDONTWRITEBYTECODE=1` mantido em run.sh/Makefile como defesa em profundidade; README documenta que a invocação direta não gera pycache | `06_verify_pipeline.py:37-41`; `solution/README.md` §header |
| 3 | **Ambiente x86_64 vs aarch64** (review-18199ddc F2, MEDIUM) | docs/report/requirements corrigidos para **Linux, aarch64** (Ubuntu 24.04) | `requirements.txt:15`; `solution/README.md:17-20`; report §3 |
| 4 | **Runtime ~64–66 s vs 67–75 s** (review-f1fa7caa F6, review-4179846c F2) | Documentado como **faixa observada ~65–75 s** com rótulo "aproximação, não benchmark" (não é medição de benchmark) | `solution/README.md` §6; report §6 |
| 5 | **Contagens 41 e 46/46** (review-f1fa7caa F2/F3, review-4179846c F1, review-18199ddc F3) | `DERIVED`=40 com contagem **derivada** de `$(words $(DERIVED))` no Makefile (impressa pelo target); outputs regeneráveis=**45** (40 derivados + 5 raw); `solution/README.md` estático separado; claims 41/46 removidas de decisões/report/plano/checklist | `Makefile` (clean-derived); `solution/README.md` §4/§8; decisions D1/D4; report §2/§4/§5 |
| 6 | **Colisão de uid `B4-md-README.md`** (review-18199ddc F4) | uids por **path relativo** (`B4-md-data/raw/README.md`, `B4-md-data/processed/README.md`) + **gate D7-uids** que falha se qualquer id de check se repetir (check nº 68, registrado por último) | `06_verify_pipeline.py` (b_parseable; `check_uid_uniqueness`; main) |
| 7 | **Makefile `python3` fixo** (review-f1fa7caa F5, review-4179846c F3, review-18199ddc F7) | `PYTHON ?= python3` + `export PYTHON` no Makefile; `verify`/`stage-01..05` usam `$(PYTHON)`; README documenta `PYTHON=... ./run.sh` e `make PYTHON=...`; exit 2 do `make verify` (encapsulamento do GNU make) documentado, não forçado | `Makefile:6-12,24-40`; `solution/README.md` §3/§7 |
| 8 | **Warnings pandas/matplotlib no stderr** (review-18199ddc F6) | Verificado: não vêm de cache/diretório não gravável (são dependências opcionais antigas do site-packages) → **documentados como benignos** no troubleshooting; nada suprimido (nenhum warning analítico escondido) | `solution/README.md` §9 |
| 9 | **Mensagem de falha do run.sh** (review-18199ddc F1, review-4179846c F4) | Qualificada: relatório é regravado com FAILs apenas em falhas tratadas (schema/validação); falha inesperada pode ter traceback e relatório stale — declarado com honestidade | `run.sh:83-86` |
| 10 | D5 "promete mais do que executa" (review-f1fa7caa F4) | Wording do detalhe: extras são **informativos, não bloqueiam** (sem mudança de comportamento) | `06_verify_pipeline.py` D5 |

## 3. Validações pós-correção (detalhe no review-fix report)

- **Clone fresco** (overlay exato da árvore a commitar, isolado de `/tmp/opencode/ravendata`): `./run.sh` 2× + `make all` + CWD externo + regeneração pós-`clean-derived` — **45/45 outputs byte-idênticos** ao baseline em todas as comparações; verificador **68 PASS / 0 FAIL** em todos os runs; **zero `__pycache__`** após tudo (incl. invocação direta 2×); `clean-derived` removeu exatamente **40** arquivos com raw/process-log intactos; runtime 64–66 s nesta máquina (faixa observada geral 65–75 s); memória 127,7/136,5/181,0/170,5/129,2 MB (bate com a tabela).
- **Cenários de FAIL (todos exit nonzero, 0 tracebacks, sem stale):** dado ausente (exit 1, preflight); python ausente (fake exit 127 → "Python >= 3.11 exigido"); deps ausentes (fake sem pandas → mensagem útil); schema quebrado (usage_date renomeada → 5 FAILs estruturados + relatório regravado, pipeline parado); **categórico inválido accounts `churn_flag=TruX`** (C01-churn FAIL "não executado (validação)", relatório com FAIL=1, exit 1); **categórico inválido subscriptions `churn_flag=TruX`** (D04+C02 FAIL); corrupção composta (t16 removida + PNG pruned recriado + panel `winner_mrr=-999` + raw alterado → **9 FAILs estruturados** A5/A6/A7/B2/C2/C3/C4/C5/C6; verificador direto exit 1; `make verify` exit 2 documentado; `run.sh` propaga exit 1; gate interno do estágio 03 também pegou raw alterado).
- **Gate D7-uids:** testado por injeção de duplicata (`A1-raw`) → detectado ("ids duplicados=['A1-raw']").
- **Override PYTHON:** `make verify PYTHON=<wrapper>` executa com o interpretador alternativo (exit 0).
- **Baseline:** 44/44 arquivos de output rastreados + READMEs byte-idênticos aos blobs commitados; 6 PNGs íntegros; zero alteração de output analítico (regra 9).

## 4. Riscos remanescentes (handoff It07)

1. **Pin exato (residual, D1):** pandas 3.0.5/matplotlib 3.11.1 exigem Python ≥ 3.11 — preflight falha com mensagem clara em Python 3.10 (comportamento pretendido).
2. **Corrupção de valor fora das colunas booleanas mascaradas:** guards cobrem os domínios usados em masking (churn_flag/is_trial/is_reactivation/upgrade/downgrade); colunas booleanas não mascaradas (ex.: `auto_renew_flag`) não têm guard próprio — risco baixo (nenhum crash existe hoje); It09 pode estender.
3. **Warnings pandas/matplotlib em ambientes com deps opcionais antigas:** documentados como benignos (não suprimidos).
4. **Varredura D2 com tokens fixos:** falso negativo possível para paths não canônicos; re-checado por iteração (checklist F2).
5. **Time budget:** acumulado acima do gatilho de contenção (registrado em F11; decisão consciente por gates obrigatórios).
6. **It07:** relatório executivo deve citar os 45 outputs regeneráveis + verificador como gate de QA; números das It03–05 permanecem válidos (outputs byte-idênticos).

## 5. Gate It06

**CONCLUDED** — 3 veredictos `PASS_WITH_FIXES`/`PASS`/`PASS_WITH_FIXES`; findings materiais (categórico inválido com crash+stale; ambiente aarch64) e correções de contagens/pycache/uid/Makefile/runtime/warnings aplicadas com revalidação completa em clone fresco (45/45 byte-idênticos, 68 PASS/0 FAIL, zero pycache, cenários de FAIL sem traceback/stale, run.sh propaga). Iteração 07 permanece **PENDING** (não iniciada).
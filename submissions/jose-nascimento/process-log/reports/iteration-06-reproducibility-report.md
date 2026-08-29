# Report da Iteração 06 — Reproducibilidade e execução em um comando

- **Executor:** agente único `deepseek-max` (via OpenCode Go), conforme plano de execução (regra 1).
- **HEAD base:** `e0c6b7ec582aa1e356d8e05e3afb99edaebdbbd2` (esperado no prompt) — confirmado no início (working tree limpo, branch `submission/jose-nascimento`).
- **Prompt integral:** `process-log/prompts/iteration-06-prompt.md` (arquivado antes da implementação).
- **Decisões:** `process-log/decisions/iteration-06-reproducibility-decisions.md` (D1–D10; trade-off pin exato vs faixas registrado).
- **Tempo de relógio:** ~1h15min (leitura de contexto + verificação de imports/versões + implementação do verificador/run.sh/Makefile + validações + documentos).

---

## 1. Contexto e entradas

- Prompt da It06 (arquivado); plano de execução e checklist do orquestrador;
  scripts 01–05 (8.110 linhas); evidence 01–05; contrato analítico (gates G1–G15);
  manifests commitados (`data/raw/README.md` com MD5/contagens; `data/processed/README.md`
  com linhas/MD5); `.gitignore`; `requirements.txt` original (6 pacotes).
- **Inspeção de imports (tarefa 1):** todos os scripts usam apenas stdlib + `pandas`
  (01–05 e o verificador); `matplotlib` (Agg) nos scripts 03/04. Zero imports de
  `duckdb`, `seaborn`, `jupyterlab`, `numpy` (grep `np.` = 0). Zero `datetime.now()/
  today()/random/uuid` (determinismo independente de locale/TZ). Zero rede.

## 2. Implementação (arquivos criados/alterados)

| Arquivo | Papel |
|---|---|
| `requirements.txt` | minimizado: `pandas==3.0.5`, `matplotlib==3.11.1` (pins exatos; comentário com justificativa) |
| `run.sh` | pipeline em 1 comando: `set -euo pipefail`, resolve path próprio (qualquer CWD), preflight Python/deps/data, estágios 01→05 com propagação de exit code, medição tempo (SECONDS) + pico de memória (ru_maxrss), verificador ao final, resumo curto; `PYTHONDONTWRITEBYTECODE=1` |
| `Makefile` | `all` = `./run.sh` (fonte única, sem lógica duplicada); `verify` = só o verificador; `stage-01..05`; `clean-derived` com lista explícita (40 arquivos — contagem derivada de `$(words $(DERIVED))`, não hardcoded) + guards; exporta `PYTHONDONTWRITEBYTECODE`; `PYTHON ?= python3` em todos os targets |
| `solution/src/06_verify_pipeline.py` | verificador read-only (stdlib + pandas; 68 checks): manifesto (A), parseabilidade (B), consistência com contratos commitados (C), higiene (D), sanidade compile/import (E), gate de ids de check únicos (D7); exit 0/1 com diagnóstico estruturado, zero traceback; `sys.dont_write_bytecode` para invocação direta não gerar `__pycache__` |
| `solution/README.md` | setup Linux/macOS, venv opcional, pip install, 1 comando, outputs, estrutura, tempo/memória medidos, troubleshooting, definições/lenses, licença/dados inclusos |

## 3. Ambiente e versões (documentadas)

| Item | Valor |
|---|---|
| OS | Linux (Ubuntu 24.04, **aarch64**) |
| Python | 3.12.3 (testado; exigência mínima documentada: >= 3.11) |
| pandas | 3.0.5 (pin exato) |
| matplotlib | 3.11.1 (pin exato) |
| bash | 5.x (`bash -n` OK) |
| make | GNU Make (4.x) |
| shellcheck | **não disponível — não instalado** (regra 6 do prompt); cobertura via `bash -n` |
| /usr/bin/time | não disponível → memória via `resource.ru_maxrss` (aproximação declarada) |

## 4. Validações executadas (pré-commit, no working tree)

| Validação | Comando | Resultado |
|---|---|---|
| 1ª execução | `./run.sh` | exit 0; estágios 72 PASS/18 WARN/0 FAIL · 31/1/0 · 23/0/0 · 34/0/0 · 45/0/0; verificador 68 PASS/0 FAIL; **45/45 outputs byte-idênticos** ao commitado (40 derivados + 5 raw; README estático à parte) |
| 2ª execução (determinismo) | `./run.sh` | exit 0; outputs MD5 idênticos à 1ª (45/45) |
| `make all` (fonte única) | `make all` | exit 0; outputs MD5 idênticos (45/45) |
| CWD diferente | `run.sh` a partir de `/tmp` (path absoluto) | exit 0; outputs MD5 idênticos (45/45) |
| `make verify` | de outro CWD | exit 0; 68 PASS/0 FAIL |
| Tree pós-regeneração | `git status --porcelain` | somente `requirements.txt` (modificado de propósito); zero untracked (sem `__pycache__`) |
| `bash -n` + `git diff --check` | — | OK |
| compile/imports | verificador E1/E2 | 6/6 scripts compilam e importam |
| `make clean-derived` + regeneração | sandbox | apaga só a lista explícita (40 arquivos); `data/raw/` (6 arquivos) e `process-log/` intactos; `./run.sh` regenera 45/45 byte-idênticos |
| FAIL — dado ausente | sandbox (`ravenstack_accounts.csv` removido) | exit 1; mensagem útil ("dado bruto ausente ou vazio" + lista); **0 tracebacks**; nada executado (stale-free) |
| FAIL — schema quebrado | sandbox (coluna `usage_date` renomeada) | exit 1; estágio 01 com 5 FAILs estruturados e relatório regravado ("não executado (schema)"); pipeline parou; **0 tracebacks** |
| FAIL — python/deps ausentes | sandbox (python3 fake exit 127) | exit 1; mensagem útil ("Python >= 3.11 exigido..."); 0 tracebacks |
| FAIL — verificador contra estado corrompido | sandbox (t16 removida; PNG pruned recriado; winner_mrr = -999; MD5 alterado) | exit 1; **9 FAILs estruturados** (A5/A6/A7/B2/C2/C3/C4/C5/C6); 0 tracebacks |
| Locale/TZ | inspeção | zero `now()/today()/tz`; datas naive; formatação pt-BR explícita (nunca locale) |

## 5. Determinismo (hashes e tree)

- MD5 capturados antes da 1ª execução vs depois de: 1ª execução, 2ª execução,
  `make all`, CWD diferente e regeneração pós-`clean-derived` — **45/45
  idênticos em todas as comparações** (evidence 01–05, account_month + README
  processado, contrato, 26 tabelas, 6 PNGs, 5 raw). O `solution/README.md` é
  estático (não regenerado) e fica fora da contagem de outputs.
- `git status` após regenerações: limpo exceto o `requirements.txt` pretendido.
- PNGs: exatamente 6, byte-idênticos; os 4 pruned (gate It04) ausentes (checados
  pelo verificador A5/A6).

## 6. Tempo e memória (medidos; aproximação declarada, não benchmark)

Pipeline completo: **~65–75 s** de relógio (faixa observada em execuções
repetidas nesta máquina e em revisões independentes; varia com máquina/carga).

| Estágio | Tempo | Pico (ru_maxrss) |
|---|---|---|
| 01_ingest_audit | ~1 s | ~125 MB |
| 02_reconcile_churn | ~50 s | ~134 MB |
| 03_root_cause | ~6 s | ~176 MB |
| 04_lifecycle_watchlist | ~4 s | ~167 MB |
| 05_actions_impact | ~1–2 s | ~126 MB |
| 06_verify_pipeline | ~1 s | — |

> ru_maxrss = pico do processo filho (RUSAGE_CHILDREN), KB no Linux / bytes no
> macOS (normalizado). Aproximação honesta, **não** benchmark universal.

## 7. Erros reais encontrados e corrigidos (nunca "não houve erros")

1. **Verificador casava consigo mesmo** — a varredura de paths pessoais (D2)
   encontrava `/tmp`, `/home`, `ubuntu`, `josenascimento` no próprio
   `06_verify_pipeline.py` (lista de tokens literal). **Causa raiz:** scanner
   varre o próprio código-fonte. **Correção:** tokens compostos em runtime
   (`"/"+"tmp"`, `"ub"+"untu"` etc.) — nenhum literal completo existe no fonte
   (decisão D9).
2. **Gate FAIL de reports 01/02 mal interpretado** — reports 01/02 documentam a
   semântica de `FAIL` em prosa e têm linha-resumo legítima `| FAIL | 0 |`; a
   checagem ingênua "sem `**FAIL**`" falhava. **Correção:** verificação pelo
   formato real de cada report: tabela-resumo (`| Resultado | Quantidade |`)
   para 01/02; linhas de gate (`**PASS**`/`**FAIL**`, `| PASS |`) para 03–05
   (decisão D10).
3. **Reports 04/05 sem markers negrito** — usam `| PASS |` (célula de tabela),
   não `**PASS**`. **Correção:** `PASS_MARKER` aceita ambos os formatos.
4. **`diff` de MD5 com path relativo confundiu comparação** (erro de verificação,
   não do pipeline) — hashes idênticos, paths relativos vs absolutos. **Correção:**
   comparação re-executada com paths absolutos: 45/45 idênticos.
5. **`__pycache__` pré-existente no working tree** (ignorado, nunca commitado) —
   a checagem D1 do verificador o reportava. **Correção:** removido localmente;
   `run.sh`/`Makefile` exportam `PYTHONDONTWRITEBYTECODE=1` para nunca recriar
   (decisão D6).

## 8. Clone fresco (pós-commit) e handoff

- **Metodologia:** clone local da branch `submission/jose-nascimento` em sandbox
  **sem** copiar `/tmp/opencode/ravendata`; `./run.sh` usando somente os raw
  commitados; verificação de tree limpa e byte-idempotência. Executado após o
  commit `build: one-command reproducible pipeline` (hash registrado após o push,
  conforme prática das Iterações 04–05); resultados no report final da iteração
  (resposta do executor) e no review gate 3x da It06.
- **Handoff It07:** `solution/README.md` e `run.sh` são a base da entrega; o
  relatório executivo (It07) pode citar os artefatos regeneráveis e o verificador
  como gate de QA; nenhum output analítico mudou (45/45 byte-idênticos), então os
  números das Iterações 03–05 permanecem válidos.

## 10. Adendo — correções do review gate 3x (2026-08-29)

- **Reviewers:** 3 revisores read-only (review-f1fa7caa, review-4179846c,
  review-18199ddc); veredictos `PASS_WITH_FIXES` / `PASS` / `PASS_WITH_FIXES`;
  ledger em `process-log/reviews/iteration-06-review-summary.md`; detalhe das
  correções em `process-log/reports/iteration-06-review-fix-report.md` e nas
  decisões D11–D17.
- **Correções aplicadas (sem alterar nenhum output analítico):**
  1. **Categórico inválido** (review-18199ddc F1, MEDIUM): `01_ingest_audit.py`
     ganhou `BOOL_COLUMNS`/`guard_bools` — valor não-booleano (ex.: `churn_flag=
     TruX`) vira FAIL estruturado "não executado (validação)" nos checks que
     mascaram booleano (D04/C01/C02/C03/C07/C08), relatório regravado, exit 1,
     sem traceback e sem catch-all (testado em accounts e subscriptions).
  2. **`__pycache__` na invocação direta** (review-f1fa7caa F1, MÉDIO):
     `sys.dont_write_bytecode = True` no verificador — invocação direta 2× em
     clone limpo comprovada sem pyc e sem D1 auto-falhar.
  3. **Ambiente** (review-18199ddc F2, MEDIUM): `aarch64` (não x86_64) nas
     docs/report/requirements; runtime como faixa observada ~65–75 s
     ("aproximação, não benchmark").
  4. **Contagens** (F2/F3): `DERIVED`=40 derivado de `$(words $(DERIVED))`;
     outputs regeneráveis=45 (40 derivados + 5 raw); README estático separado;
     claims 41/46 removidas.
  5. **uids do verificador** (review-18199ddc F4): B4 por path relativo + gate
     D7-uids (duplicata vira FAIL) — verificador agora com 68 checks.
  6. **Makefile/PYTHON** (F5/F3/F7): `PYTHON ?= python3` em `verify`/`stage-*`;
     override documentado; exit 2 do `make verify` documentado (semântica make).
  7. **Warnings de pandas/matplotlib** (review-18199ddc F6): não vêm de cache —
     documentados como benignos no troubleshooting; nada suprimido.
  8. **Mensagem de falha do run.sh** (review-18199ddc F1/review-4179846c F4):
     qualificada — relatório é regravado apenas em falhas tratadas; falha
     inesperada pode ter traceback e relatório stale (declarado com honestidade).
- **Revalidação pós-correção:** clone fresco (sem ravendata) 2× `./run.sh` +
  `make all` + CWD externo + verificador direto 2× + `clean-derived`: 45/45
  byte-idênticos, tree limpa, zero `__pycache__`, 68 PASS/0 FAIL; cenários de
  falha (arquivo/schema/categórico/python/deps/verifier corrompido) sem
  traceback e sem stale; detalhe no review-fix report.

## 9. Estados (atualizados no plano/checklist)

- **It06 `CONCLUDED`** (implementação + validações acima; critérios de aceitação
  do prompt atendidos: run.sh em execução repetida, make all igual, 2×
  determinista, verifier passa/falha corretamente, dependências mínimas, docs de
  setup, sem outputs extras, process/git completos).
- **Review gate 3x da It06: `PENDING`** (dispara em seguida; ledger em
  `process-log/reviews/` quando concluído).
- It07–It10: `PENDING`.
- Checklist: C3/C6/F2/F5/F10 atualizados com evidência da It06; F11 atualizado
  (tempo desta iteração).
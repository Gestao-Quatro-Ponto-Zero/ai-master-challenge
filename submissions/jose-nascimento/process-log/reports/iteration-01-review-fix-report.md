# Report — Correção Sequencial do Review Gate · Iteração 01

- **Iteração:** 01 (review gate 3x — correção sequencial)
- **Data:** 2026-08-28
- **Executor:** este agente corretor sequencial `deepseek-max` (subagente via OpenCode Go), sob orquestração do opencode
- **Prompt integral desta correção:** [`process-log/prompts/iteration-01-review-fix-prompt.md`](../prompts/iteration-01-review-fix-prompt.md) (transcrição fiel)
- **Commit revisado:** `80f6a3f4e8a94034173226d848fecf179bc9b031`
- **Commit desta correção:** `fix: handle schema failures in data audit` (hash completo verificado após o commit e reportado ao orquestrador)
- **Status:** PASS

---

## 1. Objetivo

Corrigir o finding convergente M1 (MEDIUM, 3/3 revisores) — caminho de FAIL por schema quebrado crashava com `KeyError`/traceback e não regravava `solution/evidence/01_audit_report.md` (relatório stale) — e os LOWs convergentes factuais, sem refatoração ampla, sem catch-all e sem iniciar a Iteração 02.

## 2. Workflow executado

1. `git status`/`git log`/`rev-parse` (HEAD `80f6a3f…` confirmado; tree limpo; nada alheio a reverter).
2. Leitura integral dos 3 reports de revisão (`review-38738f37.md`, `review-44ca5ff5.md`, `review-caef990c.md`), do script (763 linhas), do relatório versionado, do report/prompt da Iteração 01, do execution-plan, do orchestrator-checklist, do review summary da Iteração 00 e das instruções oficiais (README, CONTRIBUTING, submission-guide, challenge 001, template).
3. Sandbox `/tmp/opencode/fix-sandbox-01/` (cópia da pasta da submissão, fora do repo): verificação independente do L-C (21 IDs duplicados → 21/21 assinaturas diferentes, **19/21** features diferentes, máx. 2 linhas/ID — confirma o finding do revisor 2).
4. Correção do script (guards de coluna + LOWs — detalhe em §3).
5. Testes em sandbox (§4): baseline ×2 + 4 cenários de FAIL + extra arquivo vazio + determinismo no caminho de FAIL.
6. Reexecução do baseline no repo; conferência de que os números materiais ficaram idênticos; novo checksum registrado (§5).
7. Atualização de governança (execution-plan, orchestrator-checklist, report da Iteração 01 — somente fatos) e criação dos artefatos de gate (review summary, prompt arquivado, este report).
8. Validações finais (§6), commit e push (§7).

## 3. Patch — causa raiz e mudanças

**Causa raiz (M1):** os checks acessavam colunas (`df[key]`, `df["seats"]`, `df["industry"]`, `df[col]` em `check_ids`, colunas de data, colunas em `check_cross_tables` e em `collect_syntheticity_evidence`) sem verificar presença após `S01` registrar FAIL; `render_report`/`write_text` só rodavam no fim de `main()`, então qualquer coluna ausente abortava antes da gravação — relatório antigo permanecia (stale).

**Correção (mínima e robusta, sem catch-all):** três helpers novos (`missing_cols`, `guard_columns`, `cross_blocked` — `01_ingest_audit.py:132-171`) e guardas granulares por check:

- **`check_schema`** (`:219-240`): S02/S03 só executam se a chave existir; se faltar, registram `FAIL "não executado (schema): coluna X ausente"` (não esconde o FAIL).
- **`check_types_ranges`/`check_ids`/`check_dates`/`check_global_window`** (`:262-505`): cada check emite `FAIL "não executado (schema): colunas ausentes: [...]"` quando falta alguma coluna de que depende; checks com colunas presentes continuam rodando (ex.: com `industry` ausente, T01 seats e T02 country/referral/plan ainda executam).
- **`check_cross_tables`** (`:513-822`): cada check cross-table (K01–K05, D06–D11, C01–C09) guardado com `cross_blocked` (arquivo/coluna ausente → FAIL estruturado).
- **`collect_syntheticity_evidence`** (`:824-927`): evidências §5 com guardas; aspectos não executáveis ficam explícitos ("não executado (schema): coluna ausente").
- **Sem catch-all:** nenhum `try/except` genérico foi adicionado — bugs reais de lógica continuam propagando (traceback + exit != 0), apenas acessos a colunas são guardados.

**LOWs convergentes (factuais, baixo risco):**

| Mudança | Local |
|---|---|
| C01/C02/C09 condicionais (PASS quando divergência = 0; WARN quando > 0) — na base atual seguem WARN (35/277, 125, 439/363) | `01_ingest_audit.py:693, 711, 816` |
| S02/S03: "chave candidata" no lugar de "chave primária" (`usage_id` não é a chave do brief para `feature_usage`) | `01_ingest_audit.py:224-235` |
| Evidência §5: reuso de IDs com precisão 21/21 assinaturas e **19/21** features (calculado dinamicamente) | `01_ingest_audit.py:874-881` |
| Descrição C05 corrigida ("reason_code 'unknown' **sem** feedback preenchido") | `01_ingest_audit.py:748-754` |
| execution-plan: commit esperado da Iteração 01 sincronizado com o commit real (`feat: ingest and audit RavenStack datasets`, `a40e129`) | `execution-plan.md:84` |
| Prose do report da Iteração 01 alinhada (chaves candidatas; 19/21) | `iteration-01-ingest-audit-report.md:65,82` |

**Não alterado (decisão):** C03/C06 permanecem checks de medição `PASS` (condicioná-los mudaria as contagens materiais 72/18/0); semântica de `closed_at` nulo e wording "colunas do brief"/"76,6%" aceitos conforme justificativa no review summary §5.

## 4. Testes (sandbox `/tmp/opencode/fix-sandbox-01/`, fora do repo)

| Cenário | Resultado | Outputs |
|---|---|---|
| Baseline execução 1 | exit 0 | `PASS=72 WARN=18 FAIL=0`; MD5 `7af8b9b0a710e494bd169ae3f72dd512` |
| Baseline execução 2 (idempotência) | exit 0 | MD5 idêntico (`7af8b9b0…`); stdout idêntico |
| Diff baseline vs report versionado (HEAD) | só LOWs | 12 pares de linhas: "chave candidata" ×10, C05 ×1, §5 reuso 19/21 ×1; **zero números materiais alterados** |
| Arquivo ausente (`ravenstack_churn_events.csv` removido) | exit 1, sem traceback | report regravado; `PASS=57 WARN=11 FAIL=1`; F01 "arquivo ausente" |
| Coluna-chave ausente (`account_id`→`acct_id` em accounts) | exit 1, sem traceback | report regravado; `PASS=64 WARN=14 FAIL=12` (S01 + S02/S03/I01/K01/K02/K03/D06/D07/D08/C01/C09 "não executado (schema)"); idempotente (MD5 `fb33f1cc…` ×2) |
| Coluna categórica ausente (`industry`→`industria` em accounts) | exit 1, sem traceback | report regravado; `PASS=70 WARN=18 FAIL=2` (S01 + T02-industry); checks possíveis preservados; §5 com nota |
| Data inválida (`usage_date=NOTADATE` em feature_usage) | exit 1, sem traceback | report regravado; `PASS=71 WARN=18 FAIL=1`; D01 "1 valores não parseáveis" |
| Extra — arquivo vazio (0 bytes) | exit 1, sem traceback | report regravado; F01 "arquivo vazio (0 bytes)" |

Determinismo verificado também no caminho de FAIL (fail2 executado 2×, mesmo MD5). Exit 1 sempre que há FAIL.

## 5. Baseline no repo — estabilidade dos números

Reexecução a partir da pasta da submissão: exit 0; `72 PASS / 18 WARN / 0 FAIL`; idempotente. Comparação byte-a-byte com o relatório versionado anterior (`719663ced05be97dc0235a02a7637d40`): únicas diferenças são os textos LOW corrigidos (§4) — todos os números materiais (contagens, nulos, FKs, janelas, divergências, distribuições) permanecem **idênticos**. **Novo checksum do relatório: `7af8b9b0a710e494bd169ae3f72dd512`** (registrado no review summary §9; o checksum antigo permanece como registro histórico no report da Iteração 01 §9).

## 6. Validações executadas

| Validação | Resultado |
|---|---|
| `python3 -m py_compile` + parse AST do script | PASS |
| Baseline idempotente (2× no sandbox + 2× no repo) | PASS — mesmo MD5 |
| 5 cenários exigidos + extra (vazio) | PASS — exit 0/1 corretos, report sempre regravado, zero tracebacks |
| `git diff --check` | PASS — limpo |
| Escopo: apenas arquivos dentro de `submissions/jose-nascimento/` | PASS |
| Estados válidos (`PENDING\|OPEN\|CONCLUDED`) em plano e checklist | PASS |
| Grep de traceback (`Traceback`, `KeyError` não estruturado) nos artefatos | PASS — zero ocorrências em artefatos da solução |
| Grep de paths pessoais/segredos (`/tmp`, `/home`, `ubuntu`, `api_key`/`token`/`secret`) nos artefatos da solução | PASS — zero fora do prompt arquivado (exceção documentada da Iteração 00) |
| References markdown (links relativos do summary/report) | PASS |
| Matriz de findings completa (M1 + 5 LOWs → ação; LOWs aceitos justificados) | PASS |
| `git status`/`git diff` antes do commit | PASS — somente arquivos pretendidos |

## 7. Git

- **Antes:** HEAD `80f6a3f4e8a94034173226d848fecf179bc9b031`, tree limpo, tracking `origin/submission/jose-nascimento` up to date.
- **Commit:** `fix: handle schema failures in data audit` — autor do candidato (`Jose Nascimento <322186960+josenascimento1@users.noreply.github.com>`), sem alteração de `git config`, sem amend/force-push.
- **Arquivos no commit:** `solution/src/01_ingest_audit.py` (M), `solution/evidence/01_audit_report.md` (M — regenerado), `process-log/management/execution-plan.md` (M), `process-log/management/orchestrator-checklist.md` (M), `process-log/reports/iteration-01-ingest-audit-report.md` (M), `process-log/reviews/iteration-01-review-summary.md` (A), `process-log/prompts/iteration-01-review-fix-prompt.md` (A), `process-log/reports/iteration-01-review-fix-report.md` (A).
- **Push:** `origin submission/jose-nascimento`; validação pós-push: `git ls-remote origin submission/jose-nascimento` == hash local; tracking up to date; working tree limpo.

## 8. Decisões desta correção

| Decisão | Registro |
|---|---|
| Guards granulares por check em vez de short-circuit por arquivo ou try/except | Preserva checks possíveis (exigência do prompt); nenhum catch-all (bugs reais continuam propagando) |
| Checks não executáveis registram `FAIL "não executado (schema)"` em vez de serem omitidos | Não esconde FAIL; diagnóstico estruturado e determinístico |
| C03/C06 permanecem `PASS` de medição | Condicioná-los alteraria os números materiais 72/18/0; registrado no summary §5 |
| Report da Iteração 01 tratado como histórico; só as duas claims factuais LOW foram ajustadas | Consistência docs ↔ código sem reescrever história (precedente Iteração 00) |
| Checksum antigo preservado como registro histórico; novo checksum registrado nos artefatos do gate | Evidência honesta |

## 9. Riscos residuais

- Determinismo vs versão de pandas (dtypes `str` vs `object` em pandas 2.x) — pinning na Iteração 06.
- WARNs de medição C03/C06 hardcoded `PASS` e assimetria de nulos `closed_at` (latente) — sem impacto na base atual; contrato analítico (Iteração 02).
- Anomalias temporais (76,6% uso pré-start; 13.198 pré-signup) — regras de janela no contrato analítico (Iteração 02).
- Reconciliação de churn (35/277/125; 175 multi-evento; 61 reativações) — insumo da Iteração 02; grão account-month com invariantes.
- `requirements.txt` sem pinning — Iteração 06.
- Push/rede — commit verificado em `origin`; risco residual apenas para iterações futuras.

## 10. Handoff — Iteração 02

O gate da Iteração 01 está **concluído** (3 veredictos `PASS_WITH_FIXES`, finding M1 corrigido e validado nos 5 cenários, LOWs convergentes corrigidos, gate `CONCLUDED` no ledger). O orquestrador (opencode) pode disparar a **Iteração 02 — Reconciliação das definições/grãos de churn e contrato analítico**, conforme o handoff do report da Iteração 01 (§11): entradas `solution/evidence/01_audit_report.md` (checks C01/C02/C03), `solution/data/raw/` e o execution-plan (critérios da Iteração 02). **Nada da Iteração 02 foi iniciado nesta correção.**
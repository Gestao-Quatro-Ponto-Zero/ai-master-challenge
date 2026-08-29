# Prompt integral — Agente Corretor Sequencial do review gate da Iteração 06 (arquivado)

**Data:** 2026-08-29 · **Agente:** corretor sequencial `deepseek-max` (DeepSeek V4 Flash, max reasoning, via OpenCode Go) · **Commit esperado:** `fix: harden fresh-clone pipeline verification`

> Transcrição fiel do prompt recebido (padrão de arquivamento dos gates anteriores).

---

Você é o AGENTE CORRETOR SEQUENCIAL da ITERAÇÃO 06. Corrija findings materiais/contagens, valide em clone fresco e feche o gate. NÃO inicie It07.

REPO
- `/tmp/opencode/ai-master-challenge-work`, branch `submission/jose-nascimento`, pasta única `submissions/jose-nascimento/`, HEAD `9357c202bbd4b5739fd8dc44420c66f2c9e4b9e6`.

REVISÕES
- `/tmp/opencode/ai-master-review-reports/iteration-06/review-f1fa7caa.md`
- `/tmp/opencode/ai-master-review-reports/iteration-06/review-4179846c.md`
- `/tmp/opencode/ai-master-review-reports/iteration-06/review-18199ddc.md`
Leia integralmente, mais run/Make/verifier/docs/reports/scripts.

CORREÇÕES
1. **pycache:** invocação direta documentada `python3 solution/src/06_verify_pipeline.py` não pode criar `solution/src/__pycache__` nem fazer D1 auto-falhar. Corrija o verificador/py_compile para usar temp cfile ou desabilitar bytecode de forma robusta; teste invocação direta em clone limpo 2×, zero pyc/cache, exit 0.
2. **valor categórico inválido:** `01_ingest_audit.py` não pode explodir KeyError/traceback/stale quando schema existe mas `churn_flag` contém `TruX` (ou categoria inválida equivalente). Faça guard/validation mínimo: registre FAIL estruturado, gere report atualizado, exit 1, sem catch-all que esconda bugs. Teste pelo menos accounts churn_flag inválido e outro categórico relevante.
3. Corrija arquitetura do ambiente: medições foram em Linux **aarch64**, não x86_64. Runtime como faixa aproximada observada (~65–75s), não benchmark.
4. Corrija contagens dinamicamente: `DERIVED`=40; regeneráveis analíticos=45 (README estático separado); remova claims 41/46. Não hardcode na narrativa quando pode derivar.
5. Corrija colisão de uid `B4-md-README.md` no verifier para IDs/path únicos e gate que detecte duplicate check IDs.
6. Makefile deve respeitar `PYTHON ?= python3` em targets individuais/verify e docs devem explicar override; `make verify` encapsula exit 1 do Python como exit 2 do make — documente, não force sem necessidade.
7. Warnings de cache pandas/matplotlib: se vêm de diretório não gravável, configure cache local temporário/seguro apenas se necessário e sem gerar untracked; senão documente stderr benigno. Não esconda warning analítico.

TESTES
8. Fresh clone sem ravendata: run 2×, make all, CWD externo, direct verifier 2×, clean-derived; 45 outputs byte-idênticos/tree limpa/zero pycache; 6 PNG.
9. Failures: file/schema/categorical invalid/python/deps/verifier corruption; no traceback/stale; run propaga.
10. `bash -n`, pycompile sem cache, imports, diff-check, scope, links, secrets; outputs analíticos byte-idênticos no baseline.

EVIDÊNCIA
11. Crie `process-log/reviews/iteration-06-review-summary.md`; prompt `process-log/prompts/iteration-06-review-fix-prompt.md`; report `process-log/reports/iteration-06-review-fix-report.md`; adendo decisions/report; checklist gate It06 CONCLUDED, It07 PENDING.

GIT
- Só pasta; commit `fix: harden fresh-clone pipeline verification`; sem amend/force/config/destrutivo; push/local==remote/tree limpo.

FINAL
PASS/BLOCKED; hash/push; matriz; categorical fail/pycache proof; counts/platform/runtime; clone tests; files/risks/handoff It07. BLOCKED se direct verifier criar pycache ou invalid category deixar report stale.
# Prompt — Agente Corretor Sequencial do review gate da Iteração 08 (arquivado)

**Data:** 2026-08-29 · **Agente:** corretor sequencial `deepseek-max` (DeepSeek V4 Flash, max reasoning, via OpenCode Go) · **Commit esperado:** `docs: reconcile process log review evidence`

> **Transcrição fiel com paths operacionais normalizados:** transcrição fiel do prompt recebido do orquestrador (padrão de arquivamento dos gates anteriores). **Categorias normalizadas (2):** `<repo-workdir>` — path absoluto do repositório de trabalho; `<review-reports-dir>` — path absoluto do diretório externo dos reports brutos de revisão (working artifacts fora do repo). **Por quê:** política F2/It08 — zero paths de máquina em docs novos; o avaliador deve re-ler o prompt sem conhecer o ambiente do candidato. Todo o restante é transcrito fielmente.

---

Você é o AGENTE CORRETOR SEQUENCIAL da ITERAÇÃO 08. Corrija imprecisões documentais, feche o gate 3x e preserve autenticidade. NÃO inicie QA It09.

REPO
- `<repo-workdir>`, branch `submission/jose-nascimento`, pasta única `submissions/jose-nascimento/`, HEAD `9e603159fa0a2275efcc31ae56c3943b7b484137`.
Leia process docs, checklist F11, evidence index, README, errors ledger, It04 summary.

REVISÕES
- `<review-reports-dir>/iteration-08/review-edba2342.md`
- `<review-reports-dir>/iteration-08/review-8a66fb81.md`
- `<review-reports-dir>/iteration-08/review-a306a10d.md`

CORREÇÕES
1. `iteration-08-prompt.md` e referências: não diga "prompt integral" se 2 paths foram normalizados. Use **"transcrição fiel com paths operacionais normalizados"**, explique quais categorias foram normalizadas e por quê; não restaure paths de máquina.
2. F11/time budget: remova soma pontual inconsistente. Reconcilie reports por iteração se possível; caso fontes sejam estimativas não aditivas, use faixa honesta (ex.: ~20–24h de execução documentada) e diga metodologia/limite. Mantenha conclusão inequívoca: excedeu 4–6h por decisão consciente de revisão. Não racionalize.
3. Qualifique todas contagens mutáveis como **snapshot no fechamento da It08**; It09/10 devem regenerar/atualizar o snapshot ou evitar total final estático. Atualize captions em README/evidence-index/process README/report.
4. Corrija detecção dos erros: não use "1/3 em E2–E4" agregado. Registre E2 conforme summaries; E3 conforme reviewers; E4 KM 3/3 e gráfico B 1/3. Derive da evidência.
5. Evidence index: `G1–G11`, não G1–G9.
6. Review summary It04 §10: commit da correção ocular/mapping é `617e4ac...`; `1517a73` é base. Corrija sem reescrever história.
7. Preserve exatamente 8 errors, 18 decisions, checkboxes e attribution. Não copie raw reviews.

EVIDÊNCIA/GATE
8. Crie `process-log/reviews/iteration-08-review-summary.md` com 3 veredictos/paths, findings→ações, auditoria 8 erros/attribution/verifier e gate.
9. Prompt `process-log/prompts/iteration-08-review-fix-prompt.md`; report `process-log/reports/iteration-08-review-fix-report.md`; adendo It08 report/checklist; mark gate It08 CONCLUDED, It09 PENDING.
10. Rode verifier/fresh clone/run 2×; links, hashes, counts snapshot, sem paths/segredos de máquina, exactly 8, report/6 PNG/tables byte-idênticos; fail link/error test.

GIT
- Commit `docs: reconcile process log review evidence`; só pasta, sem amend/force/config/destrutivo; push/local==remote/tree limpo.

FINAL
PASS/BLOCKED; hash/push; matriz; time-range; snapshot wording; E2-E4 correction; process gates; verifier; risks/handoff It09. BLOCKED se attribution/errors/links quebrarem.
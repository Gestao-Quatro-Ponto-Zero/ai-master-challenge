# Prompt — Agente Corretor Sequencial do review gate da Iteração 09 (arquivado)

**Data:** 2026-08-29 · **Agente:** corretor sequencial `deepseek-max` (DeepSeek V4 Flash, max reasoning, via OpenCode Go) · **Commit esperado:** `chore: close pre-submission QA gate`

> **Transcrição fiel com paths operacionais normalizados:** transcrição fiel do prompt recebido do orquestrador (padrão de arquivamento dos gates anteriores). **Categorias normalizadas (2):** `<repo-workdir>` — path absoluto do repositório de trabalho; `<review-reports-dir>` — path absoluto do diretório externo dos reports brutos de revisão (working artifacts fora do repo). **Por quê:** política F2/It08 — zero paths de máquina em docs novos; o avaliador deve re-ler o prompt sem conhecer o ambiente do candidato. Todo o restante é transcrito fielmente.

---

Você é o AGENTE CORRETOR SEQUENCIAL da ITERAÇÃO 09. Corrija somente stale factual dos 3 reviewers, feche gate 3x e deixe estado pronto para auditoria final 5x. NÃO preencha data, NÃO faça commit final It10, NÃO abra PR.

REPO
- `<repo-workdir>`, branch `submission/jose-nascimento`, pasta única `submissions/jose-nascimento/`, HEAD `8e77a88cf9da144a3161e9efec1d66ab8a9dce4f`.

REVISÕES
- `<review-reports-dir>/iteration-09/review-eb90f31b.md`
- `<review-reports-dir>/iteration-09/review-7faed002.md`
- `<review-reports-dir>/iteration-09/review-878b8c24.md`

CORREÇÕES
1. Links: use definição estável/derivada: **252 referências relativas, 0 quebradas** no gate completo (G3 211 + F2 41). Evite claim frágil de nº de arquivos; corrija QA report/plano/checklist onde aparece 244/27.
2. Word counts snapshot pós-It09: README **1.623**, process-log README **2.408**, report executivo 2.275, summary 322; rotule método/snapshot. Se uma edição desta correção alterar README/PL, derive novamente e use valor final — não copie cegamente.
3. Time F11: soma bruta das 16 fatias = **27h40**. Como estimativas podem sobrepor, defina faixa honesta consistente (ex. ~24–28h) com metodologia; não mantenha upper abaixo da soma bruta sem explicar. Conclusão excedeu 4–6h permanece, sem racionalizar.
4. Preserve todos os dados analíticos/solution/report/6 PNG/tables byte-idênticos.

GATE/EVIDÊNCIA
5. Crie `process-log/reviews/iteration-09-review-summary.md`; prompt `process-log/prompts/iteration-09-review-fix-prompt.md`; report `process-log/reports/iteration-09-review-fix-report.md`; atualize plan/checklist/readiness: gate It09 CONCLUDED, It10 PENDING; P1/P2/P3 únicas pendências.
6. Re-derive snapshot pós-fix e rotule como fechamento It09; evite totais que It10 tornará falsos ou diga explicitamente que It10 rederiva.
7. Fresh clone/run/verifier/links/word/time/git/PR absence; no placeholders novos; exactly 8 errors; scope.

GIT
- Commit `chore: close pre-submission QA gate`; só pasta; sem amend/force/config/destrutivo; push/local==remote/tree limpo.

FINAL
PASS/BLOCKED; hash/push; 3 fixes; gate/snapshot; fresh clone/verifier; exact pending; readiness para auditoria final5x. Não abrir PR.
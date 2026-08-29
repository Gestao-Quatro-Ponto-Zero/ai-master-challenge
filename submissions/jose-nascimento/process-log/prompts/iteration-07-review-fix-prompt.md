# Prompt integral — Agente Corretor Sequencial do review gate da Iteração 07 (arquivado)

**Data:** 2026-08-29 · **Agente:** corretor sequencial `deepseek-max` (DeepSeek V4 Flash, max reasoning, via OpenCode Go) · **Commit esperado:** `docs: polish executive report for decision clarity`

> Transcrição fiel do prompt recebido (padrão de arquivamento dos gates anteriores).

---

Você é o AGENTE CORRETOR SEQUENCIAL da ITERAÇÃO 07. Corrija drift/truncamentos, crie margem de concisão e feche o gate 3x. NÃO inicie It08.

REPO
- `/tmp/opencode/ai-master-challenge-work`, branch `submission/jose-nascimento`, pasta única `submissions/jose-nascimento/`, HEAD `a726cb4318d0765565c96e03491b8c9bf79964a7`.

REVISÕES
- `/tmp/opencode/ai-master-review-reports/iteration-07/review-b63ea739.md`
- `/tmp/opencode/ai-master-review-reports/iteration-07/review-91ae8e7b.md`
- `/tmp/opencode/ai-master-review-reports/iteration-07/review-0ceda1fc.md`
Leia relatório/gerador/README/outline/process report/plano/checklist.

CORREÇÕES
1. README: remova número stale "11 commits"; não substitua por outro número que ficará stale. Use "histórico git incremental e semântico" com link/comando se útil.
2. Atualize execution-plan/process report para valores reais após correção (word count, summary, verifier PASS, nº tabelas). Prefira derivações/sem contagem estática se vai mudar.
3. Tabela de ações: nenhuma célula pode terminar no meio de palavra/frase. Gere tabela compacta com campos curtos e completos (ID/quando/owner/entrega/gate); detalhes permanecem na prosa e t18/t20. Não use truncamento silencioso. Gate deve detectar truncation markers/células cortadas.
4. Crie margem de word budget: reduza relatório para alvo **2.150–2.300 palavras** sem remover nenhum requisito/âncora/ask/limitação/conta. Corte redundância, notas repetidas e prosa que já está em tabelas/links. Summary fica 250–350.
5. Explique `lift` na primeira ocorrência em uma frase curta (precision da regra / incidence baseline), se ainda não explícito.
6. Corrija file mode do `report-executivo.md`: geração atomic deve terminar 0644 em Linux/macOS; teste run em clone e `git diff` limpo.
7. Corrija adendo do process report sobre 0–2 p.p.: falso-GO não é arredondamento da auditoria independente; reescreva precisamente ou remova.
8. Não mude números, conclusões, 6 imagens ou ações. Todos 88/88 numeric anchors devem permanecer.

EVIDÊNCIA/GATE
9. Reexecute run 2×/fresh clone/CWD; report byte-idêntico/mode 0644; verifier; FAIL input sem stale; links/images; word count; table completeness; 6 PNG byte-idênticos.
10. Crie `process-log/reviews/iteration-07-review-summary.md`; prompt `process-log/prompts/iteration-07-review-fix-prompt.md`; report `process-log/reports/iteration-07-review-fix-report.md`; adendo outline/process report; checklist gate It07 CONCLUDED, It08 PENDING.

GIT
- Só pasta; commit `docs: polish executive report for decision clarity`; sem amend/force/config/destrutivo; push/local==remote/tree limpo; diff-check/links/segredos.

FINAL
PASS/BLOCKED; hash/push; matrix; word counts before/after; table/mode fixes; numeric stability; pipeline tests; files/risks/handoff It08. BLOCKED se truncamento ou drift numérico persistir.
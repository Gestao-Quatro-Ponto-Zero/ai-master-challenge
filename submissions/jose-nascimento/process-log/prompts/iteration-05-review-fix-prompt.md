# Prompt integral — Agente Corretor Sequencial do review gate da Iteração 05 (arquivado)

**Data:** 2026-08-28 · **Agente:** corretor sequencial `deepseek-max` (DeepSeek V4 Flash, max reasoning, via OpenCode Go) · **Commit esperado:** `fix: align impact scenarios with experiment power`

> Transcrição fiel do prompt recebido (padrão de arquivamento dos gates anteriores).

---

Você é o AGENTE CORRETOR SEQUENCIAL da ITERAÇÃO 05. Corrija os findings convergentes dos três reviewers, preserve premissas históricas com adendo transparente e feche o gate. NÃO inicie It06.

REPO
- `/tmp/opencode/ai-master-challenge-work`, branch `submission/jose-nascimento`, pasta única `submissions/jose-nascimento/`, HEAD `a8a6ca6a25e653893cff2e9c534e428cc81293be`.

LEIA
- `/tmp/opencode/ai-master-review-reports/iteration-05/review-9a2752e1.md`
- `/tmp/opencode/ai-master-review-reports/iteration-05/review-838ab021.md`
- `/tmp/opencode/ai-master-review-reports/iteration-05/review-c17f9a4e.md`
- Assumptions (não reescrever), script/outputs/evidence/report It05, plano/checklist, contrato e instruções.

CORREÇÕES OBRIGATÓRIAS
1. Substitua regra GO assimétrica/ruidosa por decisão de 3 estados, claramente separando operação de evidência:
   - `SCALE/GO de eficácia` somente se redução relativa estimada ≥10% **E** IC95 do efeito exclui 0 na direção favorável, sem guardrail violado;
   - `CONTINUE/LEARN` se ponto favorável/leading metrics melhoram mas IC cruza 0 (não alegar eficácia; ampliar amostra/janela);
   - `STOP/HARM` se efeito adverso e IC95 exclui 0 ou guardrail crítico falha.
   Explique que MDE~37% com N=136/braço torna efeito real de 10–30% frequentemente inconclusivo; power aprox 11%/31%/61% e P(falso GO por ponto ≥10 sob nulo) ~24% devem ser DERIVADOS/validados, não hardcoded. Não troque threshold por 37% retroativamente; preserve 10% como mínimo operacional, mas exija evidência estatística para scale.
2. Remova a linha `annualized MRR-equivalent` de t19/evidence (mais confusa que útil; usava 4×estoque). Não substitua por outro forecast anual. Atualize gates/contagens.
3. Nomeie 0,3393–0,5417 como `observed cutoff range` (min-max de 3 coortes disjuntas), NÃO CI. Se mostrar Wilson pooled 95% (~0,362–0,501), derive separadamente e rotule. Não use independência sem afirmar que overlap=0 foi verificado.
4. Troque qualquer "eventos evitados" por "eventos afetados no cenário"/"redução assumida"; zero claim causal.
5. Sequência: ACT-03 instrumentação mínima é `Now / pré-requisito`, com SLA ≤30d; ACT-01 inicia rollout somente após instrumentation readiness. Reordene tabela se necessário. ACT-04 Later permanece baixa confiança.
6. Corrija horizonte 2/4 trimestres, markup/bold, precisão e literais narrativos baratos indicados pelos reviewers.
7. Atualize script para gerar tudo em runtime, incluindo power/falso-GO e decision rule; acrescente gates materiais. Preserve 6 PNGs byte-idênticos.

EVIDÊNCIA/GATE
8. Reexecute 2×/CWD; outputs determinísticos; recalc independente de base/scenarios/power/decision; FAIL estrutural; 3 MVs; no claims proibidos; nenhuma constante de dados; reports↔tables.
9. Crie `process-log/reviews/iteration-05-review-summary.md` com veredictos, matriz finding→ação, recálculos, decisão experiment, gate.
10. Arquive prompt em `process-log/prompts/iteration-05-review-fix-prompt.md`; crie `process-log/reports/iteration-05-review-fix-report.md`; adendo datado às assumptions (não reescreva parte pré-registrada); atualize checklist gate It05 CONCLUDED, It06 PENDING.

GIT
- status/log/diff antes; só pasta; `git add -f`; commit `fix: align impact scenarios with experiment power`; sem amend/force/config/destrutivo; push/local==remote/tree limpo; diff-check/links/segredos.

REPORT FINAL
PASS/BLOCKED; hash/push; matriz; regra 3 estados; power/falso-GO; t19 sem annualized; range vs CI; sequencing; validações; riscos/handoff It06. BLOCKED se GO ainda puder ser declarado só pelo ponto estimado.
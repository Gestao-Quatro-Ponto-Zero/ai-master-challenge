# Prompt — Iteração 03 · Correção do review gate 3x (agente corretor sequencial)

Transcrição fiel do prompt recebido pelo agente corretor sequencial (arquivado por evidência de processo, conforme regra de governança).

---

Você é o AGENTE CORRETOR SEQUENCIAL da ITERAÇÃO 03. Corrija os findings das 3 revisões, revalide a análise central e feche o gate. NÃO inicie It04/watchlist nem recomendações.

REPO
- `/tmp/opencode/ai-master-challenge-work`, branch `submission/jose-nascimento`, pasta única `submissions/jose-nascimento/`, HEAD esperado `9e02e18daf8b8a77a5ae4f552b6b5713b23a142e`.

LEIA INTEGRALMENTE
- `/tmp/opencode/ai-master-review-reports/iteration-03/review-4c090c69.md`
- `/tmp/opencode/ai-master-review-reports/iteration-03/review-b41e9a07.md`
- `/tmp/opencode/ai-master-review-reports/iteration-03/review-63a29930.md`
- Hipóteses pré-registradas (não reescrever), código/outputs/evidence/decisions/process report It03, contrato It02, plano/checklist e instruções oficiais.

CORREÇÃO MATERIAL
1. H4 atualmente inclui meses antes do signup como zero no lado churn. Corrija o desenho para usar apenas tempo em risco/observável após signup e antes da data índice; controls com exposição comparável (calendar/tenure conforme implementado). Não padronize período inexistente como zero. Recalcule. Espera-se aproximadamente 61,7% vs 60,2% (Δ~1,5 p.p.), mas derive do código — não hardcode. Atualize t10, evidence, decisão e process report. H4 deve preservar threshold pré-registrado e ser rotulada conforme resultado; deixe explícito que 13,7 p.p. era artefato e registre como erro real corrigido.
2. Verifique se outras features pré-index têm o mesmo erro de exposição; corrija se houver. Mantenha anti-leakage.

CORREÇÕES FACTUAIS/ROBUSTEZ (faça as de baixo risco)
3. Wording ≤30d: acumulado incluindo same-day é 43,6%/513.586 (derive); bucket 1–30d =39,6%; não misture.
4. Corrija referência do gráfico C de `t04` para `t03c`.
5. Corrija MD5 stale e timeline/horários no process report; registre hash histórico sem reescrever passado.
6. KM: tabelas t6/t12/t18 devem avaliar a função degrau no maior tempo ≤ horizonte, não exigir evento exatamente no horizonte. Respeite follow-up/censura; deixe vazio apenas quando horizonte não observável conforme regra explícita. Recalcule e atualize outputs/texto; valide independentemente.
7. Gráfico B não pode cortar curvas abaixo de 0,55; use eixo adequado (0–1 ou range íntegro) e confira todas as coortes.
8. H6: preserve hipótese original e registre que threshold de taxa `1,5×global` era estruturalmente inalcançável com base 70,4%; não finja teste informativo. Baseie conclusão apenas no critério alternativo pré-registrado que for válido (ex.: sobrevivência/intervalos) ou rotule inconclusivo. Isso é erro de desenho a documentar, não justificativa retroativa.
9. Suporte: retire do controle as 6 contas com primeiro evento em jan–mar/2023 incorretamente seedadas em `prev_ev`; recalcule e registre impacto. Clarifique mediana do uso alinhado (pooled vs median-of-medians) sem alterar por conveniência.
10. Ajuste frase "nível elevado 2024-03 em diante" para refletir o vale de abril/quantidade exata, sem enfraquecer o achado.

EVIDÊNCIA/GATE
11. Reexecute script, regenere 20 outputs; baseline 2× idempotente/CWD diferente; recálculos independentes de pico, KM, onboarding, uso corrigido, suporte, H6; 3 MVs; FAIL estrutural sem stale/traceback; abra/valide 6 PNGs.
12. Crie `process-log/reviews/iteration-03-review-summary.md` com veredictos/paths, findings, matriz ação→arquivo:linha, números recalculados, decisão causal e gate.
13. Arquive este prompt em `process-log/prompts/iteration-03-review-fix-prompt.md`; crie `process-log/reports/iteration-03-review-fix-report.md`; adendo de correção em decisions/report sem alterar hipóteses originais. Atualize checklist review gate It03 `CONCLUDED`; It04 permanece PENDING.

GIT
- Antes status/diff/log; preserve. Só pasta permitida; `git add -f` paths pretendidos.
- Commit `fix: correct exposure windows in root cause analysis`.
- Sem amend/force/config/destrutivo. Push; valide local==remote/tree limpo; diff-check/links/paths/segredos.

REPORT FINAL
PASS/BLOCKED; hash/push; matriz reviews; H4 antes/depois e causa do viés; KM/H6/suporte corrigidos; estabilidade da causa raiz; outputs/testes; arquivos/riscos; handoff It04. Se H4 ainda usar tempo pré-signup ou KM estiver errado, BLOCKED.
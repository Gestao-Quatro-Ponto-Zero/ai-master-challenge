# Prompt — Iteração 02 · Correção do review gate 3x (agente corretor sequencial)

Transcrição fiel do prompt recebido pelo agente corretor sequencial (arquivado por evidência de processo, conforme regra de governança).

---

Você é o AGENTE CORRETOR SEQUENCIAL da ITERAÇÃO 02. Leia as três revisões, corrija os findings materiais e feche o gate. NÃO inicie causa raiz/Iteração 03.

REPO
- `/tmp/opencode/ai-master-challenge-work`, branch `submission/jose-nascimento`, pasta única permitida `submissions/jose-nascimento/`, HEAD esperado `9305e2edcdea7506feab0af75e0f29401becf6b7`.

REVISÕES (leia integralmente)
- `/tmp/opencode/ai-master-review-reports/iteration-02/review-9d3b7e05.md`
- `/tmp/opencode/ai-master-review-reports/iteration-02/review-6c2f9a41.md`
- `/tmp/opencode/ai-master-review-reports/iteration-02/review-8b41e9c2.md`
- Leia também código/outputs/contract/decisions/report/prompt It02, plano/checklist e instruções oficiais.

FINDINGS MATERIAIS
1. O contrato de revenue churn baseado apenas no winner captura `18.507`, enquanto o reviewer recalculou `398.462` de MRR em 255 episódios de subscriptions não-dominantes encerradas com conta ativa (ex. `A-5a215a` 2024-12: 34.626 encerrado sem winner mover). Isso não invalida winner para estado/risco, mas torna a fórmula única de revenue churn incompleta/degenerada.
2. Existem números de qualidade hardcoded na geração do contract/report (`13.198`, `1.077`, `53`, `90`, `143`, `825`, `41,2%`, `148` etc.). Eles devem ser calculados em runtime dos CSVs/frames, não constantes.
3. Política para `closed_at` nulo/temporal precisa ficar explícita para evitar leakage posterior.

TAREFAS
1. Corrija contrato, código e outputs com duas lentes de receita inequivocamente nomeadas:
   - **gross subscription ending MRR**: soma das subscriptions encerradas no período, exposição contratual bruta; NÃO chamar automaticamente de receita/logo perdida porque pode ser troca/replacement/overlap;
   - **net account-state MRR loss**: perda de MRR do estado/winner entre snapshots (separe churn para inativo de contraction ativa); explique cobertura/trade-off.
   Preserve winner como estado/risk exposure, mas proíba usar sua saída isoladamente como total de churn contratual. Quantifique e derive em runtime o gap, episódios não-dominantes e exemplo material; escolha fórmulas/nomes que não enganem.
2. Se necessário, adicione colunas auditáveis ao `account_month.csv` (por exemplo MRR de subs encerradas no mês e deltas do estado) e invariantes que reconciliem gross ending MRR à fonte, sem target leakage: rotule colunas de outcomes claramente e proíba-as em features de risco.
3. Substitua todos os números hardcoded de data quality/reason/CSAT no render por valores computados; faça busca sistemática por outros números de dados hardcoded. Constantes de regra/janelas/tolerância são permitidas e devem ser nomeadas.
4. Documente `closed_at`: tickets existem por `submitted_at`; métricas de resolução/CSAT só usam tickets fechados e informação observável até a data índice; nulos ficam excluídos com denominador explícito; nunca imputar fechamento futuro.
5. Enderece LOWs baratos/factuais sem refatoração ampla: nota de arredondamento de quantis; tie-break do matching explícito; remova coluna/wording redundante "Acumulado" se enganoso; remova código morto; clarifique D4/§9 diário vs mensal. Aceite trade-offs documentados quando não materiais.
6. Reexecute e regenere todos os outputs It02; verifique números existentes e novos independentemente, incluindo 1.179.139 gross ending total, 18.507 churn-to-inactive (se essa for a definição correta), 398.462/255 non-dominant hidden conforme algoritmo final; reporte qualquer diferença com causa.
7. Rode baseline 2x/idempotente, comparação com outputs commitados novos, três MVs, invariantes, e cenários FAIL (schema/arquivo) sem stale/traceback.
8. Crie `process-log/reviews/iteration-02-review-summary.md` com veredictos, findings, matriz ação/arquivo:linha, recálculos, decisão sobre winner, testes, riscos, gate final.
9. Arquive este prompt integral em `process-log/prompts/iteration-02-review-fix-prompt.md`; crie `process-log/reports/iteration-02-review-fix-report.md`; atualize checklist para review gate It02 `CONCLUDED`, sem iniciar It03. Estados válidos apenas.

GIT/VALIDAÇÃO
- Antes status/diff/log; preserve tudo. Modifique só pasta permitida.
- Syntax/import, data hardcode scan, outputs determinísticos, `git diff --check`, Markdown/links, paths/segredos, escopo.
- `git add -f` só paths pretendidos. Commit `fix: strengthen revenue churn contract`. Sem amend/force/config/destrutivo. Push e valide local==remote/tree limpo.

REPORT FINAL
PASS/BLOCKED; hash/push; matriz dos 3 reviews; fórmulas finais e novos números; como M1/M2/closed_at foram corrigidos; testes/invariantes; arquivos; riscos; handoff It03. Se revenue lenses continuarem ambíguas ou hardcodes persistirem, BLOCKED.
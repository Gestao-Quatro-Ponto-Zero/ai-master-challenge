# Report de Correção — Review Gate da Iteração 05 (fixer sequencial)

- **Data:** 2026-08-28
- **Agente:** corretor sequencial `deepseek-max` (DeepSeek V4 Flash, max reasoning, via OpenCode Go), sob orquestração do opencode
- **HEAD base:** `a8a6ca6a25e653893cff2e9c534e428cc81293be` (esperado no prompt) — confirmado no início (working tree limpo, branch `submission/jose-nascimento`)
- **Prompt integral:** `process-log/prompts/iteration-05-review-fix-prompt.md` (arquivado)
- **Tempo de relógio (F11):** ~1h15min (3 reports de revisão + correções do script + recálculos independentes + validações + documentos) — acumulado analítico ~15h50

---

## 1. Status

**PASS** — regra de decisão do ACT-01 convertida para 3 estados (escala exige evidência estatística); poder por cenário e falso-GO derivados em runtime com gates; linha `annualized` removida; faixa 0,3393–0,5417 rotulada como `observed cutoff range` (não CI) com Wilson derivado separadamente e overlap=0 verificado; ACT-03 → Now/pré-requisito com SLA ≤ 30d; wording causal e literais de narrativa corrigidos; revalidação completa (45 PASS / 0 WARN / 0 FAIL, idempotência 2× + CWD, FAIL estrutural 2 cenários, 3 MVs, recálculo independente power/falso-GO/Wilson/disjoint, 6 PNGs byte-idênticos); commit `fix: align impact scenarios with experiment power` e push concluídos; gate It05 `CONCLUDED`; It06 `PENDING` (não iniciada).

## 2. Correções (matriz finding → ação)

| # | Finding (revisores) | Correção | Onde |
|---|---|---|---|
| 1 | **M1 (3/3):** GO por ponto ≥ 10% vs MDE ≈ 37% — assimetria de evidência; falso-GO ≈ 24%; power 11/31/61% | Regra de decisão em **3 estados** (SCALE/GO = ponto ≥ 10% E IC95 exclui 0 na direção favorável, sem guardrail violado; CONTINUE/LEARN = IC cruza 0, sem alegar eficácia, ampliar amostra/janela; STOP/HARM = efeito adverso significativo ou guardrail crítico). Poder por cenário e P(falso GO) **derivados em runtime** (`power_for_reduction`, `prob_go_under_null`) com gates G13-power-scenarios / G13-false-go / G13-decision-rule; piso operacional de 10% preservado (threshold NÃO trocado por 37%); horizonte "4 trimestres + 90d de follow-up"; 1ª decisão em 2 trimestres | `05_actions_impact.py` (funções de poder; t18 ACT-01 stop_go_criteria; render §5); evidence §5; adendo decisions §1 |
| 2 | **M2 (3/3):** linha `annualized` (N=320 = 4×estoque ≠ fluxo 273) | Linha **removida** da t19/evidence; sem forecast substituto; nota "nenhuma linha anualizada é apresentada"; gate G13-annualized-absent | `build_scenarios`; render §4; t19 (7 linhas) |
| 3 | **M3 (3/3):** 0,3393–0,5417 = min/max entre cutoffs, não CI | Rotulada **`observed cutoff range`** ("faixa observada entre cutoffs — NÃO é intervalo de confiança"); **Wilson 95% do pooled ≈ 0,362–0,501 derivado separadamente** (`wilson_ci`) e rotulado como CI; independência com **overlap = 0 verificado** (t14b, `compute_disjointness`); gates G13-wilson / G13-disjoint | `05_actions_impact.py`; render §4; t19 notas |
| 4 | **M4/L2/LOW-4 (3/3):** ACT-01 Now vs ACT-03 Next sem SLA | **ACT-03 → Now/pré-requisito, SLA ≤ 30d** (milestone de ativação em produção); **ACT-01 inicia rollout somente após instrumentation readiness**; t18 reordenada (ACT-03, ACT-01, ACT-02, ACT-04); ACT-04 permanece **Later**; gate G13-sequencing; §5: "outcome primário independe de ACT-03; leading metrics dependem" | `build_prioritized`; render §1/§5; t18 |
| 5 | **L3:** horizonte "2 trimestres" vs "4 trimestres" | Alinhado: 1ª decisão (STOP/reescopo) em 2 trimestres; decisão de escala em 4 trimestres **+ 90d de follow-up** (nuance de maturidade do review-3) | render §5; t18; adendo |
| 6 | **L4:** precisão de exibição (≤ 24 US$) | Tolerância documentada (componentes exibidos arredondados; re-cálculo pode divergir ≤ 0,01% / ~25 US$); números em precisão plena preservados (53.497/45.639) | render §4; adendo §7 |
| 7 | **L5:** negrito mal fechado | "**392.030 US$/mês (10,7% do total)**" | render §1 |
| 8 | **L6:** literais de narrativa (lifts, KM) | **Derivados em runtime** da t14/t12 (`compute_lifts` regras A/B/D/E 90d + D 180d; `compute_km` KM 90d/180d/mediana; âncoras 34,7%/52,4%); G10 estendido; docstring sem literais | `05_actions_impact.py`; t18/t21/t20; render §2 |
| 9 | **LOW-2:** "76,6% fora da janela" imprecisa | Adendo: "uso antes do start_date 76,6% (19.142/25.000); em janela 22,3% (5.568/25.000)" — pré-registro INTACTO | adendo decisions §5 |
| 10 | **I1b:** ambicioso ancorado no spike | Nota derivada no t19: "incidência = precisão do cutoff 2024-09-30 (janela do pico sintético — cautela It04)" | `build_scenarios`; t19 |
| 11 | **L1/M3:** "eventos evitados" | → "eventos afetados no cenário (redução assumida)"; zero claim causal; gates G13-wording / G13-wording-md | t18 impact_metric; render §1/§7 |

## 3. Regra de decisão em 3 estados (ACT-01) — texto final

1. **SCALE/GO (eficácia):** redução relativa estimada ≥ 10% (piso operacional preservado) **E** IC95 do efeito exclui 0 na direção favorável, sem guardrail violado → escala total (4 trimestres de rollout + 90d de follow-up).
2. **CONTINUE/LEARN:** ponto estimado favorável e/ou leading metrics melhoram, mas IC95 cruza 0 → NÃO alegar eficácia; estender holdout/ampliar amostra ou janela.
3. **STOP/HARM:** efeito adverso com IC95 excluindo 0, ou guardrail crítico falhado (CSAT/escalação) → encerrar/reduzir. 1ª decisão (STOP/reescopo) em 2 trimestres.

Justificativa (derivada em runtime, gates G13-power-scenarios / G13-false-go): MDE ≈ 37% a 80% power com N=136/braço ⇒ efeito real de 10–30% é frequentemente inconclusivo (poder ≈ 11/31/61%); P(ponto ≥ 10% | efeito nulo) ≈ 24% ⇒ GO por ponto isolado dispararia por ruído em ~1 de 4 experimentos nulos. O threshold **não** foi trocado por 37% retroativamente; 10% permanece o mínimo operacional de planejamento, mas a evidência estatística (IC95 excluindo 0) é o que autoriza escala. Inconclusivo ≠ ausência de efeito (declarado).

## 4. Poder / falso-GO / CI / disjunção — derivados e validados

| Métrica | Valor derivado (runtime) | Recalc independente (corretor) | Gate |
|---|---|---|---|
| Poder 10/20/30% (N=136/braço) | 11% / 31% / 61% | 10,8% / 30,9% / 60,6% ✓ | G13-power-scenarios |
| P(falso GO por ponto ≥ 10% | nulo) | ≈ 24% (23,7%) | 23,7% ✓ | G13-false-go |
| CI Wilson 95% do pooled | 0,362–0,501 | 0,362–0,501 ✓ | G13-wilson |
| Disjunção do pooling (overlap=0) | 193 únicas = Σ n_rule; 0 em >1 cutoff | idem ✓ | G13-disjoint |
| MDE 80% power (34/68/136) | 68% / 51% / 37% | 67,5 / 50,7 / 37,2 ✓ | G7 |

## 5. Validações executadas

| Validação | Resultado |
|---|---|
| Script do zero (sandbox + repo) | **45 PASS / 0 WARN / 0 FAIL**, exit 0 (32 → 45: +F11/F12/SC-F11/SC-F12 [t14b, t12] + 8 gates G13 + G13-wording-md) |
| Idempotência 2× + CWD diferente | 5 outputs **byte-idênticos** (MD5) entre execução 1, execução 2 e CWD diferente; sandbox == repo (MD5) |
| FAIL estrutural (2 cenários) | (a) `tenure_days` renomeada; (b) t14b ausente → exit 1; relatório regravado com "Falha estrutural"; **0 tracebacks**; restauração → 45 PASS |
| 3 MVs independentes | MV-1 base 80/621.981 (esperado); MV-2 cenário base 6,9 eventos / 53.497 US$ (== t19); MV-3 tiers 8/169.747 + 12/222.283 = 392.030 (10,7%) — todos conferem |
| Recálculo independente | power 10,8/30,9/60,6%; falso-GO 23,7%; Wilson 0,362–0,501; disjoint 193/0; MDE 67,5/50,7/37,2%; t19 linha a linha (0 divergências > 0,1) — todos conferem |
| 6 PNGs byte-idênticos | MD5 dos 6 PNGs == blobs do git (8de9904b/ecca1338/742ef0b9/99d8daa1/d8e40a2e/b95c537e); nenhum PNG novo (G9) |
| Nenhuma constante de dado | G10 estendido: lifts/KM/Wilson/power/falso-GO/âncoras ausentes como literais — PASS |
| Claims proibidos | "evitad" zerado nas seções 1–7 e no t18 (G13-wording/G13-wording-md); G11b PASS; "alto risco"/"reativação mais barata" só em contextos proibitivos |
| Report ↔ CSV | t18 4 ações (ordem ACT-03/01/02/04), t19 7 cenários (sem annualized), t20 18 métricas (âncoras KM derivadas), t21 20 contas (8+12) — G12 PASS |
| Markdown/links/paths/segredos | refs do relatório resolvem; grep `/tmp`/`/home`/`ubuntu` nos artefatos da solução: zero exceto paths de processo já documentados (reports de revisão externos em `ai-master-review-reports/` e prompts arquivados — exceção documentada, mesma do gate It04); `py_compile` ok |
| `git diff --check` / escopo | limpo; apenas `submissions/jose-nascimento/` |

## 6. Arquivos

**Alterados (código/outputs):** `solution/src/05_actions_impact.py` (funções de poder/Wilson/disjunção/lifts/KM; t18 reordenada com regra 3 estados; t19 sem annualized; render §1/§2/§4/§5; gates G13); `solution/evidence/05_action_plan.md` (regenerado); `solution/out/tables/t18_actions_prioritized.csv` (regenerado); `solution/out/tables/t19_impact_sensitivity.csv` (regenerado); `solution/out/tables/t20_measurement_plan.csv` (byte-idêntico — âncoras derivadas com os mesmos valores); `solution/out/tables/t21_watchlist_split_actions.csv` (byte-idêntico — lifts derivados com os mesmos valores).

**Alterados (processo):** `process-log/decisions/iteration-05-action-impact-assumptions.md` (**adendo datado** — parte pré-registrada INTACTA); `process-log/management/orchestrator-checklist.md` (cabeçalho; B3; B10; F11); `process-log/management/execution-plan.md` (cabeçalho/status; It05); `process-log/reports/iteration-05-actions-impact-report.md` (adendo pós-gate).

**Criados:** `process-log/reviews/iteration-05-review-summary.md` (ledger do gate); `process-log/prompts/iteration-05-review-fix-prompt.md` (prompt integral); `process-log/reports/iteration-05-review-fix-report.md` (este).

**Intactos:** premissas pré-registradas It05 (conteúdo original), contrato analítico, decisions It02–It04, hipóteses It03, tabelas t01–t17/t20–t21 (conteúdo), 6 PNGs, README.

## 7. Git

- **Commit:** `fix: align impact scenarios with experiment power` (sem amend); `git add -f` apenas nos paths pretendidos.
- **Push:** realizado para `origin/submission/jose-nascimento`; local == remote confirmado; working tree limpo; `git diff --check` limpo.
- Disciplina: sem amend/force/config/destrutivo.

## 8. Riscos e handoff para a It06

1. **Poder estruturalmente baixo do experimento** (MDE ≈ 37%): desfecho mais provável é inconclusivo — acomodado pela regra de 3 estados (CONTINUE/LEARN); It07 deve preservar "planejado, não medido".
2. **Leitura do GO como evidência:** mitigado — escala exige IC95 excluindo 0; falso-GO ≈ 24% divulgado no artefato CEO (§5).
3. **Spike sintético:** cenário ambicioso ancorado no cutoff do pico (2024-09-30) com nota explícita.
4. **Dependência de instrumentação:** SLA ≤ 30d pré-registrado; rollout do ACT-01 gated; contingência de atraso mantida.
5. **Time budget:** acumulado ~15h50 vs 4–6h — acima do gatilho de contenção (§2.5b); F11 registra a decisão consciente e os trims formais vigentes desde a It05.
6. **It06 (automação):** `05_actions_impact.py` é o 5º estágio do pipeline com 2 novos inputs (t14b, t12); `run.sh` deve reproduzir os 5 outputs byte-a-byte; validar FAIL estrutural no pipeline integrado.
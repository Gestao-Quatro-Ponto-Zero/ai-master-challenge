# Ledger de Revisão — Iteração 05 · Ações priorizadas, impacto e plano de medição (review gate 3x + correção sequencial)

- **Iteração revisada:** 05 (ações/impacto/medição)
- **Commits sob revisão:** premissas `dc5748f30e90ff9be4a9631c65ca21caf7afbcf8` (`docs: define action and impact assumptions`) · execução `a8a6ca6a25e653893cff2e9c534e428cc81293be` (`feat: prioritize churn interventions and impact scenarios`); base `617e4ac252043475492d2b2e4c92e2eea1a3f385`
- **Revisores:** 3 agentes `deepseek-max` independentes, modo read-only, em paralelo (2026-08-28) — sandboxes fora do repo (`/tmp/opencode/it05-reviewer-sandbox/`, `/tmp/opencode/it05_review_sandbox/`, `/tmp/opencode/sandbox-it05/`); **repo intacto** (working tree limpo antes/depois; HEAD inalterado)
- **Relatórios dos revisores:** `/tmp/opencode/ai-master-review-reports/iteration-05/review-9a2752e1.md` · `review-838ab021.md` · `review-c17f9a4e.md` (veredictos e evidências na íntegra)
- **Correção sequencial:** agente corretor (este) — commit `fix: align impact scenarios with experiment power`; ver `process-log/reports/iteration-05-review-fix-report.md` e prompt arquivado `process-log/prompts/iteration-05-review-fix-prompt.md`
- **Gate It05:** `CONCLUDED` (3 veredictos `PASS_WITH_FIXES`; 1 finding MEDIUM convergente — regra GO por ponto vs poder do experimento — e correções LOW convergentes aplicadas com revalidação completa: 45 PASS / 0 WARN / 0 FAIL, idempotência 2× + CWD, FAIL estrutural 2 cenários, recálculo independente 3 MVs + power/falso-GO/Wilson/disjoint, 6 PNGs byte-idênticos). Iteração 06 permanece `PENDING` (não iniciada).

---

## 1. Veredictos dos revisores

| Revisor | Veredicto | Findings |
|---|---|---|
| review-9a2752e1 | **PASS_WITH_FIXES** | MEDIUM-1 (regra GO ≥10% = threshold operacional, não evidência; falso-GO sob nulo ≈ 24%; poder 20% ≈ 31%); LOW-1 (annualized 4×estoque=320 vs fluxo 273); LOW-2 (76,6% = uso ANTES do start_date); LOW-3 (0,3393–0,5417 = min/max por cutoff, NÃO CI; Wilson pooled 0,362–0,501); LOW-4 (dependência ACT-01→ACT-03 sem SLA); INFO-1/INFO-2 (sem correção) |
| review-838ab021 | **PASS_WITH_FIXES** | M1 (GO ≥10% vs MDE ≈ 37%: contradição de desenho não resolvida; CI ±27% relativo em N=136); M2 (annualized N=320 inconsistente; 213.987 US$ citável fora de contexto); M3 ("evitados" no t18); M4 (ACT-01 Now vs ACT-03 Next sem frase de paralelismo); I1 (pooling defensável; lower/upper não é CI); I1b (ambicioso ancorado no cutoff do spike — nota opcional) |
| review-c17f9a4e | **PASS_WITH_FIXES** | M1 (GO por ponto vs MDE 37%; power 11/31/61%; N p/ 10% ≈ 2.047/braço; falso-GO ≈ 24%; nuance de maturidade: 4 trimestres + 90d de follow-up); M2 (annualized); M3 (lower/upper = min–max, não IC); L1 ("evitados"); L2 (sequência ACT-01/ACT-03); L3 (horizonte 2 vs 4 trimestres); L4 (precisão de exibição); L5 (negrito mal fechado); L6 (literais de narrativa hardcoded) |

**Convergência:** 100% dos números-chave recalculados de forma independente
pelos 3 revisores bateram (base 80/621.981; incidência 83/193 = 0,4301; faixa
0,3393–0,5417; cenários 2,7/6,9/13,0 e 21.104/53.497/101.078; watchlist
8/169.747 + 12/222.283 = 392.030 = 10,7%; MDE 68/51/37%; fluxo 68,25); pooling
defensável (coortes disjuntas, overlap 0/0/0 verificado); idempotência
byte-a-byte; FAIL estrutural sem traceback; 6 PNGs imutáveis; zero claims
proibidos afirmativos. **Finding material único convergente: M1 — regra de
decisão GO (redação de regra, não aritmética).**

## 2. Matriz finding → ação → arquivo:linha (pós-correção)

| # | Finding (revisores) | Ação | Arquivo:linha (pós-fix) |
|---|---|---|---|
| M1 (3/3) | GO por ponto ≥ 10% vs MDE ≈ 37%: assimetria de evidência; falso-GO ≈ 24%; power 11/31/61% | **Regra de decisão em 3 estados**: SCALE/GO = ponto ≥ 10% (piso operacional preservado) **E** IC95 exclui 0 na direção favorável, sem guardrail violado; CONTINUE/LEARN = ponto/leading melhoram mas IC95 cruza 0 (sem alegar eficácia; ampliar amostra/janela); STOP/HARM = efeito adverso com IC95 excluindo 0 ou guardrail crítico falhado. Poder por cenário e P(falso GO) **derivados em runtime** (funções `power_for_reduction`/`prob_go_under_null`; gates G13-power-scenarios/G13-false-go/G13-decision-rule). Horizonte: 4 trimestres de rollout **+ 90d de follow-up**; 1ª decisão em 2 trimestres | `05_actions_impact.py` (`power_for_reduction`/`prob_go_under_null`; t18 ACT-01 stop_go_criteria; render §5); `05_action_plan.md` §5; adendo `iteration-05-action-impact-assumptions.md` §1 |
| M2/LOW-1 (3/3) | Linha `annualized` (N=320 = 4×estoque; fluxo real 273/ano) | **Linha removida** da t19/evidence; nenhum forecast anual substituto; nota de honestidade "nenhuma linha anualizada é apresentada"; gate G13-annualized-absent | `05_actions_impact.py` (`build_scenarios`; render §4); t19 (7 linhas); gate G13-annualized-absent |
| M3/LOW-3 (3/3) | 0,3393–0,5417 = min/max por cutoff, não CI | Nomeada **`observed cutoff range`** ("faixa observada entre cutoffs, NÃO é intervalo de confiança"); Wilson 95% do pooled ≈ 0,362–0,501 **derivado separadamente** e rotulado como CI (`wilson_ci`); independência com **overlap = 0 verificado** (t14b; gate G13-disjoint); gate G13-wilson | `05_actions_impact.py` (`wilson_ci`, `compute_incidence`, `compute_disjointness`); render §4; t19 notas; gates G13-wilson/G13-disjoint |
| M4/L2/LOW-4 (3/3) | Sequenciamento ACT-01 (Now) vs ACT-03 (Next) sem SLA | **ACT-03 → Now/pré-requisito com SLA ≤ 30d** (milestone em produção); **ACT-01 inicia rollout somente após instrumentation readiness**; t18 reordenada (ACT-03, ACT-01, ACT-02, ACT-04); ACT-04 permanece Later; gate G13-sequencing; §5 nota "outcome primário independe de ACT-03; leading metrics dependem" | `05_actions_impact.py` (`build_prioritized`; render §1/§5); t18; gate G13-sequencing |
| L3 (review-3) | Horizonte "2 trimestres até decisão" vs "GO após 4 trimestres" | Alinhado: 1ª decisão (STOP/reescopo) em 2 trimestres; escala em 4 trimestres **+ 90d de follow-up** (nuance de maturidade); texto em §5, t18 e adendo | `05_actions_impact.py` (render §5; t18 ACT-01 stop_go_criteria) |
| L4 (review-3) | Precisão: t19 calcula com pooled não arredondado vs exibido | Tolerância documentada: componentes exibidos arredondados; re-cálculo do leitor pode divergir ≤ 0,01% (~25 US$); números em precisão plena preservados (53.497/45.639 intactos) | render §4; adendo §7 |
| L5 (review-3) | Negrito mal fechado "**392.030 US$/mês (10,7%** do total)" | Corrigido: "**392.030 US$/mês (10,7% do total)**" | render §1 (ACT-02) |
| L6 (review-3) | Literais de narrativa (lifts 1,57/1,56/1,83; KM 0,653/187d) hardcoded | **Derivados em runtime** da t14/t12 (`compute_lifts`, `compute_km`): regras A/B/D/E 90d, D 180d, KM 90d/180d/mediana, âncoras 34,7%/52,4%; G10 estendido; docstring sem literais | `05_actions_impact.py` (`compute_lifts`, `compute_km`; `build_prioritized`; `build_watchlist_split`; `build_measurement_plan`; render §2) |
| LOW-2 (review-1) | "76,6% fora da janela" imprecisa (contrato §9: uso ANTES do start_date) | Adendo às premissas: "uso antes do start_date 76,6% (19.142/25.000); em janela 22,3% (5.568/25.000)" — pré-registro INTACTO | adendo `iteration-05-action-impact-assumptions.md` §5 |
| I1b (review-2) | Cenário ambicioso ancorado no cutoff do spike (2024-09-30) | Nota derivada em runtime no t19 (linha ambicioso): "incidência = precisão do cutoff 2024-09-30 (janela do pico sintético — cautela It04)" | `build_scenarios`; t19 |

## 3. Recálculos (revisores + corretor, implementação independente) — todos confirmados

| Métrica | Valor verificado |
|---|---|
| Base elegível (tenure ≤ 90d no corte) | 80 contas / 621.981 US$ (2 caminhos; tenure == (cut−signup).days em 500/500) ✓ |
| Incidência pooled regra D 90d | 83/193 = 0,430052 (19/56 + 25/65 + 39/72); faixa observada 0,3393–0,5417 ✓ |
| CI de Wilson 95% do pooled | **0,362–0,501** (derivado separadamente; NÃO é a faixa) ✓ |
| Disjunção do pooling | 193 contas únicas em t14b (56/65/72); overlap = 0 (nenhuma em >1 cutoff) ✓ |
| Cenários 90d | 2,7/6,9/13,0 eventos e 21.104/53.497/101.078 US$; sens 42.208/53.497/67.385; sens-pop-flow 29,4/530.628/45.639 ✓ (t19 linha a linha, 0 divergências > 0,1) |
| Annualized | **removido** (era 27,5/213.987 com N=320; gate G13-annualized-absent) |
| Watchlist | Tier A 8/169.747; B+C 12/222.283; total 20/392.030 = 10,7% de 3.668.852 ✓ |
| Fluxo 2024 | 56/65/72/80; média 68,25; total 273 ✓ |
| MDE (80% power) | 67,5/50,7/37,2% → 68/51/37% (N/braço 34/68/136) ✓ |
| **Poder por cenário (N=136/braço)** | **10,8% (10%) / 30,9% (20%) / 60,6% (30%)** → 11/31/61% — DERIVADO em runtime (gate G13-power-scenarios) ✓ |
| **P(falso GO por ponto ≥ 10% | nulo)** | **23,7% ≈ 24%** (SE(diff)=0,060; limiar absoluto 0,043) — DERIVADO em runtime (gate G13-false-go) ✓ |
| Qualidade (baseline ACT-03) | CSAT 58,8%; unknown 15,83%; uso em janela 22,3% (= 5.568/25.000, contrato §9); vínculo 21,0% ✓ |
| Fatos It03 citados | 53,4%; 68,4%; 83,7% ✓ (verificados nas fontes) |

## 4. Decisão do experimento (ACT-01) — regra de 3 estados

- **SCALE/GO (eficácia):** redução relativa estimada ≥ 10% (piso operacional preservado) **E** IC95 do efeito exclui 0 na direção favorável, sem guardrail violado → escala total (4 trimestres de rollout + 90d de follow-up).
- **CONTINUE/LEARN:** ponto estimado favorável e/ou leading metrics melhoram, mas IC95 cruza 0 → NÃO alegar eficácia; estender holdout/ampliar amostra ou janela.
- **STOP/HARM:** efeito adverso com IC95 excluindo 0, ou guardrail crítico falhado (CSAT/escalação) → encerrar/reduzir. 1ª decisão (STOP/reescopo) em 2 trimestres.
- **Justificativa estatística (derivada, não hardcoded):** com N=136/braço o MDE a 80% power ≈ 37% ⇒ efeitos reais de 10–30% são frequentemente inconclusivos (poder ≈ 11/31/61%); GO por ponto isolado dispararia por ruído em ~1 de 4 experimentos nulos (falso-GO ≈ 24%). O threshold **não** foi trocado por 37% retroativamente — 10% permanece o mínimo operacional de planejamento; a evidência estatística (IC95 excluindo 0) é o que autoriza escala. Inconclusivo ≠ ausência de efeito (declarado).

## 5. Validações pós-correção (detalhe no review-fix report)

- Script re-executado do zero em sandbox e repo: **45 PASS / 0 WARN / 0 FAIL** (32 → 45: +2 F/SC [t14b, t12] + 8 gates G13 + G13-wording-md); idempotência 2× + CWD diferente: 5 outputs **byte-idênticos** (MD5); sandbox == repo (MD5).
- FAIL estrutural: (a) coluna `tenure_days` renomeada; (b) t14b ausente → exit 1, relatório regravado com "Falha estrutural", **0 tracebacks**, restauração → 45 PASS.
- 3 MVs independentes: MV-1 80/621.981; MV-2 6,9/53.497; MV-3 8/169.747 + 12/222.283 = 392.030 — todos conferem.
- Recálculo independente (implementação própria do corretor): power 10,8/30,9/60,6%; falso-GO 23,7%; Wilson 0,362–0,501; disjoint 193/0; MDE 67,5/50,7/37,2%; t19 linha a linha — todos conferem.
- 6 PNGs do keep-set: MD5 antes/depois **iguais aos blobs do git** (8de9904b/ecca1338/742ef0b9/99d8daa1/d8e40a2e/b95c537e); nenhum PNG novo (G9 PASS).
- G10 estendido: zero literais derivados no script (lifts, KM, Wilson, power, falso-GO, âncoras verificados).
- Claims: "evitad" zerado nas seções 1–7 e no t18 (G13-wording / G13-wording-md PASS); "alto risco"/"reativação mais barata" apenas em contextos proibitivos; G11b PASS.
- Report↔CSV: t18 (4 ações reordenadas ACT-03/01/02/04), t19 (7 cenários, sem annualized), t20 (18 métricas), t21 (20 contas; 8+12) consistentes (G12 PASS).
- Git: escopo 100% `submissions/jose-nascimento/`; `git diff --check` limpo; autor do candidato; sem amend/force/rebase; push validado (local == remote).

## 6. Riscos remanescentes (handoff It06/It07)

1. **Poder estruturalmente baixo do experimento** (MDE ≈ 37%): o desfecho mais provável é inconclusivo — já acomodado pela regra de 3 estados (CONTINUE/LEARN sem alegar eficácia); It07 deve preservar a linguagem "planejado, não medido".
2. **Leitura do GO como evidência:** mitigado — escala agora exige IC95 excluindo 0; a regra e o falso-GO estão no artefato CEO (§5).
3. **Spike sintético:** cenário ambicioso usa a precisão do cutoff do pico (2024-09-30) — nota explícita adicionada (I1b).
4. **Dependência de instrumentação (ACT-03):** SLA ≤ 30d pré-registrado; rollout do ACT-01 gated por instrumentation readiness; contingência para atraso mantida.
5. **Time budget:** acumulado ~14h35 + custo deste gate (~1h15) — acima do gatilho de contenção (§2.5b); F11 registra a decisão consciente e os trims formais vigentes desde a It05.
6. **It06 (automação):** script é o 5º estágio do pipeline (`01..05`) com 2 novos inputs (t14b, t12) — `run.sh` deve reproduzir byte-a-byte; validar FAIL estrutural no pipeline integrado.

## 7. Gate It05

**CONCLUDED** — 3 veredictos `PASS_WITH_FIXES`; finding material convergente M1 (regra de decisão GO) corrigido com regra de 3 estados + poder/falso-GO derivados em runtime; correções LOW convergentes (annualized removido; faixa vs CI; sequenciamento com SLA; wording "afetados"; horizonte; bold; precisão; literais) aplicadas com revalidação completa. Iteração 06 permanece **PENDING** (não iniciada).
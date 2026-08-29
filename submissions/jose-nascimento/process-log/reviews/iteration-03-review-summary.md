# Ledger de Revisão — Iteração 03 · Causa raiz, coortes e economia do onboarding (review gate 3x + correção sequencial)

- **Iteração revisada:** 03 (causa raiz, coortes e onboarding economics)
- **Commits sob revisão:** hipóteses `8cb93c33779d199a6cf05a37f5c411ff25fe75f3` (docs: define churn hypotheses before analysis, 2026-08-28T20:28:39Z) · análise `9e02e18daf8b8a77a5ae4f552b6b5713b23a142e` (feat: diagnose churn root cause and cohort dynamics, 20:47:32Z) · base `6e7be698c484a6c80f41b45d59b4f3ab4a8ddf67`
- **Revisores:** 3 agentes `deepseek-max` independentes, modo read-only, em paralelo (2026-08-28) — sandboxes fora do repo; **repo intacto** (working tree limpo antes/depois de cada revisão)
- **Relatórios dos revisores:** `/tmp/opencode/ai-master-review-reports/iteration-03/review-4c090c69.md` · `review-b41e9a07.md` · `review-63a29930.md` (veredictos e evidências na íntegra)
- **Correção sequencial:** agente corretor (este) — commit `fix: correct exposure windows in root cause analysis`; ver `process-log/reports/iteration-03-review-fix-report.md` e prompt arquivado `process-log/prompts/iteration-03-review-fix-prompt.md`
- **Gate It03:** `CONCLUDED` (3 veredictos `PASS_WITH_FIXES`; finding material M1 corrigido; 12 correções aplicadas; revalidação independente 49/49; 23 PASS / 0 WARN / 0 FAIL). Iteração 04 permanece `PENDING` (não iniciada — sem watchlist/recomendações).

---

## 1. Veredictos dos revisores

| Revisor | Veredicto | Findings materiais | Findings menores/INFO |
|---|---|---|---|
| review-4c090c69 | **PASS_WITH_FIXES** | M1 — H4 zero-uso conta meses pré-signup como zero (Δ 13,7 p.p. ≈9× superestimado; corrigido ≈1,5–9,0 p.p.) | L1 (wording ≤30d), L2 (H6 RATE_FLAG inalcançável), L3 (t04→t03c), L4 (vale de abril), L5 (KM por tempo exato); I1/I2/I3 |
| review-b41e9a07 | **PASS_WITH_FIXES** | nenhum material | LOW-1 (MD5 stale), LOW-2 (39,6% vs 43,6%), LOW-3 (t04), LOW-4 (linguagem H4), LOW-5 (sensibilidade H2 à definição de pico), LOW-6 (H6 inalcançável); INFO-1 (KM), INFO-2 (coluna contas únicas) |
| review-63a29930 | **PASS_WITH_FIXES** | 2 obrigatórios factuais: MD5 stale + timeline conflitante com CommitDate | #3 (seed prev_ev), #4 (mediana alinhada), #5 (gráfico B corta curvas < 0,55), #6 (KM carry-forward), #7 (H6 inalcançável), #8 (t04), #9 (wording 39,6%), #10 (cosméticos) |

**Convergência:** nenhum revisor refutou a causa raiz declarada (churn precoce de coortes novas, concentrado no onboarding, com aumento real de taxa no pico) — todos os números-chave reproduzidos independentemente (74/74, 130/130 e ~40 checks). O único finding material (M1) **fortalece** o veredito H4 (REFUTADA) e não altera a síntese causal.

## 2. Matriz finding → ação → arquivo:linha (pós-correção)

| # | Finding (revisores) | Ação | Arquivo:linha (pós-fix) |
|---|---|---|---|
| M1 | H4: meses pré-signup como zero (333/1.048 churn; 810/5.093 controle) | Janela restrita a `pm >= signup_month` nos DOIS lados; recálculo; registro como erro real | `solution/src/03_root_cause.py:1084-1141` (bloco H4; comentário de correção na linha 1087); `out/tables/t10_hypothesis_verdicts.csv` (H4); `solution/evidence/03_root_cause_report.md` §10; `process-log/reports/iteration-03-root-cause-report.md` §5/§7.7/§9; decisions D7 |
| L5/INFO-1/#6 | KM t6/t12/t18 por tempo exato → células vazias com follow-up | `surv_at_horizon` (função degrau; maior t ≤ horizonte; vazio só se não observável); coortes + segmentos | `solution/src/03_root_cause.py:482-491` (helper), `:518-520` (coortes), `:899, :917` (segmentos); `out/tables/t02_cohort_km.csv`, `t02a_cohort_km_month.csv`; evidence §3 |
| #5 | Gráfico B corta curvas < 0,55 | ylim (0,0; 1,02) + legenda fora da área de plotagem | `solution/src/03_root_cause.py:1409-1416`; `out/charts/b_km_by_signup_quarter.png` |
| L2/LOW-6/#7 | H6 RATE_FLAG estruturalmente inalcançável (1,5×70,4% = 105,6%) | Hipótese preservada; nota de erro de desenho; conclusão pelo critério alternativo pré-registrado SURV_FLAG (gap máx 6,9 p.p.) + spread | `solution/src/03_root_cause.py:1184-1228` (bloco H6); t10 (H6); evidence §10; decisions D8; report §7.9 |
| #3 | Suporte: seed `prev_ev` ausente (6 contas 2023-01..03 no controle) | Seed com primeiros eventos de 2023-01..03; recálculo (controle 3.288 → 3.162; 0,352→0,349; 5,3→5,1; 92,0→93,5; 34,5→35,0) | `solution/src/03_root_cause.py:766-773` (seed); `out/tables/t06_support_monthly.csv`; evidence §6; decisions D10; report §7.8 |
| L3/#8/LOW-3 | Rodapé gráfico C referencia "t04" inexistente | → `t03c_cac_equivalent.csv`; PNG C re-renderizado | `solution/src/03_root_cause.py:1445`; `out/charts/c_onboarding_exposure_by_duration.png` |
| L1/LOW-2/#9 | "39,6% em ≤30d" misturava bucket com janela acumulada | "43,6% ≤ 30d incluindo same-day (513.586); bucket 1-30d = 39,6% (467.262)" (derivado de t03c) | `solution/src/03_root_cause.py:1692-1699` (render §4); `process-log/reports/iteration-03-root-cause-report.md` §5 (H8); evidence §4 |
| L4 | "NÍVEL elevado de 2024-03 em diante" ignora vale de abril | "9 meses (2024-03, 05..12); vale em 2024-04 (15 < 1,5×11,5 = 17,25)" | `solution/src/03_root_cause.py:1617-1628` (render §2); evidence §2 |
| #4 | Mediana de uso alinhado sensível à definição | Nota de definição: mediana-das-medianas-mensais (primário) vs pooled (1,0 → 2,0 = +100%) | `solution/src/03_root_cause.py:688-713` (pooled), `:1726-1732` (render §5); evidence §5 |
| LOW-1/#1 | MD5 stale no process report (6324b0d4 ≠ commitado) | Hash histórico registrado como geração intermediária pré-D4; commitado = 996debf9; pós-fix = e25b2375 | `process-log/reports/iteration-03-root-cause-report.md` §8 |
| #2 | Timeline do process report conflita com CommitDate (20:47:32Z) | Tabela §2 alinhada ao CommitDate + nota de correção; passado git não reescrito | `process-log/reports/iteration-03-root-cause-report.md` §2 |
| LOW-4 | Linguagem H4 "não distinguem churn" forte demais | Números corrigidos + nota explícita de artefato (Δ 13,7 p.p.) no t10/evidence/report | t10 (H4 note); evidence §10; decisions D7 |
| LOW-5 | H2 rótulo sensível à definição de pico | Aceito como documentado (D1 registra racional; substância robusta sob ambas as definições: 1,52×/1,73×) | sem alteração (decisions D1) |
| #10 | Cosméticos (docstring t01..t11; constantes mortas) | Aceitos como não-bloqueantes (sem alteração funcional) | — |

## 3. Números recalculados (pós-correção; verificação independente 49/49)

| Número | Antes (9e02e18) | Depois (pós-fix) | Origem |
|---|---|---|---|
| H4 zero-uso churn / controle | 73,9% / 60,2% (Δ 13,7 p.p. — artefato) | **61,7% / 52,7% (Δ 9,0 p.p.)** | t10; recálculo independente (715/4.283 valores pós-signup) |
| Suporte controle N / tickets / escal. / FRT / res | 3.288 / 0,352 / 5,3% / 92,0 min / 34,5 h | **3.162 / 0,349 / 5,1% / 93,5 min / 35,0 h** | G7; t06; evidence §6 |
| KM t12 2023Q2 (era vazio) | vazio | **0,7037** (função degrau; t18 = 0,4444) | t02 |
| KM t6 2023-02 (mensal, era vazio) | vazio | **0,7778** | t02a |
| KM t6 2024Q3/Q4 | vazio | vazio (follow-up < 6 — regra explícita) | t02 |
| Exposição ≤30d acumulada | (não destacada) | **513.586 = 43,6%** (bucket 1-30d = 467.262 = 39,6%) | t03c; evidence §4 |
| H6 | "nenhum segmento com taxa ≥ 1,5× global" | nota: limiar 105,6% inalcançável; SURV_FLAG nenhum cruza (gap máx **6,9 p.p.**); spread 60,2–75,3% | t10 |
| Pico/KM t6/H1/H2/H3/H8/H9 | 43/191/22,51%; 0,6364…0,3077; 75,3%; 3,03×/1,73×; +225,3%; 68,4%; 83,7% | **inalterados** (verificados) | t01/t02/t03/t05/t10 |

Vereditos finais (thresholds pré-registrados preservados): H1 SUSTENTADA · H2 SUSTENTADA (aumento real de taxa) · H3 SUSTENTADA · H4 REFUTADA · H5 REFUTADA · H6 REFUTADA (critério alternativo SURV_FLAG) · H7 SUSTENTADA · H8 SUSTENTADA · H9 SUSTENTADA · H10 APLICADA.

## 4. Decisão causal e estabilidade da causa raiz

- **Causa raiz inalterada:** churn precoce de coortes novas, concentrado no onboarding — 75,3% dos primeiros eventos ≤ 6m (H1), 53,4% ≤ 90d e 68,4% do R1 ≤ 90d (H8), pico 2024-12 com mecanismo bucket 0-3m (83,7%; 2,37×) e aumento real de taxa (1,73× após controle de composição de tenure; esperado 24,82 vs observado 43) (H2/H9). Todas as lentes convergentes permanecem numericamente idênticas após as correções (as correções tocaram apenas H4/H5/H6/KM-células — nenhuma afeta H1/H2/H3/H7/H8/H9).
- **H4 (uso pré-evento):** veredito REFUTADA **mais robusto** após a correção — o Δ real (9,0 p.p. no desenho simétrico pós-signup; ou 1,5 p.p. se o controle fosse mantido como os revisores estimaram) fica muito abaixo do threshold pré-registrado de 25 p.p.; o Δ 13,7 p.p. era artefato de exposição (meses pré-signup inexistentes padronizados como zero) e está registrado como erro real corrigido (report §7.7; decisions D7).
- **H5 (suporte):** REFUTADA mantida com o controle contratualmente correto (seed `prev_ev`; N 3.162); direção mista preservada (escalação MAIOR no controle).
- **H6 (segmentos):** "sem heterogeneidade material" sustentado pelo critério alternativo pré-registrado válido (SURV_FLAG — nenhum segmento ≥ 10 p.p. abaixo da global; maior gap 6,9 p.p.) + spread reportado (60,2–75,3%). O limiar de taxa era estruturalmente inalcançável (erro de desenho documentado, não renegociado).
- **Status causal:** inalterado — `hipótese causal plausível` (mecanismo coorte/onboarding), `descritivo` (economia do onboarding), `não identificável` (papel causal de uso/suporte/reasons).

## 5. Validações pós-correção (resumo; detalhe no review-fix report)

- Script re-executado 2× no repo + sandbox: exit 0; **23 PASS / 0 WARN / 0 FAIL**; 20 outputs byte-a-byte idênticos (report `e25b2375b0fbe397962692d6bcb62239`); CWD diferente idêntico.
- Recálculo independente (implementação própria, `/tmp/opencode/fix-sandbox-02/independent_recalc.py`): **49/49 PASS** (pico, KM + carry-forward, onboarding, H4 corrigido, suporte seedado, H6, 3 MVs).
- FAIL estrutural ×2 (coluna renomeada; arquivo removido): exit 1, relatório regravado com "Falha estrutural", zero tracebacks, outputs de dados não regenerados (MD5 preservados).
- PNGs 6/6: PIL válidos; dimensões 1050–1713 × 392–685 px; 258–783 cores únicas; não-brancos 3,7–30,8%; gráfico B com eixo 0–1 (8/8 coortes íntegras); gráfico C com rodapé corrigido.
- Report↔CSV: números do report conferem com t01–t10 (H4/H5/H6/suporte/KM verificados linha a linha).
- Git: escopo 100% `submissions/jose-nascimento/`; `git diff --check` limpo; autor do candidato; sem amend/force/rebase; push validado (local == remote).

## 6. Gate It03

**CONCLUDED** — 3 veredictos `PASS_WITH_FIXES`, finding material M1 corrigido com recálculo e registro de erro real; correções factuais/robustez aplicadas; revalidação completa executada. Iteração 04 permanece **PENDING** (não iniciada; sem watchlist, sem recomendações — escopo respeitado).
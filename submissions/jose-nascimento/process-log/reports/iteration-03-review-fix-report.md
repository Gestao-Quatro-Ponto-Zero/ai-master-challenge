# Report — Iteração 03 · Correção do review gate 3x (agente corretor sequencial)

- **Iteração:** 03 (causa raiz, coortes e onboarding economics) — correção pós-gate
- **Data:** 2026-08-28
- **Executor:** exatamente um subagente `deepseek-max` (via OpenCode Go), sob orquestração do opencode — agente corretor sequencial do review gate (execution-plan, regra 2/4)
- **Base sob correção:** `9e02e18daf8b8a77a5ae4f552b6b5713b23a142e` (HEAD esperado confirmado antes de qualquer alteração; working tree limpo)
- **Commit desta correção:** `fix: correct exposure windows in root cause analysis` (hash completo no §11)
- **Ledger do gate:** [`process-log/reviews/iteration-03-review-summary.md`](../reviews/iteration-03-review-summary.md)
- **Prompt integral desta correção:** [`process-log/prompts/iteration-03-review-fix-prompt.md`](../prompts/iteration-03-review-fix-prompt.md)
- **Tempo de relógio (F11):** ~1h30min (leitura das 3 revisões + análise do viés de exposição nos dois lados do H4 + implementação das 12 correções + recálculo independente 49/49 + sandbox FAIL/CWD + documentos) — acumulado analítico ~7h15; orquestrador mantém o controle (política de contenção §2 do plano)

---

## 1. Status

**PASS** — finding material M1 corrigido (com recálculo e registro de erro real), 11 correções factuais/robustez aplicadas, revalidação completa (49/49 independentes; 23 PASS / 0 WARN / 0 FAIL; idempotência; FAIL estrutural; 6 PNGs). Gate It03 `CONCLUDED` no checklist; Iteração 04 **não** iniciada (permanece `PENDING`).

## 2. Matriz dos 3 reviews

| Revisor | Veredicto | Findings | Tratamento |
|---|---|---|---|
| R1 (`review-4c090c69.md`) | `PASS_WITH_FIXES` | **M1** (H4: meses pré-signup como zero; Δ 13,7 p.p. ≈9× superestimado); L1 (wording ≤30d); L2 (H6 RATE_FLAG inalcançável); L3 (t04→t03c); L4 (vale de abril); L5 (KM por tempo exato); I1–I3 | **M1 corrigido** (simétrico, D7); L1–L5 corrigidos; I1–I3 aceitos como trade-offs documentados (pareamento por conta e tier como "quando viável" — sem impacto) |
| R2 (`review-b41e9a07.md`) | `PASS_WITH_FIXES` | LOW-1 (MD5 stale); LOW-2 (39,6% vs 43,6%); LOW-3 (t04); LOW-4 (linguagem H4); LOW-5 (sensibilidade H2 ao pico); LOW-6 (H6 inalcançável); INFO-1 (KM); INFO-2 (coluna contas únicas) | LOW-1/2/3/4/6 corrigidos; LOW-5 aceito como documentado (D1; substância robusta sob ambas as definições — 1,52×/1,73×); INFO-1 corrigido (D9); INFO-2 aceito (ambas as visões de pico apontam 2024-12) |
| R3 (`review-63a29930.md`) | `PASS_WITH_FIXES` | 2 obrigatórios (MD5 stale; timeline vs CommitDate); #3 (seed `prev_ev`); #4 (mediana alinhada pooled); #5 (gráfico B corta curvas); #6 (KM carry-forward); #7 (H6 inalcançável); #8 (t04); #9 (wording 39,6%); #10 (cosméticos) | Obrigatórios corrigidos; #3/#4/#5/#6/#7/#8/#9 corrigidos; #10 aceito (cosmético, sem alteração funcional) |

## 3. Correções aplicadas (resumo técnico; matriz completa com arquivo:linha no review summary)

1. **H4 (M1)** — janela pré-evento restrita a `pm >= signup_month` nos DOIS lados (`03_root_cause.py` bloco H4). Quantificação do viés: lado churn 333/1.048 = 31,8% dos valores pré-signup; lado controle 810/5.093 = 15,9% (caso `m == signup_month` — os revisores assumiram controle limpo, mas o código incluía o mesmo erro; a expectativa "61,7% vs 60,2%" dos revisores mantinha o viés no controle, o que contrariaria o contrato §2 — "meses anteriores ao signup não existem para a conta"). Resultado derivado do código: **61,7% vs 52,7% (Δ 9,0 p.p.)** — veredito REFUTADA (threshold pré-registrado 25 p.p.) inalterado e mais robusto. Δ 13,7 p.p. registrado como artefato (report §7.7; decisions D7; nota no t10).
2. **KM (D9)** — `surv_at_horizon`: função degrau no maior t ≤ horizonte; vazio somente quando follow-up < horizonte (não observável). Aplicado a coortes (t02/t02a) e segmentos (t07). Ex.: 2023Q2 t12 = 0,7037, t18 = 0,4444 (antes vazios); 2023-02 mensal t6 = 0,7778; 2024Q3/Q4 seguem vazios (correto).
3. **Gráfico B** — ylim (0,0; 1,02) + legenda fora da área de plotagem; 8/8 coortes íntegras (2024Q2 chega a 0,3077 sem corte).
4. **H6 (D8)** — hipótese original preservada; nota explícita: limiar RATE_FLAG (1,5×70,4% = 105,6%) estruturalmente inalcançável — erro de desenho do pré-registro documentado (não renegociado, não justificativa retroativa); conclusão pelo critério alternativo pré-registrado válido SURV_FLAG (nenhum segmento ≥ 10 p.p. abaixo da global 0,4428; maior gap 6,9 p.p.) + spread 60,2–75,3%.
5. **Suporte (D10)** — seed `prev_ev` com primeiros eventos de 2023-01..03 (6 contas fora do controle): controle 3.288 → **3.162**; tickets/conta 0,352 → **0,349**; escalação 5,3 → **5,1%**; FRT 92,0 → **93,5 min**; resolução 34,5 → **35,0 h** — imaterial; H5 REFUTADA mantida (N 3.162 ≥ 30; G7 PASS).
6. **Gráfico C** — rodapé "tabela t04" → `t03c_cac_equivalent.csv`.
7. **Wording ≤30d** — 43,6% ≤ 30d incluindo same-day (513.586; derivado de t03c) vs bucket 1-30d = 39,6% (467.262); evidence §4 ganhou linha de exposição acumulada (≤30d/≤60d/≤90d).
8. **Período elevado** — "9 meses (2024-03, 2024-05..2024-12); vale em 2024-04 (15 primeiros eventos < 1,5× mediana 11,5 = 17,25)" — achado mantido (nível elevado real e sustentado).
9. **Mediana de uso alinhado** — nota de definição: mediana-das-medianas-mensais (primário, inalterado) vs pooled 1,0 → 2,0 (+100%) — veredito H3 dirigido pela variante raw (2,0 → 2,0), robusta.
10. **Process report** — MD5: 6324b0d4 registrado como geração intermediária (pré-D4, evidenciado por `it03_md5_1.txt`/sandbox pré-fix), commitado = 996debf9, pós-fix = e25b2375; timeline §2 alinhada ao CommitDate 20:47:32Z com nota de correção (passado git não reescrito).

## 4. Números recalculados (antes → depois; origem no pipeline e no recálculo independente)

| Métrica | Antes (`9e02e18`) | Depois | Veredito |
|---|---|---|---|
| H4 zero-uso churn / controle / Δ | 73,9% / 60,2% / 13,7 p.p. (artefato) | **61,7% / 52,7% / 9,0 p.p.** | REFUTADA (inalterado; mais robusto) |
| Suporte controle N / tickets / escal. / FRT / res. | 3.288 / 0,352 / 5,3% / 92,0 / 34,5 h | **3.162 / 0,349 / 5,1% / 93,5 / 35,0 h** | REFUTADA (inalterado) |
| KM t12/t18 2023Q2 | vazio / vazio | **0,7037 / 0,4444** | — |
| KM t6 2023-02 (mensal) | vazio | **0,7778** | — |
| Exposição ≤30d acumulada | (não destacada) | **513.586 = 43,6%** | H8 SUSTENTADA (inalterado) |
| H6 nota | "nenhum segmento ≥ 1,5× global" | limiar 105,6% inalcançável; SURV_FLAG: gap máx **6,9 p.p.**; spread 60,2–75,3% | REFUTADA (inalterado; base correta) |
| Pico/KM t6/H1/H2/H3/H8/H9 | 43/191/22,51%; 0,6364–0,3077; 75,3%; 3,03×/1,73×; +225,3%; 68,4%; 83,7%/2,37× | **inalterados** | todos inalterados |

## 5. Estabilidade da causa raiz

Nenhuma correção afetou as lentes da causa raiz (H1/H2/H3/H7/H8/H9 — distribuição de tenure, taxa com controle de composição, economia do onboarding, mecanismo do pico). As correções tocaram exclusivamente H4 (uso pré-evento — veredito REFUTADA reforçado), H5 (suporte — números corrigidos sem mudança de direção), H6 (base do veredito explicitada) e células KM de auditoria. **Causa raiz declarada permanece:** churn precoce de coortes novas, concentrado no onboarding, com aumento real de taxa no pico (1,73× após controle de composição; bucket 0-3m com 83,7% do pico a 2,37×) — hipótese causal plausível, não refutada por nenhuma das 3 revisões.

## 6. Validações executadas

| Validação | Resultado |
|---|---|
| Re-execução pós-fix (repo + sandbox, 2×) | exit 0; **23 PASS / 0 WARN / 0 FAIL**; outputs byte-a-byte idênticos (report `e25b2375b0fbe397962692d6bcb62239`) |
| CWD diferente (execução de `/tmp` com path absoluto) | exit 0; report idêntico |
| Recálculo independente (implementação própria, só CSVs raw + painel) | **49/49 PASS** — pico (43/191/22,51%; meses elevados), KM (t6 por coorte + carry-forward t12/t18 + 2024Q4 vazio), onboarding (buckets; ≤30d 513.586 = 43,6%; 1-30d 39,6%), H4 corrigido (61,7/52,7/Δ9,0; N 715/4.283), suporte seedado (3.162; 0,349/5,1/93,5/35,0; churn inalterado 346/0,309), H6 (105,6%; gap 6,9 p.p.; spread 60,2–75,3%), 3 MVs (pico dez/24; A-039727; Cybersecurity 100/72/279.062) |
| FAIL estrutural (2 cenários: coluna `churn_date` renomeada; `support_tickets.csv` removido) | exit 1 ×2; relatório regravado com "Falha estrutural"; zero tracebacks; outputs de dados NÃO regenerados (MD5 preservados) |
| PNGs (6) | PIL válidos; 1050–1713 × 392–685 px; 258–783 cores únicas; não-brancos 3,7–30,8%; B com eixo 0–1 (nenhuma curva cortada); C com rodapé corrigido |
| Report↔CSV | números do report conferem com t01–t10 (H4/H5/H6/suporte/KM linha a linha) |
| Hygiene/escopo/segredos | `git diff --check` limpo; 100% `submissions/jose-nascimento/`; grep `/tmp`/`/home`/`ubuntu` = zero ocorrências fora do prompt arquivado; hipóteses pré-registradas intactas (git diff vazio no arquivo de hipóteses) |

## 7. Arquivos alterados/criados

**Alterados (código/outputs):** `solution/src/03_root_cause.py` (H4, KM helper, chart_b, chart_c, H6, suporte seed, render §2/§3/§4/§5); `solution/evidence/03_root_cause_report.md`; `solution/out/tables/t02_cohort_km.csv`, `t02a_cohort_km_month.csv`, `t06_support_monthly.csv`, `t10_hypothesis_verdicts.csv`; `solution/out/charts/b_km_by_signup_quarter.png`, `c_onboarding_exposure_by_duration.png`, `e_support_churn_vs_control.png`.
**Alterados (processo):** `process-log/reports/iteration-03-root-cause-report.md` (timeline, MD5, §5/§7/§8/§9/§10/§11); `process-log/decisions/iteration-03-root-cause-decisions.md` (adendo D7–D11); `process-log/management/orchestrator-checklist.md` (gate It03); `process-log/management/execution-plan.md` (status do gate).
**Criados:** `process-log/reviews/iteration-03-review-summary.md`; `process-log/prompts/iteration-03-review-fix-prompt.md`; este report.
**Intactos:** hipóteses pré-registradas (`iteration-03-root-cause-hypotheses.md`), contrato analítico, decisions D1–D6, t01/t02b/t03/t03b/t03c/t05/t07/t08/t09, charts a/d/f (byte-idênticos).

## 8. Riscos residuais (monitorar; não bloqueiam)

1. **H4 Δ entre definições:** 9,0 p.p. (desenho simétrico pós-signup) vs 1,5 p.p. (se o controle mantivesse o viés, como estimaram os revisores) — ambos ≪ 25 p.p.; qualquer variante mantém REFUTADA. It04 deve usar 61,7%/52,7% (números corrigidos).
2. **H6:** não citar "REFUTADA" como prova de homogeneidade total — há spread 15,1 p.p. nas taxas e 17,2 p.p. na sobrevivência t6; o rótulo correto é "sem heterogeneidade MATERIAL segundo os critérios pré-registrados aplicáveis".
3. **Thresholds estruturalmente inalcançáveis:** lição registrada (D8) para hipóteses de futuras iterações (preferir margem absoluta ou múltiplo alcançável).
4. **Concentração de R1 em dez/2024 (48,7%)** — descritiva, possível artefato de geração; manter o rótulo no handoff It04.
5. **Determinismo vs versão de pandas** (3.0.5 neste ambiente; pinning na It06) — re-execução reproduziu byte-a-byte.

## 9. Handoff para a Iteração 04 (inalterado em substância)

A It04 permanece `PENDING` e NÃO foi iniciada. Entradas e restrições no handoff do report da iteração (§11, atualizado com os números corrigidos): watchlist com contas reais, jornada completa, reativações quantificadas, viés contra contas novas declarado — sem usar uso/suporte/reasons como features sem rótulo (NO-GO H4/H5) e sem tratar segmentação como mecanismo primário (H6).

## 10. Limitações declaradas

- Inspeção visual de PNGs não realizada pelo modelo (sem suporte a imagem): validação programática (PIL/dimensões/cores) + verificação do código gerador + OCR de textos não usado; o eixo do gráfico B e a legenda foram verificados por construção (ylim contém todos os valores; legenda fora da área de plotagem).
- O recálculo independente é do próprio agente corretor (implementação separada do pipeline, mesmos inputs); a revisão 3x original permanece como evidência externa (3 sandboxes distintos).

---

*Prompt integral em [`process-log/prompts/iteration-03-review-fix-prompt.md`](../prompts/iteration-03-review-fix-prompt.md); ledger do gate em [`process-log/reviews/iteration-03-review-summary.md`](../reviews/iteration-03-review-summary.md); decisões (adendo D7–D11) em [`process-log/decisions/iteration-03-root-cause-decisions.md`](../decisions/iteration-03-root-cause-decisions.md).*
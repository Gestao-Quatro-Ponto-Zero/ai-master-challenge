# Report de Correção — Review Gate da Iteração 04 + Adendo (fixer sequencial)

- **Data:** 2026-08-28
- **Agente:** corretor sequencial `deepseek-max` (DeepSeek V4 Flash, max reasoning, via OpenCode Go), sob orquestração do opencode
- **HEAD base:** `2a4b5b437c80a7b13f0ca9ad14d9bbae6d2036dd` (esperado no prompt) — confirmado no início (working tree limpo, branch `submission/jose-nascimento`)
- **Prompt integral:** `process-log/prompts/iteration-04-review-fix-prompt.md` (arquivado)
- **Tempo de relógio (F11):** ~2h30min (3 reports de revisão + correções analíticas/documentais + refinamento visual dos 6 PNGs + pruning + validações completas + documentos) — acumulado analítico ~12h35

---

## 1. Status

**PASS** — todos os findings factuais corrigidos; narrativa derivada em runtime com gates; 6 PNGs essenciais re-renderizados com layout validado programaticamente; 4 PNGs pruned removidos do git e do gerador (não reaparecem); scripts 03/04 validados (23/34 PASS, idempotência, CWD, FAIL estrutural, MVs, leakage); commit `fix: refine lifecycle evidence and essential charts` e push concluídos; gate It04 + adendo `CONCLUDED`; It05 `PENDING`. Nenhuma recomendação de It05 iniciada.

## 2. Correções analíticas/factuais

| # | Correção | Onde |
|---|---|---|
| 1 | D7 atualizado: KM finais 90d=0,653, 180d=0,476, mediana=187d (derivados em runtime no relatório; exploração com censura incompleta marcada como SUPERADA); âncora G13-km | `process-log/decisions/iteration-04-watchlist-decisions.md` (D7); `solution/src/04_lifecycle_watchlist.py` (gate G13-km) |
| 2 | Sensibilidade 180d qualificada: "as demais ficam <= 1,05 **com o filtro pré-registrado N >= 25 (D4)** — sem esse filtro há exceções aparentes e instáveis (N < 25, cutoff 2024-06-30): R_B 1,05 (N=20); R_G 1,36 (N=12); R_H 1,61 (N=16)" — derivada da t14 em runtime | render §6 do `04_lifecycle_watchlist.py`; evidence §6; gate G13-sens180 |
| 3 | R_B/S3 com rounding consistente: strings dos segmentos derivadas de `bt_summary` (R_B 0,52/0,41/1,29; R_G citado apenas na sensibilidade); S3 sem "regras B/G"; KM do S3 derivado (0,653, mediana 187d) | `priority_segments` + `s3_row` (runtime); t15/evidence regenerados |
| 4 | "maioria das reativações é recente" removida → "26 de 61 flags (42,6%) — parcela substancial, NÃO maioria"; maioria das CENSURADAS é recente (20/37 = 54,1%) — derivado em runtime | render §3; `recent_flags`/`recent_censored` no script; gate G13-reactivation |
| 5 | Top-3 ordenado por `winner_mrr` desc com tiers: A-c70870 (33.830, A), A-56962b (32.437, C), A-18793f (29.452, A) | `process-log/reports/iteration-04-lifecycle-watchlist-report.md` §6 |
| 6 | Narrativa hardcoded eliminada (175/70,5%; 61/55; 24/61=39,3%; 18.507; 28.766.224; 3.668.852; 1.179.139; 110; lifts 1,57/1,56/1,83; KM; strings de segmentos) — tudo derivado das variáveis/tabelas em runtime; 5 gates G13 (km, reactivation, backtest-exact, sens180, narrative) para os claims executivos materiais; INFO-2 atendido (t13 com `winner_mrr_prev`, R2 do mês anterior) | render do `04_lifecycle_watchlist.py`; `state_cycles`; gates G13; t13 |
| 7 | D1–D9: nota de transparência (commitadas no mesmo commit `adbbad7`; cronologia git não prova separação; conteúdo interno + auto-relato como evidência) no decisions file, no report da iteração e no evidence (render §1); F11 reescrito ("acima do gatilho de contenção §2.5b — decisão consciente por revisão adicional; custo registrado; trims a partir da It05") | decisions (cabeçalho); report It04 §1; render §1; `orchestrator-checklist.md` (F11) |
| 8 | Glob de charts do It03 escopado por manifesto (04 PNGs + 13 tabelas; check C01-charts falha se pruned reaparecer); It04 com manifesto próprio (2 PNGs + check de fora-do-manifesto) | `03_root_cause.py` main(); `04_lifecycle_watchlist.py` main() |

## 3. Refinamento visual (padrão único; sem dashboard/design system)

- Padrão: 150dpi; fundo branco; spines topo/direita removidas; paleta Okabe-Ito colorblind-safe; títulos curtos; unidades explícitas; rodapés em `fig.text` (coordenadas de figura, 2 linhas, dentro do canvas); margens explícitas (`subplots_adjust`); **sem `bbox_inches="tight"`** (causa raiz dos canvas esticados e eixos esmagados).
- `a_monthly`: ylim com headroom (1,18×pico) → anotação do pico dentro dos eixos; ticks mensais rotacionados 90° legíveis; ticks y explícitos (sem overhang).
- `b_km`: figura 10×6; eixos ocupam 90% da largura; legenda 2 colunas em faixa própria abaixo dos eixos (sem sobrepor título/dados); curvas íntegras 0–1; ticks explícitos (0,6,12,18,24 / 0,0–1,0).
- `c_onboarding`: barras horizontais em ordem de duração (0d, 1-30d, 31-60d, 61-90d, 91-180d, 181-365d, >365d) com "% · US$" ao lado; grid vertical leve; nada sobreposto.
- `d_usage`: 2 painéis mantidos; ticks 90°; rodapé compacto em 2 linhas; escalas claras.
- `It04_c`: scatter mantido; legenda em faixa própria acima dos eixos (não cobre pontos); labels com offset em pontos; ticks log explícitos (sem overhang 10^2/10^5).
- `It04_d`: substituído por **dot/errorbar plot horizontal** — regras no eixo y, lift no x, 3 cutoffs por cor/offset (±0,22), CI de Wilson (escalado pela baseline), linhas verticais em 1,0 (baseline) e 1,15 (limiar D4), legenda fora dos dados (acima), R_D destacado por faixa leve + marcadores maiores (sem poluição).

## 4. Pruning (keep-set final = 6 PNGs)

- **Removidos do git e do gerador:** `e_support_churn_vs_control.png` (→ t06/t09), `f_segment_first_event_rates.png` (→ t07), `It04_a_recurrence_reactivation.png` (→ t12), `It04_b_cycle_lenses.png` (→ t13, com `winner_mrr_prev`).
- **Keep-set commitado:** `a_monthly_events_and_rate.png`, `b_km_by_signup_quarter.png`, `c_onboarding_exposure_by_duration.png`, `d_usage_volume_vs_intensity.png`, `It04_c_lifecycle_vs_current_mrr.png`, `It04_d_backtest_lift.png`.
- Reports/manifests/gates/links atualizados para tabelas: evidence 03/04 regenerados pelos scripts; D9 (decisions), report da iteração, review summary, este report.
- Garantia de não-reaparecimento: manifestos explícitos + checks `C01-charts` (falham se arquivo fora do manifesto existir) nos dois scripts.

## 5. Validações executadas

| Validação | Resultado |
|---|---|
| Scripts 03 e 04 do zero (sandbox + repo) | 03: 23 PASS / 0 WARN / 0 FAIL; 04: 34 PASS / 0 WARN / 0 FAIL |
| Idempotência 2× (sandbox e repo) | 8 outputs (2 evidence + 6 PNGs) byte-a-byte idênticos (MD5) |
| CWD diferente (path absoluto) | idênticos (MD5) |
| Repo == sandbox | MD5 idênticos entre repo e sandbox |
| FAIL estrutural (coluna `status` renomeada; 03 e 04) | exit 1; relatório regravado com "Falha estrutural"; 0 tracebacks; tabelas/PNGs preservados (MD5); restauração → idênticos |
| Report ↔ CSV | 21/21 checks reais (lifts exatos t14 [R_B 0,515/0,405/1,295; R_D 1,574/1,556/1,835; R_G 180d 1,362 N=12; R_H 180d 1,606 N=16]; strings de segmentos derivadas; watchlist 20/8/8/4 e Σ 392.030; t13 R2 com winner_mrr_prev 12.736+5.771; t12 KM) |
| 3 MVs It04 (independentes) | MV1a A-68f37c (06-29→12-18, gap 172d; 2ª reativação censurada) ✓; MV1b A-956988 (12-30, follow-up 1d, censurada) ✓; MV2 rank shifts (overlap 7; A-68f37c 5→1; A-a8d89d só na jornada) ✓; MV3 A-c70870 (tenure 70, MRR 33.830, 1 evento, proxy 34.419, último evento 12-13) ✓ |
| Leakage | G6b 5/5 PASS (coluna a coluna — lógica inalterada, re-executada) |
| Validação visual programática (`/tmp/opencode/it04-fix-sandbox/visual_validate.py`) | PASS 6/6: eixo principal ≥ 0,695 da largura (painéis somam ≥ 0,816); 0 overlaps legend×title / legend×axes / ticks; 0 textos clipped; 6 PNGs abrem (1170–1560 × 615–900 px; 258–835 cores); 4 PNGs pruned ausentes |
| Números It03/It04 estáveis | todos os checks de âncora (G1–G15 It03; G1–G13 It04) PASS; nenhum número de conclusão alterado pelas correções (apenas textos derivados e layout) |
| `git diff --check` / escopo / segredos | limpo; apenas `submissions/jose-nascimento/`; sem paths pessoais/segredos fora da exceção documentada |

## 6. Arquivos

**Alterados (código/outputs):** `solution/src/03_root_cause.py` (charts a–d reescritos; e/f removidos; manifesto de charts/tabelas); `solution/src/04_lifecycle_watchlist.py` (narrativa derivada em runtime; charts a/b removidos; c/d reescritos; gates G13; `winner_mrr_prev`; manifesto); `solution/evidence/03_root_cause_report.md` (regenerado); `solution/evidence/04_lifecycle_watchlist_report.md` (regenerado); `solution/out/charts/` (6 PNGs re-renderizados; 4 removidos via `git rm`); `solution/out/tables/t13_state_cycles.csv` (coluna `winner_mrr_prev`).

**Alterados (processo):** `process-log/decisions/iteration-04-watchlist-decisions.md` (D7; D9; nota de transparência); `process-log/reports/iteration-04-lifecycle-watchlist-report.md` (§1 honestidade; §2 charts; §6 top-3; §8/§9 pós-gate); `process-log/management/orchestrator-checklist.md` (cabeçalho; B3; B10; F11); `process-log/management/execution-plan.md` (cabeçalho/status; It04); `process-log/management/orchestration-architecture.md` (§7 tabela It04; §9 status); `process-log/reports/iteration-03-root-cause-report.md` (notas de pruning pós-gate).

**Criados:** `process-log/reviews/iteration-04-review-summary.md` (ledger do gate); `process-log/prompts/iteration-04-review-fix-prompt.md` (prompt integral); `process-log/reports/iteration-04-review-fix-report.md` (este).

**Intactos:** hipóteses It03, contrato analítico, decisions It02/It03, tabelas t01–t10 (conteúdo), prompt/report do adendo (históricos), README (sem mudança necessária neste passe).

## 7. Git

- **Commit:** `fix: refine lifecycle evidence and essential charts` (sem amend); `git rm` dos 4 PNGs pruned; `git add -f` apenas nos paths pretendidos.
- **Push:** realizado para `origin/submission/jose-nascimento`; local == remote confirmado; working tree limpo; `git diff --check` limpo.
- Disciplina: sem amend/force/config/destrutivo.

## 8. Riscos e handoff para a It05

1. **Extrapolação do spike sintético:** lifts de R_D crescem exatamente na janela do pico (1,83) — cautela mantida no report; a It05 deve tratar ações em faixa, nunca ponto.
2. **Poder estatístico:** CIs largos; N < 25 nas exceções 180d e nos tiers B/C; CI do lift ainda não reportado (opcional para It05/It07).
3. **Pré-especificação não auditável via git (LOW-4):** mitigada por nota de transparência; a partir da It05, commitar decisões antes do código (prática It03).
4. **Time budget:** acumulado ~12h35 vs 4–6h — acima do gatilho de contenção (§2.5b); F11 registra a decisão e o plano de trims formais a partir da It05.
5. **Inspeção ocular do orquestrador:** pendente sobre os 6 PNGs (este report fornece as métricas objetivas: eixos ≥ 69,5% da largura, 0 overlaps, 0 clips, dimensões 1170–1560 × 615–900 px).
6. **It05 (próxima):** recebe o único sinal validado (onboarding ≤90d, lift 1,57–1,83) para ações de ativação em faixa; segmentos S1–S5 com N/US$; watchlist 8/8/4 como priorização operacional (sem score); nada de CAC/winback factual (não existe na base); NÃO iniciada neste passe.
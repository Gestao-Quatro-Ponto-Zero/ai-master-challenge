# Ledger de Revisão — Iteração 04 · Ciclos de reativação, jornada, backtest e watchlist + Adendo de Arquitetura (review gate 3x + correção sequencial)

- **Iteração revisada:** 04 (lifecycle/watchlist) + adendo `docs: document multi-agent orchestration architecture`
- **Commits sob revisão:** base `12ff47c9bcc29f1dbd81aba186985c1191a8f10b` · implementação `adbbad7` (`feat: prioritize accounts by lifecycle and validated risk signals`) · fix R1 `fb9d2de` (`fix: report R1 exposure of repeat-event and reactivated accounts by lens`) · adendo `2a4b5b4` (`docs: document multi-agent orchestration architecture`) · HEAD revisado `2a4b5b437c80a7b13f0ca9ad14d9bbae6d2036dd`
- **Revisores:** 3 agentes `deepseek-max` independentes, modo read-only, em paralelo (2026-08-28) — sandboxes fora do repo; **repo intacto** (working tree limpo antes/depois de cada revisão)
- **Relatórios dos revisores:** `/tmp/opencode/ai-master-review-reports/iteration-04/review-9c41f7a2.md` · `review-df141f4f.md` · `review-3a4f8efa.md` (veredictos e evidências na íntegra)
- **Correção sequencial:** agente corretor (este) — commit `fix: refine lifecycle evidence and essential charts`; ver `process-log/reports/iteration-04-review-fix-report.md` e prompt arquivado `process-log/prompts/iteration-04-review-fix-prompt.md`
- **Gate It04:** `CONCLUDED` (3 veredictos `PASS_WITH_FIXES`; nenhum finding material analítico — todas as correções são documentação/consistência (LOW) + qualidade visual (LOW/MEDIUM); correções aplicadas com revalidação completa: 23 PASS (It03) / 34 PASS (It04), idempotência byte-a-byte, CWD diferente, FAIL estrutural, visual programático PASS). Adendo: revisado no mesmo gate e `CONCLUDED`. Iteração 05 permanece `PENDING`.

---

## 1. Veredictos dos revisores

| Revisor | Veredicto | Findings analíticos/documentais | Findings visuais |
|---|---|---|---|
| review-9c41f7a2 | **PASS_WITH_FIXES** | F1 (KM stale no D7), F2 (≤1,05 falso — R_H 1,61 n=16 e R_G 1,36 n=12), F3 (R_B 0,41/1,29 vs 0,40/1,30), F4 (42,6% ≠ maioria), F5 (top-3 fora de ordem), F6 (números narrativos hardcoded), F7 (F11 "dentro da política"), F9 (rótulo S3 "out-dez" ok) | F8: 6 PNGs com defeitos (causas no código) |
| review-df141f4f | **PASS_WITH_FIXES** | MEDIUM-1 (≤1,05 falso), LOW-1 (S3 "0,52/0,40/1,30" ≠ t14), LOW-2 (42,6% ≠ maioria), LOW-3 (KM stale D7), LOW-4 (pré-especificação não verificável via git), INFO-1 (top-3), INFO-2 (t13 winner_mrr 0), INFO-3 (F11) | §7: 6 PNGs (b/e/It04_b/It04_d/c/a) com causas no código |
| review-3a4f8efa | **PASS_WITH_FIXES** | L1 (glob `*.png` do 03 quebra com PNGs It04 no diretório), L2 (F11), 2 obrigatórios factuais (42,6%; ≤1,05) | §8: 6 PNGs confirmados por medição + correções mínimas validadas em sandbox |

**Convergência:** nenhum revisor refutou qualquer número, método ou conclusão — 100% dos números-chave recalculados de forma independente bateram (recorrência/reativação/KM/ciclos/proxy/rank/backtest 45–49 valores/watchlist/segmentos/exposição); zero leakage; nomenclatura proporcional à evidência. Os 3 revisores também validaram o **adendo de arquitetura** (URLs 3/3 e 7/7 verificadas; distinção runtime metadata vs claims externas correta; honestidade de diversidade explícita; nenhuma claim não sustentada). Fixes exigidos: documentação/consistência narrativa (LOW) e qualidade visual (LOW/MEDIUM).

## 2. Matriz finding → ação → arquivo:linha (pós-correção)

| # | Finding (revisores) | Ação | Arquivo:linha (pós-fix) |
|---|---|---|---|
| F1/LOW-3 | D7 com KM stale (0,72/0,64/mediana não alcançada) vs finais 0,653/0,476/187d | D7 atualizado com valores finais + nota "exploração superada" (censura incompleta documentada no report da iteração §4.1); âncora G13-km | `process-log/decisions/iteration-04-watchlist-decisions.md` (D7); `solution/src/04_lifecycle_watchlist.py:1545-1551` (gate G13-km) |
| F2/MEDIUM-1 | "as demais ficam <= 1,05" factualmente falso (R_G 1,36 N=12; R_H 1,61 N=16 no cutoff 06-30; R_B 1,05 N=20) | Frase derivada em runtime da t14 (filtro N>=25 pré-registrado + exceções listadas com N e cutoff); gate G13-sens180 | `04_lifecycle_watchlist.py` (bloco `exc_parts`/`exc_txt` no render; sentença da seção 6); evidence §6; gate G13-sens180 (`:1567-1575`) |
| F3/LOW-1 | R_B inconsistente (0,40/1,30 vs 0,41/1,29; string S3 "regras B/G") | Strings dos segmentos derivadas de `bt_summary` (R_B 0,52/0,41/1,29 — rounding único de 2 casas em toda a cadeia); S3 sem "regras B/G" | `04_lifecycle_watchlist.py:588-640` (`priority_segments` com helper `lifts()`), `:1456-1479` (s3_row derivado); t15/evidence regenerados |
| F4/LOW-2 | "a maioria das reativações é recente" (26/61=42,6%) | "26 de 61 (42,6%) — parcela substancial, NÃO maioria"; maioria das CENSURADAS é recente (20/37=54,1%) — derivado em runtime; gates G13-reactivation | `04_lifecycle_watchlist.py` (`recent_flags`/`recent_censored` em `reactivation_episodes`, `:283-290`; render §3); gate G13-reactivation |
| F5/INFO-1 | "top-3" fora de ordem (A-56962b > A-18793f) | "maiores MRR da watchlist (top-3 por winner_mrr desc): A-c70870 (33.830, Tier A), A-56962b (32.437, Tier C), A-18793f (29.452, Tier A)" | `process-log/reports/iteration-04-lifecycle-watchlist-report.md` §6 |
| F6 | Números narrativos hardcoded (175/70,5%; 61/55; 24/61; 18.507; 28.766.224; 3.668.852; 1.179.139; 110; lifts; KM; strings de segmentos) | Todas as frases derivadas em runtime das variáveis/tabelas; gates G13 (km, reactivation, backtest-exact, sens180, narrative) para os claims executivos materiais; INFO-2 atendido (coluna `winner_mrr_prev` na t13, R2 do mês anterior) | `04_lifecycle_watchlist.py` (bloco de derivação no render `:950-990`; seções 2–6 e guia da watchlist); `state_cycles` (`dec_r2_sum`, `winner_mrr_prev`, `:324-370`); t13; gates G13 (`:1544-1595`) |
| F7/L2/INFO-3 | F11 "dentro da política" com acumulado ~10h05 (gatilho §2.5b = ~5h antes da It09 cruzado) | F11 reescrito: "acima do gatilho de contenção do plano... decisão consciente do orquestrador/candidato por revisão adicional; custo registrado; trims formais a partir da It05" | `process-log/management/orchestrator-checklist.md` (F11) |
| LOW-4 | D1–D9 commitadas no mesmo commit do código (cronologia git não prova separação) | Nota de transparência no arquivo de decisões + no report da iteração + no evidence (render) | `iteration-04-watchlist-decisions.md` (cabeçalho); `iteration-04-lifecycle-watchlist-report.md` §1; `04_lifecycle_watchlist.py` render §1 |
| L1 | Glob `*.png` do script 03 falha com PNGs It04 no mesmo diretório (C01-charts) | Scope por manifesto explícito nos DOIS scripts (03: 4 PNGs; 04: 2 PNGs + check de "fora do manifesto"); tabelas do 03 também escopadas (13) | `03_root_cause.py:2035-2058` (manifesto + stale check), `:2072-2084` (tabelas); `04_lifecycle_watchlist.py:1660-1678` |
| F8 (visual) | 6 PNGs: b (legenda×título, canvas esticado), e (3 métricas num eixo, y-label×título), It04_b (eixos 30px), It04_d (congestionado, metade vazia), c (labels x sobrepostos), a (anotação no título) | Ver seção 5 (refinamento visual) + pruning (seção 6): causa raiz comum (rodapé em `ax.text(0,-0.2x)` + `bbox_inches="tight"` esticava o canvas) eliminada | `03_root_cause.py` (charts a–d reescritos; `_footer` em `fig.text`; margens explícitas; sem tight bbox; 150dpi); `04_lifecycle_watchlist.py` (charts c/d reescritos) |
| F9 | Rótulo S3 "out-dez/2024" = (2024-10-02, 2024-12-31] | Aceito como aproximação (mencionado na revisão como aceitável); inalterado | — |

## 3. Recálculos (revisores, implementação independente) — todos confirmados

| Métrica | Valor verificado |
|---|---|
| Eventos 600/352; dist 0/177/116/47/10/2; 175≥2; 59≥3; máx 5; 423/600 (70,5%) | ✓ |
| Gaps 248, mediana 58d, média 102,06, 148 (59,7%) ≤90d | ✓ |
| Reativação 61/55; 26 1º evento; 35 com anterior (mediana 45d); 24 com próximo (53d/88d); 37 censurados; follow-up 12,0/28,6/35,0% | ✓ |
| **KM 90d 0,653 / 180d 0,476 / mediana 187d** | ✓ (3/3 revisores) |
| Ciclos: 2 dec; 281 inc (279 gaps + 2 retornos); 2 completos (A-180abf, A-0baac2); R2 18.507 (winner do mês anterior) | ✓ |
| Σ proxy 28.766.224; current 3.668.852; 500/500 ativas; overlap 7/Jaccard 0,21/Spearman 0,575; shifts −9/+4/+11/+13/+3 | ✓ |
| Backtest 90d: elegíveis 283/348/420; outcomes 61/86/124; baselines 0,2155/0,2471/0,2952; R_D 1,574/1,556/1,835; Wilson 27/27 | ✓ (45/45 e 49/49 linhas t14) |
| Sensibilidade 180d: R_D 1,263/1,509; **R_G 1,362 (N=12) e R_H 1,606 (N=16) no 06-30; R_B 1,051 (N=20)** | ✓ |
| Watchlist 20 únicas 8/8/4; Σ 392.030 (10,7%); top-3 MRR A-c70870 33.830 / A-56962b 32.437 / A-18793f 29.452 | ✓ |
| Segmentos S1–S5 (N/US$); overlaps 26/54/110/25/19; S3⊂S4; exposição R1 1.179.139 (multi 383.038/32,5%; react 124.461/10,6%) | ✓ |
| Leakage | zero (auditoria coluna a coluna; G6b 5/5) |

## 4. Review do adendo de orquestração (itens 10–12)

- **Verificado pelos 3 revisores:** IDs e papéis consistentes (orquestrador `openai/gpt-5.6-sol` = metadata runtime, NÃO verificável publicamente; `deepseek-max` = DeepSeek V4 Flash via OpenCode Go); URLs verificadas via web (3/3 principais pelos revisores 1–2; 7/7 HTTP 200 pelo revisor 3); distinção runtime metadata vs claims externas correta; honestidade de diversidade explícita (mesmo modelo, independência de contexto/amostragem); nenhum benchmark/preço/ranking não sustentado; nenhum arquivo histórico reescrito.
- **Único ponto levantado (F7/L2/INFO-3):** wording do F11 "dentro da política" — **corrigido** (seção 2). Nenhuma correção material no adendo.
- **Adendo após o gate: `CONCLUDED`** (execução validada e revisada; fonte atual de verdade de ferramenta/processo).

## 5. Refinamento visual — métricas before/after (programático)

Causa raiz comum corrigida: rodapés longos em `ax.text(0.0, -0.2x, transform=ax.transAxes)` + `savefig(bbox_inches="tight")` esticavam o canvas e esmagavam o eixo; agora rodapés em `fig.text` (coordenadas de figura, 2 linhas), margens explícitas (`subplots_adjust`), **sem `bbox_inches="tight"`**, 150dpi, paleta Okabe-Ito colorblind-safe (`#0072B2/#E69F00/#009E73/#D55E00/#CC79A7/#56B4E9/#F0E442/#000000`), fundo branco, títulos curtos.

| Gráfico | Before (revisores) | After (medido) |
|---|---|---|
| `a_monthly_events_and_rate.png` | 1050×394; anotação do pico colada no título (10px) | 1170×660; ylim com headroom (1,18×pico) → anotação dentro dos eixos; ticks mensais rotacionados 90° (0 overlaps); sem clip |
| `b_km_by_signup_quarter.png` | 1713×441; eixos ~17% da largura; legenda sobre título; right-half ink 0,6–14% | 1500×900; eixos = 90% da largura (1350px/1500); legenda 2 colunas em faixa própria abaixo dos eixos; 0 overlaps/clips; curvas íntegras 0–1 (ticks explícitos 0–24/0–1,0) |
| `c_onboarding_exposure_by_duration.png` | 1353×392; labels x sobrepostos (−3,5/−11,5/−6,5px) | 1170×630; **barras horizontais** em ordem de duração (0d→>365d) com % e US$ ao lado; 0 overlaps |
| `d_usage_volume_vs_intensity.png` | 1157×443 (aceitável) | 1560×615; 2 painéis (0,408+0,408 da largura); ticks 90°; rodapé compacto; 0 overlaps/clips |
| `It04_c_lifecycle_vs_current_mrr.png` | 1087×466 (aceitável) | 1290×780; legenda em faixa própria acima (não cobre pontos); labels com offset em pontos; ticks log explícitos (sem overhang 10^2/10^5); 0 overlaps/clips |
| `It04_d_backtest_lift.png` | 1491×433; right-half ink 5,4%; 27 barras+erros congestionados; legenda sobre o 1º grupo | 1260×840; **dot/errorbar horizontal** (regras no y, lift no x, 3 cutoffs por cor/offset ±0,22, CI Wilson, linhas em 1,0 e 1,15, legenda fora, faixa de destaque R_D); ink L/R 50,8/49,2%; 0 overlaps/clips |
| `e_support_churn_vs_control.png` | 1320×418; 3 métricas num eixo (tickets invisível); y-label×título | **removido** → tabelas t06/t09 (pruning) |
| `f_segment_first_event_rates.png` | 1184×685 (aceitável) | **removido** → tabela t07 (pruning) |
| `It04_a_recurrence_reactivation.png` | 1050×421 (aceitável) | **removido** → tabela t12 (pruning) |
| `It04_b_cycle_lenses.png` | 1678×399; eixos 30px de 1678 | **removido** → tabela t13 (pruning) |

Validação programática (script `/tmp/opencode/it04-fix-sandbox/visual_validate.py`, medição de bboxes no renderer em 150dpi): **PASS** em todos os 6 PNGs — eixo principal ≥ 69,5% da largura (painéis somam ≥ 81,6%); 0 overlaps legend×title/legend×axes/ticks; 0 textos clipped; dimensões 1170–1560 × 615–900 px; 258–835 cores; os 4 PNGs pruned ausentes (não reaparecem em execução limpa; os checks C01-charts dos scripts falham se reaparecerem). Inspeção ocular do orquestrador: pendente (métricas objetivas reportadas no fix-report).

## 6. Pruning (item 15 do prompt)

- **Removidos do git e do gerador (4):** `e_support_churn_vs_control.png`, `f_segment_first_event_rates.png`, `It04_a_recurrence_reactivation.png`, `It04_b_cycle_lenses.png`. Números preservados: `t06_support_monthly.csv`/`t09_causality.csv` (suporte), `t07_segments.csv` (segmentos), `t12_reactivation_recurrence.csv` (recorrência/reativação), `t13_state_cycles.csv` (lentes de ciclo; com `winner_mrr_prev` para o R2).
- **Manifestos nos scripts:** It03 → 4 PNGs + 13 tabelas; It04 → 2 PNGs + 9 tabelas; checks `C01-charts` falham se houver arquivo fora do manifesto (pruning não pode reaparecer).
- **Keep-set final (6 PNGs commitados):** `a_monthly_events_and_rate.png`, `b_km_by_signup_quarter.png`, `c_onboarding_exposure_by_duration.png`, `d_usage_volume_vs_intensity.png`, `It04_c_lifecycle_vs_current_mrr.png`, `It04_d_backtest_lift.png`.

## 7. Validações pós-correção (detalhe no review-fix report)

- Scripts 03 e 04 re-executados do zero em sandbox e repo: **23 PASS (03) / 34 PASS (04), 0 WARN / 0 FAIL**; 8 outputs (2 evidence + 6 PNGs) byte-a-byte idênticos entre 2 execuções, CWD diferente e repo↔sandbox (MD5).
- FAIL estrutural: It04 (coluna `status` renomeada) e It03 (idem) → exit 1, relatório regravado com "Falha estrutural", 0 tracebacks, outputs preservados; restauração → idênticos.
- Report↔CSV: 21/21 checks reais (lifts exatos t14, strings de segmentos derivadas, watchlist 20/8/8/4, Σ 392.030, t13 R2, t12 KM, MVs); 3 MVs It04 (MV1a A-68f37c 172d; MV1b A-956988 censurada; MV2 overlap 7/shifts; MV3 A-c70870 5/5); leakage G6b 5/5.
- Git: escopo 100% `submissions/jose-nascimento/`; `git diff --check` limpo; autor do candidato; sem amend/force/rebase; push validado (local == remote).

## 8. Riscos remanescentes (handoff It05)

1. **Extrapolação do spike sintético:** R_D tem lift máximo (1,83) na janela do pico — cautela declarada, manter na It05.
2. **Poder estatístico:** CIs largos; CI do lift não reportado (recomendação opcional dos revisores para It05/It07); N pequenos nos tiers B/C.
3. **Pré-especificação não auditável via git (LOW-4):** registrada honestamente; prática It03 (decisões antes do código) retomada nas It05+.
4. **Time budget:** acumulado ~12h35 vs 4–6h — acima do gatilho de contenção; registrado no F11 com plano de trims formais a partir da It05.
5. **Inspeção ocular do orquestrador** sobre os 6 PNGs (métricas objetivas já reportadas).

## 9. Gate It04

**CONCLUDED** — 3 veredictos `PASS_WITH_FIXES`; nenhum finding analítico material; correções de documentação/consistência (F1–F7, L1, LOW-1..4) e qualidade visual (F8 + pruning) aplicadas com revalidação completa (scripts, idempotência, CWD, FAIL estrutural, MVs, leakage, visual programático). Adendo de arquitetura: revisado e `CONCLUDED`. Iteração 05 permanece **PENDING** (não iniciada; sem recomendações/ROI — escopo respeitado).

## 10. Adendo — correção visual pós-inspeção ocular do orquestrador (2026-08-28)

- **Review programático passou**, mas a inspeção ocular do orquestrador detectou um **erro material de mapping no It04_d** não captado pelos validadores de bbox/ink: a linha rotulada `R_D onboarding<=90d` exibia os lifts de R_F (~0,66/0,40/0,92) e a linha `R_F A e C` (sombreada) exibia os lifts de R_D (1,57/1,56/1,83) — causa raiz: `y = len(rules)-1-j` (ordem invertida vs yticklabels).
- **Correção** (`fix: align chart labels and final visual spacing`, commit `617e4ac` — correção visual pós-gate sobre a **base** `1517a73`, o fixer do gate It04; hash no [`relatório da correção visual`](../reports/orchestrator-visual-correction-report.md) §0): associação explícita `rule → y` keyed em `chart_d`, faixa de destaque keyed em R_D, gate programático (27 pares rule×cutoff == t14; R_D exato 1,574/1,556/1,835; y destacado resolve para label R_D) + rodapés curtos/2 linhas e margens bottom em `a/b/c/d` (It04_c intocado).
  - *Precisão de hash (adendo no fechamento da It08, correção do gate 3x da It08):* a menção anterior associava `1517a73…` à mensagem da correção; `1517a73` é a **base** (fixer do gate It04) e o commit da correção visual é **`617e4ac`** — o errors ledger (E5) e o relatório da correção visual já citavam `617e4ac` corretamente; o ledger It08 confere a cadeia (`adbbad7`/`fb9d2de` → fix `1517a73` → visual `617e4ac`).
- **Hash:** ver `process-log/reports/orchestrator-visual-correction-report.md` (md5 pré/pós por PNG; 26/26 CSV/MD byte-idênticos; idempotência 2x; 27/27 keyed; margens −22→+32,3 / 7,7→+30,1 / 4,4→+22,9 px; clip à direita eliminado em b/c).
- **Não alterado:** gates/estado analítico (It04 `CONCLUDED`, It05 `PENDING`), análises, tabelas, watchlist, decisões e recomendações. Reinspeção ocular dos 6 PNGs solicitada ao orquestrador.
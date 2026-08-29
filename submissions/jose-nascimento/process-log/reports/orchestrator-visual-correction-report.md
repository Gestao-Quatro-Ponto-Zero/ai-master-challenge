# Relatório — Correção Visual Sequencial (inspeção ocular do orquestrador pós-gate It04)

- **Data:** 2026-08-28 · **Agente:** corretor visual sequencial `deepseek-max` (DeepSeek V4 Flash, max reasoning, via OpenCode Go)
- **Prompt arquivado:** `process-log/prompts/orchestrator-visual-correction-prompt.md`
- **Base:** commit `1517a7338d8565eb3bf41cb8723c2498e102905a` (branch `submission/jose-nascimento`)
- **Resultado:** **PASS** — mapping It04_d corrigido (R_D = 1,574/1,556/1,835), spacing dos 4 gráficos corrigido, validação sem visão 100% verde, outputs numéricos byte-idênticos, idempotência 2x confirmada.

---

## 1. Achado ocular (orquestrador)

| PNG | Achado ocular | Veredito pós-fix (medição) |
|---|---|---|
| `It04_d_backtest_lift.png` | Linha rotulada `R_D onboarding<=90d` exibe ~0,66/0,40/0,92; os pontos 1,57/1,56/1,83 aparecem na linha `R_F A e C`, que está sombreada — contradiz t14 (R_D = 1,574/1,556/1,835 é a regra validada) | **CORRIGIDO** — R_D agora exibe exatamente 1,574/1,556/1,835; faixa de destaque (y 2,5–3,5) envolve o y rotulado `R_D onboarding<=90d`; 27/27 pontos keyed == t14 |
| `a_monthly_events_and_rate.png` | xlabel `mês` + as duas linhas de rodapé na mesma faixa inferior (colisão) | **CORRIGIDO** — margem xlabel/ticks→rodapé: −22 px → **+32,3 px**; linhas de rodapé sem overlap entre si |
| `b_km_by_signup_quarter.png` | Rodapé longo clippa no limite direito | **CORRIGIDO** — rodapé dividido em 2 linhas curtas (fonte / censura); texto completo dentro do canvas (antes x1 = 1505 > 1500 px) |
| `c_onboarding_exposure_by_duration.png` | Rodapé truncado à direita (nome da tabela CAC-equivalent cortado) | **CORRIGIDO** — antes x1 = 1278 > 1170 px (−108 px cortados); agora 2 linhas curtas dentro do canvas; margem 7,7 px → **+30,1 px** |
| `d_usage_volume_vs_intensity.png` | Ticks verticais e rodapé próximos demais | **CORRIGIDO** — margem 4,4 px → **+22,9 px** |
| `It04_c_lifecycle_vs_current_mrr.png` | Aceitável (não mexer) | **INTOCADO** — md5 inalterado (`8de9904b…`); margem 11,6 px mantida |

## 2. Causa raiz

### 2.1 It04_d — mismatch de ordem (reverse/index)

Em `solution/src/04_lifecycle_watchlist.py::chart_d` (commit 1517a73), o y de cada ponto era calculado como `y = len(rules) - 1 - j` (regra A no TOPO, regra I embaixo), enquanto os yticklabels eram gravados na ordem natural de `RULES` (`R_A` em y=0 … `R_I` em y=8). As duas ordens são independentes e **invertidas** — exatamente o padrão "reverse/index" citado pelo orquestrador:

- Regra D (j=3) era plotada em y=5, que exibe o label `R_F A e C` (e a faixa de destaque `axhspan(4.5, 5.5)` cobria esse y — a linha sombreada vista pelo orquestrador);
- Regra F (j=5) era plotada em y=3, que exibe o label `R_D onboarding<=90d`;
- Reversão completa em cadeia: A↔I, B↔H, C↔G, D↔F (E é simétrico e passava despercebido).

A extração keyed dos artists (renderer) provou o bug no estado pré-fix: **26 dos 27 pares (rule, cutoff) divergiam** de t14 (ex.: `R_D 2024-03-31: x plotado 0.663 != t14.lift 1.574`; `R_F 2024-09-30: x plotado 1.835 != t14.lift 0.924`); somente a regra E (posição simétrica) coincidia. Os validadores programáticos anteriores mediam apenas bboxes/ink e não extraíam os dados dos artists — por isso o erro material passou.

### 2.2 Spacing — rodapé e margens

`_footer` (03_root_cause.py) posicionava as duas linhas em `fig.text(0.01, 0.02/0.005)` com `va="bottom"`: com 6,5pt e figuras baixas (4,1–4,4 in), a altura de linha em fração da figura (~0,020) era **maior que o espaçamento entre as linhas (0,015)** → as duas linhas se sobrepunham; e textos longos (130–190 chars) extrapolavam a largura do canvas (clip à direita em b e c, com o nome `t03c_cac_equivalent.csv` cortado). Margens `bottom` pequenas (0,15–0,17) deixavam xlabel/ticks rotacionados a <8 px (ou sobrepostos, −22 px em `a`) do rodapé.

## 3. Patch aplicado (escopo mínimo: mapping/layout apenas)

### `solution/src/04_lifecycle_watchlist.py`
- **`chart_d`** (linhas ~865–960):
  - Associação **explícita e keyed** `y_by_rule = {r: i for i, r in enumerate(rules)}` (R_A em y=0 … R_I em y=8, na MESMA ordem dos yticklabels); `y = y_by_rule[r] + offsets[i]`. Removido `len(rules) - 1 - j`.
  - Faixa de destaque agora keyed: `ax.axhspan(y_by_rule["D"] - 0.5, y_by_rule["D"] + 0.5)` → cobre o y rotulado `R_D onboarding<=90d`.
  - **Gate programático** após a gravação dos yticklabels (falha com `RuntimeError` se divergir):
    1. cada par (rule, cutoff) plotado == `t14.lift` lido do CSV em disco (keyed) — 27 pares;
    2. R_D exato nos 3 cutoffs: `[round(v,3) for v in rd] == [1.574, 1.556, 1.835]`;
    3. `len(plotted) == 9 × 3` (nenhuma regra pulada);
    4. `tick_txt[y_d].startswith("R_D ")` — o y destacado resolve para o label R_D.
  - Teste negativo executado: corromper R_D@09-30 para 1.900 dispara `RuntimeError: [chart_d] gate de mapping falhou: R_D 2024-09-30: x plotado 1.9 != t14.lift 1.835`.

### `solution/src/03_root_cause.py`
- **`_footer`**: espaçamento entre linhas derivado da altura da figura (`lh = 6.5/72/figheight`; `y1 = 0.008 + 1.45·lh`, `y2 = 0.008`) — as duas linhas nunca se sobrepõem nem saem do canvas; permanece `fig.text` dentro da figura, sem `bbox_inches="tight"`.
- **`chart_a`**: `bottom 0.16 → 0.26`; rodapé em 2 linhas curtas (fonte / denominador).
- **`chart_b`**: rodapé em 2 linhas curtas (fonte / nota de censura) — sem clip à direita.
- **`chart_c`**: `bottom 0.15 → 0.20`; rodapé em 2 linhas curtas (fonte / R1 + CAC-equivalent).
- **`chart_d` (03)**: `bottom 0.17 → 0.22`; rodapé em 2 linhas curtas (fonte / definições).

Nenhuma alteração em análises, tabelas, watchlist, decisões, recomendações, estados ou gates analíticos (G1–G13, checks C01). `It04_c` não foi tocado.

## 4. Validação sem visão (script `/tmp/opencode/visual-fix-sandbox/validate_charts.py`, renderer Agg 150 dpi, captura via monkeypatch de `Figure.savefig`)

### 4.1 It04_d — extração keyed dos artists (27/27)

Para cada `ErrorbarContainer` de `It04_d_backtest_lift.png` (figura capturada no savefig), extraídos `x` (lift) e `y` (posição + offset de cutoff) dos marcadores; regra resolvida pelo yticklabel do y inteiro (mesma convenção do código fixado); comparação keyed contra `t14_backtest_temporal.csv` (horizon 90d):

- **27/27 pontos extraídos**; 27/27 pares `(rule, cutoff)` com `|x plotado − t14.lift| < 1e-9` e y resolvendo para o label correto (`R_{rule} …`).
- **R_D exato nos 3 cutoffs:** 1,574 (2024-03-31) / 1,556 (2024-06-30) / 1,835 (2024-09-30) — confere com t14 e com o report.
- **Faixa de destaque:** `axhspan(2.5, 3.5)` envolve y=3, cujo yticklabel é `R_D onboarding<=90d`. (Pré-fix: faixa (4.5, 5.5) não envolvia y=3 e destacava o label `R_F A e C`.)
- Pré-fix, a mesma extração acusava 26/27 divergências (R_D mostrando 0,663/0,405/0,924 — os lifts de R_F, exatamente o achado ocular).

### 4.2 Layout (renderer bbox, todos os 6 PNGs)

Critérios: zero overlap título×legenda×eixos×ticks×textos; rodapé dentro do canvas com texto completo; margem vertical mínima ≥ 8 px entre o bbox mais baixo de xlabel/ticks e o topo do rodapé; linhas de rodapé sem overlap entre si.

| Gráfico | Margem xlabel/ticks→rodapé (antes → depois) | Clip à direita (antes → depois) | Overlaps |
|---|---|---|---|
| `a_monthly_events_and_rate.png` | **−22,0 px → +32,3 px** | não havia → não há | 0 |
| `b_km_by_signup_quarter.png` | 180,8 px → 172,0 px | x1 1505 > 1500 (−5 px) → dentro (2 linhas curtas) | 0 |
| `c_onboarding_exposure_by_duration.png` | **7,7 px → +30,1 px** | x1 1278 > 1170 (−108 px, CAC-equivalent cortado) → dentro | 0 |
| `d_usage_volume_vs_intensity.png` | **4,4 px → +22,9 px** | não havia → não há | 0 |
| `It04_c_lifecycle_vs_current_mrr.png` | 11,6 px → 11,6 px (intocado) | não havia → não há | 0 |
| `It04_d_backtest_lift.png` | 42,2 px → 42,2 px | não havia → não há | 0 |

Gap entre as duas linhas de rodapé: 5,4 / 5,4 / 2,4 / 5,4 px (a–d) — sem sobreposição.

### 4.3 Manifesto / pruning / idempotência / imutabilidade numérica

- Exatamente **6 PNGs** em `solution/out/charts/`, todos abrem (`PIL.Image`); **nenhum pruned reapareceu** (`e_support_churn_vs_control.png`, `f_segment_first_event_rates.png`, `It04_a_recurrence_reactivation.png`, `It04_b_cycle_lenses.png` ausentes; checks `C01-charts` dos scripts PASS).
- Scripts 03/04 re-executados 3x (sandbox) e 2x (repo): PNGs **byte-idênticos entre execuções** (md5) e iguais sandbox↔repo.
- **26/26 CSV/MD numéricos byte-idênticos ao pré-fix** (t01..t17, t14b, evidence 01–04): nenhum número, tabela, watchlist, decisão ou recomendação mudou. Únicas mudanças: 5 PNGs (It04_d, a, b, c, d) + 2 scripts + docs de processo. `It04_c_lifecycle_vs_current_mrr.png` byte-idêntico ao pré-fix (não tocado).
- Scripts: `23 PASS / 0 WARN / 0 FAIL` (03) e `34 PASS / 0 WARN / 0 FAIL` (04) — gates analíticos G1–G13 intactos.

## 5. Arquivos alterados

| Arquivo | Mudança |
|---|---|
| `solution/src/04_lifecycle_watchlist.py` | `chart_d`: mapping keyed `rule→y`, faixa em R_D, gate programático (27 pares vs t14, R_D exato, label do y destacado) |
| `solution/src/03_root_cause.py` | `_footer` com espaçamento derivado da altura; rodapés curtos em a/b/c/d; `bottom` 0,26/0,20/0,22 (a/c/d) |
| `solution/out/charts/It04_d_backtest_lift.png` | regenerado (mapping corrigido; md5 `54bdd8a9…` → `ecca1338…`) |
| `solution/out/charts/a_monthly_events_and_rate.png` | regenerado (md5 `fe22acbc…` → `742ef0b9…`) |
| `solution/out/charts/b_km_by_signup_quarter.png` | regenerado (md5 `8df6d5db…` → `99d8daa1…`) |
| `solution/out/charts/c_onboarding_exposure_by_duration.png` | regenerado (md5 `b22c0565…` → `d8e40a2e…`) |
| `solution/out/charts/d_usage_volume_vs_intensity.png` | regenerado (md5 `dac4f96a…` → `b95c537e…`) |
| `solution/out/charts/It04_c_lifecycle_vs_current_mrr.png` | **intocado** (md5 `8de9904b…` igual ao pré-fix) |
| `process-log/prompts/orchestrator-visual-correction-prompt.md` | prompt arquivado |
| `process-log/reports/orchestrator-visual-correction-report.md` | este relatório |
| `process-log/reviews/iteration-04-review-summary.md` | adendo curto (seção 10) |

## 6. Riscos / notas

- A extração keyed depende da convenção de label `R_{regra} …` nos yticklabels; o gate embutido no `chart_d` protege contra qualquer edição futura que descole mapping/labels/t14 (falha a execução, exit não-zero via `RuntimeError`).
- Reversões completas em dot-plots horizontais são invisíveis para validadores de bbox/ink; a inspeção ocular do orquestrador foi decisiva para este achado — a lição está registrada no adendo do review summary.

## 7. Solicitação de reinspeção ocular

**PASS** — commit `fix: align chart labels and final visual spacing` (hash no report final da sessão; push validado, local == remote, working tree limpo). Solicita-se ao orquestrador a **reinspeção ocular dos 6 PNGs** com foco em: (1) linha `R_D onboarding<=90d` destacada exibindo 1,574/1,556/1,835; (2) rodapés curtos em 2 linhas dentro do canvas nos 4 gráficos It03; (3) ausência de colisão entre xlabel/ticks e rodapé.
# Report da Iteração 04 — Ciclos de reativação, jornada da conta e watchlist operacional

- **Executor:** agente único `deepseek-max` (via OpenCode Go), conforme plano de execução (regra 1).
- **HEAD base:** `12ff47c9bcc29f1dbd81aba186985c1191a8f10b` (esperado no prompt) — confirmado no início (working tree limpo, branch `submission/jose-nascimento`).
- **Prompt integral:** `process-log/prompts/iteration-04-prompt.md` (arquivado antes da implementação).
- **Decisões com regras pré-especificadas ANTES dos resultados:** `process-log/decisions/iteration-04-watchlist-decisions.md` (D1–D9; backtest e watchlist fixados a priori, sem tunagem).
- **Tempo de relógio:** ~2h10min (leitura de contexto + exploração de dados + script + 6 correções + validações + documentos).

---

## 1. Workflow

1. **Inspeção git:** branch/status/log conferidos; HEAD = `12ff47c`; árvore limpa. It04 `OPEN` (lógico) durante a execução.
2. **Leitura de contexto:** instruções oficiais já lidas em iterações anteriores (checklist A1–A5); relidos contrato analítico It02, reports/evidence It01–It03, review summaries It00–It03, execution-plan e checklist. Nenhuma pesquisa externa usada como fonte (regra 7/8 do plano).
3. **Exploração de dados (sem alterar repo):** distribuição de eventos (600/352; 175 ≥2; 59 ≥3; máx 5); 61 flags/55 contas de reativação; transições do painel (2 dec; 281 inc; 279 gaps de ativação + 2 retornos); all-active no corte; P75 do winner 9.751; Σ winner 28.766.224 / 3.668.852.
4. **Decisões pré-especificadas:** D1–D9 escritas e commitadas ANTES do backtest final (regras R_A–R_I, cutoffs, critério de validação lift > 1,15 × 3 cutoffs, caps 8/8/4 da watchlist).
5. **Implementação:** `solution/src/04_lifecycle_watchlist.py` (1.530 linhas; stdlib + pandas + matplotlib; offline; determinístico).
6. **6 correções durante o desenvolvimento (erros reais, causa raiz abaixo).**
7. **Validações completas:** seção 5.
8. **Commit final:** `feat: prioritize accounts by lifecycle and validated risk signals` + push + verificação local==remote.

## 2. O que foi entregue

- `solution/evidence/04_lifecycle_watchlist_report.md` (12 seções; 29 PASS / 0 WARN / 0 FAIL).
- `solution/out/tables/`: `t11_account_lifecycle.csv` (500 contas), `t12_reactivation_recurrence.csv`, `t13_state_cycles.csv`, `t14_backtest_temporal.csv` (regras×cutoffs 90d/180d), `t14b_backtest_detail.csv` (auditoria por conta×cutoff), `t15_priority_segments.csv`, `t15b_segment_overlap.csv`, `t16_watchlist_top20.csv`, `t17_rank_comparison.csv`.
- `solution/out/charts/`: `It04_a_recurrence_reactivation.png`, `It04_b_cycle_lenses.png`, `It04_c_lifecycle_vs_current_mrr.png`, `It04_d_backtest_lift.png` (não repetem It03).

## 3. Hipótese/regra → backtest → decisão (arco honesto)

| Regra (pré-especificada) | Intuição (de It03/escopo) | Backtest 90d (lift por cutoff) | Decisão |
|---|---|---|---|
| R_A recorrência ≥2 | "quem churnou volta a churnar" | 0,44 / 0,41 / 0,89 | NÃO valida → associação histórica (concentração 70,5% dos eventos), nunca preditor |
| R_B reativação ≥1 | "reativação precede novo evento" | 0,52 / 0,41 / 1,29 | NÃO valida (lift só no período do spike, inconsistente) → descrita com KM e censura |
| R_C evento ≤90d | janela acionável | 0,74 / 0,63 / 1,01 | NÃO valida → recência operacional, não risco |
| **R_D onboarding ≤90d** | causa raiz It03 (H1/H8/H9) | **1,57 / 1,56 / 1,83** | **ÚNICA VALIDADA** (3/3 cutoffs, N ≥ 25; 180d: 1,26/1,51) |
| R_E winner ≥P75 | exposição prediz saída | 0,56 / 0,85 / 0,71 | NÃO valida → exposição é dimensão de priorização, não risco |
| R_F/G/H/I combinações | — | ≤ 1,27, inconsistentes | NÃO validam (N pequenos reportados) |

**Consequência (D8):** sem lift consistente para recorrência/reativação/MRR, **NÃO existe score de churn validado**; a watchlist é nomeada **operational priority/exposure** e ordenada por exposição + evidência, com tiers declarados (8 onboarding validado / 8 evento recente / 4 proteção de receita).

## 4. Erros reais encontrados e corrigidos (nunca "não houve erros")

1. **Kaplan-Meier com desempacotamento de dict** — `for t, s in km` desempacota as CHAVES do dict (strings `"t"`/`"survival"`), quebrando a comparação `t >= 90` (TypeError str vs int). **Causa raiz:** km armazenado como lista de dicts (não tuplas) e genexpr com desempacotamento errado. **Correção:** iterar `item["t"]`/`item["survival"]`; números corrigidos (sobrevivência 90d 0,653; mediana 187d) e verificados por implementação KM própria.
2. **Censura KM incompleta na exploração inicial** — episódios censurados entre tempos de evento não eram removidos do at-risk; a versão corrigida do script subtrai `d + c` por tempo. (Erro só da exploração; o script final nasceu correto — detectado pela verificação independente.)
3. **KeyError `_ever_active_before` em `state_cycles`** — seleção de `inc_rows` antes de adicionar a coluna ao painel (pandas copia em indexação booleana). **Correção:** reordenar (coluna antes da seleção).
4. **`yerr` negativo no gráfico D** — barras de erro calculadas na escala de precision (0–1) aplicadas ao lift (escala ~0,3–1,8). **Correção:** escalar CI pela baseline (`ci/base`).
5. **Overlap S3 inconsistente (34 vs 25)** — a matriz de overlap usava `is_reactivated` (55 contas) enquanto a tabela de segmentos define S3 como reativação em out-dez/2024 (25). **Correção:** overlap usa a MESMA definição (`s3_recent_react`); resultado S3∩S4=25, S2∩S3=19.
6. **Contagem de tabelas misturava It03** (G10 dizia 22) — glob `t*.csv` pegava t01–t10. **Correção:** lista explícita das 9 tabelas It04.
7. Menores: IDs G6b duplicados nas sensibilidades (adicionado horizonte); bold sem fechamento na seção 3; lift R_B 1,30→1,29 no texto; G11 tautológico → âncora de regressão declarada; sintaxe do bloco t13 (parêntese).

## 5. Validações executadas

| Validação | Resultado |
|---|---|
| Baseline 2× + idempotência (3 execuções) | exit 0; 29 PASS / 0 WARN / 0 FAIL; 14 outputs byte-a-byte idênticos (MD5) |
| CWD diferente (sandbox fora do repo, path absoluto do script) | exit 0; outputs idênticos (MD5) |
| FAIL estrutural (coluna `status` renomeada no painel) | exit 1; relatório regravado com "Falha estrutural"; **0 tracebacks**; painel restaurado e re-executado com 29 PASS |
| PNGs (PIL) | 4/4 abrem; 1050–1678 × 399–466 px; 260–767 cores; não-branco 3,3–15,0% |
| Report ↔ CSV | watchlist 20/20 contas; segmentos N/US$; lifts 90d (2 casas); t11/t12/t13/t14/t16 conferem linha a linha |
| No-leakage audit coluna a coluna | seção 9 do report; checks G6b por cutoff (max(churn_date) ≤ cutoff; max(end_date) ≤ cutoff) — 5/5 PASS |
| 3 verificações manuais independentes (implementação própria) | MV1a A-68f37c (reativada 2024-06-29 → próximo evento 2024-12-18, gap 172d; 2ª reativação 2024-12-18 sem próximo — censura); MV1b A-956988 (reativada 2024-12-30, follow-up 1d — censurada, NÃO sucesso); MV2 rank shifts (A-68f37c 5→1; A-a8d89d só na jornada; overlap 7); MV3 A-c70870 (tenure 70d, MRR 33.830, 1 evento, proxy 34.419 — 5/5 campos) |
| Recálculo independente do backtest (90d) | 3/3 cutoffs: elegíveis 283/348/420, outcomes 61/86/124, R_D prec 0,339/0,385/0,542, lift 1,574/1,556/1,835 — idênticos a t14 |
| Recálculo independente de recorrência/reativação | 175/59/máx 5; 61 flags/55 contas; 24 episódios com próximo evento |
| `git diff --check` / escopo / paths / segredos | limpo; só `submissions/jose-nascimento/`; sem paths pessoais nos artefatos da solução (grep; exceção documentada: prompts arquivados) |

## 6. Números-chave (origem: `evidence/04_lifecycle_watchlist_report.md` + tabelas)

- **Recorrência:** 175 contas ≥2 eventos (59 ≥3, máx 5); 423/600 eventos (70,5%) concentrados nessas 175 contas; gaps medianos 58d (59,7% ≤90d).
- **Reativação:** 61 flags / 55 contas; 26 flags são o 1º evento da conta; 24 episódios com próximo evento observado (mediana 53d), 37 censurados; KM sobrevivência 90d = 0,653 (≈35% com próximo evento ≤90d), mediana 187d; follow-up explícito (10/35 ≤90d = 28,6%).
- **Ciclos reais:** 2 transições active→inactive; 281 inactive→active (279 = gap de ativação signup; 2 = retornos reais); **2 ciclos completos** (A-180abf, A-0baac2) — vs 175 multi-evento e 55 reativações: lentes distintas, não intercambiáveis.
- **Jornada/valor:** Σ lifecycle proxy = 28.766.224; current winner MRR = 3.668.852; overlap top-20 current vs lifecycle = 7 (Jaccard 0,21); Spearman 0,575; rank shifts A-977ca0 +13, A-80eeb6 +11, A-1f0636 −9; viés contra contas novas declarado.
- **Backtest (90d):** baselines 0,216/0,247/0,295; só R_D valida (1,57/1,56/1,83); sensibilidade 180d confirma (1,26/1,51).
- **Watchlist:** 20 contas específicas (8/8/4); top-3: A-c70870 (33.830), A-18793f (29.452), A-56962b (32.437, Tier C); Σ winner do top-20 = 392.030 (10,7% da exposição total).
- **Segmentos:** S1 onboarding 80 contas / 621.981; S2 repeat-event 175 / 1.245.634; S3 reativação recente 25 / 179.256; S4 evento recente 178 / 1.299.245; S5 alto valor 130 / 1.780.851 (overlap declarado).

## 7. Limitações e handoff para a Iteração 05

- **Não confundir:** recorrência/reativação/ciclo de estado são associações e lentes distintas; nenhum número delas é "risco validado".
- **All-active no corte** impede validação direta de perda de estado no presente; o backtest usa eventos históricos como outcome.
- **Sinteticidade:** pico de fim de 2024 pode ser artefato de geração (It01 §5) — os lifts mais altos de R_D ocorrem exatamente no período do pico; cautela na extrapolação.
- **It05 (próxima):** recebe (a) o único sinal com validação temporal (onboarding ≤90d, lift 1,57–1,83) para ações de ativação; (b) os segmentos com N/US$; (c) a watchlist 8/8/4 como insumo de priorização — e DEVE continuar sem score arbitrário; recomendações em faixa paramétrica com premissas nomeadas (ex.: exposição R1 ≤90d 871.812 em out-dez/2024 como teto, nunca perda); (d) nada de CAC/winback factual (não existe na base).
- **Risco de review:** N grande suficiente nos tiers B/C? (C = 36 candidatos, top-4 selecionados); gate 3x da It04 dispara em seguida — findings materiais serão corrigidos por agente sequencial.

## 8. Estados (atualizados no plano/checklist)

- It04 `CONCLUDED` (implementação validada pelo executor; 29 PASS; 3 MVs; recálculo independente; git ok). Review gate 3x da It04 `PENDING` (ledger B3). It05–It10 `PENDING`.
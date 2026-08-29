# Prompt integral — Agente Corretor Sequencial do review gate da Iteração 04 + adendo (arquivado)

**Data:** 2026-08-28 · **Agente:** corretor sequencial `deepseek-max` (DeepSeek V4 Flash, max reasoning, via OpenCode Go) · **Commit esperado:** `fix: refine lifecycle evidence and essential charts`

> Transcrição fiel do prompt recebido (padrão de arquivamento dos gates anteriores).

---

Você é o AGENTE CORRETOR SEQUENCIAL da ITERAÇÃO 04 e do adendo de orquestração. Corrija findings factuais, faça o refinamento visual orientado pelo orquestrador, faça pruning de gráficos e feche o gate 3x. NÃO inicie recomendações It05.

REPO
- `/tmp/opencode/ai-master-challenge-work`, branch `submission/jose-nascimento`, pasta única `submissions/jose-nascimento/`, HEAD esperado `2a4b5b437c80a7b13f0ca9ad14d9bbae6d2036dd`.

LEIA PRIMEIRO
- `/tmp/opencode/ai-master-review-reports/iteration-04/review-9c41f7a2.md`
- `/tmp/opencode/ai-master-review-reports/iteration-04/review-df141f4f.md`
- `/tmp/opencode/ai-master-review-reports/iteration-04/review-3a4f8efa.md`
- Todos os artefatos It04, scripts/outputs It03, adendo de arquitetura, plano/checklist e instruções oficiais.

CORREÇÕES ANALÍTICAS/FACTUAIS
1. Atualize D7: números finais de reactivation KM são 90d=0,653, 180d=0,476, mediana 187d (derive em runtime; não hardcode narrativa sem gate). Preserve exploração como histórico, mas marque-a superada.
2. Corrija sensibilidade 180d: não diga "demais <=1,05" sem qualificador. R_G=~1,36 (N=12), R_H=~1,61 (N=16); explique instabilidade/N pequeno e, se usar regra de N>=25, aplique derivada da tabela.
3. R_B/S3: use precisão/rounding consistentes (valores exatos derivados), sem números conflitantes.
4. Remova "maioria das reativações é recente": 26/61=42,6%; distinga maioria das censuradas se isso for verdade e relevante.
5. Ordene top-3 por critério declarado ou chame apenas exemplos; não liste fora de ordem.
6. Reduza números narrativos hardcoded: gere textos a partir das tabelas/variáveis e adicione gates para claims executivos materiais.
7. Registre honestamente que D1–D9 foram commitadas junto do código (pré-especificação em arquivo, mas cronologia git não prova separação). Ajuste F11: 10h05 excede gatilho de contenção do plano; diga que o candidato optou por revisão adicional e registrou o custo, não "dentro da política".
8. Verifique glob de charts no script It03 para não falhar com outputs It04; faça scope por prefixos/manifesto.

REFINAMENTO VISUAL — ORQUESTRADOR É OS OLHOS; VOCÊ EXECUTA
O orquestrador abriu os 10 PNGs e determinou: grandes áreas brancas em b/e/It04_b/It04_d; legenda/título sobrepostos em b; escalas incompatíveis e label/título colidindo em e; ticks sobrepostos em c; anotação do pico perto do título em a; It04_d congestionado. Implemente mudanças mínimas no código gerador, sem dashboard/design system.
9. **Keep-set final, somente 6 PNGs commitados**:
   - `a_monthly_events_and_rate.png`
   - `b_km_by_signup_quarter.png`
   - `c_onboarding_exposure_by_duration.png`
   - `d_usage_volume_vs_intensity.png`
   - `It04_c_lifecycle_vs_current_mrr.png`
   - `It04_d_backtest_lift.png`
   Remova do git e pare de gerar: `e_support_churn_vs_control.png`, `f_segment_first_event_rates.png`, `It04_a_recurrence_reactivation.png`, `It04_b_cycle_lenses.png`. Preserve suas tabelas/números; atualize reports/manifests/gates/links para usar tabelas em vez desses gráficos. Em execução limpa, eles não podem reaparecer.
10. Padrão visual simples: fundo branco; grid horizontal leve quando útil; spines topo/direita removidas; fonte legível; paleta consistente colorblind-safe; títulos curtos; unidades explícitas; rodapés em `fig.text` dentro do canvas, quebrados em 2 linhas; layout compacto com `constrained_layout` ou margens explícitas; sem `bbox_inches=tight` expandindo canvas por texto fora da figura; 150dpi.
11. Ajustes específicos:
    - `a`: headroom e anotação do pico dentro da área sem colidir com título; ticks legíveis.
    - `b`: figure ~10x6, plot ocupa canvas; legenda compacta 2 colunas abaixo/acima sem sobrepor título/dados; curvas completas 0–1.
    - `c`: prefira barras horizontais em ordem de duração (0d,1–30,31–60,61–90,91–180,181–365,>365) com %/US$ legíveis; nada sobreposto.
    - `d`: manter 2 painéis, compactar rodapé/ticks, escalas claras.
    - `It04_c`: manter scatter, garantir legenda não cobre pontos e labels não colidem.
    - `It04_d`: substituir barras agrupadas congestionadas por dot/errorbar plot horizontal: regras no eixo y, lift no x, 3 cutoffs por cor/offset, Wilson CI, linhas verticais em 1,0 e threshold 1,15; legenda fora dos dados; destacar R_D sem poluição.
12. Validação visual programática: canvas/axes ratio (eixo principal ocupa >60% da largura útil; exceção painéis), bounding boxes de legend/title/ticks sem overlap, nenhum texto clipped, 6 PNGs abrem, dimensões razoáveis, cores/labels. O orquestrador fará inspeção ocular posterior; você deve reportar métricas objetivas.

EVIDÊNCIA/GATE
13. Reexecute scripts 03 e 04 do zero em sandbox e repo; 2x/idempotência/CWD; outputs report↔CSV; todos números It03/It04 estáveis; FAIL estrutural; 3 MVs It04; no leakage.
14. Crie `process-log/reviews/iteration-04-review-summary.md` com os três reports, matriz finding→ação→arquivo:linha, recálculos, review do adendo, visual before/after métricas, pruning e gate.
15. Arquive este prompt em `process-log/prompts/iteration-04-review-fix-prompt.md`; crie `process-log/reports/iteration-04-review-fix-report.md`; atualize evidence/decisions/process report, plano/checklist: gate It04 + adendo `CONCLUDED`, It05 PENDING.

GIT
- status/diff/log antes; preserve; só pasta permitida; `git add -f` paths pretendidos.
- Commit `fix: refine lifecycle evidence and essential charts`.
- Sem amend/force/config/destrutivo. Push; local==remote/tree limpo; diff-check/Markdown/links/paths/segredos.

REPORT FINAL
PASS/BLOCKED; hash/push; matriz review; números corrigidos; lista exata 6 PNGs; métricas layout before/after; pruning; testes/idempotência; arquivos/riscos; handoff It05. BLOCKED se gráficos removidos reaparecerem, layout ainda colidir ou claim factual persistir.
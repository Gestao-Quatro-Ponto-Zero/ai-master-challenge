# Prompt integral — Agente Corretor Visual Sequencial (inspeção ocular do orquestrador pós-gate It04) — arquivado

**Data:** 2026-08-28 · **Agente:** corretor visual sequencial `deepseek-max` (DeepSeek V4 Flash, max reasoning, via OpenCode Go) · **Commit esperado:** `fix: align chart labels and final visual spacing` (HEAD base `1517a7338d8565eb3bf41cb8723c2498e102905a`)

> Transcrição fiel do prompt recebido (padrão de arquivamento dos gates anteriores).

---

Você é o AGENTE CORRETOR VISUAL SEQUENCIAL. O orquestrador (único componente com inspeção ocular das imagens) abriu os 6 PNGs após o commit `1517a7338d8565eb3bf41cb8723c2498e102905a` e encontrou um erro visual material não captado pelos validadores. Corrija estritamente o mapping/layout; NÃO altere análises, tabelas, watchlist, decisões, recomendações ou estados.

REPO
- `/tmp/opencode/ai-master-challenge-work`, branch `submission/jose-nascimento`, pasta única `submissions/jose-nascimento/`, HEAD esperado `1517a7338d8565eb3bf41cb8723c2498e102905a`.

ACHADO OCULAR MATERIAL (It04_d)
- No PNG `solution/out/charts/It04_d_backtest_lift.png`, a linha rotulada `R_D onboarding<=90d` exibe pontos aproximadamente 0,66/0,40/0,92, enquanto os pontos 1,57/1,56/1,83 aparecem na linha `R_F A e C` e essa linha está sombreada. Isto contradiz `t14` e o report: **R_D é a regra validada e deve ter 1,574/1,556/1,835**. Há mismatch entre ordem de labels/y e grupos plotados (provavelmente reverse/index).
- Corrija por associação explícita `rule -> y`/merge keyed, nunca por listas em ordens independentes. A faixa de destaque deve estar na linha `R_D onboarding<=90d`, não R_F.
- Adicione assert/gate programático para cada rule×cutoff: x plotado == `t14.lift` correspondente; verifique R_D explicitamente nos 3 cutoffs e que o y destacado resolve para label R_D. Falhe se mapping divergir.

ACHADOS OCULARES DE SPACING
- `a_monthly_events_and_rate.png`: xlabel `mês` e as duas linhas de rodapé ocupam a mesma faixa inferior/colidem visualmente.
- `b_km_by_signup_quarter.png`: rodapé longo chega/clippa no limite direito; separar fonte e nota de censura em linhas curtas.
- `c_onboarding_exposure_by_duration.png`: rodapé fica truncado à direita (nome da tabela CAC-equivalent cortado).
- `d_usage_volume_vs_intensity.png`: ticks verticais e rodapé ficam próximos demais.
- `It04_c` está aceitável; não mexa sem necessidade.
- Use rodapés curtos, wrap explícito 2 linhas, `fig.text` dentro da figura, margem bottom suficiente e distância mínima mensurável entre bbox de xlabel/ticks e footer. Não use `bbox_inches=tight` para resolver. Preserve layout simples.

TAREFAS
1. Inspecione status/log; leia scripts 03/04, t14, reports e visual fix report anterior.
2. Corrija mapping/destaque It04_d e spacing nos quatro gráficos indicados; regenere somente os 6 PNGs do manifesto via scripts (outputs numéricos devem ficar byte-idênticos).
3. Validação sem visão:
   - extraia dados de cada artist/errorbar do It04_d e compare keyed com t14 (27/27);
   - assert R_D lifts exatos e band y/label R_D;
   - renderer bbox: nenhum overlap title/legend/axes/ticks/xlabel/footer; footer dentro canvas e texto completo; margem ≥8 px;
   - 6 PNGs abrem; exatamente 6; sem pruned reaparecer;
   - execute scripts 2x/idempotência e compare todos CSV/MD numéricos com pre-fix: byte-idênticos, exceto referências/checksum de PNG se existirem.
4. Arquive este prompt em `process-log/prompts/orchestrator-visual-correction-prompt.md` e crie `process-log/reports/orchestrator-visual-correction-report.md` com achado ocular, causa raiz, patch, assertions, before/after, arquivos, validações e pedido explícito de reinspeção ocular.
5. Adicione um adendo curto em `process-log/reviews/iteration-04-review-summary.md`: review programático passou, inspeção humana/orquestrador detectou mapping, correção e hash. Não mude gate/status analítico.

GIT
- Só pasta permitida; status/diff/log antes; `git diff --check`; paths/segredos/links.
- Commit `fix: align chart labels and final visual spacing`.
- Sem amend/force/config/destrutivo; push; local==remote/tree limpo.

REPORT FINAL
PASS/BLOCKED; hash/push; causa do mismatch; prova keyed 27/27 e R_D; lista de arquivos; métricas spacing; confirmação outputs numéricos imutáveis/pruning; solicitação de reinspeção ocular. BLOCKED se R_D ainda não mapear 1,574/1,556/1,835.
# Report da Iteração 05 — Ações priorizadas, impacto em faixa e plano de medição

- **Executor:** agente único `deepseek-max` (via OpenCode Go), conforme plano de execução (regra 1).
- **HEAD base:** `617e4ac252043475492d2b2e4c92e2eea1a3f385` (esperado no prompt) — confirmado no início (working tree limpo, branch `submission/jose-nascimento`).
- **Prompt integral:** `process-log/prompts/iteration-05-prompt.md` (arquivado na fase A, antes da implementação).
- **Premissas fixadas ANTES do cálculo:** `process-log/decisions/iteration-05-action-impact-assumptions.md` (commit `dc5748f`), com timestamp, 4 ações, fórmula, cenários 10/20/30% e origem, esforço qualitativo, stop/go, claims proibidos. Nenhum adendo necessário (nenhuma premissa mudou durante a execução).
- **Tempo de relógio:** ~2h00min (leitura de contexto + verificação independente das âncoras + fase A + script + 9 correções + validações + documentos).

---

## 1. Timeline dos dois commits (fase A e fase B)

| Passo | Commit | Hash | Conteúdo |
|---|---|---|---|
| Fase A (premissas) | `docs: define action and impact assumptions` | `dc5748f30e90ff9be4a9631c65ca21caf7afbcf8` | decisões/premissas It05 + prompt arquivado; push antes de qualquer script |
| Fase B (cálculo/plano) | `feat: prioritize churn interventions and impact scenarios` | (hash registrado após o push — o commit contém este report; ver timeline no report final da iteração e no review gate It05) | script `05_actions_impact.py`, evidence, tabelas t18–t21, report de processo, plano/checklist |

A cronologia git prova a separação premissas→código (prática It03 retomada; nota de transparência da It04 registra que ali a separação não era provável — aqui é).

## 2. Assumptions → cálculo → decisão (arco honesto)

| Premissa (fase A) | Cálculo (fase B) | Decisão |
|---|---|---|
| Só onboarding ≤ 90d tem validação temporal → ação A+D fundida | base elegível atual = 80 contas / 621.981 US$ winner MRR (t11, cross-check t15 S1); incidência histórica 90d = precision pooled regra D = 83/193 = 0,4301 (lower 0,3393 / upper 0,5417) | **ACT-01 (Now)**: programa de ativação com rollout experimental; impacto planejado 2,7–13,0 eventos/90d e 21.104–101.078 US$ de exposição afetada (não "receita salva") |
| Watchlist é operational priority/exposure, não score | top-20 = 392.030 US$/mês (10,7% da exposição total); Tier A 8 contas/169.747 vs B+C 12 contas/222.283 | **ACT-02 (Now)**: triage semanal com tratamento diferenciado; os 12 exposure-only NÃO rotulados como risco |
| Limitações estruturais de dados (CSAT 41,2% nulos; reason 15,8% unknown; uso fora da janela 76,6%; 21,0% vínculo evento-sub; sem milestone de ativação) | baselines re-derivados em runtime: CSAT cobertura 58,8%; unknown 15,83%; uso em janela 22,3%; vínculo 21,0%; campo de ativação ausente | **ACT-03 (Next)**: instrumentação com metas de qualidade nomeadas; pré-requisito da medição do ACT-01 |
| Reativação/recorrência: baixa confiança, sem ROI | sem lift (regra B 0,52/0,41/1,29); associação descritiva (KM 90d 0,653) | **ACT-04 (Later)**: piloto OBSERVACIONAL com gate pré-registrado (âncora 34,7%) |

## 3. Fórmula e cenários (componentes expostos)

- `expected_events_90d = N × incidence`; `events_affected = N × incidence × redução_relativa`; `exposure_affected = Σ winner_mrr × incidence × redução_relativa`.
- Cenários: conservador (incidência lower × 10%), base (pooled × 20%), ambicioso (upper × 30%) + sensibilidades (incidência lower/base/upper a 20%; população fluxo 68,25; annualized nomeado explicitamente "annualized MRR-equivalent exposure", aritmética, NÃO forecast).
- **Lift ≠ efeito causal do programa**: a redução relativa é premissa de planejamento (origem declarada), testada pelo experimento; nenhuma linha de US$ para ACT-02/03/04 (sem estimativa defensável → impacto operacional mensurável).

## 4. Experiment e measurement plan

- ACT-01: rollout gradual 50/50 por semana de signup, 4 trimestres, outcome primeiro evento 90d; poder por aproximação normal de 2 proporções (sem dependência extra): N/braço ≈ 34/68/136 → MDE 80% power ≈ 68%/51%/37%; declaração explícita de que efeitos < ~37% são inconclusivos, não ausência de efeito.
- t20: 18 métricas (leading/lagging/guardrail) com denominador, coorte, janela, fonte, owner, cadência e stop/go por ação (7 ACT-01, 4 ACT-02, 4 ACT-03, 3 ACT-04).

## 5. Erros reais encontrados e corrigidos (nunca "não houve erros")

1. **G3 via dupla de agregação quebrada** — primeira versão tentava `sum(int)` (TypeError) ao re-somar os componentes já agregados. **Causa raiz:** gate escrito antes de fixar o formato dos outputs de `compute_incidence`. **Correção:** re-agregação independente via média ponderada por `n_rule` direto do t14; tolerância 1e-3 (precisions do t14 são arredondadas a 4 casas).
2. **Bissecção do MDE com direção invertida** — `if n_required > n_arm: hi = mid` em vez de `lo = mid`; convergia para 0% (N=34/68) ou 43% (N=136). **Causa raiz:** n(mid) é decrescente em mid; a condição estava invertida. **Correção:** direção corrigida; MDEs 68%/51%/37%; gate G7 exige monotonicidade decrescente com N.
3. **G10 falso positivo "80"** — a contagem N=80 aparecia como literal em strings legítimas ("0.80", "80%"). **Correção:** lista de verificação restrita a valores distintivos (somas de MRR, pooled a 4 casas, exposição total).
4. **G11 falso positivo de "campo de ativação presente=True"** — substring `"activation" in "is_reactivation"` casava a coluna de reativação. **Correção:** verificação por token (`split("_")`).
5. **G11b claims proibidos fora da tabela de gates e com falso positivo** — check emitido DEPOIS de renderizar a tabela (aparecia só no console) e a seção 8 (lista de proibições) nomeia os termos propositalmente. **Correção:** check movido para antes da tabela de gates e varredura restrita às seções 1–7 (claims afirmativos).
6. **Truncamentos feiosos no relatório** — "NÃO rotular alto" (90 chars) e "7/14/" (80 chars) cortavam frases no meio. **Correção:** limites ampliados (110/110).
7. **Decimal pt-BR faltante** — share da ACT-02 saía "10.7%" em vez de "10,7%". **Correção:** `fmt_br_dec`.
8. **Linha em branco ausente antes de "## 10."** — cabeçalho colado no último bullet da seção 9. **Correção:** newline inicial no append.
9. **MV-1 da validação manual com borda errada (89 dias)** — primeira verificação independente usou `cutoff − 89d` (tenure > 90d); deu 78/608.439. **Causa raiz:** erro da verificação manual, não do script (a checagem de definição provou tenure_days == (cut−signup).days em 500/500 linhas). **Correção:** borda `cutoff − 90d`; MV-1 final 80/621.981 em dois caminhos independentes.

## 6. Validações executadas

| Validação | Resultado |
|---|---|
| Baseline 2× + idempotência (3 execuções + CWD diferente) | exit 0; 32 PASS / 0 WARN / 0 FAIL; 5 outputs byte-a-byte idênticos (MD5) |
| CWD diferente (sandbox fora do repo, path absoluto do script) | exit 0; outputs idênticos (MD5) |
| FAIL estrutural — coluna `tenure_days` renomeada no sandbox | exit 1; relatório regravado com "Falha estrutural"; **0 tracebacks** |
| FAIL estrutural — `t14` ausente no sandbox | exit 1; relatório regravado ("arquivo ausente"); 0 tracebacks |
| 3 verificações manuais independentes (implementação própria) | MV-1 base onboarding 80/621.981 (2 caminhos + definição tenure 500/500); MV-2 cenário base 6,9 eventos / 53.497 US$ (== t19); MV-3 tiers A 8/169.747, B+C 12/222.283, total 392.030 = 10,7% de 3.668.852 (== t21) |
| Report ↔ CSV | t18 4 ações; t19 cenários linha a linha (re-cálculo independente no gate G4); t20 18 métricas; t21 20 contas/8+12 |
| Sem PNG novo / charts intocados | gate G9: lista de charts antes == depois (6 PNGs do keep-set) |
| Nenhuma constante de dado hardcoded | gate G10: valores derivados em runtime ausentes como literais no script |
| Claims proibidos ausentes | gate G11b: "receita salva"/"revenue saved"/"cac queimado" zerados nas seções 1–7 |
| `py_compile` / Markdown / links | syntax OK; refs de arquivos do relatório resolvem (0 quebrados) |
| Paths/segredos | grep `/tmp`, `/home`, `ubuntu` nos artefatos da solução: zero (exceção documentada: prompts arquivados) |
| `git diff --check` / escopo | limpo; apenas `submissions/jose-nascimento/` |

## 7. Números-chave (origem: `solution/evidence/05_action_plan.md` + tabelas t18–t21)

- **Base elegível:** 80 contas onboarding (tenure ≤ 90d), Σ winner MRR 621.981 US$ (16,9% da exposição total 3.668.852).
- **Incidência histórica 90d:** 83/193 = 0,4301 (precision pooled regra D; lower 0,3393 / upper 0,5417).
- **Cenários (90d):** conservador 2,7 eventos / 21.104 US$; base 6,9 eventos / 53.497 US$; ambicioso 13,0 eventos / 101.078 US$; annualized (nomeado, aritmético) 27,5 eventos / 213.987 US$.
- **Watchlist:** 8 onboarding validados (169.747 US$) + 12 exposure-only (222.283 US$) = 392.030 US$ (10,7%); fluxo 2024: 56/65/72/80 (média 68,25).
- **Poder:** MDE 68%/51%/37% para N/braço 34/68/136; evento esperado no controle em 4 trimestres ≈ 58.

## 8. Limitações e handoff para a Iteração 06

- Impacto é **planejado, não medido**; efeito causal só via experimento ACT-01 (poder limitado declarado: efeitos < ~37% inconclusivos em 4 trimestres).
- All-active no corte, sinteticidade, N pequenos e censura seguem limitando (It04 §10).
- **It06 (automação):** `05_actions_impact.py` é o 5º estágio do pipeline (`01..05`), determinístico, offline, sem dependências novas; `run.sh` deve re-gerar `05_action_plan.md` + `t18..t21` idênticos byte-a-byte; revisar que o script falha estruturalmente sem traceback (2 cenários testados) e que os charts (keep-set 6) não são tocados.

## 9. Estados (atualizados no plano/checklist)

- It05 `CONCLUDED` (implementação validada pelo executor: 32 PASS / 0 WARN / 0 FAIL; 3 MVs; idempotência 3× + CWD; 2 cenários de FAIL estrutural; git ok). **Review gate 3x da It05 `CONCLUDED`** (dispara em seguida). It06–It10 `PENDING`.
- Checklist: D9/D10/D11 `CONCLUDED`; F11 atualizado (tempo ~2h00; acumulado ~14h35, acima do gatilho — custo registrado, trims formais já vigentes).

## 10. Adendo pós-gate (2026-08-28) — correções do review gate 3x

O gate 3x retornou 3 veredictos `PASS_WITH_FIXES` (review-9a2752e1 / review-838ab021 / review-c17f9a4e). Correções aplicadas pelo agente corretor sequencial (commit `fix: align impact scenarios with experiment power`; ver `process-log/reports/iteration-05-review-fix-report.md` e `process-log/reviews/iteration-05-review-summary.md`):

1. **Regra de decisão ACT-01 em 3 estados** — escala (SCALE/GO) exige ponto estimado ≥ 10% **E** IC95 excluindo 0 na direção favorável, sem guardrail violado; CONTINUE/LEARN quando IC cruza 0 (sem alegar eficácia); STOP/HARM com efeito adverso significativo ou guardrail crítico falhado. Poder por cenário (≈ 11/31/61% com N=136/braço) e P(falso GO por ponto ≥ 10% sob nulo) ≈ 24% passaram a ser **derivados em runtime** (gates G13-power-scenarios / G13-false-go / G13-decision-rule); piso operacional de 10% preservado; decisão de escala em 4 trimestres + 90d de follow-up.
2. **Linha `annualized` removida** da t19/evidence (usava 4×estoque = 320 ≠ fluxo 273/ano; "melhor evitar se confuso"); gate G13-annualized-absent.
3. **0,3393–0,5417 rotulada `observed cutoff range`** (min-max de 3 coortes disjuntas), NÃO CI; Wilson 95% do pooled ≈ 0,362–0,501 derivado separadamente e rotulado; overlap = 0 verificado (gate G13-disjoint).
4. **Sequenciamento:** ACT-03 → Now/pré-requisito com SLA ≤ 30d; ACT-01 inicia rollout somente após instrumentation readiness; ACT-04 permanece Later (gate G13-sequencing).
5. **Wording:** "eventos evitados" → "eventos afetados no cenário" (zero claim causal; G13-wording/G13-wording-md); "76,6%" corrigido para "uso antes do start_date" no adendo de premissas.
6. **Cosméticos:** negrito do share corrigido; horizonte alinhado (1ª decisão em 2 trimestres; escala em 4 + 90d); tolerância de precisão documentada (≤ 0,01%); literais de narrativa (lifts A/B/D/E e D 180d; KM/âncoras) derivados em runtime da t14/t12.
7. **Validação pós-fix:** 45 PASS / 0 WARN / 0 FAIL (32 + F11/F12 [t14b, t12] + 8 gates G13 + G13-wording-md); idempotência 2× + CWD; FAIL estrutural 2 cenários; 3 MVs; recálculo independente (power 10,8/30,9/60,6%; falso-GO 23,7%; Wilson 0,362–0,501; disjoint 193/0); 6 PNGs byte-idênticos; git ok (commit `fix: align impact scenarios with experiment power`; local == remote).
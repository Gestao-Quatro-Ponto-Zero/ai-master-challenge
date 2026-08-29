# Outline do Relatório Executivo — Iteração 07 (decidido ANTES da redação)

Data: 2026-08-29. Executor: agente único `deepseek-max` (via OpenCode Go).
Este arquivo fixa a narrativa do `solution/report-executivo.md` ANTES da
implementação do gerador (`solution/src/07_generate_executive_report.py`),
seguindo a prática das Iterações 03/05 (premissas commitadas antes do código).
Nenhum número é "escolhido" aqui: todos os valores materiais são derivados em
runtime das tabelas/evidence validados (It01–06) pelo gerador, com gates.
Este outline NÃO é reescrito retroativamente; revisões do gate 3x geram adendo.

---

## 1. Mensagem central (uma frase)

**O churn subiu porque contas recém-adquiridas estão saindo nos primeiros 90
dias (churn precoce de onboarding) — não por insatisfação geral, nem por uso,
nem por segmento; a base não permite provar causa, então a resposta é
instrumentar e testar um programa de ativação com experimento, com triage
semanal da watchlist em paralelo.**

## 2. Ask executivo (decisão pedida)

1. **Aprovar ACT-03 (Now):** instrumentação de dados com SLA ≤ 30d para o
   milestone de ativação em produção (pré-requisito de medição e do rollout).
2. **Aprovar ACT-01 (Now, gated):** programa de ativação/onboarding 0–90d com
   rollout gradual e holdout (experimento); rollout inicia só após ACT-03.
3. **Aprovar ACT-02 (Now):** triage semanal da watchlist top-20 (8 onboarding
   validados + 12 exposure-only); ACT-04 fica para depois (Later).
4. **Não escalar nada antes de evidência estatística:** regra de decisão em 3
   estados (SCALE/GO exige IC95 excluindo 0; CONTINUE/LEARN; STOP/HARM).

## 3. Três provas que sustentam a mensagem (cada uma = número + definição + fonte)

| Prova | Número central | Definição/limite | Fonte |
|---|---|---|---|
| P1 — o pico é real e é de contas novas | 43 primeiros eventos em dez/24 = 22,51% dos 191 elegíveis vs mediana 13,01% dos 6m anteriores (razão 1,73); controle de tenure: esperado 24,82, observado 43 | "primeiro evento" = 1ª ocorrência por conta na lente de eventos (C); "elegível" = signup ≤ mês sem evento anterior; dez/24 teve 117 episódios totais — 43 é o hazard de PRIMEIRO evento, não todos os episódios | t01, evidence/03 §2 |
| P2 — o mecanismo é o onboarding | pico: bucket 0–3m = 36/43 (83,7%, ratio 2,37); R1 ≤90d = 68,4% da janela (806.419/1.179.139 US$, exposição, NÃO perda); 53,4% dos primeiros eventos ≤90d do signup (188/352); única regra com validação temporal: lift 1,57/1,56/1,83 nos 3 cutoffs 90d (N≥25) | R1 = gross ending MRR (exposição contratual bruta, contrato §5); lift = precision/baseline em backtest point-in-time (It04), associação observada, NÃO efeito causal | t03/t03b/t03c, t14, evidence/03 §4, evidence/04 §6 |
| P3 — o resto não explica | uso total +225,3% (2.775→9.027 linhas) com intensidade mediana 0,0% (2,0→2,0); suporte: tickets/conta 0,309 vs 0,349, CSAT 4,0 vs 3,97, escalação 2,8% vs 5,1%; nenhum segmento com taxa ≥1,5x a global (limiar inalcançável por desenho; gap KM máx 6,9 p.p.); H4 corrigida: zero-uso churn 61,7% vs controle 52,7% (Δ 9,0 p.p.) — REFUTADA | comparações pré-evento com anti-leakage (contrato §8); CSAT/reason = evidência sugestiva (contrato §10), nunca causa | t05/t06/t07/t09/t10, evidence/03 §5–8 |

## 4. Estrutura obrigatória do relatório (pyramid principle; resposta primeiro)

1. **Executive summary + decisão solicitada** (250–350 palavras): causa operacional (churn precoce 0–90d), tamanho (dez/24: 43 primeiros eventos/22,51%; 117 episódios), incerteza (hipótese causal plausível; poder baixo), 2 ações Now (ACT-03 → ACT-01) + ask explícito.
2. **Como medimos churn** — reconciliação das lentes: 110 (snapshot, rótulo do corte, lente A) vs 486 assinaturas encerradas/312 contas (lente B, receita) vs 600 eventos/352 contas (lente C, diagnóstico). Lente por pergunta; nunca misturar; 117 episódios em dez ≠ 43 primeiros eventos.
3. **O que mudou / causa raiz** — pico e mecanismo (P1+P2); KM/censura (coortes Q4-24 com follow-up curto; Q2-24 churn KM t6 = 69,2%; global t6 = 0,4428); status explícito: **hipótese causal plausível, não prova**.
4. **O que não explica** — P3 (uso/suporte/segmentos/reasons), H4 corrigida; evita narrativa falsa de "uso cresceu = saudável".
5. **Segmentos e contas** — lifecycle states (S1–S5), não industry; 80 onboarding atuais / 621.981 US$ winner MRR; top-20 = 392.030 US$ (10,7% da exposição atual 3.668.852); 8 Tier A validados + 12 exposure-only; 8–10 contas específicas com MRR/sinal/limitação; link para t16/t11 completas.
6. **Ações priorizadas** — ACT-03 (Now, SLA ≤30d) → ACT-01 (Now, experimento com holdout); ACT-02 (Now, triage semanal); ACT-04 (Later). Owner, prazo, 1º sinal, métrica, stop/go em 3 estados.
7. **Impacto em faixa** — 2,7/6,9/13,0 eventos afetados em 90d; 21.104/53.497/101.078 US$ de MRR-equivalent exposure afetada em 90d; premissas nomeadas (incidência 0,4301 pooled; faixa observada 0,3393–0,5417 ≠ CI; Wilson 95% 0,362–0,501; redução 10/20/30% premissa de planejamento); NÃO revenue saved/forecast.
8. **Não fazer agora** — ML/score; descontos amplos; reason/CSAT como causa; automação sem holdout; ROI/revenue saved.
9. **Limitações e próximos dados** — base sintética; lentes decopladas (21,0% de eventos com sub encerrada ±30d); all-active no corte (500/500); proxies; poder baixo (MDE ≈37% em 4 trimestres; P(falso GO) ≈24%); próximos dados (milestone de ativação, reason estruturado, timestamps, CSAT coberto).
10. **Reprodução/evidence map** — `./run.sh`; runtime ~65–75 s; links relativos: contrato, evidence 01–05, tabelas, process log, verificador.

## 5. Gráficos (exatamente os 6 existentes; nenhum novo; path relativo; caption = takeaway)

| PNG | Onde | Takeaway do caption |
|---|---|---|
| `out/charts/a_monthly_events_and_rate.png` | §3 | Nível elevado sustentado com pico em dez/24 (43 primeiros eventos; 22,51%) |
| `out/charts/b_km_by_signup_quarter.png` | §3 | Coortes recentes churnam mais cedo (Q2-24: 69,2% em t6); Q4-24 censuradas |
| `out/charts/c_onboarding_exposure_by_duration.png` | §3 | 68,4% da exposição contratual (R1) em assinaturas ≤90d |
| `out/charts/d_usage_volume_vs_intensity.png` | §4 | Volume cresce; intensidade por conta não (0,0%) |
| `out/charts/It04_c_lifecycle_vs_current_mrr.png` | §5 | Jornada vs exposição atual: dimensões complementares, não substitutas |
| `out/charts/It04_d_backtest_lift.png` | §6 | Única regra com lift consistente: onboarding (1,57/1,56/1,83) |

## 6. Tabelas compactas (máximo necessário; sem parede de números)

1. Lentes de churn (pergunta → lente → contagem; inclui 117 vs 43 em dez/24);
2. Três evidências (P1/P2/P3 → número → fonte);
3. Contas específicas (8–10 linhas: conta, grupo, winner MRR, evidência, limitação);
4. Ações priorizadas (4 linhas: ID, decisão, owner, prazo, 1º sinal, stop/go);
5. Impacto em faixa (3 cenários + premissas; NOTA faixa≠CI);
6. Status causal/evidence map (achado → status → link de auditoria).

## 7. Word budget (contagem de palavras do markdown, sem código/frontmatter)

- `solution/report-executivo.md`: **alvo 1.500–2.000 palavras**; gate 1.400–2.400
  (tolerância de tabelas); gate do gerador conta palavras em runtime.
- `README.md` da submissão: **curto** — 350–600 palavras de conteúdo próprio
  (template oficial + resumos + links; a tabela de ferramentas existente é
  preservada/integrada, não recriada).
- Fraseamento: cada claim = número + definição + fonte (arquivo relativo).

## 8. Claims permitidos vs proibidos (gate do gerador e do verificador)

**Permitidos (obrigatórios no tom):**
- "hipótese causal plausível" para churn precoce (nunca "causa provada");
- exposição "MRR-equivalent exposure afetada no cenário" (nunca perda/receita);
- "eventos afetados" no cenário (nunca "evitados/salvos");
- faixas com premissas nomeadas; faixa observada ≠ intervalo de confiança;
- "afetados" com lente declarada (R1 = exposição; winner = estado);
- status por achado (descritivo | hipótese causal plausível | não identificável).

**Proibidos em contexto afirmativo (gate G-f):
- "receita perdida/salva", "revenue saved", "forecast", ROI pontual;
- causalidade afirmativa sem o rótulo de hipótese ("churn é causado por…");
- misturar/somar/subtrair as lentes 110/312/352/600 como mesma medida;
- "uso cresceu" como sinal de saúde sem a intensidade mediana (0,0%);
- segmento/CSAT/reason como causa de churn;
- números materiais sem origem rastreável (tabela/evidence relativa);
- menção a concorrentes, pesquisa interna, benchmark/baseline copiado;
- anualização de impacto apresentada como previsão;
- palavras de marketing/emoji/jargão sem definição.

## 9. Critérios de CEO-readability (não-técnico lê e age)

1. Resposta primeiro: a decisão pedida aparece nas primeiras 350 palavras;
2. Cada número tem definição no mesmo parágrafo ou em nota curta;
3. Parágrafos curtos; frases diretas; pt-BR; US$ conforme dados (sem conversão);
4. 6 gráficos com caption-takeaway; nenhum gráfico depende do texto;
5. Auditável por links relativos (contrato/evidence/tabelas/process log), mas
   compreensível sem abrir código;
6. "O que não fazer" explícito para evitar ação errada com dados fracos;
7. Nenhuma afirmação de receita/causalidade sem rótulo (gate G-f).

## 10. Gate do gerador (`07_generate_executive_report.py` — runtime, não literais)

- G1: números-chave do report == tabelas t01/t03/t03b/t05/t06/t09/t14/t15/t16/t18/t19
  (parsing dos CSVs no runtime; divergência → FAIL e geração abortada);
- G2: contas citadas ⊆ t16 (subset);
- G3: ação/impacto consistentes com t18/t19/t20;
- G4: claims proibidos (lista §8) ausentes em contexto afirmativo;
- G5: links relativos existem; exatamente 6 imagens, cada uma usada 1×;
- G6: word count 1.400–2.400 (report) — fora da faixa → FAIL;
- G7: sem concorrentes/pesquisa interna/baseline copiado (term-list);
- G8: determinismo (sem timestamp/now/random); paths relativos; offline.

## 11. Validações planejadas (após a implementação)

1. `./run.sh` 2× + CWD diferente + clone fresco: report byte-idêntico; 45 outputs
   anteriores inalterados + report novo = 46 outputs derivados;
2. Markdown: headings únicos, links relativos existem, 6 imagens (1× cada);
3. Inspeção programática dos 6 PNGs (magic bytes);
4. 3 spot checks manuais independentes (ex.: 43/22,51%; 68,4%; 392.030/10,7%);
5. FAIL: input ausente (tabela removida) → gerador exit != 0 e report NÃO fica
   stale (sem report novo escrito);
6. Sem nova dependência (imports stdlib+pandas);
7. `git diff --check` limpo; tree limpa após regeneração.

## 12. Update planejado do pipeline/README (It07)

- `run.sh`: estágios 01–05 → gerador 07 → verificador 06;
- `Makefile`: `stage-07` + `DERIVED` + `report-executivo.md` (contagens derivadas);
- `solution/README.md`: seção de outputs/estrutura atualizada (46 outputs);
- `06_verify_pipeline.py`: manifestos A2/A3 + contagens derivadas (sem renomear);
- `README.md` da submissão: template oficial preenchido (índice executivo);
  ferramentas/orquestração preservadas; data de submissão `pendente` (It10);
  sem marcar itens de It08/09 como concluídos.

## 13. Adendo técnico (2026-08-29, registrado na implementação — outline base não reescrito)

1. **KM global t6 (0,4428) removida do report:** a re-derivação pooled a partir de
   `t02b_cohort_km_at_risk.csv` (soma de at_risk/events por t entre coortes) produz
   0,462 — convenção de censura divergente da do `evidence/03 §7` (0,4428);
   reimplementar a convenção exata do estágio 03 seria duplicação analítica. No
   lugar, o report usa números deriváveis: taxa global de primeiro evento
   **70,4% (352/500)** e churn KM t6 **por coorte** (t02; Q1-24 58,9%; Q2-24
   69,2%; Q3/Q4-24 não observados — censura no corte), que sustentam a mesma
   mensagem (coortes recentes churnam mais cedo).
2. **Tabela de segmentos (7ª tabela):** a seção "Segmentos e contas" exige
   lifecycle states (S1–S5); a forma mais compacta é uma tabela de 5 linhas
   (segmento, N, current MRR, sinal de backtest), derivada de `t15_priority_segments.csv`.
3. **MDE/poder/P(falso GO):** derivados no evidence 05 §5 com convenções
   próprias (68/51/37%; 11/31/61%; ≈24%); a re-derivação independente no
   gerador difere **0–2 p.p. para MDE e poder** (70/52/37; 11/31/60 —
   arredondamento) e **~8 p.p. para P(falso GO)** (15,6% vs 23,7%/≈24% —
   convenção distinta de cálculo do falso GO, NÃO arredondamento; precisado
   no adendo §15 do gate 3x) — o report cita os valores do evidence 05 com
   gate de substring (fonte validada), e o Wilson CI 95% (0,362–0,501) é
   re-derivado em runtime de 83/193 (bate exato).

## 14. Critérios de aceitação da It07 (repetidos do prompt)

Causa raiz, segmentos/contas, ações/impacto respondidos integralmente; CEO lê e
age; 6 gráficos legíveis; report reproduzível (1 comando); README completo;
honestidade estatística (faixa≠CI; hipótese≠prova; exposição≠perda); process/git
completos. BLOCKED se qualquer número divergir das tabelas ou houver claim de
receita/causalidade indevida.

## 15. Adendo do gate de revisão 3x (It07-fix, 2026-08-29)

Registro da correção sequencial após os 3 veredictos do gate
(`PASS_WITH_FIXES`/`PASS_WITH_FIXES`/`PASS`); o outline base (§§1–12) e os
adendos §§13–14 NÃO foram reescritos retroativamente — este adendo documenta:

1. **§13.3 precisado (correção de redação do próprio adendo):** a frase
   "difere em 0–2 p.p." vale apenas para MDE e poder (70/52/37; 11/31/60 —
   arredondamento). Para **P(falso GO)** a re-derivação independente produz
   ~15,6% vs ≈24% (23,7%) do evidence 05 — divergência de ~8 p.p. por
   **convenção distinta de cálculo** (definição do falso GO e N por braço dos
   cenários), não por arredondamento. O report permanece correto: cita o
   evidence 05 com gate de substring e "≈" (fonte validada).
2. **Tabela de ações compactada (5 campos: ID/quando/owner/entrega/gate):**
   células curtas e completas, sem corte no meio de palavra; truncamento só
   em fronteira de palavra com '…' explícito; prazo, 1º sinal leading e
   stop/go completos permanecem em t18/t20 (linkados) e na prosa §6. Novo
   gate G3b no gerador detecta células penduradas e regressões de render.
3. **`lift` definido na primeira ocorrência (§5):** "lift (precisão da regra
   ÷ taxa base de incidência)" — fecha o critério §9.2 ("cada número tem
   definição").
4. **Margem de word budget restaurada:** report 2.389 → 2.275 palavras
   (gate 1.400–2.400; summary inalterado 322, dentro de 250–350); cortes
   apenas de redundância/prosa já coberta por tabelas/links — nenhuma âncora
   numérica removida (auditoria: zero números ausentes vs versão anterior).
5. **Modo 0644 na regeneração:** gerador aplica `os.chmod(tmp, 0o644)` antes
   do `os.replace` (mkstemp criava 0600; git não rastreia a diferença).
6. **Docs de processo sincronizados com valores reais** (77 PASS/0 FAIL; 6
   tabelas; word count medido em runtime pelo gate G6); README da submissão
   sem contagem stale de commits ("histórico git incremental e semântico" +
   comando `git log --author="Jose Nascimento"`).
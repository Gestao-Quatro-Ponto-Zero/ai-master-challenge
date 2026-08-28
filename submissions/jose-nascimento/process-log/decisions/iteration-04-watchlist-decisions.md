# Decisões — Iteração 04 · Watchlist operacional e validação temporal (regras PRÉ-especificadas)

**Contexto:** decisões da Iteração 04 (ciclos de reativação, jornada da conta, backtest point-in-time e watchlist). As regras do backtest e a regra de composição da watchlist foram **fixadas ANTES** de computar os resultados do backtest (escritas neste arquivo antes da primeira execução do script `04_lifecycle_watchlist.py`); nenhum threshold foi ajustado após ver os números. As decisões seguem o formato problema → opções → evidência → decisão → trade-off das iterações anteriores.

---

## D1 — O que cada "sinal" significa (três fenômenos distintos, nunca um só)

**Problema:** a base tem três formas de "voltou/saiu de novo": múltiplos `churn_events` por conta (recorrência), `is_reactivation=True` em eventos (reativação marcada) e transições de estado `active→inactive→active` no painel account-month (ciclo real de assinatura). Misturá-las produz contagens falsas (ex.: 175 contas com ≥2 eventos lidas como "175 contas que morreram/reviveram").

**Evidência (exploração de dados, It04):** 600 eventos / 352 contas com ≥1 evento; 175 contas com ≥2 eventos (59 com ≥3, máx 5); 61 flags de reativação em 55 contas; no painel account-month há apenas **2** transições `active→inactive` (2023-10→2023-11: A-180abf; 2024-08→2024-09: A-0baac2) e 281 transições `inactive→active`, das quais **279 são o gap inicial signup→primeira assinatura ativa** (ex.: A-019782 signup 2023-04, primeira assinatura ativa em 2023-06) e apenas **2** são retornos reais (as mesmas A-180abf e A-0baac2). Nenhuma das 2 contas com ciclo real tem `is_reactivation=True`; e 26 das 61 flags de reativação são o **primeiro** evento da conta (sem evento anterior na janela). As três lentes são estruturalmente descopladas (contrato §4/§7).

**Decisão:** tratar como três dimensões separadas e reportadas com nomes próprios: (a) **recorrência de eventos** (lente C, histórico); (b) **reativação marcada** (flag de evento, episódio); (c) **ciclo de estado** (lente B/painel, mudança real de estado de assinatura). Nenhuma contagem de uma lente é usada como proxy das outras.

**Trade-off:** o relatório fica mais complexo (3 dimensões), mas evita a confusão estrutural que a base sintética incentiva.

---

## D2 — `lifecycle_value_proxy` (jornada/valor) e exposição atual

**Problema:** como medir o valor acumulado da jornada de cada conta sem double-counting (somar MRR de assinaturas sobrepostas dobra o total: 62.216.507 vs 28.766.224 — razão 2,16×, contrato §6) e sem chamar o resultado de receita GAAP.

**Opções:** (1) soma de MRR de todas as assinaturas (double-counting); (2) soma do `winner_mrr` mensal do painel (1 linha por account×mês, sem duplicidade); (3) só o MRR atual.

**Decisão (D2):** `lifecycle_value_proxy` = Σ `winner_mrr` dos account-months da conta até o cutoff (1 valor por conta×mês; contas inativas contribuem 0 no mês). Declarado **proxy operacional**, não receita GAAP nem receita recuperada. `current winner MRR` (winner de 2024-12) é mantido como a dimensão de exposição atual, separada do proxy. Nenhuma soma de reativação é tratada como dinheiro recuperado (não há ligação demonstrável com receita — contrato §5).

**Trade-off:** o proxy favorece contas antigas (acumula ao longo do tenure) — viés declarado e quantificado (ver D5); a exposição atual preserva contas novas de alto MRR.

---

## D3 — Segmentos de atenção (estados/jornadas, não industry/channel/tier)

**Problema:** It03 (H6) não encontrou heterogeneidade material por industry/channel/tier (SURV_FLAG: nenhum segmento ≥10 p.p. abaixo da global; maior gap 6,9 p.p.). Os segmentos de atenção precisam vir de estados/jornadas observáveis.

**Decisão (D3):** cinco segmentos por jornada/estado no cutoff 2024-12-31, com overlap **declarado** (não oculto):
- **S1 Onboarding** — tenure ≤ 90 dias (80 contas; 54 com evento recente);
- **S2 Repeat-event** — ≥2 eventos (175 contas; 110 com evento recente);
- **S3 Reativação recente** — flag `is_reactivation` em out-dez/2024 (25 contas; subconjunto de S4);
- **S4 Evento recente** — último evento ≤ 90d antes do cutoff (178 contas);
- **S5 Alto valor** — `winner_mrr` ≥ P75 do cutoff (130 contas por empates no quantil; 125 esperados).

Cada segmento reporta N, current MRR, lifecycle proxy, taxa histórica de evento e o resultado do backtest da regra correspondente (D4). S3 ⊂ S4 por construção; as demais interseções (S1∩S2=26, S1∩S4=54, S2∩S4=110) são reportadas em tabela.

**Trade-off:** segmentos por jornada são mais acionáveis que por firmografia, mas se sobrepõem — exige matriz de overlap explícita.

---

## D4 — Backtest point-in-time sem ML: regras fixadas ANTES dos resultados

**Problema:** validar honestamente se algum sinal observável até a data índice prediz o próximo evento; proibido ajustar thresholds no mesmo período sem disclosure.

**Desenho (fixado a priori):**
- **Cutoffs:** 2024-03-31, 2024-06-30 e 2024-09-30 (o prompt pede 2; adicionamos o terceiro para robustez). Horizontes de 90 dias **completamente observáveis** (o mais tardio termina em 2024-12-29 ≤ corte 2024-12-31). Sensibilidade adicional: horizonte 180d para os dois primeiros cutoffs.
- **Elegíveis:** contas com `signup_date ≤ cutoff` (283 / 348 / 420).
- **Outcome:** ≥1 `churn_event` com `churn_date ∈ (cutoff, cutoff+90d]` (binário por conta; múltiplos eventos NÃO duplicam logos).
- **Features (somente dados ≤ cutoff):** `tenure_days`; `n_events_pre`; `n_react_pre`; `last_event_days`; `recent_ended_mrr_90d` (R1: `end_date ∈ (cutoff-90d, cutoff]`); `winner_mrr_at` (painel do mês do cutoff); `lifecycle_proxy_pre` (Σ winner ≤ cutoff). **Proibidos:** `accounts.churn_flag` (snapshot) e qualquer evento/assinatura/uso com data > cutoff.
- **Regras (thresholds fixos, sem tunagem):**
  - R_A recorrência: `n_events_pre ≥ 2`
  - R_B reativação: `n_react_pre ≥ 1`
  - R_C evento recente: `last_event_days ≤ 90`
  - R_D onboarding: `tenure_days ≤ 90`
  - R_E alta exposição: `winner_mrr_at ≥ P75` (percentil do cutoff)
  - R_F recorrência recente: R_A ∧ R_C
  - R_G reativação recente: R_B ∧ R_C
  - R_H onboarding com evento recente: R_D ∧ R_C
  - R_I alto valor com sinal: R_E ∧ (R_A ∨ R_B ∨ R_C)
- **Métricas por regra×cutoff:** N da regra, precision (P(outcome|regra)), recall, lift = precision/baseline, intervalo de Wilson 95%.
- **Racional das regras (de It03, não dos números do backtest):** R_D vem do mecanismo de causa raiz (churn precoce de coortes novas — H1/H8/H9: 75,3% dos primeiros eventos ≤6m, 53,4% ≤90d); R_A/R_B/R_C são os sinais de jornada do escopo desta iteração; R_E testa exposição como preditor.
- **Critério de decisão pré-registrado:** uma regra é "sinal validado" somente se lift > 1,15 **nos três cutoffs** de 90d com N ≥ 25; caso contrário, o sinal é descrito como associação/histórico, nunca como preditor. Se nenhuma regra validar, a watchlist é nomeada **operational priority/exposure** (ordenação por exposição + evidência), proibido score somando pesos.

**Trade-off:** regras simples e auditáveis sacrificam recall em favor de transparência e reprodutibilidade; 3 cutoffs curtos limitam o poder estatístico (N pequenos → intervalos largos, reportados).

---

## D5 — Top-20 current MRR vs top-20 lifecycle proxy (duas dimensões, não substituição)

**Problema:** ordenar contas só por MRR atual ignora jornada; só por proxy acumulado penaliza contas novas.

**Decisão (D5):** reportar **ambas** as ordenações lado a lado: overlap (Jaccard) e rank shifts por conta (ex.: A-68f37c — atual rank 5, lifecycle rank 1; A-a8d89d — lifecycle top-20, fora do top-20 atual apesar de 15.522/mês), mais correlação de Spearman entre as duas dimensões (0,575 na exploração). Viés declarado: o proxy acumula tenure → favorece contas antigas; MRR atual favorece contas novas de alto valor. Nenhuma dimensão substitui a outra; a watchlist usa exposição + evidência (D4/D6).

**Trade-off:** duas ordenações podem confundir leitores apressados; mitigado por tabela explícita de overlap/deslocamentos e guia de interpretação.

---

## D6 — Regra de composição da watchlist (tiers + caps declarados, sem score)

**Problema:** a watchlist precisa de contas específicas (ID, MRR, sinal, evidência) sem inventar poder preditivo nem score arbitrário.

**Opções:** (1) só onboarding (sinal validado) — top-20 todo de contas novas, ignora ação imediata de CS sobre episódios recentes; (2) só evento recente — ignora o único sinal com lift; (3) tiers com caps declarados (escolhida).

**Decisão (D6):** prioridade em **3 tiers**, com **caps de composição declarados** (regra de agregação, não score):
- **Tier A — sinal validado:** onboarding (tenure ≤ 90d) → top 8 por `winner_mrr` desc;
- **Tier B — acionabilidade operacional:** evento recente (último evento ≤ 90d, fora do Tier A) → top 8 por `winner_mrr` desc;
- **Tier C — proteção de receita:** recorrência ou reativação sem evento recente e `winner_mrr ≥ P50` → top 4 por `winner_mrr` desc.
Total 20. Justificativa dos caps 8/8/4: peso igual ao sinal validado (evidência) e à janela acionável (recência), metade disso para exposição pura; é uma escolha de governança declarada, reproduzível e auditável, NÃO um modelo de risco. Desempate determinístico: `winner_mrr` desc, depois `account_id` asc. Campos por linha: account_id, tier, evidências (onboarding/recorrência/reativação/datas), winner_mrr, lifecycle proxy, tenure, nº de eventos/subs, gross ending MRR recente, flag de qualidade (`accounts.churn_flag` como rótulo snapshot — proibido como feature, permitido como contexto), e guia de interpretação. **Não declara churn futuro nem target inexistente.**

**Trade-off:** caps fixos excluem algumas contas de alto MRR fora dos tiers (todas permanecem na tabela completa t11); a regra é transparente e qualquer re-fatia é reproduzível.

---

## D7 — Análise de reativação: sequência temporal com censura (nunca "sucesso")

**Problema:** 37 de 61 episódios de reativação não têm evento posterior observado; concluir "reativar funciona" seria erro de censura (muitas reativações são recentes: 26 flags em out-dez/2024).

**Decisão (D7):** por episódio de reativação (61): gap desde o evento anterior (mediana 45d, n=35 — 26 flags são o 1º evento da conta, sem gap), tempo até o próximo evento com **Kaplan-Meier com censura no corte** (sobrevivência em 90d ≈ 0,72; em 180d ≈ 0,64; mediana não alcançada na janela) e taxas com denominador explícito de follow-up (10/35 episódios com ≥90d de follow-up têm próximo evento ≤90d = 28,6%). Nenhuma taxa é chamada de "sucesso de reativação"; nenhum valor em US$ é atribuído a reativação (sem ligação demonstrável com receita — contrato §5).

**Trade-off:** intervalos amplos (N pequeno) e conclusões modestas, mas sem claim falso.

---

## D8 — Nomeação honesta da watchlist (dependente do backtest, decidida mecanicamente)

**Problema:** a nomenclatura precisa ser proporcional ao lift observado.

**Decisão (D8 — mecânica, aplicada após o backtest):** se R_D (onboarding) validar nos 3 cutoffs (lift > 1,15, N ≥ 25) e nenhuma outra regra validar, a watchlist é nomeada **"Operational Priority / Exposure Watchlist"** com o tier A ancorado no sinal validado e os demais tiers rotulados como acionabilidade/proteção, explicitando que **não é um score de risco de churn** (o lift de recorrência/reativação/MRR não é consistente). Nenhum número do backtest será re-interpretado para "salvar" uma regra.

**Trade-off:** nome menos ambicioso do que "churn risk score", mas honesto e defendível.

---

## D9 — Estrutura de saídas (tabelas e gráficos sem repetir It03)

**Decisão (D9):** tabelas `t11_account_lifecycle.csv` (500 contas), `t12_reactivation_recurrence.csv` (distribuições de eventos/reativações/episódios), `t13_state_cycles.csv` (ciclos reais vs lentes), `t14_backtest_temporal.csv` (regras×cutoffs), `t14b_backtest_detail.csv` (flags por conta×cutoff para auditoria), `t15_priority_segments.csv` (segmentos N/$), `t16_watchlist_top20.csv` (watchlist), `t17_rank_comparison.csv` (current vs lifecycle). Gráficos (prefixo `It04_`): (a) recorrência×reativação; (b) lentes de ciclo (evento vs assinatura vs estado); (c) current MRR × lifecycle proxy (top-20 destacados); (d) lift do backtest por cutoff com intervalos. It03 não possui nenhum desses.
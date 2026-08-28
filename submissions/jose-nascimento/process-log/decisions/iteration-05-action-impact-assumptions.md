# Decisões — Iteração 05 · Ações priorizadas, impacto em faixa e plano de medição (premissas ANTES do cálculo)

**Data/hora:** 2026-08-28 (fase A da Iteração 05, ANTES da implementação do script `05_actions_impact.py` e de qualquer cálculo de impacto).
**Método:** este arquivo fixa as premissas de ação/impacto/medição ANTES de computar números; o commit `docs: define action and impact assumptions` precede o commit do código, então a cronologia git prova a separação (prática It03, retomada conforme nota de transparência da It04).

**Fatos congelados (evidência validada It01–It04 — nenhum renegociado aqui):**
- Onboarding (tenure ≤ 90d) é a ÚNICA regra com lift consistente no backtest point-in-time: 1,57 / 1,56 / 1,83 (90d, cutoffs 2024-03-31/06-30/09-30, N ≥ 25; sensibilidade 180d 1,26/1,51).
- Segmentos amplos (industry/channel/tier), uso e suporte NÃO discriminam (It03 H3/H4/H5/H6 refutadas; H1/H8/H9 sustentadas como hipótese causal plausível de churn precoce).
- Watchlist top-20 = **operational priority/exposure**, NÃO score de risco (It04 D8; recorrência 0,44/0,41/0,89, reativação 0,52/0,41/1,29, alto MRR 0,56/0,85/0,71 não validam).
- R1 (gross ending MRR 1.179.139 na janela) = exposição contratual bruta, NÃO perda (contrato §5, D9).
- All-active no corte 2024-12-31 (500/500 ativas por estado) — validação direta de perda de estado no presente impossível.
- CAC, winback e custos NÃO existem na base — esforço é qualitativo (S/M/L), nunca custo monetário.

---

## 1. Ações candidatas (3–5; famílias A–E do prompt consolidadas)

| ID | Ação (família) | Racional (evidência) | Owner | Horizonte | Mecanismo esperado |
|---|---|---|---|---|---|
| ACT-01 | **Programa de ativação/onboarding 0–90d com milestones instrumentados e rollout gradual (A + D fundidas)** | único sinal com validação temporal (R_D 1,57/1,56/1,83); 53,4% dos primeiros eventos ≤90d do signup (It03 §4); R1 ≤90d = 68,4% da janela (exposição, não perda); pico 2024-12 = bucket 0-3m (83,7% share) | PM Onboarding (desenho) + CS (execução) | 90d até 1º sinal; 2 trimestres até decisão | reduzir tempo-para-ativação e taxa de primeiro evento em 90d por intervenção por estágio; o desenho experimental (rollout staggered com holdout) é o que pode, no futuro, sustentar causalidade — nada aqui é efeito causal provado |
| ACT-02 | **Triage operacional da watchlist top-20 (8 onboarding validados vs 12 exposure-only)** | watchlist já entregue (It04 D6); separar tratamento: Tier A (sinal validado) vs B/C (exposure-only, NÃO rotular risco) | CS Lead | imediato; cadência semanal | atenção humana priorizada por evidência+exposição; os 12 exposure-only recebem revisão de conta/renovação, sem claim de risco predito |
| ACT-03 | **Instrumentação de dados (lens unificada, timestamps, CSAT/reasons, milestone de ativação, reason estruturado)** | limitações estruturais da base: CSAT 41,2% nulos; reason 'unknown' 15,8%; uso fora da janela 76,6%; 21,0% dos eventos com sub encerrada ±30d; sem telemetria de ativação | Data/Product Eng | 1 trimestre | habilitar medição (leading metrics) e reduzir viés estrutural das futuras análises; pré-requisito do ACT-01 |
| ACT-04 | **Piloto OBSERVACIONAL de reativação/recorrência (baixa confiança, sem claim de ROI)** | reativação/recorrência NÃO validam como preditores (It04); mas associação histórica real (KM 90d 0,653 → 34,7% dos episódios com próximo evento ≤90d; mediana 187d; censura declarada) | CS + Data | 2 trimestres (observação) | medir recorrência pós-reativação com dados instrumentados (ACT-03); decisão de escalar só por regra pré-registrada; reativação mais barata/ROI PROIBIDO |

**Por que não A e D separados:** um único programa com desenho experimental (rollout staggered + holdout pré-registrado) resolve a ação E a causalidade de forma não duplicada (item 4 do prompt). **Por que ACT-04 existe mesmo sem lift:** a associação descritiva é real e a base não permite medir melhor — o piloto é observação + instrumentação, com gate explícito, zero ROI.

---

## 2. Fórmula de impacto e nomes honestos das métricas

**Fórmula (apenas ACT-01 tem estimativa de exposição defensável; as demais usam impacto operacional mensurável):**

```
expected_events_90d        = N_elegível × incidence_90d                      (descritivo histórico)
events_affected_90d        = N_elegível × incidence_90d × redução_relativa
expected_exposure_affected = Σ winner_mrr(elegíveis) × incidence_90d × redução_relativa
```

- `N_elegível` = contas onboarding atuais no corte (tenure ≤ 90d; esperado 80).
- `incidence_90d` = taxa histórica de primeiro/próximo evento em 90d entre contas onboarding = precision pooled da regra D nos cutoffs 90d (esperado 83/193 = 0,430; lower 0,339; upper 0,542).
- `redução_relativa` = cenário de planejamento 10% / 20% / 30% (conservador/base/ambicioso) — ver §3.
- Nomes: **`expected MRR-equivalent exposure affected`** (lente winner/estado, janela 90d). PROIBIDO: "receita salva", "receita recuperada", "revenue saved". Se anualizar: nome exato `annualized MRR-equivalent exposure` (aritmética ×4 coortes/ano, NÃO forecast).
- **Eventos ≠ logos ≠ revenue churn** (contrato §4: lentes C/B/A não intercambiáveis); **R1 não é perda** (§5); **lift ≠ efeito causal do programa** — o lift descreve a associação observada; a redução relativa é premissa de planejamento a ser testada pelo experimento (ACT-01), nunca derivada do lift.

**Impacto operacional (ACT-02/03/04 — sem US$ forçado):** cobertura do triage (20/20 por semana), % da exposição coberta (Σ winner top-20 / total = esperado 10,7%), quality coverage (CSAT com nota ≥ 90%, reason 'unknown' < 5%, uso em janela ≥ 90%, milestone de ativação capturado em 100% dos novos signups), N de reativações monitoradas com follow-up explícito.

## 3. Cenários pré-definidos (conservador/base/ambicioso) — ranges e ORIGEM

| Cenário | Redução relativa da taxa de evento 90d | Origem |
|---|---|---|
| Conservador | 10% | premissa de planejamento (nenhum programa existe na base para medir efeito); valor mínimo razoável de um programa de ativação; NÃO derivado de lift |
| Base | 20% | idem — ponto médio de planejamento |
| Ambicioso | 30% | idem — teto de planejamento |

- Sensibilidade de INCIDÊNCIA (origem: backtest It04, t14): lower 0,339 / base 0,430 / upper 0,542.
- Sensibilidade de POPULAÇÃO (origem: accounts.csv): estoque no corte 80; fluxo médio trimestral 2024 = 68,25 (trimestres 56/65/72/80).
- **Nenhum ponto mágico:** cada cenário é um produto simples de três componentes com origem rastreável (tabela t19 expõe os componentes, não só o resultado).
- Se anualizar: 1 linha com nome exato e nota de aritmética (não forecast).

## 4. Esforço qualitativo / recursos (nunca custo monetário)

- ACT-01: esforço **M** (desenho do programa + milestones + rollout); recursos: PM ×1 (tempo parcial), CS ×2 (execução semanal), Eng ×0,5 (instrumentação de milestone via ACT-03).
- ACT-02: esforço **S** (usa watchlist existente); recursos: CS Lead ×1 + agente CS ×1, 1–2h/semana.
- ACT-03: esforço **M**; recursos: Data Eng ×1 (tempo parcial), Product Eng ×0,5.
- ACT-04: esforço **S** (observação); recursos: CS ×0,5 + Data ×0,25.
- Nenhum valor em US$ de custo é afirmado (CAC/winback não existem na base).

## 5. Stop/go criteria e métricas leading/lagging

| Ação | GO | STOP | Leading | Lagging |
|---|---|---|---|---|
| ACT-01 | experimento com redução relativa ≥ 10% (limite inferior do cenário conservador) com regra de decisão pré-registrada e N/holdout declarados; se efeito < 10% por 2 trimestres → reescopo | violação de guardrail (ex.: CSAT em queda, escalações em alta) ou ausência de efeito com N suficiente | milestone completion rate; time-to-first-key-action (TTV); onboarding completion | first-event ≤90d (taxa por coorte); R1 gross exposure de subs curtas (lente separada); state MRR por lente |
| ACT-02 | cobertura ≥ 90% do top-20 triaged/semana por 4 semanas | sem ação documentada possível (dado ausente) por 2 semanas seguidas | % do top-20 com triage na semana; % com ação registrada | nº de contatos com desfecho documentado (renovação/ativação) em 90d |
| ACT-03 | metas de qualidade: CSAT ≥ 90%, reason unknown < 5%, uso em janela ≥ 90%, milestone de ativação 100% novos signups | 2 trimestres sem avanço nas metas | cobertura de cada campo instrumentado (semanal) | % de eventos com reason estruturado e sub vinculada ±30d |
| ACT-04 | após 2 trimestres de dados instrumentados, taxa de próximo evento ≤90d pós-reativação ≥ 34,7% (âncora histórica KM) → desenhar programa; senão encerrar piloto | custo de observação sem dado utilizável (instrumentação ACT-03 atrasada > 1 trimestre) | nº de reativações com follow-up explícito | taxa de próximo evento ≤90d/180d pós-reativação (KM com censura) |

## 6. Claims PROIBIDOS nesta iteração (e em todas as futuras)

1. "Revenue saved" / "receita salva" em qualquer forma (exposição afetada ≠ receita).
2. CAC queimado factual (não existe custo de aquisição na base; cenários CAC-equivalent It03 são nomeados).
3. Causalidade provada (o programa pode ser desenhado para testar causalidade; nenhum efeito é atribuído antes do experimento).
4. Score preditivo de churn (nenhuma regra além de onboarding valida; watchlist é operational priority/exposure).
5. Reativação mais barata que retenção / ROI de winback (sem ligação demonstrável com receita).
6. Anualização apresentada como forecast.
# Prompt 004 — Agent Hipóteses

**Data:** 2026-03-20
**Agent:** 03_hypothesis_agent.py
**Ferramenta:** Claude Code
**Executado por:** Lucas Reis

---

## Prompt enviado ao Claude Code

> Contexto: projeto G4 AI Master Challenge — Challenge 001 Diagnóstico de Churn.
>
> O cross-table revelou achados contraintuitivos que precisam de validação estatística.
> Três hipóteses foram REFUTADAS pelos dados (uso, auto_renew, urgent tickets).
> Uma confirmada com força: DevTools 31%, event 30.2%, features 60.9%.
>
> Rode python submissions/lucas-reis/solution/agents/03_hypothesis_agent.py
>
> Validar estatisticamente 5 hipóteses:
> H1: chi-square industry/channel × churn (odds ratios por grupo)
> H2: t-test tenure até churn — upgraders vs não-upgraders
> H3: t-test uso de features churners vs retidos (confirmar paradoxo)
> H4: chi-square satisfaction_null × churn
> H5: chi-square plan_tier × churn (OR Enterprise vs Basic)
>
> Output: CONFIRMADA/REFUTADA/INCONCLUSIVA + p-value + números + interpretação.
> Síntese: causa raiz, mecanismo, segmentos prioritários.

---

## Dependências instaladas

```bash
pip3 install scipy
```

---

## Resultados dos testes estatísticos

| Hipótese | p-value | Sig? | OR / t-stat | Conclusão |
|---------|---------|------|-------------|-----------|
| H1 industry | 0.0657 | ❌ (borderline) | DevTools OR=2.36× | Efeito real, amostra pequena |
| H1 referral | 0.0794 | ❌ (borderline) | event OR=2.53× | Efeito real, amostra pequena |
| H2 buyer's remorse | 0.0667 | ❌ (borderline) | t=-1.971, 165 vs 263 dias | Efeito presente, n=11 insuficiente |
| H3 uso paradoxo | 0.1054 | ❌ | t=1.627 | Não-significativo AND efeito pequeno |
| H4 sat null | 0.7410 | ❌ | OR=0.88 (inverso) | Hipótese na direção ERRADA |
| H5 plan_tier | 0.9993 | ❌ | χ²=0.001 | Nulo perfeito — plan_tier irrelevante |

---

## Insight metodológico crítico (julgamento humano)

**Nenhuma hipótese atingiu p<0.05. Mas isso não significa "nada funciona".**

A distinção entre:
- **Poder estatístico insuficiente** (H1, H2 — efeitos reais, amostra pequena)
- **Hipótese genuinamente nula** (H3, H4, H5 — sem efeito real)

...é o tipo de julgamento que a IA não fez sozinha e que um analista humano precisa aplicar.

H1 com OR=2.5× é economicamente relevante mesmo com p=0.07 — com dados reais de produção
(n>5.000), seria p<0.001. A decisão de recomendar ação sobre DevTools e event channel
é fundamentada nos odds ratios, não nos p-values.

---

## Decisão estratégica tomada

Com base nos achados do Agent 03, o Agent 04 (modelo preditivo) deve ser configurado com:
- Features segmentais (industry, referral_source) como candidatos de alta importância
- Features comportamentais (usage, satisfaction) como candidatos de baixa importância
- Target = a.churn_flag (22.0%) — já corrigido desde prompt_003
- A expectativa de AUC é moderada (~0.65–0.75) dado que o churn parece segmental,
  não comportamental

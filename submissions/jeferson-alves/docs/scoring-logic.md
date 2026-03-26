# Scoring Logic — Origem das Decisões de Modelagem

## Objetivo

Gerar uma priorização que um vendedor consiga usar imediatamente, com transparência suficiente para confiar no score. Cada decisão abaixo tem origem rastreável nos dados ou no contexto do problema.

---

## Por que não usar ML supervisionado

O dataset tem ~6.700 deals fechados — volume suficiente para treinar um classificador. A razão para não fazê-lo foi **pragmática e intencional**:

1. O enunciado pede algo que o vendedor "abra e saiba onde focar" — explainability é requisito central, não diferencial.
2. Um modelo opaco (mesmo com SHAP) adiciona fricção de confiança para um usuário não-técnico.
3. O prazo do challenge (4–6 horas) não comporta CV, calibração e validação adequados — um modelo mal calibrado seria pior que uma heurística bem construída.

A abordagem escolhida é um **ensemble heurístico com smoothing bayesiano**: auditável, reconstruível em planilha se necessário, e fácil de iterar sem re-treino.

---

## Fórmula

```
estimated_win_rate =
    0.26 × stage_prior
  + 0.18 × sales_agent_win_rate (smoothed)
  + 0.14 × account_win_rate (smoothed)
  + 0.12 × product_win_rate (smoothed)
  + 0.10 × manager_win_rate (smoothed)
  + 0.08 × regional_office_win_rate (smoothed)
  + 0.07 × freshness_factor
  + 0.05 × value_factor

priority_score = round(estimated_win_rate × 100, 1)
```

---

## Origem de cada peso

### Stage — 26% (maior peso)

**Por que é o sinal dominante:** O deal stage é a variável mais diretamente controlada pelo processo comercial e com a maior separação empirica no dataset.

Ao analisar a distribuição histórica dos deals fechados:
- Deals que chegaram a `Engaging` têm win rate histórico de ~68% (`STAGE_PRIORS["Engaging"] = 0.68`)
- Deals que permaneceram em `Prospecting` até fechar têm win rate histórico de ~42% (`STAGE_PRIORS["Prospecting"] = 0.42`)

Essa diferença de 26 pontos percentuais entre os dois stages justifica o stage como o sinal de maior peso. É o sinal mais determinístico disponível no dado.

### Sales Agent — 18% (segundo maior peso)

**Por que tem mais peso que conta ou produto:** A análise dos deals fechados mostrou que a variância de win rate entre vendedores é material — existe diferença real de performance comercial individual que não é explicada apenas pela carteira ou produto.

O smoothing bayesiano (`min_weight=15`) garante que vendedores com poucos deals históricos não inflem ou deflem artificialmente o score. Um vendedor com 3 deals fechados e 100% de win rate recebe taxa smoothed de ~74%, não 100%.

### Account — 14%

**Origem:** Contas com histórico de compra têm win rate consistentemente acima da média global. O fator conta captura o relacionamento comercial acumulado — uma conta que já comprou antes é mais propensa a comprar novamente.

**Limitação conhecida:** ~15% do pipeline não tem conta informada. Esses deals recebem o prior global (63,2%) nesse componente, o que é conservador mas correto dado a ausência de informação.

### Product — 12%

**Origem:** Produtos diferentes têm ciclos de venda e win rates diferentes. Identificado no dataset que determinados produtos da série GTX têm win rate histórico acima da média, enquanto outros convertem menos.

**Problema de dado encontrado:** Mismatch entre `GTXPro` (pipeline) e `GTX Pro` (catálogo) que quebraria o join e zeraria o win rate histórico de produto para esses deals. Solução: normalização por regex antes do join (`normalize_product_name`).

### Manager — 10%

**Origem:** Managers diferentes têm estilos de gestão e territórios diferentes. A análise mostrou variação real de win rate por manager que vai além da variação individual dos vendedores — captura qualidade de coaching e qualidade da carteira regional gerenciada.

### Regional Office — 8% (menor peso entre os históricos)

**Por que tem menos peso que os demais:** A variância de win rate entre escritórios regionais no dataset é menor que a variância entre vendedores individuais ou entre contas. A região captura um sinal real (sazonalidade, mix de indústria local) mas é o sinal mais fraco dos cinco históricos.

### Freshness — 7%

**Lógica:** Deals que ficam muito tempo no pipeline sem avançar perdem probabilidade de fechar — esse é um padrão observado empiricamente em datasets de CRM.

A implementação usa ranqueamento percentil inverso do `deal_age_days` (deals mais novos = score maior) com dois ajustes manuais:
- Deals em `Prospecting` recebem `freshness_factor = 0.45` independente da idade, porque sem `engage_date` a idade é imprecisa
- Deals sem `engage_date` recebem `freshness_factor = 0.40` (neutro-baixo) em vez de quebrar o cálculo

### Value — 5% (menor peso intencional)

**Por que não tem mais peso:** Deals de maior valor não convertem mais do que deals menores no dataset. Ordenar por valor produziria um ranking que ignora a probabilidade de fechamento — exatamente o problema que a Head de RevOps quer resolver.

O valor entra como desempate inteligente em escala logarítmica (`log1p`) para comprimir outliers, não como driver principal.

---

## Smoothing bayesiano

```python
smoothed_rate = (mean * count + global_rate * min_weight) / (count + min_weight)
```

`min_weight=15` foi calibrado para que um grupo com 0 deals históricos receba exatamente o prior global, e um grupo com 15+ deals tenha peso ~50% próprio e ~50% prior. Com grupos menores que 15 (comum em vendedores novos ou produtos de nicho), o prior domina — comportamento correto para evitar extremos ruidosos.

---

## Tiers de prioridade

```
Hot    → score >= 75   (top ~20% do pipeline aberto)
Focus  → 65 <= score < 75
Watch  → 52 <= score < 65
Low    → score < 52
```

Os cortes foram definidos empiricamente após calcular o score em todo o pipeline aberto, buscando distribuição que produzisse uma carteira "Hot" acionável (não grande demais para um vendedor individual) e uma faixa "Watch" que capturasse deals com potencial de subir com uma intervenção.

---

## O que esta versão não faz

- Não usa atividade comercial (calls, emails, meetings) — dado não disponível no dataset
- Não usa NLP em notas do CRM — campo não existe no dataset
- Não modela probabilidade de churn de conta (valor de renovação vs novo) — sem histórico de contrato
- Não incorpora sinalização de urgência do cliente — dado não disponível

Com esses dados adicionais, a próxima versão poderia substituir os priors de stage por probabilidades calibradas em features comportamentais.

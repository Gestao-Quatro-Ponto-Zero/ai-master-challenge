# Metodologia — G4 Lead Scorer

## 1. Objetivo

O produto não tenta responder "qual deal vai fechar?" como se houvesse informação suficiente para uma previsão confiável. Ele responde:

> Quais oportunidades abertas exigem atenção agora, e qual decisão comercial faz mais sentido com base nos dados disponíveis?

## 2. Dados

Os CSVs são dependências locais e não são versionados na submissão. A aplicação os procura em `datasets/crm-sales-predictive-analytics/`, diretamente em `datasets/`, ou no caminho definido por `CRM_DATA_DIR`.

Arquivos usados:

- `sales_pipeline.csv`: 8.800 oportunidades;
- `accounts.csv`: 85 contas;
- `products.csv`: 7 produtos;
- `sales_teams.csv`: 35 vendedores;
- `metadata.csv`: dicionário de campos.

O pipeline contém 6.711 oportunidades encerradas (`Won`/`Lost`) e 2.089 abertas (`Prospecting`/`Engaging`).

### Limpeza relevante

O pipeline usa `GTXPro`, enquanto o catálogo usa `GTX Pro`. A implementação normaliza o primeiro para o segundo antes do join.

O campo `sector` contém `technolgy`; ele é normalizado para `technology` apenas para consistência textual.

## 3. Leakage

`close_date` e `close_value` não são usados para gerar o score de oportunidades abertas.

`close_date` foi utilizado durante a fase analítica apenas para:

- organizar validação temporal;
- medir retrospectivamente ciclos históricos encerrados.

No produto, o score de uma oportunidade aberta depende apenas de informações disponíveis antes do resultado.

## 4. Por que não há um modelo preditivo de fechamento

Foram comparados candidatos simples e modelos supervisionados com split temporal:

- taxa histórica por produto;
- Seller × Product;
- Product × Sector;
- combinação de taxas históricas;
- regressão logística Core e Enriched;
- gradient boosting Core e Enriched.

As AUCs ficaram próximas de 0,50 e os lifts do topo foram modestos/instáveis. Por isso, um score apresentado como probabilidade de fechamento seria mais convincente visualmente do que defensável metodologicamente.

A decisão foi usar os padrões históricos como **contexto secundário**.

## 5. Historical Fit

### Taxas suavizadas

Para evitar taxas extremas em grupos pequenos:

```text
Smoothed Rate =
(Group Wins + Prior Strength × Global Win Rate)
/
(Group Deals + Prior Strength)
```

Prior strengths do MVP:

- Product: 100;
- Seller × Product: 30;
- Product × Sector: 30.

### Composição

Sem contexto de conta:

```text
70% Seller × Product
30% Product
```

Com setor disponível:

```text
50% Seller × Product
35% Product × Sector
15% Product
```

Cada taxa é comparada ao baseline global e transformada em um índice 0–100, em que 50 representa comportamento histórico aproximadamente equivalente ao baseline.

### Confiança

- `Limited`: Seller × Product com menos de 15 observações;
- `High`: pelo menos 30 observações em Seller × Product e Product × Sector;
- `Medium`: demais casos.

A confiança é mostrada separadamente e não reduz artificialmente o score.

## 6. Attention Need

Somente deals em `Engaging` possuem `engage_date`. Para eles:

1. calcula-se `days_in_engaging` usando snapshot de 31/12/2017;
2. compara-se a idade com ciclos históricos encerrados;
3. utiliza-se Product × Sector quando há pelo menos 30 observações, caso contrário Product e depois Global.

Estados:

| Percentil histórico | Score | Estado          |
| ------------------- | ----: | --------------- |
| < P50               |    20 | Normal          |
| P50–P75             |    40 | Watch           |
| P75–P90             |    70 | Needs Attention |
| P90–P95             |   100 | Urgent Review   |
| > P95               |    60 | Stale           |

`Stale` cai para 60 propositalmente: um deal extremamente velho deve provocar uma decisão de pipeline, não receber esforço infinito.

Para `Prospecting`, o timeline signal é indisponível porque não existe `created_date`.

## 7. Priority Score

### Engaging

```text
Priority Score = 0.35 × Historical Fit + 0.65 × Attention Need
```

### Prospecting

```text
Priority Score = Historical Fit
```

Nesse estágio, a interface informa explicitamente que não existe sinal temporal.

O Priority Score é um ranking operacional e **não** representa chance percentual de fechamento.

## 8. Action Category

A categoria é definida pela combinação de Historical Fit e estado de Attention Need. Exemplos:

- Fit positivo + Needs Attention/Urgent Review → `Focus Now`;
- Fit positivo + Stale → `Re-engage`;
- Fit fraco + Needs Attention → `Requalify`;
- Fit típico/fraco + Stale → `Qualify or Drop`.

A aplicação ordena primeiro pelo rank da categoria e, dentro da categoria, pelo Priority Score.

Isso evita que um `Qualify or Drop` com score numericamente alto apareça acima de um `Focus Now`.

## 9. Explainability

As explicações são determinísticas, baseadas nas taxas suavizadas e no aging calculado. Nenhum LLM gera justificativas em runtime.

Exemplos:

- "Seller-product history is 12% above the portfolio baseline.";
- "Account context is unavailable; fit uses core historical evidence only.";
- "This deal has been Engaging for 103 days, around the 90th percentile of comparable historical cycles."

## 10. Caminho para produção

Um sistema real deveria adicionar:

- `created_date` e datas de mudança de estágio;
- `last_activity_date`;
- reuniões, emails e chamadas;
- próxima ação e data prometida;
- valor estimado da oportunidade;
- stakeholders e sinais de intenção;
- backtesting em snapshots reais do CRM.

Com esses dados, faria sentido reavaliar um modelo preditivo e separar claramente `Win Likelihood` de `Attention Priority`.

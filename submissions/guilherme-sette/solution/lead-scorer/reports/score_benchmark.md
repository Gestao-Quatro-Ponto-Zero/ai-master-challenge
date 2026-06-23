# Score Benchmark

Este benchmark e um sanity check historico, nao uma prova de forecast calibrado.

Metodologia:

- usa oportunidades fechadas com `engage_date` conhecido;
- divide o historico por tempo: 70% mais antigo para construir taxas e 30% mais recente para testar ranking;
- compara uma heuristica compativel com o score V1 contra baselines simples;
- mede win rate no topo da lista, lift contra a media e captura de receita ganha.

## Metadata

```json
{
  "train_rows": 4697,
  "test_rows": 2014,
  "test_overall_win_rate": 0.6212,
  "test_total_won_revenue": 2968498.0,
  "split": "70% earliest engage_date train / 30% latest engage_date test"
}
```

## Resultado principal - Top 10%

| strategy | top_cut | top_n | top_win_rate | lift_vs_overall_win_rate | won_revenue_capture | avg_score_top |
| --- | --- | --- | --- | --- | --- | --- |
| seller_win_rate_baseline | 10.0% | 201 | 66.2% | 1.06x | 11.6% | 68.31 |
| v1_compatible_score | 10.0% | 201 | 65.2% | 1.05x | 24.8% | 72.01 |
| product_win_rate_baseline | 10.0% | 201 | 63.7% | 1.02x | 0.2% | 65.34 |
| value_only | 10.0% | 201 | 62.2% | 1.00x | 25.8% | 75.2 |

## Resultado principal - Top 20%

| strategy | top_cut | top_n | top_win_rate | lift_vs_overall_win_rate | won_revenue_capture | avg_score_top |
| --- | --- | --- | --- | --- | --- | --- |
| value_only | 20.0% | 403 | 64.8% | 1.04x | 48.6% | 73.91 |
| v1_compatible_score | 20.0% | 403 | 62.8% | 1.01x | 44.4% | 71.11 |
| seller_win_rate_baseline | 20.0% | 403 | 62.8% | 1.01x | 22.0% | 67.55 |
| product_win_rate_baseline | 20.0% | 403 | 62.8% | 1.01x | 3.5% | 65.32 |

## Todos os cortes

| strategy | top_cut | top_n | top_win_rate | lift_vs_overall_win_rate | won_revenue_capture | avg_score_top |
| --- | --- | --- | --- | --- | --- | --- |
| product_win_rate_baseline | 10.0% | 201 | 63.7% | 1.02x | 0.2% | 65.34 |
| seller_win_rate_baseline | 10.0% | 201 | 66.2% | 1.06x | 11.6% | 68.31 |
| v1_compatible_score | 10.0% | 201 | 65.2% | 1.05x | 24.8% | 72.01 |
| value_only | 10.0% | 201 | 62.2% | 1.00x | 25.8% | 75.2 |
| product_win_rate_baseline | 20.0% | 403 | 62.8% | 1.01x | 3.5% | 65.32 |
| seller_win_rate_baseline | 20.0% | 403 | 62.8% | 1.01x | 22.0% | 67.55 |
| v1_compatible_score | 20.0% | 403 | 62.8% | 1.01x | 44.4% | 71.11 |
| value_only | 20.0% | 403 | 64.8% | 1.04x | 48.6% | 73.91 |
| product_win_rate_baseline | 30.0% | 604 | 58.0% | 0.93x | 7.0% | 65.11 |
| seller_win_rate_baseline | 30.0% | 604 | 63.4% | 1.02x | 31.6% | 67.01 |
| v1_compatible_score | 30.0% | 604 | 63.2% | 1.02x | 63.6% | 70.44 |
| value_only | 30.0% | 604 | 64.7% | 1.04x | 69.0% | 73.16 |

## Leitura pratica

- No top 10%, o score V1 teve win rate de 65.2%, contra 62.2% do baseline por valor.
- No top 20%, o baseline por valor capturou 48.6% da receita ganha, contra 44.4% do score V1.
- Leitura honesta: valor puro e um baseline forte para captura de receita historica; o score V1 nao deve ser vendido como maximizador puro de receita.
- A utilidade do V1 esta em priorizacao operacional com explicabilidade, fit vendedor-oportunidade, saneamento de dados e governanca de remanejamento.
- Como nao ha snapshots reais, este teste deve ser tratado como evidencia direcional para o desafio, nao como validacao de modelo em producao.
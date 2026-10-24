# Relatório de Backtest Out-of-Time

| Estratégia / Modelo | AUC-ROC | Brier Score | Lift @ Top 10% | Lift @ Top 20% | Precisão @ Top 20% |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **🎯 RevOps Survival Engine (Nosso)** | **0.5565** | **0.2428** | **1.09x** | **1.07x** | **65.3%** |
| Baseline 1: Valor Nominal (sales_price) | 0.4834 | N/A | 0.96x | 0.96x | 58.2% |
| Baseline 2: Aging (-cycle_days) | 0.4790 | N/A | 1.03x | 0.96x | 58.5% |
| Baseline 3: Média do Vendedor | 0.4955 | 0.2429 | 0.95x | 1.01x | 61.6% |

**Receita Real Capturada no Top 20%:** $2,515,771.00 USD

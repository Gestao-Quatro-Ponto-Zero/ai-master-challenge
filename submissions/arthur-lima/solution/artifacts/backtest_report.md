# Relatório de Backtest Out-of-Time

| Estratégia / Modelo | AUC-ROC | Brier Score | Lift @ Top 10% | Lift @ Top 20% | Precisão @ Top 20% |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **🎯 RevOps Survival Engine (Nosso)** | **0.5021** | **0.2398** | **0.94x** | **0.96x** | **60.3%** |
| Baseline 1: Valor Nominal (sales_price) | 0.4916 | N/A | 1.10x | 1.01x | 63.4% |
| Baseline 2: Aging (-cycle_days) | 0.5011 | N/A | 0.92x | 0.90x | 56.7% |
| Baseline 3: Média do Vendedor | 0.5070 | 0.2355 | 1.10x | 1.05x | 66.0% |

**Receita Real Capturada no Top 20%:** $625,063.00 USD

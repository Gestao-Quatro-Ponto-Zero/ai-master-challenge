# Análise — scripts reprodutíveis

Scripts que produziram o diagnóstico, o classificador e o benchmark. São **evidência do processo** (ver [`../../process-log/PROCESS_LOG.md`](../../process-log/PROCESS_LOG.md)) e permitem reproduzir os números da submissão.

## Dados (públicos, não versionados aqui)

- **Dataset 1** — [Customer Support Ticket Dataset](https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset) → `customer_support_tickets.csv`
- **Dataset 2** — [IT Service Ticket Classification Dataset](https://www.kaggle.com/datasets/adisongoh/it-service-ticket-classification-dataset) → `all_tickets_processed_improved_v3.csv`

> Os scripts usam caminhos absolutos da máquina de desenvolvimento (`D:\Projetos\Case G4\data\...`). Ajuste o topo de cada script para o seu caminho antes de rodar.

## Ordem e propósito

| Script | O que faz |
|---|---|
| `validate_datasets.py` | Auditoria inicial — colunas, volumes, confirma texto templated / Resolution sintética |
| `phase0_integrity.py` | Confirma os 3 landmines: durações negativas (49%), CSAT sem driver (R²=0,003), uniformidade |
| `phase1_diagnosis.py` | Diagnóstico operacional + gera as figuras `01`–`04` |
| `phase2_classifier.py` | Treina TF-IDF + Regressão Logística (86,5%), gera figs `05`–`06` e o modelo `.joblib` |
| `phase2b_llm_compare.py` | Benchmark TF-IDF vs Haiku/Sonnet/Opus zero-shot (prompt cru) — *requer chave da API Anthropic, lida de um arquivo local* |
| `phase2c_opus_fair.py` | Opus com prompt caprichado + breakdown por classe — *idem* |
| `make_sample_tickets.py` | Gera o `sample_tickets.csv` usado pelo protótipo |

## Requisitos

```
pandas · scikit-learn==1.8.0 · matplotlib · joblib · anthropic (só para 2b/2c)
```

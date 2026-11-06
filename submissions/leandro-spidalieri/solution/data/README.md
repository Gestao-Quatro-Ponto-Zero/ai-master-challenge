# Dados oficiais locais

Use Python 3.13, com as dependências do [setup](../../README.md). Em `solution/`:

```bash
.venv/bin/python scripts/pipeline.py acquire
.venv/bin/python scripts/pipeline.py audit
```

O comando de aquisição busca os ZIPs públicos do Kaggle e valida o SHA-256 do CSV extraído antes de gravá-lo. A URL pública pode entregar uma revisão mais nova. O pipeline recusa arquivos com bytes diferentes dos snapshots v1 verificados, mesmo que o nome seja igual.

Se o download automático estiver indisponível, baixe a versão 1 de cada página oficial, extraia apenas o CSV indicado e coloque em `solution/data/raw/` com o nome original.

| Fonte Kaggle | Arquivo | Versão |
|---|---|---:|
| [Customer Support Ticket Dataset](https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset) | `customer_support_tickets.csv` | 1 |
| [IT Service Ticket Classification Dataset](https://www.kaggle.com/datasets/adisongoh/it-service-ticket-classification-dataset) | `all_tickets_processed_improved_v3.csv` | 1 |

A licença CC0 e as versões foram verificadas nas APIs de metadados. O [manifesto](../artifacts/manifest.json) contém origem, data, nomes reais de colunas, bytes e hashes. Os [rótulos de TI](../artifacts/it-quality.json) vêm de `Topic_group`. No Dataset 1, `Customer Email`, `Customer Age`, `Customer Gender` e `Date of Purchase` existem no CSV. Campos pessoais e data de compra ficam fora das features e do cubo. A resolução e a descrição são usadas somente na auditoria de qualidade. O Dataset 2 usa só `Document` como feature e `Topic_group` como alvo.

Mantenha originais intactos. Dados brutos, ZIPs, metadados baixados e artefatos locais de execução são ignorados no Git.

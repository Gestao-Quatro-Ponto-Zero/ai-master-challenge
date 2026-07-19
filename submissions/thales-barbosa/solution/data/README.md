# Dados

Os dois datasets brutos (públicos no Kaggle, licença CC0) estão incluídos para a solução rodar sem downloads:

| Arquivo | Fonte | Registros |
|---|---|---|
| `customer_support_tickets.csv` | [Customer Support Ticket Dataset](https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset) | 8.469 × 17 |
| `it_service_ticket_classification.csv` | [IT Service Ticket Classification](https://www.kaggle.com/datasets/adisongoh/it-service-ticket-classification-dataset) | 47.837 × 2 |

A pasta `processed/` (parquets com features) é gerada pelo fluxo completo `python bootstrap.py` e não é versionada. O módulo `python src/data_prep.py` pode ser usado isoladamente apenas para regenerar essa etapa.

O banco `app.db` é criado automaticamente no primeiro start do protótipo para persistir tickets e resoluções da demonstração. Ele é estado local de runtime e não é versionado.

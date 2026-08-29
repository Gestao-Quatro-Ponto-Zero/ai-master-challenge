# Dados brutos — RavenStack (5 CSVs)

Esta pasta contém os cinco datasets do Challenge 001 (Diagnóstico de Churn), copiados
byte-for-byte da origem local e commitados para reprodutibilidade **offline** do pipeline.

## Origem oficial (citada pelo challenge)

- **Dataset:** [SaaS Subscription & Churn Analytics](https://www.kaggle.com/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset) (Kaggle)
- **Licença:** MIT — conforme o README oficial do challenge (`challenges/data-001-churn/README.md`).
- **Autor do dataset:** rivalytics (Kaggle).

> Nota de uso: estes arquivos são distribuídos com o repositório apenas para permitir a
> re-execução integral da análise sem acesso à rede. Nenhuma outra fonte é necessária.

## Snapshot e checksums (MD5)

Checksums capturados na origem em 2026-08-28 (Iteração 00) e re-verificados após a cópia
(Iteração 01): cópia byte-for-byte, MD5 idêntico entre origem e esta pasta.

| Arquivo | MD5 | Linhas (com cabeçalho) | Registros (dados) |
|---|---|---|---|
| `ravenstack_accounts.csv` | `2c1dbd0d9d25ef044564c10e56ce59a5` | 501 | 500 |
| `ravenstack_churn_events.csv` | `7ac3c66bc4212f9f2136772ed3bfcb4d` | 601 | 600 |
| `ravenstack_feature_usage.csv` | `0377a02ec034ef5d30f05b66a434e1ab` | 25.001 | 25.000 |
| `ravenstack_subscriptions.csv` | `94073fd10488eda224a1687d5414bb7c` | 5.001 | 5.000 |
| `ravenstack_support_tickets.csv` | `51e144eced16a86370f9d4ce7ef0b9e4` | 2.001 | 2.000 |

## Propósito

- Fonte única de dados do pipeline (Iterações 01–06); nenhum download em runtime.
- Auditoria de estrutura/qualidade/integridade: `solution/src/01_ingest_audit.py` →
  `solution/evidence/01_audit_report.md`.

## Tabelas e chaves (conforme brief do challenge)

| Arquivo | Conteúdo | Chave |
|---|---|---|
| `ravenstack_accounts.csv` | Contas (indústria, país, canal, plano, trial, flag de churn) | `account_id` |
| `ravenstack_subscriptions.csv` | Assinaturas (MRR, ARR, plano, upgrades/downgrades, billing) | `subscription_id` → `account_id` |
| `ravenstack_feature_usage.csv` | Uso diário por feature (contagem, duração, erros, beta) | `subscription_id` |
| `ravenstack_support_tickets.csv` | Tickets (resolução, first response, satisfação, escalações) | `account_id` |
| `ravenstack_churn_events.csv` | Eventos de churn (reason code, refund, feedback) | `account_id` |

## Uso offline

- O script `src/01_ingest_audit.py` resolve esta pasta por path relativo ao próprio
  projeto (`solution/data/raw/`) — sem rede, sem hardcode de paths de máquina.
- Nenhum arquivo desta pasta deve ser modificado; alterações invalidam os checksums
  acima e a auditoria.
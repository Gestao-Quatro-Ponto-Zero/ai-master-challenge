# Auditoria de ligação entre as tabelas

Gerado por `solution/scripts/01_build_dataset.py`. Chaves ligam 100%; **datas entre tabelas não**.

| checagem | resultado | leitura |
|---|---|---|
| Contas | 500 |  |
| Assinaturas / contas com assinatura | 5000 / 500 |  |
| Assinaturas órfãs (account_id inexistente) | 0 |  |
| Linhas de uso órfãs (subscription_id inexistente) | 0 |  |
| Tickets órfãos | 0 |  |
| Eventos de churn órfãos | 0 |  |
| Contas sem nenhum ticket | 8 |  |
| Assinaturas sem nenhum uso | 33 |  |
| Contas com churn_flag=True | 110 | 22.0% da base |
| ...dessas, com TODAS as assinaturas encerradas | 0 | conta 'churnada' continua com assinaturas ativas |
| Contas com ≥1 evento em churn_events | 352 | 600 eventos |
| Contas com churn_flag E evento | 75 |  |
| Contas com churn_flag SEM evento | 35 |  |
| Contas com evento SEM churn_flag | 277 |  |
| Contas com assinatura iniciada após o último churn | 284 | de 352 |
| Eventos de churn com assinatura encerrada ±7 dias | 47 | de 600 |
| Uso fora da vigência da assinatura | 77.7% |  |
| Tickets abertos antes do signup da conta | 53.8% |  |
| Plano da conta = plano da assinatura mais recente | 34.4% | acaso seria ~33% |
| Notas de satisfação 1 ou 2 | 0 | escala 1–5 |
| Tickets sem nota de satisfação | 41.2% |  |
| Associação reason_code × feedback_text (V de Cramér) | 0.06 | 0 = nenhuma; motivo e comentário não conversam |
| Assinaturas trial com MRR=0 | 778 de 778 |  |

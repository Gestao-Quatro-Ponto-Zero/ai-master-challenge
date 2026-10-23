# Qualidade de dados — run `3f3c24da` (2026-10-23)

Fonte: Kaggle `rivalytics/saas-subscription-and-churn-analytics-dataset`, versão 1, via MCP.
Carga: 33.100 linhas lidas, **33.100 no silver, 0 rejeitadas**.

Conferido contra os CSVs:

| Controle | CSV | Silver |
|---|---|---|
| Σ MRR | 11.338.747 | 11.338.747 |
| Σ `usage_count` | 250.525 | 250.525 |
| Σ CSAT | 4.678 | 4.678 |
| Σ refunds | 8.652,25 | 8.652,25 |

A segunda execução foi marcada como `skipped`: nenhum arquivo novo e nenhuma linha duplicada no bronze. A carga é idempotente.

## Checagens

| Severidade | Checagem | Resultado | O que significa para a análise |
|---|---|---|---|
| error | linhas rejeitadas · fim antes do início · MRR negativo · ticket fecha antes de abrir | ✅ 0 | Integridade básica ok; o gold pode ser construído |
| warning | churn antes do cadastro · ARR ≠ 12×MRR | ✅ 0 | — |
| warning | **churn sem fim de assinatura** | 594 de 600 | Churn e assinaturas são desacoplados → churn vem só de `churn_events` (decisão de 2026-10-23); KPIs de receita levam ressalva |
| warning | **contas com várias assinaturas abertas** | 500 de 500 | Somar MRR de tudo infla a receita → regra de MRR vigente a validar no gold |
| warning | **CSAT sem notas 1 e 2** | escala 3–5 apenas | "Satisfação ok" é garantida pela própria escala dos dados — achado central para H1 |
| warning | evento de churn com flag falsa / flag sem evento | 277 / 35 contas | `accounts.churn_flag` não é confiável |
| warning | `usage_id` colidindo | 42 linhas (21 ids) | Eventos diferentes com o mesmo id; mantidos com sufixo `#n` |
| warning | **uso fora da assinatura** | 19.432 de 25.000 (78%) | Uso não pode ser analisado "dentro da assinatura"; analisar por conta e data do uso |
| info | CSAT sem resposta | 825 de 2.000 (41%) | A média de satisfação ignora 41% dos tickets |
| info | assinaturas sem uso | 33 de 5.000 | — |
| info | feedback pouco variado | 4 textos distintos em 452 | Feedback livre não tem informação analítica |

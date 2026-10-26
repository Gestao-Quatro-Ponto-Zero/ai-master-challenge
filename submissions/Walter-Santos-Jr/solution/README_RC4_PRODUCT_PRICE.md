# RC4 DEV — Produto e preço no Deal Closure

- A aba **Encerrar deal** mostra produto e preço de catálogo do CSV `opportunities.csv` via `/api/sales-action/{id}`; não permite editar o preço de referência.
- O valor de fechamento Won permanece obrigatório e independente do preço de catálogo.
- Quantidade e moeda não existem explicitamente na fonte de oportunidades; não são presumidas.
- O fechamento persiste `product_snapshot` e `catalog_price_snapshot` em `deal_closures` (migração aditiva de SQLite) e inclui esses campos no evento de auditoria.
- O histórico existente permanece intacto; encerramentos anteriores à migração terão snapshots nulos.
- Nenhuma sincronização de KPIs históricos Head/Manager foi implementada nesta alteração.

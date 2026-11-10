# Fonte dos dados

- Dataset: CRM Sales Predictive Analytics (Kaggle), indicado pelo README do challenge 003.
- Endereço: https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics
- Licença: CC0 (domínio público), como declarado no README do challenge.
- Data do download: PENDENTE (pergunta feita ao Daniel em 10/11/2026 às 15:08 -03; os arquivos já estavam na pasta de trabalho nessa data).
- Arquivos: `accounts.csv`, `products.csv`, `sales_teams.csv`, `sales_pipeline.csv`, copiados sem nenhuma alteração. O download traz também `metadata.csv` (o dicionário de campos do próprio dataset), que não é usado pela solução e não foi copiado.
- Conferência: `sha256sum -c SHA256SUMS` nesta pasta.

Os dados ficam no repositório para que quem avalia rode tudo sem conta no Kaggle. Nenhuma linha foi corrigida nos arquivos: as normalizações (por exemplo o produto `GTXPro`, que no catálogo é `GTX Pro`) são feitas no código e impressas por ele.

# Fonte dos dados

- Dataset: CRM Sales Predictive Analytics (Kaggle), indicado pelo README do challenge 003.
- Endereço: https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics
- Licença: CC0 (domínio público), como declarado no README do challenge.
- Data do download, nas palavras do Daniel: "Baixei o dataset do Kaggle hoje, 10/11/2026, por volta das 15h05 e extraí as 15:06."
- Arquivos: `accounts.csv`, `products.csv`, `sales_teams.csv`, `sales_pipeline.csv`, copiados sem nenhuma alteração. O download traz também `metadata.csv` (o dicionário de campos do próprio dataset), que não é usado pela solução e não foi copiado.
- Conferência: `sha256sum -c SHA256SUMS` nesta pasta.

Os dados ficam no repositório para que quem avalia rode tudo sem conta no Kaggle. Nenhuma linha foi corrigida nos arquivos: as normalizações (por exemplo o produto `GTXPro`, que no catálogo é `GTX Pro`) são feitas no código e impressas por ele.

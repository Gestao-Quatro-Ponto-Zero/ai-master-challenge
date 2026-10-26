# RC4 DEV — Head Executive Workspace

Escopo desta iteração: apenas Diretoria / Head. Manager e Seller preservados para revisão posterior.

- Navbar: logotipo/avatar e seleção vertical Central, East, West. Indicadores comerciais e donut antigos ocultos somente para Head.
- Aside: gerentes da região selecionada, com opção de remover filtro de gerente.
- Main: 12 cards (10 setores, Não informado, All Sectors), donut Won/Lost, Prospecting e Engaging, Account 360°, KPIs derivados e coortes.
- Contexto: região -> gerente (opcional) -> setor; mudanças recalculam dados históricos e invalidam requisições anteriores.
- Fonte: `sales_pipeline_history.csv` e `historical_dimensions.csv` (dimensões extraídas da planilha original All_Accounts.xlsx por opportunity_id).
- `sector=28` no Excel original significa setor não informado; não é um 11º setor.
- Receita Won vem de `close_value`; exposição Lost usa `sales_price` de catálogo e não significa receita recuperável.
- As coortes são agrupadas por `engage_date`; não indicam causa ou conversão preditiva.
- O Deal Score continua índice heurístico, não probabilidade calibrada.
- Testes: `python -m unittest discover -s tests -q`.
- Pacote DEV, não pacote de submissão; não publicado no GitHub.

# Referential integrity

## Objetivo
Garantir consistência entre fato (`sales_pipeline.csv`) e dimensões (`accounts`, `products`, `sales_teams`).

## Relacionamentos validados
- `sales_pipeline.account -> accounts.account`
- `sales_pipeline.product -> products.product` (com normalização semântica)
- `sales_pipeline.sales_agent -> sales_teams.sales_agent`

## Classificação de desvios
- **blocking**: quebra de join com valor preenchido (falha o pipeline)
- **warning**: sobra de dimensão sem uso no fato (não bloqueia)
- **ok**: relação íntegra

## Entrypoint reproduzível

```powershell
python .\scripts\validate_referential_integrity.py
```

Relatório gerado:
- `artifacts/data-validation/referential-integrity-report.json`

## Achados do snapshot atual
- Contas batem para registros com account preenchido.
- Agentes batem no join do pipeline com dimensão.
- Produtos batem após normalização (`GTXPro -> GTX Pro`).
- Agentes na dimensão sem uso no pipeline são classificados como `warning`.

## Testes
- `tests/test_referential_integrity.py`
- Executar:

```powershell
python -m pytest -q tests/test_referential_integrity.py
```

# Normalization rules

## Objetivo
Resolver divergências semânticas conhecidas sem alterar o raw original.

## Mapa versionado
- Arquivo: `config/normalization-map.json`
- Camada de aplicação: `src/normalization/mapper.py`

## Regra obrigatória atual

| Campo | Problema | Regra aplicada | Risco |
|---|---|---|---|
| `sales_pipeline.csv.product` | pipeline usa `GTXPro` e catálogo usa `GTX Pro` | alias semântico `GTXPro -> GTX Pro` | médio |

## Rastreabilidade
Cada normalização retorna:
- `original`
- `canonical`
- `strategy`
- `risk`

Exemplo:
- `original=GTXPro`
- `canonical=GTX Pro`
- `strategy=semantic_alias`

## Garantias
- Não altera CSV original.
- Mantém divergência explícita e auditável.
- Permite joins consistentes com catálogo.

## Evidência funcional
- Testes: `tests/test_normalization.py`
- Execução:

```powershell
python -m pytest -q tests/test_normalization.py
```

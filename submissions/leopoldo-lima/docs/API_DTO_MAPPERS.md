# API DTOs e Mappers

Separacao entre payload wire (JSON) e contrato tipado usado pelo backend/UI.

## Arquivos
- DTOs wire: `src/infrastructure/http/dtos.py`
- Mappers: `src/infrastructure/http/mappers.py`

## Objetivo
- isolar validação/coerção de borda HTTP;
- evitar espalhar parsing em handlers;
- manter mapeamento explícito entre payload legado (`nextBestAction`) e campo normalizado (`next_action`).

## Regras de mapeamento
- `next_action`:
  - usa `next_action` quando presente;
  - fallback para `nextBestAction` quando necessário.
- Tipos numéricos vindos como string são coeridos por validação Pydantic.

## Testes

```powershell
python -m pytest -q tests/test_http_mappers.py
```

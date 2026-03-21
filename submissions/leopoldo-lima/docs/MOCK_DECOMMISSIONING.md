# Mock Decommissioning

Limpeza de acoplamentos residuais de mock para garantir caminho API como primeira classe.

## O que foi desacoplado
- `src/infrastructure/repositories/repository_factory.py`
  - default alterado para `api`
  - imports de `ApiOpportunityRepository` e `MockOpportunityRepository` movidos para import lazy por modo
- `src/infrastructure/repositories/__init__.py`
  - removido import/export de `MockOpportunityRepository` para evitar carregamento implícito
- `.env.example`
  - modo padrão atualizado para `LEAD_SCORER_REPOSITORY_MODE=api`

## O que permanece como mock contratual
- `src/infrastructure/repositories/mock_opportunity_repository.py`
  - permanece como fake explícito para demo/testes
  - só deve ser ativado por `LEAD_SCORER_REPOSITORY_MODE=mock`

## Evidência de validação
- `tests/test_repository_factory.py` valida:
  - default em `api`
  - fallback em `mock` por flag
  - ausência de import do módulo de mock quando modo é `api`

## Riscos residuais
- `data/demo-opportunities.json` continua disponível quando `LEAD_SCORER_DATA_SOURCE_MODE=demo_dataset` (testes e dev controlado); o **padrão** do serving HTTP é `real_dataset` (CSVs oficiais). Ver `docs/RUNTIME_DATA_FLOW.md`.

# View models

View models implementados para payload de produto e explainability:

- `OpportunityListItemView`
- `OpportunityDetailView`
- `ScoreExplanationView`

Implementação: `src/api/view_models.py`.

## Campos essenciais entregues
- `score`
- `priority_band`
- `positive_factors`
- `negative_factors`
- `risk_flags`
- `next_action`
- dados essenciais da oportunidade (`id`, `title`, `seller`, `manager`, `region`, `status`, `amount`)

## Contrato de listagem (`/api/ranking`)
- item de lista já orientado a UI:
  - score consolidado
  - banda de prioridade
  - próxima ação sugerida
- evita expor regra de score para o frontend.

## Contrato de detalhe (`/api/opportunities/{id}`)
- detalhe + bloco `scoreExplanation` pronto para consumo:
  - fatores positivos
  - fatores negativos
  - flags de risco
  - próxima ação

## Testes de serialização
- `tests/test_view_models.py`
- `tests/test_api_contract.py`

Executar:

```powershell
python -m pytest -q tests/test_view_models.py tests/test_api_contract.py
```

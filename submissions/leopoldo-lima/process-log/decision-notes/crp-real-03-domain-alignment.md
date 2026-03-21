# CRP-REAL-03 — Evidência de alinhamento de domínio

## arquivos alterados (grep orientado)

- `src/domain/deal_stage.py` (enum + normalização)
- `src/api/app.py`, `src/api/contracts.py`, `src/api/dataset_loader.py`
- `src/serving/models.py`, `src/serving/opportunity_pipeline.py`
- `src/infrastructure/http/dtos.py`, `filter_params.py`, `api_client.py`
- `src/infrastructure/repositories/api_opportunity_repository.py`, `mock_opportunity_repository.py`, `repository_factory.py`
- `data/demo-opportunities.json`
- `public/index.html`, `public/app.js`, `public/infrastructure/repositories/*.js`, `public/application/contracts/opportunity-repository.js`, `public/infrastructure/mocks/fixtures/*.js`
- `tests/test_deal_stage.py` e testes de contrato/cliente/repos/UI atualizados
- `docs/DOMAIN_ALIGNMENT.md`, `docs/DATA_CONTRACT_FRONTEND.md`, `docs/API_CONTRACT.md`, `docs/API_CONTRACT_UI.md`, `docs/API_CLIENT.md`, `docs/RUNTIME_DATA_FLOW.md`, `docs/SERVING_REAL_DATA.md`, `docs/ADR/0005-frontend-dataset-contract-alignment.md`
- `README.md`, `LOG.md`, `PROCESS_LOG.md`

## Exemplo de payload (listagem)

```json
{
  "id": "OPP-001",
  "deal_stage": "Engaging",
  "title": "Enterprise expansion",
  "score": 65
}
```

## Exemplo de filter-options

```json
{
  "regions": ["Core", "Expansion", "Other"],
  "managers": ["Fernanda", "Marcos"],
  "deal_stages": ["Engaging", "Won"]
}
```

## Screenshot UI

*(Anexar `crp-real-03-ui-stages.png` nesta pasta após validação manual no browser — tabela com coluna “Estágio” e valores oficiais.)*

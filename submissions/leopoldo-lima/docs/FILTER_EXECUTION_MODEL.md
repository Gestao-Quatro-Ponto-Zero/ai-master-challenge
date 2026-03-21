# Filter Execution Model

Modelo de execucao dos filtros da listagem para evitar divergencia entre UI, BFF e API.

## Onde cada filtro roda
- `region`: servidor (`GET /api/opportunities`)
- `manager`: servidor (`GET /api/opportunities`)
- `deal_stage`: servidor (`GET /api/opportunities`)
- `q` (busca por titulo): servidor (`GET /api/opportunities`)
- `sort_by` + `sort_order`: servidor (`GET /api/opportunities`)
- `limit`: servidor (`GET /api/opportunities`)
- `page` e `page_size`: reservados para extensao de paginacao no cliente/BFF (serializados pelo client Python)

## Contrato de query params
Ordem estavel de serializacao no client Python:
1. `region`
2. `manager`
3. `deal_stage`
4. `q`
5. `sort_by`
6. `sort_order`
7. `limit`
8. `page`
9. `page_size`

Implementacao:
- `src/infrastructure/http/filter_params.py`
- `src/infrastructure/http/api_client.py`

## Nota sobre duplo filtro
- a UI pode manter filtros locais de UX, mas o recorte oficial da listagem deve vir do servidor.
- em caso de conflito, prevalece o comportamento da API documentado em `docs/API_CONTRACT_UI.md`.

## UI (cockpit estático)
- **Gestor comercial**: o valor enviado em `manager` na listagem corresponde ao texto canónico devolvido por `GET /api/dashboard/filter-options` (`managers`), escolhido via combobox (lista completa ao focar + filtro incremental). Ver `docs/CBX-08_MANAGER_COMBOBOX.md` e CRP-FIN-01.

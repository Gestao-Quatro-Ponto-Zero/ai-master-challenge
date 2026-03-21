# Repo Map UI

Mapa da trilha de frontend/UI no estado atual do repositório.

## Diretórios principais
- `public/`
  - `index.html` (estrutura da UI)
  - `styles.css` (estilos)
  - `app.js` (integração com API e fluxo principal)
- `legacy/focus-score-ui-api-crps/crps/` (pacote importado; não é código da UI em produção)
  - `CRP-UI-01` ... `CRP-UI-10`
  - `CRP-API-01` ... `CRP-API-10`
- `docs/`
  - documentação de contrato, runbooks e governança aplicável à integração UI/API
- `tests/`
  - `test_ui_smoke.py` (smoke da UI shell)
  - `test_api_contract.py` (contrato que impacta a UI)

## Pontos de acoplamento UI/API
- backend serve a UI em:
  - `GET /` (index)
  - `/ui/*` (assets)
- UI consome:
  - `GET /api/ranking` (compat)
  - `GET /api/opportunities/{id}`
- contrato de referência:
  - `docs/API_CONTRACT_UI.md`

## Estado de governança UI
- baseline UI registrado em `docs/ARCHITECTURE_UI.md`
- modo de runtime mock/api em `docs/RUNTIME_MODES.md`
- runbook de integração em `docs/RUNBOOK_UI_API_INTEGRATION.md`
- rastreabilidade obrigatória em `PROCESS_LOG.md`

# REPO_MAP

Forma geral do repositório (pós CRP-REAL-06): **`docs/REPO_SHAPE.md`**.

## Raiz
- `00-START-HERE.md`: regras rápidas de operação do pacote
- `01-ROADMAP.md`: roadmap resumido por fases
- `README.md`: visão geral do challenge pack
- `LOG.md`: changelog operacional curto
- `PROCESS_LOG.md`: registro detalhado de processo e uso de IA

## Pastas principais
### `crps/executed/` e `indexes/`
CRPs curados por tema (`foundation`, `data`, `ui`, `product-tuning`, `submission`); inventário em `indexes/crp-index.csv`. Lista plana antiga: `archive/superseded/crps-root-flat-pre-SUB-08/`.

### `legacy/`
Material **importado** e metodologia que não faz parte do runtime: pacotes `focus-score-*`, `prompts/` (`.txt` da trilha principal), ferramenta de concat e dump opcional. Ver `legacy/README.md` e `docs/REPO_SHAPE.md`.

### `docs/`
Documentos de governança e submissão.

Arquivos visíveis no snapshot:
- `docs/BASELINE.md`
- `docs/REPO_MAP.md`
- `docs/SUBMISSION_STRATEGY.md`
- `docs/PROCESS_LOG_GUIDE.md`
- `docs/CRP_GOVERNANCE.md`
- `docs/README_SUBMISSION_SKELETON.md`
- `docs/CHALLENGE_CHECKLIST.md`
- `docs/IA_TRACE.md`
- `docs/DATA_CONTRACT.md`
- `docs/SETUP.md`

### `contracts/`
Contrato de dados estruturado do snapshot atual:
- `contracts/repository-data-contract.json`

### `scripts/`
Automação Python disponível:
- `scripts/tasks.py`
- `scripts/validate_data_contract.py`

### `src/domain/`
Tipos de domínio para os datasets:
- `src/domain/models.py`

### `artifacts/process-log/`
Estrutura de evidências para submissão:
- `screenshots/`
- `chat-exports/`
- `test-runs/`
- `ui-captures/`
- `decision-notes/`

### `data/`
Dados CSV do challenge:
- `accounts.csv`
- `products.csv`
- `sales_teams.csv`
- `sales_pipeline.csv`
- `metadata.csv`

## Observação de consistência
Após `CRP-003`, `README.md` e mapa do repositório foram alinhados ao estado real em disco para reduzir divergência documental.

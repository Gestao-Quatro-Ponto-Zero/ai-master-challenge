# ADR 0005 — Alinhamento do contrato frontend ao dataset real

## Contexto
Os CRPs de UI pressupõem, em alguns pontos, tipos frontend específicos (ex.: `DealStage`) típicos de stack TypeScript/Lovable.  
No snapshot atual, a UI shell consome contrato HTTP em JavaScript (`public/app.js`) e não possui `src/domain/models/types.ts`.

## Decisão
Adotar o contrato HTTP como fonte única para a UI neste repositório, com:
- foco em **`deal_stage`** (`Prospecting|Engaging|Won|Lost`) para listagem/filtro na UX (CRP-REAL-03)
- registro do domínio oficial e legado em `docs/DATA_CONTRACT_FRONTEND.md` e `docs/DOMAIN_ALIGNMENT.md`
- proibição de introduzir estados não servidos pela API sem mudança coordenada de contrato

## Consequências
- reduz risco de desalinhamento entre frontend e backend
- mantém compatibilidade com snapshots demo via normalização de wire legado (`status: Open` → `Engaging`)
- prepara evolução futura para TypeScript sem inventar camada de tipos inexistente no snapshot atual

## Evidência
- contrato em `docs/API_CONTRACT_UI.md`
- validação em `tests/test_api_contract.py`
- rastreabilidade em `PROCESS_LOG.md` (CRP-UI-02)

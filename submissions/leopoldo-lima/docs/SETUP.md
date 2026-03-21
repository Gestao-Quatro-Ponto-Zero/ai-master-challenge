# Setup e onboarding

**Pacote de submissão:** execute os comandos a partir de `solution/` (ver [`../solution/README.md`](../solution/README.md)), para manter `data/`, `scripts/` e `artifacts/` alinhados ao código.

Este repositório está em modo **challenge pack/governança**. Os comandos abaixo foram validados no Windows com Python 3.13.

## Pré-requisitos
- Python 3.11+
- `pip` disponível

## 1) Instalar dependências de desenvolvimento (opcional, recomendado)

```powershell
python -m pip install -e .[dev]
```

Se preferir começar sem instalar extras, os comandos básicos de smoke/build continuam disponíveis.

## 2) Comandos principais

```powershell
python .\scripts\tasks.py install
python .\scripts\tasks.py test
python .\scripts\tasks.py lint
python .\scripts\tasks.py format
python .\scripts\tasks.py typecheck
python .\scripts\tasks.py contract
python .\scripts\tasks.py inspect-data
python .\scripts\tasks.py data-dictionary
python .\scripts\tasks.py data-quality
python .\scripts\tasks.py normalization
python .\scripts\tasks.py referential-integrity
python .\scripts\tasks.py features
python .\scripts\tasks.py security
python .\scripts\tasks.py sbom
python .\scripts\tasks.py build
python .\scripts\tasks.py dev
```

## 3) Variáveis de ambiente

`.env.example` não contém segredos e atualmente apenas documenta que não há variáveis obrigatórias para o snapshot atual.

## 4) O que validar antes de avançar para próximos CRPs
- `test` passa confirmando estrutura mínima do pacote.
- `lint` passa sem whitespace final em arquivos Markdown monitorados.
- `typecheck` compila `scripts/tasks.py` sem erros.
- `build` executa o fluxo composto de validação.
- `dev` sobe a API local de referência em `http://127.0.0.1:8787`.
- UI shell disponível em `http://127.0.0.1:8787/` (arquivos estáticos em `public/` servidos pela API).

## 5) Observações
- Este setup garante reprodução do **estado atual** do repositório.
- Por defeito a API serve o **dataset oficial** (`LEAD_SCORER_DATA_SOURCE_MODE=real_dataset`); ver `docs/RUNTIME_DATA_FLOW.md` e o pipeline em `docs/SERVING_REAL_DATA.md`. O JSON `data/demo-opportunities.json` permanece para modo `demo_dataset` e testes.
- Contrato HTTP em `docs/API_CONTRACT.md`.
- Runbook de integração UI/API em `docs/RUNBOOK_UI_API_INTEGRATION.md`.
- Quality gates e segurança em `docs/QUALITY_GATES.md`.
- Demo containerizada em `docs/RUNBOOK.md`.
- Evidência HTTP do fluxo real (JSON em `artifacts/process-log/test-runs/`): `python .\scripts\tasks.py export-real-flow-evidence` (CRP-REAL-09).

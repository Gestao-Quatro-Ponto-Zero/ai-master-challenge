# Quality Gates, segurança e dependências

## Gates adotados
- `lint`: markdown + `ruff check .`
- `format`: `ruff format --check .`
- `typecheck`: `py_compile` + `mypy src scripts tests`
- `test`: `pytest -q`
- `contract` (**crítico**): validação do contrato de dados
- `data-quality` (**crítico**): validação estrutural do `sales_pipeline.csv`
- `normalization` (**crítico**): testes da camada de normalização semântica
- `referential-integrity` (**crítico**): validação de joins fato-dimensões + testes
- `features` (**crítico**): smoke da camada de feature engineering
- `ui-quality` (**crítico para trilha UI**): validação de arquitetura UI + smoke frontend
- `security`: `pip-audit`
- `sbom`: geração de SBOM CycloneDX em `artifacts/security/sbom.json`

## Comandos de execução

```powershell
python .\scripts\tasks.py lint
python .\scripts\tasks.py format
python .\scripts\tasks.py typecheck
python .\scripts\tasks.py test
python .\scripts\tasks.py contract
python .\scripts\tasks.py data-quality
python .\scripts\tasks.py normalization
python .\scripts\tasks.py referential-integrity
python .\scripts\tasks.py features
python .\scripts\tasks.py ui-quality
python .\scripts\tasks.py ui-ci-check
python .\scripts\tasks.py security
python .\scripts\tasks.py sbom
python .\scripts\tasks.py build
```

## Dependências e segurança
- Ferramenta de scan: `pip-audit`
- SBOM: `cyclonedx-bom` (`cyclonedx_py`)
- Dependências de desenvolvimento versionadas em `pyproject.toml`.

## Hooks locais
- Configuração em `.pre-commit-config.yaml`
- Instalação:

```powershell
python -m pre_commit install
python -m pre_commit run --all-files
```

## Política operacional
- Gate vermelho bloqueia promoção do CRP.
- Exceções precisam de justificativa explícita no `PROCESS_LOG.md`.

## CI em Pull Request
- Workflow: `.github/workflows/ci-pr.yml`
- Workflow frontend: `.github/workflows/frontend-ci.yml`
- Jobs:
  - `Quality Gates`: lint, format, typecheck, testes, contrato, qualidade de dados, normalização, integridade referencial e smoke de features
  - `Security and SBOM`: `pip-audit` + geração/upload do SBOM
  - `UI Quality Gates`: `ui-tests` + `ui-quality`
- Estratégia:
  - cache de dependências com `actions/setup-python`
  - `fail fast` por job (qualidade precisa passar antes de segurança)
  - nomes de etapas explícitos para indicar claramente qual proteção falhou

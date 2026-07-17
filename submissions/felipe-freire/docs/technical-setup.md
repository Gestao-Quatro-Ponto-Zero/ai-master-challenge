# Setup técnico

## Requisitos

- Python 3.10–3.13;
- PowerShell 5.1+ para o ETL bootstrap atual;
- Git.

O runtime encontrado nesta máquina é Python 3.10.9 em `C:\Users\Felipe Freire\AppData\Local\Programs\Python\Python310\python.exe`. O projeto não deve depender desse caminho absoluto; use um ambiente virtual local.

## Instalação

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Se `python` não estiver no PATH, use o caminho do runtime apenas para criar `.venv`; todos os comandos seguintes devem usar `.venv`.

## Comandos canônicos

```powershell
# Validar ambiente
.\.venv\Scripts\python.exe scripts\check_environment.py

# Reconstruir dataset analítico sem mudar a política do sistema
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\src\etl\build_dataset.ps1

# Testes de dados
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tests\data\test_build_dataset.ps1

# Testes Python
.\.venv\Scripts\python.exe -m pytest

# Qualidade
.\.venv\Scripts\python.exe -m ruff check src tests scripts
.\.venv\Scripts\python.exe -m ruff format --check src tests scripts
```

## Contratos e falhas

Contratos vivem em `docs/contracts/`. Qualquer quebra deve falhar antes da análise. A ausência de Python ou dependência deixa `TECH-FOUNDATION` em `FAIL/BLOCKED`, nunca em `PASS`. Respostas interrompidas são `INCOMPLETE` até conferência de arquivos e testes.

## Troubleshooting

- `running scripts is disabled`: use somente o comando com `-ExecutionPolicy Bypass -File`; não altere a política global.
- decimal com vírgula: o ETL serializa taxas explicitamente com cultura invariável; se reaparecer, o teste deve falhar.
- `python` abre o gerenciador: localize um runtime real ou instale Python e crie `.venv`.
- dataset não encontrado: execute a partir da raiz `submissions/felipe-freire`.

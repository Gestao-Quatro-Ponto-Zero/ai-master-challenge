$ErrorActionPreference = "Stop"

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Virtual environment not found. See docs/technical-setup.md"
}

& $python scripts\check_environment.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tests\data\test_build_dataset.ps1
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $python -m pytest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $python -m ruff check src tests scripts
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $python -m ruff format --check src tests scripts
exit $LASTEXITCODE

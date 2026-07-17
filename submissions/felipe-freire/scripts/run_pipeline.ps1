$ErrorActionPreference = "Stop"
$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) { throw "Missing .venv; see docs/technical-setup.md" }

powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\src\etl\build_dataset.ps1
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $python src\analysis\run_eda.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $python src\analysis\run_inference.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
exit $LASTEXITCODE

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$python = Join-Path $PSScriptRoot 'backend\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Create backend\.venv and install backend\requirements.txt first.' }
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'frontend\dist\index.html'))) { throw 'Run npm.cmd --prefix frontend run build first.' }
Write-Host 'ArecaLens: open http://127.0.0.1:8000 after Application startup complete.' -ForegroundColor Green
& $python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

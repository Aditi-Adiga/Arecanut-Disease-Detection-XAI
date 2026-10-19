@echo off
cd /d "%~dp0"
if not exist "frontend\dist\index.html" (
  echo Build the interface first: npm.cmd --prefix frontend run build
  pause
  exit /b 1
)
echo Open http://127.0.0.1:8000 after Application startup complete.
"backend\.venv\Scripts\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
pause

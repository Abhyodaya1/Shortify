Write-Host "Starting Motion GVA Backend API Server on http://localhost:8000..." -ForegroundColor Cyan
& ".\backend\.venv\Scripts\uvicorn.exe" backend.app.main:app --host 0.0.0.0 --port 8000 --reload


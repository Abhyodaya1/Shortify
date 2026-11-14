@echo off
echo Starting Motion GVA Backend API Server...
cd ..
backend\.venv\Scripts\uvicorn.exe backend.app.main:app --host 0.0.0.0 --port 8000 --reload


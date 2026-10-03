@echo off
cd /d "%~dp0\.."
echo Starting GlaucoMap Backend on http://localhost:8000 ...
.\venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

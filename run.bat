@echo off
title GlaucoMap Clinical Workstation Launcher
cd /d "%~dp0"
echo =======================================================
echo GLAUCOMAP CLINICAL DECISION-SUPPORT WORKSTATION
echo =======================================================
echo Starting Backend (FastAPI on port 8000)...
start "GlaucoMap Backend" cmd /k ".\venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000"

echo Starting Frontend (Vite on port 5173)...
start "GlaucoMap Frontend" cmd /k "cd frontend && npm run dev"

echo Waiting for services to initialize...
timeout /t 3 /nobreak >nul

echo Opening Clinical Workstation in default browser...
start http://localhost:5173

echo =======================================================
echo Services are running:
echo - Clinical Workstation: http://localhost:5173
echo - API Documentation:   http://127.0.0.1:8000/docs
echo =======================================================

@echo off
cd /d "%~dp0\.."
echo Running GlaucoMap Backend Tests with pytest ...
.\venv\Scripts\pytest.exe -v

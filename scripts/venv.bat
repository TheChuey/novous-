@echo off
REM Virtualenv bootstrap for Novous Agent Factory (Windows)
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install fastapi uvicorn ollama
echo.
echo Virtualenv ready. Run: python server.py

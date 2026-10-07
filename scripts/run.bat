@echo off
rem Start the web app from the repository-root virtual environment.

cd /d "%~dp0.."

set "PYTHON="
if exist ".venv\Scripts\python.exe" set "PYTHON=.venv\Scripts\python.exe"
if not defined PYTHON set "PYTHON=python"

echo Starting web app at http://127.0.0.1:8000
echo To stop: press Ctrl+C
echo.

%PYTHON% server.py

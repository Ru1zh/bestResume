@echo off
setlocal
cd /d "%~dp0"

set HOST=127.0.0.1
set PORT=8020

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+ first.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo [OK] Using Python %PYVER%

if not exist ".venv" (
    echo [..] Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo [..] Installing dependencies...
python -m pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo [OK] Starting bestResume at http://%HOST%:%PORT% ...
python app.py

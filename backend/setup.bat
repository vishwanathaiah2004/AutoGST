@echo off
echo ============================================
echo   AutoGST Pro - Windows Setup Script
echo ============================================
echo.

cd /d "%~dp0"

REM Check if we're in the backend folder
if not exist "main.py" (
    echo ERROR: Run this script from inside the backend\ folder
    echo Current folder: %CD%
    pause
    exit /b 1
)

echo [1/5] Checking Python...
python --version 2>NUL
if errorlevel 1 (
    echo ERROR: Python not found. Install from https://python.org
    echo Make sure to check "Add Python to PATH" during install
    pause
    exit /b 1
)

echo.
echo [2/5] Creating virtual environment...
if exist "venv" (
    echo venv already exists, skipping...
) else (
    python -m venv venv
)

echo.
echo [3/5] Activating venv and installing packages...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt

echo.
echo [4/5] Checking .env file...
if not exist ".env" (
    copy .env.example .env
    echo .env file created from .env.example
    echo.
    echo =============================================
    echo   IMPORTANT: Edit .env before continuing!
    echo   Open backend\.env and set:
    echo   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/autogst_pro
    echo =============================================
    notepad .env
    echo.
    echo Press any key after saving .env...
    pause
) else (
    echo .env already exists
)

echo.
echo [5/5] Running database seed...
python utils/seed.py

echo.
echo ============================================
echo   Setup Complete!
echo   Now run: start_backend.bat
echo ============================================
pause

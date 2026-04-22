@echo off
cd /d "%~dp0"
echo Starting AutoGST Pro Backend...
echo.
call venv\Scripts\activate.bat
echo Backend running at: http://localhost:8000
echo API Docs at:        http://localhost:8000/docs
echo Press Ctrl+C to stop
echo.
python main.py
pause

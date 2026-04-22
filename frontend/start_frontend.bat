@echo off
cd /d "%~dp0"
echo Starting AutoGST Pro Frontend...
echo.
echo App will open at: http://localhost:3000
echo Login: demo@autogst.pro / Demo@1234
echo Press Ctrl+C to stop
echo.
npm run dev
pause

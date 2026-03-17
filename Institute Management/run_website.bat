@echo off
echo Starting Balaji Computer Institute System...
echo Please wait while the server starts...

:: Start the Python backend in a new window
start "Institute Server" python backend/app.py

:: Wait for a few seconds to let the server initialize
timeout /t 3 >nul

:: Open the browser
start http://127.0.0.1:5000/

echo.
echo System Running! Do not close the "Institute Server" window.
echo You can minimize it.
pause

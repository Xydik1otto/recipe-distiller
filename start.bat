@echo off
rem Recipe Distiller launcher: double-click me.
cd /d "%~dp0"
echo Recipe Distiller: http://localhost:8000  (close this window to stop)
start "" http://localhost:8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
echo.
echo Server stopped. Press any key to close.
pause >nul

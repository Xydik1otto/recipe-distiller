@echo off
rem One-time setup for Recipe Distiller on Windows: installs dependencies.
cd /d "%~dp0"
echo Installing Recipe Distiller dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo FAILED. Is Python installed and on PATH? See INSTALL.md step 1.
  pause
  exit /b 1
)
echo.
echo Done! Now run start.bat
pause

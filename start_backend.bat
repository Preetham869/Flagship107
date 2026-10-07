@echo off
REM Flagship 107 - Backend Startup Script (Windows)
REM Ensures processing module is available by setting PYTHONPATH

echo Starting Flagship 107 Backend...
echo.

REM Get the directory where this script is located (project root)
set "PROJECT_ROOT=%~dp0"

REM Add project root to PYTHONPATH so 'processing' module can be imported
set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"

echo Project Root: %PROJECT_ROOT%
echo PYTHONPATH: %PYTHONPATH%
echo.

REM Change to backend directory and start uvicorn
cd /d "%PROJECT_ROOT%backend"
python -m uvicorn app.main:app --reload --host localhost --port 8000

pause

@echo off
setlocal
cd /d "%~dp0"
set "APP_PYTHON=.venv\Scripts\python.exe"
if exist .venv312\Scripts\python.exe set "APP_PYTHON=.venv312\Scripts\python.exe"
if not exist "%APP_PYTHON%" (
  echo Run launch.bat once to set up Python, then run this file again.
  pause
  exit /b 1
)
"%APP_PYTHON%" configure_api.py
pause

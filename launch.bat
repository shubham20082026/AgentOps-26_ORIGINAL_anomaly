@echo off
setlocal
cd /d "%~dp0"
set "APP_PYTHON=.venv\Scripts\python.exe"
if exist .venv312\Scripts\python.exe set "APP_PYTHON=.venv312\Scripts\python.exe"
if exist "%APP_PYTHON%" goto check_python
echo First run: creating a Python environment...
py -3.12 -m venv .venv >setup.log 2>&1
if not errorlevel 1 goto check_python
py -3.11 -m venv .venv >>setup.log 2>&1
if errorlevel 1 goto fail
:check_python
"%APP_PYTHON%" -c "import sys; print('Using Python',sys.version.split()[0])" >setup.log 2>&1
if errorlevel 1 goto fail
type setup.log
"%APP_PYTHON%" -c "import streamlit, pandas, pyarrow" >>setup.log 2>&1
if not errorlevel 1 goto run_app
echo Installing dependencies. Please wait...
"%APP_PYTHON%" -m pip install -r requirements.txt >>setup.log 2>&1
if errorlevel 1 goto fail
:run_app
echo Starting ReRoute. Keep this window open.
"%APP_PYTHON%" -m streamlit run app.py --server.fileWatcherType poll
if errorlevel 1 goto fail
goto :eof
:fail
echo.
echo ReRoute could not start. The actual error is below:
type setup.log
echo.
echo Full details are saved in setup.log in this folder.
echo This app was tested with Python 3.12. Python 3.11 is also supported.
pause

@echo off
setlocal

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

echo Setting PYTHONPATH...
set PYTHONPATH=%PYTHONPATH%;D:/home/vnpy-test-v2

echo Starting application...
python ui/main.py
if errorlevel 1 (
    echo Application exited with error code %errorlevel%
    pause
    exit /b %errorlevel%
)

echo Application closed successfully
pause 
@echo off
REM Trading System Launcher v2.0
setlocal enabledelayedexpansion

title Trading System Launcher v2.0
echo Starting Trading System... 
echo.

REM Check Python environment
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    echo Please install Python 3.7+ and add to PATH
    pause
    exit /b 1
)

REM Set environment variables
set PYTHONPATH=%CD%
set PYTHONIOENCODING=utf-8

REM Create directories
if not exist "data" mkdir data
if not exist "logs" mkdir logs

REM Check dependencies (optional)
echo Checking dependencies...
python -c "import PyQt5" >nul 2>&1 || echo PyQt5 check failed (optional)
python -c "import vnpy" >nul 2>&1 || echo vnpy check failed (optional)

REM Simple menu without Chinese characters
echo Choose interface:
echo   1. New UI (vn.py style)
echo   2. Legacy UI (compatible)
echo   3. Exit

set /p choice=Enter choice (1-3): 

if "%choice%"=="1" goto new_ui
if "%choice%"=="2" goto legacy_ui
if "%choice%"=="3" goto exit

:new_ui
echo.
echo Starting new trading system...
python ui/new_main_window.py
goto end

:legacy_ui
echo.
echo Starting legacy interface...
python ui/main.py
goto end

:exit
echo Exiting...
exit /b 0

:end
pause
@echo off
REM Mock Trading System Launcher
setlocal enabledelayedexpansion

title Mock Trading System Launcher
echo Starting Mock Trading System...
echo.

REM Check Python environment
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    echo Please install Python 3.7+ and add to PATH
    pause
    exit /b 1
)

REM Set environment variables for mock mode
set PYTHONPATH=%CD%
set PYTHONIOENCODING=utf-8
set USE_MOCK_DATA=true

echo 🚀 Mock Trading System Starting...
echo.
echo Configuration:
echo   - Mock Data: Enabled
echo   - Broker: MockCTP
echo   - Contracts: 10 predefined contracts
echo   - Initial Balance: ¥1,000,000
echo.

echo Choose interface:
echo   1. New UI (with mock data)
echo   2. Legacy UI (with mock data)
echo   3. Exit

set /p choice=Enter choice (1-3): 

if "%choice%"=="1" goto new_ui
if "%choice%"=="2" goto legacy_ui
if "%choice%"=="3" goto exit

:new_ui
echo.
echo Starting new mock trading system...
python ui/new_main_window.py
goto end

:legacy_ui
echo.
echo Starting legacy mock interface...
python ui/main.py
goto end

:exit
echo Exiting...
exit /b 0

:end
echo.
echo Mock system stopped.
pause
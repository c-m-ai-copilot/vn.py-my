@echo off
chcp 65001

:: 设置Python环境
set PATH=D:\veighna_studio;D:\veighna_studio\Scripts;%PATH%
set PYTHONPATH=%~dp0;%PYTHONPATH%

:: 设置vnpy环境变量
set VNPY_TESTING=1

:: 运行市场测试
echo 运行市场测试...
python tests/integration_test_market.py

pause
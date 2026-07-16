@echo off
title ERP Launcher
echo Starting El-Joumla ERP...
cd /d "%~dp0"
if not exist .venv (
    echo Error: Virtual environment .venv not found!
    pause
    exit /b
)
call .venv\Scripts\activate.bat
python main.py
if %errorlevel% neq 0 (
    echo Error: Application exited with error code %errorlevel%
    pause
)

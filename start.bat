@echo off
setlocal enabledelayedexpansion
title FinGuard Platform Runner

echo ========================================================
echo   Starting FinGuard - AI Deepfake ^& Scam Detector
echo ========================================================
echo.

:: 1. Detect Python executable
set "PYTHON_CMD=python"
if exist "%~dp0.venv_gpu\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0.venv_gpu\Scripts\python.exe"
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0.venv\Scripts\python.exe"
)

echo [1/5] Checking Ollama Service...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo Starting local Ollama server in background...
    start "Ollama Server" /B ollama serve
    ping -n 4 127.0.0.1 >nul
) else (
    echo Ollama service is already running.
)

echo.
echo [2/5] Starting FinGuard Backend API on http://localhost:8000...
start "FinGuard Backend (Port 8000)" /D "%~dp0" "%PYTHON_CMD%" -u app.py

echo.
echo [3/5] Starting FinGuard Frontend Dashboard on http://localhost:3000...
start "FinGuard Frontend (Port 3000)" /D "%~dp0" "%PYTHON_CMD%" -u run_frontend.py

echo.
echo [4/5] Starting Permanent Public Ngrok Tunnel...
if exist "%~dp0start_ngrok.bat" (
    start "FinGuard Ngrok Tunnel" /D "%~dp0" start_ngrok.bat
)

echo.
echo [5/5] Opening Web Dashboard in default browser...
ping -n 4 127.0.0.1 >nul
start http://localhost:3000

echo.
echo ========================================================
echo   FinGuard is up and running!
echo   - Local Web UI: http://localhost:3000
echo   - Backend API:  http://localhost:8000
echo   - Public URL:   https://nutcase-exodus-precinct.ngrok-free.dev
echo   - API Docs:     http://localhost:8000/docs
echo   Run stop.bat to terminate all servers and tunnels.
echo ========================================================

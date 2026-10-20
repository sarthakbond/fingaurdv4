@echo off
echo Stopping FinGuard services...

:: 1. Terminate listeners on ports 8000 and 3000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /f /pid %%a >nul 2>&1
)

:: 2. Terminate tunnel processes if running
taskkill /f /im ngrok.exe >nul 2>&1
taskkill /f /im cloudflared.exe >nul 2>&1

echo FinGuard backend (port 8000), frontend (port 3000), and public tunnels stopped.

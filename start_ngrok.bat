@echo off
title FinGuard Permanent Ngrok Tunnel
echo ========================================================
echo   FinGuard - Permanent Public Tunnel
echo ========================================================
echo.
echo Connecting to permanent public endpoint:
echo https://nutcase-exodus-precinct.ngrok-free.dev
echo.
echo Forwarding traffic to local FinGuard on http://localhost:8000...
echo ========================================================
echo.

set "NGROK_CMD=ngrok"
if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe" (
    set "NGROK_CMD=%LOCALAPPDATA%\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe"
)

"%NGROK_CMD%" http 8000 --url=nutcase-exodus-precinct.ngrok-free.dev
pause

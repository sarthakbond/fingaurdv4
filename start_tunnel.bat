@echo off
title FinGuard Cloudflare Tunnel
echo ========================================================
echo   FinGuard - Cloudflare Public Tunnel
echo ========================================================
echo.
echo Exposing FinGuard forensic platform to the public internet...
echo Local service: http://localhost:8000 (Web Dashboard & API)
echo.
echo Look for the 'trycloudflare.com' link below:
echo ========================================================
echo.
"C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://localhost:8000
pause

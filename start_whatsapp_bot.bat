@echo off
title FinGuard WhatsApp Forensic Shield
color 0A

echo =============================================================
echo   FinGuard WhatsApp Direct Shield Bridge
echo   Connects your mobile WhatsApp directly to local forensic engine
echo =============================================================
echo.
cd /d %~dp0whatsapp_bridge
node bridge.js
pause

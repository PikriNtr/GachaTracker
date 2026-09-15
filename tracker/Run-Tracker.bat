@echo off
chcp 65001 >nul
echo ============================================
echo   WuWa Local Tracker
echo   Fetching gacha records...
echo ============================================
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0WuWa-LocalTracker.ps1"
pause

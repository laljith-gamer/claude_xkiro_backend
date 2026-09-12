@echo off
title xKiro Proxy Setup
echo ============================================
echo   xKiro to Anthropic Proxy - Setup Script
echo ============================================
echo.

echo [1/2] Installing Python dependencies...
echo.
python -m pip install fastapi uvicorn httpx python-dotenv -q
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install dependencies.
    echo         Make sure Python is installed and in PATH.
    pause
    exit /b 1
)
echo [OK] Dependencies installed!
echo.

echo [2/2] Checking configuration...

:: Check if .env has been configured
findstr /C:"xk-paste-your-xkiro-api-key-here" "%~dp0.env" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo.
    echo [ACTION REQUIRED] You need to set your xKiro API key!
    echo.
    echo   1. Sign up for FREE at: https://xkiro.com
    echo   2. Get your API key from the dashboard
    echo   3. Open: %~dp0.env
    echo   4. Replace "xk-paste-your-xkiro-api-key-here" with your actual key
    echo.
) else (
    echo [OK] API key appears to be configured.
)

echo ============================================
echo   Setup Complete!
echo ============================================
echo.
echo Next steps:
echo   1. Make sure your API key is set in .env
echo   2. Run start-proxy.bat to launch the converter
echo   3. Configure Claude Desktop (see README.md)
echo.
pause

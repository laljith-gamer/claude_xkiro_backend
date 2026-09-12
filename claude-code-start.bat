@echo off
title Claude Code via xKiro Proxy
echo ============================================
echo   Claude Code with xKiro Free Models
echo ============================================
echo.

:: Load API key from .env
for /f "usebackq tokens=1,* delims==" %%a in ("%~dp0.env") do (
    if "%%a"=="UPSTREAM_API_KEY" set "API_KEY=%%b"
    if "%%a"=="LISTEN_PORT" set "PORT=%%b"
    if "%%a"=="LISTEN_HOST" set "HOST=%%b"
)

if "%PORT%"=="" set "PORT=3000"
if "%HOST%"=="" set "HOST=127.0.0.1"

:: Check proxy is running
curl -s "http://%HOST%:%PORT%/healthz" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Proxy doesn't appear to be running!
    echo          Start it first with: start-proxy.bat
    echo.
    echo Trying to launch Claude Code anyway...
    echo.
)

:: Set environment for Claude Code
set "ANTHROPIC_BASE_URL=http://%HOST%:%PORT%"
set "ANTHROPIC_API_KEY=%API_KEY%"

echo Using proxy at: %ANTHROPIC_BASE_URL%
echo.

:: Launch Claude Code
claude %*

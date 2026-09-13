@echo off
setlocal enabledelayedexpansion
title xKiro Model Switcher
echo ============================================
echo   xKiro Free Model Switcher
echo ============================================
echo.
echo Note: Most DeepSeek, Qwen, and MiniMax models are no longer free.
echo The following models are currently working on the free tier:
echo.
echo Select a free model to use:
echo.
echo --- Mistral ---
echo   1. mistralai/mistral-large-2512     [256K ctx, Best Overall]
echo   2. mistralai/codestral-2508         [256K ctx, Best Coding]
echo   3. mistralai/mistral-small-2603     [256K ctx, Fast]
echo   4. mistralai/mistral-medium-3.5     [256K ctx, Vision]
echo   5. mistralai/devstral-medium        [256K ctx, Coding]
echo   6. mistralai/ministral-14b          [256K ctx, Lightweight]
echo   7. mistralai/ministral-8b           [256K ctx, Lightweight]
echo   8. mistralai/ministral-3b           [128K ctx, Very Lightweight]
echo.
echo --- SenseNova ---
echo   9. sensenova/sensenova-6.7-flash-lite [262K ctx, Fast]
echo.
echo --- Default / Auto ---
echo  10. Clear UPSTREAM_MODEL (Use proxy.py auto-mapping)
echo.

set /p "choice=Enter number (1-10): "

if "%choice%"=="1" set "MODEL=mistralai/mistral-large-2512"
if "%choice%"=="2" set "MODEL=mistralai/codestral-2508"
if "%choice%"=="3" set "MODEL=mistralai/mistral-small-2603"
if "%choice%"=="4" set "MODEL=mistralai/mistral-medium-3.5"
if "%choice%"=="5" set "MODEL=mistralai/devstral-medium"
if "%choice%"=="6" set "MODEL=mistralai/ministral-14b"
if "%choice%"=="7" set "MODEL=mistralai/ministral-8b"
if "%choice%"=="8" set "MODEL=mistralai/ministral-3b"
if "%choice%"=="9" set "MODEL=sensenova/sensenova-6.7-flash-lite"
if "%choice%"=="10" set "MODEL="

if "%choice%"=="" (
    echo Invalid choice.
    pause
    exit /b 1
)

if "%choice%"=="10" (
    echo.
    echo Clearing UPSTREAM_MODEL to use proxy mapping...
) else (
    echo.
    echo Switching model to: %MODEL%
)

echo.

:: Update the .env file
powershell -Command "(Get-Content '%~dp0.env') -replace 'UPSTREAM_MODEL=.*', 'UPSTREAM_MODEL=%MODEL%' | Set-Content '%~dp0.env'"

echo [OK] Model updated in .env
echo.
echo NOTE: Restart the proxy (stop-proxy.bat then start-proxy.bat) for changes to take effect.
echo.
pause

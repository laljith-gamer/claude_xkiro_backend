@echo off
setlocal enabledelayedexpansion
title xKiro Model Switcher
echo ============================================
echo   xKiro Free Model Switcher
echo ============================================
echo.
echo Select a free model to use:
echo.
echo --- DeepSeek (Best Overall) ---
echo   1. deepseek/deepseek-v4-pro         [1M ctx, reasoning]
echo   2. deepseek/deepseek-v4-flash       [1M ctx, fast]
echo   3. deepseek/deepseek-v3.2           [131K ctx]
echo   4. deepseek/deepseek-chat-v3.1      [164K ctx]
echo.
echo --- Qwen (Best Vision + Reasoning) ---
echo   5. qwen/qwen3.8-max:free            [1M ctx, vision]
echo   6. qwen/qwen3.7-max:free            [1M ctx]
echo   7. qwen/qwen3.7-plus:free           [1M ctx, vision]
echo   8. qwen/qwen3-coder-plus:free       [1M ctx, coding]
echo   9. qwen/qwen3.5-flash:free          [1M ctx, vision]
echo.
echo --- Mistral (Coding Specialists) ---
echo  10. mistralai/mistral-medium-3.5     [256K ctx, vision]
echo  11. mistralai/codestral-2508         [256K ctx, coding]
echo  12. mistralai/devstral-medium        [256K ctx, coding]
echo  13. mistralai/mistral-large-2512     [256K ctx, vision]
echo.
echo --- MiniMax ---
echo  14. minimax/minimax-m3:free          [1M ctx, vision]
echo  15. minimax/minimax-m2.7:free        [205K ctx]
echo.
echo --- OpenAI ---
echo  16. openai/gpt-5.3-codex-spark      [128K ctx, coding]
echo.

set /p "choice=Enter number (1-16): "

if "%choice%"=="1" set "MODEL=deepseek/deepseek-v4-pro"
if "%choice%"=="2" set "MODEL=deepseek/deepseek-v4-flash"
if "%choice%"=="3" set "MODEL=deepseek/deepseek-v3.2"
if "%choice%"=="4" set "MODEL=deepseek/deepseek-chat-v3.1"
if "%choice%"=="5" set "MODEL=qwen/qwen3.8-max:free"
if "%choice%"=="6" set "MODEL=qwen/qwen3.7-max:free"
if "%choice%"=="7" set "MODEL=qwen/qwen3.7-plus:free"
if "%choice%"=="8" set "MODEL=qwen/qwen3-coder-plus:free"
if "%choice%"=="9" set "MODEL=qwen/qwen3.5-flash:free"
if "%choice%"=="10" set "MODEL=mistralai/mistral-medium-3.5"
if "%choice%"=="11" set "MODEL=mistralai/codestral-2508"
if "%choice%"=="12" set "MODEL=mistralai/devstral-medium"
if "%choice%"=="13" set "MODEL=mistralai/mistral-large-2512"
if "%choice%"=="14" set "MODEL=minimax/minimax-m3:free"
if "%choice%"=="15" set "MODEL=minimax/minimax-m2.7:free"
if "%choice%"=="16" set "MODEL=openai/gpt-5.3-codex-spark"

if "%MODEL%"=="" (
    echo Invalid choice.
    pause
    exit /b 1
)

echo.
echo Switching model to: %MODEL%
echo.

:: Update the .env file
powershell -Command "(Get-Content '%~dp0.env') -replace 'UPSTREAM_MODEL=.*', 'UPSTREAM_MODEL=%MODEL%' | Set-Content '%~dp0.env'"

echo [OK] Model updated in .env
echo.
echo NOTE: Restart the proxy (stop-proxy.bat then start-proxy.bat) for changes to take effect.
echo.
pause

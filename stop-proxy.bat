@echo off
echo Stopping xKiro Anthropic Proxy...
echo.

:: Find and kill the Python proxy process on port 3000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000" ^| findstr "LISTENING"') do (
    echo Killing process PID: %%a
    taskkill /F /PID %%a 2>nul
)

echo [OK] Proxy stopped.
echo.
pause

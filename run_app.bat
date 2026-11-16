@echo off
title Kerala & Hanoi Live Gold Tracker
cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel%==0 (
    py -3 launcher.py
    goto :done
)

where python >nul 2>&1
if %errorlevel%==0 (
    python launcher.py
    goto :done
)

echo.
echo [ERROR] Python 3 was not found on this PC.
echo Please install Python 3.10+ from https://www.python.org/downloads/
echo (Make sure to check "Add Python to PATH" during installation.)
echo.
pause
exit /b 1

:done
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application exited with code %errorlevel%.
    pause
)

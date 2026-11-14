@echo off
title LEO  -  Vietnam / India Gold Rate Comparison
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py leo_desktop.py
) else (
    python leo_desktop.py
)

if errorlevel 1 (
    echo.
    echo ------------------------------------------------------------
    echo  LEO could not start.
    echo  Make sure Python 3.9+ is installed:  https://python.org
    echo  Windows: install it and tick "Add python.exe to PATH".
    echo  Then run:  python leo_desktop.py
    echo ------------------------------------------------------------
    pause
)

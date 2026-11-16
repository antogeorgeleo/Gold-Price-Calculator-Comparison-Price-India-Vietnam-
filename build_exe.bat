@echo off
title Building Standalone EXE - Kerala & Hanoi Gold Tracker
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
)

.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller
.venv\Scripts\pyinstaller.exe --noconfirm --onefile --windowed --name "KeralaHanoiGoldTracker" --add-data "fonts;fonts" app.py

echo.
echo Build complete! Standalone EXE is at:
echo   %~dp0dist\KeralaHanoiGoldTracker.exe
echo.
pause

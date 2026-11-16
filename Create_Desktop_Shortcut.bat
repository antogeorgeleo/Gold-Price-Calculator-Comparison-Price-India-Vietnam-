@echo off
cd /d "%~dp0"
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Kerala Hanoi Gold Tracker.lnk'); $s.TargetPath = '%~dp0run_app.bat'; $s.WorkingDirectory = '%~dp0'; $s.WindowStyle = 7; $s.Save()"
echo.
echo Desktop shortcut "Kerala Hanoi Gold Tracker" created!
pause

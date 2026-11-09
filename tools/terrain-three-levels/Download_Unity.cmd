@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Download_Release.ps1" -Mode Unity -Extract
if errorlevel 1 echo Download incomplete. Run this command again to retry.
pause

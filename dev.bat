@echo off
REM Raccourci Windows (cmd.exe) vers dev.ps1 :  dev.bat test
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0dev.ps1" %*

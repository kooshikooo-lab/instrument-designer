@echo off
title Save Session Log
set LOGDIR=%USERPROFILE%\Desktop\WDesigner-session-logs
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set TIMESTAMP=%DATE:/=%%TIME::=%
set TIMESTAMP=%TIMESTAMP: =0%
set LOGFILE=%LOGDIR%\session_%TIMESTAMP%.txt

echo ======================================== > "%LOGFILE%"
echo Instrument Designer Session Log >> "%LOGFILE%"
echo Date: %DATE% %TIME% >> "%LOGFILE%"
echo ======================================== >> "%LOGFILE%"
echo. >> "%LOGFILE%"

echo -- Project Files -- >> "%LOGFILE%"
dir /s /b "%~dp0*.py" "%~dp0*.yaml" "%~dp0*.toml" "%~dp0*.json" 2>nul >> "%LOGFILE%"
echo. >> "%LOGFILE%"

echo -- Designs in TEMP -- >> "%LOGFILE%"
dir /b "%TEMP%\woodwind_*" 2>nul >> "%LOGFILE%" || echo (none) >> "%LOGFILE%"
echo. >> "%LOGFILE%"

echo -- OpenCode Log (last 50 lines) -- >> "%LOGFILE%"
if exist "%USERPROFILE%\.local\share\opencode\log\opencode.log" (
    powershell -Command "Get-Content '%USERPROFILE%\.local\share\opencode\log\opencode.log' -Tail 50" >> "%LOGFILE%"
) else (
    echo (no log found) >> "%LOGFILE%"
)

echo ======================================== >> "%LOGFILE%"
echo End of session log >> "%LOGFILE%"
echo ======================================== >> "%LOGFILE%"

echo Session log saved to: %LOGFILE%
echo You can open this file in Notepad or any text editor.
pause

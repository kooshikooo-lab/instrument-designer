@echo off
title Instrument Designer
cd /d "%~dp0"
echo Starting Instrument Designer...
python -m woodwind_designer
if errorlevel 1 (
    echo.
    echo Error: Failed to launch. Make sure dependencies are installed.
    echo Run: pip install -r requirements.txt
    pause
)

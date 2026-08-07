@echo off
cd /d "%~dp0.."
python scripts\start_gemma.py %*
pause

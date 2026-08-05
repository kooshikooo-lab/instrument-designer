@echo off
cd /d "%~dp0.."
python scripts\view_instrument.py %*
pause

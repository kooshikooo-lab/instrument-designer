@echo off
cd /d "%~dp0.."
python scripts\view_browser.py %*
REM No pause: avoid pop-ups.

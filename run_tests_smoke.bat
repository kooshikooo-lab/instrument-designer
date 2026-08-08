@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_tests_smoke.ps1"
pause

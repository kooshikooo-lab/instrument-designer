@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_tests_integration.ps1"
pause

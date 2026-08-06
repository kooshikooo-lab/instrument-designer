@echo off
if "%~1"=="" (
  wscript //nologo "%~dp0_run_hidden.vbs" view_browser.py koncovka_C
) else (
  wscript //nologo "%~dp0_run_hidden.vbs" view_browser.py %*
)

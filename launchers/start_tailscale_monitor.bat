@echo off
REM Start the Tailscale peer monitor (server + heartbeat) on this machine.
REM The script reads scripts/.tailscale_config.json to know the peer IP.
REM
REM Usage: double-click this file, or run from Command Prompt/PowerShell.
REM Check status: python scripts\tailscale_monitor.py status

setlocal

REM Infer machine name from hostname if not already set.
if not defined MACHINE_NAME (
    for /f "tokens=*" %%a in ('hostname') do set "_HOST=%%a"
    echo !_HOST! | findstr /I "desktop" >nul && set "MACHINE_NAME=desktop"
    echo !_HOST! | findstr /I "laptop" >nul && set "MACHINE_NAME=laptop"
)

powershell -WindowStyle Hidden -Command "Start-Process -FilePath pythonw -ArgumentList '%~dp0..\scripts\tailscale_monitor.py','monitor' -WindowStyle Hidden -RedirectStandardOutput '%~dp0..\scripts\tailscale_monitor.out.log' -RedirectStandardError '%~dp0..\scripts\tailscale_monitor.err.log'"
REM No pop-ups: use pythonw and no echo/pause.

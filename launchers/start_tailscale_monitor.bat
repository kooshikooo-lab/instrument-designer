@echo off
REM Start the Tailscale peer monitor (server + heartbeat) on this machine.
REM Reads scripts/.tailscale_config.json to know the peer IP.
REM Launches hidden (no PowerShell, no console): wscript -> _run_hidden.vbs -> python hidden.
REM Check status: python scripts\tailscale_monitor.py status
wscript //nologo "%~dp0_run_hidden.vbs" tailscale_monitor.py monitor

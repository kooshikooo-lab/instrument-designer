@echo off
REM Start the Tailscale peer monitor on desktop.
REM Binds to 0.0.0.0:9124 and connects to laptop at 100.100.66.117:9124.

setlocal
set "MACHINE_NAME=desktop"
set "TAILSCALE_PEER_IP=100.100.66.117"
set "TAILSCALE_PORT=9124"
set "TAILSCALE_BIND_IP=0.0.0.0"

powershell -WindowStyle Hidden -Command "Start-Process -FilePath python -ArgumentList '%~dp0..\scripts\tailscale_monitor.py','monitor' -WindowStyle Hidden -RedirectStandardOutput '%~dp0..\scripts\tailscale_monitor.out.log' -RedirectStandardError '%~dp0..\scripts\tailscale_monitor.err.log'"

echo Tailscale monitor started in background.
echo Check status: python scripts\tailscale_monitor.py status
pause

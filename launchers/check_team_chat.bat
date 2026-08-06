@echo off
REM Silent health check for team chat channels (no pop-ups, no console output).
REM Writes status to scripts\check_team_chat.log.

setlocal
set "MACHINE_NAME=desktop"
set "TAILSCALE_PEER_IP=100.100.66.117"
set "TAILSCALE_PORT=9124"
set "TAILSCALE_BIND_IP=0.0.0.0"

pythonw "%~dp0..\scripts\check_team_chat.py" %*

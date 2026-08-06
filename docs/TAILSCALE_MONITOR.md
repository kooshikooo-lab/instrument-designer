# Tailscale Peer Monitor

`scripts/tailscale_monitor.py` provides direct, reliable machine-to-machine
communication and monitoring over Tailscale. It is inspired by the simple,
state-machine protocols used by chess engines talking to servers (e.g., UCI
/XBoard/ICS): a persistent TCP connection, newline-delimited JSON commands,
automatic reconnect, ping/pong heartbeats, and explicit message acknowledgments.

## Why this exists

The GitHub Discussion #23 channel is canonical for long-lived decisions, but it is
not suitable for real-time coordination. The old `scripts/lan_chat.py` on port 9123
was unreliable. This monitor runs directly over Tailscale IPs with a
battle-tested protocol shape.

## Protocol

Both machines run the same script. One machine starts a `server` (or use
`monitor` which runs both server and client). The other starts a `client` (or
`monitor`) pointing at the first machine's Tailscale IP.

Commands are JSON objects, one per line:

- `{"cmd": "ping", "from": "desktop", "time": "..."}` -> reply with `pong`
- `{"cmd": "msg", "id": "...", "from": "desktop", "text": "..."}` -> reply with `ack`
- `{"cmd": "status"}` -> reply with `status_reply`

The connection auto-reconnects with exponential backoff. Messages are queued on
disk and delivered when the peer comes back online.

## Environment variables

- `MACHINE_NAME` — `desktop` or `laptop`. Defaults to `desktop` if COMPUTERNAME
  contains `desktop`, otherwise `laptop`.
- `TAILSCALE_PEER_IP` — Tailscale IP of the other machine.
- `TAILSCALE_PORT` — TCP port (default `9124`).
- `TAILSCALE_BIND_IP` — IP to bind the server on (default `0.0.0.0`).

## Desktop usage

Double-click `launchers/start_tailscale_monitor.bat` or run:

```powershell
$env:MACHINE_NAME="desktop"
$env:TAILSCALE_PEER_IP="100.100.66.117"
$env:TAILSCALE_PORT="9124"
python scripts/tailscale_monitor.py monitor
```

## Laptop usage

```bash
export MACHINE_NAME="laptop"
export TAILSCALE_PEER_IP="100.69.113.41"
export TAILSCALE_PORT="9124"
python scripts/tailscale_monitor.py monitor
```

## CLI

```bash
python scripts/tailscale_monitor.py server      # accept incoming connections
python scripts/tailscale_monitor.py client      # connect to peer and keep alive
python scripts/tailscale_monitor.py monitor     # run both server and client
python scripts/tailscale_monitor.py status      # print peer status
python scripts/tailscale_monitor.py test        # one-shot connectivity check
python scripts/tailscale_monitor.py send "..."  # queue a message
```

## State and logs

- `scripts/.tailscale_monitor.json` — last seen time, queued messages, received messages.
- `scripts/tailscale_monitor.log` — human-readable log.

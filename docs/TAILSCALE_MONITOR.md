# Tailscale Peer Monitor

`scripts/tailscale_monitor.py` provides direct, reliable machine-to-machine
communication and monitoring over Tailscale. It is inspired by the simple,
state-machine protocols used by chess engines talking to servers (e.g., UCI
/XBoard/ICS): newline-delimited JSON commands, ping/pong heartbeats, and
short-lived TCP connections.

## Why this exists

The GitHub Discussion #23 channel is canonical for long-lived decisions, but it is
not suitable for real-time coordination. The old `scripts/lan_chat.py` on port 9123
was unreliable. This monitor runs directly over Tailscale IPs with a
battle-tested protocol shape.

## Protocol

Both machines run the same script. Each machine runs a `server` to accept
incoming connections, and a `heartbeat` loop to poll the peer.

Commands are JSON objects, one per line:

- `{"cmd": "ping", "from": "desktop", "time": "..."}` -> reply with `pong`
- `{"cmd": "msg", "from": "desktop", "text": "..."}` -> reply with `ok`
- `{"cmd": "status"}` -> reply with `status_reply`

Each interaction opens a fresh TCP connection, sends one command, waits for the
reply, and closes the connection. There is no persistent connection to break, no
message queue, and no acknowledgment state to keep in sync.

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
python scripts/tailscale_monitor.py heartbeat   # ping peer every N seconds
python scripts/tailscale_monitor.py monitor     # run server + heartbeat
python scripts/tailscale_monitor.py status      # print peer status
python scripts/tailscale_monitor.py test        # one-shot connectivity check
python scripts/tailscale_monitor.py send "..."  # send a message
```

## State and logs

- `scripts/.tailscale_monitor.json` — last seen time, received messages.
- `scripts/tailscale_monitor.log` — human-readable log.

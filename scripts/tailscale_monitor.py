"""Tailscale peer monitor and direct message relay.

Symmetric, UCI/ICS-inspired protocol:
- Both machines run the same script.
- Both machines run a TCP server (bind 0.0.0.0:port) so either can initiate.
- Every interaction is a short-lived connection: connect, send one command,
  receive a reply, disconnect.
- Peer IP/port is read from scripts/.tailscale_config.json (or env overrides).
- MACHINE_NAME can be set via env var; otherwise inferred from hostname.

This avoids the fragility of persistent TCP connections and NAT/firewall issues.

Usage:
    python scripts/tailscale_monitor.py configure              # auto-write config
    python scripts/tailscale_monitor.py server                # start listening server
    python scripts/tailscale_monitor.py monitor               # server + heartbeat loop
    python scripts/tailscale_monitor.py heartbeat             # ping peer every N seconds
    python scripts/tailscale_monitor.py send "hello"          # one-shot message to peer
    python scripts/tailscale_monitor.py notify "sync github"  # one-shot notify to peer
    python scripts/tailscale_monitor.py status                # show last seen time
    python scripts/tailscale_monitor.py test                  # one-shot connectivity test

Environment overrides:
    TAILSCALE_PEER_IP    - IP of the other machine (default from config)
    TAILSCALE_BIND_IP    - IP to bind the server on (default from config)
    TAILSCALE_PORT       - port (default from config)
    MACHINE_NAME         - "desktop" or "laptop" (default: inferred from hostname)
"""

import argparse
import json
import os
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

HEARTBEAT_INTERVAL = 15.0
OFFLINE_THRESHOLD = 60.0
RECV_TIMEOUT = 5.0
CONNECT_TIMEOUT = 3.0

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = REPO_ROOT / "scripts" / ".tailscale_config.json"
STATE_FILE = REPO_ROOT / "scripts" / ".tailscale_monitor.json"
LOG_FILE = REPO_ROOT / "scripts" / "tailscale_monitor.log"


def _machine_name():
    """Return 'desktop' or 'laptop'. Prefer env, then hostname hints."""
    for key in ("MACHINE_NAME", "TEAM_MACHINE"):
        env = os.environ.get(key, "").strip().lower()
        if env in ("desktop", "laptop"):
            return env
    host = os.environ.get("COMPUTERNAME", "").lower()
    if "desktop" in host:
        return "desktop"
    if "laptop" in host:
        return "laptop"
    # Fallback: if this machine's Tailscale IP matches the desktop entry, we are desktop.
    cfg = _load_config(silent=True)
    if cfg:
        my_ip = _my_tailscale_ip(silent=True)
        if my_ip and cfg.get("desktop", {}).get("ip") == my_ip:
            return "desktop"
        if my_ip and cfg.get("laptop", {}).get("ip") == my_ip:
            return "laptop"
    return "unknown"


def _load_config(silent=False):
    """Load Tailscale peer config from scripts/.tailscale_config.json."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            if not silent:
                _log(f"config load failed: {e}")
    return None


def _save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    _log(f"config saved to {CONFIG_FILE}")


def _my_tailscale_ip(silent=False):
    """Try to discover this machine's Tailscale IPv4 address."""
    try:
        result = subprocess.run(
            ["tailscale", "ip", "-4"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            ip = result.stdout.strip().splitlines()[0].strip()
            if ip:
                return ip
    except Exception as e:
        if not silent:
            _log(f"tailscale ip discovery failed: {e}")
    return None


def _resolve_config():
    """Return (machine_name, peer_ip, bind_ip, port) for this machine."""
    machine = _machine_name()
    if machine == "unknown":
        _log("ERROR: cannot determine machine name. Set MACHINE_NAME=desktop or laptop.")
        sys.exit(1)

    # Environment overrides always win.
    peer_ip = os.environ.get("TAILSCALE_PEER_IP", "")
    bind_ip = os.environ.get("TAILSCALE_BIND_IP", "")
    port_env = os.environ.get("TAILSCALE_PORT", "")

    if not peer_ip or not bind_ip or not port_env:
        cfg = _load_config()
        if cfg is None:
            _log(f"ERROR: config not found at {CONFIG_FILE}. Run: python scripts/tailscale_monitor.py configure")
            sys.exit(1)
        entry = cfg.get(machine)
        if not entry:
            _log(f"ERROR: no config entry for machine '{machine}' in {CONFIG_FILE}")
            sys.exit(1)
        peer_ip = peer_ip or entry.get("peer", "")
        bind_ip = bind_ip or entry.get("bind", "0.0.0.0")
        port_env = port_env or str(entry.get("port", 9124))

    port = int(port_env)

    if not peer_ip:
        _log(f"ERROR: peer IP not configured for machine '{machine}'")
        sys.exit(1)

    return machine, peer_ip, bind_ip, port


def _log(text):
    line = f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] {_machine_name()}: {text}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _load_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "last_seen_peer": None,
        "last_heartbeat_sent": None,
        "received_messages": [],
    }


def _save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except OSError as e:
        _log(f"state save failed: {e}")


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _encode(obj):
    return (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")


def _send_and_receive(peer_ip, port, command, timeout=RECV_TIMEOUT):
    """One-shot request: connect, send one command, receive reply, close."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(CONNECT_TIMEOUT)
    try:
        sock.connect((peer_ip, port))
        sock.settimeout(timeout)
        sock.sendall(_encode(command))
        sock.shutdown(socket.SHUT_WR)
        buf = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf += chunk
            if b"\n" in buf:
                break
        if not buf:
            return None
        try:
            return json.loads(buf.decode("utf-8", errors="replace").strip().split("\n")[0])
        except (json.JSONDecodeError, ValueError):
            return None
    except (ConnectionRefusedError, socket.timeout, OSError) as e:
        return None
    finally:
        try:
            sock.close()
        except Exception:
            pass


def _update_last_seen(peer_ip):
    state = _load_state()
    state["last_seen_peer"] = _now_iso()
    _save_state(state)
    _log(f"heard from peer at {peer_ip}")


def _handle_command(sock, addr, obj):
    me = _machine_name()
    cmd = obj.get("cmd")
    if cmd == "ping":
        _update_last_seen(addr[0])
        sock.sendall(_encode({"cmd": "pong", "from": me, "time": _now_iso()}))
    elif cmd == "msg":
        sender = obj.get("from", "unknown")
        text = obj.get("text", "")
        _update_last_seen(addr[0])
        state = _load_state()
        existing = state.get("received_messages", [])
        msg_id = obj.get("id")
        if msg_id and any(m.get("id") == msg_id for m in existing):
            _log(f"duplicate message id {msg_id} ignored")
        else:
            entry = {"from": sender, "text": text, "time": _now_iso()}
            if msg_id:
                entry["id"] = msg_id
            existing = existing + [entry]
        state["received_messages"] = existing[-200:]
        _save_state(state)
        _log(f"message from {sender}: {text[:80]}")
        sock.sendall(_encode({"cmd": "ok", "from": me, "time": _now_iso()}))
    elif cmd == "notify":
        channel = obj.get("channel", "unknown")
        text = obj.get("text", "")
        _update_last_seen(addr[0])
        _log(f"notify from {obj.get('from', 'unknown')}: channel={channel} text={text[:80]}")
        sock.sendall(_encode({"cmd": "notify_ok", "from": me, "time": _now_iso(), "channel": channel}))
    elif cmd == "status":
        _update_last_seen(addr[0])
        state = _load_state()
        sock.sendall(_encode({
            "cmd": "status_reply",
            "from": me,
            "time": _now_iso(),
            "last_seen_peer": state.get("last_seen_peer"),
        }))


def _client_handler(sock, addr):
    buf = b""
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line.decode("utf-8", errors="replace"))
                except json.JSONDecodeError:
                    _log(f"non-JSON line from {addr}: {line[:80]}")
                    continue
                _handle_command(sock, addr, obj)
    except (ConnectionResetError, OSError) as e:
        _log(f"peer {addr} disconnected: {e}")
    finally:
        try:
            sock.close()
        except Exception:
            pass


def cmd_server(bind_ip, port):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((bind_ip, port))
    srv.listen(5)
    srv.settimeout(1.0)
    _log(f"server listening on {bind_ip}:{port}")
    try:
        while True:
            try:
                sock, addr = srv.accept()
            except socket.timeout:
                continue
            sock.settimeout(5.0)
            _log(f"peer connected from {addr}")
            threading.Thread(target=_client_handler, args=(sock, addr), daemon=True).start()
    except KeyboardInterrupt:
        pass
    finally:
        srv.close()


def cmd_send(peer_ip, port, text):
    reply = _send_and_receive(peer_ip, port, {
        "cmd": "msg",
        "from": _machine_name(),
        "text": text,
    })
    if reply:
        _log(f"message delivered to {peer_ip}:{port}, reply: {reply.get('cmd')}")
        return True
    else:
        _log(f"message failed to deliver to {peer_ip}:{port}")
        return False


def cmd_notify(peer_ip, port, text, channel="github"):
    reply = _send_and_receive(peer_ip, port, {
        "cmd": "notify",
        "from": _machine_name(),
        "channel": channel,
        "text": text,
    })
    if reply:
        _log(f"notify delivered to {peer_ip}:{port}, reply: {reply.get('cmd')}")
        return True
    else:
        _log(f"notify failed to deliver to {peer_ip}:{port}")
        return False


def cmd_heartbeat(peer_ip, port):
    _log(f"heartbeat loop starting, peer={peer_ip}:{port}")
    while True:
        reply = _send_and_receive(peer_ip, port, {
            "cmd": "ping",
            "from": _machine_name(),
            "time": _now_iso(),
        })
        if reply and reply.get("cmd") == "pong":
            state = _load_state()
            state["last_heartbeat_sent"] = _now_iso()
            _save_state(state)
            _log(f"heartbeat ok from {peer_ip}:{port}")
        else:
            state = _load_state()
            last_seen = state.get("last_seen_peer")
            if last_seen:
                ago = (datetime.now(timezone.utc) - datetime.fromisoformat(last_seen)).total_seconds()
                if ago > OFFLINE_THRESHOLD:
                    _log(f"ALERT: peer offline for {ago:.0f}s")
            else:
                _log(f"peer unreachable at {peer_ip}:{port}")
        time.sleep(HEARTBEAT_INTERVAL)


def cmd_status(peer_ip, port):
    state = _load_state()
    last_seen = state.get("last_seen_peer")
    last_sent = state.get("last_heartbeat_sent")
    print(f"machine: {_machine_name()}")
    print(f"peer: {peer_ip}:{port}")
    print(f"last_seen_peer: {last_seen or 'never'}")
    print(f"last_heartbeat_sent: {last_sent or 'never'}")
    if last_seen:
        ago = (datetime.now(timezone.utc) - datetime.fromisoformat(last_seen)).total_seconds()
        print(f"peer_offline_for_seconds: {ago:.0f}")
    else:
        print("peer_offline_for_seconds: N/A")


def cmd_test(peer_ip, port):
    reply = _send_and_receive(peer_ip, port, {
        "cmd": "ping",
        "from": _machine_name(),
        "time": _now_iso(),
    })
    if reply and reply.get("cmd") == "pong":
        print(f"OK: peer replied {reply}")
        return True
    else:
        print(f"FAIL: no reply from {peer_ip}:{port}")
        sys.exit(1)


def cmd_monitor(bind_ip, port, peer_ip):
    """Run server in background and heartbeat in foreground."""
    threading.Thread(target=cmd_server, args=(bind_ip, port), daemon=True).start()
    # Briefly let the server thread start before heartbeat fires.
    time.sleep(0.5)
    cmd_heartbeat(peer_ip, port)


def cmd_configure():
    """Interactively create/update the Tailscale config file."""
    machine = _machine_name()
    my_ip = _my_tailscale_ip()
    print(f"Detected machine: {machine}")
    print(f"Detected Tailscale IP: {my_ip or 'unknown'}")

    peer_name = "laptop" if machine == "desktop" else "desktop"
    peer_ip = input(f"Enter Tailscale IP for {peer_name}: ").strip()
    if not peer_ip:
        print("Peer IP required. Exiting.")
        sys.exit(1)

    cfg = _load_config(silent=True) or {}
    cfg[machine] = {"ip": my_ip, "peer": peer_ip, "bind": "0.0.0.0", "port": 9124}
    cfg[peer_name] = cfg.get(peer_name, {})
    cfg[peer_name]["ip"] = peer_ip
    if "peer" not in cfg[peer_name] and my_ip:
        cfg[peer_name]["peer"] = my_ip
    if "bind" not in cfg[peer_name]:
        cfg[peer_name]["bind"] = "0.0.0.0"
    if "port" not in cfg[peer_name]:
        cfg[peer_name]["port"] = 9124
    _save_config(cfg)


def main():
    machine, peer_ip, bind_ip, port = _resolve_config()

    parser = argparse.ArgumentParser(description="Tailscale peer monitor")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("configure", help="create/update Tailscale config file")
    sub.add_parser("server", help="start listening server")
    sub.add_parser("monitor", help="run server + heartbeat")
    sub.add_parser("heartbeat", help="send ping to peer every N seconds")
    sub.add_parser("status", help="show local status")
    sub.add_parser("test", help="one-shot connectivity test")
    p_send = sub.add_parser("send", help="send a message to the peer")
    p_send.add_argument("text", help="message text")
    p_notify = sub.add_parser("notify", help="send a notification to the peer")
    p_notify.add_argument("text", help="notification text")
    p_notify.add_argument("--channel", default="github", help="channel name")
    args = parser.parse_args()

    if args.cmd == "configure":
        cmd_configure()
    elif args.cmd == "server":
        cmd_server(bind_ip, port)
    elif args.cmd == "monitor":
        cmd_monitor(bind_ip, port, peer_ip)
    elif args.cmd == "heartbeat":
        cmd_heartbeat(peer_ip, port)
    elif args.cmd == "status":
        cmd_status(peer_ip, port)
    elif args.cmd == "test":
        cmd_test(peer_ip, port)
    elif args.cmd == "send":
        cmd_send(peer_ip, port, args.text)
    elif args.cmd == "notify":
        cmd_notify(peer_ip, port, args.text, args.channel)


if __name__ == "__main__":
    main()

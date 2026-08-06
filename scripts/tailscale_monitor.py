"""Tailscale peer monitor and direct message relay.

Simple, robust protocol inspired by UCI/ICS chess-engine interfaces:
- Desktop always runs a TCP server on its Tailscale IP.
- Each interaction is a short-lived connection: connect, send one command,
  receive a reply, disconnect.
- The laptop can send heartbeats, messages, and status requests.
- The desktop tracks the last time it heard from the laptop.

This avoids the fragility of persistent TCP connections and NAT/firewall issues.

Usage:
    python scripts/tailscale_monitor.py server                # start listening server
    python scripts/tailscale_monitor.py heartbeat             # ping peer every N seconds
    python scripts/tailscale_monitor.py send "hello"          # one-shot message to peer
    python scripts/tailscale_monitor.py status                # show last seen time
    python scripts/tailscale_monitor.py test                  # one-shot connectivity test

Environment:
    TAILSCALE_PEER_IP    - IP of the other machine (default: 100.100.66.117)
    TAILSCALE_BIND_IP    - IP to bind the server on (default: 0.0.0.0)
    TAILSCALE_PORT       - port (default: 9124)
    MACHINE_NAME         - "desktop" or "laptop" (default: inferred from hostname)
"""

import argparse
import json
import os
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PEER_IP = "100.100.66.117"  # laptop
DEFAULT_BIND_IP = "0.0.0.0"
DEFAULT_PORT = 9124

HEARTBEAT_INTERVAL = 15.0
OFFLINE_THRESHOLD = 60.0
RECV_TIMEOUT = 5.0

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = REPO_ROOT / "scripts" / ".tailscale_monitor.json"
LOG_FILE = REPO_ROOT / "scripts" / "tailscale_monitor.log"


def _machine_name():
    return os.environ.get("MACHINE_NAME") or (
        "desktop" if "desktop" in os.environ.get("COMPUTERNAME", "").lower() else "laptop"
    )


def _peer_ip():
    return os.environ.get("TAILSCALE_PEER_IP", DEFAULT_PEER_IP)


def _port():
    return int(os.environ.get("TAILSCALE_PORT", DEFAULT_PORT))


def _bind_ip():
    return os.environ.get("TAILSCALE_BIND_IP", DEFAULT_BIND_IP)


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
        "peer_ip": _peer_ip(),
        "port": _port(),
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
    sock.settimeout(timeout)
    try:
        sock.connect((peer_ip, port))
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
        state["received_messages"] = state.get("received_messages", []) + [
            {"from": sender, "text": text, "time": _now_iso()}
        ]
        _save_state(state)
        _log(f"message from {sender}: {text[:80]}")
        sock.sendall(_encode({"cmd": "ok", "from": me, "time": _now_iso()}))
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


def cmd_server():
    port = _port()
    bind = _bind_ip()
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((bind, port))
    srv.listen(5)
    srv.settimeout(1.0)
    _log(f"server listening on {bind}:{port}")
    try:
        while True:
            try:
                sock, addr = srv.accept()
            except socket.timeout:
                continue
            sock.settimeout(5.0)
            _log(f"peer connected from {addr}")
            _client_handler(sock, addr)
            _log(f"peer disconnected from {addr}")
    except KeyboardInterrupt:
        pass
    finally:
        srv.close()


def cmd_send(text):
    peer_ip = _peer_ip()
    port = _port()
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


def cmd_heartbeat():
    peer_ip = _peer_ip()
    port = _port()
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


def cmd_status():
    state = _load_state()
    last_seen = state.get("last_seen_peer")
    last_sent = state.get("last_heartbeat_sent")
    print(f"machine: {_machine_name()}")
    print(f"peer: {state.get('peer_ip')}:{state.get('port')}")
    print(f"last_seen_peer: {last_seen or 'never'}")
    print(f"last_heartbeat_sent: {last_sent or 'never'}")
    if last_seen:
        ago = (datetime.now(timezone.utc) - datetime.fromisoformat(last_seen)).total_seconds()
        print(f"peer_offline_for_seconds: {ago:.0f}")
    else:
        print("peer_offline_for_seconds: N/A")


def cmd_test():
    peer_ip = _peer_ip()
    port = _port()
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


def cmd_monitor():
    """Run server in background and heartbeat in foreground."""
    import threading
    threading.Thread(target=cmd_server, daemon=True).start()
    cmd_heartbeat()


def main():
    parser = argparse.ArgumentParser(description="Tailscale peer monitor")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("server", help="start listening server")
    sub.add_parser("heartbeat", help="send ping to peer every N seconds")
    sub.add_parser("monitor", help="run server + heartbeat")
    sub.add_parser("status", help="show local status")
    sub.add_parser("test", help="one-shot connectivity test")
    p_send = sub.add_parser("send", help="send a message to the peer")
    p_send.add_argument("text", help="message text")
    args = parser.parse_args()

    if args.cmd == "server":
        cmd_server()
    elif args.cmd == "heartbeat":
        cmd_heartbeat()
    elif args.cmd == "monitor":
        cmd_monitor()
    elif args.cmd == "status":
        cmd_status()
    elif args.cmd == "test":
        cmd_test()
    elif args.cmd == "send":
        cmd_send(args.text)


if __name__ == "__main__":
    main()

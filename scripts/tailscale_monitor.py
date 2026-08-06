"""Tailscale peer monitor and direct message relay.

Chess-engine-inspired protocol over a persistent TCP connection:
- newline-delimited JSON commands
- automatic reconnect with exponential backoff
- ping/pong heartbeat, msg/ack delivery, status/status_reply
- both peers run the same script (server + client loop)

Usage:
    python scripts/tailscale_monitor.py server              # accept incoming connections
    python scripts/tailscale_monitor.py client              # connect to peer and keep alive
    python scripts/tailscale_monitor.py send "hello"        # queue a message
    python scripts/tailscale_monitor.py status              # show peer status
    python scripts/tailscale_monitor.py test                # one-shot connectivity test

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
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PEER_IP = "100.100.66.117"  # laptop
DEFAULT_BIND_IP = "0.0.0.0"
DEFAULT_PORT = 9124

HEARTBEAT_INTERVAL = 15.0
OFFLINE_THRESHOLD = 60.0
RECONNECT_MIN = 1.0
RECONNECT_MAX = 30.0

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
        "queued_messages": [],
        "received_messages": [],
        "connection_up": False,
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
    return json.dumps(obj, ensure_ascii=False) + "\n"


def _recv_line(sock, buf):
    """Read one complete line from socket. Returns (line, buf) or (None, buf) on close/error."""
    while True:
        if "\n" in buf:
            line, buf = buf.split("\n", 1)
            return line, buf
        try:
            chunk = sock.recv(4096).decode("utf-8", errors="replace")
        except (socket.timeout, ConnectionResetError, OSError):
            return None, buf
        if not chunk:
            return None, buf
        buf += chunk


class _Connection:
    """One persistent TCP connection (either inbound or outbound)."""

    def __init__(self, sock, name, is_inbound):
        self.sock = sock
        self.name = name
        self.is_inbound = is_inbound
        self.buf = ""
        self.lock = threading.Lock()
        self.alive = True

    def send(self, obj):
        if not self.alive:
            return False
        with self.lock:
            try:
                self.sock.sendall(_encode(obj).encode("utf-8"))
                return True
            except (ConnectionResetError, OSError) as e:
                self.alive = False
                return False

    def close(self):
        self.alive = False
        try:
            self.sock.close()
        except Exception:
            pass


def _handle_command(conn, obj):
    me = _machine_name()
    cmd = obj.get("cmd")
    state = _load_state()

    if cmd == "ping":
        conn.send({"cmd": "pong", "from": me, "time": _now_iso()})
        state["last_seen_peer"] = _now_iso()
        state["connection_up"] = True
        _save_state(state)
    elif cmd == "pong":
        state["last_seen_peer"] = _now_iso()
        state["connection_up"] = True
        _save_state(state)
    elif cmd == "msg":
        msg_id = obj.get("id", "")
        text = obj.get("text", "")
        sender = obj.get("from", "unknown")
        msg = {
            "from": sender,
            "text": text,
            "time": _now_iso(),
            "id": msg_id,
        }
        state["received_messages"] = state.get("received_messages", []) + [msg]
        state["last_seen_peer"] = _now_iso()
        state["connection_up"] = True
        _save_state(state)
        _log(f"message from {sender}: {text[:80]}")
        conn.send({"cmd": "ack", "id": msg_id, "from": me})
    elif cmd == "ack":
        msg_id = obj.get("id", "")
        _remove_acked(msg_id)
        state["last_seen_peer"] = _now_iso()
        state["connection_up"] = True
        _save_state(state)
    elif cmd == "status":
        conn.send({
            "cmd": "status_reply",
            "from": me,
            "time": _now_iso(),
            "queued": len(state.get("queued_messages", [])),
            "last_seen_peer": state.get("last_seen_peer"),
        })
        state["last_seen_peer"] = _now_iso()
        state["connection_up"] = True
        _save_state(state)
    elif cmd == "status_reply":
        state["last_seen_peer"] = _now_iso()
        state["connection_up"] = True
        _save_state(state)


def _remove_acked(msg_id):
    state = _load_state()
    queue = state.get("queued_messages", [])
    new_queue = [m for m in queue if m.get("id") != msg_id]
    if len(new_queue) != len(queue):
        state["queued_messages"] = new_queue
        _save_state(state)


def _server_connection_loop(conn):
    peer_addr = conn.sock.getpeername()
    _log(f"peer connected from {peer_addr}")
    _flush_queue(conn)
    while conn.alive:
        line, conn.buf = _recv_line(conn.sock, conn.buf)
        if line is None:
            break
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            _log(f"non-JSON line: {line[:80]}")
            continue
        _handle_command(conn, obj)
    conn.close()
    state = _load_state()
    state["connection_up"] = False
    _save_state(state)
    _log(f"peer disconnected from {peer_addr}")


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
            conn = _Connection(sock, str(addr), True)
            threading.Thread(target=_server_connection_loop, args=(conn,), daemon=True).start()
    except KeyboardInterrupt:
        pass
    finally:
        srv.close()


def _connect_peer(peer_ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)
    try:
        sock.connect((peer_ip, port))
        sock.settimeout(None)
        return _Connection(sock, peer_ip, False)
    except (ConnectionRefusedError, socket.timeout, OSError) as e:
        sock.close()
        return None


def _client_loop():
    peer_ip = _peer_ip()
    port = _port()
    _log(f"client loop starting, peer={peer_ip}:{port}")
    backoff = RECONNECT_MIN
    while True:
        conn = _connect_peer(peer_ip, port)
        if conn is None:
            _log(f"peer unreachable, reconnect in {backoff:.1f}s")
            time.sleep(backoff)
            backoff = min(backoff * 2, RECONNECT_MAX)
            continue
        _log(f"connected to peer {peer_ip}:{port}")
        backoff = RECONNECT_MIN

        # Heartbeat thread
        stop_event = threading.Event()

        def heartbeat():
            while not stop_event.is_set():
                if not conn.send({"cmd": "ping", "from": _machine_name(), "time": _now_iso()}):
                    break
                time.sleep(HEARTBEAT_INTERVAL)

        hb_thread = threading.Thread(target=heartbeat, daemon=True)
        hb_thread.start()

        # Send any queued messages
        _flush_queue(conn)

        # Receive loop
        while conn.alive:
            line, conn.buf = _recv_line(conn.sock, conn.buf)
            if line is None:
                break
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                _log(f"non-JSON line from peer: {line[:80]}")
                continue
            _handle_command(conn, obj)

        stop_event.set()
        conn.close()
        state = _load_state()
        state["connection_up"] = False
        _save_state(state)
        _log(f"peer connection lost, reconnect in {backoff:.1f}s")
        time.sleep(backoff)
        backoff = min(backoff * 2, RECONNECT_MAX)


def _flush_queue(conn):
    state = _load_state()
    queue = state.get("queued_messages", [])
    if not queue:
        return
    for msg in list(queue):
        if conn.send({
            "cmd": "msg",
            "id": msg.get("id"),
            "from": _machine_name(),
            "text": msg.get("text", ""),
        }):
            _log(f"sent message: {msg.get('text', '')[:60]}")
        else:
            break


def cmd_client():
    _client_loop()


def cmd_send(text):
    state = _load_state()
    msg_id = f"{_machine_name()}-{int(time.time()*1000)}"
    state["queued_messages"] = state.get("queued_messages", []) + [
        {"id": msg_id, "text": text, "time": _now_iso()}
    ]
    _save_state(state)
    _log(f"queued message [{msg_id}]: {text[:80]}")


def cmd_status():
    state = _load_state()
    last_seen = state.get("last_seen_peer")
    last_sent = state.get("last_heartbeat_sent")
    queued = len(state.get("queued_messages", []))
    print(f"machine: {_machine_name()}")
    print(f"peer: {state.get('peer_ip')}:{state.get('port')}")
    print(f"connection_up: {state.get('connection_up', False)}")
    print(f"last_seen_peer: {last_seen or 'never'}")
    print(f"queued_messages: {queued}")
    if last_seen:
        ago = (datetime.now(timezone.utc) - datetime.fromisoformat(last_seen)).total_seconds()
        print(f"peer_offline_for_seconds: {ago:.0f}")


def cmd_test():
    peer_ip = _peer_ip()
    port = _port()
    conn = _connect_peer(peer_ip, port)
    if conn is None:
        print(f"FAIL: cannot connect to {peer_ip}:{port}")
        sys.exit(1)
    conn.send({"cmd": "ping", "from": _machine_name(), "time": _now_iso()})
    line, conn.buf = _recv_line(conn.sock, conn.buf)
    conn.close()
    if line:
        try:
            obj = json.loads(line)
            if obj.get("cmd") == "pong":
                print(f"OK: peer replied with {obj}")
                return
        except json.JSONDecodeError:
            pass
    print(f"FAIL: no pong from {peer_ip}:{port}")
    sys.exit(1)


def cmd_monitor():
    """Run both server and client in background threads."""
    threading.Thread(target=cmd_server, daemon=True).start()
    cmd_client()


def main():
    parser = argparse.ArgumentParser(description="Tailscale peer monitor")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("server", help="accept incoming connections")
    sub.add_parser("client", help="connect to peer and keep alive")
    sub.add_parser("monitor", help="run both server and client")
    sub.add_parser("status", help="show local status")
    sub.add_parser("test", help="one-shot connectivity test")
    p_send = sub.add_parser("send", help="queue a message for the peer")
    p_send.add_argument("text", help="message text")
    args = parser.parse_args()

    if args.cmd == "server":
        cmd_server()
    elif args.cmd == "client":
        cmd_client()
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

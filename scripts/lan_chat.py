"""
Lightweight LAN chat over Tailscale.

Both machines run a server on port 9123. Each machine sends to the OTHER's server.
Server is headless (no input()), auto-ACKs every message.

Usage:
  python lan_chat.py server                  # Start headless server on 9123
  python lan_chat.py client <host> [port]    # Persistent client connection
  python lan_chat.py send <msg> <host> [port]  # One-shot send, get ACK
"""
import sys, socket, threading, json, time, os

DEFAULT_PORT = 9123
MY_NAME = "desktop" if "desktop" in os.environ.get("COMPUTERNAME", "").lower() else "laptop"
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "chat.log")


def _log(text):
    """Print and append to chat.log."""
    print(text)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {text}\n")
    except Exception:
        pass


def server(port=DEFAULT_PORT):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", port))
    srv.listen(5)
    print(f"[{MY_NAME.upper()} SERVER] Listening on port {port}...")

    def handle_client(conn, addr):
        print(f"[SERVER] Connection from {addr}")
        try:
            buf = ""
            while True:
                data = conn.recv(4096).decode("utf-8")
                if not data:
                    break
                buf += data
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    if not line.strip():
                        continue
                    try:
                        msg = json.loads(line)
                        sender = msg.get("from", "unknown")
                        text = msg.get("text", "")
                        print(f"[{sender}] {text}")

                        ack = json.dumps({
                            "from": MY_NAME,
                            "text": f"ACK: {text[:100]}"
                        }) + "\n"
                        conn.sendall(ack.encode("utf-8"))
                    except json.JSONDecodeError:
                        print(f"[WARN] Non-JSON: {line[:80]}")
        except Exception as e:
            print(f"[SERVER] Error: {e}")
        finally:
            conn.close()
            print(f"[SERVER] {addr} disconnected")

    while True:
        try:
            conn, addr = srv.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
        except OSError:
            break
    srv.close()


def send(text, host, port=DEFAULT_PORT, wait=5.0):
    """One-shot send: connect, send message, wait for ACK, close."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(wait)
    try:
        sock.connect((host, port))
        msg = json.dumps({"from": MY_NAME, "text": text}) + "\n"
        sock.sendall(msg.encode("utf-8"))
        print(f"[SENT -> {host}:{port}] {text[:60]}...")

        replies = []
        buf = ""
        deadline = time.time() + wait
        while time.time() < deadline:
            try:
                chunk = sock.recv(4096).decode("utf-8")
                if not chunk:
                    break
                buf += chunk
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    if line.strip():
                        r = json.loads(line)
                        replies.append(r)
                        print(f"[REPLY] {r['from']}: {r['text'][:80]}")
            except socket.timeout:
                break
            except ConnectionResetError:
                print("[RESET] Connection closed by remote")
                break

        sock.close()
        return replies
    except ConnectionRefusedError:
        print(f"[ERROR] {host}:{port} refused - server not running?")
        return []
    except socket.timeout:
        print(f"[ERROR] Connection to {host}:{port} timed out")
        sock.close()
        return []
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        sock.close()
        return []


# Persistent message queue for sending from background threads
_msg_queue = []
_queue_lock = threading.Lock()


def _enqueue(text, host, port=DEFAULT_PORT):
    """Queue a message to be sent by the client thread."""
    with _queue_lock:
        _msg_queue.append((text, host, port))


def client(host, port=DEFAULT_PORT):
    """Persistent client: connects to host server, stays open, sends queued messages."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1.0)
    try:
        sock.connect((host, port))
        print(f"[CLIENT] Connected to {host}:{port}")
    except Exception as e:
        print(f"[CLIENT] Failed to connect: {e}")
        return

    connected = True

    def recv_loop():
        nonlocal connected
        buf = ""
        while connected:
            try:
                chunk = sock.recv(4096).decode("utf-8")
                if not chunk:
                    break
                buf += chunk
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    if line.strip():
                        try:
                            r = json.loads(line)
                            print(f"[{r.get('from', '?')}] {r.get('text', '')}")
                        except json.JSONDecodeError:
                            pass
            except socket.timeout:
                continue
            except (ConnectionResetError, OSError):
                break
        connected = False
        print("[CLIENT] Disconnected from server")

    t = threading.Thread(target=recv_loop, daemon=True)
    t.start()

    while connected:
        msg = None
        with _queue_lock:
            if _msg_queue:
                msg = _msg_queue.pop(0)
        if msg:
            text, target_host, target_port = msg
            try:
                payload = json.dumps({"from": MY_NAME, "text": text}) + "\n"
                sock.sendall(payload.encode("utf-8"))
                print(f"[SENT] {text[:60]}...")
            except (ConnectionResetError, OSError):
                print("[CLIENT] Send failed - disconnected")
                break
        else:
            time.sleep(0.1)

    sock.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python lan_chat.py server [port]")
        print(f"       python lan_chat.py client <host> [port]")
        print(f"       python lan_chat.py send <msg> <host> [port]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "server":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT
        server(port)
    elif cmd == "client":
        host = sys.argv[2] if len(sys.argv) > 2 else "100.69.113.41"
        port = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_PORT
        client(host, port)
    elif cmd == "send":
        text = sys.argv[2] if len(sys.argv) > 2 else ""
        host = sys.argv[3] if len(sys.argv) > 3 else "100.69.113.41"
        port = int(sys.argv[4]) if len(sys.argv) > 4 else DEFAULT_PORT
        replies = send(text, host, port)
        if not replies:
            print("[no reply]")
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

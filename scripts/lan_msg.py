"""HTTP-based machine-to-machine messaging over Tailscale/LAN.

No dependencies beyond stdlib. Each machine runs a server and polls the other.

Server:  python scripts/lan_msg.py server [port]
Send:    python scripts/lan_msg.py send <host> <msg>
Poll:    python scripts/lan_msg.py poll <host> [--since=<id>]
"""
import sys, json, http.server, threading, os, time, urllib.request, urllib.error
from datetime import datetime, timezone

DEFAULT_PORT = 9124
MSG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lan_messages.json")

_messages = []
_msg_lock = threading.Lock()
_next_id = 0

def load_messages():
    global _messages, _next_id
    if os.path.exists(MSG_FILE):
        try:
            with open(MSG_FILE, "r", encoding="utf-8") as f:
                _messages = json.load(f)
            if _messages:
                _next_id = max(m["id"] for m in _messages) + 1
        except (json.JSONDecodeError, OSError):
            _messages = []

def save_messages():
    try:
        os.makedirs(os.path.dirname(MSG_FILE), exist_ok=True)
        with open(MSG_FILE, "w", encoding="utf-8") as f:
            json.dump(_messages, f, indent=2)
    except OSError:
        pass

load_messages()

class MsgHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send_json(self, data, code=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/messages"):
            since = int(self.path.split("since=")[-1]) if "since=" in self.path else 0
            with _msg_lock:
                new = [m for m in _messages if m["id"] > since]
            self._send_json({"messages": new, "now": datetime.now(timezone.utc).isoformat()})
        elif self.path == "/ping":
            self._send_json({"pong": True, "time": time.time()})
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path == "/send":
            length = int(self.headers.get("Content-Length", 0))
            if length:
                raw = self.rfile.read(length).decode("utf-8")
                try:
                    data = json.loads(raw)
                    text = data.get("text", "")
                    sender = data.get("from", "unknown")
                    with _msg_lock:
                        global _next_id
                        mid = _next_id
                        _next_id += 1
                        entry = {
                            "id": mid,
                            "from": sender,
                            "text": text,
                            "time": datetime.now(timezone.utc).isoformat()
                        }
                        _messages.append(entry)
                    save_messages()
                    print(f"[{sender}] {text}")
                    self._send_json({"status": "ok", "id": mid})
                except json.JSONDecodeError:
                    self._send_json({"error": "bad json"}, 400)
            else:
                self._send_json({"error": "empty body"}, 400)
        else:
            self._send_json({"error": "not found"}, 404)

def run_server(port=DEFAULT_PORT):
    server = http.server.HTTPServer(("0.0.0.0", port), MsgHandler)
    print(f"[MSG SERVER] Listening on port {port}")
    server.serve_forever()

def send_message(host, text, port=DEFAULT_PORT, timeout=5):
    url = f"http://{host}:{port}/send"
    from_host = "desktop" if "desktop" in os.environ.get("COMPUTERNAME", "").lower() else os.environ.get("COMPUTERNAME", "unknown")
    payload = json.dumps({"from": from_host, "text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, ConnectionRefusedError, ConnectionResetError, OSError) as e:
        return {"error": f"Send failed: {e}"}

def poll_messages(host, since=0, port=DEFAULT_PORT, timeout=5):
    url = f"http://{host}:{port}/messages?since={since}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, ConnectionRefusedError, OSError) as e:
        return {"error": f"Poll failed: {e}", "messages": []}

def ping(host, port=DEFAULT_PORT, timeout=3):
    url = f"http://{host}:{port}/ping"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/lan_msg.py server [port]")
        print("  python scripts/lan_msg.py send <host> <text>")
        print("  python scripts/lan_msg.py poll <host> [--since=N]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "server":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT
        run_server(port)
    elif cmd == "send":
        host = sys.argv[2]
        text = sys.argv[3] if len(sys.argv) > 3 else "(empty)"
        port = int(sys.argv[4]) if len(sys.argv) > 4 else DEFAULT_PORT
        result = send_message(host, text, port)
        print(json.dumps(result, indent=2))
    elif cmd == "poll":
        host = sys.argv[2]
        port = DEFAULT_PORT
        since = 0
        if "--since=" in " ".join(sys.argv[3:]):
            for a in sys.argv[3:]:
                if a.startswith("--since="):
                    since = int(a.split("=")[1])
                elif a.isdigit():
                    port = int(a)
        elif len(sys.argv) > 3 and sys.argv[3].isdigit():
            port = int(sys.argv[3])
        result = poll_messages(host, since, port)
        print(json.dumps(result, indent=2))
    else:
        print(f"Unknown: {cmd}")
        sys.exit(1)

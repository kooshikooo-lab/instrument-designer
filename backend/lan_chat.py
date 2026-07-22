"""
Lightweight LAN chat over Tailscale.
Usage:
  Desktop (server):  python lan_chat.py server
  Laptop (client):   python lan_chat.py client 100.69.113.41
  One-shot send:     python lan_chat.py send "message" [host]
  
Server listens on port 9123. Client connects and exchanges messages.
Type messages and press Enter. Type 'quit' to exit.
'send' mode sends one message, waits 2s for reply, then exits.
"""
import sys, socket, threading, json, time

PORT = 9123

def server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", PORT))
    srv.listen(5)
    print(f"[SERVER] Listening on port {PORT}...")
    
    def handle_client(conn, addr):
        print(f"[SERVER] Client connected from {addr}")
        sender_name = "unknown"
        
        def recv_loop():
            nonlocal sender_name
            while True:
                try:
                    data = conn.recv(4096).decode("utf-8")
                    if not data:
                        break
                    for line in data.strip().split("\n"):
                        if line:
                            msg = json.loads(line)
                            sender_name = msg.get('from', 'unknown')
                            print(f"\n[{msg['from']}] {msg['text']}")
                            try:
                                ack = json.dumps({"from": "server", "text": f"ACK: {msg['text'][:60]}"}) + "\n"
                                conn.sendall(ack.encode("utf-8"))
                            except:
                                pass
                except:
                    break
            print(f"[SERVER] Client {addr} disconnected.")
        
        t = threading.Thread(target=recv_loop, daemon=True)
        t.start()
        
        while True:
            try:
                text = input("[You] ")
                if text == "quit":
                    break
                reply = json.dumps({"from": "laptop", "text": text}) + "\n"
                conn.sendall(reply.encode("utf-8"))
            except:
                break
        
        conn.close()
    
    while True:
        try:
            conn, addr = srv.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
        except:
            break
    
    srv.close()

def client(host):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, PORT))
    print(f"[CLIENT] Connected to {host}:{PORT}")
    
    def recv_loop():
        while True:
            try:
                data = sock.recv(4096).decode("utf-8")
                if not data:
                    break
                for line in data.strip().split("\n"):
                    msg = json.loads(line)
                    print(f"\n[{msg['from']}] {msg['text']}")
            except:
                break
        print("[CLIENT] Disconnected.")
    
    t = threading.Thread(target=recv_loop, daemon=True)
    t.start()
    
    while True:
        text = input("[You] ")
        if text == "quit":
            break
        msg = json.dumps({"from": "laptop", "text": text}) + "\n"
        sock.sendall(msg.encode("utf-8"))
    
    sock.close()

def send(text, host, wait=3.0):
    """Send a message and wait for reply. More robust version."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(wait)
    try:
        sock.connect((host, PORT))
        msg = json.dumps({"from": "laptop", "text": text}) + "\n"
        sock.sendall(msg.encode("utf-8"))
        print(f"[SENT] {text[:50]}...")
        
        replies = []
        try:
            while True:
                data = sock.recv(4096).decode("utf-8")
                if not data:
                    break
                for line in data.strip().split("\n"):
                    if line:
                        r = json.loads(line)
                        replies.append(r)
                        print(f"[REPLY] {r['from']}: {r['text'][:80]}")
        except socket.timeout:
            print("[TIMEOUT] No more replies")
        except ConnectionResetError:
            print("[RESET] Connection closed by remote")
        
        sock.close()
        return replies
    except ConnectionRefusedError:
        print(f"[ERROR] Cannot connect to {host}:{PORT} - server not running?")
        return []
    except Exception as e:
        print(f"[ERROR] {e}")
        return []

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python lan_chat.py server|client|send [host|message]")
        sys.exit(1)
    
    if sys.argv[1] == "server":
        server()
    elif sys.argv[1] == "client":
        host = sys.argv[2] if len(sys.argv) > 2 else "100.69.113.41"
        client(host)
    elif sys.argv[1] == "send":
        text = sys.argv[2] if len(sys.argv) > 2 else ""
        host = sys.argv[3] if len(sys.argv) > 3 else "100.69.113.41"
        replies = send(text, host)
        for r in replies:
            print(f"[{r['from']}] {r['text']}")
        if not replies:
            print("[no reply]")
    else:
        print(f"Unknown command: {sys.argv[1]}")
        sys.exit(1)

"""
Lightweight LAN chat over Tailscale.
Usage:
  Desktop (server):  python lan_chat.py server
  Laptop (client):   python lan_chat.py client 100.69.113.41
  
Server listens on port 9123. Client connects and exchanges messages.
Type messages and press Enter. Type 'quit' to exit.
"""
import sys, socket, threading, json, time

PORT = 9123

def server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", PORT))
    srv.listen(1)
    print(f"[SERVER] Listening on port {PORT}...")
    
    conn, addr = srv.accept()
    print(f"[SERVER] Client connected from {addr}")
    
    def recv_loop():
        while True:
            try:
                data = conn.recv(4096).decode("utf-8")
                if not data:
                    break
                for line in data.strip().split("\n"):
                    msg = json.loads(line)
                    print(f"\n[{msg['from']}] {msg['text']}")
            except:
                break
        print("[SERVER] Client disconnected.")
    
    t = threading.Thread(target=recv_loop, daemon=True)
    t.start()
    
    while True:
        text = input("[You] ")
        if text == "quit":
            break
        msg = json.dumps({"from": "desktop", "text": text}) + "\n"
        conn.sendall(msg.encode("utf-8"))
    
    conn.close()
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

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python lan_chat.py server|client [host]")
        sys.exit(1)
    
    if sys.argv[1] == "server":
        server()
    elif sys.argv[1] == "client":
        host = sys.argv[2] if len(sys.argv) > 2 else "100.69.113.41"
        client(host)

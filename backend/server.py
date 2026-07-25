"""
Persistent Tailscale server for desktop-laptop communication.
Listens on 0.0.0.0:9999 for messages from laptop.
Writes received messages to inbox.txt, reads from outbox.txt to reply.
"""
import socket
import os
import time
import sys

HOST = '0.0.0.0'
PORT = 9999
INBOX = os.path.join(os.path.dirname(__file__), 'inbox.txt')
OUTBOX = os.path.join(os.path.dirname(__file__), 'outbox.txt')

def main():
    # Clear old inbox
    if os.path.exists(INBOX):
        os.remove(INBOX)
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)
    
    print(f"[SERVER] Listening on {HOST}:{PORT}", flush=True)
    
    while True:
        try:
            s.settimeout(10)
            conn, addr = s.accept()
            print(f"[SERVER] Connection from {addr}", flush=True)
            
            data = b''
            conn.settimeout(5)
            while True:
                try:
                    chunk = conn.recv(65536)
                    if not chunk:
                        break
                    data += chunk
                except socket.timeout:
                    break
            
            if data:
                msg = data.decode('utf-8', errors='replace')
                print(f"[SERVER] Received {len(msg)} chars:", flush=True)
                print(msg[:2000], flush=True)
                
                # Save to inbox
                with open(INBOX, 'w', encoding='utf-8') as f:
                    f.write(msg)
                print(f"[SERVER] Saved to {INBOX}", flush=True)
                
                # Check for outbox reply
                reply = ""
                if os.path.exists(OUTBOX):
                    with open(OUTBOX, 'r', encoding='utf-8') as f:
                        reply = f.read()
                    os.remove(OUTBOX)
                
                if not reply:
                    reply = f"ACK: received {len(msg)} bytes at {time.strftime('%H:%M:%S')}"
                
                conn.sendall(reply.encode('utf-8'))
                print(f"[SERVER] Sent reply: {reply[:200]}", flush=True)
            
            conn.close()
            
        except socket.timeout:
            continue
        except Exception as e:
            print(f"[SERVER] Error: {e}", flush=True)
            continue

if __name__ == "__main__":
    main()

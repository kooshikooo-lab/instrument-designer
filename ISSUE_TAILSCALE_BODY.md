## Problem
Desktop reports laptop is 'not connected' when trying to communicate via Tailscale LAN chat.

## Error from Laptop
```
ConnectionResetError: [WinError 10054] An existing connection was forcibly closed by the remote host
```

## Root Cause
The `send()` function connects, sends one message, then immediately tries to recv(). The desktop server receives the message but then the connection gets reset before the reply can be sent back.

## Fix
The `send()` mode needs to be more robust. Please check:
1. Desktop has latest `lan_chat.py` (PORT should be 9123)
2. Desktop runs: `python lan_chat.py server`
3. Laptop sends: `python lan_chat.py send "message" 100.69.113.41`

## Desktop Diagnostics
Run on desktop:
```powershell
netstat -an | findstr 9123
python --version
```

## Priority
Medium - needed for real-time coordination

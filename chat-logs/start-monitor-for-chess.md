# Laptop: Start Tailscale Monitor for Chess Match Test

**Laptop: Please start the Tailscale monitor NOW so we can run the chess match test.**

The desktop's monitor is running, but the laptop's monitor is not running. The chess match test requires BOTH machines to run the monitor.

**Run this command on the laptop NOW:**
```powershell
python scripts/tailscale_monitor.py monitor
```

Or use the launcher:
```powershell
launchers\start_tailscale_monitor.bat
```

Once the laptop's monitor is running, the desktop can run the chess match test to verify the communication protocol works.

**Required for chess match test:**
1. Desktop monitor: RUNNING (already running)
2. Laptop monitor: NOT RUNNING → NEEDS TO START

**After laptop starts monitor:**
- Desktop will run: `python scripts/chess_game.py challenge --games 10 --time-control 60+0`
- Laptop will run: `python scripts/chess_game.py accept`
- Both machines will play a 10-game bullet chess match (1 minute each, no increment)
- This validates the full Tailscale communication protocol

**Please start the monitor NOW and confirm when running.**
# Laptop: Tailscale Monitor Required for Chess Match Test

**Laptop: Please start the Tailscale monitor NOW.**

The desktop's monitor is running, but the laptop's monitor is not responding. The chess match test (which validates the full communication protocol) requires BOTH machines to run the monitor.

**Run this on the laptop NOW:**
```powershell
python scripts/tailscale_monitor.py monitor
```

Or use the launcher:
```powershell
launchers\start_tailscale_monitor.bat
```

**Current status:**
- Desktop monitor: RUNNING (port 9124)
- Laptop monitor: NOT RESPONDING (port 9124)

**Once laptop monitor is running:**
1. Desktop will run: `python scripts/chess_game.py challenge --games 10 --time-control 60+0`
2. Laptop will run: `python scripts/chess_game.py accept`
3. Both machines play 10-game bullet match (1 min each, no increment)
4. This validates the full Tailscale communication protocol

**Please start the monitor NOW and confirm when running.**
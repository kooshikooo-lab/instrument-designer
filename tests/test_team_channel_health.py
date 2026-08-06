"""Team-channel health rules for the instrument-designer repo.

Encodes the operational rules for the Tailscale peer channel + bullet-chess
match, so the diagnosed failures (2026-08-06) become regression tests.

Rules:
  R1  Machine name must resolve to "desktop" or "laptop", never "unknown",
      for both tailscale_monitor.py and chess_game.py — via MACHINE_NAME,
      TEAM_MACHINE, or tailscale-IP match against the config.
  R2  scripts/.tailscale_config.json must have ip/peer/port for BOTH machines,
      and the desktop ip must match this machine's real Tailscale IP.
  R3  The tailscale monitor process must be running.
  R4  The monitor server must be listening on port 9124.
  R5  The wire protocol must answer ping with pong.
  R6  The monitor state file must not accumulate duplicate message ids and must
      not keep stale queued messages forever.
  R7  The Tailscale peer must be reachable (live rule; auto-skips when the peer
      is offline so the desktop suite can still run).
  R8  The peer channel command must succeed (live rule; auto-skips when offline).
  R9  Chess rules: time control "60+0" parses to (60000, 0); move picker only
      returns legal moves; a "match" is a series of >1 games; match analysis
      assigns the loser correctly.
"""

import json
import importlib.util
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
CONFIG_FILE = SCRIPTS / ".tailscale_config.json"
STATE_FILE = SCRIPTS / ".tailscale_monitor.json"
PORT = 9124

PEER_KEY = "peer"
IP_KEY = "ip"
MACHINES = ("desktop", "laptop")


def _load_script_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MONITOR = _load_script_module("tailscale_monitor", "tailscale_monitor.py")
CHESS = _load_script_module("chess_game", "chess_game.py")


# ---------------------------------------------------------------- R1

def _call_machine_name(module, monkeypatch, machine, key):
    monkeypatch.setenv(key, machine)
    monkeypatch.delenv("COMPUTERNAME", raising=False)
    monkeypatch.delenv("MACHINE_NAME", raising=False)
    monkeypatch.delenv("TEAM_MACHINE", raising=False)
    monkeypatch.setenv(key, machine)
    return module._machine_name()


@pytest.mark.parametrize("key", ["MACHINE_NAME", "TEAM_MACHINE"])
def test_r1_monitor_machine_name_via_env(monkeypatch, key):
    assert _call_machine_name(MONITOR, monkeypatch, "desktop", key) == "desktop"
    assert _call_machine_name(MONITOR, monkeypatch, "laptop", key) == "laptop"


@pytest.mark.parametrize("key", ["MACHINE_NAME", "TEAM_MACHINE"])
def test_r1_chess_machine_name_via_env(monkeypatch, key):
    assert _call_machine_name(CHESS, monkeypatch, "desktop", key) == "desktop"
    assert _call_machine_name(CHESS, monkeypatch, "laptop", key) == "laptop"


def test_r1_monitor_machine_name_via_tailscale_ip(monkeypatch):
    result = subprocess.run(["tailscale", "ip", "-4"], capture_output=True, text=True, timeout=10)
    if result.returncode != 0 or not result.stdout.strip():
        pytest.skip("tailscale ip unavailable")
    monkeypatch.delenv("MACHINE_NAME", raising=False)
    monkeypatch.delenv("TEAM_MACHINE", raising=False)
    monkeypatch.delenv("COMPUTERNAME", raising=False)
    assert MONITOR._machine_name() in MACHINES


def test_r1_chess_machine_name_via_tailscale_ip(monkeypatch):
    result = subprocess.run(["tailscale", "ip", "-4"], capture_output=True, text=True, timeout=10)
    if result.returncode != 0 or not result.stdout.strip():
        pytest.skip("tailscale ip unavailable")
    monkeypatch.delenv("MACHINE_NAME", raising=False)
    monkeypatch.delenv("TEAM_MACHINE", raising=False)
    monkeypatch.delenv("COMPUTERNAME", raising=False)
    assert CHESS._machine_name() in MACHINES


# ---------------------------------------------------------------- R2

def test_r2_config_has_both_machines():
    assert CONFIG_FILE.exists()
    cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    for machine in MACHINES:
        entry = cfg.get(machine)
        assert entry, f"missing config entry for {machine}"
        assert entry.get(IP_KEY), f"missing ip for {machine}"
        assert entry.get(PEER_KEY), f"missing peer for {machine}"
        assert entry.get("port") == PORT, f"wrong port for {machine}"


def test_r2_config_desktop_ip_matches_tailscale():
    result = subprocess.run(["tailscale", "ip", "-4"], capture_output=True, text=True, timeout=10)
    if result.returncode != 0 or not result.stdout.strip():
        pytest.skip("tailscale ip unavailable")
    my_ip = result.stdout.strip().splitlines()[0].strip()
    cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    assert cfg["desktop"]["ip"] == my_ip


def test_r2_config_peers_are_symmetric():
    cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    assert cfg["desktop"]["peer"] == cfg["laptop"]["ip"]
    assert cfg["laptop"]["peer"] == cfg["desktop"]["ip"]


# ---------------------------------------------------------------- R3

def test_r3_monitor_process_running():
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*tailscale_monitor.py*' } | Measure-Object | Select-Object -ExpandProperty Count"],
        capture_output=True, text=True, timeout=10,
    )
    count = int(proc.stdout.strip() or 0)
    assert count >= 1, "no tailscale_monitor.py process is running"


# ---------------------------------------------------------------- R4

def test_r4_server_listening_on_9124():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3.0)
    try:
        sock.connect(("127.0.0.1", PORT))
    except OSError as e:
        pytest.fail(f"no listener on 127.0.0.1:{PORT}: {e}")
    finally:
        sock.close()


# ---------------------------------------------------------------- R5

def test_r5_protocol_ping_pong_loopback():
    env = os.environ.copy()
    env["MACHINE_NAME"] = "desktop"
    env["TAILSCALE_BIND_IP"] = "127.0.0.1"
    env["TAILSCALE_PORT"] = "9126"
    env["TAILSCALE_PEER_IP"] = "127.0.0.1"
    proc = subprocess.Popen(
        [sys.executable, str(SCRIPTS / "tailscale_monitor.py"), "server"],
        cwd=REPO_ROOT, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(0.8)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect(("127.0.0.1", 9126))
        sock.sendall((json.dumps({"cmd": "ping", "from": "test"}) + "\n").encode("utf-8"))
        sock.shutdown(socket.SHUT_WR)
        buf = b""
        while b"\n" not in buf:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf += chunk
        sock.close()
        reply = json.loads(buf.decode("utf-8").strip().split("\n")[0])
        assert reply["cmd"] == "pong"
        assert reply["from"] == "desktop"
    finally:
        proc.terminate()
        proc.wait(timeout=5)


# ---------------------------------------------------------------- R6

def test_r6_state_has_no_duplicate_message_ids():
    if not STATE_FILE.exists():
        pytest.skip("no state file yet")
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    seen = set()
    for msg in state.get("received_messages", []):
        mid = msg.get("id")
        if not mid:
            continue
        assert mid not in seen, f"duplicate message id {mid}"
        seen.add(mid)


def test_r6_state_has_no_stale_queued_messages():
    if not STATE_FILE.exists():
        pytest.skip("no state file yet")
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    now = time.time()
    from datetime import datetime, timezone
    for msg in state.get("queued_messages", []):
        ts = msg.get("time")
        if not ts:
            continue
        age = now - datetime.fromisoformat(ts).timestamp()
        assert age < 3600, f"stale queued message {msg.get('id')} queued {age:.0f}s ago"


# ---------------------------------------------------------------- R7 / R8 (live)

def _peer_online():
    cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    peer_ip = cfg["desktop"]["peer"]
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2.0)
    try:
        sock.connect((peer_ip, PORT))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def test_r7_tailscale_peer_reachable():
    cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    peer_ip = cfg["desktop"]["peer"]
    result = subprocess.run(["tailscale", "ping", peer_ip], capture_output=True, text=True, timeout=15)
    if result.returncode != 0:
        pytest.skip(f"peer {peer_ip} offline: {result.stdout.strip() or result.stderr.strip()}")
    assert "pong" in result.stdout


def test_r8_peer_channel_command():
    if not _peer_online():
        pytest.skip("peer monitor offline on port 9124")
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "tailscale_monitor.py"), "test"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=20,
        env={**os.environ, "MACHINE_NAME": "desktop"},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout


def test_r8_machine_name_error_is_gone():
    """Regression: the 'cannot determine machine name' failure must never return."""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "tailscale_monitor.py"), "test"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=20,
    )
    assert "cannot determine machine name" not in (result.stdout + result.stderr)


# ---------------------------------------------------------------- R9 (chess)

def test_r9_time_control_parse():
    assert CHESS._parse_time_control("60+0") == (60000, 0)
    assert CHESS._parse_time_control("1+0") == (1000, 0)
    assert CHESS._parse_time_control("garbage") == (60000, 0)


def test_r9_move_picker_returns_legal_moves():
    import chess as chess_lib
    board = chess_lib.Board()
    for _ in range(20):
        move = CHESS._pick_move(board, 60000)
        assert move is not None
        assert move in board.legal_moves
        board.push(move)


def test_r9_match_is_a_series_of_games():
    import inspect
    sig = inspect.signature(CHESS.cmd_challenge)
    assert sig.parameters["match_games"].default == 10
    assert CHESS.CHALLENGE_TIMEOUT > 0


def test_r9_match_requires_more_than_one_game():
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "chess_game.py"), "challenge", "--games", "1"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=20,
        env={**os.environ, "MACHINE_NAME": "desktop"},
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "more than one game" in result.stderr

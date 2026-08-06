"""Bullet chess match over the Tailscale peer channel (UCI notation).

This is a stress test of the Tailscale instant-messaging channel. A 10-game
match is played with a fixed time control (default 1 minute each, no increment).
The challenger plays White. The challengee must accept within 20 seconds or
forfeit the game.

Usage:
    python scripts/chess_game.py challenge            # desktop challenges laptop
    python scripts/chess_game.py accept               # wait for a challenge and play

Protocol (all payloads are JSON sent via tailscale_monitor.py send/mag):
    challenge: {"cmd": "chess_challenge", "match_games": 10, "time_control": "60+0", "game": 1}
    accept:    {"cmd": "chess_accept", "game": 1}
    move:      {"cmd": "chess_move", "game": N, "move": "e2e4", "white_ms": 60000, "black_ms": 60000}
    forfeit:   {"cmd": "chess_forfeit", "game": N, "reason": "timeout"}
    result:    {"cmd": "chess_result", "game": N, "result": "1-0", "reason": "checkmate"}
"""

import argparse
import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import chess
except ImportError as e:
    print("ERROR: python-chess is required. Install with: pip install python-chess", file=sys.stderr)
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = REPO_ROOT / "scripts" / ".tailscale_config.json"
STATE_FILE = REPO_ROOT / "scripts" / ".tailscale_monitor.json"

CHALLENGE_TIMEOUT = 20.0  # seconds to accept a challenge
MOVE_POLL_INTERVAL = 0.2  # seconds

# 10 minutes for games + 20s abort window + 20s grace.
# Override with CHESS_MATCH_BUDGET_SECONDS for testing.
MATCH_TOTAL_SECONDS = int(os.environ.get("CHESS_MATCH_BUDGET_SECONDS", 600 + 20 + 20))


def _machine_name():
    env = os.environ.get("MACHINE_NAME", "").strip().lower()
    if env in ("desktop", "laptop"):
        return env
    host = os.environ.get("COMPUTERNAME", "").lower()
    if "desktop" in host:
        return "desktop"
    if "laptop" in host:
        return "laptop"
    return "unknown"


def _load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return None


def _resolve_peer():
    machine = _machine_name()
    if machine == "unknown":
        print("ERROR: cannot determine machine name. Set MACHINE_NAME=desktop or laptop.", file=sys.stderr)
        sys.exit(1)

    peer_ip = os.environ.get("TAILSCALE_PEER_IP", "")
    port_env = os.environ.get("TAILSCALE_PORT", "")

    if not peer_ip or not port_env:
        cfg = _load_config()
        if cfg is None:
            print(f"ERROR: config not found at {CONFIG_FILE}", file=sys.stderr)
            sys.exit(1)
        entry = cfg.get(machine)
        if not entry:
            print(f"ERROR: no config entry for machine '{machine}'", file=sys.stderr)
            sys.exit(1)
        peer_ip = peer_ip or entry.get("peer", "")
        port_env = port_env or str(entry.get("port", 9124))

    return peer_ip, int(port_env)


def _post_to_team_channel(body):
    """Post a message to GitHub Discussion #23 via team_chat.py."""
    env = os.environ.copy()
    env.setdefault("TEAM_MACHINE", _machine_name())
    msg_path = REPO_ROOT / "scripts" / ".chess_match_post.md"
    try:
        with open(msg_path, "w", encoding="utf-8") as f:
            f.write(body)
        result = subprocess.run(
            [sys.executable, "scripts/team_chat.py", "post", "--file", str(msg_path)],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            print(result.stdout.strip())
        else:
            print(f"Failed to post to team channel: {result.stderr}", file=sys.stderr)
    except Exception as e:
        print(f"Failed to post to team channel: {e}", file=sys.stderr)
    finally:
        try:
            msg_path.unlink()
        except Exception:
            pass


def _send_payload(peer_ip, port, payload):
    """Send a JSON payload via tailscale_monitor.py send."""
    env = os.environ.copy()
    env["MACHINE_NAME"] = _machine_name()
    env["TAILSCALE_PEER_IP"] = peer_ip
    env["TAILSCALE_PORT"] = str(port)
    result = subprocess.run(
        [sys.executable, "scripts/tailscale_monitor.py", "send", json.dumps(payload)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return result.returncode == 0 and "delivered" in (result.stdout + result.stderr)


def _read_chess_messages(from_peer_only=True):
    """Read chess-protocol messages from the tailscale monitor state file."""
    if not STATE_FILE.exists():
        return []
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    me = _machine_name()
    messages = []
    for msg in state.get("received_messages", []):
        text = msg.get("text", "")
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            continue
        if obj.get("cmd", "").startswith("chess"):
            if from_peer_only and obj.get("from", "") == me:
                continue
            messages.append(obj)
    return messages


def _wait_for_message(peer_ip, port, predicate, timeout, last_count=0):
    """Poll until a message matching predicate arrives. Returns message or None."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        messages = _read_chess_messages(from_peer_only=True)
        for msg in messages[last_count:]:
            if predicate(msg):
                return msg
        last_count = max(last_count, len(messages))
        time.sleep(MOVE_POLL_INTERVAL)
    return None


def _clear_chess_messages():
    if not STATE_FILE.exists():
        return
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
        state["received_messages"] = [
            m for m in state.get("received_messages", [])
            if not (m.get("text", "").startswith('{"cmd": "chess'))
        ]
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except (json.JSONDecodeError, OSError):
        pass


def _print_board(board, white_ms, black_ms, side_names):
    print("\n" + "=" * 40)
    print(f" {side_names['white']:>8} (White) {white_ms/1000:.1f}s")
    print(f" {side_names['black']:>8} (Black) {black_ms/1000:.1f}s")
    print("=" * 40)
    print(str(board))
    print("=" * 40)


def _pick_move(board, time_ms):
    """Greedy move picker: captures first, then checks, then random."""
    legal = list(board.legal_moves)
    if not legal:
        return None
    captures = [m for m in legal if board.is_capture(m)]
    if captures:
        return random.choice(captures)
    checks = [m for m in legal if board.gives_check(m)]
    if checks:
        return random.choice(checks)
    return random.choice(legal)


def _parse_time_control(tc):
    """Parse '60+0' into (ms_per_side, increment_ms)."""
    try:
        base, inc = tc.split("+")
        return int(base) * 1000, int(inc) * 1000
    except ValueError:
        return 60000, 0


def _play_game(peer_ip, port, game_num, time_control, my_color, side_names, start_fen=None, match_deadline=None):
    """Play one bullet game. Returns result string (e.g. '1-0')."""
    base_ms, inc_ms = _parse_time_control(time_control)
    white_ms = base_ms
    black_ms = base_ms
    board = chess.Board(start_fen) if start_fen else chess.Board()
    _print_board(board, white_ms, black_ms, side_names)

    # Clear opponent chess messages before the game starts.
    msg_count = len(_read_chess_messages(from_peer_only=True))

    while not board.is_game_over():
        if match_deadline is not None and time.time() >= match_deadline:
            print(f"[{_machine_name()}] Game {game_num}: match budget expired.")
            return "*"

        is_my_turn = (board.turn == my_color)
        side_str = "White" if board.turn == chess.WHITE else "Black"

        if is_my_turn:
            move_start = time.time()
            move = _pick_move(board, white_ms if board.turn == chess.WHITE else black_ms)
            if move is None:
                break
            elapsed_ms = int((time.time() - move_start) * 1000)
            if board.turn == chess.WHITE:
                white_ms = max(0, white_ms - elapsed_ms)
            else:
                black_ms = max(0, black_ms - elapsed_ms)
            if board.turn == chess.WHITE:
                white_ms += inc_ms
            else:
                black_ms += inc_ms
            if white_ms <= 0 or black_ms <= 0:
                print(f"Time forfeit: {side_str} ran out of time")
                return "0-1" if board.turn == chess.WHITE else "1-0"

            board.push(move)
            uci = move.uci()
            payload = {
                "cmd": "chess_move",
                "game": game_num,
                "move": uci,
                "white_ms": white_ms,
                "black_ms": black_ms,
                "from": _machine_name(),
            }
            if not _send_payload(peer_ip, port, payload):
                print(f"FAILED to send move to {peer_ip}:{port}")
                return "*"
            print(f"[{_machine_name()}] Game {game_num}: {side_str} plays {uci}")
        else:
            opponent = side_names["black"] if board.turn == chess.BLACK else side_names["white"]
            remaining_ms = black_ms if board.turn == chess.BLACK else white_ms
            print(f"[{_machine_name()}] Game {game_num}: waiting for {opponent} ({side_str})...")

            def is_game_move(msg):
                return msg.get("cmd") == "chess_move" and msg.get("game") == game_num

            move_timeout = remaining_ms / 1000.0 + 0.5
            if match_deadline is not None:
                move_timeout = min(move_timeout, match_deadline - time.time())

            wait_start = time.time()
            msg = _wait_for_message(peer_ip, port, is_game_move, move_timeout, msg_count)
            elapsed_ms = int((time.time() - wait_start) * 1000)

            if msg is None:
                if match_deadline is not None and time.time() >= match_deadline:
                    print(f"[{_machine_name()}] Game {game_num}: match budget expired while waiting.")
                    return "*"
                print(f"[{_machine_name()}] Game {game_num}: {opponent} did not reply in time.")
                return "1-0" if board.turn == chess.WHITE else "0-1"

            msg_count = len(_read_chess_messages(from_peer_only=True))

            # Update clocks from the opponent's message. Their own clock already
            # reflects the time they spent thinking. Network delay is *not* charged
            # to either side; the waiting side uses its own local clock.
            white_ms = msg.get("white_ms", white_ms)
            black_ms = msg.get("black_ms", black_ms)
            if (board.turn == chess.WHITE and white_ms <= 0) or (board.turn == chess.BLACK and black_ms <= 0):
                print(f"[{_machine_name()}] Game {game_num}: {opponent} ran out of time.")
                return "0-1" if board.turn == chess.WHITE else "1-0"

            uci = msg.get("move", "")
            try:
                move = board.parse_uci(uci)
                if move not in board.legal_moves:
                    print(f"[{_machine_name()}] Game {game_num}: illegal move {uci}")
                    return "1-0" if board.turn == chess.WHITE else "0-1"
            except ValueError:
                print(f"[{_machine_name()}] Game {game_num}: invalid UCI {uci}")
                return "1-0" if board.turn == chess.WHITE else "0-1"

            board.push(move)
            print(f"[{_machine_name()}] Game {game_num}: {opponent} ({side_str}) plays {uci} (waited {elapsed_ms}ms)")

        _print_board(board, white_ms, black_ms, side_names)

    result = board.result()
    print(f"Game {game_num} over: {result}")
    _send_payload(peer_ip, port, {
        "cmd": "chess_result",
        "game": game_num,
        "result": result,
        "from": _machine_name(),
    })
    return result


def cmd_challenge(peer_ip, port, match_games=10, time_control="60+0"):
    """Desktop challenges laptop to a match (one challenge per game, sequential)."""
    side_names = {"white": _machine_name(), "black": "opponent"}
    my_color = chess.WHITE
    scores = {"1-0": 0, "0-1": 0, "1/2-1/2": 0, "*": 0}
    games_played = 0
    match_aborted = False
    both_failed = False
    match_start = time.time()
    match_deadline = match_start + MATCH_TOTAL_SECONDS

    print(f"\n### Match: {match_games} games, {time_control}, total budget {MATCH_TOTAL_SECONDS}s ###")

    for game_num in range(1, match_games + 1):
        remaining_budget = match_deadline - time.time()
        if remaining_budget <= 0:
            print(f"[{_machine_name()}] Match budget expired ({MATCH_TOTAL_SECONDS}s elapsed).")
            if games_played == 0:
                print("No games were played. Both sides fail.")
                both_failed = True
            else:
                print(f"{games_played} games played; match stopped.")
            break

        print(f"\n### Game {game_num}/{match_games} ###")
        print(f"[{_machine_name()}] Challenging {peer_ip}:{port} to {time_control}")

        _clear_chess_messages()
        challenge = {
            "cmd": "chess_challenge",
            "match_games": match_games,
            "time_control": time_control,
            "game": game_num,
            "from": _machine_name(),
        }
        if not _send_payload(peer_ip, port, challenge):
            print(f"[{_machine_name()}] Challenge failed to deliver. Aborting match — monitoring is not working.")
            scores["*"] += (match_games - game_num + 1)
            match_aborted = True
            break

        challenge_timeout = min(CHALLENGE_TIMEOUT, match_deadline - time.time())
        if challenge_timeout <= 0:
            print(f"[{_machine_name()}] Match budget expired during challenge.")
            if games_played == 0:
                print("No games were played. Both sides fail.")
                both_failed = True
            break

        def is_accept(msg):
            return msg.get("cmd") == "chess_accept" and msg.get("game") == game_num

        accept = _wait_for_message(peer_ip, port, is_accept, challenge_timeout, 0)
        if accept is None:
            print(f"[{_machine_name()}] No acceptance within {CHALLENGE_TIMEOUT}s. Win game {game_num} by forfeit.")
            scores["1-0"] += 1
            games_played += 1
            continue

        print(f"[{_machine_name()}] Challenge accepted for game {game_num}. Playing White.")
        result = _play_game(peer_ip, port, game_num, time_control, my_color, side_names, match_deadline=match_deadline)
        scores[result] = scores.get(result, 0) + 1
        if result != "*":
            games_played += 1

    if both_failed:
        print(f"\n### Match failed: no games played within {MATCH_TOTAL_SECONDS}s ###")
    elif match_aborted:
        print(f"\n### Match aborted at game {game_num}/{match_games} ###")
    else:
        print(f"\n### Match result ({match_games} games) ###")
    for k, v in scores.items():
        print(f"  {k}: {v}")
    print(f"  games_played: {games_played}")

    _analyze_match(peer_ip, port, match_games, time_control, scores, side_names,
                   aborted=match_aborted, aborted_at=game_num, both_failed=both_failed, games_played=games_played)


def _analyze_match(peer_ip, port, match_games, time_control, scores, side_names, aborted=False, aborted_at=0, both_failed=False, games_played=0):
    """If the loser is the local machine, propose improvements.

    If the loser is the remote machine, post a failure analysis to the team
    channel so the remote side can improve.
    """
    my_name = _machine_name()
    opponent = "opponent"
    wins = scores.get("1-0", 0)
    losses = scores.get("0-1", 0)
    draws = scores.get("1/2-1/2", 0)
    forfeits = scores.get("*", 0)

    # For this match, the local player is White (challenger), so wins = 1-0.
    # Forfeits (scores['*']) mean the opponent failed to respond, so they are losses for the opponent.
    if forfeits > 0 or losses > wins:
        loser = opponent
    elif wins > losses:
        loser = my_name
    else:
        loser = "draw"

    analysis = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "match_games": match_games,
        "time_control": time_control,
        "scores": scores,
        "loser": loser,
        "observation": "",
        "improvements": [],
    }

    if both_failed:
        analysis["observation"] = (
            f"Match budget ({MATCH_TOTAL_SECONDS}s) expired with no games played. "
            "Both sides failed to establish a working Tailscale channel."
        )
        analysis["improvements"] = [
            "Both machines must pull the latest opencode/main/desktop.",
            "Both machines must run `python scripts/tailscale_monitor.py configure`.",
            "Both machines must start the monitor before the rematch.",
            "Verify both Tailscale IPs are correct and reachable.",
            "Add a lightweight UDP beacon or TCP keep-alive as a backup channel.",
        ]
        loser = "both"
    elif aborted:
        analysis["observation"] = (
            f"Match aborted at game {aborted_at}: "
            "the challenge could not be delivered to the peer. "
            "The monitoring channel is not working."
        )
        analysis["improvements"] = [
            "Ensure the laptop has pulled the latest opencode/main/desktop.",
            "Run `python scripts/tailscale_monitor.py configure` on the laptop.",
            "Start the monitor via launchers/start_tailscale_monitor.bat on the laptop.",
            "Verify the laptop's Tailscale IP is reachable from the desktop.",
            "Add a lightweight UDP beacon or TCP keep-alive as a backup channel.",
        ]
    elif forfeits > 0:
        analysis["observation"] = (
            f"{forfeits} games were forfeited because the opponent did not accept "
            f"a challenge or reply within the time limit."
        )
        analysis["improvements"] = [
            "Ensure tailscale_monitor.py is running in monitor mode (server + heartbeat).",
            "Start the monitor via launchers/start_tailscale_monitor.bat before the match.",
            "Reduce heartbeat interval and add a notify command so the peer wakes up faster.",
            "Add a lightweight UDP beacon or TCP keep-alive as a backup channel.",
        ]
    elif losses > wins:
        analysis["observation"] = "Lost on the board. Engine needs better move selection."
        analysis["improvements"] = [
            "Replace greedy move picker with a shallow minimax or search.",
            "Add opening book to avoid blunders in the first moves.",
            "Use time management to spend more time in critical positions.",
        ]
    elif wins > losses:
        analysis["observation"] = "Won the match. No improvements required from this side."
    else:
        analysis["observation"] = "Match was drawn. Consider sharper openings next time."

    report_path = REPO_ROOT / "scripts" / "chess_match_analysis.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)
    print(f"\nMatch analysis saved to {report_path}")
    print(json.dumps(analysis, indent=2))

    if loser == opponent:
        # Post the failure analysis to the team channel so the laptop can improve.
        body = (
            f"## Chess match result: {my_name} won {wins}-{losses} (draws {draws}, forfeits {forfeits})\n\n"
            f"{analysis['observation']}\n\n"
            "Suggested improvements for the losing side:\n" +
            "\n".join(f"- {imp}" for imp in analysis["improvements"]) +
            "\n\nNext match: please run `python scripts/chess_game.py accept` "
            "and start the Tailscale monitor first."
        )
        print(f"\n[{my_name}] Sending analysis to peer...")
        # Also try to send via Tailscale in case the peer is actually up.
        _send_payload(peer_ip, port, {
            "cmd": "chess_match_analysis",
            "text": body,
            "from": my_name,
        })
        _post_to_team_channel(body)
    elif loser == my_name:
        print(f"\n[{my_name}] I lost the match. Analysis saved locally; implement the improvements before the next match.")


def cmd_accept(peer_ip, port):
    """Wait for challenges, accept each game, and play Black."""
    print(f"[{_machine_name()}] Waiting for chess challenges from {peer_ip}:{port}...")
    msg_count = len(_read_chess_messages(from_peer_only=True))

    while True:
        def is_challenge(msg):
            return msg.get("cmd") == "chess_challenge"

        challenge = _wait_for_message(peer_ip, port, is_challenge, 3600, msg_count)
        if challenge is None:
            print("No challenge received in the last hour. Exiting.")
            return

        msg_count = len(_read_chess_messages(from_peer_only=True))
        game_num = challenge.get("game", 1)
        match_games = challenge.get("match_games", 1)
        time_control = challenge.get("time_control", "60+0")

        print(f"[{_machine_name()}] Accepted game {game_num}/{match_games}")
        _send_payload(peer_ip, port, {
            "cmd": "chess_accept",
            "game": game_num,
            "from": _machine_name(),
        })

        side_names = {"white": "opponent", "black": _machine_name()}
        _play_game(peer_ip, port, game_num, time_control, chess.BLACK, side_names)


def main():
    parser = argparse.ArgumentParser(description="Bullet chess match over Tailscale")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_challenge = sub.add_parser("challenge", help="challenge the laptop to a 10-game bullet match")
    p_challenge.add_argument("--games", type=int, default=10, help="number of games in the match")
    p_challenge.add_argument("--time-control", default="60+0", help="time control in seconds+increment")
    sub.add_parser("accept", help="wait for and accept a challenge")
    args = parser.parse_args()

    peer_ip, port = _resolve_peer()

    if args.cmd == "challenge":
        cmd_challenge(peer_ip, port, match_games=args.games, time_control=args.time_control)
    elif args.cmd == "accept":
        cmd_accept(peer_ip, port)


if __name__ == "__main__":
    main()

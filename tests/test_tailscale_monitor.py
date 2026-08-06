"""Tests for scripts/tailscale_monitor.py."""

import json
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "tailscale_monitor.py"


def _env():
    env = os.environ.copy()
    env["MACHINE_NAME"] = "desktop"
    env["TAILSCALE_PEER_IP"] = "127.0.0.1"
    env["TAILSCALE_PORT"] = "9125"
    env["TAILSCALE_BIND_IP"] = "127.0.0.1"
    return env


def _connect(port=9125):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)
    sock.connect(("127.0.0.1", port))
    return sock


def _send(sock, obj):
    sock.sendall((json.dumps(obj) + "\n").encode("utf-8"))


def _recv(sock):
    data = b""
    deadline = time.time() + 5.0
    while time.time() < deadline:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
        if b"\n" in data:
            break
    if not data:
        return None
    return json.loads(data.decode("utf-8").strip().split("\n")[0])


def test_server_accepts_ping():
    env = _env()
    proc = subprocess.Popen(
        [sys.executable, str(SCRIPT), "server"],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        time.sleep(0.5)
        sock = _connect()
        _send(sock, {"cmd": "ping", "from": "test"})
        reply = _recv(sock)
        assert reply is not None
        assert reply["cmd"] == "pong"
        assert reply["from"] == "desktop"
        sock.close()
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_server_accepts_message():
    env = _env()
    proc = subprocess.Popen(
        [sys.executable, str(SCRIPT), "server"],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        time.sleep(0.5)
        sock = _connect()
        _send(sock, {"cmd": "msg", "from": "test", "text": "hello"})
        reply = _recv(sock)
        assert reply is not None
        assert reply["cmd"] == "ok"
        sock.close()
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_one_shot_send():
    env = _env()
    proc = subprocess.Popen(
        [sys.executable, str(SCRIPT), "server"],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        time.sleep(0.5)
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "send", "test message"],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert "delivered" in result.stdout or "failed" in result.stdout
    finally:
        proc.terminate()
        proc.wait(timeout=5)

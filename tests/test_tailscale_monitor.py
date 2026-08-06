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


def _recv(sock, buf):
    deadline = time.time() + 5.0
    while time.time() < deadline:
        if "\n" in buf:
            line, buf = buf.split("\n", 1)
            return line, buf
        chunk = sock.recv(4096).decode("utf-8")
        if not chunk:
            break
        buf += chunk
    return None, buf


def test_server_accepts_connection():
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
        sock.close()
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_ping_pong():
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
        line, _ = _recv(sock, "")
        assert line is not None
        obj = json.loads(line)
        assert obj["cmd"] == "pong"
        assert obj["from"] == "desktop"
        sock.close()
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_message_and_ack():
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
        _send(sock, {"cmd": "msg", "id": "m1", "from": "test", "text": "hello"})
        line, _ = _recv(sock, "")
        assert line is not None
        obj = json.loads(line)
        assert obj["cmd"] == "ack"
        assert obj["id"] == "m1"
        sock.close()
    finally:
        proc.terminate()
        proc.wait(timeout=5)

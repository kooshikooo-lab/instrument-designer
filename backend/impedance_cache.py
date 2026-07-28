"""
Shared impedance cache for parallel workers.

Uses SQLite for process-safe caching across Windows spawn workers.
Each worker opens the same DB; reads/writes are serialized by SQLite.
"""
import os
import json
import sqlite3
import threading
import tempfile
from pathlib import Path

_CACHE_CONN: sqlite3.Connection | None = None
_CACHE_LOCK = threading.Lock()
_DB_PATH: str | None = None


def _get_db_path() -> str:
    global _DB_PATH
    if _DB_PATH is None:
        _DB_PATH = os.path.join(tempfile.gettempdir(), "impedance_cache.sqlite")
    return _DB_PATH


def _get_conn() -> sqlite3.Connection:
    global _CACHE_CONN
    if _CACHE_CONN is None:
        db_path = _get_db_path()
        _CACHE_CONN = sqlite3.connect(db_path, timeout=30)
        _CACHE_CONN.execute(
            "CREATE TABLE IF NOT EXISTS cache (hash TEXT PRIMARY KEY, data TEXT)"
        )
        _CACHE_CONN.commit()
    return _CACHE_CONN


def cache_get(cache_hash: str) -> dict | None:
    try:
        conn = _get_conn()
        cursor = conn.execute("SELECT data FROM cache WHERE hash = ?", (cache_hash,))
        row = cursor.fetchone()
        if row is not None:
            return json.loads(row[0])
    except Exception:
        pass
    return None


def cache_set(cache_hash: str, data: dict):
    try:
        conn = _get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO cache (hash, data) VALUES (?, ?)",
            (cache_hash, json.dumps(data, default=_json_fallback)),
        )
        conn.commit()
    except Exception:
        pass


def cache_size() -> int:
    try:
        conn = _get_conn()
        cursor = conn.execute("SELECT COUNT(*) FROM cache")
        return cursor.fetchone()[0]
    except Exception:
        return 0


def cache_clear():
    try:
        conn = _get_conn()
        conn.execute("DELETE FROM cache")
        conn.commit()
    except Exception:
        pass


def _json_fallback(obj):
    if hasattr(obj, "tolist"):
        return obj.tolist()
    if hasattr(obj, "__float__"):
        return float(obj)
    return str(obj)

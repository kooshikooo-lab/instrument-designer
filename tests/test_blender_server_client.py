"""Tests for the Blender addon's stdlib-only HTTP client.

`server_client` must work inside Blender's bundled Python (no pip packages),
so it is tested purely against monkeypatched `urllib.request.urlopen` — no
live server, no requests library.
"""
import io
import importlib.util
import json
import os
import sys
from urllib.error import HTTPError

import pytest

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# server_client.py is bpy-free (stdlib only). Load it standalone so the test
# runs in a host Python that has no Blender; importing blender_addon as a
# package would pull __init__.py which requires bpy.
_spec = importlib.util.spec_from_file_location(
    "blender_addon_server_client",
    os.path.join(_root, "blender_addon", "server_client.py"),
)
server_client = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(server_client)

ServerError = server_client.ServerError


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200):
        self._body = body
        self.status = status

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _http_error(code: int, body: bytes) -> HTTPError:
    return HTTPError("http://test", code, f"HTTP {code}", {}, io.BytesIO(body))


def _patch_urlopen(monkeypatch, return_value):
    captured = {}

    def fake_urlopen(req_or_url, timeout=30):
        captured["req"] = req_or_url
        captured["timeout"] = timeout
        if isinstance(return_value, Exception):
            raise return_value
        return return_value

    monkeypatch.setattr(server_client.urllib.request, "urlopen", fake_urlopen)
    return captured


def test_get_json_parses_response(monkeypatch):
    _patch_urlopen(monkeypatch, FakeResponse(b'{"status": "ok"}'))
    assert server_client.get_json("http://127.0.0.1:8000/health") == {"status": "ok"}


def test_get_json_wraps_http_error(monkeypatch):
    _patch_urlopen(monkeypatch, _http_error(404, b'{"detail": "nope"}'))
    with pytest.raises(ServerError) as ei:
        server_client.get_json("http://127.0.0.1:8000/nope")
    assert "404" in str(ei.value)
    assert "nope" in str(ei.value)


def test_get_json_wraps_network_error(monkeypatch):
    _patch_urlopen(monkeypatch, OSError("connection refused"))
    with pytest.raises(ServerError):
        server_client.get_json("http://127.0.0.1:8000/health")


def test_post_bytes_sends_json_request(monkeypatch):
    captured = _patch_urlopen(monkeypatch, FakeResponse(b"stl-bytes"))
    out = server_client.post_bytes(
        "http://127.0.0.1:8000/export/cadquery", {"preset": "koncovka_C"}
    )
    assert out == b"stl-bytes"

    req = captured["req"]
    assert req.method == "POST"
    assert req.full_url == "http://127.0.0.1:8000/export/cadquery"
    assert any(v == "application/json" for v in req.headers.values())
    assert json.loads(req.data) == {"preset": "koncovka_C"}


def test_post_bytes_wraps_http_error(monkeypatch):
    _patch_urlopen(monkeypatch, _http_error(500, b"boom"))
    with pytest.raises(ServerError) as ei:
        server_client.post_bytes("http://x/export/cadquery", {})
    assert "500" in str(ei.value)
    assert "boom" in str(ei.value)


def test_base_url_handles_trailing_slash(monkeypatch):
    captured = _patch_urlopen(monkeypatch, FakeResponse(b'{"status": "ok"}'))
    server_client.health("http://127.0.0.1:8000/")
    assert captured["req"] == "http://127.0.0.1:8000/health"


def test_health_and_instrument_endpoints(monkeypatch):
    captured = _patch_urlopen(
        monkeypatch, FakeResponse(b'{"status": "ok", "version": "2.0.0"}')
    )
    info = server_client.health("http://127.0.0.1:8000")
    assert info["status"] == "ok"
    assert captured["req"] == "http://127.0.0.1:8000/health"

    captured = _patch_urlopen(
        monkeypatch, FakeResponse(b'{"koncovka_C": {}}')
    )
    assert server_client.list_cadquery_instruments("http://127.0.0.1:8000") == {
        "koncovka_C": {}
    }
    assert captured["req"] == "http://127.0.0.1:8000/export/cadquery/instruments"


def test_fetch_instrument_stl_posts_preset(monkeypatch):
    captured = _patch_urlopen(monkeypatch, FakeResponse(b"solid x"))
    out = server_client.fetch_instrument_stl("http://127.0.0.1:8000", "pvc_flute_D")
    assert out == b"solid x"
    assert json.loads(captured["req"].data) == {"preset": "pvc_flute_D"}
    assert captured["req"].full_url == "http://127.0.0.1:8000/export/cadquery"

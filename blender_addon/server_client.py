"""HTTP client for the Instrument Designer design_server.

Uses only the standard library (urllib) so it works inside Blender's bundled
Python without pip-installing anything.
"""

import json
import urllib.error
import urllib.request

DEFAULT_TIMEOUT = 30


class ServerError(Exception):
    pass


def _base(url: str) -> str:
    return (url or "http://127.0.0.1:8000").rstrip("/")


def get_json(url: str, timeout: int = DEFAULT_TIMEOUT):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:500]
        raise ServerError(f"HTTP {e.code}: {body}")
    except Exception as e:  # noqa: BLE001 - surface any network failure to the user
        raise ServerError(str(e))


def post_bytes(url: str, payload: dict, timeout: int = DEFAULT_TIMEOUT) -> bytes:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:500]
        raise ServerError(f"HTTP {e.code}: {body}")
    except Exception as e:  # noqa: BLE001
        raise ServerError(str(e))


def health(url: str):
    return get_json(_base(url) + "/health")


def list_cadquery_instruments(url: str):
    return get_json(_base(url) + "/export/cadquery/instruments")


def fetch_instrument_stl(url: str, preset: str) -> bytes:
    return post_bytes(_base(url) + "/export/cadquery", {"preset": preset})

"""
HTTP client for the remote Instrument Designer compute server.
Drops in as a replacement for DemakeinDesigner with the same interface.
"""
import os
import io
import time
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Callable
import requests

from .demakein_wrapper import DesignResult


class RemoteDesigner:
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url.rstrip("/")
        self._session = requests.Session()

    def design(
        self,
        preset: str,
        transpose: int = 0,
        output_dir: Optional[str] = None,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> DesignResult:
        if not output_dir:
            output_dir = os.path.join(tempfile.gettempdir(), f"remote_{preset}")

        resp = self._session.post(
            f"{self.server_url}/design",
            json={"preset": preset, "transpose": transpose},
            timeout=30,
        )
        resp.raise_for_status()
        job_id = resp.json()["job_id"]

        if on_progress:
            on_progress(f"Submitted job {job_id} to server...")

        last_idx = 0
        while True:
            status = self._session.get(
                f"{self.server_url}/design/{job_id}/status", timeout=30
            )
            status.raise_for_status()
            data = status.json()

            progress = data.get("progress", [])
            for msg in progress[last_idx:]:
                if on_progress:
                    on_progress(msg)
            last_idx = len(progress)

            if data["status"] in ("completed", "failed"):
                result_data = data.get("result", {}) or {}
                stl_files = []
                if result_data.get("success"):
                    stl_files = self._download_stls(
                        job_id, output_dir, result_data.get("stl_files", [])
                    )
                return DesignResult(
                    output_dir=output_dir,
                    ident=result_data.get("ident", ""),
                    stl_files=stl_files,
                    log=result_data.get("log", ""),
                    success=result_data.get("success", False),
                )

            time.sleep(1)

    def _download_stls(self, job_id: str, output_dir: str, stl_names: list[str]) -> list[str]:
        resp = self._session.get(
            f"{self.server_url}/design/{job_id}/download", timeout=120
        )
        resp.raise_for_status()
        os.makedirs(output_dir, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            zf.extractall(output_dir)
        return [str(p) for p in Path(output_dir).rglob("*.stl")]

    def health(self) -> bool:
        try:
            resp = self._session.get(f"{self.server_url}/health", timeout=10)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def list_presets(self) -> dict[str, str]:
        resp = self._session.get(f"{self.server_url}/presets", timeout=10)
        resp.raise_for_status()
        return resp.json().get("presets", {})

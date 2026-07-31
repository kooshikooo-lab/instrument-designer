"""
Design job routes.
"""
import os
import uuid
import threading
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..shared_state import get_app, get_jobs, get_lock

router = APIRouter()

app = get_app()
_jobs = get_jobs()
_lock = get_lock()


class DesignRequest(BaseModel):
    preset: str
    transpose: int = 0
    quick: bool = True


@router.post("/")
def start_design(req: DesignRequest):
    job_id = str(uuid.uuid4())[:8]
    with _lock:
        _jobs[job_id] = {"status": "queued", "progress": [], "result": None}

    def run():
        try:
            with _lock:
                _jobs[job_id]["status"] = "running"
                _jobs[job_id]["progress"] = ["Starting design..."]

            from woodwind_designer.engine.demakein_wrapper import DemakeinDesigner
            designer = DemakeinDesigner()
            family, sub = designer.find_preset_category(req.preset)
            if not family:
                raise ValueError(f"Preset {req.preset} not found")

            with _lock:
                _jobs[job_id]["progress"].append(f"Generating {req.preset}...")

            output_dir = designer.design(
                preset=req.preset,
                transpose=req.transpose,
                quick=req.quick,
            )

            with _lock:
                _jobs[job_id]["status"] = "completed"
                _jobs[job_id]["result"] = {"output_dir": str(output_dir)}
                _jobs[job_id]["progress"].append("Design completed")
        except Exception as e:
            with _lock:
                _jobs[job_id]["status"] = "failed"
                _jobs[job_id]["progress"].append(f"Error: {e}")

    threading.Thread(target=run, daemon=True).start()
    return {"job_id": job_id}


@router.get("/{job_id}/status")
def get_design_status(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {"status": job["status"], "progress": job["progress"], "result": job.get("result")}


@router.get("/{job_id}/download")
def download_design(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
    if not job or job.get("status") != "completed":
        raise HTTPException(404, "Job not found or not completed")
    result = job.get("result", {})
    output_dir = result.get("output_dir")
    if not output_dir:
        raise HTTPException(404, "No output directory")
    # Return the first STL file found
    for f in Path(output_dir).rglob("*.stl"):
        from fastapi.responses import FileResponse
        return FileResponse(f, media_type="application/sla", filename=f.name)
    raise HTTPException(404, "No STL file found")
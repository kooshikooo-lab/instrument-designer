"""
Auto-design (sequential optimization) routes.
"""
import os
import uuid
import threading
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

_jobs: dict[str, dict] = {}
_lock = threading.Lock()


class AutoDesignRequest(BaseModel):
    target_frequencies: list[float]
    n_stages: int = 3
    pop_size: int = 30
    n_generations: int = 20


class SequentialOptimizeRequest(BaseModel):
    target_frequencies: list[float]
    n_stages: int = 3
    pop_size: int = 30
    n_generations: int = 20
    n_control_points: Optional[int] = None
    bore_length: Optional[float] = None
    min_radius: float = 0.003
    max_radius: float = 0.025


@router.post("/design-desk/auto")
def start_auto_design(req: AutoDesignRequest):
    job_id = str(uuid.uuid4())[:8]
    with _lock:
        _jobs[job_id] = {"status": "queued", "progress": [], "result": None}

    def run():
        try:
            with _lock:
                _jobs[job_id]["status"] = "running"
                _jobs[job_id]["progress"] = ["Starting auto-design..."]

            import sys
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
            from backend.sequential_optimizer import SequentialOptimizer

            optimizer = SequentialOptimizer(
                target_frequencies=req.target_frequencies,
                n_stages=req.n_stages,
                pop_size=req.pop_size,
                n_generations=req.n_generations,
            )

            def progress_cb(stage, gen, best):
                with _lock:
                    _jobs[job_id]["progress"].append(f"Stage {stage}, Gen {gen}: best={best:.2f}¢")

            result = optimizer.run(progress_callback=progress_cb)

            with _lock:
                _jobs[job_id]["status"] = "completed"
                _jobs[job_id]["result"] = result
                _jobs[job_id]["progress"].append("Auto-design completed")
        except Exception as e:
            with _lock:
                _jobs[job_id]["status"] = "failed"
                _jobs[job_id]["progress"].append(f"Error: {e}")

    threading.Thread(target=run, daemon=True).start()
    return {"job_id": job_id}


@router.get("/design-desk/instruments")
def list_saved_instruments():
    from pathlib import Path
    import json
    lib_dir = Path("instrument_library")
    if not lib_dir.exists():
        return {"instruments": []}
    instruments = []
    for f in lib_dir.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            instruments.append(data)
        except Exception:
            pass
    return {"instruments": instruments}


@router.get("/design-desk/auto/{job_id}/status")
def get_auto_design_status(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {"status": job["status"], "progress": job["progress"], "result": job.get("result")}


@router.post("/optimize/sequential")
def start_sequential_optimization(req: SequentialOptimizeRequest):
    job_id = str(uuid.uuid4())[:8]
    with _lock:
        _jobs[job_id] = {"status": "queued", "progress": [], "result": None}

    def run():
        try:
            with _lock:
                _jobs[job_id]["status"] = "running"
                _jobs[job_id]["progress"] = ["Starting sequential optimization..."]

            import sys
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
            from backend.sequential_optimizer import SequentialOptimizer

            optimizer = SequentialOptimizer(
                target_frequencies=req.target_frequencies,
                n_stages=req.n_stages,
                pop_size=req.pop_size,
                n_generations=req.n_generations,
                n_control_points=req.n_control_points,
                bore_length=req.bore_length,
                min_radius=req.min_radius,
                max_radius=req.max_radius,
            )

            def progress_cb(stage, gen, best):
                with _lock:
                    _jobs[job_id]["progress"].append(f"Stage {stage}, Gen {gen}: best={best:.2f}¢")

            result = optimizer.run(progress_callback=progress_cb)

            with _lock:
                _jobs[job_id]["status"] = "completed"
                _jobs[job_id]["result"] = result
                _jobs[job_id]["progress"].append("Sequential optimization completed")
        except Exception as e:
            with _lock:
                _jobs[job_id]["status"] = "failed"
                _jobs[job_id]["progress"].append(f"Error: {e}")

    threading.Thread(target=run, daemon=True).start()
    return {"job_id": job_id}


@router.get("/optimize/sequential/{job_id}/status")
def get_sequential_status(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {"status": job["status"], "progress": job["progress"], "result": job.get("result")}


@router.get("/optimize/sequential/{job_id}/stl")
def get_sequential_stl(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
    if not job or job.get("status") != "completed":
        raise HTTPException(404, "Job not found or not completed")
    result = job.get("result", {})
    stl_path = result.get("stl_path")
    if not stl_path or not os.path.exists(stl_path):
        raise HTTPException(404, "STL not found")
    from fastapi.responses import FileResponse
    return FileResponse(stl_path, media_type="application/sla", filename="sequential_result.stl")


@router.get("/optimize/sequential/{job_id}/profile")
def get_sequential_profile(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
    if not job or job.get("status") != "completed":
        raise HTTPException(404, "Job not found or not completed")
    result = job.get("result", {})
    return {"profile": result.get("bore_profile", [])}
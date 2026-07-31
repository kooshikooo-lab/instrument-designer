"""
Optimization routes.
"""
import os
import threading
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..shared_state import get_app, get_jobs, get_lock

router = APIRouter()

app = get_app()
_jobs = get_jobs()
_lock = get_lock()


class OptimizeRequest(BaseModel):
    target_frequencies: list[float]
    n_control_points: int = 12
    bore_length: Optional[float] = None
    min_radius: float = 0.003
    max_radius: float = 0.025
    pop_size: int = 30
    n_generations: int = 20
    temperature: Optional[float] = None
    n_workers: Optional[int] = None


@router.post("/start")
def start_optimization(req: OptimizeRequest):
    job_id = str(uuid.uuid4())[:8]
    with _lock:
        _jobs[job_id] = {"status": "queued", "progress": [], "result": None}

    def run():
        try:
            with _lock:
                _jobs[job_id]["status"] = "running"
                _jobs[job_id]["progress"] = ["Starting optimization..."]

            import sys
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
            from backend.optimizer import BoreOptimizer

            optimizer = BoreOptimizer(
                target_frequencies=req.target_frequencies,
                n_control_points=req.n_control_points,
                bore_length=req.bore_length,
                min_radius=req.min_radius,
                max_radius=req.max_radius,
                pop_size=req.pop_size,
                n_generations=req.n_generations,
                temperature=req.temperature,
                n_workers=req.n_workers,
            )

            def progress_cb(gen, best, pop):
                with _lock:
                    _jobs[job_id]["progress"].append(f"Gen {gen}: best={best:.2f}¢")

            result = optimizer.run(progress_callback=progress_cb)

            with _lock:
                _jobs[job_id]["status"] = "completed"
                _jobs[job_id]["result"] = result
                _jobs[job_id]["progress"].append("Optimization completed")
        except Exception as e:
            with _lock:
                _jobs[job_id]["status"] = "failed"
                _jobs[job_id]["progress"].append(f"Error: {e}")

    threading.Thread(target=run, daemon=True).start()
    return {"job_id": job_id}


@router.get("/{job_id}/status")
def get_optimization_status(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {"status": job["status"], "progress": job["progress"], "result": job.get("result")}


@router.post("/evaluate")
def evaluate_optimization(req: OptimizeRequest):
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from backend.optimizer import BoreOptimizer

    optimizer = BoreOptimizer(
        target_frequencies=req.target_frequencies,
        n_control_points=req.n_control_points,
        bore_length=req.bore_length,
        min_radius=req.min_radius,
        max_radius=req.max_radius,
    )
    result = optimizer.evaluate(req.target_frequencies)
    return result


@router.get("/presets")
def get_optimization_presets():
    return {
        "pentatonic_major": {"name": "Pentatonic Major", "frequencies": [261.63, 293.66, 329.63, 392.00, 440.00, 523.25]},
        "pentatonic_minor": {"name": "Pentatonic Minor", "frequencies": [261.63, 293.66, 311.13, 392.00, 466.16, 523.25]},
        "major_scale": {"name": "Major Scale", "frequencies": [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]},
        "chromatic": {"name": "Chromatic (1 octave)", "frequencies": [261.63, 277.18, 293.66, 311.13, 329.63, 349.23, 369.99, 392.00, 415.30, 440.00, 466.16, 493.88, 523.25]},
    }


@router.get("/cache/stats")
def get_cache_stats():
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from backend.impedance_cache import cache_size
    return {"cache_size": cache_size()}


@router.post("/cache/clear")
def clear_cache():
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from backend.impedance_cache import cache_clear
    cache_clear()
    return {"cleared": True}


@router.get("/cache/stats")
def get_cache_stats():
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from backend.impedance_cache import cache_size
    return {"cache_size": cache_size()}
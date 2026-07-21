"""
FastAPI server for remote Instrument Designer compute.
Run: uvicorn woodwind_designer.engine.design_server:app --host 0.0.0.0 --port 8000

Dependencies: pip install fastapi uvicorn pymoo openwind
"""
import os
import io
import uuid
import json
import threading
import tempfile
import zipfile
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .demakein_wrapper import DemakeinDesigner

app = FastAPI(title="Instrument Designer Server", version="1.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_jobs: dict[str, dict] = {}
_lock = threading.Lock()


class DesignRequest(BaseModel):
    preset: str
    transpose: int = 0
    quick: bool = False


class OptimizeRequest(BaseModel):
    target_frequencies: list[float]
    n_control_points: int = 12
    bore_length: Optional[float] = None
    min_radius: float = 0.003
    max_radius: float = 0.025
    pop_size: int = 30
    n_generations: int = 20
    temperature: float = 20.0
    n_workers: Optional[int] = None  # None = auto-detect CPU count


class EvaluateRequest(BaseModel):
    variables: list[float]
    bore_length: float
    target_frequencies: list[float]
    temperature: float = 20.0


class HealthResponse(BaseModel):
    status: str
    version: str


def _run_design(job_id: str, preset: str, transpose: int, quick: bool):
    progress_log = []
    def on_progress(msg):
        with _lock:
            progress_log.append(msg)
            _jobs[job_id]["progress"] = list(progress_log)

    try:
        out_dir = os.path.join(tempfile.gettempdir(), f"remote_{job_id}")
        designer = DemakeinDesigner()
        result = designer.design(preset, transpose, out_dir, on_progress, quick=quick)

        stl_basenames = [os.path.basename(p) for p in result.stl_files]
        with _lock:
            _jobs[job_id].update(
                status="completed" if result.success else "failed",
                result={
                    "success": result.success,
                    "log": result.log,
                    "ident": result.ident,
                    "stl_files": stl_basenames,
                    "output_dir": out_dir,
                },
                progress=list(progress_log),
            )
    except Exception as e:
        with _lock:
            _jobs[job_id].update(
                status="failed",
                error=str(e),
                result={
                    "success": False,
                    "log": f"Design failed: {e}",
                    "ident": "",
                    "stl_files": [],
                    "output_dir": "",
                },
                progress=list(progress_log) + [f"Error: {e}"],
            )


@app.post("/design", response_model=dict)
def start_design(req: DesignRequest):
    job_id = uuid.uuid4().hex[:12]
    with _lock:
        _jobs[job_id] = {"status": "queued", "progress": [], "result": None}
    t = threading.Thread(
        target=_run_design, args=(job_id, req.preset, req.transpose, req.quick), daemon=True
    )
    t.start()
    return {"job_id": job_id}


@app.get("/design/{job_id}/status")
def get_status(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {
        "status": job["status"],
        "progress": job["progress"],
        "result": job["result"],
    }


@app.get("/design/{job_id}/download")
def download_stls(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
    if not job or not job.get("result"):
        raise HTTPException(404, "No result for this job")
    result = job["result"]
    output_dir = result.get("output_dir", "")
    stl_files = result.get("stl_files", [])

    if not output_dir or not os.path.isdir(output_dir):
        raise HTTPException(404, "Output directory not found on server")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in stl_files:
            path = os.path.join(output_dir, name)
            if os.path.isfile(path):
                zf.write(path, name)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="design_{job_id}.zip"'},
    )


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", version="1.0.0")


@app.get("/presets")
def list_presets():
    designer = DemakeinDesigner()
    presets = {}
    for family in designer.list_families():
        for sub in designer.list_subcategories(family):
            for key in designer.list_presets(family, sub):
                presets[key] = designer.PRESET_DISPLAY_NAMES.get(key, key)
    return {"presets": presets}


# ─── Optimization Endpoints ────────────────────────────────────────────────

def _run_optimization(job_id: str, req: OptimizeRequest):
    """Run optimization in a background thread."""
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from backend.optimizer import BoreOptimizer

        with _lock:
            _jobs[job_id]["progress"] = ["Starting optimization..."]

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

        with _lock:
            _jobs[job_id]["progress"].append(
                f"Config: {req.pop_size} pop x {req.n_generations} gen, "
                f"{req.n_control_points} control points, "
                f"bore {optimizer.bore_length:.3f}m, "
                f"workers: {req.n_workers or 'auto'}"
            )

        result = optimizer.run(verbose=False)

        # Strip heavy data from designs for JSON serialization
        slim_designs = []
        for d in result.get("designs", []):
            slim_designs.append({
                "bore_profile": d["bore_profile"],
                "objectives": d["objectives"],
                "matched_frequencies": d.get("matched_frequencies", []),
            })

        slim_best = []
        for d in result.get("best_candidates", []):
            slim_best.append({
                "bore_profile": d["bore_profile"],
                "objectives": d["objectives"],
                "matched_frequencies": d.get("matched_frequencies", []),
                "variables": d.get("variables", []),
            })

        with _lock:
            _jobs[job_id].update(
                status="completed",
                result={
                    "pareto_front": result.get("pareto_front", []),
                    "designs": slim_designs,
                    "best_candidates": slim_best,
                    "n_evaluations": result.get("n_evaluations", 0),
                    "n_generations": result.get("n_generations", 0),
                    "bore_length": result.get("bore_length", 0),
                    "freq_range": result.get("freq_range", []),
                    "seed": result.get("seed", 0),
                },
                progress=_jobs[job_id].get("progress", []) + ["Optimization complete"],
            )
    except Exception as e:
        with _lock:
            _jobs[job_id].update(
                status="failed",
                error=str(e),
                progress=_jobs[job_id].get("progress", []) + [f"Error: {e}"],
            )


@app.post("/optimize/start")
def start_optimization(req: OptimizeRequest):
    """Start an evolutionary bore optimization job."""
    job_id = uuid.uuid4().hex[:12]
    with _lock:
        _jobs[job_id] = {"status": "queued", "progress": [], "result": None}
    t = threading.Thread(target=_run_optimization, args=(job_id, req), daemon=True)
    t.start()
    return {"job_id": job_id}


@app.get("/optimize/{job_id}/status")
def get_optimization_status(job_id: str):
    """Poll optimization job status."""
    with _lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job.get("progress", []),
        "result": job.get("result"),
        "error": job.get("error"),
    }


@app.post("/optimize/evaluate")
def evaluate_single(req: EvaluateRequest):
    """Evaluate a single bore design (for interactive tweaking)."""
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from backend.optimizer import BoreOptimizer

        optimizer = BoreOptimizer(
            target_frequencies=req.target_frequencies,
            bore_length=req.bore_length,
            temperature=req.temperature,
        )
        result = optimizer.evaluate_single(req.variables)
        return result
    except Exception as e:
        raise HTTPException(500, f"Evaluation failed: {e}")


@app.get("/optimize/presets")
def get_optimization_presets():
    """Return optimization presets with correct target frequencies per instrument type."""
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from backend.target_frequencies import get_preset_info

        presets = {}
        for preset_key in ["folk_whistle", "folk_flute", "recorder", "reedpipe", "folk_shawm", "clarinet_Bb", "reed_drone"]:
            info = get_preset_info(preset_key)
            if info:
                presets[preset_key] = {
                    "name": info["description"],
                    "frequencies": info["targets"],
                    "type": info["type"],
                    "fundamental": info["fundamental"],
                }
        return {"presets": presets}
    except Exception:
        return {"presets": {
            "clarinet_Bb": {
                "name": "Bb Clarinet (odd harmonics)",
                "frequencies": [233.1, 699.3, 1165.5, 1631.7, 2097.9, 2564.1],
            },
            "folk_whistle": {
                "name": "Penny Whistle D (D5-D6)",
                "frequencies": [587.3, 1174.7, 1762.0, 2349.3, 2936.6, 3523.9],
            },
            "recorder": {
                "name": "Soprano Recorder (C5-C6)",
                "frequencies": [523.3, 1046.5, 1569.8, 2093.0, 2616.3, 3139.6],
            },
        }}


# ─── Cache Management ────────────────────────────────────────────────────

@app.get("/optimize/cache/size")
def get_cache_size():
    from backend.mp_cache import cache_size
    return {"cache_size": cache_size()}


@app.post("/optimize/cache/clear")
def clear_cache():
    from backend.mp_cache import cache_clear
    cache_clear()
    return {"status": "cache cleared"}


@app.get("/optimize/cache/stats")
def get_cache_stats():
    from backend.mp_cache import cache_size
    return {"cache_size": cache_size(), "status": "ok"}

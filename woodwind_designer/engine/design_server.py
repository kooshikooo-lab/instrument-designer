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


class TMMOptimizeRequest(BaseModel):
    """TMM-based bore optimization using Powell + L-BFGS-B two-phase approach."""
    target_frequencies: list[float]
    fingering_sets: list[list[str]]
    n_control_points: int = 12
    bore_length: Optional[float] = None
    min_radius: float = 1.0  # mm (TMM uses mm internally)
    max_radius: float = 15.0  # mm
    temperature: float = 20.0
    hole_positions: Optional[list[float]] = None  # mm
    hole_diameters: Optional[list[float]] = None  # mm
    hole_lengths: Optional[list[float]] = None  # mm
    closed_top: bool = False
    outer_diameter: float = 22.0  # mm
    n_register: int = 1
    maxiter: int = 300


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
        for preset_key in ["folk_whistle", "folk_flute", "recorder", "reedpipe", "folk_shawm", "clarinet_Bb", "reed_drone", "soprano_sax", "alto_sax", "tenor_sax", "baritone_sax", "trumpet_bb", "trombone", "french_horn", "tuba"]:
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


# ─── TMM Optimization Endpoints ──────────────────────────────────────────

def _run_tmm_optimization(job_id: str, req: TMMOptimizeRequest):
    """Run TMM-based optimization in a background thread."""
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from backend.tmm_optimizer_v2 import TMMBoreOptimizerJAX

        with _lock:
            _jobs[job_id]["progress"] = ["Starting TMM optimization..."]

        optimizer = TMMBoreOptimizerJAX(
            target_frequencies=req.target_frequencies,
            fingering_sets=req.fingering_sets,
            n_control_points=req.n_control_points,
            bore_length=req.bore_length,
            min_radius=req.min_radius,
            max_radius=req.max_radius,
            temperature=req.temperature,
            hole_positions=req.hole_positions,
            hole_diameters=req.hole_diameters,
            hole_lengths=req.hole_lengths,
            closed_top=req.closed_top,
            outer_diameter=req.outer_diameter,
            n_register=req.n_register,
        )

        with _lock:
            _jobs[job_id]["progress"].append(
                f"Config: {req.n_control_points} control points, "
                f"bore {optimizer.bore_length:.1f}mm, "
                f"{len(req.fingering_sets)} fingerings, "
                f"maxiter={req.maxiter}"
            )

        result = optimizer.run(verbose=False, maxiter=req.maxiter)

        with _lock:
            _jobs[job_id].update(
                status="completed",
                result={
                    "success": result.get("success", True),
                    "best_radii": result.get("best_radii", []),
                    "final_rms_cents": result.get("final_rms_cents", 0),
                    "global_offset_cents": result.get("global_offset_cents", 0),
                    "matched_frequencies": [
                        {"target": m["target"], "actual": m["actual"], "error_cents": m["error_cents"]}
                        for m in result.get("matched_frequencies", [])
                    ],
                    "wall_time": result.get("wall_time", 0),
                    "bore_length_mm": result.get("bore_length_mm", 0),
                    "best_objective": result.get("best_objective", 0),
                },
                progress=_jobs[job_id].get("progress", []) + ["TMM optimization complete"],
            )
    except Exception as e:
        with _lock:
            _jobs[job_id].update(
                status="failed",
                error=str(e),
                progress=_jobs[job_id].get("progress", []) + [f"Error: {e}"],
            )


@app.post("/optimize/tmm")
def start_tmm_optimization(req: TMMOptimizeRequest):
    """Start a TMM-based bore optimization job (Powell + L-BFGS-B two-phase)."""
    job_id = uuid.uuid4().hex[:12]
    with _lock:
        _jobs[job_id] = {"status": "queued", "progress": [], "result": None}
    t = threading.Thread(target=_run_tmm_optimization, args=(job_id, req), daemon=True)
    t.start()
    return {"job_id": job_id}


@app.get("/optimize/tmm/{job_id}/status")
def get_tmm_optimization_status(job_id: str):
    """Poll TMM optimization job status."""
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


# ─── Sequential Bore Optimization (Bordeaux Method) ────────────────────

class SequentialOptimizeRequest(BaseModel):
    """Sequential bore + tone hole optimization (Bordeaux method)."""
    target_frequencies: list[float]
    fingering_sets: list[list[str]]
    bore_radius: float = 7.25  # mm
    outer_diameter: float = 22.0  # mm
    closed_top: bool = True
    n_register: int = 1
    hole_diameter: float = 7.0  # mm
    hole_length: float = 3.75  # mm
    bore_length_bounds: list[float] = [100.0, 2000.0]  # mm
    n_bore_cp: int = 0  # 0=uniform bore, >0=variable-radius bore with N control points
    bore_radius_bounds: list[float] = [2.0, 20.0]  # mm, min/max radius for variable bore


def _run_sequential_optimization(job_id: str, req: SequentialOptimizeRequest):
    """Run sequential bore optimization in a background thread."""
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from backend.tmm_optimizer_sequential import SequentialBoreOptimizer

        with _lock:
            _jobs[job_id]["progress"] = ["Starting sequential optimization..."]

        optimizer = SequentialBoreOptimizer(
            target_frequencies=req.target_frequencies,
            fingering_sets=req.fingering_sets,
            bore_radius=req.bore_radius,
            outer_diameter=req.outer_diameter,
            closed_top=req.closed_top,
            n_register=req.n_register,
            hole_diameter=req.hole_diameter,
            hole_length=req.hole_length,
            bore_length_bounds=tuple(req.bore_length_bounds),
            n_bore_cp=req.n_bore_cp,
            bore_radius_bounds=tuple(req.bore_radius_bounds),
        )

        with _lock:
            _jobs[job_id]["progress"].append(
                f"Config: {len(req.target_frequencies)} notes, "
                f"bore r={req.bore_radius:.1f}mm, "
                f"{'closed' if req.closed_top else 'open'} top"
            )

        result = optimizer.run(verbose=False)

        with _lock:
            _jobs[job_id].update(
                status="completed",
                result={
                    "success": result.get("success", False),
                    "bore_length_mm": result.get("bore_length_mm", 0),
                    "bore_radii": result.get("bore_radii", []),
                    "n_bore_cp": req.n_bore_cp,
                    "hole_positions": result.get("hole_positions", []),
                    "hole_diameters": result.get("hole_diameters", []),
                    "hole_lengths": result.get("hole_lengths", []),
                    "final_rms_cents": result.get("final_rms_cents", 0),
                    "peak_error_cents": result.get("peak_error_cents", 0),
                    "wall_time": result.get("wall_time", 0),
                    "matched_frequencies": [
                        {"target": m["target"], "actual": m["actual"], "error_cents": m["error_cents"]}
                        for m in result.get("matched_frequencies", [])
                    ],
                },
                progress=_jobs[job_id].get("progress", []) + ["Sequential optimization complete"],
            )
    except Exception as e:
        with _lock:
            _jobs[job_id].update(
                status="failed",
                error=str(e),
                progress=_jobs[job_id].get("progress", []) + [f"Error: {e}"],
            )


@app.post("/optimize/sequential")
def start_sequential_optimization(req: SequentialOptimizeRequest):
    """Start a sequential bore + tone hole optimization (Bordeaux method)."""
    job_id = uuid.uuid4().hex[:12]
    with _lock:
        _jobs[job_id] = {"status": "queued", "progress": [], "result": None}
    t = threading.Thread(target=_run_sequential_optimization, args=(job_id, req), daemon=True)
    t.start()
    return {"job_id": job_id}


@app.get("/optimize/sequential/{job_id}/status")
def get_sequential_optimization_status(job_id: str):
    """Poll sequential optimization job status."""
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


@app.get("/optimize/sequential/{job_id}/stl")
def download_sequential_stl(job_id: str):
    """Download STL file for a completed sequential optimization."""
    from backend.stl_export import export_optimizer_result
    with _lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job["status"] != "completed" or not job.get("result"):
        raise HTTPException(400, "Job not completed yet")
    import tempfile
    tmp_dir = tempfile.mkdtemp()
    stl_path = os.path.join(tmp_dir, f"{job_id}.stl")
    try:
        export_optimizer_result(job["result"], stl_path)
    except Exception as e:
        raise HTTPException(500, f"STL generation failed: {e}")
    from fastapi.responses import FileResponse
    return FileResponse(
        stl_path, media_type="model/stl",
        filename=f"instrument_{job_id}.stl",
    )


@app.get("/optimize/sequential/{job_id}/profile")
def download_sequential_profile(job_id: str):
    """Download bore profile JSON for visualization."""
    from backend.stl_export import export_bore_profile_json
    with _lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job["status"] != "completed" or not job.get("result"):
        raise HTTPException(400, "Job not completed yet")
    import tempfile
    tmp_dir = tempfile.mkdtemp()
    json_path = os.path.join(tmp_dir, f"{job_id}_profile.json")
    try:
        export_bore_profile_json(job["result"], json_path)
    except Exception as e:
        raise HTTPException(500, f"Profile generation failed: {e}")
    from fastapi.responses import FileResponse
    return FileResponse(
        json_path, media_type="application/json",
        filename=f"instrument_{job_id}_profile.json",
    )


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


# ─── AI Design Advisor ───────────────────────────────────────────────────

class AdvisorAnalyzeRequest(BaseModel):
    optimization_result: dict
    target_frequencies: list[float]
    use_llm: bool = False
    llm_model: str = "llama3.2"


class AdvisorStoreRequest(BaseModel):
    instrument_type: str = ""
    target_frequencies: list[float] = []
    bore_profile: list = []
    n_control_points: int = 0
    pop_size: int = 0
    n_generations: int = 0
    frequency_accuracy: float = 0
    scale_evenness: float = 0
    projection: float = 0
    n_evaluations: int = 0
    bore_length: float = 0
    notes: str = ""


@app.get("/advisor/status")
def advisor_status():
    """Check AI advisor capabilities."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from backend.ai_advisor import get_advisor_status
    return get_advisor_status()


@app.post("/advisor/analyze")
def advisor_analyze(req: AdvisorAnalyzeRequest):
    """Analyze an optimization result and return suggestions."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from backend.ai_advisor import analyze_optimization_result, get_llm_suggestion

    result = analyze_optimization_result(req.optimization_result, req.target_frequencies)

    response = {
        "score": result.score,
        "grade": result.grade,
        "analysis": result.analysis,
        "suggestions": [asdict(s) for s in result.suggestions],
        "comparison": result.comparison,
        "llm_analysis": None,
    }

    if req.use_llm:
        llm_text = get_llm_suggestion(
            req.optimization_result, req.target_frequencies, req.llm_model
        )
        response["llm_analysis"] = llm_text

    return response


@app.post("/advisor/store")
def advisor_store(req: AdvisorStoreRequest):
    """Store a design in the advisor's memory for future reference."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from backend.ai_advisor import store_design

    store_design({
        "instrument_type": req.instrument_type,
        "target_frequencies": req.target_frequencies,
        "bore_profile": req.bore_profile,
        "n_control_points": req.n_control_points,
        "pop_size": req.pop_size,
        "n_generations": req.n_generations,
        "frequency_accuracy": req.frequency_accuracy,
        "scale_evenness": req.scale_evenness,
        "projection": req.projection,
        "n_evaluations": req.n_evaluations,
        "bore_length": req.bore_length,
        "notes": req.notes,
    })
    return {"status": "stored"}


@app.get("/advisor/history")
def advisor_history(limit: int = 20):
    """Get design history from advisor memory."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from backend.ai_advisor import get_design_history
    return {"designs": get_design_history(limit)}


# ─── Automated Design Agent ─────────────────────────────────────────────

class AutoDesignRequest(BaseModel):
    instrument_type: str
    max_iterations: int = 3
    target_accuracy: float = 3.0
    target_frequencies: Optional[list[float]] = None


def _run_auto_design(job_id: str, req: AutoDesignRequest):
    """Run the automated design loop in a background thread."""
    progress_log = []
    def on_progress(msg):
        with _lock:
            progress_log.append(msg)
            _jobs[job_id]["progress"] = list(progress_log)

    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from backend.design_desk import run_auto_design

        result = run_auto_design(
            req.instrument_type,
            max_iterations=req.max_iterations,
            on_progress=on_progress,
        )

        with _lock:
            _jobs[job_id].update(
                status="completed",
                result=result,
                progress=list(progress_log),
            )
    except Exception as e:
        with _lock:
            _jobs[job_id].update(
                status="failed",
                error=str(e),
                progress=list(progress_log) + [f"Error: {e}"],
            )


@app.post("/design-desk/auto")
def start_auto_design(req: AutoDesignRequest):
    """Start an automated multi-iteration design loop."""
    from backend.design_desk import INSTRUMENT_CONFIGS
    if req.instrument_type not in INSTRUMENT_CONFIGS:
        raise HTTPException(400, f"Unknown instrument type: {req.instrument_type}. Available: {list(INSTRUMENT_CONFIGS.keys())}")
    job_id = uuid.uuid4().hex[:12]
    with _lock:
        _jobs[job_id] = {"status": "queued", "progress": [], "result": None}
    t = threading.Thread(target=_run_auto_design, args=(job_id, req), daemon=True)
    t.start()
    return {"job_id": job_id}


@app.get("/design-desk/instruments")
def list_design_desk_instruments():
    """List available instrument types for auto-design."""
    from backend.design_desk import INSTRUMENT_CONFIGS
    return {"instruments": {k: v["description"] for k, v in INSTRUMENT_CONFIGS.items()}}


# ─── SVG Export ─────────────────────────────────────────────────────────

class SvgExportRequest(BaseModel):
    bore_profile: list[list[float]]
    title: str = "Instrument Bore Profile"
    hole_positions: Optional[list[float]] = None
    hole_diameters: Optional[list[float]] = None
    bore_length: Optional[float] = None
    view: str = "side"


@app.post("/export/svg")
def export_svg(req: SvgExportRequest):
    """Generate SVG from bore profile data."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from backend.svg_export import bore_to_svg, bore_to_cross_section_svg

    if req.view == "cross":
        svg = bore_to_cross_section_svg(
            req.bore_profile, req.title, req.hole_positions,
        )
    else:
        svg = bore_to_svg(
            req.bore_profile, req.title, req.hole_positions,
            req.hole_diameters, req.bore_length,
        )
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=svg, media_type="image/svg+xml")

"""
Bore optimization and unconventional bore routes.
"""
import uuid
import threading
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..shared_state import get_app, get_jobs, get_lock

router = APIRouter()

app = get_app()
_jobs = get_jobs()
_lock = get_lock()


class BoreOptimizeRequest(BaseModel):
    bore_type: str
    params: dict
    target_frequencies: list[float]
    pop_size: int = 30
    n_generations: int = 20
    n_control_points: Optional[int] = None


@router.post("/bore/optimize")
def optimize_bore(req: BoreOptimizeRequest):
    job_id = str(uuid.uuid4())[:8]
    with _lock:
        _jobs[job_id] = {"status": "queued", "progress": [], "result": None}

    def run():
        try:
            with _lock:
                _jobs[job_id]["status"] = "running"
                _jobs[job_id]["progress"] = ["Starting bore optimization..."]

            import sys
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
            from backend.physics.bore_optimizer import optimize_bore_shape

            result = optimize_bore_shape(
                bore_type=req.bore_type,
                params=req.params,
                target_frequencies=req.target_frequencies,
                pop_size=req.pop_size,
                n_generations=req.n_generations,
            )

            with _lock:
                _jobs[job_id]["status"] = "completed"
                _jobs[job_id]["result"] = result
                _jobs[job_id]["progress"].append("Bore optimization completed")
        except Exception as e:
            with _lock:
                _jobs[job_id]["status"] = "failed"
                _jobs[job_id]["progress"].append(f"Error: {e}")

    threading.Thread(target=run, daemon=True).start()
    return {"job_id": job_id}


@router.get("/bore/optimize/{job_id}/status")
def get_bore_optimize_status(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {"status": job["status"], "progress": job["progress"], "result": job.get("result")}


# TMM Optimization
class TMMOptimizeRequest(BaseModel):
    target_frequencies: list[float]
    bore_type: str = "cylindrical"
    n_control_points: int = 12
    pop_size: int = 20
    n_generations: int = 10
    wall_thickness: float = 3.0


@router.post("/optimize/tmm")
def start_tmm_optimization(req: TMMOptimizeRequest):
    job_id = str(uuid.uuid4())[:8]
    with _lock:
        _jobs[job_id] = {"status": "queued", "progress": [], "result": None}

    def run():
        try:
            with _lock:
                _jobs[job_id]["status"] = "running"
                _jobs[job_id]["progress"] = ["Starting TMM optimization..."]

            import sys
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
            from backend.tmm_optimizer import TMMOptimizer

            optimizer = TMMOptimizer(
                target_frequencies=req.target_frequencies,
                bore_type=req.bore_type,
                n_control_points=req.n_control_points,
                wall_thickness=req.wall_thickness,
                pop_size=req.pop_size,
                n_generations=req.n_generations,
            )

            def progress_cb(gen, best, pop):
                with _lock:
                    _jobs[job_id]["progress"].append(f"Gen {gen}: best={best:.2f}")

            result = optimizer.run(progress_callback=progress_cb)

            with _lock:
                _jobs[job_id]["status"] = "completed"
                _jobs[job_id]["result"] = result
                _jobs[job_id]["progress"].append("TMM optimization completed")
        except Exception as e:
            with _lock:
                _jobs[job_id]["status"] = "failed"
                _jobs[job_id]["progress"].append(f"Error: {e}")

    threading.Thread(target=run, daemon=True).start()
    return {"job_id": job_id}


@router.get("/optimize/tmm/{job_id}/status")
def get_tmm_status(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {"status": job["status"], "progress": job["progress"], "result": job.get("result")}


# Sequential Optimization
class SequentialOptimizeRequest(BaseModel):
    target_frequencies: list[float]
    bore_type: str = "cylindrical"
    n_control_points: int = 12
    wall_thickness: float = 3.0
    pop_size: int = 20
    n_generations: int = 10
    stages: int = 3


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
                bore_type=req.bore_type,
                n_control_points=req.n_control_points,
                wall_thickness=req.wall_thickness,
                pop_size=req.pop_size,
                n_generations=req.n_generations,
                stages=req.stages,
            )

            def progress_cb(stage, gen, best, pop):
                with _lock:
                    _jobs[job_id]["progress"].append(f"Stage {stage}, Gen {gen}: best={best:.2f}")

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
    stl_bytes = result.get("stl_bytes")
    if not stl_bytes:
        raise HTTPException(404, "No STL data")
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        iter([stl_bytes]),
        media_type="application/sla",
        headers={"Content-Disposition": "attachment; filename=sequential_optimized.stl"},
    )


@router.get("/optimize/sequential/{job_id}/profile")
def get_sequential_profile(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
    if not job or job.get("status") != "completed":
        raise HTTPException(404, "Job not found or not completed")
    result = job.get("result", {})
    return {"profile": result.get("bore_profile", [])}


# Stub endpoints for frontend routes not yet implemented
class ImpedanceComputeRequest(BaseModel):
    preset: str


class ImpedanceComputeResponse(BaseModel):
    frequencies: list[float]
    impedance_magnitude: list[float]
    impedance_real: list[float]
    impedance_imag: list[float]


@router.post("/impedance/compute")
def compute_impedance(req: ImpedanceComputeRequest):
    raise HTTPException(501, "Impedance computation not yet implemented. See backend/solvers/impedance_solver.py")


@router.get("/impedance/precomputed/{preset}")
def get_precomputed_impedance(preset: str):
    raise HTTPException(501, "Precomputed impedance not available. Run impedance benchmark first.")


class SimulateSoundParams(BaseModel):
    preset: str
    note_hz: float
    duration_sec: float = 1.0
    sample_rate: int = 44100


@router.post("/simulate/sound")
def simulate_sound(params: SimulateSoundParams):
    raise HTTPException(501, "Sound simulation not yet implemented. Requires synthesis backend.")


class AnalyzeAudioRequest(BaseModel):
    preset: str
    top_peaks: int = 10


class AnalyzeAudioResponse(BaseModel):
    frequencies: list[float]
    impedance_magnitude: list[float]


@router.post("/analyze/audio")
def analyze_audio(req: AnalyzeAudioRequest):
    raise HTTPException(501, "Audio analysis not yet implemented. Requires microphone pipeline.")


# Auto-design routes
class AutoDesignRequest(BaseModel):
    target_frequencies: list[float]
    instrument_type: str = "reed"
    constraints: Optional[dict] = None


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
            from backend.auto_designer import AutoDesigner

            designer = AutoDesigner()
            result = designer.design(
                target_frequencies=req.target_frequencies,
                instrument_type=req.instrument_type,
                constraints=req.constraints,
            )

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
def list_instruments():
    from woodwind_designer.engine.instrument_library import list_instruments as lib_list
    return {"instruments": lib_list()}


# /design-desk/auto/{job_id}/status is in auto_design_routes.py
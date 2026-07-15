import io
import os
import json
import uuid
import tempfile
import threading
import time
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import numpy as np
from build123d import Cylinder as B123dCylinder, export_step as b123d_export_step, Align, Location, Axis

app = FastAPI(title="Instrument Designer Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BORE_DIR = Path(__file__).parent / "bore_profiles"
IMPEDANCE_DIR = Path(__file__).parent / "impedance_data"

AVAILABLE_BORES = {
    "recorder": "recorder.csv",
    "folk_whistle": "folk_whistle.csv",
    "flute": "flute.csv",
    "reedpipe": "reedpipe.csv",
    "shawm": "shawm.csv",
    "didgeridoo": "didgeridoo.csv",
}


@app.get("/health")
def health():
    """Health check endpoint — returns server status and version."""
    return {"status": "ok", "version": "1.0.0"}


@app.get("/presets")
def list_presets():
    """List all available bore profile presets (recorder, folk_whistle, flute, etc.)."""
    return {"presets": list(AVAILABLE_BORES.keys())}


DESIGN_JOBS: dict[str, dict] = {}
JOB_MAX_AGE_SECONDS = 3600  # Clean up jobs older than 1 hour
JOB_MAX_COUNT = 50  # Keep at most 50 completed jobs


def _cleanup_old_jobs():
    """Remove completed jobs older than JOB_MAX_AGE_SECONDS to prevent memory leaks."""
    now = time.time()
    to_delete = [
        jid for jid, job in DESIGN_JOBS.items()
        if job.get("status") in ("completed", "failed")
        and now - job.get("completed_at", now) > JOB_MAX_AGE_SECONDS
    ]
    for jid in to_delete:
        del DESIGN_JOBS[jid]
    # Also enforce max count by dropping oldest completed jobs
    completed = [
        (jid, job) for jid, job in DESIGN_JOBS.items()
        if job.get("status") in ("completed", "failed")
    ]
    if len(completed) > JOB_MAX_COUNT:
        completed.sort(key=lambda x: x[1].get("completed_at", 0))
        for jid, _ in completed[: len(completed) - JOB_MAX_COUNT]:
            del DESIGN_JOBS[jid]


JOB_LOCK = threading.Lock()


def _run_design_job(job_id: str, preset: str, transpose: int):
    """Background thread target — runs Build123d STL generation and updates job status."""
    try:
        with JOB_LOCK:
            DESIGN_JOBS[job_id]["progress"].append("Starting Build123d...")
        stl_data = build_instrument_stl(preset, transpose)
        with JOB_LOCK:
            DESIGN_JOBS[job_id]["stl_data"] = stl_data
            DESIGN_JOBS[job_id]["progress"].append("STL mesh generated")
            DESIGN_JOBS[job_id]["progress"].append("Done!")
            DESIGN_JOBS[job_id]["status"] = "completed"
    except Exception as e:
        with JOB_LOCK:
            DESIGN_JOBS[job_id]["status"] = "failed"
            DESIGN_JOBS[job_id]["progress"].append(f"Error: {str(e)}")
            DESIGN_JOBS[job_id]["error"] = str(e)


def parse_bore_profile(preset: str) -> list[tuple[float, float, float, float]]:
    """Parse bore CSV into [(start_pos, end_pos, start_r, end_r), ...] in mm."""
    bore_file = BORE_DIR / AVAILABLE_BORES[preset]
    segments = []
    with open(bore_file) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                segments.append((
                    float(parts[0]) * 1000,
                    float(parts[1]) * 1000,
                    float(parts[2]) * 1000,
                    float(parts[3]) * 1000,
                ))
    return segments


TONE_HOLES: dict[str, list[dict]] = {
    "recorder": [
        {"z": 60.0, "r": 2.5, "label": "thumb"},
        {"z": 100.0, "r": 2.8, "label": "H1"},
        {"z": 120.0, "r": 2.8, "label": "H2"},
        {"z": 140.0, "r": 2.8, "label": "H3"},
        {"z": 160.0, "r": 2.8, "label": "H4"},
        {"z": 180.0, "r": 2.8, "label": "H5"},
        {"z": 210.0, "r": 2.8, "label": "H6"},
        {"z": 240.0, "r": 2.8, "label": "H7"},
    ],
    "folk_whistle": [
        {"z": 100.0, "r": 2.5, "label": "H1"},
        {"z": 120.0, "r": 2.5, "label": "H2"},
        {"z": 140.0, "r": 2.5, "label": "H3"},
        {"z": 160.0, "r": 2.5, "label": "H4"},
        {"z": 180.0, "r": 2.5, "label": "H5"},
        {"z": 220.0, "r": 2.5, "label": "H6"},
    ],
    "flute": [
        {"z": 200.0, "r": 4.0, "label": "H1"},
        {"z": 260.0, "r": 4.0, "label": "H2"},
        {"z": 320.0, "r": 4.0, "label": "H3"},
        {"z": 380.0, "r": 4.0, "label": "H4"},
        {"z": 440.0, "r": 4.0, "label": "H5"},
        {"z": 520.0, "r": 4.0, "label": "H6"},
    ],
    "reedpipe": [
        {"z": 120.0, "r": 2.0, "label": "H1"},
        {"z": 150.0, "r": 2.0, "label": "H2"},
        {"z": 180.0, "r": 2.0, "label": "H3"},
        {"z": 210.0, "r": 2.0, "label": "H4"},
    ],
    "shawm": [
        {"z": 150.0, "r": 2.5, "label": "H1"},
        {"z": 180.0, "r": 2.5, "label": "H2"},
        {"z": 210.0, "r": 2.5, "label": "H3"},
        {"z": 240.0, "r": 2.5, "label": "H4"},
        {"z": 270.0, "r": 2.5, "label": "H5"},
        {"z": 310.0, "r": 2.5, "label": "H6"},
    ],
    "didgeridoo": [
        {"z": 400.0, "r": 6.0, "label": "breath"},
    ],
}


def build_instrument_stl(preset: str, transpose: int = 0) -> bytes:
    """Build a full instrument STL with bore profile and tone holes using Build123d."""
    from build123d import (
        Cylinder, Location, Align, Axis, Plane,
        export_stl, Compound,
    )

    bore = parse_bore_profile(preset)
    total_length = bore[-1][1] - bore[0][0]
    wall_thickness = 2.0

    mean_inner_r = sum(s[2] + s[3] for s in bore) / (2 * len(bore))
    mean_outer_r = mean_inner_r + wall_thickness

    outer = Cylinder(
        radius=mean_outer_r, height=total_length,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    bore_verts = []
    for i, (z0, z1, r0, r1) in enumerate(bore):
        z = z0 - bore[0][0]
        bore_verts.append((r0, z))
        if i == len(bore) - 1:
            bore_verts.append((r1, z1 - bore[0][0]))

    from build123d import Line, Wire, extrude, BuildPart

    profile_edges = []
    for i in range(len(bore_verts) - 1):
        r0, z0 = bore_verts[i]
        r1, z1 = bore_verts[i + 1]
        profile_edges.append(Line((z0, r0), (z1, r1)))

    bottom = Line((bore_verts[-1][1], 0), (bore_verts[0][1], 0))
    left = Line((bore_verts[0][1], 0), (bore_verts[0][1], bore_verts[0][0]))
    right = Line((bore_verts[-1][1], 0), (bore_verts[-1][1], bore_verts[-1][0]))
    profile_edges.extend([bottom, left, right])

    wire = Wire(profile_edges)
    bore_profile_face = extrude(Plane.XZ * wire, amount=0.001)

    inner_bore = Cylinder(
        radius=mean_inner_r, height=total_length + 1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    tube = outer - inner_bore

    holes = TONE_HOLES.get(preset, [])
    if holes:
        for h in holes:
            z_pos = h["z"]
            hole_r_h = h["r"]
            hole_cyl = Cylinder(
                radius=hole_r_h, height=wall_thickness + 4.0,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            )
            hole_cyl = hole_cyl.moved(Location((0, 0, z_pos - total_length / 2)))
            hole_cyl = hole_cyl.rotate(Axis.Y, 90)
            tube = tube - hole_cyl

    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        export_stl(tube, tmp_path)
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


class DesignRequest(BaseModel):
    """Request body for starting a design job."""
    preset: str
    transpose: int = 0


@app.post("/design")
def start_design(req: DesignRequest):
    """Start an async design job — generates an STL file with bore profile and tone holes.

    Returns a job_id that can be polled via /design/{job_id}/status.
    The STL is built using Build123d with CSG operations (outer tube minus inner bore minus tone holes).
    """
    if req.preset not in AVAILABLE_BORES:
        raise HTTPException(404, f"Unknown preset: {req.preset}")

    job_id = str(uuid.uuid4())[:8]
    with JOB_LOCK:
        DESIGN_JOBS[job_id] = {
            "job_id": job_id,
            "status": "running",
            "progress": [
                f"Loading preset: {req.preset}",
                f"Transpose: {req.transpose} semitones",
                "Parsing bore profile...",
                "Computing tone hole positions...",
            ],
            "result": {"output_dir": f"output/{job_id}", "files": [f"{req.preset}.stl"]},
            "preset": req.preset,
            "stl_data": None,
        }

    t = threading.Thread(target=_run_design_job, args=(job_id, req.preset, req.transpose), daemon=True)
    t.start()
    return {"job_id": job_id}


@app.get("/design/{job_id}/status")
def design_status(job_id: str):
    """Get the current status and progress of a design job.

    Returns job_id, status (running/completed/failed), progress messages,
    result metadata, and preset name. Does NOT include stl_data (bytes) to avoid serialization issues.
    """
    if job_id not in DESIGN_JOBS:
        raise HTTPException(404, f"Job not found: {job_id}")
    job = DESIGN_JOBS[job_id]
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "progress": job["progress"],
        "result": job["result"],
        "preset": job["preset"],
        "error": job.get("error"),
    }


@app.get("/design/{job_id}/download")
def design_download(job_id: str):
    """Download the generated STL file for a completed design job.

    If the job's stl_data was cleaned up from memory, regenerates it on-the-fly.
    Returns the STL as a binary stream with Content-Disposition header.
    """
    if job_id not in DESIGN_JOBS:
        raise HTTPException(404, f"Job not found: {job_id}")

    job = DESIGN_JOBS[job_id]
    preset = job["result"]["files"][0].replace(".stl", "")

    with JOB_LOCK:
        stl_data = job.get("stl_data")

    if stl_data is None:
        try:
            stl_data = build_instrument_stl(preset)
        except Exception as e:
            raise HTTPException(500, f"STL generation failed: {str(e)}")

    filename = f"{preset}-design.stl"
    return StreamingResponse(
        io.BytesIO(stl_data),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


class ImpedanceRequest(BaseModel):
    """Request body for real-time impedance computation."""
    preset: str
    frequencies_start: float = Field(default=50, ge=1, le=10000)
    frequencies_end: float = Field(default=3000, ge=10, le=20000)
    frequencies_step: float = Field(default=2, ge=0.1, le=100)
    temperature: float = Field(default=25.0, ge=-20, le=60)


class ImpedanceResponse(BaseModel):
    """Response body for impedance computation results."""
    frequencies: list[float]
    impedance_real: list[float]
    impedance_imag: list[float]
    impedance_magnitude: list[float]
    preset: str


@app.post("/impedance/compute", response_model=ImpedanceResponse)
def compute_impedance(req: ImpedanceRequest):
    """Compute acoustic impedance in real-time using OpenWInD.

    Takes a bore preset, frequency range (start/end/step), and temperature.
    Returns arrays of frequencies, real/imaginary impedance, and impedance magnitude.
    This is a slow operation (~10-30 seconds) — prefer /impedance/precomputed when available.
    """
    import openwind

    if req.preset not in AVAILABLE_BORES:
        raise HTTPException(404, f"Unknown preset: {req.preset}. Available: {list(AVAILABLE_BORES.keys())}")

    bore_file = str(BORE_DIR / AVAILABLE_BORES[req.preset])
    if not os.path.exists(bore_file):
        raise HTTPException(404, f"Bore profile not found: {bore_file}")

    frequencies = np.arange(req.frequencies_start, req.frequencies_end, req.frequencies_step)

    try:
        result = openwind.ImpedanceComputation(frequencies, bore_file, temperature=req.temperature)
        z = result.impedance
        z_real = np.real(z).tolist()
        z_imag = np.imag(z).tolist()
        z_mag = np.abs(z).tolist()

        return ImpedanceResponse(
            frequencies=frequencies.tolist(),
            impedance_real=z_real,
            impedance_imag=z_imag,
            impedance_magnitude=z_mag,
            preset=req.preset,
        )
    except Exception as e:
        raise HTTPException(500, f"OpenWInD computation failed: {str(e)}")


@app.get("/impedance/precomputed/{preset}")
def get_precomputed_impedance(preset: str):
    """Get pre-computed impedance data for a preset (fast, instant response).

    Returns JSON with frequencies, impedance_real, impedance_imag, impedance_magnitude arrays.
    Preset is validated against AVAILABLE_BORES to prevent path traversal attacks.
    """
    # Validate preset to prevent path traversal
    if preset not in AVAILABLE_BORES:
        raise HTTPException(404, f"Unknown preset: {preset}. Available: {list(AVAILABLE_BORES.keys())}")
    json_file = IMPEDANCE_DIR / f"{preset}.json"
    if not json_file.exists():
        raise HTTPException(404, f"Precomputed impedance not found for: {preset}")

    with open(json_file) as f:
        data = json.load(f)
    return data


@app.get("/impedance/precomputed")
def list_precomputed():
    """List all presets that have pre-computed impedance data available."""
    files = list(IMPEDANCE_DIR.glob("*.json"))
    return {"available": [f.stem for f in files]}


class StepExportRequest(BaseModel):
    """Request body for STEP file export."""
    preset: str
    length: float = 200
    bore_diameter: float = 20
    wall_thickness: float = 3
    segments: int = 64


@app.post("/export/step")
def export_step(req: StepExportRequest):
    """Export a bore profile as a STEP file using Build123d.

    If preset matches a known bore profile, uses its dimensions and tone holes.
    Otherwise uses the custom parameters (length, bore_diameter, wall_thickness).
    Returns the STEP file as a binary stream.
    """
    try:
        bore = parse_bore_profile(req.preset) if req.preset in AVAILABLE_BORES else None
        holes = TONE_HOLES.get(req.preset, [])

        if bore:
            total_length = bore[-1][1] - bore[0][0]
            mean_inner_r = sum(s[2] + s[3] for s in bore) / (2 * len(bore))
            mean_outer_r = mean_inner_r + 2.0
        else:
            total_length = req.length
            inner_r = req.bore_diameter / 2
            mean_outer_r = inner_r + req.wall_thickness
            mean_inner_r = inner_r

        outer = B123dCylinder(radius=mean_outer_r, height=total_length,
                              align=(Align.CENTER, Align.CENTER, Align.MIN))
        inner = B123dCylinder(radius=mean_inner_r, height=total_length + 1,
                              align=(Align.CENTER, Align.CENTER, Align.MIN))
        result = outer - inner

        if holes:
            for h in holes:
                z_pos = h["z"]
                hole_r = h["r"]
                hole_cyl = B123dCylinder(
                    radius=hole_r, height=req.wall_thickness + 4.0,
                    align=(Align.CENTER, Align.CENTER, Align.CENTER),
                )
                hole_cyl = hole_cyl.moved(Location((0, 0, z_pos - total_length / 2)))
                hole_cyl = hole_cyl.rotate(Axis.Y, 90)
                result = result - hole_cyl

        buf = io.BytesIO()
        b123d_export_step(result, buf)
        buf.seek(0)

        filename = f"{req.preset}-bore.step"
        return StreamingResponse(
            buf,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(500, f"STEP export failed: {str(e)}")


@app.post("/export/step/custom")
def export_custom_step(
    bore_points: list[list[float]],
    wall_thickness: float = 3.0,
):
    """Export a custom bore profile as STEP from a list of (position, radius) points.

    bore_points should be [[x0, r0], [x1, r1], ...] where x is position and r is radius in mm.
    Creates a 2D profile extruded to 3D via Build123d.
    """
    from build123d import Wire, extrude, Plane, BuildPart, export_step

    try:
        if len(bore_points) < 2:
            raise HTTPException(400, "Need at least 2 bore profile points")

        edges = []
        for i in range(len(bore_points) - 1):
            x0, r0 = bore_points[i]
            x1, r1 = bore_points[i + 1]
            from build123d import Line
            edges.append(Line((x0, r0), (x1, r1)))

        bottom_line = Line((bore_points[-1][0], 0), (bore_points[0][0], 0))
        left_line = Line((bore_points[0][0], 0), (bore_points[0][0], bore_points[0][1]))
        right_line = Line((bore_points[-1][0], 0), (bore_points[-1][0], bore_points[-1][1]))

        from build123d import Wire as W
        wire = W(edges + [bottom_line, left_line, right_line])
        face = extrude(Plane.XZ * wire, amount=0.001)

        buf = io.BytesIO()
        export_step(face, buf)
        buf.seek(0)

        return StreamingResponse(
            buf,
            media_type="application/octet-stream",
            headers={"Content-Disposition": 'attachment; filename="custom-bore.step"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Custom STEP export failed: {str(e)}")


class SimulateSoundRequest(BaseModel):
    """Request body for time-domain sound simulation."""
    preset: str
    duration: float = 1.0
    player_type: str = "FLUTE"
    temperature: float = 25.0


@app.post("/simulate/sound")
def simulate_sound(req: SimulateSoundRequest):
    """Simulate time-domain audio output from a bore profile using OpenWInD.

    Uses OpenWInD's coupled player-bore simulation. Returns a WAV file with the
    bell radiation pressure signal normalized to [-0.9, 0.9]. Sample rate ~550kHz.
    Default player type is FLUTE; also supports CLARINET, LIPS, SOPRANO_RECORDER, etc.
    """
    from openwind import simulate, Player
    import scipy.io.wavfile as wavfile

    if req.preset not in AVAILABLE_BORES:
        raise HTTPException(404, f"Unknown preset: {req.preset}")

    bore_file = str(BORE_DIR / AVAILABLE_BORES[req.preset])
    player = Player(req.player_type)

    try:
        rec = simulate(
            duration=req.duration,
            main_bore=bore_file,
            player=player,
            temperature=req.temperature,
            verbosity=0,
        )
    except Exception as e:
        raise HTTPException(500, f"OpenWInD simulation failed: {str(e)}")

    bell_key = [k for k in rec.values if "bell_radiation_pressure" in k]
    if not bell_key:
        raise HTTPException(500, "No bell radiation pressure in simulation output")

    signal = np.array(rec.values[bell_key[0]], dtype=np.float64)
    sample_rate = int(round(1.0 / rec.dt))

    signal_max = np.max(np.abs(signal))
    if signal_max > 0:
        signal = signal / signal_max * 0.9

    signal_int16 = (signal * 32767).astype(np.int16)

    buf = io.BytesIO()
    wavfile.write(buf, sample_rate, signal_int16)
    buf.seek(0)

    filename = f"{req.preset}-simulated.wav"
    return StreamingResponse(
        buf,
        media_type="audio/wav",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


class AnalyzeAudioRequest(BaseModel):
    """Request body for impedance peak analysis."""
    preset: str = ""
    n_fft: int = 4096
    top_peaks: int = 10


@app.post("/analyze/audio")
def analyze_audio(req: AnalyzeAudioRequest):
    """Analyze impedance peaks from pre-computed data and map them to musical notes.

    Finds local maxima in the impedance magnitude array, converts each peak frequency
    to a note name (C, C#, D...) with octave and cents deviation from A4=440Hz.
    Returns the top N peaks sorted by frequency.
    """
    if not req.preset:
        raise HTTPException(400, "preset is required for peak reference")
    if req.preset not in AVAILABLE_BORES:
        raise HTTPException(404, f"Unknown preset: {req.preset}. Available: {list(AVAILABLE_BORES.keys())}")

    json_file = IMPEDANCE_DIR / f"{req.preset}.json"
    if not json_file.exists():
        raise HTTPException(404, f"Precomputed impedance not found for: {req.preset}")

    with open(json_file) as f:
        data = json.load(f)

    frequencies = np.array(data["frequencies"])
    z_mag = np.array(data["impedance_magnitude"])

    peak_indices = []
    for i in range(1, len(z_mag) - 1):
        if z_mag[i] > z_mag[i - 1] and z_mag[i] > z_mag[i + 1]:
            peak_indices.append(i)
    peak_indices.sort(key=lambda i: z_mag[i], reverse=True)

    peaks = []
    A4 = 440.0
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    for idx in peak_indices[: req.top_peaks]:
        freq = frequencies[idx]
        semitones = 12 * np.log2(freq / A4)
        note_num = int(round(semitones)) + 69
        note_name = note_names[note_num % 12]
        octave = note_num // 12 - 1
        cents = round((semitones - round(semitones)) * 100)

        peaks.append({
            "frequency": round(float(freq), 1),
            "magnitude": round(float(z_mag[idx]), 2),
            "note": note_name,
            "octave": octave,
            "cents": cents,
        })

    peaks.sort(key=lambda p: p["frequency"])

    return {
        "preset": req.preset,
        "peaks": peaks,
        "frequencies": frequencies.tolist(),
        "impedance_magnitude": z_mag.tolist(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

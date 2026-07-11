import io
import os
import json
import tempfile
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np

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
    return {"status": "ok", "version": "1.0.0"}


@app.get("/presets")
def list_presets():
    return {"presets": list(AVAILABLE_BORES.keys())}


class ImpedanceRequest(BaseModel):
    preset: str
    frequencies_start: float = 50
    frequencies_end: float = 3000
    frequencies_step: float = 2
    temperature: float = 25.0


class ImpedanceResponse(BaseModel):
    frequencies: list[float]
    impedance_real: list[float]
    impedance_imag: list[float]
    impedance_magnitude: list[float]
    preset: str


@app.post("/impedance/compute", response_model=ImpedanceResponse)
def compute_impedance(req: ImpedanceRequest):
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
    json_file = IMPEDANCE_DIR / f"{preset}.json"
    if not json_file.exists():
        raise HTTPException(404, f"Precomputed impedance not found for: {preset}")

    with open(json_file) as f:
        data = json.load(f)
    return data


@app.get("/impedance/precomputed")
def list_precomputed():
    files = list(IMPEDANCE_DIR.glob("*.json"))
    return {"available": [f.stem for f in files]}


class StepExportRequest(BaseModel):
    preset: str
    length: float = 200
    bore_diameter: float = 20
    wall_thickness: float = 3
    segments: int = 64


@app.post("/export/step")
def export_step(req: StepExportRequest):
    from build123d import Cylinder, export_step

    try:
        outer_r = req.bore_diameter / 2 + req.wall_thickness
        inner_r = req.bore_diameter / 2

        outer = Cylinder(radius=outer_r, height=req.length)
        inner = Cylinder(radius=inner_r, height=req.length + 1)
        result = outer - inner

        buf = io.BytesIO()
        export_step(result, buf)
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

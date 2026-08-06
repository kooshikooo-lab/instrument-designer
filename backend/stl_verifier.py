"""STL visual verifier agent.

Renders an STL to multi-view images with VTK and asks a vision-capable
LLM (via OpenRouter) to verify the mesh against expected geometry,
complementing numeric checks (volume, watertightness, bbox).

Pipeline::
    render_mesh_views(stl)        -> {view_name: png_bytes}
    ask_vision(images, prompt)    -> LLM text answer
    verify_stl(stl, expected)     -> VerifyReport (numeric + visual)

The numeric checks run locally with trimesh. The visual check only runs
when a vision model is configured (OPENROUTER_API_KEY set).

CLI::
    python -m backend.stl_verifier stl_library/flat/contra_bass_clarinet_Bb.stl
    python -m backend.stl_verifier --all
"""

from __future__ import annotations

import base64
import io
import json
import os
import tempfile
from dataclasses import dataclass, field, asdict
from pathlib import Path

import numpy as np

# The strongest free vision model verified on this project's OpenRouter key.
DEFAULT_VISION_MODEL = os.environ.get(
    "VISION_MODEL", "google/gemma-4-31b-it:free"
)
# Fallbacks tried in order when a provider is rate-limited or down.
FALLBACK_VISION_MODELS = [
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
]
VISION_BASE = "https://openrouter.ai/api/v1"


# ── Numeric mesh checks (no LLM needed) ────────────────────────────────────

def _is_manifold(mesh) -> bool:
    """True when no edge is shared by more than two faces (edge valence <= 2).

    The classic STL solid is watertight *and* manifold: every edge borders
    exactly two triangles. An edge shared by 3+ triangles is a non-manifold
    (e.g. two walls fused along a seam), which slicing software and SDF/CAD
    kernels reject even when the shell looks closed.
    """
    edges = mesh.edges_sorted
    if edges.size == 0:
        return False
    _, counts = np.unique(edges, axis=0, return_counts=True)
    return bool(int((counts > 2).sum()) == 0)


def _component_count(mesh) -> int:
    """Number of connected components (separate shells) in the mesh.

    A single printable solid must be one component. Two watertight shells that
    do not touch (e.g. a tube with a detached floating cap) still pass
    watertight+manifold but are NOT one solid — slicing and CAD kernels treat
    them as separate bodies, and the repair gate must reject them.
    """
    if len(mesh.faces) == 0:
        return 0
    return len(mesh.split(only_watertight=False))


@dataclass
class MeshMetrics:
    """Numeric facts about a mesh, computed locally with trimesh."""

    vertex_count: int
    face_count: int
    watertight: bool
    manifold: bool
    component_count: int
    volume_mm3: float
    bbox_mm: list  # [x, y, z]
    z_extent_mm: float
    open_bounds: int = 0  # boundary edges forming holes (0 = closed shell)


def compute_mesh_metrics(stl_path: str) -> MeshMetrics:
    """Compute numeric mesh metrics with trimesh."""
    import trimesh

    m = trimesh.load(stl_path, force="mesh")
    bbox = m.bounds[1] - m.bounds[0]
    return MeshMetrics(
        vertex_count=len(m.vertices),
        face_count=len(m.faces),
        watertight=bool(m.is_watertight),
        manifold=_is_manifold(m),
        component_count=_component_count(m),
        volume_mm3=float(m.volume),
        bbox_mm=[round(float(v), 1) for v in bbox],
        z_extent_mm=round(float(bbox[2]), 1),
        open_bounds=int(m.area > 0 and not m.is_watertight),
    )


def check_mesh_repair_gate(stl_path: str) -> dict:
    """Check-only mesh-repair gate (see ``docs/TOOLS.md`` protocol).

    A mesh passes when it is **watertight AND manifold AND a single connected
    component** (every edge borders exactly two triangles, and the mesh is one
    closed solid — not a compound of separate shells). This is the numeric gate
    ``cadquery_export.export_stl`` runs after writing a mesh; per the
    build123d-first + repair-fallback decision it is advisory (logs a warning,
    never fails the export).

    Returns a plain dict (not :class:`MeshMetrics`) so callers without dataclass
    plumbing can read it easily. Never raises.
    """
    try:
        metrics = compute_mesh_metrics(stl_path)
    except Exception as e:  # noqa: BLE001 — gate is advisory
        return {"stl": os.path.basename(stl_path), "passed": False, "error": str(e)}
    passed = bool(
        metrics.watertight and metrics.manifold and metrics.component_count == 1
    )
    return {
        "stl": os.path.basename(stl_path),
        "passed": passed,
        "watertight": metrics.watertight,
        "manifold": metrics.manifold,
        "component_count": metrics.component_count,
        "vertex_count": metrics.vertex_count,
        "face_count": metrics.face_count,
        "volume_mm3": metrics.volume_mm3,
    }


# ── VTK multi-view renderer ────────────────────────────────────────────────

def _make_polydata(mesh):
    import vtk

    polydata = vtk.vtkPolyData()
    pts = vtk.vtkPoints()
    pts.SetNumberOfPoints(len(mesh.vertices))
    for i, v in enumerate(mesh.vertices):
        pts.SetPoint(i, float(v[0]), float(v[1]), float(v[2]))
    polydata.SetPoints(pts)
    polys = vtk.vtkCellArray()
    for f in mesh.faces:
        polys.InsertNextCell(3, (int(f[0]), int(f[1]), int(f[2])))
    polydata.SetPolys(polys)
    return polydata


def _vtk_render(mesh, camera_position, size=(768, 768)) -> bytes:
    """Render a trimesh to PNG bytes from a given camera position."""
    import vtk

    polydata = _make_polydata(mesh)

    ren = vtk.vtkRenderer()
    ren.SetBackground(0.95, 0.95, 0.95)

    ren_win = vtk.vtkRenderWindow()
    ren_win.SetOffScreenRendering(1)
    ren_win.AddRenderer(ren)
    ren_win.SetSize(*size)

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(polydata)
    mapper.ScalarVisibilityOff()

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(0.15, 0.35, 0.75)
    actor.GetProperty().SetAmbient(0.35)
    actor.GetProperty().SetDiffuse(0.6)
    actor.GetProperty().SetSpecular(0.2)
    ren.AddActor(actor)

    bounds = polydata.GetBounds()
    cx = (bounds[0] + bounds[1]) / 2
    cy = (bounds[2] + bounds[3]) / 2
    cz = (bounds[4] + bounds[5]) / 2
    dx = bounds[1] - bounds[0]
    dy = bounds[3] - bounds[2]
    dz = bounds[5] - bounds[4]
    dist = max(dx, dy, dz) * 2.6 + 10

    camera = ren.GetActiveCamera()
    camera.SetPosition(cx + camera_position[0] * dist,
                       cy + camera_position[1] * dist,
                       cz + camera_position[2] * dist)
    camera.SetFocalPoint(cx, cy, cz)
    # View-up: Z for horizontal views; X for the top-down view so the
    # view-up vector is not parallel to the camera view direction.
    view_up = (1.0, 0.0, 0.0) if camera_position[2] else (0.0, 0.0, 1.0)
    camera.SetViewUp(*view_up)
    ren.ResetCamera()
    ren_win.Render()

    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(ren_win)
    w2i.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetWriteToMemory(1)
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()
    data = writer.GetResult()
    return bytes(memoryview(data))


VIEWS = {
    # name: (camera x, y, z) offset around target
    "front": (1.0, 0.0, 0.0),
    "side": (0.0, -1.0, 0.0),
    "isometric": (0.6, -0.8, 0.6),
    "top": (0.0, 0.0, 1.0),
}


def render_mesh_views(stl_path: str, size=(768, 768)) -> dict[str, bytes]:
    """Render front/side/isometric/top views of an STL to PNG bytes."""
    import trimesh

    mesh = trimesh.load(stl_path, force="mesh")
    return {
        name: _vtk_render(mesh, camera, size=size)
        for name, camera in VIEWS.items()
    }


# ── Multimodal client ──────────────────────────────────────────────────────

def _data_uri(png_bytes: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png_bytes).decode()


def ask_vision(images: dict[str, bytes], prompt: str,
               model: str = "") -> str:
    """Send images + prompt to a vision model via OpenRouter.

    Tries :data:`DEFAULT_VISION_MODEL` (or ``model`` if given) first, then
    each :data:`FALLBACK_VISION_MODELS` entry in order. Retries 429/5xx with
    exponential backoff. Returns the first successful reply, or an error
    string prefixed with "[ERROR]".
    """
    import requests

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        return "[ERROR] OPENROUTER_API_KEY not set"

    content = [{"type": "text", "text": prompt}]
    for label, png in images.items():
        content.append({
            "type": "image_url",
            "image_url": {"url": _data_uri(png)},
        })

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    models = [model or DEFAULT_VISION_MODEL] + FALLBACK_VISION_MODELS
    for attempt, model_id in enumerate(models):
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": 2048,
            "temperature": 0.2,
        }
        for backoff in (2, 4, 8):
            try:
                resp = requests.post(
                    f"{VISION_BASE}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=180,
                )
                if resp.status_code == 429 or resp.status_code >= 500:
                    import time

                    time.sleep(backoff)
                    continue
                resp.raise_for_status()
                data = resp.json()
                msg = data["choices"][0]["message"]
                return msg.get("content") or msg.get("reasoning") or "[ERROR] empty reply"
            except Exception as e:  # noqa: BLE001
                return f"[ERROR] {model_id}: {type(e).__name__}: {e}"
    return "[ERROR] all vision models rate-limited or unavailable"


VERIFY_SYSTEM_PROMPT = """You are a CAD quality-control inspector for 3D-printed woodwind instruments.
You are shown multiple rendered views (front, side, isometric, top) of ONE STL mesh.
Check the model against the expected geometry supplied in the request.

Rules:
- The mesh may be a straight tube, a tapered (conical) tube, or a folded
  'paperclip' U-bend (two parallel legs joined by a 180-degree bend).
- For a folded instrument, verify BOTH legs are present and joined by a bend
  (not just a short elbow/junction).
- Look for tone holes: circular holes through the tube wall. Holes often
  alternate between opposite sides of the tube, so from a single view only a
  subset may be visible; give your best low-bound estimate and do not fail the
  check solely on hole count.
- A hollow tube must show an open bore at the ends (you can see the inner wall).
  A solid rod shows no inner bore.
- Compare overall proportions (length vs width) against the expected bbox size.

Answer with a SHORT JSON object only, no markdown fences:
{"shape": "...", "hollow": true|false, "tone_holes_visible": true|false,
 "tone_hole_count_estimate": int, "folded_paperclip": true|false,
 "matches_expected": true|false, "issues": ["..."], "notes": "..."}
"""


# ── Verifier orchestration ─────────────────────────────────────────────────

@dataclass
class VerifyReport:
    file: str
    metrics: dict = field(default_factory=dict)
    visual: dict = field(default_factory=dict)
    passed: bool = False
    errors: list = field(default_factory=list)


def _parse_verdict(text: str) -> dict:
    """Best-effort parse of the vision model's JSON answer."""
    if text.startswith("[ERROR]"):
        return {"error": text}
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return {"error": f"no JSON found in reply: {text[:200]}"}
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return {"error": f"bad JSON: {text[start:end + 1][:300]}"}


def _expected_prompt(expected: dict | None) -> str:
    if not expected:
        return "Expected: a woodwind instrument body (unknown exact shape)."
    parts = [f"Expected geometry: {expected.get('display_name', 'instrument')}"]
    if expected.get("bend_radius_mm"):
        parts.append("This is a FOLDED paperclip U-bend instrument.")
    if expected.get("expected_hollow"):
        parts.append("This instrument must have a HOLLOW bore (open tube, not a solid rod).")
    if expected.get("bbox_mm"):
        parts.append(f"Expected bbox (x,y,z) mm: {expected['bbox_mm']}")
    if expected.get("n_holes") is not None:
        parts.append(f"Expected ~{expected['n_holes']} tone holes on the straight legs.")
    return "\n".join(parts)


def verify_stl(stl_path: str, expected: dict | None = None,
               vision_model: str = "", use_vision: bool | None = None) -> VerifyReport:
    """Verify one STL: local numeric checks + (optional) vision check.

    Args:
        stl_path: path to the STL to verify.
        expected: expected-geometry dict (see _build_expected_registry).
        vision_model: OpenRouter vision model id ('' = default).
        use_vision: override whether to run the vision model. Defaults to
            None = auto (run if OPENROUTER_API_KEY is set).
    """
    report = VerifyReport(file=os.path.basename(stl_path))
    try:
        metrics = compute_mesh_metrics(stl_path)
        report.metrics = asdict(metrics)
    except Exception as e:  # noqa: BLE001
        report.errors.append(f"metrics: {e}")
        report.passed = False
        return report

    # Numeric pass/fail: sane bbox + nonzero volume
    checks = []
    z = report.metrics["z_extent_mm"]
    vol = report.metrics["volume_mm3"]
    if z > 0 and vol > 0:
        checks.append("numeric_basic")
    if expected and expected.get("bbox_mm"):
        exp = expected["bbox_mm"]
        got = report.metrics["bbox_mm"]
        ratios = [got[i] / exp[i] if exp[i] else 1 for i in range(3)]
        if all(0.5 <= r <= 2.0 for r in ratios):
            checks.append("bbox_match")
    report.metrics["checks"] = checks

    # Visual check (skip if vision disabled or no API key)
    run_vision = (use_vision is not None) and use_vision
    if use_vision is None:
        run_vision = bool(os.environ.get("OPENROUTER_API_KEY"))
    if not run_vision:
        report.visual = {"skipped": "vision disabled or OPENROUTER_API_KEY not set"}
        report.passed = bool(checks)
        return report

    try:
        views = render_mesh_views(stl_path)
        prompt = (
            VERIFY_SYSTEM_PROMPT
            + "\n\n"
            + _expected_prompt(expected)
            + "\n\nImages (front, side, isometric, top):"
        )
        answer = ask_vision(views, prompt, vision_model)
        verdict = _parse_verdict(answer)
        report.visual = verdict
        report.visual["views"] = list(views.keys())
        report.passed = _compute_passed(checks, verdict, expected)
    except Exception as e:  # noqa: BLE001
        report.visual = {"error": str(e)}
        report.passed = bool(checks)

    return report


def _compute_passed(checks: list, verdict: dict,
                    expected: dict | None) -> bool:
    """Pass = numeric sanity + vision agrees on folded/hollow.

    Hole count is advisory only (holes alternate ±X and are undercounted in
    2D renders), so it never gates the verdict by itself.
    """
    if not checks:
        return False
    if verdict.get("error"):
        return False
    vision_ok = True
    if expected and expected.get("bend_radius_mm"):
        vision_ok = vision_ok and bool(verdict.get("folded_paperclip"))
    if expected and expected.get("expected_hollow"):
        vision_ok = vision_ok and bool(verdict.get("hollow"))
    return vision_ok


def verify_many(stl_paths: list[str], expected_by_name: dict | None = None,
                vision_model: str = "", workers: int = 4,
                progress: bool = True,
                use_vision: bool | None = None) -> list[VerifyReport]:
    """Verify a list of STLs in parallel (thread pool).

    Args:
        stl_paths: STL paths to verify.
        expected_by_name: filename stem -> expected geometry dict.
        vision_model: OpenRouter vision model id ('' = default).
        workers: number of parallel threads. Vision calls dominate the wall
            time; the free tier rate-limits heavily, so a small pool (3-4)
            with in-process fallback/backoff is safer than a large one.
        progress: print "[i/total] file" as each finishes (unless called from
            a context that suppresses it).
        use_vision: pass through to verify_stl (None = auto).
    """
    import threading

    from concurrent.futures import ThreadPoolExecutor, as_completed

    expected_by_name = expected_by_name or {}
    lock = threading.Lock()
    done = 0
    reports = []

    def _run(path):
        name = Path(path).stem
        expected = expected_by_name.get(name)
        return path, verify_stl(path, expected, vision_model,
                                use_vision=use_vision)

    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        futures = [ex.submit(_run, p) for p in stl_paths]
        for fut in as_completed(futures):
            path, report = fut.result()
            with lock:
                reports.append(report)
                done += 1
                if progress:
                    status = "PASS" if report.passed else "FAIL"
                    print(f"[{done}/{len(stl_paths)}] [{status}] "
                          f"{os.path.basename(path)}", flush=True)
    reports.sort(key=lambda r: r.file)
    return reports


def _max_diameter(spec) -> float:
    """Resolve bore_diameter to a max outer diameter (scalar or (d_in,d_out))."""
    d = spec["bore_diameter"]
    return max(d) if isinstance(d, (tuple, list)) else float(d)


def _build_expected_registry() -> dict[str, dict]:
    """Map STL filename stem -> expected geometry from INSTRUMENTS presets."""
    try:
        from backend.cadquery_export import INSTRUMENTS, generate_folded_bore_instrument

        registry = {}
        for key, spec in INSTRUMENTS.items():
            if "_meta" not in spec:
                continue
            meta = spec["_meta"]
            n_holes = len(spec.get("holes", []))
            if spec.get("bend_radius_mm"):
                solid = generate_folded_bore_instrument(
                    bore_length=spec["bore_length"],
                    bore_diameter=spec["bore_diameter"],
                    wall_thickness=spec["wall_thickness"],
                    bend_radius_mm=spec["bend_radius_mm"],
                    holes=spec.get("holes", []),
                    closed_top=spec.get("closed_top", False),
                )
                bb = solid.val().BoundingBox()
                bbox = [round(bb.xmax - bb.xmin, 1),
                        round(bb.ymax - bb.ymin, 1),
                        round(bb.zmax - bb.zmin, 1)]
            else:
                diam = _max_diameter(spec)
                bbox = [
                    round(diam + 2 * spec["wall_thickness"], 1),
                    round(diam + 2 * spec["wall_thickness"], 1),
                    round(spec["bore_length"] + 2 * spec["wall_thickness"], 1),
                ]
            registry[key] = {
                "display_name": meta.get("display_name", key),
                "bend_radius_mm": spec.get("bend_radius_mm"),
                "bbox_mm": bbox,
                "n_holes": n_holes,
                "expected_hollow": True,
            }
        return registry
    except Exception as e:  # noqa: BLE001
        return {"_error": str(e)}


# ── CLI ────────────────────────────────────────────────────────────────────

def _cli():
    import argparse
    import glob as globmod

    parser = argparse.ArgumentParser(description="STL visual verifier agent")
    parser.add_argument("stl", nargs="*", help="STL path(s) to verify")
    parser.add_argument("--all", action="store_true",
                        help="Verify every STL in stl_library/flat")
    parser.add_argument("--limit", type=int, default=0,
                        help="Only verify the first N STLs (for smoke tests)")
    parser.add_argument("--no-vision", action="store_true",
                        help="Numeric checks only (skip vision model)")
    parser.add_argument("--workers", type=int, default=4,
                        help="Parallel worker threads (default 4)")
    parser.add_argument("--model", default="",
                        help=f"OpenRouter vision model (default {DEFAULT_VISION_MODEL})")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args()

    if args.all:
        base = Path(__file__).parent.parent / "stl_library" / "flat"
        stls = sorted(globmod.glob(str(base / "*.stl")))
    else:
        stls = args.stl

    if not stls:
        parser.error("provide an STL path or --all")

    if args.limit > 0:
        stls = stls[: args.limit]

    expected = _build_expected_registry()
    if not args.no_vision and not os.environ.get("OPENROUTER_API_KEY"):
        print("Note: OPENROUTER_API_KEY not set — numeric checks only. "
              "Set it to enable the vision agent.")
        args.no_vision = True

    reports = verify_many(stls, expected if expected else None,
                          "" if args.no_vision else args.model,
                          workers=args.workers,
                          progress=not args.json,
                          use_vision=False if args.no_vision else None)

    if args.json:
        print(json.dumps([asdict(r) for r in reports], indent=2))
        return

    for r in reports:
        status = "PASS" if r.passed else "FAIL"
        print(f"\n[{status}] {r.file}")
        m = r.metrics
        if m:
            print(f"  bbox(x,y,z)={m.get('bbox_mm')}  vol={m.get('volume_mm3', 0):.0f}mm3 "
                  f"watertight={m.get('watertight')} manifold={m.get('manifold')} "
                  f"verts={m.get('vertex_count')}")
        v = r.visual
        if v and not v.get("skipped"):
            print(f"  shape={v.get('shape')}  hollow={v.get('hollow')} "
                  f"folded={v.get('folded_paperclip')} holes={v.get('tone_hole_count_estimate')}")
            print(f"  matches_expected={v.get('matches_expected')}")
            for issue in v.get("issues", []) or []:
                print(f"    issue: {issue}")
        for e in r.errors:
            print(f"  ERROR: {e}")


if __name__ == "__main__":
    _cli()

# build123d-mcp Deep Dive

**Date:** 2026-07-18
**Repository:** https://github.com/pzfreo/build123d-mcp
**Author:** Paul Fremantle (pzfreo)
**License:** Apache 2.0
**Latest Version:** v0.3.79 (79 releases)
**Stars:** 31 | **Forks:** 6 | **Language:** Python 100%

---

## 1. What It Is

build123d-mcp is an **MCP (Model Context Protocol) server** that wraps the [build123d](https://github.com/gumyr/build123d) Python CAD library. It is NOT a standalone chatbot or CAD program — it's a **CAD toolbox** that AI/LLM apps (Claude, Cursor, VS Code, Continue, Cline, Codex CLI) can call through MCP.

**Tagline:** "Give your AI CAD eyes."

**Core problem it solves:** When an AI writes build123d scripts without this server, it writes **blind** — it cannot see the geometry it produces. build123d-mcp closes the feedback loop: the AI can create geometry, render views, query dimensions, and catch errors incrementally rather than writing complete scripts and hoping they work.

**Performance:** On the public [CADGenBench](https://huggingface.co/spaces/HuggingAI4Engineering/CADGenBench) leaderboard (June 2026), using build123d-mcp raised the same model's score from 0.360 to 0.457 and CAD validity from 88% to 100%.

---

## 2. How It Works (Architecture)

### The Loop

1. **Agent writes Python** (build123d code) → sends via MCP `execute()` tool
2. **Server executes** the code in a persistent Python session (sandboxed)
3. **Agent queries geometry** via `measure()`, `render_view()`, `validate()`
4. **Agent iterates** — fixes mistakes, adds features, re-verifies
5. **Agent exports** — STEP, STL, DXF, SVG

### Key Concept: Persistent Session

All `execute()` calls share a **single Python namespace**. Variables and shapes persist across calls. This allows incremental construction:
```python
# execute() call 1:
from build123d import *
frame = Box(60, 40, 8)
show(frame, "frame")

# execute() call 2:
axle = Cylinder(5, 50)
show(axle, "axle")
```

### Multi-Object Sessions

Use `show(shape, name)` inside `execute` to register named objects. Tools like `measure()`, `render_view()`, `export()` can target specific objects by name.

### Sandbox (3 layers)

Every `execute()` call is sandboxed:
1. **Import allowlist** — only `build123d`, `math`, `numpy`, safe stdlib. `os`, `pathlib`, `subprocess`, `socket` are BLOCKED.
2. **Restricted builtins** — `open`, `eval`, `exec`, `compile`, `breakpoint`, `input` are removed. `hasattr` and `dir()` allowed.
3. **Execution timeout** — wall-clock limit (default 120s, configurable).

The sandbox can be lifted with `--no-sandbox` in trusted environments.

### Transport

- **Default:** stdio (subprocess per client process) — isolated sessions
- **HTTP mode:** `--transport http` for web/container/remote deployments (shared session, no built-in auth)

### Source Code Structure

```
src/build123d_mcp/
├── server.py              # MCP server entry point, tool registration
├── session.py             # Persistent build123d session management
├── worker.py              # Worker for sandboxed execution
├── cli.py                 # CLI entry point
├── security.py            # AST inspection, sandbox enforcement
├── viewer.py              # Live viewer socket publisher
├── quickref.py            # build123d API quick reference
├── selectors_cookbook.py  # Selector cookbook
├── drafting_cookbook.py   # 2D engineering drawing cookbook
├── presentation_cookbook.py
├── bd_warehouse_resource.py
├── skills/                # Workflow skill files (modeling, drawing, repair)
├── tools/                 # Individual tool implementations
│   ├── execute.py
│   ├── render.py
│   ├── measure.py
│   ├── export.py
│   ├── recognize.py       # Feature recognition (holes, bosses, countersinks)
│   ├── compare.py
│   ├── validate.py
│   ├── design_audit.py
│   ├── verify_spec.py
│   ├── align_check.py
│   ├── resolve.py
│   ├── script.py
│   └── ...
├── _tessellate_subprocess.py    # Out-of-process tessellation
├── _vtk_render_subprocess_worker.py  # Out-of-process VTK rendering
├── _shape_compare_subprocess.py
├── _shape_op_subprocess.py
├── _design_audit_subprocess.py
├── _gate_subprocess.py
└── _locate_subprocess.py
```

---

## 3. Complete Tool List (31+ Tools)

### Core

| Tool | Description |
|------|-------------|
| `execute` | Run build123d Python code in the persistent session. Use `show(shape, name)` to register named parts. |
| `reset` | Clear session back to empty state (namespace, shapes, snapshots) |

### Geometry Inspection

| Tool | Description |
|------|-------------|
| `measure` | Full geometric summary: volume, area, topology, bounding box, centre of mass, inertia tensor, face-type inventory. Supports density/mass calculation. |
| `clearance` | Minimum distance (mm) between two named shapes. Reports status: apart/touching/containing/interpenetrating. |
| `cross_sections` | Cross-sectional areas at evenly spaced planes along X/Y/Z. Useful for detecting voids and wall-thickness variation. |
| `resolve` | Evaluate a selector expression against a named object, return geometry descriptor. |
| `validate` | Fast validity screen: BRepCheck, watertight, manifold, non-zero volume. Returns PASS/FAIL. |

### Feature Recognition

| Tool | Description |
|------|-------------|
| `find_holes` | Coaxial drill + counterbore + spotface stacks as one hole record (axis, location, diameter, depth, bottom type). |
| `find_bosses` | External bosses with height. |
| `find_hole_patterns` | Bolt-circle and linear-array patterns. |
| `find_countersinks` | Conical countersinks (major/drill diameter, included angle, depth). |

### Advanced Analysis

| Tool | Description |
|------|-------------|
| `analyze_printability` | BREP-exact FDM printability analysis: overhangs, thin walls, minimum features, bed fit, tip-over risk. |
| `design_audit` | Audit the session program as a *design*: surfaces named numeric parameters, perturbs each ±ε, re-runs validity gate to flag brittle parameters. |
| `verify_spec` | Check built solid against declared design-intent spec (experimental, off by default). |
| `suggest_spec` | Draft a verify_spec spec from current shape (experimental). |

### Viewing

| Tool | Description |
|------|-------------|
| `render_view` | Render shapes as PNG/SVG/DXF. Auto-detects 3D vs 2D. Supports assembly compositing, high-quality tessellation, cross-section clip planes, labels for named shapes/faces/edges. |

### Engineering Drawings

| Tool | Description |
|------|-------------|
| `suggest_view_layout` | Auto-calculate safe page positions for multi-view drawing layout. |
| `view_axes` | World-to-page axis mapping for projected view. |
| `render_drawing` | Rasterise SVG file from disk to PNG. |
| `inspect_drawing` | Structured bbox/annotation report for 2D drawing. |
| `lint_drawing` | Structural drawing-quality checks. |
| `save_drawing_annotations` | Write `.dims.json` sidecar for label metadata. |

### Import/Export

| Tool | Description |
|------|-------------|
| `export` | Export as STEP/STL/DXF/SVG (or comma-separated like "step,stl"). Auto-detects 2D vs 3D. |
| `import_cad_file` | Load STEP/STL file as named object for comparison. |

### Comparison

| Tool | Description |
|------|-------------|
| `shape_compare` | Compare two shapes: volume, bbox, topology, surface-deviation diff, localized changed regions. |
| `align_check` | Check alignment between objects along axis (flush/center/clearance modes). |

### Session Checkpoints

| Tool | Description |
|------|-------------|
| `save_snapshot` | Save named checkpoint of current geometric state. |
| `restore_snapshot` | Restore from checkpoint. |
| `diff_snapshot` | Compare two snapshots by geometry metrics. |

### Part Library (requires `--library` flag)

| Tool | Description |
|------|-------------|
| `search_library` | Search part library by keyword. |
| `load_part` | Load named part with optional parameter overrides. |

### Utility

| Tool | Description |
|------|-------------|
| `version` | Return server version. |
| `health_check` | Verify VTK/SVG/STEP/STL dependencies work end-to-end. |
| `repair_hints` | Targeted fix suggestions for execute() errors. |
| `workflow_hints` | Guidance on using tools effectively. |
| `script` | Assemble reproducible Python script from session's executed code blocks. |
| `install_skill` | Copy b123d workflow skill (modeling/drawing/repair) into project. |
| `session_state` | Full JSON snapshot of active shapes, named objects, snapshots, variables. |
| `last_error` | Details of last failed execute(). |

---

## 4. MCP Resources (Read-only, no tool-call cost)

| URI | Contents |
|-----|----------|
| `build123d://quickref` | build123d API quick reference (primitives, booleans, positioning, selectors, fillets) |
| `build123d://selectors` | Task-indexed selector cookbook |
| `build123d://drafting` | 2D engineering drawings cookbook |
| `build123d://drafting-api` | API reference for build123d-drafting-helpers |
| `build123d://session` | Live session state as JSON |
| `build123d://bd_warehouse` | Pre-built parametric parts catalogue |

---

## 5. CAD Operations Available

### Via `execute()` (full build123d API)

ALL build123d operations are available through the `execute()` tool:

- **Primitives:** Box, Cylinder, Sphere, Cone, Wedge, Torus
- **Booleans:** Union (+), Subtract (-), Intersect (&), mode=Mode.SUBTRACT/INTERSECT
- **Extrude:** extrude() — linear extrusion of sketches/profiles
- **Revolve:** revolve() — rotational sweep
- **Loft:** loft() — blend between profiles
- **Sweep:** sweep() — sweep profile along path
- **Fillet:** fillet() — round edges
- **Chamfer:** chamfer() — bevel edges
- **Shell:** shell() — hollow out with wall thickness
- **Thread:** thread() — create screw threads (also bd_warehouse)
- **Hole:** CounterSinkHole, CounterBoreHole, Hole
- **Pattern:** GridLocations, PolarLocations
- **Movement:** Pos(), Rot(), Location(), move()
- **Joints:** RigidJoint, RevoluteJoint, LinearJoint, CylindricalJoint, BallJoint
- **Sketches:** 2D profiles (Circle, Rectangle, Polyline, etc.)
- **Selects/Selectors:** Face, Edge, Vertex selectors with filtering
- **Drafting:** ExtensionLine, DimensionLine, Centerline, CenterMark, Leader, TitleBlock, etc.
- **bd_warehouse:** Pre-built bearings, fasteners, gears, pipes, threads, sprockets

### Via MCP Tools (dedicated)

- Feature recognition (holes, bosses, countersinks, hole patterns)
- Printability analysis (FDM-specific)
- Design audit (parameter robustness)
- Shape comparison (localized surface-deviation diff)
- Alignment checking
- Cross-section analysis
- Clearance checking
- Specification verification (experimental)

---

## 6. Export Capabilities

### YES — Full STEP/STL/DXF/SVG Export

| Format | Use Case |
|--------|----------|
| **STEP** (.step/.stp) | Exact geometry for downstream CAD tools (SolidWorks, Fusion 360, etc.). Preserves named bodies/labels for assemblies. |
| **STL** (.stl) | Mesh for 3D printing, slicers, GitHub preview |
| **DXF** (.dxf) | 2D CAD geometry for fabrication |
| **SVG** (.svg) | Documentation, web preview |
| **Multiple** | `format="step,stl"` exports both in one call |

### Import Capabilities

- **STEP** (.step/.stp) — full solid import
- **STL** (.stl) — mesh import (produces shell, not solid — volume=0)

---

## 7. Installation & Running

### Quick Start

**Requirements:**
- Python 3.11, 3.12, 3.13, or 3.14
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- An MCP-compatible AI app (Claude Code, Claude Desktop, Cursor, VS Code, Continue, Cline, Codex CLI)

**No clone needed:**

```bash
# Verify it works:
uv tool run --python 3.12 build123d-mcp@latest --version

# Add to your AI app's MCP config:
# command: uv
# args: ["tool", "run", "--python", "3.12", "build123d-mcp@latest"]
```

### Claude Code (.mcp.json or ~/.claude/mcp.json):
```json
{
  "mcpServers": {
    "build123d-mcp": {
      "command": "uv",
      "args": ["tool", "run", "--python", "3.12", "build123d-mcp@latest"]
    }
  }
}
```

### Claude Desktop (%APPDATA%\Claude\claude_desktop_config.json):
```json
{
  "mcpServers": {
    "build123d-mcp": {
      "command": "uv",
      "args": ["tool", "run", "--python", "3.12", "build123d-mcp@latest"]
    }
  }
}
```

### Cursor (~/.cursor/mcp.json):
Same JSON structure as above.

### HTTP Mode (advanced):
```bash
uv tool run --python 3.12 "build123d-mcp[http]@latest" \
  --transport http --host 127.0.0.1 --port 8000
```
Connect at: `http://localhost:8000/mcp`

### GitHub Codespaces:
One-click: https://codespaces.new/pzfreo/build123d-mcp

### Developer Setup:
```bash
git clone https://github.com/pzfreo/build123d-mcp.git
cd build123d-mcp
uv sync --all-groups
uv run build123d-mcp --version
uv run pytest
```

---

## 8. Dependencies

### Core Runtime Dependencies (from pyproject.toml)

| Package | Purpose |
|---------|---------|
| `mcp>=1.9` | MCP Python SDK |
| `build123d>=0.10,<0.12` | Core CAD library (wraps OpenCascade) |
| `vtk>=9.3` | 3D rendering (VTK for shaded PNG renders) |
| `bd_warehouse` | Pre-built parametric parts (bearings, fasteners, gears, threads) |
| `resvg-py` | SVG → PNG rasterisation (Rust wheels, no native deps) |
| `build123d-drafting-helpers>=0.10.0` | 2D engineering drawing helpers |
| `defusedxml>=0.7.1` | Safe XML parsing |
| `augura>=0.1.6` | Printability analysis, wall thickness measurement |
| `scipy` | cKDTree for nearest-neighbour surface diff |

### Optional Dependencies

| Package | When |
|---------|------|
| `uvicorn` | HTTP mode (`build123d-mcp[http]`) |

### Dev Dependencies

| Package | Purpose |
|---------|---------|
| `pytest` | Testing |
| `pytest-timeout` | Test timeouts |
| `mypy` | Type checking |
| `pytest-cov` | Coverage |
| `ruff` | Linting |

### Underlying CAD Kernel

build123d wraps **Open Cascade (OCC)** via:
- `cadquery-ocp` (build123d 0.10) or `cadquery-ocp-novtk` (build123d 0.11)
- The kernel provides: B-Rep modeling, STEP/STL I/O, boolean operations, mesh tessellation, HLR projection

---

## 9. Rendering Backend

### Three rendering paths:

1. **VTK (PNG)** — `_vtk_render_subprocess_worker.py`
   - Runs in a **hard-bounded subprocess** (60s budget, can't kill session)
   - High-quality shaded 3D renders
   - Supports clip planes, azimuth/elevation camera control
   - Quality: standard or high (finer tessellation)

2. **Build123d HLR (SVG/DXF)** — `render_view(format="svg"|"dxf")`
   - Uses build123d's built-in Hidden Line Removal projection
   - Returns parseable 2D CAD geometry (polylines)
   - Auto-detects 2D inputs (sketches/drafting objects)
   - Lightweight, no VTK dependency

3. **Resvg (PNG from SVG)** — for 2D drawing review
   - Rasterises SVG via `resvg-py` (Rust-based, fast)
   - Used when `render_view(format="png")` receives a 2D sketch/drawing object
   - Also used by `render_drawing()` tool

### Live Viewer (optional)

- `--viewer-socket PATH` streams geometry over Unix domain socket
- Encodes as **glTF-binary (glb)** — self-contained, no extra deps
- Compatible with three.js, trimesh, pyvista, Blender
- Per-shape deltas only tessellated changed shapes
- Background thread, never blocks agent path
- POSIX only (AF_UNIX)

### Tessellation

- `_tessellate_subprocess.py` — out-of-process, hard-bounded
- Per-shape delta detection (only re-tessellate changed shapes)
- Configurable deflection/tolerance

---

## 10. Ollama/Local LLM Support

### build123d-mcp is LLM-agnostic

The server is a **standard MCP server** — it works with ANY MCP-compatible client. The LLM/model choice is on the client side.

### For Ollama specifically

Ollama does NOT natively speak MCP (as of April 2026). You need a **bridge layer**:

1. **MCPHost** (Go CLI):
   ```bash
   go install github.com/mark3labs/mcphost@latest
   mcphost -m ollama:qwen3 --config servers.json
   ```

2. **ollama-mcp-bridge** (TypeScript/Python):
   - TypeScript: https://github.com/patruff/ollama-mcp-bridge
   - Python: https://github.com/Fino123/ollama-mcp-bridge
   - Adds MCP tools to Ollama's `/api/chat` endpoint
   - Multi-round tool calling loop

3. **Custom client** with MCP Python SDK + Ollama Python library

### Model recommendations for tool calling

| Model | Size | Notes |
|-------|------|-------|
| Qwen 3 | 14B, 32B | Best tool calling per compute dollar |
| Llama 3.1/3.3 | various | Good tool calling |
| Mistral | various | Good tool calling |
| Gemma 4 | various | Good tool calling |

**Minimum practical size:** 14B parameters for single-tool workflows
**Recommended for multi-step:** 32B+ (Qwen 3 32B is the sweet spot)

### Key constraint

The `execute()` tool sends Python code to the server. The model needs to write **syntactically correct build123d Python code**. This is a significant capability requirement — smaller models may struggle with:
- Correct build123d API syntax
- Selector expressions
- Complex multi-step builds
- Understanding error messages and fixing code

---

## 11. Can It Handle Complex Geometry Like Instrument Bores with Tone Holes?

### Short answer: YES, with caveats

build123d-mcp inherits all of build123d's capabilities, which are built on Open Cascade. This means:

**What it CAN do:**
- Cylindrical/conical bores (Cylinder, Cone primitives)
- Tone holes via boolean subtract (Cylinder subtracted from bore)
- Chimney-style tone holes (small cylinders intersecting main bore)
- Complex profiles via loft/sweep/revolve
- Thread creation (bd_warehouse)
- Counterbore/counterbore/countersink holes
- Any B-rep geometry build123d supports

**Example instrument bore construction:**
```python
from build123d import *

# Main bore - cylindrical
bore = Cylinder(radius=8, height=300)

# Conical section
cone = Cone(bottom_radius=12, top_radius=8, height=50)
cone = cone.move(Location((0, 0, 300)))

# Tone holes
for pos in [50, 100, 150, 200, 250]:
    hole = Cylinder(radius=3, height=20)
    hole = hole.move(Location((0, 0, pos)))
    hole = hole.rotate((0,0,0), (1,0,0), 90)  # perpendicular to bore
    bore = bore - hole

# Register and export
show(bore, "instrument_bore")
```

**Feature recognition would work on:**
- `find_holes()` — would detect tone holes as cylindrical features
- `find_bosses()` — would detect any raised features
- `measure()` — volume, cross-sectional areas
- `cross_sections()` — detect internal bore profile along axis
- `clearance()` — check wall thickness between tone holes and bore

**Challenges:**
- Very complex multi-body operations may hit the execution timeout (120s default)
- Boolean operations on many intersecting cylinders can be computationally expensive
- Conical bore profiles need loft/sweep rather than simple primitives
- The AI needs to understand build123d's coordinate system and positioning

**For acoustic instrument design specifically:**
- The geometry itself is straightforward for build123d
- The hard part (acoustic optimization) is outside build123d-mcp's scope
- But the CAD modeling loop (design → verify dimensions → export → iterate) is exactly what build123d-mcp excels at
- `cross_sections()` is particularly useful for verifying bore profiles
- `measure()` with density can calculate mass/inertia for instrument balance

---

## 12. Demos and Examples

### Included Examples

The repository includes:
- `examples/live_viewer_client.py` — dependency-free live viewer client
- `examples/live_viewer_pyvista.py` — PyVista-based viewer

### First Test Prompt (from README)

```
Use build123d-mcp to make a 60 mm x 40 mm x 6 mm mounting plate with two
5 mm through holes 40 mm apart. Render it, measure it, then export STEP and STL.
```

### Workflow Skills

The server includes installable workflow skills:
```python
install_skill(target="agents-md", skill="modeling")  # 3D parts
install_skill(target="agents-md", skill="drawing")   # 2D engineering drawings
install_skill(target="agents-md", skill="repair")    # Fix broken solids
```

### Recommended Workflow (from llms.md)

1. `version` — confirm server version
2. `health_check` — verify dependencies
3. Read `build123d://quickref` — get API syntax
4. `reset` — start clean
5. `execute` — imports and initial geometry
6. `measure` — verify geometry numerically
7. `render_view` — visually verify (only AFTER measure confirms)
8. `save_snapshot` — checkpoint before complex operations
9. Repeat until satisfied
10. `export` — write STEP + STL

---

## 13. Limitations

### Execution Limits
- **Timeout:** Default 120s per execute() call (configurable)
- **No memory limit:** User code can allocate unbounded memory
- **Windows timeout:** Cannot forcibly terminate runaway threads (SIGALRM unavailable)
- **Large shapes:** Heavy operations (booleans, tessellation) can hit timeout

### Sandbox Limitations
- **No filesystem access** (os, pathlib blocked)
- **No network access** (socket, urllib blocked)
- **No shell access** (subprocess blocked)
- **Restricted builtins:** open, eval, exec removed
- **Import allowlist:** Only build123d, math, numpy, safe stdlib

### Geometry Limitations
- **B-rep only:** No mesh-based modeling (STL import is shell, not solid)
- **Coincident faces:** Don't fuse reliably — need slight interpenetration
- **Feature recognition:** Limited to holes, bosses, countersinks, hole patterns
- **Fillets/chamfers/pockets/ribs:** Not yet recognized by feature recognizers
- **Curved-surface holes:** Face centers can be off-axis — use find_holes bore axis

### Rendering Limitations
- **VTK budget:** 60s per render (hard-bounded subprocess)
- **HLR/SVG:** Lightweight but no shading
- **Live viewer:** POSIX only (AF_UNIX sockets)
- **2D drawings:** Require build123d-drafting-helpers package

### Session Limitations
- **Single session per stdio connection:** No multi-tenant support in stdio mode
- **HTTP mode:** No built-in authentication, shared session
- **Snapshots:** Don't save Python namespace — only geometry state
- **Timeout recovery:** Session may be dirty after timeout — reset recommended

### Model Limitations (for AI agent)
- **Code quality depends on model:** Small models may produce syntactically incorrect build123d code
- **Complex multi-step builds:** Require models with strong tool-calling capabilities
- **Error recovery:** Model needs to understand build123d error messages

### Experimental Tools
- `verify_spec` and `suggest_spec` are off by default (`--experimental`)
- `conforms: true` can mislead agents into premature finalization

---

## 14. Security Model

### Threat Model
- Primary threat: **prompt injection** — malicious content causing execute() with harmful payload
- Designed for **local development**, not multi-tenant/production

### Defenses
1. AST inspection (pre-execution) — blocks dangerous imports, dunder access
2. Restricted builtins — removes open, eval, exec, etc.
3. Execution timeout — prevents infinite loops
4. Path traversal rejection on export/render_view save_to

### Known Residual Risks
- build123d internals could theoretically wrap file/subprocess operations
- Memory exhaustion not blocked
- Determined attacker with build123d function access could bypass

### Higher-Security Recommendations
- Run in container with no network, read-only filesystem
- Use seccomp/AppArmor for syscall restriction
- Use RestrictedPython as additional layer
- Run each execute() in subprocess

---

## 15. Related Projects

| Project | Description |
|---------|-------------|
| [fingerskier/build123d-claude-plugin](https://github.com/fingerskier/build123d-claude-plugin) | Simpler Claude Code plugin (7 tools vs 31+) |
| [brs077/3dp-mcp-server](https://github.com/brs077/3dp-mcp-server) | 3D-printing focused MCP server (33 tools, Bambu Lab X1C target) |
| [Svetlana-DAO-LLC/cad-agent](https://github.com/clawd-maf/cad-agent) | Containerized CAD agent with VTK rendering (HTTP/MCP) |
| [patruff/ollama-mcp-bridge](https://github.com/patruff/ollama-mcp-bridge) | Bridge between Ollama and MCP servers |

---

## 16. Key Takeaways for Instrument Design

### Why build123d-mcp is relevant for instrument design:

1. **Incremental modeling** — build bore, add tone holes one at a time, verify each
2. **Dimensional verification** — `measure()` confirms bore diameter, tone hole size, wall thickness
3. **Cross-section analysis** — `cross_sections()` along bore axis shows profile
4. **Feature recognition** — `find_holes()` detects and catalogs all tone holes
5. **Clearance checking** — `clearance()` verifies wall thickness between features
6. **Export for simulation** — STEP export for acoustic simulation tools
7. **Iterative design** — snapshots allow "what if?" exploration without losing state
8. **Design audit** — verify parametric dimensions are robust to changes

### What build123d-mcp does NOT do:

- Acoustic simulation/optimization (use Chalumier, DEMAKEIN, or custom code)
- Direct CNC toolpath generation (export STEP → import in CAM software)
- 3D print slicing (export STL → import in slicer)
- Material property assignment beyond density

### Workflow suggestion for instrument bore design:

```
1. Start with bore profile (Cylinder/Cone/Loft)
2. Add tone holes one at a time via boolean subtract
3. Use measure() after each boolean to verify topology changed
4. Use cross_sections() to verify bore profile
5. Use find_holes() to catalog all tone holes
6. Use clearance() to check wall thickness
7. Use design_audit() to verify parameter robustness
8. Export STEP for acoustic simulation
9. Export STL for 3D printing prototype
```

---

*Report generated 2026-07-18 from GitHub repository, PyPI, and web search.*
*Sources: github.com/pzfreo/build123d-mcp, pypi.org/project/build123d-mcp, glama.ai/mcp/servers*

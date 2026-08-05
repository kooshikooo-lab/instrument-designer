# TOOLS.md — Tool Registry

Every third-party tool this project uses must be **declared** (pyproject.toml),
**importable** (in the live pipeline), and **tested** (whitelisted pytest file)
— otherwise it is considered un-adopted. Installing alone is NOT a step.

The registry is enforced automatically:

- `scripts/toolcheck.py` — standalone cross-check (installed / declared / imported).
- `tests/test_tool_registry.py` — pytest guard (whitelisted) that fails if any
  third-party import in backend/, scripts/, woodwind_designer/, or the
  whitelisted tests is missing from pyproject.toml.

## How to adopt a new tool

1. `pip install <pkg>` — provisional, not yet a step.
2. Add it to `[project.optional-dependencies]` under the right extra
   (or `[project.dependencies]` if core). Strip extras/version pins in the
   registry check automatically.
3. Import it in the live pipeline and use it for real.
4. Add a pytest file that exercises it, and whitelist that file in
   `pyproject.toml` → `[tool.pytest.ini_options]` → `python_files`.
5. Run `python scripts/toolcheck.py` → PHANTOM must be empty. If the import
   name differs from the pip package name (e.g. `yaml` vs `PyYAML`), add an
   entry to `PACKAGE_ALIASES` in `scripts/toolcheck.py` instead of silencing it.

## Current declarations

### Core — `[project.dependencies]`
| pip package | import root | where used |
|---|---|---|
| PySide6 | PySide6 | woodwind_designer GUI (main.py, gui/*) |
| numpy | numpy | everywhere |
| scipy | scipy | backend, tests |
| matplotlib | matplotlib | reports, plots |
| demakein | demakein | bore geometry |
| openwind | openwind | wave equation solver |
| pyyaml | yaml | config loading |
| pydantic | pydantic | schemas |
| pymoo | pymoo | multi-objective optimization |
| fastapi | fastapi | design_server.py |
| uvicorn[standard] | uvicorn | main.py ASGI server |
| requests | requests | API client |
| fpdf2 | fpdf | scripts/convert_report_to_pdf.py |

### Extra: `jax`
| pip package | import root |
|---|---|
| jax | jax |
| jaxlib | jaxlib |

### Extra: `surrogate`
| pip package | import root | where used |
|---|---|---|
| jax / jaxlib | jax / jaxlib | jax TMM |
| flax | flax | surrogate model |
| optax | optax | optimizer |
| botorch | botorch | bi_objective_bo.py |
| torch | torch | surrogate backend |
| gpytorch | gpytorch | bi_objective_bo.py |

### Extra: `cad`
| pip package | import root | where used |
|---|---|---|
| cadquery | cadquery | test_cadquery_instrument.py, STL export |
| build123d | build123d | design_server.py STEP export |
| vtk | vtk | stl_verifier.py (guarded import) |
| trimesh | trimesh | stl_export.py |

### Extra: `bench`
| pip package | import root | where used |
|---|---|---|
| dask[distributed] | dask / distributed | benchmark_dask.py, generate_surrogate_data.py |
| psutil | psutil | run_all_tests.py (guarded import) |
| cma | cma | backend/experiments/ |

### Extra: `perf`
| pip package | import root | where used |
|---|---|---|
| numba | numba | backend/tmm_numba.py (guarded, TMM resonance fast path) |

### Extra: `freecad`
| pip package | import root | where used |
|---|---|---|
| freecad | FreeCAD / Part / Mesh / Import | freecad_widget.py, freecad_backend.py |

### Extra: `dev`
| pip package | import root |
|---|---|
| pytest | pytest |
| ruff | (lint, not imported) |

## External applications (not pip packages)

These are installed outside Python and are never imported by the pipeline;
they are declared here so the registry documents every external tool.

| App | Executable | Used by |
|---|---|---|
| Blender | `blender.exe` (auto-detected: `BLENDER_EXE` env, PATH, or `C:\Program Files\Blender Foundation\Blender*\`) | `scripts/view_instrument.py`, `blender_addon/` |
| LM Studio | `lms.exe` (auto-detected: `LMSTUDIO_BIN` env, or `~\.lmstudio\bin\lms.exe`) | `backend/local_llm.py` (local Gemma 4: `google/gemma-4-12b`) |
| Ollama | `ollama.exe` (on PATH) | `backend/ai_advisor.py` (LLM fallback tier) |
| Autodesk Fusion | `FusionLauncher.exe` (webdeploy) | prototyping only (not integrated) |

The local LLM stack prefers LM Studio (Gemma 4, server default
`http://localhost:1234`), then Ollama (`http://localhost:11434`), then
OpenRouter free models. `backend/local_llm.py` auto-starts the LM Studio
server headless; `launchers\start_gemma.bat` is the one-click entry point.

## Known-not-installed (fine)

`freecad` (optional GUI/CAD extra — not installed on headless), `ruff` (dev
lint). These are ORPHAN (declared, not installed) but not errors.

## Notes

- FORGOTTEN packages (installed, imported nowhere) are informational — they are
  transitive deps or candidates for archiving, never auto-removed here.
- The pytest guard uses `scripts/toolcheck.py`'s scanner directly so the
  standalone check and the CI check can never drift.

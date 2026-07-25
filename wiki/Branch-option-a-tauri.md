# Branch: option-a-tauri

> Tauri desktop app architecture. Desktop decides what to do with this.

## Purpose

Tauri + HTTP backend desktop app. Tauri spawns the Python FastAPI server as a managed process. Frontend talks to it via localhost:8000.

## What It Has

| Feature | Status |
|---------|--------|
| Tauri build setup | ✅ |
| Optimization UI with presets | ✅ |
| Cache stats endpoint + UI | ✅ |
| WikiTab | ✅ |
| AI assistant (OpenRouter) | ✅ |
| Coding agent (Cohere North) | ✅ |
| Research prompt generator | ✅ |

## What It Doesn't Have

| Feature | Branch |
|---------|--------|
| KeefeLoss | laptop |
| Two-phase optimizer | laptop |
| 91 instruments | laptop |
| Absolute RMS metric | ⚠️ Uses median correction |
| Chalumier integration | origin/experiment-chalumier-integration |

## Conflicts with Laptop

- `optimizer_global.py` uses median correction (laptop uses absolute RMS)
- `phase_cost_with_offset` uses median correction (laptop uses absolute RMS)
- Speed of sound values may differ

## Recommendation

Desktop should:
1. Pull `main` after laptop merges
2. Fix median correction in `optimizer_global.py` and `phase_cost_with_offset`
3. Update to absolute RMS as primary metric
4. Keep AI assistant and optimization UI (unique to this branch)

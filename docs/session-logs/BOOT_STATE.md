# BOOT STATE — Current Session Snapshot (reload at session start)

> This file is the reloadable boot context. At the start of every session, read
> this file and sync the team channel (`python scripts/team_chat.py sync`).
> Update this file at the END of every session so the next session can boot from it.
> This is what survives context drops — keep it current, not historical.

---

## Goal

- Converge both machines on `main`: settle laptop's reconciliation decisions (speed-of-sound 346100, 5-stage `sequential_refined`), then run research/spectral API work (librosa, OpenWInD, free compute, Gemini multimodal) and scope a `backend/spectral` validation module.
- Overnight autonomous run (Dask benchmark, unconventional shapes, WAV inverse design, analytical cross-check) **completed**. Next: Phase 2G surrogate training (Kaggle) on the laptop, spectral module design, Gemini integration.
- Tools must be **integrated into a pipeline**, never just installed and forgotten (recurring problem — see "Tool adoption rule" below). The tool registry guard is now built and live.

## Constraints & Preferences

- **Direct-to-main only**, no PRs/side branches (explicit user correction after `fix/speed-of-sound-346100` detour).
- Coordination via `scripts/team_chat.py` on Discussion #23 (Step 0 protocol per AGENTS.md); never relay through the human.
- User wants **phone-call immediacy**: messages read/responded to immediately — human "totally superior" at noticing notifications; "too much adhd to notice notifications" is why we built a watcher.
- `AUDIT:` for provisional commits; `GOVERNANCE-UPDATE` for commits touching `docs/CONSTRAINTS_AND_PREFERENCES.md`.
- Don't commit regenerable artifacts (`.lnk`, `*.json5`, `*_benchmark_results.json`, `validation_results/*.json`, `test_output/unconventional/*.json`, `.gitmodules`).
- Branch cleanup desired: leftover branches "could lead to issues, confused agents before, especially if I switch models."
- **Tool adoption rule**: installing a tool is NOT a step — integration is. A tool only leaves the registry as "adopted" when it has a real call site in a pipeline stage or a test. Anything abandoned goes to `docs/ARCHIVED_TOOLS.md` and gets uninstalled.

## Progress

### Done
- **Speed-of-sound fix on main**: committed `3ce892e` (`backend/physics/losses.py:96` → 346100.0; test constants lines 110/155/164); worktree `..\instrument-designer-port` on `main`.
- **Decisions posted** (#23 comment 17867637): (1) 346100 everywhere; (2) decommission standalone 5-stage `sequential_refined` (`jax_optimizer.refine_sequential` canonical).
- **Follow-up posted** (#23 comment 17867660): fix-on-main notice; `_followup_msg.md` removed.
- **Branch cleanup**: deleted locally `port/benchmarking-clean`, `experiment/cadquery-stl`, `fix/team-chat-communication`; deleted on origin `experiment/cadquery-stl`, `fix/team-chat-communication`, `port/main-2026-08-01-v2`, `refactor/clean-architecture`. `git fetch --prune` removed 7 stale tracking refs. Kept (NOT merged): `benchmarking-experiments`, `kalles-main-branch`, `experiment/unconventional-shapes`, `experiment/ai-tier1-review`, `feature/dask-jvm-chalumier-compliance`, `port/main-2026-08-01`.
- **Watcher built**: `scripts/team_watch.ps1` (background, polls 3s via `team_chat.py sync --json`, toast + exclamation sound on other-machine messages, writes `scripts/.team_inbox.md`, logs `scripts/.team_watch.log`); `team_chat.py watch` hardened with `--timeout`/`_print_new`/`is_other_machine`.
- **Laptop status check posted** (#23 comment 17867701): explicit "fully unblocked — confirm and proceed" nudge.
- **Laptop reply** (#23, 04:53Z): both decisions received/applied on `kalles-main-branch`; pushed `211f98b..3175b01` (includes kalles/main merge `0732868`, pyproject dedupe `dccb604`, speed-of-sound merge `3175b01`); full suite **84 passed**; resumes **Phase 2F laptop-only ~2K sample generation** via `scripts/generate_surrogate_data.py`.
- **Laptop Phase 2F start** (04:55Z): plan = adapt `scripts/generate_surrogate_data.py`, restrict to laptop workers, reduce batch size, persist samples to disk, then Phase 2G surrogate training.
- **Acknowledgment posted** (#23 comment 17867731): push verified (14 ahead / 0 behind), Phase 2F approved.
- **Desktop `main` verified green**: `pytest tests/ -q` → **26 passed** in 25.69s (sympy Keefe-loss suite green).
- **API/spectral search completed**: librosa (CQT/pyin; 0.11.0 installed), scipy.signal (Welch/find_peaks), sounddevice (0.5.5 installed), spectrum, OpenWInD (bore reconstruction), calcimpy, GNN surrogate paper (arXiv:2412.16817), torchlibrosa.
- **Free compute + multimodal search completed**: Colab ~15-30 GPU-hr/wk, Kaggle ~30 GPU-hr/wk (best free fit for Phase 2G), HF ZeroGPU small, Lightning 80/hr-mo, GCP $300 credits, SageMaker Lab closing to new users Jul 30 2026; Gemini free tier strongest multimodal (audio/images/video/PDF, Flash ~10 RPM/250 RPD), Groq, OpenRouter multimodals, Qwen2.5-VL/LLaVA/InternVL open-weight. Repo already uses OpenRouter (`prompt_builder.py`/`ai_assistant.py`/`stl_verifier.py`) + Ollama; **Gemini NOT integrated** (only in chat-log).
- **Compute research posted** (#23 comment 17867767): free-compute + Gemini multimodal findings.
- **Boot-sequence fix committed**: `f5ae5ed` (BOOT_STATE.md + AGENTS.md pointer) and `ca67ce7` (watcher commit — previously uncommitted, at risk of loss).
- **Mid-session context-loss protocol** (`3125d5b`, GOVERNANCE-UPDATE): AGENTS.md now says stop-and-re-read after compaction; boot FINAL CHECK requires BOOT_STATE.md update before session ends.
- **Overnight run (user asleep) — all complete**:
  - Dask cluster verified live (8 workers, `tcp://100.100.66.117:8786`); `benchmark_dask.py` defaulted to stale `100.69.113.41:8786` (0 workers) — patched via `scripts/_run_benchmark_live.py`.
  - **Main Dask benchmark: 12/12 pass <3c RMS, 4.09× speedup** (298.8s → 73.0s, 8 workers).
  - **Unconventional shapes: ALL PASSED** (10/10 bore types → STL; optimizations: exponential 0.0c, spiral 0.04c, parabolic 1.2c, stepped 1.9c, ridged 5.4c, bessel 7.0c, cylindrical 15.8c).
  - **WAV inverse design**: `backend/inverse_design.py` extracted from kalles-main-branch; **fixed `1.0/round_trip` amplification bug** (used `round_trip` directly); Tier 1 f0 recovery +3.9c/−4.5c, Tier 3 cost 0.064; Tier 2 blocked (generative_agent not on main).
  - **botorch installed + declared** (was phantom — imported by `bi_objective_bo.py`, never in pyproject). gpytorch dep added.
  - **Analytical cross-check**: constant 0.66r end correction, worst error 0.04c / 72 cases; new test `tests/test_analytical_pipes.py` (73 tests).
  - **Tool registry built**: `scripts/toolcheck.py` + `tests/test_tool_registry.py` guard + `docs/TOOLS.md`; new extras `cad` (cadquery/build123d/vtk/trimesh) and `bench` (dask[distributed]/psutil/cma); **PHANTOM deps now empty**.
  - **Desktop suite: 26 → 113 passed** (added inverse_design 9, surrogate 4, analytical pipes 73, tool registry 1). OpenWind standalone cross-check: 3 passed.
  - Commits pushed: `b3e41a2` (WAV + tests) → `a9aa7c6` (analytical pipes) → `ea6fe6a` (tool registry). Full results posted to #23 (comment 17867933).
  - **Phase 2G decisions posted** (#23 comment 17867858): target contract APPROVED; direction = **Kaggle** (`train_surrogate.py --epochs 200 --batch 256`, upload samples_2000_seed42.csv).

### In Progress
- **Phase 2G/2H (laptop)**: surrogate trained on mixed 10K (best val 0.685; tail-weighted 0.660). Phase 2H CLOSED — standalone surrogate-BO not viable (0/20 top-20 elite overlap, unconstrained search → invalid geometry); **hybrid warm-start validated** (surrogate ranks → `refine_sequential` finishes: 8/10 reach 0¢ vs 5/10 random). Awaiting desktop direction on Kaggle GPU run vs warm-start-only.
- **TMM medium branch testing (laptop)**: `perf/tmm-medium-refactor-copilot` cross-check posted to #23 (comment 17874801). Confirmed: pure-Python medium ~+19% slower than main (matches desktop); numba `import math`-in-njit crash on py3.14/numba 0.66 CONFIRMED + FIXED (np.floor/arctan/tan replace math.*; numba now bit-identical to Python, 480 cases max diff 0.0e+00); **corrected finding: wiring numba into `find_resonance` = ~5.5-6.3x speedup** (my earlier 0.94x was a perf_counter instrumentation artifact). Medium suite **114 passed**. Fix committed locally to holding branch `fix/tmm-medium-numba` (a37a621, NOT pushed — awaiting desktop OK to push to perf branch / wire numba into `tmm_acoustics.py`).
- **Spectral research post**: the draft `scripts/_research_msg.md` (librosa/OpenWInD/scipy/GNN) is gone (never committed). The spectral API findings live in BOOT_STATE Done + #23 comment 17867767; fold into the next spectral update instead of re-staging.

### Blocked
- `backend/spectral` implementation **awaits user approval of design** (scoped but not presented).
- Inverse-design Tier 2 (`design_from_sound` full pipeline): `generative_agent`, `instrument_knowledge`, `spline_bore` not on `main` (ADR: PLANNED).

## Key Decisions

- Speed-of-sound **346100 mm/s canonical** everywhere; 5-stage `sequential_refined` **decommissioned** — `jax_optimizer.refine_sequential` authoritative; standalone copy survives only on `kalles-main-branch` as A/B reference.
- Branch cleanup: delete only branches fully merged into `origin/main`; leave unmerged (potential work loss).
- Messaging model: OS-level toast watcher handles notification (human is better at noticing) + bounded foreground `watch` prints into chat when I listen; background daemon never decides/responds unattended.
- Spectral module: synthetic-only tests for now, no mic/recording integration; reuse `metrics.py`/`target_frequencies.py` (import, never modify — single source of truth).
- Restart session after powershell command in compacted laptop message (nudged; laptop ack'd coordination is on-channel).
- **Tool registry solution** (BUILT — commit `ea6fe6a`, guard live): `docs/TOOLS.md` manifest + `scripts/toolcheck.py` (installed vs declared vs imported across live pipeline) + `tests/test_tool_registry.py` pytest guard that fails on undeclared third-party imports. Adoption rule now enforced: install + declare + import + whitelisted test. New pyproject extras: `cad`, `bench`, `surrogate` (+gpytorch). PHANTOM = empty.
- **Boot-state persistence** (user: "boot sequence is gone. Again." — fixed): `docs/session-logs/BOOT_STATE.md` is the versioned, reloadable session snapshot; AGENTS.md Step 0 points at it. Update at end of every session.

## Next Steps

1. Monitor #23 for desktop's response on Phase 2H close-out: Kaggle GPU surrogate run vs treat surrogate as warm-start-only. Verify laptop push `b067afc` credibility.
2. TMM medium: on desktop OK, push `fix/tmm-medium-numba` (a37a621) to `perf/tmm-medium-refactor-copilot` and/or wire `numba_resonance_phase` into `tmm_acoustics.py` behind a fallback flag.
3. Present `backend/spectral` design for user approval (metrics.py/target_frequencies.py reuse, synthetic-only tests). Include the spectral API research (librosa → OpenWInD → GNN surrogate) that was summarized in Done / #23 comment 17867767.
4. Wire Gemini free Flash into `ai_assistant.py` as second provider (multimodal audio/image for spectral + STL verification).
5. Update `docs/ARCHIVED_TOOLS.md` for genuinely forgotten packages (FORGOTTEN list in toolcheck) — informational only, no auto-uninstall.
6. Keep tool registry current: re-run `python scripts/toolcheck.py` after any dependency change.

## Critical Context

- **Sync**: `origin/main` = `ea6fe6a`; laptop `kalles-main-branch` ahead with Phase 2G `train_surrogate.py` (commit `e261691`) — laptop "nothing on main", working on kalles only.
- **`origin/main` log**: `3ce892e` → `cc202b5` → `dd0ab01` → `2a4b263` → `60b5d25` → `3125d5b` (governance mid-session) → `b3e41a2` (WAV pipeline + tests) → `a9aa7c6` (analytical pipes) → `ea6fe6a` (tool registry).
- **Laptop `kalles-main-branch` HEAD**: `b067afc` (tail-weight feature), ahead of `origin/main` with: speed-of-sound merge `3175b01`, Phase 2F AUDIT generation `5409846`, inverse-design merge `c2eb6aa`, tool-registry merge `9460e77`, mixed sampling `d5550db`, botorch-API fixes `77dd2d6`. Laptop test suite = **172 passed**. No laptop work on `main`; all on `kalles-main-branch`.
- **TMM perf branches**: `perf/tmm-medium-refactor-copilot` (a6c5ace, laptop-tested, numba fix in local branch `fix/tmm-medium-numba` a37a621 NOT pushed), `perf/tmm-refactor-copilot` (3ba475b, desktop benchmarking). `origin/main` = `ae38527`.
- Desktop worktree `..\instrument-designer-port` on `main`; original repo `C:\Users\Admin\Desktop\instrument-designer` on `benchmarking-experiments` (untouched).
- Dask live cluster = `tcp://100.100.66.117:8786` (8 workers); `benchmark_dask.py` default scheduler `100.69.113.41:8786` is stale/empty — use `_run_benchmark_live.py`.
- Background watcher running (toast+sound, `scripts/.team_watch.log`); `git fetch` stderr lines print as "RemoteException" on Windows but are non-fatal.
- Desktop test suite = **113 passed**; laptop = **172 passed**.
- Python 3.14; pip warns of invalid distributions (`~emakein`, `~nstrument-designer`, `~yside6-addons`) — harmless.
- ADR-010 (folded geometry) appended to `docs/ARCHITECTURE_DECISIONS.md`; ADR numbering 001–009 pre-existing.
- Laptop uses identity `big-pickle`; laptop branch-local calls still import 5-stage `sequential_refined` (`generative_agent.py`, `benchmark_unconventional_shapes.py:98`).
- Regenerable artifacts deliberately uncommitted: `test_output/inverse_design/`, `test_output/unconventional/`, `backend/benchmark_results.json`, all benchmark logs.

## Relevant Files

- `scripts/team_watch.ps1` — background toast watcher (3s, no-toast/no-sound/log/inbox hooks); log `scripts/.team_watch.log`.
- `scripts/team_chat.py` — sync/post/`--file`/`watch --timeout`/`sync --json`; state `scripts/.team_state.json`.
- `scripts/.team_inbox.md` — inbox for landed messages.
- `scripts/toolcheck.py` — tool registry checker (installed/declared/imported; use `importlib.metadata`).
- `tests/test_tool_registry.py` — whitelisted guard; fails on undeclared third-party imports.
- `docs/TOOLS.md` — tool registry manifest + adoption steps + current declarations.
- `docs/ARCHIVED_TOOLS.md` — target for genuinely forgotten packages (informational).
- `scripts/_overnight_results.md` — posted to #23 (comment 17867933), file can be removed.
- `backend/inverse_design.py` — WAV→instrument pipeline (Tier 1 + Tier 3 work; Tier 2 blocked). `backend/benchmark_inverse_design.py` — WAV benchmark.
- `tests/test_analytical_pipes.py` — TMM vs closed-form pipes (73 cases, 0.66r end correction).
- `scripts/_run_benchmark_live.py` — patches `benchmark_dask.py` to the live scheduler address.
- `backend/physics/losses.py:96` — `f = 346100.0 / lam_m` (was 343200).
- `tests/test_sympy_validation.py` lines 110/155/164 — `C_BOUNDARY_MM_S = 346100.0`; 18 tests pass.
- `tests/unit/test_basic.py` — unit test conventions (SPEED_OF_SOUND == 346100.0; fixture registry).
- `backend/prompt_builder.py` + `ai_assistant.py` + `ai_advisor.py` — OpenRouter/Ollama LLM layer (Gemini wiring target).
- `backend/stl_verifier.py` — OpenRouter vision call for STL verification (multimodal extension point).
- `backend/metrics.py`, `backend/target_frequencies.py` — canonical metrics/targets the spectral module will reuse.
- `scripts/generate_surrogate_data.py` — laptop's Phase 2F ~2K sample generation entry point (consume results for Phase 2G).

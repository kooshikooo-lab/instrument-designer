# BOOT STATE — Current Session Snapshot (reload at session start)

> This file is the reloadable boot context. At the start of every session, read
> this file and sync the team channel (`python scripts/team_chat.py sync`).
> Update this file at the END of every session so the next session can boot from it.
> This is what survives context drops — keep it current, not historical.

---

## Goal

- Converge both machines on `main`: settle laptop's reconciliation decisions (speed-of-sound 346100, 5-stage `sequential_refined`), then run research/spectral API work (librosa, OpenWInD, free compute, Gemini multimodal) and scope a `backend/spectral` validation module.
- Tools must be **integrated into a pipeline**, never just installed and forgotten (recurring problem — see "Tool adoption rule" below).

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

### In Progress
- `scripts/_research_msg.md` staged for #23, **not yet posted** (spectral APIs: librosa → OpenWInD → GNN surrogate; recommended order).

### Blocked
- `backend/spectral` implementation **awaits user approval of design** (scoped but not presented).

## Key Decisions

- Speed-of-sound **346100 mm/s canonical** everywhere; 5-stage `sequential_refined` **decommissioned** — `jax_optimizer.refine_sequential` authoritative; standalone copy survives only on `kalles-main-branch` as A/B reference.
- Branch cleanup: delete only branches fully merged into `origin/main`; leave unmerged (potential work loss).
- Messaging model: OS-level toast watcher handles notification (human is better at noticing) + bounded foreground `watch` prints into chat when I listen; background daemon never decides/responds unattended.
- Spectral module: synthetic-only tests for now, no mic/recording integration; reuse `metrics.py`/`target_frequencies.py` (import, never modify — single source of truth).
- Restart session after powershell command in compacted laptop message (nudged; laptop ack'd coordination is on-channel).
- **Tool registry solution** (proposed, user wants tools "integrated in a pipeline of some sort" — awaiting explicit build approval): `docs/TOOLS.md` manifest + `scripts/toolcheck.py` (installed vs declared vs imported vs call-site) + `tests/test_tool_registry.py` guard that fails on forgotten/phantom deps. First action: reconcile pyproject to reality (torch, torchaudio, torchvision, dask, distributed, librosa, sounddevice are phantom).
- **Boot-state persistence** (user: "boot sequence is gone. Again." — fixed): `docs/session-logs/BOOT_STATE.md` is the versioned, reloadable session snapshot; AGENTS.md Step 0 points at it. Update at end of every session.

## Next Steps

1. Post `scripts/_research_msg.md` to #23; remove the file.
2. Implement the tool registry: `docs/TOOLS.md` + `scripts/toolcheck.py` + pytest guard, with a governance commit (see "Key Decisions").
3. Team sync + check `scripts/.team_inbox.md` for Phase 2F results / laptop ack.
4. Verify push credibility + monitor Phase 2F; hand off to Phase 2G (Kaggle free GPU candidate).
5. Wire Gemini free Flash into `ai_assistant.py` as second provider (multimodal audio/image for spectral + STL verification; first deploy once Gemini integration lands).
6. Implement `backend/spectral` per design once approved.

## Critical Context

- **Sync**: `kalles-main-branch` = `3175b01` = clean superset of `origin/main` (`3ce892e`): **14 ahead / 0 behind**, no divergence; laptop local `0732868` now pushed.
- **`origin/main` log**: `3ce892e` (speed-of-sound) → `cc202b5` (laptop merge `kalles-main-branch` in) → `dd0ab01` (Phase 2 surrogate stack) → `2a4b263` (port) → `60b5d25` (rename).
- Desktop worktree `..\instrument-designer-port` on `main`; original repo `C:\Users\Admin\Desktop\instrument-designer` on `benchmarking-experiments` (untouched).
- `origin/HEAD -> origin/experiment/unconventional-shapes` (harmless remote HEAD pointer; branch kept as unmerged).
- Background watcher PID 24148 running (toast+sound; log shows 06:41/06:42 starts); `git fetch origin` post-push on Windows prints stderr lines as "RemoteException" but is non-fatal.
- Desktop test suite = 26 passed (unit 8 + sympy 18 equivalent subset); laptop = 84 passed.
- ADR-010 (folded geometry) appended to `docs/ARCHITECTURE_DECISIONS.md`; ADR numbering 001–009 pre-existing.
- Laptop uses identity `big-pickle`; remote push `211f98b..3175b01` confirmed. Laptop branch-local calls still import 5-stage `sequential_refined` (`generative_agent.py`, `benchmark_unconventional_shapes.py:98`).

## Relevant Files

- `scripts/team_watch.ps1` — background toast watcher (3s, no-toast/no-sound/log/inbox hooks); log `scripts/.team_watch.log`.
- `scripts/team_chat.py` — sync/post/`--file`/`watch --timeout`/`sync --json`; state `scripts/.team_state.json`.
- `scripts/.team_inbox.md` — inbox for landed messages.
- `scripts/_research_msg.md` — staged spectral research post (librosa/OpenWInD/scipy/GNN).
- `backend/physics/losses.py:96` — `f = 346100.0 / lam_m` (was 343200).
- `tests/test_sympy_validation.py` lines 110/155/164 — `C_BOUNDARY_MM_S = 346100.0`; 18 tests pass.
- `tests/unit/test_basic.py` — unit test conventions (SPEED_OF_SOUND == 346100.0; fixture registry).
- `backend/prompt_builder.py` + `ai_assistant.py` + `ai_advisor.py` — OpenRouter/Ollama LLM layer (Gemini wiring target).
- `backend/stl_verifier.py` — OpenRouter vision call for STL verification (multimodal extension point).
- `backend/metrics.py`, `backend/target_frequencies.py` — canonical metrics/targets the spectral module will reuse.
- `scripts/generate_surrogate_data.py` — laptop's Phase 2F ~2K sample generation entry point (consume results for Phase 2G).

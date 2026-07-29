# Session Log — 2026-07-28 (Full Day)

## Morning Session
- Posted Discussion #23: Phase 1 complete summary (recorder breakthrough, manufacturing tolerance findings, robust optimization)
- GitHub monitor running (PID 696)
- Fixed Dask: restarted scheduler + workers with 4GB memory limit
- Wired `--w-int` through entire benchmark pipeline
- Full distributed benchmark: 11 instruments, mean 0.17c RMS, max 0.82c (w_int=0.9)
- Posted results to Discussion #23

## Afternoon Session
- **Chalumier integration**:
  - Committed Bb Clarinet Designer (Boehm 17-hole, dual register) to chalumier fork
  - PR to upstream: https://github.com/MarkChuCarroll/chalumier/pull/1
  - Updated submodule pointer to 2bdff4d
  - Added multi-register support to `eval_all()` — per-note `fingerings` + `n_reg` list
- **Bore monotonicity constraint (Phase 1d)**:
  - Added `_bore_monotonicity_penalty()` in pareto_optimizer.py
  - Wired `w_mono` (default 0.3) through eval_all → safe_eval → refine_sequential → refine_robust
- **Power settings**: sleep=never, display=120min AC/30min DC, screensaver=off
- **ROADMAP updated**: multi-register optimization marked done
- Posted Discussion #23 updates

## Commits
1. `a7d11e1` feat: bore monotonicity constraint (Phase 1d)
2. `c23bf0c` feat: multi-register support in eval_all (Phase 1g)
3. `bcbb5d7` docs: mark multi-register optimization done in ROADMAP
4. `060907c` chore: update chalumier submodule to Bb clarinet designer (2bdff4d)

## Next Steps
1. Test clarinet optimization with chalumier parameters + multi-register eval
2. Phase 2: 3D print accuracy — shrinkage compensation, measurement loop
3. Consider Phase 1b (timbre with actual a₂/a₁ ratios) or Phase 1d (hard monotonicity constraint)

---

## Notes for Desktop (Kalle)
- Chalumier PR #1 submitted to upstream. Our fork is at `kooshikooo-lab/chalumier:main` with the clarinet designer.
- Submodule in instrument-designer now points to commit `2bdff4d` (the clarinet commit).
- Multi-register optimization is ready — `eval_all()` accepts `fingerings` list + `n_reg` list per note.
- Clarinet needs both chalumeau (n_reg=1, odd harmonics) and clarion (n_reg=2, all harmonics) registers.
- Bore monotonicity constraint uses soft penalty (w_mono=0.3 default) — doesn't trap optimizer.
- Dask workers on laptop (this machine) running with 4GB memory limit. Desktop should reconnect automatically.
- GitHub monitor polls Discussion #23 every 60s.
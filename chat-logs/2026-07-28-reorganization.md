# Session Log: 2026-07-28

## Repository Reorganization

**Branch:** `reorganize/restructure-repo` → PR #22

### What We Did
Massive cleanup of root and backend directories. Moved scattered test files, benchmarks, debug scripts, docs, and misc files to their proper locations.

### Results
| Location | Before | After |
|----------|--------|-------|
| Root directory | 145 entries | 27 entries |
| Backend root | 46 entries | 31 entries |

### Key Moves
- 49 duplicate files deleted from backend/ root (kept in backend/scratch/)
- 27 root-level test_*.py → tests/
- 6 benchmark files → scripts/
- Debug/diagnose files → backend/scratch/
- JSON exports → designs/
- 20+ markdown docs → docs/, research/, wiki/
- Chat logs consolidated to chat-logs/
- Scripts (.ps1/.cmd/.bat) → scripts/
- Test output dirs → tests/
- .zip/.spec → dist/build/
- trumpet files → backend/instruments/
- bore_optimizer_lbfgs → backend/archived_optimizers/
- flute_calculator → backend/instruments/
- tone_hole_corrections → backend/physics/

### What's Still Needed
- Update imports in moved test files (ad-hoc sys.path hacks)
- Fix benchmark imports (reference archived tmm_optimizer modules)
- GitHub Actions CI setup
- README.md update

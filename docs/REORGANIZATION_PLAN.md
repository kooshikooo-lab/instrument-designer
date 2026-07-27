# Reorganization Plan: Woodwind Design Automation

## Problem Statement

Current state: 144 entries in root directory, test files scattered everywhere, stale branches accumulating, no clear separation between experiments and production code, duplicate files across directories.

## Research Findings Summary

### 1. Monorepo is Correct for This Project
- Single developer, tightly coupled physics/solver/optimizer code
- Shared types (acoustic network, bore profiles, fingerings) across all components
- Small team (<5 engineers) = monorepo wins over polyrepo
- Hybrid not needed — this is one cohesive system

### 2. Branch-per-Experiment Pattern
- Each hypothesis/approach gets its own `experiment/*` branch
- Branches are disposable — delete losers guilt-free
- `main` = verified production only
- Git worktrees = parallel experiments without file conflicts

### 3. GitHub Actions for CI
- Automated testing on every push to `main`
- Parallel test sharding for fast feedback
- Experiment branches get manual trigger CI

---

## Proposed Directory Structure

```
woodwind-designer/
├── src/                          # Production source code
│   ├── core/                     # Acoustic network, coordinates, types
│   │   ├── network.py
│   │   ├── coordinates.py
│   │   └── types.py
│   ├── physics/                  # Loss models, junctions, radiation
│   │   ├── losses.py
│   │   ├── junction.py
│   │   ├── propagation.py
│   │   ├── radiation.py
│   │   └── tonehole.py
│   ├── solvers/                  # TMM, OpenWInD, external
│   │   ├── tmm_solver.py
│   │   ├── openwind_solver.py
│   │   └── external_solvers.py
│   ├── optimizer/                # Optimization engines
│   │   ├── bore_optimizer.py
│   │   ├── sequential.py
│   │   ├── two_phase.py
│   │   └── jax_optimizer.py
│   ├── instruments/              # Instrument definitions
│   │   ├── clarinet.py
│   │   ├── saxophone.py
│   │   └── flute.py
│   └── export/                   # STL, SVG, CAD export
│       ├── stl_exporter.py
│       └── svg_export.py
├── server/                       # FastAPI backend
│   ├── design_server.py
│   └── api/
├── web/                          # Frontend (Tauri + React)
│   ├── src/
│   └── src-tauri/
├── tests/                        # All tests, organized by module
│   ├── test_core.py
│   ├── test_physics.py
│   ├── test_solvers.py
│   ├── test_optimizer.py
│   └── integration/
├── experiments/                  # Experiment results (data only)
│   ├── ai-tier1/
│   ├── chalumier-comparison/
│   └── benchmarks/
├── docs/                         # Documentation
│   ├── wiki/
│   ├── session-logs/
│   └── research/
├── config/                       # Instrument configurations
├── chalumier/                    # Submodule (reference implementation)
├── scripts/                      # Utility scripts
│   ├── benchmark_all.py
│   ├── create_worktree.sh
│   └── sync_worktree.sh
├── .github/                      # GitHub Actions workflows
│   └── workflows/
├── AGENTS.md                     # AI agent instructions
├── pyproject.toml
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Branching Strategy

### Branch Types
```
main                        # Verified production code only
├── experiment/*            # Active experiments (disposable)
│   ├── experiment/jax-optimizer
│   ├── experiment/chalumier-integration
│   └── experiment/timbre-optimization
├── fix/*                   # Bug fixes (merge to main)
│   └── fix/issue-20-bugs
└── feature/*               # New features (merge to main)
    └── feature/instrument-agnostic
```

### Rules
1. **`main` is always deployable** — only merge verified code
2. **One branch per experiment** — name describes the hypothesis
3. **Delete losers promptly** — weekly cleanup of stale experiment branches
4. **Rebase, don't merge** — keeps experiment history linear
5. **Commit at session boundaries** — every 20 min during AI work

### Worktree Workflow (for parallel experiments)
```bash
# Create worktree for experiment
git worktree add ../woodwind-experiment-jax experiment/jax-optimizer

# Work in isolation
cd ../woodwind-experiment-jax
# ... make changes, commit ...

# Sync with main (rebase)
git fetch origin
git rebase origin/main

# When done: merge winner or delete loser
git checkout main
git merge experiment/jax-optimizer    # winner
# OR
git branch -D experiment/jax-optimizer  # loser
```

---

## GitHub Actions Workflows

### 1. CI Pipeline (on push to main)
```yaml
# .github/workflows/ci.yml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        shard: [1, 2, 3, 4]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ --shard=${{ matrix.shard }}/4
```

### 2. Experiment CI (manual trigger)
```yaml
# .github/workflows/experiment.yml
name: Experiment
on:
  workflow_dispatch:
    inputs:
      branch:
        description: 'Experiment branch'
        required: true

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.inputs.branch }}
      - run: pip install -r requirements.txt
      - run: python scripts/benchmark_all.py --experiment
```

---

## Migration Steps

### Phase 1: Directory Reorganization (1-2 hours)
1. Create `src/` directory structure
2. Move production code from `backend/` to `src/`
3. Move all `test_*.py` files to `tests/`
4. Move `benchmark_*.py` to `scripts/`
5. Move session logs to `docs/session-logs/`
6. Move research docs to `docs/research/`
7. Clean up root directory (remove stale files)
8. Update imports in all files
9. Update `pyproject.toml` paths

### Phase 2: Branch Cleanup (30 min)
1. Delete all stale local branches (already done)
2. Delete stale remote branches via GitHub
3. Create `.github/workflows/ci.yml`
4. Set up branch protection rules on `main`

### Phase 3: Worktree Infrastructure (30 min)
1. Create `scripts/create_worktree.sh`
2. Create `scripts/sync_worktree.sh`
3. Add `.worktreeinclude` for gitignored files to copy
4. Document workflow in `AGENTS.md`

### Phase 4: Documentation (1 hour)
1. Update `README.md` with new structure
2. Update `AGENTS.md` with branching rules
3. Update wiki pages with new paths
4. Create `CONTRIBUTING.md` with workflow

---

## What Stays As-Is

- `chalumier/` submodule — reference implementation, don't touch
- `openwind/` submodule — external solver, don't touch
- `web/` — frontend stays separate, already organized
- `config/` — instrument configs stay here
- `wiki/` — stays as-is

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Import breakage | Run full test suite after migration |
| Lost work | Create backup branch before migration |
| Submodule paths break | Update `.gitmodules` if paths change |
| CI breaks | Test CI on feature branch before merging |
| Merge conflicts | Do migration in one atomic PR |

---

## Success Criteria

- [ ] Root directory has <30 entries
- [ ] All tests in `tests/` and pass
- [ ] CI runs on every push to main
- [ ] Experiment branches are disposable and isolated
- [ ] Worktrees enable parallel AI work
- [ ] No duplicate files across directories

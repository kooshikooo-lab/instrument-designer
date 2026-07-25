# Branch Comparison

> Current state after cleanup (2026-07-25). All dead branches deleted.

## Current Branches

| Branch | Status | Purpose | Last Commit |
|--------|--------|---------|-------------|
| `main` | **ACTIVE** | Shared stable branch, verified code only | `a80019a` 2026-07-25 |
| `laptop` | Redundant | All work now in main | `514e2f3` 2026-07-25 |
| `experiment/lbfgs-bore` | Keep | L-BFGS optimizer (1.27c RMS) | `2d0b4de` 2026-07-21 |
| `experiment/sequential-optimizer` | Keep (desktop) | New optimizer + LLM prompts | `648b7de` 2026-07-25 |
| `option-a-tauri` | Side branch | Compute decision doc | `c829540` 2026-07-24 |
| `ui/card-design` | Ancient | Old UI mockups | `14338d4` 2026-07-22 |
| `origin/scipy-prototype` | Frozen | Original prototype reference | `34bf13c` 2026-07-06 |
| `origin/experiment-chalumier-integration` | Reference | Chalumier SVG integration | `38bc7c9` 2026-07-21 |

## Deleted Branches (2026-07-25)

### Local (merged into main)
- `experiment/cadquery-test`, `experiment/flute-pvc`, `experiment/independent-hole-placement`
- `experiment/tmm-improvements`, `experiment/bore-profile-optimization`
- `fix/cumulative-fingering-openopen`, `fix/open-open-fingering-convention`
- `option-b-web-app`, `ui/magazine-design`, `ui/wiki-design`
- `refactor/architecture-redesign`, `experiment/bass-clarinet-stl`

### Remote (17 dead branches deleted)
All `exp/*`, superseded experiment, fix, and UI branches removed from origin.

## Merge Priority

1. **`experiment/lbfgs-bore`** — clean, L-BFGS optimizer algorithm
2. **`experiment/sequential-optimizer`** — desktop's new work, needs review
3. **`origin/experiment-chalumier-integration`** — has conflicts, valuable integration

## Communication Protocol

- **Primary:** Tailscale direct chat (port 9123)
- **Secondary:** GitHub issues (documentation, research, bugs)
- **Wiki:** Updated with findings, decisions, architecture

# Branch Comparison

> Full audit of all branches. Recommendations for merge/keep/discard.

## Summary

| Action | Count | Branches |
|--------|-------|----------|
| **MERGE into laptop** | 3 | `experiment/lbfgs-bore`, `ui/card-design`, `origin/experiment-chalumier-integration` |
| **KEEP as reference** | 1 | `origin/scipy-prototype` |
| **DISCARD (local)** | 12 | `experiment/bore-profile-optimization`, `experiment/cadquery-test`, `experiment/flute-pvc`, `experiment/independent-hole-placement`, `experiment/tmm-improvements`, `fix/cumulative-fingering-openopen`, `fix/open-open-fingering-convention`, `option-a-tauri`, `option-b-web-app`, `refactor/architecture-redesign`, `ui/magazine-design`, `ui/wiki-design` |
| **DISCARD (remote)** | 9 | `origin/exp/acoustic-element-hierarchy`, `origin/exp/gp-correction-model`, `origin/exp/impedance-primary`, `origin/experiment/alto-sax-bore-profile`, `origin/experiment-processpoolexecutor`, `origin/experiment-staged-optimization`, `origin/experiment/trumpet-openwind`, `origin/experiment/v2-scipy-gradient`, `origin/fix/alto-sax-open-open` |

## MERGE — Should Be Integrated

### `experiment/lbfgs-bore`
- **Purpose:** L-BFGS-B two-phase bore optimizer
- **Unique work:** 1 commit, 583 lines across 5 files (`bore_optimizer_lbfgs.py`, test scripts)
- **Achievement:** 1.27 cents RMS on test instruments
- **Conflict with laptop:** None
- **Action:** Clean merge. Useful algorithmic work.

### `ui/card-design`
- **Purpose:** Card-based resource/instrument UI design
- **Unique work:** 2 commits, 1,507 lines across 8 files (AI art, frequency viz, sound player, spectrum analyzer)
- **Conflict with laptop:** None
- **Action:** Clean merge. Enriches instrument detail view with unique UI components.

### `origin/experiment-chalumier-integration`
- **Purpose:** Chalumier acoustic engine integration (backend endpoints, SVG bore renderer, build trigger)
- **Unique work:** 5 commits, 487 lines across 5 files (`BoreProfileView.tsx`, `DesignTab.tsx`, `api.ts`, `design_server.py`)
- **Conflict with laptop:** Yes (4 conflicts — `DesignTab.tsx`, `api.ts`, `design_server.py`, `LIVE-CHAT-LOG.md`)
- **Action:** Merge with conflict resolution. Valuable Chalumier integration that laptop doesn't have.

## KEEP — Side Branches

### `origin/scipy-prototype`
- **Purpose:** Original scipy DE + basinhopping optimizer prototype with folk flute design output
- **Unique work:** 5 commits, 5,834 lines (scipy optimizer, folk flute config, design SVG/data)
- **Conflict with laptop:** None
- **Action:** Keep as frozen reference. Contains original prototype artifacts useful for validation.

## DISCARD — Dead Branches (Fully Merged)

These branches are at the same commit as laptop or main. All work has been integrated. Safe to delete.

| Branch | Reason |
|--------|--------|
| `experiment/bore-profile-optimization` | All 6 commits in laptop |
| `experiment/cadquery-test` | Was the primary dev branch — became laptop |
| `experiment/flute-pvc` | Merged into both main and laptop |
| `experiment/independent-hole-placement` | Merged into both main and laptop |
| `experiment/tmm-improvements` | Merged into both main and laptop |
| `fix/cumulative-fingering-openopen` | Merged into both main and laptop |
| `fix/open-open-fingering-convention` | Merged into both main and laptop |
| `option-a-tauri` | All Tauri work in laptop |
| `refactor/architecture-redesign` | Synced with laptop (all files identical) |

## DISCARD — Superseded Branches

| Branch | Reason |
|--------|--------|
| `option-b-web-app` | Rejected architecture (Tauri chosen). 35k lines of divergent code with conflicts. All useful ideas independently implemented in laptop. |
| `ui/magazine-design` | Overlaps with `ui/card-design` (same 6 files). Weakest of three UI variants. |
| `ui/wiki-design` | Overlaps with `ui/card-design` (same 6 files). `card-design` is most complete. |

## DISCARD — Remote Dead Branches

These remote branches point to commits already in laptop or main.

| Branch | Reason |
|--------|--------|
| `origin/exp/acoustic-element-hierarchy` | Same commit as KeefeLoss/impedance-primary |
| `origin/exp/gp-correction-model` | Same commit as above |
| `origin/exp/impedance-primary` | Same commit as above |
| `origin/experiment/alto-sax-bore-profile` | All 12 commits in laptop |
| `origin/experiment-processpoolexecutor` | Single benchmark script, not production code |
| `origin/experiment-staged-optimization` | Merged into laptop via experiment/cadquery-test |
| `origin/experiment/trumpet-openwind` | All content merged into laptop |
| `origin/experiment/v2-scipy-gradient` | Merged into main and laptop |
| `origin/fix/alto-sax-open-open` | Merged into main |

## Detailed Branch Pages

- [[Branch-laptop]] — Current active branch
- [[Branch-main]] — Shared stable branch
- [[Branch-option-a-tauri]] — Tauri UI (desktop decides)
- [[Branch-experiment-trumpet]] — Trumpet model
- [[Branch-refactor-architecture]] — Architecture redesign

## Feature Matrix

| Feature | laptop | main | option-a-tauri | architecture |
|---------|--------|------|----------------|--------------|
| KeefeLoss | ✅ | ❌ | ❌ | ✅ (synced) |
| true_wavelength_near | ✅ | ❌ | ❌ | ✅ (synced) |
| Per-note register | ✅ | ❌ | ❌ | ✅ (synced) |
| Two-phase optimizer | ✅ | ❌ | ❌ | ✅ (synced) |
| Staged optimizer | ✅ | ❌ | ✅ | ✅ (synced) |
| 91 instruments | ✅ | ❌ | ❌ | ✅ (synced) |
| Hole diameter opt | ✅ | ❌ | ❌ | ✅ (synced) |
| Absolute RMS metric | ✅ | ❌ | ⚠️ median | ✅ (synced) |
| Tauri integration | ✅ | ❌ | ✅ | ✅ (synced) |
| AI assistant | ❌ | ❌ | ✅ | ❌ |
| Trumpet model | ❌ | ❌ | ❌ | ❌ |
| Optimization UI | ❌ | ❌ | ✅ | ❌ |
| Wiki tab | ❌ | ❌ | ✅ | ❌ |

## Merge Priority

1. **`experiment/lbfgs-bore`** — clean merge, useful optimizer algorithm
2. **`ui/card-design`** — clean merge, enriches instrument detail UI
3. **`origin/experiment-chalumier-integration`** — has conflicts, needs manual resolution, but valuable Chalumier integration

## Cleanup Commands

```bash
# Delete local dead branches
git branch -d experiment/bore-profile-optimization experiment/cadquery-test experiment/flute-pvc experiment/independent-hole-placement experiment/tmm-improvements fix/cumulative-fingering-openopen fix/open-open-fingering-convention option-a-tauri refactor/architecture-redesign

# Delete local superseded branches
git branch -D option-b-web-app ui/magazine-design ui/wiki-design

# Delete remote dead branches
git push origin --delete exp/acoustic-element-hierarchy exp/gp-correction-model exp/impedance-primary experiment/alto-sax-bore-profile experiment-processpoolexecutor experiment-staged-optimization experiment/trumpet-openwind experiment/v2-scipy-gradient fix/alto-sax-open-open
```

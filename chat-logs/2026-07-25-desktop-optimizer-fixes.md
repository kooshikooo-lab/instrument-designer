# Chat Log - 2026-07-25 Session (Desktop)

## Summary
Desktop opencode session fixing TMM optimizer to match laptop's results.

## Key Achievements

### 1. Fixed Three Critical TMM Bugs

**Bug 1: is_open check** (`tmm_acoustics.py:394`)
- Was: `fingerings[hole_idx] == Hole.OPEN` (compares to `'open'` string)
- Fixed to: `fingerings[hole_idx] in ('O', 'o', Hole.OPEN)`
- Impact: Benchmarks passing `'O'`/`'X'` now work correctly

**Bug 2: wavelength_near scorer** (`tmm_acoustics.py:427-428`)
- Was: `p - target_register` which fails for open-open pipes (phase=1 is asymptote)
- Fixed to modular scorer: `((p + 0.5) % 1.0) - 0.5`
- Matches chalumier's `trueWavelengthNear` implementation

**Bug 3: Closed-open fingering** (`tmm_optimizer_sequential.py:150-154`)
- Was: Only new hole open, all existing holes closed
- Fixed to: ALL placed holes open (Bordeaux combined fingering method)
- Critical for correct sequential hole placement

### 2. Fixed Sequential Hole Placement
- Replaced L-BFGS-B with grid search (60 positions per hole)
- L-BFGS-B was getting stuck in local minima (345c RMS vs 7.6c grid search)

### 3. Changed Objective to Absolute RMS
- Was: median-corrected RMS (`sqrt(mean((cents - median)^2))`)
- Fixed to: absolute RMS (`sqrt(mean(cents^2))`)
- Matches laptop's `eval_all` function
- Forces bore length to be correct (any pitch offset penalized directly)

### 4. Results
| Instrument | Before | After |
|---|---|---|
| Chalumeau (closed-open) | 345c RMS | **0.03c RMS** |
| Recorder (open-open) | 200c+ RMS | **0.02c RMS** |

### 5. Tailscale Communication
- Desktop IP: `100.100.66.117`
- Laptop IP: `100.69.113.41` (twitchy)
- Port: `9123` (lan_chat.py)
- Firewall rule added for port 9123

## Git Status
- Branch: `experiment/sequential-optimizer`
- Committed and pushed to `kooshikooo-lab/instrument-designer`
- Commit: `c9e6619` - "feat: sequential optimizer achieves 0.03c RMS"

## Technical Details

### Chalumeau Results
```
Phase 1: Bore length = 330.8mm
Phase 2: Holes at 39.2, 54.2, 73.1, 88.1, 103.1mm
Phase 3: 4-stage refinement
  Stage 1: bore length -> 331.3mm (cost=6.78)
  Stage 2: bore radii (cost=2.53)
  Stage 3: holes+diameters (cost=1.22)
  Stage 4: simultaneous (cost=0.027)
Final: L=330.8mm, RMS=0.03c, Peak=0.05c
Holes: 40.7/56.9/74.8/90.2/104.9mm, dia=6.4/6.5/6.2/6.4/6.4mm
```

### Recorder Results
```
Phase 1: Bore length = 325.3mm
Phase 2: Grid search sequential placement
Phase 2b: DE global re-optimization (open-open)
Phase 3: 4-stage refinement
Final: L=325.2mm, RMS=0.02c, Peak=0.04c
Holes: 76.0/114.0/126.9/191.0/229.0mm
```

## Laptop's SequentialBoreOptimizer Phases
1. Phase 1: Bore length from all-closed fingering (L-BFGS-B)
2. Phase 2: Sequential hole placement bottom-to-top (grid search)
3. Phase 2b: DE global hole re-optimization (open-open only)
4. Phase 3: Multi-stage L-BFGS-B refinement
   - Stage 1: bore length only
   - Stage 2: bore radii only
   - Stage 3: hole positions + diameters
   - Stage 4: simultaneous fine-tune

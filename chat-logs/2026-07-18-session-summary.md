# Session Summary: 2026-07-18

## What We Did

### Research Phase
- Researched highest possible intonation accuracy for 3D-printed wind instruments
- Analyzed two separate areas: (1) matching verified well-intonated designs, (2) 3D print accuracy effects
- Ran diagnostic tests on our impedance solver resolution

### Optimizer Fixes
- Increased default frequency resolution: 800 → 5000 points
- Added quadratic interpolation for peak finding (sub-bin accuracy)
- Added impedance caching (2000 entry LRU, instant repeated calls)
- Created ROADMAP.md with prioritized tasks

### Code Review Fixes (Claude's feedback)
- Renamed `finished` → `simulationFinished` in SimulationWorker (avoids QThread signal shadowing)
- Added try/except in SimulationWorker.run() (prevents stuck UI on exception)
- Added public methods to ProjectWidget (fixes encapsulation violation)
- Fixed os.startfile for cross-platform (Windows/macOS/Linux)

## Key Findings
- **<10 cents IS achievable** — Noreland 2013 achieved 0.5 cents RMS computationally
- **3D print is the bottleneck** — SLA resin gives 5-12 cents error (borderline but workable)
- **Our solver now converges**: 5000 pts → 278.778 Hz, 10000 pts → 278.776 Hz (stable)
- **Caching works**: 10 repeated calls = 0.000ms (instant)

## Error Budget (Research Document)
- Bore optimization residual: 0.5-5 cents
- SLA print error (compensated): 5-12 cents
- Temperature: ~6 cents/°C (player variable, not manufacturing)

## Files Created/Modified
- `chat-logs/2026-07-18-intonation-accuracy-research.md` — full research document
- `chat-logs/2026-07-18-session-summary.md` — this file
- `backend/optimizer.py` — fixed resolution, interpolation, caching
- `woodwind_designer/gui/simulation_widget.py` — fixed signal naming, exception handling
- `woodwind_designer/gui/project_widget.py` — added public methods, cross-platform folder open
- `woodwind_designer/gui/main_window.py` — uses public methods, cross-platform folder open
- `ROADMAP.md` — prioritized task list
- `instrument-designer-share.zip` — updated with all fixes

## Next Session
- Test optimizer end-to-end with small target set
- Reduce optimizer time (consider smaller pop_size/generations)
- Add global pitch offset correction
- Validate <10 cents on synthetic targets

## Decision Points
- Use SLA resin over FDM for production
- Need material shrinkage calibration before printing
- Consider hybrid approach (3D print mold → cast final instrument)

# Architecture Guide

> **⚠ AI Governance in effect.** Before coding, read `CONSTRAINTS_AND_PREFERENCES.md` (boot sequence) and `AI_CONSTITUTION.md` (10 laws). Compliance checks run on: 15min timer, before code, after tests, when stuck. See `COMPLIANCE_CHECK.md`.

## Directory Structure

```
instrument-designer/
├── backend/                 # Core acoustic engine + pipeline modules
│   │                         # (ADR-001: geometry separate from acoustics)
│   │                         # (ADR-004: shared optimizer in pareto_optimizer)
│   │                         # (ADR-005: three-tier pipeline)
│   ├── sound_analysis.py        Tier 1: pure signal processing (leaf module)
│   ├── pareto_optimizer.py      Shared optimizer: nsga2_minimize, run_pareto, pareto_sweep
│   ├── design_from_wav.py       Thin orchestrator: WAV → optimizer (Tiers 1→2→3)
│   ├── design_from_unconventional.py  Thin orchestrator: spline bores → optimizer
│   ├── geometry.py              Explicit geometry layer (BoreProfile, InstrumentGeometry)
│   ├── inverse_design.py        Backward-compat re-export layer only (ADR-003)
│   ├── design_pipeline.py       Mode-switching dispatcher
│   ├── generative_agent.py      LLM-guided instrument knowledge + design
│   ├── tmm_acoustics.py         TMM solver (primary, ADR-006)
│   ├── cadquery_export.py       STL/STEP 3D model export
│   ├── jax_optimizer.py         JAX-accelerated gradient refinement
│   ├── spline_bore.py           Cubic spline bore profiles
│   ├── instrument_knowledge.py  Instrument family knowledge base
│   ├── physics/                 Visothermal loss models
│   ├── core/                    Core abstractions
│   ├── optimization/            Optimization helpers
│   ├── instruments/             Pre-defined instrument configs
│   ├── reference_instruments/   CSV reference data
│   └── ...                      Legacy/archived modules
│
├── woodwind_designer/       # GUI application (Tauri backend)
│   └── design_server.py     FastAPI server (imports from backend/)
│
├── web/                     # Tauri/Vite frontend (TypeScript)
├── config/                  # Instrument configuration JSON files
├── tests/                   # ALL test files
├── scripts/                 # ALL utility/debug/benchmark scripts
├── docs/                    # ALL documentation, governance, prompts
│   ├── CONSTRAINTS_AND_PREFERENCES.md *Boot sequence for AI agents*
│   ├── AI_CONSTITUTION.md           *Non-negotiable project laws*
│   ├── ARCHITECTURE_DECISIONS.md    *Architecture Decision Records (ADRs)*
│   ├── ARCHITECTURE_CHECKLIST.md    *Pre-flight and pre-commit checklist*
│   ├── AI_FAILURE_PATTERNS.md       *Logged AI mistakes and prevention*
│   ├── ARCHITECTURE.md              *This file — system map + conventions*
│   ├── CODING_STANDARDS.md          *Documentation + design rules*
│   ├── BEST_PRACTICES.md            *Debugging framework*
│   ├── PHYSICS_PRINCIPLES.md        *Acoustic modeling assumptions*
│   ├── ACOUSTIC_DESIGN_OPTIMIZATION.md  *Survey + priority recommendations*
│   ├── prompts/                     *AI prompt templates*
│   └── session-logs/                *Development session logs*
├── research/                # Research documents and references
├── designs/                 # Design output (JSON, SVG, STL)
└── README.md                # Project overview
```

### Key rules:
- `backend/` root: ONLY core source modules (no test/debug files)
- `tests/`: ALL test files (from any location)
- `scripts/`: ALL utility/debug/benchmark scripts
- `docs/`: ALL documentation, prompts, session logs
- Root: ONLY config files (pyproject.toml, README.md, etc.)

---

## Coordinate Systems

When integrating multiple acoustic tools, coordinate systems MUST be documented explicitly.

### Chalumier (Kotlin instrument designer)

```
Bore axis: 0 = bell (open end), L = mouthpiece/reed (closed end)
Hole numbering: hole1 = nearest bell, holeN = nearest mouthpiece
Hole positions: measured from bell (0)
Fingering notation: X = closed (finger down), O = open (finger up)
```

### OpenWind (FEM/TMM acoustic simulator)

```
Bore axis: 0 = mouthpiece, L = bell
Hole numbering: hole1 = nearest mouthpiece, holeN = nearest bell
Hole positions: measured from mouthpiece (0)
Fingering notation: x = closed (finger down), o = open (finger up)
```

### Our TMM (backend/tmm_acoustics.py)

```
Bore axis: 0 = mouthpiece, L = bell (same as OpenWind)
Hole numbering: follows AcousticNetwork segment order
Fingering notation: Fingerings dict with True=closed, False=open
```

### Conversion Rules

When converting between tools:
1. **Bore positions**: Reverse order and subtract from total length
   - chalumier pos_from_bell → OpenWind pos_from_mouthpiece = L - pos_from_bell
2. **Hole positions**: Same transformation as bore positions
3. **Hole numbering**: Reverse indices (chalumier hole1 → OpenWind holeN)
4. **Fingering charts**: Keep hole labels consistent with the TARGET tool's numbering
5. **Fingering notation**: X/x = closed, O/o = open (consistent across tools)

---

## Fingering Charts

Fingering charts are **independent data structures** from bore geometry.

### Structure

```
Fingering Chart = {
    notes: [note_name_1, note_name_2, ...],
    holes: {
        hole_1: [state_for_note_1, state_for_note_2, ...],
        hole_2: [state_for_note_1, state_for_note_2, ...],
        ...
    }
}
```

Where state = 'x' (closed) or 'o' (open).

### Key Principles

1. **Separation**: Fingering charts are NOT part of bore geometry
   - Bore: positions, diameters, lengths
   - Fingering: which holes are open/closed for each note
   - These are independent design variables

2. **Multiple fingerings per note**: Same note can be produced by different hole combinations
   - Example: D5 on pennywhistle can be played with different fingerings
   - Each fingering has different intonation and timbre characteristics
   - Advanced modeling explores this space; basic modeling uses one fingering per note

3. **Coordinate independence**: Fingering charts use the TOOL's hole numbering
   - When converting between tools, remap hole indices
   - Never assume hole1 in tool A = hole1 in tool B

### Example: D Pennywhistle (6 holes)

Chalumier format (.chal file):
```
fingerings = [
    { noteName="D4", fingers=["X", "X", "X", "X", "X", "X"] },  // all closed
    { noteName="E4", fingers=["O", "X", "X", "X", "X", "X"] },  // hole1 open
    ...
]
```

OpenWind format:
```python
fingerings = [
    ['label', 'D4', 'E4', ...],       # note names
    ['hole1', 'x', 'o', ...],         // hole1 states
    ['hole2', 'x', 'x', ...],         // hole2 states
    ...
]
```

Our format (AcousticNetwork):
```python
fingerings = {
    'D4': {0: True, 1: True, 2: True, 3: True, 4: True, 5: True},  # all closed
    'E4': {0: False, 1: True, 2: True, 3: True, 4: True, 5: True},  # hole0 open
    ...
}
```

---

## Tool Integration Guidelines

### When bridging tools:

1. **Document coordinate systems at function entry**
   ```python
   def convert_chalumier_to_openwind(chalumier_params):
       """Convert chalumier output to OpenWind format.
       
       Chalumier coordinates:
       - Bore: 0=bell, L=mouthpiece
       - Holes: numbered from bell (hole1=nearest bell)
       - Positions: measured from bell
       
       OpenWind coordinates:
       - Bore: 0=mouthpiece, L=bell
       - Holes: numbered from mouthpiece (hole1=nearest mouthpiece)
       - Positions: measured from mouthpiece
       """
   ```

2. **Never assume hole numbering is consistent**
   - Always check which tool's convention you're using
   - When in doubt, add explicit comments

3. **Keep fingering charts as separate variables**
   - Don't embed fingering data in bore geometry
   - Pass fingering charts as separate arguments

4. **Validate conversions**
   - After conversion, verify that fingering chart maps correctly to hole positions
   - Check that expected notes are produced at expected frequencies

### Testing conversions:

```python
# After converting chalumier → OpenWind:
# 1. Verify bore profile makes physical sense
assert ow_bore[0][0] == 0  # starts at mouthpiece
assert ow_bore[-1][1] == length  # ends at bell

# 2. Verify hole positions are within bore
for hole in ow_holes[1:]:  # skip header
    assert 0 <= hole[1] <= length

# 3. Verify fingering chart maps to correct holes
# D4 (all closed): all holes should be 'x'
assert all(fingerings[h][0] == 'x' for h in range(1, num_holes+1))
```

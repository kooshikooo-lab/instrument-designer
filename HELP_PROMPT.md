# Help Prompt: Computational Wind Instrument Design

Copy this entire file into Claude or ChatGPT for context.

---

## Project Overview

We are building a **computational wind instrument design system** using acoustic modeling. The system should be general enough to design any woodwind or brass instrument. Bass clarinet is our first priority because the developer plays it, but the architecture is instrument-agnostic.

We use three layers:
1. **TMM Engine** (Python, fast ~1.7ms/note) — Transfer Matrix Method for rapid design optimization
2. **OpenWInD FEM** (Python, slow) — 1D Finite Element Method for high-fidelity validation
3. **Chalumier** (Kotlin, reference implementation) — upstream TMM code we ported from

The design pipeline:
- TMM explores the design space (optimizes bore, hole positions, diameters, fingerings)
- OpenWInD validates the top candidates with more accurate physics
- Ideally: learn a correction model (TMM error vs FEM) to improve future optimization

## Reference Codebases

### Chalumier (MarkChuCarroll/chalumier)
Our primary TMM reference. Kotlin, based on demakein. Produces SVG + JSON instrument designs.
```
C:\Users\Admin\Desktop\Woodwind design automation\chalumier\
└── app\src\main\kotlin\org\goodmath\chalumier\design\
    ├── instruments\Instrument.kt       # Core TMM (preparePhase, resonancePhase)
    ├── InstrumentDesigner.kt           # Design parameters (bore, holes, etc.)
    ├── ReedInstrumentDesigner.kt       # Reed instrument specifics
    └── Fingering.kt                   # Fingering data class
```

### OpenWInD (thecowgoesmoo/openwind)
Python FEM toolbox for wind instrument acoustics. Higher fidelity, slower.
```
C:\Users\Admin\Desktop\Woodwind design automation\openwind\
```

## CRITICAL: Coordinate System

This has caused major bugs. Get this right first.

### Chalumier (reference, CORRECT)
```
Position 0.0  = BELL (open end, bottom/base)
Position = L  = REED (closed end, top/mouthpiece)
Walk direction: bell → reed (ascending position)
Phase starts at 0.5 (open end = bell at position 0)
Hole index 0 = nearest BELL
Hole index N-1 = nearest REED
Ascending scale: open from index 0 first (nearest bell = small pitch rise)
```

Proof from chalumier source (Instrument.kt):
```kotlin
var phase = 0.5 // ph: open end  (at position 0 = bell)
var reply = (-1.0).R  // ph: open end  (at position 0 = bell)

var position = -endFlangeLengthCorrection(outer(0.0, true), steppedInner(0.0, true))

open var innerDiameters by listOfDoublePairParameter(
    "The first element is the bore diameter at the base of the instrument; " +
    "the last element is the bore diameter at the top of the instrument."
)
```

### Our Code (Python)
```
Position 0   = REED (closed end)
Position = L = BELL (open end)
Walk direction: bell → reed (DESCENDING position)
Phase starts at 0.5 (open end = bell at position L)
Hole index 0 = nearest REED
Hole index N-1 = nearest BELL
Ascending scale: open from LAST index first (nearest bell = small pitch rise)
```

### Fingering Convention
```python
# Index 0 = nearest REED, Index N-1 = nearest BELL
# Ascending scale = open from LAST index first
fingering_sets = [
    ["closed"] * N,                                    # all closed = lowest note
    ["closed", "closed", ..., "open"],                 # bell hole opens first (small rise)
    ["closed", "closed", ..., "open", "open"],         # 2 bell holes
    ...
    ["open"] * N,                                      # all open = highest note
]
```

## Physics Principles (NON-NEGOTIABLE)

1. **All holes closed = lowest note** (longest effective tube)
2. **Ascending scale = open holes from bell end first** (small pitch rise per hole)
3. **Opening near reed = huge pitch jump** (near pressure antinode)
4. **Opening near bell = small pitch rise** (near pressure node)
5. **Phase = 0.5 at open end (bell), integer at closed end (reed) at resonance**
6. **If code results contradict physics, the code is wrong — not the physics**

## Code Architecture

### tmm_acoustics.py — Core TMM Engine
```python
class TMMInstrument:
    """
    Phase-based TMM instrument model.
    Walk direction: bell (position L) → reed (position 0)
    Phase = 0.5 at open end (bell), integer at resonance (reed)
    """
    
    def _prepare_phase(self):
        """Build action chain walking bell→reed (descending position)."""
        events.sort(key=lambda e: e[0], reverse=True)  # DESCENDING
        position = self.length + end_flange_length_correction(...)  # start at bell
        diameter = self.stepped_inner.at(self.length, ...)  # bell diameter
        # Walk descending: seg_length = position - pos (positive)
        # End event at position 0 (reed)
    
    def resonance_phase(self, wavelength, fingerings):
        """Phase = 0.5 at bell, walk to reed. Integer = resonance."""
        phase = 0.5  # Open end (bell)
        for action in self.actions:
            phase = pipe_reply_phase / junction2 / junction3
        if not self.closed_top:
            phase += 0.5  # Only for open-open pipes (flutes)
        return phase
    
    def find_resonance(self, wavelength_near, fingerings, n_register=1):
        """Find resonant wavelength near target for nth register."""
    
    def compute_fingered_frequencies(self, wavelengths, fingering_sets, n_register):
        """Compute actual frequencies for a set of fingerings."""
```

### optimizer_global.py — Design Optimizer
```python
class GlobalFingeringOptimizer:
    """Optimize all hole positions simultaneously via DE + L-BFGS-B."""
    
    def _evaluate(self, free_positions):
        """Compute weighted RMS cents error across both registers."""
        # Sorts holes by position
        # Creates TMMInstrument
        # For each note: finds resonance, computes cents error
        # Returns combined 1st + 2nd register cost
```

### fingering_reference.py — Real Bass Clarinet Fingering Chart
```python
# H1 = top (closest to reed), H12 = bottom (closest to bell)
# Format: {note: [H1..H12, R]} where 1=open, 0=closed
FINGERING_CHART_CHALUMEAU = {
    "D2":  [0,0,0,0,0,0,0,0,0,0,0,0, 0],  # all closed
    "E2":  [0,0,0,0,0,0,1,0,0,0,0,0, 0],  # H7 open (bell half)
    "F2":  [0,0,0,0,0,1,1,0,0,0,0,0, 0],  # H6+H7
    ...
    "D3":  [1,1,1,1,1,1,1,0,0,0,0,0, 0],  # H1-H7 (all 7 primary)
}
# Note: In this chart, index 0 = H1 = nearest REED
# So "E2" opens H7 (index 6) = nearest bell = CORRECT physics
```

### benchmark_chalumeau.py — Test Instruments
```python
INSTRUMENTS = {
    "chalumeau": {
        "hole_positions": [50.0, 90.0, 130.0, 170.0, 210.0, 250.0],
        # Bell-first ascending: open from LAST index first
        "fingering_sets": [
            ["closed"] * 6,
            ["closed","closed","closed","closed","closed","open"],
            ["closed","closed","closed","closed","open","open"],
            ...
        ],
    },
}
```

## Key Technical Details

- 25mm bore radius (12.5mm), ~1159mm optimized effective length
- Register hole at 80mm from reed, 2.5mm diameter
- Graduated hole diameters: 14.5mm (reed end) → 20mm (bell end)
- Bell: 220mm Bessel flare, 52mm ID (deferred — degrades 12ths)
- Plane-wave cutoff for 25mm bore ≈ 8kHz (well above operating range 70-150Hz)
- Single TMM note ~1.7ms, full chart (13 notes) ~65ms
- Multi-start DE is essential: 5 seeds gave range 4.3c to 11.6c RMS

## What We've Fixed

- TMM walk direction now matches chalumier (bell→reed, descending)
- All benchmark fingering charts reversed to bell-first ascending
- Physics-first principle documented in PHYSICS_PRINCIPLES.md

## What's Broken / Needs Work

- Need to re-run optimization with corrected TMM and fixed fingering charts
- Previous "4.3c RMS" result was from WRONG physics (reed-first fingering)
- Bell model deferred: adding bell degrades 12ths from 9.5c to 423c
- Register hole optimization not yet joint with bore length
- Viscothermal losses not yet modeled
- No OpenWInD validation workflow yet

## Specific Questions / Help Needed

### 1. TMM Validation
Our TMM is lossless and plane-wave only. How accurate is this for a 25mm bore bass clarinet?
- Plane-wave cutoff for 25mm bore ≈ 8kHz (well above operating range 70-150Hz)
- But viscothermal losses are significant in long narrow bores
- How much error do we expect from neglecting losses?

### 2. Register Hole Modeling
The register hole (80mm from reed, 2.5mm diameter) is critical for 2nd register.
- Our TMM models it as a simple T-junction
- How accurate is this for register venting?
- Should we optimize register hole position jointly with bore length?

### 3. Chromatic Fingering Design
We need full chromatic D2-D5 (about 3 octaves).
- The chalumeau register (D2-B2) uses cross-fingerings
- The clarion register (B3-G4) uses register key + chalumeau fingerings
- How should we design the fingering chart for optimization?
- Sequential (simple, 12 holes) vs. cross-fingered (realistic, 7+ holes)?
- Don't imitate Boehm system — design acoustically optimal fingering graph first

### 4. Bore Optimization
We've been optimizing bore length and hole positions separately.
- Should we optimize bore length jointly with hole positions?
- What about bore taper (cylindrical vs. slightly conical)?
- How does the bell flare model affect intonation?

### 5. OpenWInD Integration
We want to use OpenWInD (FEM) to validate TMM results.
- What's the best way to compare TMM vs FEM results?
- Should we compare impedance curves, resonant frequencies, or both?
- How do we handle the frequency-dependent discrepancy between TMM and FEM?

### 6. General Wind Instrument Design
Since the goal is general wind instrument design:
- What parameters should the optimizer expose for different instrument families?
- How should the system handle reed vs. lip-reed vs. fipple exciters?
- What are the key differences in TMM modeling for different instrument types?

## Files in the Project

```
C:\instrument-designer\
├── backend\
│   ├── tmm_acoustics.py          # Core TMM engine (ported from chalumier)
│   ├── optimizer_global.py       # Global fingering optimizer (DE + L-BFGS-B)
│   ├── fingering_reference.py    # Real bass clarinet fingering chart
│   ├── benchmark_chalumeau.py    # Test instrument configs
│   ├── benchmark_bass_clarinet.py
│   ├── benchmark_all.py
│   └── test_*.py                 # Various test scripts
├── PHYSICS_PRINCIPLES.md         # Physics-first rules
├── RESEARCH_PROMPTS.md           # Research topics
├── STATUS.md                     # Current project status
└── chat-logs/                    # Session logs
```

# Bass Clarinet Design Automation — Status

## Code
- `backend/tmm_acoustics.py` — TMM engine (phase-based, ported from chalumier)
- `backend/optimizer_global.py` — **Two-register** global fingering optimizer (DE + L-BFGS-B)
- `backend/tmm_optimizer_sequential.py` — Sequential Bordeaux optimizer (≤8 holes)
- `backend/bass_clarinet_full_test.py` — 7-hole D major + register validation
- `config/bass_clarinet_7hole.json` — Working config (uniform cylinder)

## Results

| Configuration | Reg1 RMS | Reg2 RMS | Notes |
|---|---|---|---|
| 7-hole diatonic, sequential | 6.19c | 9.51c | Two-register optimizer |
| 12-hole chromatic, sequential | 15.50c | 15.57c | Physics-limited |
| 12-hole with cross-fingerings | 47.33c | 46.41c | Poorly designed chart |

## What We Know

**Confirmed (ChatGPT research 2026-07-23):**
1. **tanner/untanner = normalized admittance** in tangent form. Physically correct.
2. **-0.5 phase for open hole = R=-1 reflection** at open end. Correct.
3. **70-150Hz is the strongest regime** (plane-wave cutoff ~8kHz, ka~0.007-0.015).
4. **Uniform offset for 11mm holes** is the expected physics — small holes at low frequencies have high Q shunt impedance (Q >> 100). Not a model bug.
5. **20mm holes give non-uniform errors** — confirms model sensitivity to local interactions.
6. **Holes should be graduated**: 10-12mm (lowest), 9-11mm (middle), 7-9mm (upper).

**Current Blockers:**
1. **12-hole sequential chromatic is physics-limited** (15-20c RMS). Sequential fingering can't produce fine semitones with small holes at low frequencies.
2. **Cross-fingerings need proper design** — my ad-hoc patterns (46c) are worse than sequential. Need research on real clarinet cross-fingering systems.
3. **OpenRouter API expired** — can't use AI-assisted coding.

## Next Steps
1. **Research**: Submit cross-fingering design prompt to ChatGPT (need proper chart based on Boehm/Oehler systems)
2. **Research**: Submit graduated hole sizes prompt
3. **Code**: Implement proper cross-fingering chart from research
4. **Code**: Add hole diameter as optimization variable (parametrized graduation)
5. **Code**: Add bore taper as optimization variable (for better twelfths)

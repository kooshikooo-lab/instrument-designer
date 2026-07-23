# Woodwind & Brass Design Automation - Project Overview

## What We're Building
An open-source computational tool for designing woodwind and brass instruments. It simulates bore acoustics using Transfer Matrix Method (TMM) and Finite Element Method (OpenWind), optimizes intonation via differential evolution + L-BFGS-B, and generates professional fingering charts.

**GitHub**: https://github.com/kooshikooo-lab/instrument-designer
**Branch**: experiment/trumpet-openwind (current active)
**OpenWind docs**: https://files.inria.fr/openwind/docs/

---

## Core Architecture

### Acoustics Engine
- `backend/tmm_acoustics.py` — TMM simulation for woodwinds (cylinders, cones, toneholes, register keys)
- `backend/trumpet_openwind.py` — OpenWind FEM model for brass (replaces TMM for trumpets)
- `backend/trumpet_acoustics.py` — custom TMM trumpet model (deprecated, kept for reference)

### Optimization
- `backend/tmm_optimizer_sequential.py` — Sequential optimization with Phase 2b global differential evolution re-optimization
- Uses L-BFGS-B for local refinement, DE (scipy) for global search

### Key Physics
- Woodwinds: open tone holes shorten effective bore length below cutoff frequency, register holes weaken fundamental
- Brass: bell flare compresses harmonic series from closed-pipe odd harmonics (1:3:5:7) toward near-harmonic (1:2:3:4:5)
- All instruments follow same logic: open holes shorten effective bore length
- Register is: n_register = 2 for open-open pipes, n_register = 1 for closed-top pipes
- TMM phase convention: pipe_reply_phase(phase, L/λ) = phase + 2L/λ; open end adds 0.5; resonance at integer n

### Literature References
- Lefebvre (2011) — Saxophone acoustics, tonehole modeling
- Nederveen (1969) — Woodwind instrument acoustics, cutoff frequency
- Dalmont et al. — Radiation impedance, end corrections
- McGill thesis — Computational woodwind design (hole placement)
- Tournemenne & Chabassier (2019) — OpenWind FEM vs TMM for brass
- Petiot (2025) — ML-based trumpet leadpipe optimization (Yamaha prototype)
- Piatt (WVU thesis, 2017) — Professional trumpet component measurements
- Sharp — Acoustic pulse reflectometry for bore reconstruction

---

## Results So Far

### Woodwinds (all sub-0.3c RMS after Phase 2b DE)
- dwhistle: 3.5c (L-BFGS-B) → sub-0.3c (DE)
- tin whistle: 0.91c
- soprano recorder 0.00c (all 7 instruments sub-1c RMS)
- Clarinet benchmark: 4.46c evenness

### Trumpet (current state)
- **Open fingering**: 243 Hz (Bb3 target 233 Hz, +7c)
- **Harmonic ratios**: 1.00, 1.49, 2.02, 2.52, 3.04 (correctly compressed)
- **Valve V1** (+whole tone): 204 Hz (lower ✓)
- **Valve V2** (+semitone): 224 Hz (lower ✓)
- **Valve V3** (+minor third): 211 Hz (lower ✓ — FIXED, was 253 Hz HIGHER)
- **V1+V2**: 194 Hz, **V2+V3**: 196 Hz, **V1+V3**: 181 Hz, **V1+V2+V3**: 171 Hz

---

## Current Blockers & Research Questions

### 1. Trumpet bore geometry — why is fundamental 243 Hz instead of 233 Hz?
We built a Bach 180-37 ML geometry (1.335m total, 5.83mm radius bore, Bessel bell to 61.12mm). The open fingering gives 243 Hz instead of Bb3=233 Hz. Is this expected? Do professional trumpets also show this slight sharpness due to the player's embouchure compensation? Or does our bore geometry need refinement — specifically the mouthpiece cup which we don't model?

### 2. Trumpet valve slide lengths — why do our formula values (±10-30c) not match perfect intervals?
We compute slide lengths using f ∝ 1/L: extra = L_total × (2^(n/12) − 1). For V1 (+2 st): 0.164m, V2 (+1 st): 0.079m, V3 (+3 st): 0.252m. But OpenWind gives errors ±30c from target. Is this because the bell flare makes effective length frequency-dependent? Should we be computing slide lengths differently for trumpets vs. the simple model?

### 3. Bass clarinet — full design from scratch (TOP PRIORITY for user)
What known designs exist? Key parameters: bore profile (cylindrical vs. tapered), tonehole placement strategy, register key mechanism (overblows at 12th like clarinet vs. octave). Which papers have detailed measurements?

### 4. Cutoff frequency optimization for woodwinds
Our 0.3c RMS woodwinds were achieved by optimizing hole positions for evenness. But real instruments have ±5-15c even on top-tier instruments. What's the known acoustic limit? Is our optimizer overfitting to a simplified model?

### 5. OpenWind valve modeling details
How exactly does OpenWind handle the junction between main bore and deviation pipe? Is there an acoustic mass or end correction at the junction that affects the effective length? The valve seems to add slightly less than the formula predicts.

---

## Key Files for Review
| File | Purpose |
|------|---------|
| `backend/tmm_acoustics.py` | TMM engine: TMMInstrument, Hole, Profile, resonance |
| `backend/tmm_optimizer_sequential.py` | Sequential + DE optimizer |
| `backend/trumpet_openwind.py` | OpenWind FEM trumpet model (558 lines) — active |
| `backend/ai_assistant.py` | AI coding/research helper module |
| `backend/lan_chat.py` | LAN chat for machine coordination |
| `ROADMAP.md` | Master roadmap with Phase 2b verification |
| `ROADMAP-Trumpet.md` | Trumpet-specific roadmap |
| `research/instrument-measurements.md` | 700+ lines of measured instrument dimensions |

---

## Modeling Gotchas (what we learned the hard way)

1. **Valve deviation pipe**: In OpenWind, deviation REPLACES the bypassed main bore section. Length must be = bypassed_section + extra_interval. If equal to bypassed, net length change is zero.

2. **No overlapping valve positions**: OpenWind errors if two valves share the same position. Each valve's entry must be after the previous valve's reconnection.

3. **First impedance peak is a sub-harmonic**: The first impedance peak (~89 Hz for a 1.335m trumpet) is a sub-harmonic. The played fundamental is the second peak (~233 Hz). Ratio computation must start from the correct fundamental.

4. **OpenWind API**: attribute is `.impedance` (not `.Z`), parameter is `note=` (not `fingering=`). Method can be FEM (default) or TMM.

5. **Phase cost is unsuitable as sole optimization objective**: Converges to wrong register basin. Must use peak-based cost or hybrid.

6. **Bore shape dominates intonation** more than hole positions. Kinks create area discontinuities that fundamentally determine resonance structure.

---

## How to Help Us
1. **Review our acoustic model**: Are we making any fundamental physics errors?
2. **Suggest improved bore geometry** for the trumpet to hit 233 Hz exactly
3. **Provide bass clarinet references**: Known designs, measured dimensions, key literature
4. **Review the OpenWind valve model**: Why does the simple slide length formula not match exact simulation?
5. **Suggest optimization improvements**: How to handle the frequency-dependent effective length issue
6. **Review the cutoff frequency physics**: Are our tonehole placement assumptions correct?

---

## Specific Questions for This Session

1. **OpenWind FEM trumpet**: We get 243 Hz fundamental instead of 233 Hz (Bb3). Is this the expected open-pipe resonance of a 1.335m tube with our exact bell profile? What's the correct quarter-wave resonance for a 1.335m tube with Bessel bell (r=5.83mm→61.12mm, parameter 0.7)?

2. **Valve slide compensation**: For a real Bb trumpet with total tube length ~1.335m, what are the actual slide lengths (in mm) for V1, V2, V3? Are they exactly the f ∝ 1/L formula, or is there bell-flare compensation?

3. **First steps for bass clarinet design**: What bore profile should we start with? Cylindrical with slight taper? Straight or tapered bore? What's the optimal bore diameter range? What register mechanism?

4. **Cutoff frequency for trumpet bell**: Our Bessel bell has parameter 0.7. What cutoff frequency does this produce? Is 0.7 appropriate for a Bb trumpet or should it be different?

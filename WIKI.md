# Instrument Designer — Project Wiki

## 1. Project Goals

Instrument Designer is an open-source computational tool for designing 3D-printable woodwind instruments with sub-cent intonation accuracy.

**Core objectives:**
- Build a fast, accurate acoustic simulator using the Transfer Matrix Method (TMM) for woodwinds
- Achieve **<3 cents RMS** intonation accuracy through multi-stage optimization (Differential Evolution + L-BFGS-B)
- Support an expandable instrument library spanning flutes, whistles, clarinets, saxophones, and recorders
- Provide AI-assisted design analysis via rule-based heuristics and LLM integration (OpenRouter free models)
- Democratize instrument design — non-technical users access the tool through a GUI (Tauri desktop or web browser)

The optimizer follows the Bordeaux group methodology (Noreland, Guilloteau, Ernoult): sequential hole placement followed by global evolutionary re-optimization and gradient-based refinement.

---

## 2. The Science (Acoustics)

### 2.1 Wind Instrument Acoustics Basics

A wind instrument is a resonant tube. The fundamental frequency is determined by the effective length of the air column and the end conditions:

| Condition | Harmonics | Fundamental wavelength | Examples |
|-----------|-----------|----------------------|----------|
| Open-open (both ends open) | All: f, 2f, 3f, 4f... | λ = 2L | Flute, recorder, tin whistle, saxophone |
| Closed-open (one end closed) | Odd: f, 3f, 5f, 7f... | λ = 4L | Clarinet, chalumeau, reedpipe |

Conical bores (saxophones, oboes) behave acoustically as open-open pipes — they produce all harmonics even when the mouthpiece end is closed by a reed.

### 2.2 Transfer Matrix Method (TMM)

The TMM engine in `tmm_acoustics.py` is a phase-based resonance model ported from chalumier (Mark C. Chu-Carroll, Paul Francis Harrison — Apache 2.0). Its key advantage over impulse-response methods like OpenWInD is speed: a single resonance evaluation takes microseconds instead of milliseconds, making gradient-based optimization feasible.

**Phase convention:**

```python
SPEED_OF_SOUND = 346100.0  # cm/s

def tanner(phase):
    """Convert phase to tangent domain (normalized admittance)."""
    return math.tan(phase * math.pi)

def untanner(x):
    """Convert from tangent domain back to phase."""
    return math.atan(x) / math.pi

def pipe_reply_phase(phase_end, length_on_wavelength):
    """Advance phase through a pipe segment: φ += 2L/λ"""
    return phase_end + length_on_wavelength * 2.0
```

**Core TMM operations:**

| Operation | Function | Purpose |
|-----------|----------|---------|
| `tanner(phase)` | `tan(π·φ)` | Convert phase to normalized admittance |
| `untanner(x)` | `atan(x)/π` | Convert admittance back to phase |
| `pipe_reply_phase(φ, L/λ)` | `φ + 2L/λ` | Phase advance through a cylindrical segment |
| `junction2_reply_phase(a0, a1, p1)` | Area-weighted admittance sum | Step change in bore diameter |
| `junction3_reply_phase(a0, a1, a2, p1, p2)` | Parallel admittance sum | Tone hole junction (bore + hole) |
| `end_flange_length_correction(od, id)` | Nederveen flange correction | Radiation end correction at bell |

**Resonance condition:** Starting from the mouthpiece end (phase = 0.5 for open, 0.0 for closed), phase is walked through all segments, steps, and holes. At the far open end, +0.5 is added. Resonance occurs when the total phase is an integer:

```python
# Open-open: 0.5 (mouth) + 2L/λ + 0.5 (bell) = n → λ = 2L/(n-1)
# Closed-open: 0.0 (reed) + 2L/λ + 0.5 (bell) = n → λ = 4L/(2n-1)
```

### 2.3 Tone Hole Physics

Tone holes are modeled via `junction3_reply_phase`, treating the hole as a parallel branch:

```python
def junction3_reply_phase(a0, a1, a2, p1, p2):
    # a0 = bore area before, a1 = bore area after, a2 = hole area
    return untanner(a1/a0 * tanner(p1) + a2/a0 * tanner(p2))
```

**Length corrections** (Keefe/Nederveen model):
- Open holes: `correction = a · (inner_correction + outer_correction)` where `inner = 1.3 - 0.9·d_hole/d_bore` and `outer = 0.7`
- Closed holes: correction = 0 (hole acts as a closed side branch)
- End flange correction (Nederveen): `a · (0.821 - 0.13 · (0.42 + w/a)^(-0.54))`

**Open vs closed tone holes:**
- **Open hole**: vents the bore, effectively shortening the instrument. The effective length below an open hole drops to near-zero for frequencies below cutoff.
- **Closed hole**: acts as a closed side branch, slightly flattening pitch (more effect closer to mouthpiece).
- **Cutoff frequency**: the frequency above which open tone holes no longer effectively vent the bore. Depends on hole geometry and spacing.

### 2.4 The n_register Concept

In the TMM phase model, open-open pipes require `n_register=2` for the fundamental. This is because the stepped-cylinder approximation introduces a phantom 1st resonance:

| n_register | Open-open (flute/sax) | Closed-open (clarinet) |
|-----------|----------------------|----------------------|
| 1 | DC (f=0) — not physical | Fundamental (1st resonance) |
| 2 | **Fundamental** | 3rd harmonic |
| 3 | 2nd harmonic (octave key) | 5th harmonic |

For saxophone 2nd register (octave key), use `n_register=3`. For clarinet 2nd register (register key), use `n_register=4`.

### 2.5 Direct vs Indirect Fingerings

| Aspect | Closed-open (Clarinet/Bordeaux) | Open-open (Sax/Flute/Ernoult) |
|--------|--------------------------------|-------------------------------|
| Fingering method | Cumulative: all lower holes + new hole open | Independent: only new hole open |
| Hole placement | Bottom-to-top (lowest note first) | Top-to-bottom (highest note first) |
| Effective bore | Closing holes extends effective length | Each hole creates independent resonator |

### 2.6 Cross-Fingering Theory

Chromatism requires cross-fingerings — patterns where not all holes below the highest open hole are open. These create complex impedance profiles and are inherently harder to tune. The current optimizer focuses on **direct fingerings** (cumulative open from one end) which follow the simplest pattern. Cross-fingerings are documented but not yet optimized.

### 2.7 Instrument-Specific Acoustics

| Instrument | Acoustic Model | Bore | closed_top | Register Key |
|-----------|---------------|------|-----------|--------------|
| **Flute** | Open-open | Cylindrical | False | Overblows octave (no key needed) |
| **Clarinet** | Closed-open | Cylindrical | True | 12th key |
| **Saxophone** | Open-open | Conical | False | Octave key |
| **Recorder** | Open-open | Conical/cylindrical | False | Overblows octave (fipple) |
| **Tin whistle** | Open-open | Cylindrical | False | Overblows octave (fipple) |
| **Chalumeau** | Closed-open | Cylindrical | True | None (single register) |

---

## 3. Optimization Methods

The optimizer in `tmm_optimizer_sequential.py` implements a multi-phase approach adapted from the Bordeaux group (Noreland, Guilloteau, Ernoult).

### 3.1 Sequential Hole Placement (Bordeaux Method)

**Phase 1 — Bore Length:** Optimize the bore length from the lowest note (all holes closed). Initial estimate from physics: `L = c/(4f)` for closed-open, `L = c/(2f)` for open-open. Refined with L-BFGS-B.

```python
# Initial estimates
if closed_top:
    L_init = SPEED_OF_SOUND / (4.0 * fundamental_freq)  # Clarinet
else:
    L_init = SPEED_OF_SOUND / (2.0 * fundamental_freq)  # Flute/sax
```

**Phase 2 — Sequential Hole Addition:** Holes are added one at a time, bottom-to-top. Each hole is positioned using L-BFGS-B with 5 random restarts to hit its target frequency.

- Closed-open instruments: existing holes CLOSED, new hole OPEN (Bordeaux cumulative method)
- Open-open instruments: only the new hole is evaluated (independent placement per Ernoult 2021)

### 3.2 Phase 2b: Differential Evolution (Breakthrough)

For open-open instruments, sequential single-hole placement creates catastrophic gaps. The fix is a **global Differential Evolution** stage that re-optimizes ALL hole positions simultaneously:

```python
result_de = differential_evolution(
    objective_function, bounds,
    x0=initial_positions + initial_diameters,
    seed=42, maxiter=100, popsize=max(10, n_holes * 2),
    mutation=(0.5, 1.0), recombination=0.7, polish=True,
)
```

**Key insight:** Overlapping bounds prevent gap formation. Each hole's bounds overlap with neighbors: `lo = i·L/(n_h·1.5+1)`, `hi = (i+2)·L/(n_h·1.5+1)`.

### 3.3 L-BFGS-B Refinement Phases

**Phase 3** applies four stages of L-BFGS-B refinement with non-crossing hole bounds:

| Stage | Variables | Description |
|-------|-----------|-------------|
| Stage 1 | 1 | Bore length only (±15%) |
| Stage 2 | n_cp | Bore radii (6 control points) |
| Stage 3 | n_h × 2 | Hole positions + diameters |
| Stage 4 | All | Simultaneous fine-tune |

### 3.4 Hole Diameter Co-Optimization

Hole diameters are co-optimized with positions in both Phase 2b DE and Phase 3 refinement. Bounds per hole: `[bore_radius × 0.4, bore_radius × 0.9]`. Adds 0.2–3 cents improvement (e.g., soprano sax improved from 0.29c to 0.03c).

### 3.5 Bore Profile Optimization

When `n_bore_cp > 0`, the bore profile is parameterized as N control points along the bore length, allowing non-uniform radius profiles. Otherwise, a uniform cylindrical bore is used.

### 3.6 Two-Register Optimization

The optimizer supports targeting any register via the `n_register` parameter. For primary register optimization, `n_register` is 1 (closed-open) or 2 (open-open). For octave key optimization, `n_register` increments by 1.

### 3.7 Cost Function

The optimizer minimizes RMS cents error with median offset correction:

```python
errors = [1200 * log2(actual / target) for each note]
offset = median(errors)
corrected_errors = errors - offset
rms = sqrt(mean(corrected_errors^2))
```

This isolates **scale evenness** from global tuning offset. A secondary `phase_cost` function (Ernoult 2020) offers a smoother alternative: it computes `sin²(π · (phase - n_register))` at target wavelengths, which is continuous even when peaks merge.

---

## 4. Key Research Findings

### 4.1 Sequential Chromatic Limit

Sequential greedy hole placement is hard-limited to ~15 cents RMS for instruments with 12+ holes. Each hole placement error compounds, and large gaps form where the TMM cannot find resonances.

### 4.2 Phase 2b DE Breakthrough

The discovery that open-open instruments were failing due to **optimizer failure, not model inaccuracy** led to the Phase 2b DE fix. Proof: xaphoon sequential holes at [101, 169, 457, 472, 487, 502] created a **288mm gap** between holes 1 and 2. TMM phase for notes F4–B4 hovered at 1.5 — halfway between resonances n=1 and n=2. No local refinement could fix this.

### 4.3 Hole Diameter Optimization

Adding hole diameter as a design variable provides 0.2–3 cents improvement. Diameters co-optimized in DE and refined in L-BFGS-B. Soprano sax improved 0.29c → 0.03c.

### 4.4 n_register Auto-Detection

The auto-detection fix: `n_register = 1 if closed_top else 2`. Previously, open-open instruments were being evaluated with the wrong register, causing systematic errors.

### 4.5 All 10 Instruments Sub-1c RMS

| Instrument | Type | RMS | Time |
|-----------|------|-----|------|
| Chalumeau C | closed-open | **0.00c** | 4.8s |
| Bass Chalumeau Bb | closed-open | **0.00c** | 14.3s |
| Soprano Sax Bb | open-open | **0.03c** | 93.9s |
| Xaphoon C | open-open | **0.00c** | 70.3s |
| Alto Sax Eb | open-open | **0.15c** | 106.2s |
| Tin Whistle D | open-open | **0.91c** | 101.6s |
| Concert Flute C | open-open | **0.00c** | — |
| Alto Flute G | open-open | **0.00c** | — |
| PVC Flute D | open-open | **0.00c** | — |
| Recorder C | open-open (conical) | **0.00c** | 178.6s |

### 4.6 Manufacturing vs Computation

Key insight from Phase 2 roadmap: manufacturing is the bottleneck, not computation. A 0.1mm bore error causes ~1–3 cents intonation error. SLA printing tolerance is ±0.05–0.1mm, so perfect computation still gets diluted by printing.

---

## 5. Instrument Library

### 5.1 Instrument Definitions (benchmark_all.py)

All instruments use a 6-8 note diatonic scale with direct (cumulative) fingerings.

| Instrument | Key | Type | Bore Radius | Outer Dia | Hole Dia | Holes | Notes |
|-----------|-----|------|------------|-----------|---------|-------|-------|
| **Chalumeau** | C | closed-open | 7.25mm | 22mm | 7.0mm | 6 | C4–A4 |
| **Bass Chalumeau** | Bb | closed-open | 9.5mm | 28mm | 8.0mm | 8 | Bb2–Bb3 |
| **Soprano Sax** | Bb | open-open | 6.0mm | 20mm | 6.5mm | 7 | Bb4–A5 |
| **Xaphoon** | C | open-open | 7.0mm | 20mm | 6.5mm | 7 | C4–B4 |
| **Alto Sax** | Eb | open-open | 8.5mm | 26mm | 7.5mm | 7 | Eb4–D5 |
| **Tin Whistle** | D | open-open | 6.5mm | 16mm | 4.5mm | 6 | D5–C#6 |
| **Concert Flute** | C | open-open | 9.5mm | 16mm | 8.0mm | 6 | C4–B4 |
| **Alto Flute** | G | open-open | 11.0mm | 18mm | 9.0mm | 6 | G3–F#4 |
| **PVC Flute** | D | open-open | 10.2mm | 14mm | 8.0mm | 6 | D4–C#5 |
| **Recorder** | C | open-open | 5.5mm | 14mm | 4.0mm | 7 | C5–C6 |

### 5.2 Fingering Convention

Hole array indexing: `[hole_0, hole_1, ..., hole_n]` where `hole_0` is closest to the mouthpiece and `hole_n` is closest to the bell.

```python
# 6-hole saxophone, cumulative fingerings
fingerings = [
    ["closed"] * 6,                                    # Lowest note
    ["open", "closed", "closed", "closed", "closed", "closed"],
    ["open", "open", "closed", "closed", "closed", "closed"],
    ...
    ["open", "open", "open", "open", "open", "closed"],  # Highest note
]
```

### 5.3 Preset Library (target_frequencies.py)

`INSTRUMENT_TYPES` categorizes 25+ instruments into open-open or closed-open acoustic models, including flutes, whistles, recorders, clarinets, shawms, saxophones, and brass instruments. `PRESET_TARGETS` provides metadata (note range, description) for quick reference.

---

## 6. AI Integration

### 6.1 AI Advisor (ai_advisor.py)

The rule-based advisor analyzes optimization results and produces actionable suggestions. It scores results A–F based on RMS accuracy and checks for:

- **Systematic pitch offset** (all notes sharp/flat → bore length issue)
- **Individual outliers** (notes >2× average error → local geometry problem)
- **Uneven hole spacing** (gap ratio >3× → register breaks)
- **Hole clustering** (min gap <15mm → printability issue)
- **Diameter variation** (range >3mm → manufacturing complexity)
- **Bore monotonicity** (non-monotonic → requires constraint)
- **Evaluation count** (<200 evals → need more iterations)

```python
# Example usage
from backend.ai_advisor import analyze_sequential_result
advice = analyze_sequential_result(optimizer_result, target_frequencies)
print(f"Score: {advice.score}/100 (Grade {advice.grade})")
for s in advice.suggestions:
    print(f"[{s.priority}] {s.title}: {s.action}")
```

**Design Memory:** Uses SQLite (`design_memory.db`) to store and compare designs across runs. `store_design()` saves results; `get_best_design()` retrieves the best-known design for comparison.

**LLM Mode:** Falls back to Ollama or OpenRouter for natural language suggestions when available:

```python
advice = get_llm_suggestion(optimizer_result, target_frequencies, model="llama3.2")
```

### 6.2 AI Assistant (ai_assistant.py)

A hybrid AI assistant supporting multiple free model tiers via OpenRouter:

| Role | Model | Context | Speed |
|------|-------|---------|-------|
| Fast | `openai/gpt-oss-20b:free` | — | ~5s |
| Research | `cohere/north-mini-code:free` | 256K | ~10–50s |
| Deep | `nvidia/nemotron-nano-9b-v2:free` | — | ~20s+ |

```python
from backend.ai_assistant import get_researcher, get_coder, prepare_research_prompt

researcher = get_researcher()
finding = researcher.ask("How does bell flare compress harmonics?")

coder = get_coder()
code = coder.generate_code("Write a trumpet impedance evaluator")

# For ChatGPT/Claude web interfaces:
prompt = prepare_research_prompt("trumpet valve physics", context_file="trumpet_openwind.py")
```

The assistant also supports `analyze_code()`, `debug_error()`, `research_topic()`, and `save_session_log()` for logging research sessions for laptop-to-desktop handoff.

### 6.3 How to Use

```powershell
# Set API key
$env:OPENROUTER_API_KEY = "your-key-here"

# Run AI analysis on an optimization result
python -c "
from backend.tmm_optimizer_sequential import SequentialBoreOptimizer
from backend.ai_advisor import analyze_sequential_result

seq = SequentialBoreOptimizer(targets, fingerings)
result = seq.run()
advice = analyze_sequential_result(result, targets)
print(advice.analysis)
"
```

---

## 7. Code Architecture

```
C:\instrument-designer\
├── backend\                          # Python optimization & AI
│   ├── tmm_acoustics.py             # Core TMM engine (Profile, Hole, TMMInstrument)
│   ├── tmm_optimizer_sequential.py  # Sequential + DE + L-BFGS-B optimizer
│   ├── benchmark_all.py             # Full benchmark suite (10 instruments)
│   ├── ai_advisor.py                # Rule-based + LLM design advisor
│   ├── ai_assistant.py              # AI coding/research assistant
│   ├── target_frequencies.py        # Instrument presets & frequency generation
│   ├── bore_optimizer.py            # NSGA-II + PAVA optimizer (legacy)
│   ├── mp_cache.py                  # SQLite shared cache for parallel workers
│   ├── design_server.py             # FastAPI server (woodwind_designer)
│   ├── lan_chat.py                  # LAN chat for machine coordination
│   └── validate_optimizer.py        # Benchmark script
├── woodwind_designer\               # Main Python package
│   ├── engine\
│   │   ├── design_server.py         # FastAPI server
│   │   ├── demakein_wrapper.py      # Demakein integration
│   │   └── instrument_library.py    # Instrument data
│   └── gui\                         # PySide6 desktop GUI
├── web\                             # React + TypeScript frontend
│   ├── src\
│   │   ├── components\             # React components
│   │   ├── data\                   # Instrument metadata
│   │   └── utils\                  # API client, filters
│   └── src-tauri\                   # Tauri Rust backend
├── research\                        # Research docs & instrument measurements
│   ├── instrument-measurements.md  # 700+ lines of measured dimensions
│   └── saxophone\                  # Saxophone-specific research (7 docs)
├── chat-logs\                       # Session logs (40+ files)
├── chalumier\                       # Kotlin TMM reference implementation
├── config\                          # JSON configurations (empty)
└── design_memory.db                 # SQLite design memory database
```

### 7.1 Core TMM Engine (`tmm_acoustics.py`)

| Class/Function | Purpose |
|---------------|---------|
| `Profile` | Stepped bore representation with interpolation |
| `Hole` | Tone hole state (OPEN/CLOSED) |
| `TMMInstrument` | Full instrument model — constructs action chain, computes resonances |
| `tmm_instrument_from_radii()` | Factory: creates TMMInstrument from radius array |
| `circle_area`, `tanner`, `untanner` | Core math primitives |
| `pipe_reply_phase`, `junction2_reply_phase`, `junction3_reply_phase` | TMM phase operations |
| `end_flange_length_correction`, `hole_length_correction` | Acoustic length corrections |

### 7.2 Sequential Optimizer (`tmm_optimizer_sequential.py`)

| Phase | Method | Variables | Description |
|-------|--------|-----------|-------------|
| Phase 1 | L-BFGS-B | 1 (bore length) | Fundamental pitch match |
| Phase 2 | L-BFGS-B | 1 per hole | Sequential hole placement |
| Phase 2b | DE | 2×n_h (positions + diameters) | Global re-optimization |
| Phase 3 S1 | L-BFGS-B | 1 | Bore length refinement |
| Phase 3 S2 | L-BFGS-B | n_cp | Bore radii refinement |
| Phase 3 S3 | L-BFGS-B | 2×n_h | Hole positions + diameters |
| Phase 3 S4 | L-BFGS-B | All | Simultaneous fine-tune |

### 7.3 Benchmark (`benchmark_all.py`)

Benchmarks all 10 instruments through two pipelines:
- **Sequential**: Phase 1 + Phase 2 only
- **Seq+Refine**: Phase 1 + Phase 2 + Phase 2b DE + Phase 3 L-BFGS-B

Generates a summary table comparing RMS and wall time across all instruments.

---

## 8. Tooling & Languages

| Tool | Purpose | Version |
|------|---------|---------|
| **Python** | Backend (TMM, optimization, AI, server) | 3.12 |
| **PowerShell** | Scripting, build automation | 5.1+ |
| **Git** | Version control | Latest |
| **Tailscale** | LAN communication between laptop/desktop | Latest |
| **OpenRouter** | Free AI model API access | — |
| **FastAPI** | Backend HTTP server | — |
| **Uvicorn** | ASGI server | — |
| **scipy** | DE + L-BFGS-B + Powell optimization | — |
| **numpy** | Array operations, FFT | — |

**Frontend (separate branch):** React 19 + TypeScript + Tailwind CSS + Three.js + Tauri v2 (Rust)

---

## 9. Physics References

### Primary Sources

| Reference | Topic | Key Finding |
|-----------|-------|-------------|
| Lefebvre (2011) | Saxophone bore shape | Straight cone NOT appropriate; deviations needed for harmonicity |
| Lafebvre PhD (2010) | Computational woodwind design | ±5 cents target; TMMI mutual radiation formulas |
| Szwarcberg (2025) | Geometric sensitivity | 0.1mm radius change → ~3.4c; chimney +1mm → ~4c |
| Keefe (1982) | Tone hole theory | Length correction formulas for open/closed holes |
| Nederveen (1969/1998) | Woodwind acoustics | Cutoff frequency, end corrections, radiation impedance |
| Benade (1976) | Fundamentals of musical acoustics | Woodwind bore design principles |
| Boehm (1871) | The Flute and Flute Playing | Modern flute scale and tone hole geometry |
| Ernoult (2020/2021) | Phase-based cost function | Smooth, differentiable cost using `sin²(π·deviation)` |
| Noreland (2013) | Logical clarinet | 0.49 cents RMS via gradient optimization |
| Debut-Kergomard-Laloë (2005) | TMM for woodwinds | Transfer matrix formalism for stepped bores |
| Dalmont et al. | Radiation impedance | End corrections for flanged/unflanged pipes |

### Research Labs

| Lab | Institution | Focus |
|-----|-------------|-------|
| CAML | McGill University | Physical modeling, instrument measurement |
| CCRMA | Stanford University | Digital waveguides, audio processing |
| IRCAM/INRIA | France | OpenWind, heritage digitization |
| NESS | University of Edinburgh | Physical modeling synthesis |
| Aalto Acoustics | Finland | FEM for musical instruments |

### Key Acoustic Constants

```python
SPEED_OF_SOUND = 346100.0  # cm/s (matches chalumier)
A4 = 440.0                  # Standard pitch reference
```

### Sensitivity Coefficients

| Parameter Change | Effect | Source |
|-----------------|--------|--------|
| 10% hole diameter reduction | ~10 cents flat | Postma |
| +1mm chimney height (register hole) | ~4 cents improvement | Szwarcberg 2025 |
| -0.1mm register hole radius | ~3.4 cents improvement | Szwarcberg 2025 |
| 0.1mm bore error | ~1–3 cents | Internal |
| +6mm chimney (tenor sax) | 20–50% diameter compensation needed | DAGA 2021 |

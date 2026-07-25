# ChatGPT / Claude Deep Research Prompts
# Ready to paste into chatgpt.com or claude.ai

---

## PROMPT 1: Woodwind Acoustic Modeling — Deep Dive

```
I'm building a 3D-printed wind instrument designer that optimizes bore geometry and tone hole placement for intonation accuracy (<3 cents RMS). I need your help understanding the complete acoustic modeling pipeline.

BACKGROUND:
- We have a working Transfer Matrix Method (TMM) engine ported from chalumier (Kotlin/Demakein)
- We have OpenWInD (Inria) FEM solver integrated as a plugin
- We have Keefe 1984 viscothermal loss model integrated
- Our TMM gives 71.0 Hz for a 1200mm cylinder, OpenWInD gives 70.8 Hz (0.3% agreement)
- Our optimizer achieves <1c RMS on the TMM model, but this is self-evaluation (simplified model)

WHAT I NEED YOU TO RESEARCH:

1. **TMM Limitations**: What does our TMM model miss that affects real-world accuracy?
   - Tone hole mutual interactions (TMMI) — Lefebvre 2013
   - Frequency-dependent losses beyond Keefe's model
   - Nonlinear effects (reed coupling, flow separation)
   - Manufacturing tolerances

2. **Validation Strategy**: How should we validate our TMM against real instruments?
   - We have access to Wolfe/UNSW impedance measurements for baroque flute
   - Should we compare impedance spectra peak-by-peak, or use the full curve?
   - What metric should we use for impedance comparison?

3. **From Impedance to Sound**: How do we go from impedance peaks to actual sound quality?
   - Spectral envelope from impedance peaks
   - Reed excitation model (linear vs nonlinear)
   - How does playing dynamics affect which resonances are excited?

4. **Sound Synthesis Pipeline**: Given optimized bore geometry, how do we generate the sound?
   - Digital waveguide approach (Smith)
   - Modal synthesis approach
   - Which is better for real-time preview?

5. **Timbre Modeling**: How do we quantify and optimize for timbre?
   - Spectral centroid, spectral flatness, harmonic-to-noise ratio
   - MFCCs for instrument timbre
   - Formant analysis for woodwinds
   - What makes a "good" woodwind sound vs a "bad" one?

Please provide specific formulas, algorithms, and implementation guidance. I need actionable technical details, not general overviews.
```

---

## PROMPT 2: Multi-Objective Instrument Optimization

```
I'm optimizing 3D-printed woodwind instruments and need to go beyond pure intonation. Professional instrument makers routinely compromise intonation for timbre, playability, and response. I need to model these trade-offs.

RESEARCH QUESTIONS:

1. **Mode Alignment (Benade's Criterion)**:
   - Benade showed that 2nd mode must be within 5 cents of 3rd harmonic for good tone
   - How do I compute mode alignment from impedance peaks?
   - What's the relationship between mode alignment and spectral quality?
   - How does mode alignment change with playing dynamics?

2. **Cutoff Frequency and Timbre**:
   - The open tone hole lattice has a cutoff frequency fc
   - Frequencies below fc: dark timbre, cross-fingering dependent
   - Frequencies above fc: bright, projecting
   - How do I compute fc from hole geometry?
   - How do I optimize for consistent fc across fingerings?

3. **Peak Amplitude Ratios**:
   - The ratio of 2nd impedance peak to 1st (a2/a1) controls register switching
   - Too high: instrument overblows too easily
   - Too low: hard to overblow
   - What are the target ranges for different instrument types?
   - How do I extract peak amplitudes from impedance curves?

4. **Resistance Profile**:
   - Resistance = back pressure felt by player
   - Related to tone hole sizes, bore geometry, reed/mouthpiece
   - How do I estimate resistance from geometry?
   - What's the relationship between resistance and playability?

5. **Dynamic Range**:
   - Distance between oscillation threshold and extinction threshold
   - Related to radiation losses vs reed nonlinearity
   - How do I estimate dynamic range from linear acoustics?

6. **Multi-Objective Optimization Algorithms**:
   - Pareto front between intonation and timbre objectives
   - NSGA-II vs MADS vs weighted sum
   - How to define "good" when objectives conflict
   - What are realistic target ranges for each objective?

Please provide specific formulas and implementation guidance.
```

---

## PROMPT 3: Baroque Flute Acoustic Validation

```
I'm validating a TMM (Transfer Matrix Method) woodwind instrument model against real measurement data from the Wolfe/UNSW database.

DATASET:
- Baroque flute bore profiles (cylindrical head + conical body)
- 6 finger holes + D# key with measured positions and diameters
- Measured input impedance |Z(f)| and arg(Z(f)) for every fingering
- Sound recordings (WAV) for every note played by Geoffrey Collins

VALIDATION PLAN:
1. Build TMM model from measured bore profile + hole geometry
2. Compute predicted impedance spectra
3. Compare with measured impedance:
   - Peak frequency alignment (cents error for each resonance)
   - Peak amplitude agreement (dB error)
   - Anti-resonance alignment
   - Overall curve shape (correlation coefficient?)

QUESTIONS:
1. What's the expected accuracy of a good TMM model vs measurements?
   - How close should peak frequencies be? (1c? 5c? 20c?)
   - How close should peak amplitudes be? (1dB? 3dB?)

2. What errors should I expect from:
   - Bore profile discretization (stepped cylinder approximation)
   - Tone hole parameterization (Keefe lumped circuit vs Lefebvre FEM)
   - Loss model accuracy (Keefe 1984 vs measured)
   - End correction approximations

3. How do I handle the partially conical bore?
   - Baroque flute has cylindrical head + conical body
   - Should I use the exact conical TMM (Legendre functions) or approximate with stepped cylinders?
   - What's the error from approximation?

4. How do I compare impedance peaks systematically?
   - Should I track individual resonance branches across fingerings?
   - Or compare the "envelope" of all peaks?
   - What's the right metric?

5. Once the model is validated, how do I use it to replicate the instrument?
   - Start from bore profile, optimize hole positions/diameters
   - Or start from target frequencies, optimize everything simultaneously
   - What optimization strategy works best for this?

Please provide specific implementation guidance with expected accuracy bounds.
```

---

## PROMPT 4: Sound-to-Instrument Inverse Problem

```
I want to go from recorded sound samples of a woodwind instrument to the instrument's physical parameters (bore profile, hole positions/diameters). This is an inverse problem.

FORWARD MODEL (we have this):
  Bore geometry + holes → TMM impedance → resonance peaks → (with excitation model) → sound

INVERSE PROBLEM (we want):
  Recorded sound → Spectral analysis → Target impedance peaks → Bore geometry + holes

RESEARCH QUESTIONS:

1. **Source-Filter Decomposition**:
   - How do I separate the excitation (reed/lip) from the filter (bore)?
   - Cepstral analysis? All-pole modeling? Iterative approach?
   - What's the standard method for woodwind source-filter separation?

2. **From Sound Spectrum to Impedance Peaks**:
   - The sound spectrum is shaped by impedance peaks
   - But the excitation spectrum also matters (harmonic content of reed vibration)
   - Can I extract impedance peak locations from the sound spectrum alone?
   - What information is lost in the source-filter convolution?

3. **From Impedance Peaks to Bore Geometry**:
   - Given target resonance frequencies for all fingerings
   - Find bore profile + hole geometry that produces these resonances
   - This is the "bore reconstruction" problem (Ernoult 2021, FWI)
   - Can I solve it without adjoint gradients? (e.g., evolutionary algorithm)

4. **Practical Implementation**:
   - I have WAV recordings of all notes from a baroque flute
   - I want to extract the bore profile that produces these sounds
   - What's the step-by-step pipeline?
   - What FFT/hop size/window should I use for spectral analysis?

5. **Timbre Matching**:
   - Beyond just pitch, how do I match the timbre?
   - Spectral envelope comparison
   - MFCC-based distance metric
   - Harmonic structure matching
   - How do I define "sounds like the same instrument"?

6. **Validation**:
   - Once I find bore geometry from sound, how do I verify it's correct?
   - Compare predicted impedance with measured impedance?
   - Compare predicted sound with original recording?
   - What's a realistic accuracy bound?

Please provide a practical implementation plan with specific algorithms and parameters.
```

---

## PROMPT 5: GitHub Repository Analysis

```
Analyze these GitHub repositories for woodwind instrument modeling and identify which ones have the most useful code/algorithms I can learn from or adapt:

CRITICAL:
1. https://gitlab.inria.fr/openwind/openwind — OpenWInD (Inria), TMM + FEM + optimization
2. https://github.com/edwardkort/WWIDesigner — WIDesigner, TMM + BOBYQA + DIRECT
3. https://github.com/pfh/demakein — demakein, design → 3D print pipeline
4. https://github.com/MarkChuCarroll/chalumier — chalumier, Kotlin TMM engine

HIGH PRIORITY:
5. https://github.com/Edinburgh-Acoustics-and-Audio-Group/ness — NESS, FDTD physical modeling
6. https://github.com/garyscavone/acmt — Air Column Modeling Toolkit, TMM + DWG
7. https://github.com/magenta/ddsp — DDSP, differentiable DSP

For each repo, I need:
- What's the core algorithm and how is it implemented?
- What are the key files/modules I should study?
- What can I adapt vs what must I reimplement?
- What are the limitations I should be aware of?
- Are there test cases or example instruments I can validate against?

Focus on the ACOUSTIC MODELING parts, not the UI or file I/O. I want to understand the math and algorithms.
```

---

## PROMPT 6: Spectral Analysis for Instrument Comparison

```
I need to compare the sound of two woodwind instruments (one measured, one computed) to determine how well my simulation matches reality.

WHAT I HAVE:
- WAV recording of each note from a real baroque flute (Geoffrey Collins, Wolfe/UNSW database)
- I can compute WAV from my TMM model + digital waveguide synthesis

ANALYSIS I NEED:

1. **Spectral Envelope Comparison**:
   - How to extract spectral envelope from both signals
   - How to compare envelopes (cosine similarity? DTW? MFCC distance?)
   - What tolerance is "good enough"?

2. **Harmonic Structure Analysis**:
   - Harmonic-to-noise ratio (HNR)
   - Odd/even harmonic ratio (important for clarinet vs flute)
   - Spectral centroid, spectral bandwidth, spectral rolloff
   - How these correlate with perceived quality

3. **Temporal Analysis**:
   - Attack transient comparison
   - Steady-state stability
   - Vibrato characteristics
   - How to compare temporal envelopes

4. **Perceptual Metrics**:
   - Mel-frequency cepstral coefficients (MFCC) distance
   - Chroma features
   - Spectral flux
   - Which metric best captures "sounds like the same instrument"?

5. **Python Implementation**:
   - What libraries to use (librosa, scipy.signal, acoustics)?
   - Recommended FFT parameters for woodwind analysis (window size, overlap, window function)
   - Standard preprocessing (pre-emphasis, normalization)

6. **Validation Thresholds**:
   - What MFCC distance is "the same instrument"?
   - What spectral correlation is "close enough"?
   - Are there established benchmarks in the literature?

Please provide specific Python code snippets and parameter recommendations.
```

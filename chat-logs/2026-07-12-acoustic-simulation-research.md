# Acoustic Simulation, Frequency Analysis & Measurement Research

**Date:** 2026-07-12  
**Goal:** Research acoustic simulation capabilities, frequency representation, analytics tools, and find a way to let users compare predicted sound (frequency analysis) with measured sound from physical instruments.

---

## 1. What OpenWInD Provides

### Frequency Domain: Input Impedance
OpenWInD computes the **acoustic input impedance** Z(f) of a wind instrument — the ratio of acoustic pressure to volume flow at the mouthpiece entrance, as a function of frequency.

**Key physics:**
- **Flutes** operate at **minima** of Z (low pressure, high flow at embouchure)
- **Reed instruments** (clarinet, saxophone, shawm) operate at **maxima** of Z (high pressure, low flow at reed)
- **Resonance peaks** in the impedance curve correspond to the **playable notes** of the instrument
- Peak height and width indicate **ease of playing** and **note stability**
- Harmonic alignment of peaks (f, 2f, 3f, 4f...) determines **timbre richness**

**What we get from OpenWInD:**
- Complex impedance Z(f) = Re(Z) + j·Im(Z) across frequency range
- |Z| magnitude peaks = predicted resonance frequencies
- Can compute for any bore profile + tone hole configuration
- Pre-computed data available for 6 presets (50-3000 Hz, 2 Hz resolution)

### Time Domain: Sound Simulation
OpenWInD's second module computes **actual sound** by coupling a nonlinear oscillator (reed or lips) to the pipe:
- Uses finite differences in time domain
- Energy-consistent discretization
- Nonlinear ODE for oscillator + linear PDE for pipe propagation
- Accounts for visco-thermal losses
- Produces time-domain waveform → can be FFT'd to get frequency spectrum

**This is the bridge between predicted and measured:** OpenWInD can generate a simulated sound waveform, which can be compared directly with a microphone recording of the physical instrument.

### Geometry Optimization
OpenWInD can also **reconstruct bore geometry from measured impedance** — useful for inverse design.

---

## 2. Acoustic Impedance Measurement Methods

### Two-Microphone Transfer Function Method (TMTF)
The standard method for measuring acoustic impedance of wind instruments (Gibiat & Laloë, 1990):
- Cylindrical measurement cavity with 2+ microphones
- Loudspeaker emits chirps (broadband excitation)
- FFT of microphone signals → transfer function → impedance
- Three-calibration technique corrects for systematic errors
- High dynamic range needed for high-Q resonances

**Equipment needed:**
- 2+ calibrated microphones
- Speaker/exciter (piezo buzzer works for narrow-bore instruments)
- Audio interface (e.g., RME, Focusrite)
- MATLAB/Python for signal processing

### Four-Microphone Four-Calibration (FMFC)
For narrow-bore instruments (oboes, bassoons) where standard probes don't fit:
- 4 microphones in a 4mm diameter tube
- Better accuracy at broader frequency ranges
- Custom adapter needed for instrument coupling

### Practical DIY Approach
For our project, a simpler approach is sufficient:
- **Single microphone** captures played sound
- **FFT** extracts frequency spectrum
- Compare played frequencies with predicted impedance peaks
- No need for absolute impedance measurement — relative comparison is enough

---

## 3. Frequency Analysis Tools & Software

### Browser-Based (Web Audio API)
| Tool | Description | Key Features |
|------|-------------|--------------|
| **Web Audio API AnalyserNode** | Built into all browsers | Real-time FFT, configurable fftSize (512-16384), getByteFrequencyData() |
| **audioMotion-analyzer** | High-res spectrum analyzer library | Log/linear/Mel/Bark scales, 240 bands, A/B/C weighting, ~30kB |
| **WebAudioSpectrum** | Open-source spectrum analyzer | Oscilloscope, frequency spectrum, spectrogram |
| **Swar** | Real-time pitch detector | HPS algorithm, note display, cents deviation |
| **Note & Chord Detector** | McLeod Pitch Method | Live pitch + chord detection, MIDI export |

**Best for our project:** Web Audio API AnalyserNode — zero dependencies, works in-browser, configurable FFT size.

### Python Libraries
| Library | Description | Key Features |
|---------|-------------|--------------|
| **librosa** (8.5k stars) | Audio/music analysis | STFT, MFCC, chroma, harmonic separation, pitch tracking |
| **scipy.signal** | Core DSP primitives | FFT, filtering, spectral estimation, windowing |
| **numpy** | Numerical computing | FFT, array operations, peak finding |
| **aubio** | Audio labeling | Onset detection, pitch tracking, beat tracking |

**Best for backend:** librosa + scipy — industry standard, well-documented.

### Desktop Software
| Software | Price | Platform | Key Features |
|----------|-------|----------|--------------|
| **Smaart v9** | $895 | Win/Mac | Dual-channel FFT transfer function, real-time alignment |
| **ARTA** | Free | Windows | Sweep recording, impulse/frequency response, impedance measurement |
| **REW (Room EQ Wizard)** | Free | Win/Mac/Linux | Waterfall, spectrogram, RT60, impedance, IIR EQ generation |
| **FuzzMeasure** | $199 | macOS | Room acoustics, transfer function |
| **NI LabVIEW SVT** | $$ | Win | Industrial-grade sound & vibration analysis |

**Best free option:** REW — can measure impedance, export frequency response as CSV for comparison.

---

## 4. Pitch Detection Algorithms

### Harmonic Product Spectrum (HPS)
- Downsample FFT spectrum by 2x, 3x, 4x...
- Multiply element-wise — fundamental frequency peaks align
- Robust against noise and overtones
- Works well for harmonic instruments (flutes, recorders)
- Less effective for instruments with weak harmonics

### Autocorrelation
- Compare signal with time-shifted version of itself
- Lag at maximum correlation = fundamental period
- More robust than FFT peak detection for noisy signals
- Computationally heavier than HPS

### YIN Algorithm
- Refined autocorrelation with cumulative mean normalization
- Reduces octave errors
- Industry standard for pitch detection

### McLeod Pitch Method
- Normalized square difference function (NSDF)
- Used by many browser-based pitch detectors
- Good for real-time applications

**Best for our project:** HPS for frequency analysis comparison (simple, effective for harmonic instruments), YIN/McLeod for real-time pitch display.

---

## 5. Predicted vs Measured Comparison Framework

### What We Can Compare

| Predicted (OpenWInD) | Measured (Microphone) | Comparison Method |
|---------------------|----------------------|-------------------|
| Impedance peak frequencies | Fundamental frequency of played notes | Frequency alignment (Hz or cents deviation) |
| Peak amplitudes (relative) | Harmonic amplitudes in FFT | Spectral envelope comparison |
| Peak widths (Q factor) | Note sustain/stability | Subjective + envelope analysis |
| Harmonic structure prediction | Measured harmonic spectrum | Harmonic amplitude ratios |
| Time-domain simulated sound | Recorded played sound | Waveform/spectrogram overlay |

### Implementation Approach

#### Phase 1: Frequency Comparison (Simple)
1. Extract impedance peaks from OpenWInD data (already have peak finder)
2. User records/plays notes via microphone
3. Browser FFT extracts fundamental frequency
4. Display: "Predicted: 523 Hz (C5) | Measured: 520 Hz | Deviation: -10 cents"
5. Show impedance curve with measured frequency overlaid

#### Phase 2: Spectral Comparison (Advanced)
1. OpenWInD generates simulated sound waveform (time-domain module)
2. User uploads or records played sound
3. Both signals FFT'd → frequency spectra compared
4. Visual: overlay predicted vs measured spectral envelopes
5. Quantitative: spectral similarity score (cosine similarity, etc.)

#### Phase 3: Impedance Measurement (Expert)
1. User builds DIY impedance probe (2-microphone setup)
2. Measures actual impedance of physical instrument
3. Uploads measurement data (CSV)
4. Direct comparison: measured Z(f) vs predicted Z(f)
5. Residual analysis shows where design differs from reality

### Data Flow

```
┌─────────────────────────────────────────────────────────┐
│                    PREDICTION PATH                       │
│                                                          │
│  Bore Profile + Tone Holes                               │
│       │                                                  │
│       ▼                                                  │
│  OpenWInD ImpedanceComputation                           │
│       │                                                  │
│       ├──→ Impedance Z(f) ──→ Peak Detection ──→ Notes   │
│       │                                                  │
│       └──→ Sound Simulation ──→ Waveform ──→ FFT         │
│                                                          │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                    ┌──────────┐
                    │ COMPARE  │
                    └──────────┘
                          ▲
                          │
┌─────────────────────────────────────────────────────────┐
│                    MEASUREMENT PATH                      │
│                                                          │
│  Microphone Input                                        │
│       │                                                  │
│       ▼                                                  │
│  Web Audio API AnalyserNode                              │
│       │                                                  │
│       ├──→ FFT Spectrum ──→ Peak Detection ──→ Notes     │
│       │                                                  │
│       └──→ Recorded Waveform ──→ FFT ──→ Spectrum        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 6. Browser-Based Measurement Implementation

### Microphone Capture
```javascript
// Request microphone access
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const audioCtx = new AudioContext();
const source = audioCtx.createMediaStreamSource(stream);

// Create analyser with high FFT resolution
const analyser = audioCtx.createAnalyser();
analyser.fftSize = 8192; // 4096 frequency bins
analyser.smoothingTimeConstant = 0.8;

source.connect(analyser);
```

### FFT Extraction
```javascript
const bufferLength = analyser.frequencyBinCount;
const dataArray = new Float32Array(bufferLength);

// Get frequency domain data
analyser.getFloatFrequencyData(dataArray);

// Find peaks (resonance frequencies)
const peaks = [];
for (let i = 1; i < bufferLength - 1; i++) {
    if (dataArray[i] > dataArray[i-1] && dataArray[i] > dataArray[i+1]) {
        if (dataArray[i] > -40) { // threshold
            const freq = i * audioCtx.sampleRate / analyser.fftSize;
            peaks.push({ frequency: freq, magnitude: dataArray[i] });
        }
    }
}
```

### Note Detection (HPS)
```javascript
// Harmonic Product Spectrum for pitch detection
function harmonicProductSpectrum(spectrum, sampleRate, numHarmonics = 5) {
    let hps = new Float32Array(spectrum);
    
    for (let n = 2; n <= numHarmonics; n++) {
        const downsampled = new Float32Array(Math.floor(spectrum.length / n));
        for (let i = 0; i < downsampled.length; i++) {
            downsampled[i] = spectrum[i * n];
        }
        for (let i = 0; i < downsampled.length; i++) {
            hps[i] *= downsampled[i];
        }
    }
    
    // Find peak
    let maxIdx = 0;
    for (let i = 1; i < hps.length; i++) {
        if (hps[i] > hps[maxIdx]) maxIdx = i;
    }
    
    return maxIdx * sampleRate / spectrum.length;
}
```

### Frequency-to-Note Conversion
```javascript
function freqToNote(freq) {
    const A4 = 440.0;
    const noteNames = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
    
    const semitones = 12 * Math.log2(freq / A4);
    const noteNum = Math.round(semitones) + 69; // MIDI note number
    const noteName = noteNames[noteNum % 12];
    const octave = Math.floor(noteNum / 12) - 1;
    const cents = Math.round((semitones - Math.round(semitones)) * 100);
    
    return { note: noteName, octave, cents, midi: noteNum };
}
```

---

## 7. Software Recommendations for Our Project

### For Browser (Frontend)
| Need | Solution | Why |
|------|----------|-----|
| Real-time FFT | Web Audio API AnalyserNode | Zero dependencies, built-in |
| Spectrum display | Canvas 2D (custom component) | Full control, matches existing ImpedancePlot |
| Pitch detection | HPS algorithm (custom) | Simple, effective for harmonic instruments |
| Spectrogram | Canvas 2D with scrolling | Visualize frequency over time |
| File upload | Web Audio API decodeAudioData | Supports WAV, MP3, FLAC, OGG |

### For Backend (Python)
| Need | Solution | Why |
|------|----------|-----|
| Audio file analysis | librosa | Industry standard, rich features |
| FFT/scipy | scipy.signal | Core DSP primitives |
| Impedance peak finding | numpy (existing code) | Already implemented |
| Sound simulation | OpenWInD time-domain module | Can generate predicted sound |
| CSV import/export | pandas/numpy | For impedance measurement data |

### For Expert Users
| Need | Solution | Why |
|------|----------|-----|
| Impedance measurement | ARTA (free) or DIY probe | Professional-grade measurement |
| Frequency response export | REW (free) | CSV/text export of measured data |
| Impedance comparison | Custom Python script | Align and compare Z(f) curves |

---

## 8. Key Academic References

1. **Gibiat & Laloë (1990)** — "Acoustical impedance measurements by the two-microphone-three-calibration (TMTC) method" — JASA 88(6):2533-2545
   - Foundation of modern impedance measurement

2. **Dickens, Smith & Wolfe (2007)** — "Improved precision in measurements of acoustic impedance spectra using resonance-free calibration loads"
   - Review of measurement techniques

3. **Wolfe (2018)** — "The Acoustics of Woodwind Musical Instruments" — Acoustics Today
   - Comprehensive overview of woodwind acoustics, impedance spectra, and their relationship to played sound

4. **Eveno et al. (2012)** — Measured impedance of 45 serpents from Musée de la Musique collection
   - Non-invasive characterization of historical instruments

5. **Bowen et al.** — Validated that bore geometry alone can predict pitch, intonation, and timbre
   - Cross-checked computed impedance against measured impedance and playing tests

6. **Chabassier & Ernoult (2020)** — "The Virtual Workshop OpenWinD" — HAL hal-02984478
   - Full description of OpenWInD's three modules: impedance, sound simulation, geometry optimization

7. **Lefebvre & Scavone (2013)** — "Input impedance measurements of conical acoustic systems"
   - Comparison of two-microphone and impedance tube methods

8. **Middleton (2003)** — "Pitch Detection Algorithms" — CNX
   - Foundational HPS algorithm description

9. **McLeod (2005)** — "A Precise Pitch Determination Algorithm" — U. Waikato
   - McLeod Pitch Method used by many browser detectors

10. **NEMUS Project** — Digital revival of historical instruments via acoustic simulation
    - Combined geometric measurement + acoustic simulation for museum specimens

---

## 9. Proposed Implementation Roadmap

### Phase 1: Basic Comparison (Week 1-2)
- [ ] Add microphone capture to browser (Web Audio API)
- [ ] Implement real-time FFT spectrum display
- [ ] Add HPS pitch detection
- [ ] Display detected frequency alongside predicted impedance peaks
- [ ] Show cents deviation from predicted note

### Phase 2: Recording & Analysis (Week 3-4)
- [ ] Add audio recording capability (MediaRecorder API)
- [ ] Save recorded audio as WAV
- [ ] Backend endpoint: analyze uploaded audio (librosa)
- [ ] Extract harmonic spectrum from recording
- [ ] Compare harmonic amplitudes with predicted impedance structure

### Phase 3: OpenWInD Sound Simulation (Week 5-6)
- [ ] Backend endpoint: generate predicted sound waveform (OpenWInD time-domain)
- [ ] Export predicted waveform as WAV
- [ ] Frontend: overlay predicted vs measured spectrograms
- [ ] Quantitative comparison metrics

### Phase 4: Impedance Measurement Import (Week 7-8)
- [ ] Support CSV import of measured impedance data
- [ ] Frontend: overlay measured vs predicted Z(f) curves
- [ ] Residual analysis and visualization
- [ ] Guide for building DIY impedance probe

---

## 10. Existing Code to Leverage

| Component | File | Reuse |
|-----------|------|-------|
| Impedance peak finder | `openwind_wrapper.py:122-129` | `_find_peaks()` — finds local maxima in |Z| |
| Frequency-to-note | `openwind_wrapper.py:131-139` | `_freq_to_note()` — Hz → note name + cents |
| Sound synthesizer | `sound_synthesizer.py` | `synthesize_from_peaks()` — peaks → audio |
| Impedance plot | `ImpedancePlot.tsx` | Canvas rendering, auto-scaling, dark theme |
| Tone player | `TonePlayer.tsx` | Web Audio API oscillators, per-note buttons |
| FFT (browser) | Web Audio API AnalyserNode | Built-in, configurable fftSize |
| FFT (Python) | scipy.signal / librosa.stft | Industry standard |

---

## Summary

**The path forward is clear:**
1. OpenWInD gives us predicted impedance peaks (= playable notes)
2. Web Audio API gives us measured frequency spectrum from microphone
3. We compare peak frequencies (Hz or cents deviation)
4. For advanced users: OpenWInD can also generate predicted sound waveforms
5. For expert users: measured impedance data can be imported for direct Z(f) comparison

**No better tools exist than OpenWInD for this purpose** — it's the only open-source library that combines impedance computation, sound simulation, and geometry optimization for wind instruments.

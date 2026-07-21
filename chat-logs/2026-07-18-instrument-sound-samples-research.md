# Instrument Sound Samples Research Report

**Date:** 2026-07-18  
**Purpose:** Identify professional instrument sound samples (especially wind instruments) for AI instrument design training data

---

## Executive Summary

This report catalogs 18 source categories for instrument sound samples, with emphasis on wind instruments (flute, clarinet, saxophone, oboe, bassoon, trumpet, trombone, horn, tuba). The **University of Iowa Musical Instrument Samples** emerges as the single best source for wind instrument research due to its anechoic recording environment, professional quality, comprehensive instrument coverage, and unrestricted free license.

---

## Top Sources for Wind Instruments

| Source | Best For | License | Quality |
|--------|----------|---------|---------|
| **Iowa MIS** | Anechoic wind samples (all dynamics, chromatic scales) | Free, unrestricted | ⭐⭐⭐⭐⭐ |
| **Philharmonia Orchestra** | Performance-quality wind samples (phrases, techniques) | Free non-commercial | ⭐⭐⭐⭐⭐ |
| **NSynth** | ML-ready wind instrument dataset | CC BY 4.0 | ⭐⭐⭐⭐ |
| **VSCO 2 CE** | Orchestral wind samples (SFZ format) | Free | ⭐⭐⭐⭐ |
| **SSO** | Basic orchestral wind samples | Free | ⭐⭐⭐ |

---

## Source Category Details

### 1. Iowa Musical Instrument Samples (MIS)

**Website:** https://theremin.music.uiowa.edu/mis.html  
**Contact:** Lawrence Fritts, University of Iowa  
**License:** Freely available, no restrictions

**Wind Instruments Covered:**
- Flute (including Alto Flute, Bass Flute)
- Oboe
- Eb Clarinet, Bb Clarinet, Bass Clarinet
- Bassoon
- Bb Soprano Saxophone, Eb Alto Saxophone
- Horn
- Bb Trumpet
- Tenor Trombone, Bass Trombone
- Tuba

**Recording Specs:**
- Pre-2012: Single Neumann KM 84 cardioid, 16-bit/44.1kHz, mono
- Post-2012: Three Earthworks QTC-40 (Decca Tree), 24-bit/96kHz stereo (left/right), mono center mic at 16/44.1
- All instruments recorded in **anechoic chamber** (27,000 cu ft, absorption to 60 Hz)
- Chromatic scales at pp, mf, ff dynamic levels
- Multiple playing techniques (arco, pizzicato, vibrato, non-vibrato)

**Sample Count:** Hundreds of notes per instrument, multiple dynamics  
**Used in:** 270+ published research articles and books  
**Download:** Direct download, zipped folders

**Strengths:**
- True anechoic recordings (no room coloration)
- Professional quality, standardized methodology
- Complete chromatic range at multiple dynamics
- Ideal for acoustic analysis and AI training

---

### 2. Philharmonia Orchestra Sound Library

**Website:** https://www.philharmonia.co.uk/explore/sound-library  
**License:** Free for non-commercial use

**Wind Instruments Covered:** All orchestral winds (flute, oboe, clarinet, bassoon, horn, trumpet, trombone, tuba)

**Sample Count:** Thousands of samples  
**Format:** WAV  
**Content:**
- Every note on every instrument
- Various volumes and durations
- Individual notes, musical phrases, full orchestra
- Professional recordings from live orchestra

**Strengths:**
- Performance-quality recordings
- Musical context (phrases, not just isolated notes)
- High production value

---

### 3. NSynth Dataset (Google Magenta)

**Website:** https://magenta.tensorflow.org/datasets/nsynth  
**License:** CC BY 4.0  
**Format:** WAV, 16-bit, 44.1kHz

**Sample Count:** 305,979 musical notes  
**Instruments:** 1,006 distinct instruments  
**Duration:** ~3 seconds per note

**Wind Instruments Included:** Yes (flute, clarinet, saxophone, trumpet, etc.)

**Strengths:**
- Pre-processed for ML training
- Consistent format and length
- Large scale (300k+ samples)
- Well-documented, widely cited

---

### 4. VSCO 2 Community Edition

**Website:** https://viscant.github.io/vsco2/  
**License:** Free  
**Format:** WAV, SFZ

**Content:** Orchestral sample library including wind instruments  
**Strengths:** SFZ format (easy to load in samplers), community-maintained

---

### 5. Sonatina Symphonic Orchestra (SSO)

**GitHub:** https://github.com/peastman/sso  
**Stars:** 245  
**License:** Free  
**Format:** WAV

**Content:** Basic orchestral samples including winds  
**Strengths:** Open source, actively maintained

---

### 6. BBC Sound Effects Archive

**Website:** https://sound-effects.bbcrewind.co.uk/  
**Mirror:** https://archive.org/details/BBCSoundEffects  
**License:** RemArc License (non-commercial); commercial licensing available

**Content:** 16,000+ sound effects  
**Strengths:** Professional production, diverse sounds

---

### 7. Freesound.org

**Website:** https://freesound.org  
**License:** Creative Commons (variable: CC0, CC-BY, CC-BY-NC)  
**Sample Count:** 718,799+ sounds

**Strengths:**
- Massive library
- Variable licenses (some commercial-friendly)
- Searchable API
- Community-contributed

---

### 8. Musopen

**Website:** https://musopen.org  
**License:** Public domain / royalty-free

**Content:** Classical music recordings, sheet music  
**Strengths:** High quality, no license restrictions

---

### 9. RWC Music Database

**Website:** https://staff.aist.go.jp/m.goto/RWC-MDB/  
**Mirror:** Zenodo (AIST)  
**License:** Academic/research  
**Format:** Various

**Content:** Instrument samples for MIR research  
**Strengths:** Well-documented, research-grade

---

### 10. MagnaTagATune

**Website:** https://mirg.city.ac.uk/datasets/magnatagatune/  
**Format:** MP3  
**Sample Count:** ~26,000 clips

**Content:** Clips from Magnatune label with crowd-sourced tags  
**Strengths:** Annotated data, useful for classification tasks

---

### 11. AudioSet (Google)

**Website:** https://research.google.com/audioset/  
**Sample Count:** 2M+ 10-second clips  
**Labels:** 632 ontology labels (including instruments)

**Content:** YouTube-sourced audio with labels  
**Strengths:** Massive scale, diverse sources

---

### 12. UNSW Acoustics Impedance Databases

**Website:** https://newt.phys.unsw.edu.au/jw/woodwinds.html  
**Researcher:** Joe Wolfe, UNSW  
**License:** Academic/research

**Instruments Covered:**
- Flute (full impedance database)
- Clarinet (full impedance database)
- Saxophone (full impedance database)
- Bassoon (full impedance database)

**Content:** Input impedance measurements, reed models, vocal tract data  
**Strengths:**
- Scientific acoustic data
- Essential for understanding wind instrument physics
- Detailed impedance curves across registers

**Limitations:** Not audio samples, but acoustic measurements

---

### 13. Inharmonicity Research

**Status:** Published data mainly for strings/piano  
**Wind Instruments:** Less common but exists in clarinet/saxophone research literature

---

### 14. Librosa (Python Library)

**Website:** https://librosa.org/doc/latest/feature.html  
**Install:** `pip install librosa`

**Features Available:**
- Spectral features (MFCC, chroma, spectral contrast)
- Bandwidth, rolloff, flatness
- Tempogram, onset detection
- Feature extraction for audio analysis

**Strengths:** Python-native, well-documented, widely used

---

### 15. Essentia

**Website:** https://essentia.upf.edu  
**License:** AGPL (open source)  
**Language:** C++ / Python bindings

**Features:** Comprehensive audio analysis and feature extraction  
**Strengths:** Production-grade, extensive feature set

---

### 16. Sonic Visualiser

**Website:** https://www.sonicvisualiser.org  
**License:** Open source

**Features:** GUI-based spectral analysis, VAMP plugin support  
**Strengths:** Visual analysis, no coding required

---

### 17. FluidSynth

**GitHub:** https://github.com/FluidSynth/fluidsynth  
**License:** LGPL 2.1+  
**Features:** SoundFont synthesizer, MIDI-to-audio

**Strengths:** Real-time synthesis, SoundFont support

---

### 18. Instrument Makers YouTube

**Channel:** https://youtube.com/@TheInstrumentMakers  
**Content:** Video series on handcrafted instrument creation

**Strengths:** Visual documentation of instrument construction

---

## Recommendations for AI Instrument Design

### Priority 1: Acoustic Data
1. **Iowa MIS** - Download all wind instrument anechoic samples (highest priority)
2. **UNSW Impedance Databases** - Input impedance data for flute, clarinet, saxophone, bassoon

### Priority 2: Performance Data
3. **Philharmonia Orchestra** - Musical phrases and techniques
4. **NSynth** - Large-scale ML-ready dataset

### Priority 3: Supplementary Data
5. **VSCO 2 / SSO** - Additional orchestral samples
6. **Freesound** - Specific sounds not found elsewhere

### Priority 4: Analysis Tools
7. **Librosa** - Feature extraction pipeline
8. **Essentia** - Advanced audio analysis

---

## Download Priority List

1. Iowa MIS wind instruments (all post-2012 24/96 files)
2. NSynth dataset (full)
3. UNSW impedance databases
4. Philharmonia wind samples
5. VSCO 2 CE

---

*Report compiled 2026-07-18*

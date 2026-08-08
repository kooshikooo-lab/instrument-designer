# Woodwind Acoustics Research References
# Compiled 2026-07-25

## Core Textbooks

### Nederveen (1998) — Acoustical Aspects of Woodwind Instruments
- Publisher: Northern Illinois University Press
- ISBN: 978-0875805771
- THE definitive monograph on woodwind acoustics. Tone hole calculations, bore corrections, reed dynamics.

### Fletcher & Rossing (1998) — The Physics of Musical Instruments
- Publisher: Springer (776 pages)
- ISBN: 978-0-387-98374-5
- Ch. 14-15: Reed vibration, woodwind instruments. Ch. 6: Pipes, horns, cavities.

### Benade (1976) — Fundamentals of Musical Acoustics
- Publisher: Oxford University Press
- Introduced "regeneration," mode interactions, tonehole lattice behavior, "response curve" paradigm.

### Chaigne & Kergomard (2016) — Acoustics of Musical Instruments
- Publisher: Springer
- Modern treatment: TMM, FDTD, connection between linear acoustics and nonlinear oscillation.

### Smith (2010) — Physical Audio Signal Processing (FREE ONLINE)
- URL: https://ccrma.stanford.edu/~jos/pasp/
- Digital waveguides, tone holes, bell radiation, reed excitation, conical bores.

---

## Key Papers: TMM & Tone Hole Modeling

### Keefe (1990) — Woodwind Air Column Models
- JASA, 88(1), pp. 35-51
- DOI: 10.1121/1.399911
- Foundational TMM paper. Lumped T-circuit tone hole model.

### Lefebvre & Scavone (2012) — Characterization of Toneholes with FEM
- JASA, 131(4), pp. 3153-3163
- DOI: 10.1121/1.3685481
- Most accurate tone hole parameterization for TMM.

### Lefebvre, Scavone & Kergomard (2013) — External Tonehole Interactions (TMMI)
- Acta Acustica, 99, pp. 975-985
- DOI: 10.3813/AAA.918676
- Mutual radiation impedance between open holes.

### Zwikker & Kosten (1949) — Classical Loss Model
- Low-reduced-frequency transmission line for viscothermal losses.

### Hélie et al. (2022) — Conical Tube Losses
- J. Sound & Vibration
- Generalizes Zwikker-Kosten to conical tubes.

---

## Key Papers: Radiation & End Corrections

### Levine & Schwinger (1948) — Unflanged Pipe Radiation
- Physical Review, 73, pp. 383-406
- End correction: δ₀ = 0.6133a

### Norris & Sheng (1989) — Flanged Pipe Radiation
- J. Sound & Vibration, 135(1), pp. 85-93
- End correction: δ∞ = 0.8216a

### Dalmont et al. (2001) — Finite Flange Radiation
- Interpolation formula for wall thickness effects.

---

## Key Papers: Optimization

### Ernoult et al. (2020) — Woodwind Design Optimization (JASA)
- JASA, 148(5), pp. 2864-2877
- DOI: 10.1121/10.0002449
- Phase-based impedance optimization with geometric constraints. Regularized unwrapped phase.

### Ernoult et al. (2021) — Full Waveform Inversion for Bore Reconstruction
- Acta Acustica, 5, p. 47
- Adjoint-state FWI for woodwind bore reconstruction from impedance measurements.

### Patkau, Lefebvre & Kort (2017) — WIDesigner (ISMA 2017)
- URL: https://isma2017.cirmmt.mcgill.ca/proceedings/pdf/ISMA_2017_paper_5.pdf
- DIRECT + BOBYQA optimization. 19 parameters, 2 minutes.

### Noreland et al. (2013) — The Logical Clarinet
- Acta Acustica, 99, pp. 615-628
- arXiv: 1209.3637v2
- First systematic numerical optimization. Up to 400 variables.

### Noreland/Guilloteau (2023) — Woodwind Optimization with Geometric Constraints
- HAL: hal-02479433
- Simultaneously optimizes frequencies AND peak amplitude ratios.

---

## Key Papers: Benade & Mode Alignment

### Benade (1970) — Acoustic Criteria for Adjusting Tone and Response
- JASA, doi:10.1121/1.1975393
- 2nd mode within 5 cents of 3rd harmonic for good tone.

### Benade (1974) — Harmonic Regeneration
- JASA, doi:10.1121/1.1919870
- Playing frequency maximizes net oscillatory energy.

### Benade (1983) — NX Clarinet
- JASA, doi:10.1121/1.2020595
- Deliberately mistuned register hole for response.

### Benade (1984) — Mode Alignment Measurement
- JASA, doi:10.1121/1.2021757
- Professional clarinetists accept 30-15¢ errors, <10¢ excellent.

---

## Key Papers: Sound Synthesis

### Smith (1992) — Digital Waveguide Physical Modeling
- Computer Music Journal, 16(4), pp. 74-91
- Foundational paper for waveguide synthesis.

### Engel et al. (2020) — DDSP
- ICLR 2020
- URL: https://openreview.net/forum?id=B1x1ma4tDr
- Differentiable DSP + neural networks. 10 min training per instrument.

### Lee et al. (2024) — Differentiable Modal Synthesis
- NeurIPS 2024
- URL: https://openreview.net/forum?id=fpxRpPbF1t
- Modal synthesis + spectral modeling in neural network.

### Darabundit & Scavone (2025) — Port-Hamiltonian Woodwind Model
- Frontiers in Signal Processing
- DOI: 10.3389/frsip.2025.1519450
- Cutting edge: energy-preserving numerical methods.

### Bilbao et al. (2019) — NESS Project
- Computer Music Journal
- Large-scale real-time modular physical modeling.

---

## Key Papers: Timbre & Spectral Analysis

### Wolfe (UNSW) — Cutoff Frequencies and Cross-fingering
- JASA
- Baroque vs modern flute cutoff: 1.5 kHz vs 2 kHz

### Wu, Wang & Liu (2013) — Nontonal MFCC
- 97.7% instrument classification accuracy

### Guaus et al. (2010) — Dynamic Spectral Envelope
- Time-varying spectral envelope for instrument sounds.

---

## Key Papers: Instrument Maker Compromises

### Greenham (2003) — Clarinet Toneholes: Undercutting Effects
- PhD diss., London Metropolitan University
- 18 clarinetist experiment on undercut vs rounded holes.

### Dalmont et al. — Radiated Power of Tone Holes
- HAL: hal-01094511
- Power nearly independent of hole radius for wide holes.

### Szwarcberg et al. (2025) — Saxophone Sensitivity
- Acta Acustica
- Register hole ≤0.5mm → instrument won't overblow.

### Tournemène et al. (2018) — Brass Optimization with Sound
- HAL/Inria
- First to optimize spectral centroid alongside intonation.

---

## GitHub Repositories

| Repo | Stars | Language | Category |
|------|-------|----------|----------|
| openwind (GitLab Inria) | — | Python | TMM+FEM+Optimization |
| WWIDesigner | 47 | Java | TMM+BOBYQA+DIRECT |
| pfh/demakein | 55 | Python | Design→3D Print |
| garyscavone/acmt | — | MATLAB | TMM+DWG |
| ness | 45 | C++ | FDTD Physical Modeling |
| gumyr/build123d | 2649 | Python | Parametric CAD |
| MarkChuCarroll/chalumier | 6 | Kotlin | TMM Design |
| magenta/ddsp | — | Python | Differentiable DSP |
| python-acoustics | — | Python | Acoustic Analysis |

---

## Databases

| Database | URL | Content |
|----------|-----|---------|
| Wolfe/UNSW | phys.unsw.edu.au/music | Impedance + sound for many instruments |
| MIT GIFT | — | CT scans of musical instruments |
| Adrian Brown Database | adrianbrown.org | Renaissance recorder bore profiles |
| MFA Boston | — | CT scans of historical instruments |
| MIMIC (McGill) | — | Impedance measurements |
| OpenWInD Demo | demo-openwind.inria.fr | Interactive impedance computation |

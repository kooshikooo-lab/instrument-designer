# Research: AI Tools for Computational Instrument Design

**Date:** 2026-07-22
**Branch:** `experiment/tmm-improvements`

## 1. Differentiable Acoustic Simulation

### JAX-BEM (April 2026)
- **What:** Differentiable Boundary Element Method for gradient-based acoustic shape optimization
- **Why:** BEM only meshes boundaries (not volume), making it efficient for unbounded domains like loudspeaker horns
- **Key insight:** JAX autodiff on numerical methods enables 10-100x faster gradient computation vs finite differences
- **Paper:** arXiv:2604.21431 (University of Salford)
- **Use case:** Could replace or augment our TMM for more accurate 3D bore optimization (currently 1D TMM)
- **Status:** Published, working code (bempp-cl based)

### j-Wave (UCL, Open Source)
- **What:** Differentiable acoustic wave simulator in JAX
- **Why:** Solves time-varying and time-harmonic acoustic problems with automatic differentiation
- **Features:** Compatible with JAX and TensorFlow, GPU-accelerated, validated against k-Wave
- **GitHub:** github.com/ucl-bug/jwave
- **Use case:** Could be used for higher-fidelity impedance computation than our TMM
- **Status:** Published in SoftwareX (2023), actively maintained

### Phi-Flow (ICML 2024)
- **What:** Differentiable simulation toolkit supporting PyTorch, TensorFlow, JAX, and NumPy
- **Why:** Provides differential operators, boundary conditions, dimension-agnostic code, sparse linear solves
- **Features:** Out-of-the-box fluid simulation support, automatic matrix generation
- **Use case:** Could accelerate our FDTD simulations if we move to full-wave modeling
- **Status:** Published at ICML 2023, actively maintained

### MIT Thesis: FDTD + Deep Learning (2019)
- **What:** GPU-accelerated 3D FDTD simulator for wind instruments + deep learning inverse design
- **Why:** Directly relevant — same problem as ours (shape → sound, sound → shape)
- **Approach:** 3D FDTD forward model → neural network inverse model → automatic pitch hole placement
- **Limitation:** Single-reed instruments only, "roughly approximates" desired sound
- **Status:** MIT MEng thesis, code not publicly available

## 2. Neural Network Surrogate Models

### Physics-Informed Neural Networks (PINNs) for Acoustics
- **Acoustic topological insulators:** PINN with 12x training data reduction, 95% prediction accuracy (2026)
- **Acoustic metasurfaces:** Probabilistic DNN for inverse design of customizable absorption (2025)
- **Multifunctional metastructures:** Cascading DNNs for acoustic-mechanical co-design (2026)
- **Key pattern:** Forward model (NN) → inverse model (cascaded with pretrained forward) → on-demand design

### Graph Neural Network Surrogates (2024)
- **What:** GNN-based surrogate for fluid-acoustic shape optimization
- **Why:** Transforms mesh-based simulations into computational graphs, 1-2% median error
- **Use case:** Could model bore geometry as graph for faster optimization
- **Status:** arXiv:2412.16817

### ML in Acoustics Review (npj Acoustics, 2025)
- **AcousticsML repository:** Open-source Jupyter notebooks for ML in acoustics
- **Applications:** Acoustic classification, generative spatial audio, physics-informed neural networks
- **GitHub:** github.com/acousticsml (McCarthy et al.)
- **Use case:** Reference implementations for impedance peak detection, spectral analysis

## 3. Spectral Analysis Tools

### librosa (Python)
- **What:** Audio and music signal analysis library (3000+ citations)
- **Features:** STFT, mel spectrograms, harmonic analysis, pitch detection (pyin), MFCCs
- **Use case:** Could analyze recorded instrument audio for impedance peak detection, intonation measurement
- **Status:** Active, v0.11.0

### python-acoustics (555 stars)
- **What:** Python library for acousticians
- **Features:** Signal processing, octave/fractional octave analysis, psychoacoustics
- **Use case:** General acoustic measurements and analysis
- **Status:** Active, BSD-3 license

### spectrum (PyPI)
- **What:** Spectral analysis tools (PSD estimation)
- **Features:** Fourier (Welch, periodogram), parametric (BURG, Yule-Walker), eigen (MUSIC), multitaper
- **Use case:** High-resolution spectral analysis for impedance curve analysis
- **Status:** v0.9.0 (2024)

## 4. Wind Instrument Tools

### OpenWInD (Inria, Python)
- **What:** Open-source wind instrument design toolbox
- **Modules:** Impedance computation (TMM + spectral FEM), sound simulation (time domain), shape optimization
- **Key features:** Bore reconstruction from measured impedance, visco-thermal losses, reed/lips coupling
- **Use case:** Direct competitor and reference for our optimizer
- **Status:** Active development, pip installable
- **Note:** We already evaluated this — faster than demakein but requires careful setup

### chalumier (Kotlin, Apache-2.0)
- **What:** Rewrite of demakein with evolutionary optimizer
- **Achievement:** 1.2 cents RMS on reedpipe template
- **Use case:** Our TMM Python port is based on this. Benchmark comparison pending (JDK blocker)

## 5. Use Cases for Our Project

### Immediate (Phase 1 completion)
1. **librosa for impedance analysis:** Record instrument audio, extract spectral peaks, compare to TMM predictions
2. **python-acoustics for measurements:** When we have physical instruments, measure impedance and compare
3. **Multi-restart Powell:** Run Powell from multiple random starting points, pick best result

### Medium-term (Phase 2)
1. **Surrogate model for bore optimization:** Train NN to predict intonation from bore profile, then optimize the NN (fast) instead of TMM (slow)
2. **OpenWInD integration:** Use OpenWInD for higher-fidelity impedance computation in validation
3. **PINN for loss modeling:** Model visco-thermal losses more accurately than current analytical corrections

### Long-term (Phase 3+)
1. **3D FDTD + inverse design:** Full 3D acoustic simulation + neural network inverse (MIT approach)
2. **Differentiable BEM:** JAX-BEM for gradient-based 3D shape optimization
3. **Measurement loop:** Print → measure impedance → compare to design → re-optimize

## 6. Tauri Desktop App Status

The Tauri v2 desktop app is **fully set up and built**:
- React 19 + Vite 8 + Tailwind 4 + Three.js
- Tauri v2.11.3 with 11 custom commands (server mgmt, HTTP bridge, file I/O, metadata)
- Built successfully: .exe + NSIS installer + MSI installer
- Missing capabilities from ROADMAP: event listening, process spawn permission

### What Could Be Improved
1. **Update tauri.conf.json capabilities** — add missing event/process permissions
2. **Add auto-updater** — GitHub releases integration
3. **Add system tray** — minimize to tray while optimization runs
4. **Add real-time bore visualization** — Three.js 3D bore profile during optimization
5. **Add impedance peak display** — matplotlib-style impedance curve overlay

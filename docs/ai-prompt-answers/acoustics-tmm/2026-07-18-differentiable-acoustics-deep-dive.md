# Differentiable Acoustics Tools for Instrument Design — Deep Dive
**Date:** 2026-07-18  
**Focus:** jaxdiffmodal, DiffSound, and the broader landscape of differentiable acoustic simulation for wind instrument design

---

## Part 1: jaxdiffmodal

### Repository
- **GitHub:** https://github.com/rodrigodzf/jaxdiffmodal
- **Website:** http://rodrigodzf.com/jaxdiffmodal/
- **Paper:** arXiv:2505.05940 (accepted to DAFx 2025)
- **Authors:** Rodrigo Diaz, Mark Sandler (Queen Mary University of London)
- **License:** GPL-3.0
- **Stars:** 14 | **Forks:** 1

### What It Is
A fast, differentiable, GPU-accelerated simulation framework for modelling the dynamics of **strings, membranes, and plates** using modal methods, implemented in JAX.

### Physical Models Supported
| Model | Type | Nonlinearity |
|-------|------|-------------|
| Kirchhoff–Carrier string | 1D string | Tension-modulated nonlinearity |
| Berger membrane | 2D membrane | Tension-modulated nonlinearity |
| von Kármán plate | 2D plate | Full nonlinear plate theory |

**No tubes, bores, or wind instrument models.** The framework is designed for vibrating structural elements (strings, membranes, plates) — not for acoustic wave propagation in tubes or air columns.

### How the Differentiable Simulation Works
1. **Modal decomposition:** Computes eigenmodes and eigenvalues of the structure analytically (for simple geometries) or numerically (using magpie-python for arbitrary boundaries)
2. **Coupling coefficients:** Computes nonlinear modal coupling tensors (e.g., von Kármán plate coupling)
3. **Time integration:** Uses Störmer-Verlet (symplectic) time integration, implemented as a differentiable JAX computation graph
4. **JAX autodiff:** The entire pipeline is written in JAX, so `jax.grad()` gives gradients through the simulation with respect to any physical parameter
5. **GPU acceleration:** JIT-compiled for GPU, achieving ~2x real-time for 100-mode von Kármán plate at 44.1 kHz

### Parameters That Can Be Optimized
- **Geometry:** Plate dimensions, membrane radius
- **Material properties:** Tension, bending stiffness, density
- **Boundary conditions:** Via numerical mode computation (magpie-python)
- **Nonlinear coupling tensors:** Directly optimized in inverse experiments
- **Damping coefficients**

### Performance Benchmarks
- Benchmarked against MATLAB, C++ (Eigen+BLAS), and PyTorch (JIT, GPU)
- **< 50 modes:** JAX slightly slower than MATLAB/C++
- **~100 modes:** JAX is fastest — achieves ~2x real-time for 1s simulation at 44.1 kHz
- **> 100 modes:** JAX significantly outperforms all alternatives
- **PyTorch GPU:** JAX substantially outperforms JIT-compiled PyTorch on GPU
- Tested on AMD Ryzen 9 5900X + NVIDIA RTX 3090, 64GB RAM, FP32

### Can It Predict Frequency Response / Impedance?
**Partially.** The framework includes tools for:
- Transfer function computation (modal → physical domain)
- Transfer function = frequency response of the structure
- Can compute the vibration response spectrum

But it does NOT compute **acoustic input impedance** of a tube/bore. It computes mechanical impedance/vibration response of structural elements.

### Installation & Dependencies
```bash
# Recommended: use uv package manager
uv sync

# Or with pip:
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```
- Requires JAX (with CUDA for GPU)
- Dependencies: JAX, scipy (for tests), magpie-python (for numerical modes)
- Development extras: `uv sync --extra dev --extra benchmark`

### Instrument-Related Use Cases
- **Inverse modelling experiments:** Recovering tension, stiffness, damping, and geometry from both synthetic and experimental data
- **Parameter recovery from real-world measurements:** Demonstrated with real string and plate recordings
- **Dataset generation:** Designed for large-scale physical parameter sweeps
- **Real-time synthesis:** At moderate mode counts, achieves real-time or faster

### Can You Define a Custom Acoustic Model for a Wind Instrument Bore?
**No.** jaxdiffmodal is fundamentally a **structural vibration** simulator, not an acoustic waveguide/tube simulator. It solves the wave equation for vibrating 1D/2D structures, not for acoustic pressure propagation in tubes. The physics are different:
- Strings/plates/membranes: transverse vibrations, governed by plate/membrane equations
- Wind instrument bores: longitudinal acoustic waves, governed by the Webster equation / waveguide equations

**However**, the framework's architecture is instructive:
- The differentiable modal approach (eigenmode computation → nonlinear coupling → time integration) could theoretically be adapted for tube acoustics if someone implemented the correct eigenmodes (Helmholtz modes of a tube) and coupling physics
- The JAX autodiff infrastructure is reusable
- The paper explicitly mentions the framework "can readily be combined with neural networks" and supports "hybrid physics-based and data-driven approaches"

### Assessment for Wind Instrument Design
| Criterion | Rating | Notes |
|-----------|--------|-------|
| Wind instrument bore modeling | ❌ Not applicable | Structural vibration only |
| Gradient-based optimization | ✅ Excellent | Native JAX autodiff |
| GPU performance | ✅ Excellent | Outperforms alternatives at scale |
| Extensibility | ✅ Good | Modular, documented, GPL-3.0 |
| Documentation | ⚠️ Moderate | README, paper, notebooks, but no API docs |
| Maturity | ⚠️ Early | 25 commits, 14 stars, single paper |

---

## Part 2: DiffSound (SIGGRAPH 2024)

### Repository
- **GitHub:** https://github.com/TechnetiumMan/DiffSound
- **Paper:** arXiv:2409.13486 (SIGGRAPH 2024)
- **Authors:** Xutong Jin, Chenxi Xu, Ruohan Gao, Jiajun Wu, Guoping Wang, Sheng Li (Peking University, Stanford)
- **Project Page:** https://hellojxt.github.io/DiffSound/
- **Stars:** 17 | **Forks:** 2

### What It Actually Does
DiffSound is a **differentiable sound rendering framework for physics-based modal sound synthesis**. It implements the full pipeline:

**Forward (Shape → Sound):**
1. 3D geometry → tetrahedral mesh (via fTetWild)
2. Mesh → modal eigenvalues (via high-order FEM)
3. Eigenvalues → audio signal (via differentiable additive synthesizer)

**Inverse (Sound → Shape):**
- Optimize material parameters (Young's modulus, Poisson's ratio) from sound
- Optimize geometric shape from sound (recover detailed shape from coarse voxel)
- Optimize volumetric thickness from sound
- Optimize impact position from sound
- Optimize shape morphing coefficients from sound

### Input/Output Format
- **Input:** 3D tetrahedral mesh (via fTetWild), material parameters, impact position
- **Output:** Synthesized audio waveform
- **Inverse input:** Target audio waveform + coarse constraints
- **Inverse output:** Optimized material/geometry parameters

### 3D Geometry Support
**Yes — full 3D.** DiffSound uses:
- **DMTet (Deep Marching Tetrahedra)** for hybrid implicit/explicit shape representation
- **Signed Distance Field (SDF)** encoded by MLP for implicit shape
- **Explicit tetrahedral mesh** for FEM computation
- fTetWild for tetrahedral meshing

This is genuinely 3D, not 2.5D. The FEM operates on 3D tetrahedral elements.

### Differentiable Renderer Architecture
Three main components:
1. **Differentiable tetrahedral mesh representation:** SDF → tetrahedral mesh via DMTet, fully differentiable
2. **High-order finite element analysis module:** Computes eigenvalues of the stiffness/mass matrices; supports different material and shape parameters
3. **Differentiable additive synthesizer:** Takes eigenvalues → synthesized audio with learnable damping coefficients and mode amplitudes

**Hybrid loss function:** Combines time-domain, spectral, and perceptual losses for smooth optimization.

### Frequency Range
- The framework works with **modal eigenvalues**, so the frequency range depends on:
  - Mesh resolution (higher order = more accurate high frequencies)
  - Number of modes computed
- Typical experiments: audio-rate sampling (likely 16-44.1 kHz)
- No explicit frequency range limitation stated, but accuracy degrades at high frequencies due to mesh resolution requirements

### Installation & Dependencies
```bash
# Python 3.8
conda create -n DiffSound python=3.8
conda activate DiffSound
pip install -r requirements.txt

# Also requires fTetWild (C++ library)
sudo apt-get install libgmp-dev
git clone https://github.com/wildmeshing/fTetWild.git
cd fTetWild && mkdir build && cd build && cmake .. && make
# Add build directory to PATH
```
- **PyTorch 2.0** (CUDA 11.7)
- fTetWild (tetrahedral meshing, C++ dependency)
- Note: **Linux only** (requires cmake, apt-get)

### Inverse Design Examples (from paper)
1. **Material parameter inference:** Recover Young's modulus and Poisson's ratio from both synthetic and real-recorded audio
2. **Geometric shape estimation:** Recover detailed 3D shape from coarse voxel + modal eigenvalues
3. **Volumetric thickness inference:** Determine if an object is solid or hollow, and the wall thickness
4. **Impact position prediction:** Find where an object was struck from its sound

### Limitations for Instrument Design
| Limitation | Severity | Details |
|------------|----------|---------|
| **Impact sounds only** | 🔴 Critical | Designed for impact/ringing sounds (bells, plates, bowls), not sustained wind-driven oscillation |
| **No bore/tube model** | 🔴 Critical | FEM on 3D solid/hollow objects, not 1D waveguide acoustics |
| **No excitation model** | 🔴 Critical | Models passive vibration response, not active lip-reed excitation |
| **No impedance computation** | 🟡 Significant | Computes eigenvalues, not input impedance vs. frequency |
| **Stiff dependency** | 🟡 Significant | PyTorch 2.0, Python 3.8, fTetWild — older stack |
| **No tone holes** | 🟡 Significant | Only models single continuous objects, not pipe networks |
| **Linux only** | 🟠 Moderate | fTetWild requires Linux build |

### Assessment for Wind Instrument Design
| Criterion | Rating | Notes |
|-----------|--------|-------|
| Wind instrument bore modeling | ❌ Not applicable | Impact sound synthesis, not tube acoustics |
| Inverse design capability | ✅ Excellent | Sound → geometry/material for solid objects |
| Differentiable pipeline | ✅ Excellent | Full end-to-end differentiability |
| 3D geometry support | ✅ Full 3D | Tetrahedral mesh FEM |
| Documentation | ⚠️ Moderate | README with experiments, but no API docs |
| Usability | ⚠️ Complex | Requires fTetWild C++ build, older Python |

---

## Part 3: Broader Landscape — Differentiable Acoustics for Wind Instruments

### 3.1 j-Wave (JAX-based Wave Simulator)

**GitHub:** https://github.com/ucl-bug/jwave  
**Paper:** SoftwareX 2023, arXiv:2207.01499  
**Authors:** Antonio Stanziola et al. (UCL)

**What it does:**
- Differentiable wave equation solver (time-varying and time-harmonic/Helmholtz)
- 1D, 2D, and 3D support
- Finite differences and Fourier spectral methods
- Fully differentiable via JAX autodiff
- GPU/TPU accelerated via JIT compilation
- Compatible with JAX ML ecosystem

**Relevance to wind instruments:**
- **Could model tube acoustics** — solves the wave equation in arbitrary media
- The Helmholtz solver could compute acoustic impedance of a bore
- Differentiable → gradients with respect to sound speed, geometry, boundary conditions
- However, designed primarily for **medical ultrasound** and **photoacoustics**, not musical acoustics
- Would need significant custom work to model bore profiles, tone holes, radiation

**Windows note:** Only runs on Windows via WSL.

### 3.2 JAX-BEM (Differentiable Boundary Element Method)

**Paper:** arXiv:2604.21431 (April 2026)  
**Authors:** James Hipperson, Jonathan Hargreaves, Trevor Cox (University of Manchester)

**What it does:**
- Differentiable BEM solver for acoustic scattering/radiation in unbounded domains
- Optimizes geometry via gradient-based methods (L-BFGS)
- Validated against bempp and analytical solutions (rigid sphere scattering)
- Demonstrated on **loudspeaker horn directivity optimization** — very close to instrument bore design

**Relevance to wind instruments:**
- **Directly applicable concept** — optimizes horn/tube geometry for desired acoustic properties
- Differentiates through the Helmholtz equation solver back to mesh vertices
- Could optimize bore profile for target impedance or directivity
- Still a preprint, not yet a mature tool

### 3.3 Full Waveform Inversion (FWI) for Bore Reconstruction

**Paper:** Acta Acustica 2021  
**Authors:** Augustin Ernoult, Juliette Chabassier et al.  
**Code:** OpenWInD (open source, GPL-3.0)

**What it does:**
- **Directly targets wind instrument bore reconstruction**
- Uses gradient-based optimization (quasi-Newton) to find bore geometry from impedance measurements
- 1D spectral FEM for wave propagation in tubes (including viscothermal losses, tone holes, radiation)
- Computes gradients analytically (Frechet derivatives), not via finite differences
- Successfully reconstructed a woodwind-like instrument (cylinder + 4 side holes, 14 parameters) in ~1 minute on a laptop

**Key insight:** The gradient of the cost function is obtained by solving the same linear system as the forward problem, with a different source term. This makes gradient computation nearly free.

**Relevance to wind instruments:**
- **This is exactly the tool for wind instrument bore design/optimization**
- Handles variable cross-section bore, tone holes with chimney heights, viscothermal losses
- Gradient-based → efficient optimization of many parameters
- Open source implementation available
- However: written in custom code (not JAX/PyTorch), uses own AD framework

### 3.4 Woodwind Instrument Design Optimization

**Paper:** JASA 2020 (Ernoult, Vergez, Missoum, Guillemain, Jousserand)  
**Also:** HAL hal-02479433

**What it does:**
- Gradient-based (SQP) optimization of woodwind instrument geometry
- Optimizes: bore profile, hole positions, hole radii, chimney heights
- Uses novel phase-based resonance description (avoids non-smooth peak detection)
- 38 design variables for a pentatonic clarinet with two registers
- Simultaneously adjusts resonance frequencies AND peak amplitude ratios

**Key challenge addressed:** Traditional peak detection is non-smooth → bad for gradient methods. The paper introduces unwrapped phase of the reflection coefficient as a smooth objective.

### 3.5 Differentiable Pulsetable Synthesis for Wind Instruments

**Paper:** ICASSP 2026  
**Authors:** Simon Schwär, Christian Dittmar, Stefan Balke, Meinard Müller  
**AudioLabs Erlangen**

**What it does:**
- Differentiable DSP approach to wind instrument synthesis
- Pulsetable synthesis (related to wavetable) with direct optimization of pulse prototypes
- Only 60,000 trainable parameters
- Interpretable control (pitch, velocity, gain)
- Trained on just minutes of recordings

**Relevance:**
- Differentiable instrument modeling, but **signal-level** not **physics-level**
- No bore geometry optimization — learns spectral characteristics directly
- Useful for sound design, not for physical instrument prototyping

### 3.6 misuka (Differentiable Room Acoustic Renderer)

**GitHub:** https://github.com/misuka-renderer/misuka  
**Paper:** Proceedings of Meetings on Acoustics 2026

**What it does:**
- Differentiable geometric acoustic renderer (ray/path tracing)
- Built on Mitsuba 3 (differentiable light transport renderer)
- Optimizes material properties, geometry, emitter/receiver positions
- Time-resolved Path Replay Backpropagation for efficient gradients
- GPU-accelerated

**Relevance:**
- Optimizes room acoustics, not instrument bore acoustics
- But the differentiable rendering infrastructure is powerful
- Could theoretically be adapted for acoustic design problems

### 3.7 Differentiable Geometric Acoustic Path Tracing

**Paper:** ACM Transactions on Graphics 2025 (SIGGRAPH 2025)  
**Authors:** Finnendahl, Worchel, Jüterbock et al. (TU Berlin)

**What it does:**
- Time-resolved Path Replay Backpropagation for acoustic path tracing
- Computes gradients of energy spectrograms w.r.t. scene parameters (materials, geometry, emitter/mic positions)
- Constant memory, linear time complexity
- Validated against RAVEN acoustic simulation software

**Relevance:**
- Theoretical foundation for misuka
- Demonstrates that differentiable acoustic rendering is possible at scale

### 3.8 Differentiation Strategies for Acoustic Inverse Problems

**Paper:** arXiv:2511.11415 (Nov 2025)  
**Authors:** Borrel-Jensen, Bjorgaard

**What it does:**
- Uses **JAX-FEM** for differentiable finite element acoustic simulation
- Admittance estimation from sparse pressure measurements (gradient-based)
- Acoustic shape optimization (48.1% energy reduction at target frequencies)
- 30-fold fewer FEM solutions than standard finite differences

**Relevance:**
- JAX-FEM could be the foundation for building a differentiable tube acoustics solver
- Demonstrates gradient-based acoustic optimization works in practice

### 3.9 PINNs for Acoustic Tube Analysis

**Paper:** Forum Acusticum 2025  
**Authors:** Luan, Yokota, Scavone

**What it does:**
- Physics-Informed Neural Networks for 1D acoustic tube problems
- Reconstructs acoustic fields from noisy/limited measurements
- Predicts radiation model coefficients
- PINN Fine-Tuning Method (PINN-FTM) for robust inverse problems

**Relevance:**
- Directly addresses tube acoustics inverse problems
- Can handle unknown radiation conditions
- Robust to noise (important for real measurements)

---

## Comparative Summary

### Tool Comparison Matrix

| Tool | Tube/Bore Model | Differentiable | GPU | Inverse Design | Wind Instruments | Status |
|------|----------------|----------------|-----|----------------|-----------------|--------|
| **jaxdiffmodal** | ❌ | ✅ JAX | ✅ | ✅ | ❌ (plates/strings) | v1.0 |
| **DiffSound** | ❌ | ✅ PyTorch | ✅ | ✅ (3D shapes) | ❌ (impact sounds) | v1.0 |
| **j-Wave** | ⚠️ (wave eq.) | ✅ JAX | ✅ | ✅ | ⚠️ (needs custom) | v0.2.1 |
| **JAX-BEM** | ⚠️ (exterior) | ✅ JAX | ✅ | ✅ | ⚠️ (horns) | Preprint |
| **FWI/OpenWInD** | ✅ | ⚠️ (manual AD) | ❌ | ✅ | ✅ | Open source |
| **JASA woodwind** | ✅ | ⚠️ (finite diff) | ❌ | ✅ | ✅ | Published |
| **DiffPulse** | ❌ (signal) | ✅ PyTorch | ✅ | ⚠️ (timbre) | ⚠️ (synthesis) | ICASSP 2026 |
| **misuka** | ❌ (room acoustics) | ✅ | ✅ | ✅ | ❌ | Open source |
| **PINNs tube** | ✅ | ⚠️ (custom) | ⚠️ | ✅ | ⚠️ (1D tube) | Published |

### Key Findings

1. **No single tool does everything.** The landscape is fragmented across structural vibration (jaxdiffmodal, DiffSound), tube acoustics (FWI/OpenWInD, JASA woodwind), wave equation solving (j-Wave), and room acoustics (misuka).

2. **For wind instrument bore design specifically:**
   - **FWI/OpenWInD** is the most directly relevant — it does gradient-based bore optimization with viscothermal losses and tone holes
   - **JASA woodwind optimization** extends this to multi-register, multi-fingering optimization
   - **JAX-BEM** could handle exterior radiation from bells/horns
   - **j-Wave** could serve as a differentiable tube simulator with significant custom work

3. **The JAX ecosystem is powerful but underutilized for musical acoustics:**
   - j-Wave has the wave equation infrastructure
   - JAX-BEM has the boundary element infrastructure
   - JAX-FEM exists for finite element problems
   - But none are specifically built for musical instrument bore acoustics

4. **The biggest gap:** A differentiable, GPU-accelerated, open-source tool that combines:
   - 1D tube/waveguide acoustics (with viscothermal losses)
   - Tone hole modeling
   - Radiation impedance
   - Nonlinear excitation (lips/reeds)
   - JAX or PyTorch autodiff for gradient-based optimization

5. **Most promising foundation for building such a tool:**
   - Start with j-Wave's differentiable wave equation infrastructure
   - Add tube-specific physics (Webster equation, viscothermal losses from Thibault & Chabassier 2021)
   - Port FWI/OpenWInD's gradient computation to JAX
   - Use JAX-BEM for exterior radiation

---

## Practical Recommendations for Instrument Design

### If you want to optimize bore geometry right now:
1. Use **OpenWInD** (FWI approach) — it's the most mature tool for this specific task
2. Or implement the JASA woodwind optimization approach in Python/JAX

### If you want to build a differentiable tool from scratch:
1. Use **JAX** as the foundation (autodiff + GPU + JIT)
2. Implement 1D tube acoustics with viscothermal losses (Thibault & Chabassier 2021 model is excellent — coefficients are geometry-independent)
3. Add tone hole modeling (switching PHS framework from the Frontiers 2025 paper)
4. Add radiation impedance (e.g., Nederveen model)
5. Use JAX autodiff for gradient-based optimization

### If you want to combine physics + ML:
1. Use j-Wave or jaxdiffmodal as the differentiable physics backbone
2. Add neural network components for learned parts (embouchure model, perception model)
3. The modular design of jaxdiffmodal is a good architectural reference

---

## References

### Primary Tools
- Diaz & Sandler (2025). "Fast Differentiable Modal Simulation of Non-linear Strings, Membranes, and Plates." DAFx 2025. arXiv:2505.05940
- Jin et al. (2024). "DiffSound: Differentiable Modal Sound Rendering and Inverse Rendering for Diverse Inference Tasks." SIGGRAPH 2024. arXiv:2409.13486

### Related Work
- Stanziola et al. (2023). "j-Wave: An open-source differentiable wave simulator." SoftwareX 22:101338.
- Hipperson et al. (2026). "JAX-BEM: Gradient-Based Acoustic Shape Optimisation via a Differentiable Boundary Element Method." arXiv:2604.21431.
- Ernoult et al. (2021). "Full waveform inversion for bore reconstruction of woodwind-like instruments." Acta Acustica 107.
- Ernoult et al. (2020). "Woodwind instrument design optimization based on impedance characteristics with geometric constraints." JASA 148.
- Thibault & Chabassier (2021). "Dissipative time-domain one-dimensional model for viscothermal acoustic propagation in wind instruments." JASA 150.
- Schwär et al. (2026). "Differentiable Pulsetable Synthesis for Wind Instrument Modeling." ICASSP 2026.
- Finnendahl et al. (2025). "Differentiable Geometric Acoustic Path Tracing using Time-Resolved Path Replay Backpropagation." ACM TOG / SIGGRAPH 2025.
- Jüterbock et al. (2026). "misuka: An open-source differentiable room acoustic renderer." Proc. Meetings on Acoustics 58.
- Borrel-Jensen & Bjorgaard (2025). "Differentiation Strategies for Acoustic Inverse Problems." arXiv:2511.11415.
- Luan, Yokota & Scavone (2025). "Acoustic field reconstruction in tubes via PINNs." Forum Acusticum.
- Mignot, Hélie & Matignon (2009). "State-space representation for digital waveguide networks of lossy flared acoustic pipes."

### Open Source Code
- jaxdiffmodal: https://github.com/rodrigodzf/jaxdiffmodal
- DiffSound: https://github.com/TechnetiumMan/DiffSound
- j-Wave: https://github.com/ucl-bug/jwave
- misuka: https://github.com/misuka-renderer/misuka
- OpenWInD (FWI): Referenced in Ernoult et al. 2021
- magpie-python: https://github.com/Nemus-Project/magpie-python
- VKPlate: https://github.com/Nemus-Project/VKPlate

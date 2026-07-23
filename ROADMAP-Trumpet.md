# Trumpet Design Roadmap

## Current Status

### Branches
- `experiment/trumpet-openwind` (active) - OpenWind FEM approach
- `experiment/trumpet-custom-tmm` - Custom TMM approach (deprecated for trumpets)

### Completed
- [x] Research literature on trumpet acoustics and optimization
- [x] Create OpenWind-based trumpet model with valve combinations
- [x] Implement impedance computation for 8 valve combinations
- [x] Resonance peak detection and playing frequency extraction

### In Progress
- [ ] Tune bore geometry to match Bb trumpet frequencies
- [ ] Optimize leadpipe for intonation (6 variables)
- [ ] Benchmark against professional trumpets (Bach 180ML, Yamaha Xeno)

---

## Approach Comparison

### 1. OpenWind FEM (Current - Recommended)
**Pros:**
- Accurate 1D FEM with visco-thermal losses
- Proper bell radiation conditions
- Valve junction physics with acoustic reactances
- Already installed, well-documented
- GPL-v3, open source

**Cons:**
- Slower than TMM (~100ms per impedance computation)
- Limited to 1D (no 2D/3D effects)

**Implementation:**
- `backend/trumpet_openwind.py`
- Uses `openwind.ImpedanceComputation` with valve definitions
- Resonance peak detection from impedance magnitude

### 2. Custom TMM (Deprecated for Trumpets)
**Pros:**
- Very fast (~1ms per computation)
- Same engine as woodwind optimization

**Cons:**
- TMM uses approximate "equivalent radius" for conical sections with losses
- Not accurate for trumpet bell flare (rapid expansion)
- Missing proper radiation impedance

**Implementation:**
- `backend/trumpet_acoustics.py`
- Phase-based resonance computation
- Known issues: harmonics not aligned (2.33x instead of 3.0x)

**Decision:** Deprecated for trumpets due to accuracy limitations. Kept as reference.

### 3. Yamaha/ML Approach (Future - Advanced)
**Pros:**
- State-of-the-art accuracy (0.305 cent RMSE)
- Optimized leadpipe manufactured by Yamaha
- Bi-objective optimization (intonation + ease of playing)

**Cons:**
- Requires ML training (1000+ simulations)
- Complex 5-stage pipeline
- Needs compute resources for training
- Requires physical model with lip-bore coupling

**Implementation Requirements:**
- Physics-based sound simulation (harmonic balance)
- ML model training (Elastic Net / Random Forest)
- NSGA-II multi-objective optimization
- Bore reconstruction from impedance

**Reference:** Petiot et al. (2024-2025), Yamaha Corporation

---

## Future Directions

### Phase 1: Basic Trumpet Optimization (Current)
- [ ] Tune bore geometry for correct Bb3 fundamental
- [ ] Optimize leadpipe shape (5 diameters + 1 length)
- [ ] Minimize RMS intonation error across chromatic scale
- [ ] Benchmark against professional instruments

### Phase 2: Advanced Acoustics
- [ ] Add mouthpiece modeling (cup volume, throat diameter)
- [ ] Include bell wall vibration effects (timbre)
- [ ] Model nonlinear propagation (high dynamics)
- [ ] Add temperature gradient effects

### Phase 3: ML-Assisted Optimization (Yamaha Approach)
- [ ] Implement physics-based sound simulation
- [ ] Train ML model on impedance parameters
- [ ] Bi-objective optimization (intonation + threshold pressure)
- [ ] Bore reconstruction from optimal impedance
- [ ] Physical prototyping and testing

### Phase 4: 3D Printing Integration
- [ ] Export optimized bore to STL (CadQuery/FreeCAD)
- [ ] Material considerations (brass vs composite)
- [ ] Wall thickness optimization for bell vibrations
- [ ] Design for additive manufacturing (DfAM)

---

## Key Parameters

### Trumpet Bore Dimensions
- **Leadpipe:** 200mm, tapers from 14.5mm to 12mm
- **Central bore:** 400mm, cylindrical 12mm (ML size)
- **Bell flare:** 370mm, Bessel horn to 127mm rim
- **Total length:** ~970mm (acoustic length for Bb3)

### Valve Tube Lengths (Bb Trumpet)
- **Valve 1:** 160mm (whole tone down)
- **Valve 2:** 70mm (semitone down)
- **Valve 3:** 270mm (minor third down)
- **Net additions:** 140mm, 60mm, 250mm (after subtracting straight path)

### Optimization Variables (Petiot's Approach)
- **d1-d5:** Leadpipe diameters at 5 positions (mm)
- **L:** Leadpipe length (m)
- **Total:** 6 variables (much simpler than woodwind's 30-50+)

### Intonation Targets
- **Professional:** ±5 cents RMS
- **Student:** ±15 cents RMS
- **Current model:** ~200 cents (needs tuning)

---

## Literature References

1. **Petiot et al. (2024-2025)** - ML + physics-based optimization, Yamaha prototype
2. **Tournemenne et al. (2016-2019)** - MADS optimization, 99% improvement
3. **Fréour et al. (2020)** - Numerical continuation, trumpet comparisons
4. **Gibson et al. (2017)** - 3D printed composite trumpets
5. **OpenWind (INRIA)** - FEM-based acoustic simulation

---

## Notes

- **Trumpet is simpler than woodwind:** 6 variables vs 30-50+
- **Leadpipe is critical:** Determines intonation and ease of playing
- **Bell affects timbre:** Wall vibrations change sound quality
- **Valves are parallel tubes:** Not serial insertion (common mistake)
- **Overblowing jumps by octaves:** Bell makes harmonics 1:2:3:4:5...

---

## Next Actions

1. **Tune bore geometry** to get Bb3 fundamental (233 Hz)
2. **Run L-BFGS-B optimization** on leadpipe (6 variables)
3. **Benchmark against Bach 180ML** measurements
4. **Update roadmap** with progress

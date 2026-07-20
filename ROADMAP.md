# Roadmap: Instrument Designer

## Completed
- [x] Bore optimization with pymoo + OpenWInD (basic)
- [x] Impedance solver resolution fix (800 → 5000 points)
- [x] Quadratic interpolation for peak finding
- [x] Impedance caching for repeated evaluations
- [x] Intonation accuracy research (documented in chat-logs/2026-07-18)

## High Priority — Next Sessions

### Optimizer Improvements
- [ ] Reduce optimizer time (currently ~hours for 100 gen × 50 pop)
  - Consider reducing pop_size or generations for quick iterations
  - Add progress callback to track convergence
  - Test with smaller target set (4 notes) first
- [ ] Add global pitch offset correction (shift all peaks by constant cents offset)
- [ ] Improve scale evenness objective (currently std of diffs, consider musical intervals)
- [ ] Add support for clarinet odd-harmonic tuning (every other peak)

### Bore Representation
- [ ] Test with more control points (12 → 20-30 for complex profiles)
- [ ] Add smooth bore constraint (penalize large radius jumps between points)
- [ ] Support for bore taper types (cylindrical, conical, parabolic)

### Validation
- [ ] Compare optimizer output to known good bore profiles
- [ ] Test with Noreland's clarinet target frequencies
- [ ] Verify <10 cents accuracy on synthetic targets

## Medium Priority — After Core Works

### 3D Print Integration
- [ ] Add material shrinkage compensation (per-material calibration)
- [ ] Export bore profile as STL for 3D printing
- [ ] Add bore measurement import (from caliper/micrometer readings)
- [ ] Support for SLA resin settings (layer height, exposure)

### Measurement Loop
- [ ] Import measured impedance data from real instruments
- [ ] Compare designed vs measured bore profiles
- [ ] Iterative correction: measure → optimize → print → measure

### GUI Enhancements
- [ ] Real-time bore profile visualization during optimization
- [ ] Impedance peak display with target frequencies overlay
- [ ] Export optimization history (convergence plots)
- [ ] Bore profile editor (drag control points)

## Low Priority — Future

### Advanced Acoustics
- [ ] Temperature sensitivity analysis (±X cents per °C)
- [ ] Vocal tract coupling simulation
- [ ] Reed/mouthpiece impedance modeling
- [ ] Multi-register optimization (clarinet twelfths)

### Manufacturing
- [ ] Hybrid approach: 3D print mold → cast final instrument
- [ ] CNC reamer profile export
- [ ] Bore straightness verification (warping detection)

### Research
- [ ] Compare FDM vs SLA acoustic performance
- [ ] Document optimal print settings for musical instruments
- [ ] Publish accuracy benchmarks

---

*Last updated: 2026-07-18*

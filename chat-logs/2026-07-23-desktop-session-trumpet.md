# Desktop Session Log — 2026-07-23 (Trumpet OpenWind + Comms Setup)

## Summary
- Created OpenWind-based trumpet model (branch: experiment/trumpet-openwind)
- Created trumpet design roadmap (ROADMAP-Trumpet.md)
- Set up LAN chat server on port 9123
- Created GitHub Issue #15: Backup Communication Channel
- Bore geometry tuning in progress

---

## Trumpet OpenWind Model (COMPLETED)

### What was built:
- `backend/trumpet_openwind.py` — Full OpenWind FEM trumpet model
- Uses OpenWind's `ImpedanceComputation` with valve deviation pipes
- Computes impedance for all 8 valve combinations (open, 1, 2, 1+2, 3, 2+3, 1+3, 1+2+3)
- Resonance peak detection from impedance magnitude
- `TrumpetBore` dataclass with bore profile, valves, fingering chart
- `TrumpetBore.default_bb()` — default Bb trumpet geometry
- `TrumpetBore.from_leadpipe_profile()` — parametric bore from 5 diameters (Petiot's approach)
- `TrumpetOpenWind.played_frequencies()` — returns playing freqs for each valve combo
- `TrumpetOpenWind.find_resonances()` — finds N strongest resonance peaks
- `TrumpetOpenWind.compute_impedance()` — full impedance curve
- `TrumpetOpenWind.plot_impedance()` — matplotlib visualization

### Commits:
- `a6d3c6e` — Initial trumpet TMM model (deprecated for trumpets)
- `e9761c7` — OpenWind-based trumpet model (the working one)
- `c121fc2` — Trumpet design roadmap
- `de37c16` — Sleep mode fix message for laptop
- `b977e41` — .gitignore cleanup + ROADMAP update

### Key API discoveries:
- OpenWind uses `note=` parameter (not `fingering=`) for fingering selection
- `ImpedanceComputation` attribute is `.impedance` (not `.Z`)
- Valve format: `['valve', 'label', 'position', 'reconnection', 'radius', 'length']`
- Fingering chart: `[['label', 'open', '2', ...], ['piston1', 'o', 'x', ...], ...]`
- OpenWind v0.12.4 installed via pip (INRIA, GPL-v3)

---

## Trumpet Bore Tuning (IN PROGRESS)

### Current status:
- Default bore gives C#4 (279 Hz) instead of Bb3 (233 Hz) — ~2 semitones sharp
- Scaled bore (×1.202) brings H2 to 232 Hz (correct!) but harmonics not aligned
- Harmonic ratios stuck at ~3:5:7 (closed pipe) instead of ~2:3:4 (trumpet)
- Bell flare adjustment barely changes ratios

### Root cause analysis:
- Bore geometry is fundamentally wrong for trumpet acoustics
- Real trumpet bell must be much more aggressive to compress harmonics
- Bessel horn with current parameters doesn't produce trumpet-like harmonic alignment
- Need to either: (a) find correct bell shape, (b) use OpenWind's own trumpet geometry, or (c) measure a real trumpet

### What I tested:
1. Scaled bore ×1.202 → H2=232 Hz (correct pitch) but ratios 3:5:7
2. Bell factor 0.8-1.5 → barely changes ratios
3. Bessel exponent 0.3-2.0 → minimal effect on harmonic compression
4. Aggressive bell (5.8mm→63.5mm in 470mm) → completely wrong (ratios 0.4:1:1.3:1.9)

### Next steps for bore tuning:
1. Find real trumpet bore profile (Piatt thesis measurements)
2. Try OpenWind's own trumpet example geometry
3. Use measured Bach 180ML dimensions
4. Consider: the issue might be the closed-open pipe convention in OpenWind

---

## Communication Setup

### LAN Chat:
- Server running on port 9123 (background process)
- Laptop responsive via LAN chat (ACKs working)
- File: `backend/lan_chat.py`

### GitHub Issues:
- Issue #15: BACKUP COMMS — Desktop/Laptop Communication Channel
- Used when Tailscale/LAN chat goes down

### Laptop status:
- Last active: 14:42 UTC (commit a13a55b)
- Working on: hole diameter optimization, tin whistle, recorder
- Branch: experiment/bore-profile-optimization
- All 7 instruments sub-1c RMS

---

## Research Findings to Share

### Trumpet acoustics:
- Trumpet is much simpler than woodwind: no tone holes, just bore profile + 8 valve combinations
- Leadpipe is THE critical design element (Petiot 2025)
- OpenWind FEM > custom TMM for brass (Tournemenne & Chabassier 2019)
- Bell flare harmonics: ideal trumpet ~1:2:3:4:5:6 (vs closed pipe 1:3:5:7:9:11)
- Yamaha ML approach: 5-stage pipeline, 0.305 cent RMSE, too complex for now
- Bessel horn: d(x) = d0 * (1 + (x/L)^2)^(p/2), p controls flare rate

### Key references:
- Petiot et al. (2025) — ML + physics, Yamaha prototype
- Tournemenne et al. (2016-2019) — MADS optimization, 99% improvement
- Piatt WVU thesis — Professional trumpet component specs
- OpenWind docs: https://files.inria.fr/openwind/docs/
- OpenBrass: https://www.openbrass.org — 3D printed trumpet designs

---

## Files Modified
- `backend/trumpet_openwind.py` — NEW: OpenWind trumpet model (558 lines)
- `backend/trumpet_acoustics.py` — NEW: Custom TMM trumpet model (deprecated)
- `ROADMAP-Trumpet.md` — NEW: Trumpet design roadmap
- `ROADMAP.md` — Updated with trumpet branch options
- `.gitignore` — Added JDK, logs, zip files
- `MSG-FROM-DESKTOP.md` — Sleep mode fix for laptop
- `test_trumpet_bell.py` — Bell geometry testing script

---

## Session Protocol (ONGOING)
1. Check in with laptop every ~2 minutes via LAN chat
2. Commit and push frequently
3. Share all findings with laptop
4. Post on GitHub issues
5. Save session logs to disk
6. Push chat logs to GitHub

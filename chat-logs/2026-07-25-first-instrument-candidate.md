# First Instrument Candidate: Baroque Flute
# Decision made 2026-07-25

## Why Baroque Flute

**Best single-source dataset available:** Wolfe/UNSW Music Acoustics database
- https://phys.unsw.edu.au/music/flute/

### What's Available
| Data Type | Available | Details |
|-----------|-----------|---------|
| Bore geometry | ✅ | Multiple historical instruments (Crone, Grenser, McGee replicas). Cylindrical head + conical body |
| Tone holes | ✅ | 6 finger holes + D# key. Positions & diameters documented |
| Impedance spectra | ✅ | Downloadable Excel files: |Z|, arg(Z), Re(Z), Im(Z) for every fingering |
| Sound recordings | ✅ | WAV files for all standard fingerings, recorded by Geoffrey Collins (professional flutist) |
| Sound spectra | ✅ | Harmonic spectra available |
| CT scan data | ⚠️ | Some museum instruments CT-scanned (Bressan recorder, Cerino flute) |
| OpenWInD support | ✅ | Flute examples included |
| demakein support | ✅ | Built-in flute designer |

### Geometry
- **Type:** Partially conical (cylindrical head + conical body)
- **Joints:** 4 sections
- **Holes:** 6 finger holes + 1 key (D#)
- **Register:** ~2.5 octaves
- **Excitation:** Fipple (whistle) mouthpiece — simpler than reed coupling

### Comparison with Other Candidates

| Instrument | Geometry | Holes | Impedance Data | Sound Samples | CT Scan |
|------------|----------|-------|----------------|---------------|---------|
| **Baroque Flute** | Partially conical | 7 | ✅ Full database | ✅ WAV all notes | ⚠️ Some |
| Bb Clarinet | Cylindrical | 17+ | ✅ Full database | ✅ WAV all notes | ⚠️ Limited |
| Tin Whistle | Cylindrical | 6 | ⚠️ Modeled only | ⚠️ Spectra only | ❌ None |
| Renaissance Recorder | Conical | 8 | ⚠️ Limited | ⚠️ Tuning only | ✅ CT available |
| Native Am. Flute | Cylindrical | 6 | ⚠️ Modeled only | ⚠️ Limited | ❌ None |
| Pan Flute | Independent pipes | 0 | ⚠️ Limited | ⚠️ Limited | ⚠️ Some |

### Why Not Clarinet?
- Clarinet is equally well-documented but has 17+ tone holes → more complex to model first
- Reed coupling is more complex than fipple excitation
- Clarinet operates at impedance MAXIMA (odd harmonics only), flute at minima → different physics
- Better to validate with simpler geometry first, then tackle clarinet as second instrument

### Why Not Tin Whistle?
- Simplest geometry (straight cylinder, 6 holes)
- But NO measured impedance data — only acoustic models
- No CT scan data
- demakein already has a working whistle designer (we'd be replicating, not validating)

### Validation Plan
1. Build TMM model of baroque flute from Wolfe measurements
2. Compute impedance spectra → compare with Wolfe's measured impedance data
3. This validates the TMM engine against REAL data (not self-evaluation)
4. Then: optimize bore/holes to match measured instrument's intonation
5. Then: compare optimized vs measured spectral envelope (timbre)
6. Finally: add timbre objectives to optimizer

### Data Sources
- **Primary:** https://phys.unsw.edu.au/music/flute/ (impedance + sound)
- **Secondary:** Wolfe JASA papers on cross-fingering
- **Tertiary:** demakein flute presets, OpenWInD examples
- **Bore profiles:** Measured from historical instruments, published in JASA papers

---

## Second Instrument (Future): Bb Clarinet

### Why Clarinet as Second
- Nearly as complete dataset (Wolfe/UNSW)
- Different excitation mechanism (reed vs fipple) → validates different physics
- Cylindrical bore → simpler TMM (constant cross-section)
- Operates at impedance maxima (odd harmonics) → complementary to flute
- Our existing TMM engine already has clarinet-specific code (reed tube, register hole)

### Data Available
- Yamaha Custom Bb bore measurements
- Full fingering chart with impedance for every note
- Sound recordings for every standard fingering (E3–C#7)
- OpenWInD support

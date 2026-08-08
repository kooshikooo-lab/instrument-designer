# Chalumier Research - 2026-07-20

## 1. Overview

**Chalumier** is a Kotlin rewrite/rewrite of **Demakein** (DEsign and MAke INstruments), an acoustic woodwind instrument design tool. It was created by **Mark Chu-Carroll** (GitHub: MarkChuCarroll, blog: goodmath.org, works at Spotify as PhD computer scientist).

The project performs acoustic analysis and optimization to produce the profile and hole sizes for acoustic woodwind instruments, including conic flutes, straight-bore flutes, double-reeds, end-blown flutes, and tinwhistles.

Mark is a clarinetist whose eventual goal is to design a modern 3D-printable basset horn using this software.

---

## 2. Repository Information

### Primary Repo
- **URL**: https://github.com/MarkChuCarroll/chalumier
- **Language**: Kotlin (100%)
- **License**: Apache-2.0
- **Stars**: 6 | **Forks**: 2 | **Watchers**: 1
- **Commits**: 25 (on `main` branch)
- **Status**: Active development, CLI tool still work-in-progress
- **No releases published** (no pre-built JARs available)
- **No GitHub Actions CI/CD configured**

### Related Repos by Mark Chu-Carroll
- https://github.com/MarkChuCarroll/instruments - OpenSCAD models of musical instruments (tenor clarinet), 34 commits, 1 release (tenor-3.0)
- https://github.com/MarkChuCarroll/simplex - Programming language for building 3D printable models (Kotlin)
- https://github.com/MarkChuCarroll/pcomb - Parser combinator library for Java

---

## 3. Forks and Community Contributions

### Chalumier Forks
- **2 forks** listed on GitHub, but both appear inactive (no active forked repos found in the forks page with activity in the last 2 years)

### Demakein Forks (upstream project)
- https://github.com/pfh/demakein - Original demakein (48 stars, 9 forks, Python 3, v1.1 released July 2025)
- https://github.com/ajwitchger/woodwind3d - Fork of demakein (0 stars, 0 forks)

### Community Contributions to Demakein Ecosystem
- **Thingiverse designs** by Paul Harrison: http://www.thingiverse.com/pfh/things
- **Maker World** re-uploads by Romansax: https://makerworld.com/en/models/1230415-folk-flutes-by-pfh-original-and-remixed

---

## 4. Author's Blog/Articles

- **Good Math/Bad Math** (Mark's blog): http://www.goodmath.org/blog/
  - No dedicated blog posts found specifically about Chalumier on the blog. The primary documentation is the GitHub README.
- **Paul Harrison's Demakein page**: http://www.logarithmic.net/pfh/design
  - Blog post "Announcing Demakein": http://www.logarithmic.net/pfh/blog/01349179196
- **Reddit thread about the name "chalumier"**: https://www.reddit.com/r/fantasywriters/comments/1e69c2/whats_a_cool_sounding_word_for_a_maker_of_musical/
  - Mark found the name "chalumier" (proposed as a woodwind-maker equivalent to "luthier") in this thread

---

## 5. Instrument Design Files (.chal format)

### Examples in the Chalumier Repo
Located at: https://github.com/MarkChuCarroll/chalumier/tree/main/examples

| File | Instrument Type | URL |
|------|----------------|-----|
| `dmajor-folk-flute.chal` | Folk Flute (D major, 7 holes) | https://github.com/MarkChuCarroll/chalumier/blob/main/examples/dmajor-folk-flute.chal |
| `dwhistle.chal` | Pennywhistle (D, 6 holes) | https://github.com/MarkChuCarroll/chalumier/blob/main/examples/dwhistle.chal |
| `eminor-7hole-flute.chal` | 7-hole chromatic flute (E minor, 8 holes) | https://github.com/MarkChuCarroll/chalumier/blob/main/examples/eminor-7hole-flute.chal |
| `folkshawm.chal` | Folk Shawm (7 holes, closed top) | https://github.com/MarkChuCarroll/chalumier/blob/main/examples/folkshawm.chal |
| `simple-shawm.chal` | Simple Shawm (minimal spec) | https://github.com/MarkChuCarroll/chalumier/blob/main/examples/simple-shawm.chal |
| `recorder.chal` | Recorder (8 holes, open top) | https://github.com/MarkChuCarroll/chalumier/blob/main/examples/recorder.chal |
| `d-flute-with-crossfingerings.json5` | D flute with cross-fingerings (JSON5 format) | https://github.com/MarkChuCarroll/chalumier/blob/main/examples/d-flute-with-crossfingerings.json5 |

### Additional Instrument Specs (in test resources)
The README mentions additional examples at: `app/src/test/resources/`

---

## 6. .chal File Format Specification

The `.chal` format is a custom Kotlin/JSON-like specification format. Based on analysis of the examples, here is the format:

### Structure
```
instrumentType {
    // Comments start with #
    fieldName = value,
    fieldName = value,
    ...
}
```

### Supported Instrument Types
- `folkFlute` - Folk flute (open top)
- `folkWhistle` - Pennywhistle
- `folkShawm` - Folk shawm (closed top)
- `recorder` - Recorder-style instrument

### Key Fields (documented in folkshawm.chal)

#### Basic Properties
- `name` (String) - Name of the instrument
- `rootNote` (String?, optional) - Root note (e.g., "D4", "C4")
- `numberOfHoles` (Int) - Number of finger holes including embouchure
- `closedTop` (Boolean) - Is this a closed top instrument?
- `transpose` (Int) - Transposition in chromatic steps
- `scale` (Double) - Scaling factor
- `length` (Double) - Length of the instrument in mm

#### Fingering Specification
- `fingerings` (List<Fingering>) - List of fingering specs:
  ```
  { noteName="C4", fingers=["X", "X", "X", ...], nth=1 }
  ```
  - `noteName`: Note to produce (e.g., "D4", "F#4", "Bb4")
  - `fingers`: Array of "X" (closed) or "O" (open) for each hole
  - `nth` (optional): Which harmonic/overblown register (1=fundamental, 2=1st overblown, etc.)

#### Bore Geometry
- `bore` (Double) - Bore diameter at top (reed diameter)
- `innerDiameters` (List<Pair<Double,Double>>) - Piecewise linear bore profile, from bottom to top
- `innerAngles` (List<Pair<Angle,Angle>?>) - Angle descriptions for bore contours
- `initialInnerFractions` (List<Double>) - Initial positions of kinks as fractions of bore length
- `minInnerSep` / `maxInnerSep` - Constraints on bore diameter changes
- `minInnerFractionSep` / `maxInnerFractionSep` - Fraction-based bore segment constraints
- `boreScale` (Double) - Scaling factor for bore diameters
- `coneStep` (Double) - Step size for translating conic sections to curves

#### Outer Body
- `outerDiameters` (List<Pair<Double,Double>>) - Outer body diameters, bottom to top
- `outerAngles` (List<Pair<Angle,Angle>?>) - Angle descriptions for outer contours
- `initialOuterFractions` (List<Double>) - Initial positions of kinks in body shape
- `outerAdd` (Boolean) - Should body thickness be automatically increased?
- `dilate` (Double) - Dilate the body by this amount
- `minOuterFractionSep` / `maxOuterFractionSep` - Outer segment constraints

#### Hole Configuration
- `minHoleDiameters` (List<Double>) - Minimum acceptable hole diameters
- `maxHoleDiameters` (List<Double>) - Maximum acceptable hole diameters
- `minHoleSpacing` (List<Double?>) - Minimum spacing between pairs of holes
- `maxHoleSpacing` (List<Double?>) - Maximum spacing between pairs of holes
- `holeAngles` (List<Double>) - Vertical angle of each hole
- `holeHorizAngles` (List<Double>) - Horizontal angle offsets for each hole
- `balance` (List<Double?>) - Spacing similarity constraints for triplets of holes
- `bottomClearanceFraction` (Double) - How close to bottom holes can be placed
- `topClearanceFraction` (Double) - How close to top holes can be placed

#### Reed/Whistle Parameters
- `reedVirtualTop` (Double) - Virtual diameter of reed top, proportion of bore diameter
- `reedVirtualLength` (Double) - Virtual length of reed as multiple of bore diameter

#### 3D Model Parameters
- `decorate` (Boolean) - Add embellishments to the body?
- `addBauble` (Boolean) - Add a decorative bauble?
- `generatePads` (Boolean) - Generate pads around holes?
- `thickSockets` (Boolean) - Make body thicker around socket joins?
- `dock` (Boolean) - Enable dock feature?
- `dockBottom` (Double) - Dock bottom position
- `dockTop` (Double) - Dock top position
- `dockDiameter` (Double) - Dock diameter
- `dockLength` (Double) - Dock length
- `gap` (Double) - Gap size between sockets
- `join` (String) - Join type: "StraightJoin", "WeldJoin", or "TaperedJoin"
- `divisions` (List<List<Pair<Int,Double>>>) - How to split into printable pieces
- `xPad` / `yPad` (Double) - Padding for 3D model

#### Experimental
- `tweakEmissions` (Double) - Experimental term to make instrument louder (possibly at cost of intonation)
- `tweakBoreLess` (Double) - (recorder-specific)
- `tweakGapExtra` (Double) - (recorder-specific)
- `maxLength` (Double?, optional) - Maximum instrument length during modeling
- `initialLength` (Double) - Initial length before modeling (recorder)
- `initialHoleFractions` (List<Double>) - Initial hole positions (recorder)
- `initialHoleDiameterFractions` (List<Double>) - Initial hole sizes (recorder)

### JSON5 Format Support
The project also supports `.json5` format for instrument specifications (see `d-flute-with-crossfingerings.json5`), which is standard JSON with comments and trailing commas allowed.

---

## 7. Build Instructions

### Prerequisites
- JDK (Java Development Kit)
- Gradle (included via `gradlew` / `gradlew.bat`)

### Build Steps
```bash
# Clone the repository
git clone https://github.com/MarkChuCarroll/chalumier.git
cd chalumier

# Build and test
./gradlew build          # Linux/macOS
gradlew.bat build        # Windows

# Create executable JAR
./gradlew shadowJar      # Linux/macOS
gradlew.bat shadowJar    # Windows

# JAR output location
# ./app/build/libs/chalumier-<<<VERSION>>>.jar
```

### Running
```bash
# Design an instrument
java -jar chalumier.jar design --output-dir <output_dir> <instrument_file.chal>

# Generate 3D model
java -jar chalumier.jar model --output-dir <output_dir> <parameters.json>
```

### Output Files
- `<instrument>-design.svg` - Diagram showing design and intonation accuracy
- `<instrument>-parameters.json` - Machine-readable model data

---

## 8. Pre-built JARs

**None available.** The repository has no releases published and no CI/CD pipeline. You must build from source.

---

## 9. Chalumier vs Demakein Comparison

| Feature | Chalumier (Kotlin) | Demakein (Python) |
|---------|-------------------|-------------------|
| **Language** | Kotlin | Python 2.7 (original) / Python 3 (v1.1) |
| **License** | Apache-2.0 | LGPL-2.1 |
| **Input Format** | .chal specification files (declarative) | Python scripts (imperative) |
| **Dependencies** | JDK + Gradle | Python 2.7 + Nesoni (original) / Python 3 + PyPy (v1.1) |
| **Performance** | ~5 min (simple major flute) | ~20 min (simple major flute) |
| **Complex Models** | ~10 min (B-minor flute with cross-fingerings) | 3+ days without completing (same model) |
| **3D Modeling** | In progress (design + model commands) | Full pipeline (design + make) |
| **CNC Milling** | Not yet implemented | Full support |
| **Instrument Types** | folkFlute, folkWhistle, folkShawm, recorder | Flutes, whistles, shawms, reedpipes |
| **Documentation** | README + inline .chal comments | Minimal |
| **Output** | SVG diagrams + JSON parameters | STL files for 3D printing + milling |
| **Extensibility** | Via .chal files (declarative) | Via Python subclassing (code) |
| **Community** | 6 stars, 2 forks | 48 stars, 9 forks |
| **Maturity** | Early stage (WIP CLI) | Mature (v1.1, PyPI package) |
| **Nesoni Dependency** | Eliminated (replaced with Kotlin coroutines) | Required (parallel computation framework) |

### Key Chalumier Improvements Over Demakein
1. **No Python 2.7 dependency** - Runs on modern JDK
2. **No Nesoni dependency** - Replaced with Kotlin coroutines
3. **Declarative instrument specification** - .chal files instead of Python scripts
4. **4x faster** on simple models, orders of magnitude faster on complex models
5. **Better documentation** - Inline comments in .chal files explain every field
6. **Bug fixes** - Fixed overlapping holes, incorrect intonation reporting
7. **Progress feedback** - Not yet fully implemented but planned

### What Demakein Still Has That Chalumier Lacks
1. **3D model generation** (STL output for 3D printing)
2. **CNC milling support**
3. **Mature "make" phase** (Chalumier only has "design" + WIP "model")
4. **PyPI package** (easy installation)
5. **Larger community** and more pre-built designs on Thingiverse

---

## 10. Similar Java/Kotlin Woodwind Design Tools

### Direct Related Tools
- **Demakein** (Python): https://github.com/pfh/demakein - The original, most mature option
- **woodwind3d** (Python): https://github.com/ajwitchger/woodwind3d - Fork of demakein

### Academic/Research
- **Woodwind instrument design optimization based on impedance characteristics** (2020):
  - https://hal.science/hal-02479433v2/file/Main_article_optimisation_4.0.pdf
  - Research paper on optimization-based woodwind design with geometric constraints
- **CCRMA Woodwind Modeling** (Stanford): https://ccrma.stanford.edu/~jos/tonehole/
  - Real-time computer modeling of woodwind instruments (C++, not a design tool)

### No other Java/Kotlin-specific woodwind instrument design tools were found.

---

## 11. Community Shared Instrument Design Files

### From Paul Harrison (Demakein Author)
- **Thingiverse**: http://www.thingiverse.com/pfh/things
  - Folk flutes in tenor, alto, and soprano (8 sizes)
  - Various shawm designs
  - Whistle designs
- **Maker World** (re-uploads by Romansax): https://makerworld.com/en/models/1230415-folk-flutes-by-pfh-original-and-remixed
- **Shapeways**: http://www.shapeways.com/designer/paul_harrison

### From Mark Chu-Carroll
- **OpenSCAD models**: https://github.com/MarkChuCarroll/instruments
  - Tenor clarinet models (3D printable)
  - Release: tenor-3.0 (Nov 2025)

### No community-shared .chal files were found outside the official repo.

---

## 12. Compatibility Notes

### Platform
- Cross-platform (any system with JDK): Windows, macOS, Linux
- Gradle wrapper included (`gradlew` for Unix, `gradlew.bat` for Windows)

### JDK Requirements
- Not explicitly specified in the README; likely requires JDK 11+ based on Kotlin/JVM targets
- Gradle Kotlin DSL is used (`settings.gradle.kts`, `build.gradle.kts`)

### Demakein Compatibility
- Chalumier's .chal format is NOT compatible with demakein's Python script format
- Chalumier reads/writes JSON parameters that may be partially compatible with demakein's pipeline
- The optimization algorithms are inspired by demakein but rewritten/refactored

### 3D Printer Compatibility
- Chalumier does not yet generate STL files (design phase only as of July 2026)
- Demakein supports STL generation for FDM/SLA 3D printers and CNC milling
- For printing, you would need to use demakein's "make" phase or write your own tool to convert Chalumier's JSON output to STL

---

## 13. Key Links Summary

| Resource | URL |
|----------|-----|
| Chalumier repo | https://github.com/MarkChuCarroll/chalumier |
| Demakein repo | https://github.com/pfh/demakein |
| Demakein homepage | http://www.logarithmic.net/pfh/design |
| Demakein on PyPI | https://pypi.org/project/demakein/ |
| Demakein blog announcement | http://www.logarithmic.net/pfh/blog/01349179196 |
| Mark's blog | http://www.goodmath.org/blog/ |
| Mark's GitHub | https://github.com/MarkChuCarroll |
| Instruments repo (OpenSCAD) | https://github.com/MarkChuCarroll/instruments |
| Thingiverse designs | http://www.thingiverse.com/pfh/things |
| Maker World remixed flutes | https://makerworld.com/en/models/1230415 |
| woodwind3d fork | https://github.com/ajwitchger/woodwind3d |
| Name origin (Reddit) | https://www.reddit.com/r/fantasywriters/comments/1e69c2/ |
| Woodwind design optimization paper | https://hal.science/hal-02479433v2/file/Main_article_optimisation_4.0.pdf |
| CCRMA woodwind modeling | https://ccrma.stanford.edu/~jos/tonehole/ |

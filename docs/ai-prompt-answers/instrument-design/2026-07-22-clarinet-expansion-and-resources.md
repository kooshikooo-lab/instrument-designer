# Chat Log: 2026-07-22 — Clarinet Family Expansion + Academic Resources

## Session Goal
Add chalumier TMM instruments, baroque clarinet, folk music clarinets to the instrument library, and add academic/computational resources to `instrument-resources.ts`.

## What Was Done

### 1. New Instruments Added to `instruments.ts` (7 new entries)

| Instrument | Key | Source | Difficulty |
|---|---|---|---|
| Chalumier TMM Bb Clarinet | Bb | Chalumier Design Engine | Advanced |
| Chalumier TMM Bass Clarinet in G | G | Chalumier Design Engine | Expert |
| Pocket Clarinet / Chalumeau | Bb | Thingiverse thing:3834802 | Intermediate |
| Keyless Clarinet in Bb | Bb | MakerWorld (Ialohrr) | Intermediate |
| JDWoodwinds Piccolo Clarinet in A | A | JDWoodwinds | Expert |
| Baroque Clarinet (2-Key Denner) | D | Historical / YouTube | Advanced |

Plus Bromiophone resources added (was missing from `instrument-resources.ts`).

### 2. DEMAKEIN_PRESET_GROUPS Updated
- Clarinet group now has 3 presets: Chalumier TMM Bb, Chalumier TMM Bass G, Baroque Clarinet (2-Key Denner)

### 3. `instrument-resources.ts` — New Exports Added

**`COMPUTATIONAL_ACOUSTICS_RESOURCES`** (24 links):
- Chalumier, OpenWInD, WIDesigner, Flutomat NG, hotair, Flutes.jl, Demakein
- Neuralacoustics (Chalmers), MIT FDTD, Stanford CNO
- Lefebvre PhD (McGill), Noreland (2013), Ernoult (2020)
- Tournemenne/Chabassier (2019), Szwarcberg (2024), Petiot (2025)
- Yamamoto (2025), Wolfe (2018), ArtisanClarinets, Syos
- PINNs (Luan 2025), Differentiable Acoustic Inverse, ISMIR 2025

**`VERIFIED_PROJECT_RESOURCES`** (15 links):
- JDWoodwinds, Lowa, Atomica, Strawboe, PrintBone, Bromiophone
- Afflato, GT Instruments, Glissonic, Nicolas Bras/BY BRAS
- Flutopedia, Paul Harrison/Demakein, LoweWa, Wolfe Lab, Bate Collection

### 4. Research Sources Consulted
- Printables, MakerWorld, Thingiverse, Cults3D for 3D-printable clarinets
- Afflato.com — professional 3D-printed historical chalumeaux and classical clarinets
- GT Instruments (Grzegorz Tomaszewicz) — handmade baroque chalumeaux
- JDWoodwinds — STL files for piccolo clarinet, bass clarinet, bass oboe
- YouTube — "3D Printed Baroque Clarinet!" (2026-04-13)
- Reddit r/3dprintedinstruments — pocket clarinet / chalumeau discussion
- Britannica — chalumeau history

## Key Findings

### Clarinet Family Taxonomy
- **Chalumeau** (17th-18th c.) — stopped pipe, doesn't overblow, 2 keys (Denner c.1700)
- **Baroque Clarinet** (c.1700) — added register key, overblows to 12th, earliest "clarinet"
- **Classical Clarinet** (c.1800) — 5-6 keys (Grenser/Baumann), Mozart era
- **Modern Clarinet** — 17+ keys, Boehm system
- **Pocket Clarinet** — modern compact version, Bb clarinet mouthpiece + short cylindrical bore

### 3D-Printed Clarinet Landscape
- Most are membrane clarinets or simplified keyless designs
- JDWoodwinds has the most complete printable clarinet (piccolo A, bass G)
- Afflato makes professional 3D-printed hand-finished historical instruments
- Our Chalumier TMM engine is unique in the landscape — computational bore optimization

## Files Modified
- `web/src/data/instruments.ts` — 7 new instruments + preset group update
- `web/src/data/instrument-resources.ts` — Resources for all new instruments + 2 new global exports

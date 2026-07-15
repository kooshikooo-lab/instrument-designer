# 3D Printed Brass Instruments Research
**Date:** 2026-07-15
**Researcher:** opencode (big-pickle)

## Overview

Research on 3D printed brass instruments (trumpet, trombone, bugle, euphonium, tuba), existing open-source designs, feasibility assessment, and difficulty evaluation for adding brass instruments to the instrument-designer library.

---

## 1. STATE OF 3D PRINTED BRASS INSTRUMENTS (2024-2026)

### 1.1 Existing Open-Source Designs

#### Working/Playable Designs Found:

**1. "Overly-Complicated Trumpet" (GCV3D, Printables 2024)**
- **Status:** Fully 3D printed, working prototype
- **Innovation:** Each of 6 valves moves a slide (trombone-style) instead of traditional rotary/piston valves
- **Bore:** Based on B-flat trumpet dimensions (13.7mm bore, ~1340mm total tubing)
- **Print time:** 55+ hours
- **Materials:** PLA, 610g filament
- **Printer:** Prusa i3 MK3/S/S+
- **Fingering:** Novel 6-valve system equivalent to standard 3-valve combinations
- **Limitations:** Still working on bell designs for better sound quality
- **Design software:** OnShape
- **Source:** https://www.printables.com/model/492588

**2. "PrusaPet Full Size Working Trumpet" (Rooster, Printables 2023)**
- **Status:** Full-size, working trumpet
- **Remixed:** Yes (original design modified)
- **Source:** https://www.printables.com/model/453005

**3. "The First FULLY PRINTED TROMBONE Prototype 1.10" (3DTLime, MakerWorld)**
- **Status:** Working prototype
- **Downloads:** 53, Likes: 55
- **Source:** MakerWorld

**4. "Fully Printable Alto Trombone" (JustinHirsh, MakerWorld)**
- **Status:** Working, fully printable
- **Downloads:** 904, Likes: 373
- **Source:** MakerWorld

**5. "Working Piccolo Trombone" (JustinHirsh, MakerWorld)**
- **Status:** Working
- **Downloads:** 12,200, Likes: 4,400 (most popular brass print)
- **Source:** MakerWorld

**6. "Piccolo Trombone Updated" (Lefebvre_3DP, MakerWorld)**
- **Status:** Updated working version
- **Downloads:** 262, Likes: 94
- **Source:** MakerWorld

**7. "Parametric Music Pipe Trumpet Trombone Bugle Clarinet" (CGTrader)**
- **Status:** Free parametric design
- **Type:** Simple pipe-based instruments (no valves)
- **Source:** CGTrader

**8. Trumpet Mouthpiece (OpenSCAD parametric)**
- **Status:** Working, parametric
- **Material:** ABS, 20% infill
- **Source:** STLFinder

#### Non-Working/Decorative Only:
- Mini trombone models (fidget toys, desk ornaments)
- Trombone Trumpet Mouthpiece (decorative)
- Various miniature/display models

### 1.2 Commercial 3D Printed Brass Products

**Limited commercial availability:**
- No major manufacturer producing fully 3D printed brass instruments
- Some 3D printed brass mouthpieces available (SYOS-style approach for woodwind mouthpieces proven)
- OHMI Trust has 3D printed accessories for brass instruments (stands, adaptive equipment)
- Trumpet Assist (solenoid-actuated valves with eye-gaze control) — 3D printed mounts

### 1.3 Academic Research

**Printone (Umetani et al., SIGGRAPH Asia 2016):**
- Interactive resonance simulation for free-form print-wind instrument design
- Uses boundary element method for fast resonance prediction
- Allows users to design arbitrary-shaped wind instruments
- Sound simulation during design process
- **Relevance:** Could be adapted for brass instrument design optimization

**"A pocket artificial buzzing system for the trumpet" (Acta Acustica 2024):**
- Studies lip-reed excitation mechanism for trumpet
- Relevant for understanding how brass instruments generate sound
- Lip buzz frequency couples with bore resonances

---

## 2. BRASS INSTRUMENT DESIGN FUNDAMENTALS

### 2.1 How Brass Instruments Work

**Excitation mechanism:**
- Player's lips buzz (lip reed) at the mouthpiece
- Buzz frequency interacts with bore resonances
- Player controls pitch by changing lip tension (not finger holes like woodwinds)
- Valve/slide changes effective tube length to select different resonance series

**Bore geometry:**
- **Cylindrical section:** Mouthpiece to valve section (most trumpets, trombones)
- **Conical section:** Valve section through bell (flares exponentially)
- **Bell:** Critical for radiation efficiency and impedance matching to air
- **Bore diameter:** ~11-13mm (trumpet), ~12-14mm (trombone), ~15-18mm (euphonium)

**Harmonic series:**
- Brass instruments produce odd AND even harmonics (unlike clarinet which produces mainly odd)
- Fundamental (pedal tone) is weak in trumpets — effectively starts from 2nd harmonic
- Harmonic series: f, 2f, 3f, 4f, 5f, 6f... where f = v/(2L)
- Valves/slide extend tube by known amounts to access different fundamentals

**Standard valve combinations (Bb trumpet):**
- Open (no valves): Bb1 fundamental
- 1st valve: -160mm (adds ~1 semitone)
- 2nd valve: -80mm (adds ~1/2 semitone)
- 3rd valve: -240mm (adds ~1.5 semitones)
- Combinations access full chromatic scale from Bb1 to ~F5

### 2.2 Key Challenges for 3D Printing Brass Instruments

#### Challenge 1: Valve Mechanism (HARD)
**Traditional brass valves:**
- **Piston valves:** Precision-machined metal pistons in metal cylinders
  - Tolerance: 0.01-0.02mm clearance
  - Requires smooth, round bore
  - Springs for return action
  - Water keys (spit valves) for condensation drainage
- **Rotary valves:** More complex, used in French horns
  - Even tighter tolerances
  - Complex linkage mechanism

**3D printed alternatives:**
1. **Slide mechanism (like "Overly-Complicated Trumpet"):**
   - Replaces valves with movable slides
   - Each slide extends/retracts by known amount
   - **Advantage:** No precision valve needed
   - **Disadvantage:** Slower note changes, requires more hand movement
   - **Tolerance needed:** 0.2-0.3mm clearance for smooth sliding
   - **Lubrication:** Silicone grease essential

2. **Solenoid-actuated valves:**
   - 3D printed mounts for solenoid motors over standard valve buttons
   - Eye-gaze or switch control for accessibility
   - **Does not replace valve mechanism** — just actuation method

3. **Print-in-place rotary valve:**
   - Theoretically possible with soluble supports
   - Tolerance requirements extremely demanding (0.05mm or less)
   - Current FDM printers cannot reliably achieve this
   - SLA/resin printing might work for small valves

4. **Diaphragm valves:**
   - Flexible membrane opens/closes air path
   - 3D printable with TPU or flexible filament
   - Simpler than piston valves
   - Less precise pitch control

#### Challenge 2: Tubing Bends (MODERATE)
**Traditional brass tubing:**
- Bent from straight brass tube using bending mandrel
- Smooth, continuous curves essential for good tone
- Any kinks or flattening in bends causes turbulence and pitch issues

**3D printing approach:**
- Print tubes in segments (straight + curved sections)
- **Curved sections:** Print in vertical orientation with supports
- **Support removal inside tube:** Critical — any remaining support material ruins tone
- **Alternative:** Print straight sections, bend after printing (requires heat for PLA/PETG)
- **Best approach:** Design bell and curves as printable sections with alignment features

#### Challenge 3: Bell (MODERATE)
**Bell function:**
- Impedance matching: Couples bore air column to open air
- Radiation efficiency increases with bell diameter
- **Bell flare:** Typically exponential or Bessel profile
- **Bell diameter:** ~125mm (trumpet), ~200mm (trombone), ~300mm+ (euphonium/tuba)

**3D printing approach:**
- Print bell in sections (too large for most print beds when complete)
- Vertical orientation with thin walls
- Bell rim can be thickened for durability
- **Surface finish inside bell matters** — smooth = brighter tone
- Print at 0.1-0.15mm layer height for visible bell surface

#### Challenge 4: Mouthpiece (EASY)
**Already proven in 3D printing:**
- Parametric OpenSCAD trumpet mouthpiece designs exist
- ABS with 20% infill works well
- SYOS-style approach: ABS plastic, 1/100mm precision
- Standard mouthpiece dimensions (Bach 7C equivalent) are well-documented
- **Can be printed on any FDM printer**
- **Key dimension:** Cup depth, throat diameter, backbore taper

#### Challenge 5: Acoustic Simulation (HARD)
**Traditional brass acoustics:**
- Lip-bore interaction is complex nonlinear coupling
- Vocal tract resonances affect pitch and timbre (especially altissimo)
- Bell radiation pattern affects projection and tone color
- **OpenWInD:** Has LIPS player type for brass simulation
  - Can compute impedance spectrum for brass-like bores
  - Time-domain simulation with lip excitation
  - Bell radiation pressure output

**Our project's capability:**
- OpenWInD already supports brass-like impedance computation
- `LIPS` player type available for simulation
- Bore CSV format supports conical sections
- Would need new bore profiles for trumpet, trombone, etc.

---

## 3. DIFFICULTY EVALUATION FOR ADDING BRASS INSTRUMENTS

### 3.1 Difficulty Matrix

| Component | Difficulty | Notes |
|-----------|-----------|-------|
| Mouthpiece | ★☆☆☆☆ Easy | Already proven, parametric designs exist |
| Straight tubing | ★★☆☆☆ Easy | Same as woodwind bore sections |
| Curved tubing | ★★★☆☆ Moderate | Needs careful support removal inside |
| Bell | ★★★☆☆ Moderate | Print in sections, smooth interior |
| Valve mechanism | ★★★★★ Very Hard | 0.01mm tolerance needed, current FDM can't do it |
| Slide mechanism | ★★☆☆☆ Easy | Proven approach, forgiving tolerances |
| Tuning slides | ★★★☆☆ Moderate | Need airtight sliding fit |
| Water keys | ★★★☆☆ Moderate | Small, functional mechanism needed |
| Leadpipe | ★★☆☆☆ Easy | Straight or slightly curved conical tube |
| Finger buttons | ★☆☆☆☆ Easy | Simple cosmetic parts |
| Bell rim guard | ★☆☆☆☆ Easy | Simple ring/rim piece |
| Overall assembly | ★★★★☆ Hard | Multiple precision joints, airtight seals |

### 3.2 Overall Feasibility Assessment

#### Easiest Entry Point: Bugle (No Valves)
- **Difficulty:** ★★☆☆☆ (2/5)
- **Components:** Mouthpiece + conical bore + bell
- **No valves needed** — player uses lip control only
- **Total tubing length:** ~1500mm (for Bb bugle)
- **Print segments:** 4-6 pieces
- **Assembly:** Join with epoxy, align carefully
- **Time estimate:** 20-30 hours printing + 5-10 hours assembly
- **Likely outcome:** Playable but limited range (3-5 notes in harmonic series)
- **Comparable to:** Our existing didgeridoo or shawm in complexity

#### Moderate Difficulty: Trombone (Slide Only)
- **Difficulty:** ★★★☆☆ (3/5)
- **Components:** Mouthpiece + cylindrical bore + slide + bell
- **No valve mechanism** — slide provides all pitch variation
- **Slide dimensions:** Inner tube OD ~12.7mm, outer tube ID ~13.2mm
- **Tolerance:** 0.25mm clearance between inner and outer slide tubes
- **Print approach:** Inner and outer slides as separate pieces
- **Lubrication:** Trombone slide cream essential
- **Time estimate:** 40-60 hours printing + 10-15 hours assembly
- **Likely outcome:** Playable but with air leaks, limited dynamic range
- **Comparable to:** "Fully Printable Alto Trombone" by JustinHirsh (proven)

#### Hard: 3-Valve Trumpet (with Slides Instead of Valves)
- **Difficulty:** ★★★★☆ (4/5)
- **Components:** Mouthpiece + cylindrical bore + 3 slide-valves + bell
- **Innovation needed:** Design reliable slide-valve mechanism
- **Total tubing length:** ~1340mm (Bb trumpet)
- **Print segments:** 8-12 pieces
- **Assembly:** Complex, many precision joints
- **Time estimate:** 55-80 hours printing + 15-20 hours assembly
- **Likely outcome:** Playable with significant limitations
- **Comparable to:** "Overly-Complicated Trumpet" by GCV3D (proven concept)

#### Very Hard: Piston-Valve Trumpet
- **Difficulty:** ★★★★★ (5/5)
- **Components:** All of above + precision piston valves
- **Valve tolerance:** 0.01-0.02mm — impossible with current FDM
- **Material needed:** Nylon, Delrin, or metal (SLS/DMLS printing)
- **Return springs:** Metal springs required (not printable)
- **Water keys:** Functional spit valves needed
- **Time estimate:** 100+ hours printing + 30+ hours assembly + significant post-processing
- **Likely outcome:** Possibly functional but far below commercial quality
- **Recommendation:** NOT feasible with current consumer FDM printing

#### Very Hard: Trombone with F-Attachment (Rotary Valve)
- **Difficulty:** ★★★★★ (5/5)
- **Components:** Standard trombone + rotary valve for low F
- **Rotary valve:** Most complex brass mechanism
- **Not recommended for initial implementation**

### 3.3 Recommended Implementation Strategy

#### Phase 1: Bugle & Simple Brass (EASY)
**Add first — proves concept, lowest risk:**
1. **Bb Bugle** — mouthpiece + bore + bell, no valves
2. **Bugle Call Horn** — military bugle, simple design
3. **Signal Horn / Post Horn** — historical brass instrument
4. **Didgeridoo (brass-style)** — long conical bore, already in our library

**What this proves:**
- Brass bore generation works in our system
- OpenWInD LIPS simulation works for brass
- Mouthpiece integration works
- Bell design works

#### Phase 2: Slide Instruments (MODERATE)
**Add after Phase 1 succeeds:**
1. **Soprano Trombone (Slide Trumpet)** — single slide, trumpet bore
2. **Piccolo Trombone** — small, simple, proven designs exist
3. **Alto Trombone** — standard trombone minus valve section
4. **Tenor Trombone** — standard trombone

**What this proves:**
- Slide mechanism design and tolerance management
- Airtight sliding joints
- Longer bore lengths work correctly

#### Phase 3: Valve-Slide Hybrids (HARD)
**Add after Phase 2 succeeds:**
1. **3-Valve Bugle** (using slide-valves)
2. **Overly-Complicated Trumpet** (GCV3D design)
3. **Valve Trombone** (3 piston-valves OR slide-valves)

**What this proves:**
- Valve-slide mechanism works
- Complex multi-section assembly
- Full chromatic range achievable

#### Phase 4: Traditional Valves (VERY HARD — Future)
**Only if there's demand and the project matures:**
1. **Custom piston valve design** (may require SLS printing)
2. **Rotary valve design** (highest complexity)
3. **Full-size trumpet with standard valves**

### 3.4 What Would Need to Change in the Codebase

#### New Files Needed:
1. **`backend/brass_profiles/`** — CSV bore profiles for trumpet, trombone, bugle, etc.
2. **`web/src/data/brass-instruments.ts`** — Brass instrument definitions
3. **`web/src/components/BrassDesignTab.tsx`** — Brass-specific design interface (if needed)
4. **`web/src/utils/brass-utils.ts`** — Brass-specific calculations (valve combinations, harmonic series)

#### Modified Files:
1. **`backend/server.py`** — New endpoints for brass-specific features:
   - `/brass/presets` — Brass instrument presets
   - `/brass/valve-combinations` — Calculate available notes for valve config
   - `/brass/harmonic-series` — Generate harmonic series for given tube length
2. **`web/src/data/instruments.ts`** — Add brass instruments to catalog
3. **`web/src/data/instrument-resources.ts`** — Add brass-specific resources/tips
4. **`web/src/components/DesignTab.tsx`** — Add brass-specific controls (valve config, slide length)

#### New OpenWInD Integration:
1. **Bore profiles:** Trumpet (cylindrical + conical), Trombone (cylindrical), Bugle (conical)
2. **Player type:** `LIPS` for all brass instruments
3. **Simulation parameters:** Lip tension range, bell radiation model
4. **Impedance peaks:** Map to brass harmonic series

### 3.5 Estimated Development Effort

| Phase | Time Estimate | Difficulty |
|-------|--------------|------------|
| Phase 1: Bugle & Simple Brass | 1-2 weeks | Easy |
| Phase 2: Slide Instruments | 2-3 weeks | Moderate |
| Phase 3: Valve-Slide Hybrids | 3-4 weeks | Hard |
| Phase 4: Traditional Valves | 4-6 weeks | Very Hard |
| **Total (Phases 1-3)** | **6-9 weeks** | **Moderate-Hard** |

---

## 4. COMPARISON: BRASS vs. WOODWIND 3D PRINTING

| Aspect | Woodwind | Brass |
|--------|----------|-------|
| Bore geometry | Cylindrical or conical | Cylindrical + exponential bell |
| Sound production | Air jet/reed/lips exciting air column | Lips buzzing into mouthpiece |
| Pitch control | Finger holes + keys | Valves/slides change tube length |
| Valve complexity | N/A | Very high (0.01mm tolerance) |
| Slide complexity | N/A | Moderate (0.25mm tolerance) |
| Bell importance | Moderate (saxophone) to none (flute) | Critical for all instruments |
| Mouthpiece complexity | Low to moderate | Low (already proven) |
| OpenWInD support | FLUTE, CLARINET, WOODWIND_REED | LIPS |
| Existing open-source | 100s of designs | ~10 working designs |
| Community size | Large (Demakein, pfh, etc.) | Small (mostly MakerWorld) |
| Material challenges | Smooth bore critical | Smooth bore + airtight slides critical |
| Assembly difficulty | Moderate | Hard |

---

## 5. RECOMMENDED BRASS INSTRUMENTS FOR THE LIBRARY

### Priority 1: Add These First (Simple, Proven)
1. **Bb Bugle** — Simplest brass instrument, no valves, great for beginners
2. **Soprano Trombone (Slide Trumpet)** — Single slide, trumpet bore, compact
3. **Piccolo Trombone** — Most popular 3D printed brass (12,200 downloads)

### Priority 2: Add Next (Moderate, High Value)
4. **Alto Trombone** — Standard trombone, fully printable designs exist
5. **Bb Trumpet (Slide-valve version)** — "Overly-Complicated Trumpet" approach
6. **Bugle with 3 slide-valves** — Full chromatic bugle

### Priority 3: Add Later (Complex, Niche)
7. **Tenor Trombone** — Standard orchestral trombone
8. **Euphonium** — Large bore, conical, 3-4 valves
9. **Tuba** — Largest brass instrument, multiple valves

### Priority 4: Aspirational (Very Complex)
10. **Bb Trumpet with piston valves** — Requires advanced printing
11. **French Horn** — Rotary valves, very complex
12. **Trombone with F-attachment** — Rotary valve in slide section

---

## 6. OPEN SOURCE DESIGNS TO STUDY

| Design | Source | Type | Status | Key Insight |
|--------|--------|------|--------|-------------|
| Overly-Complicated Trumpet | Printables | Trumpet | Working | Slide-valve hybrid approach |
| PrusaPet Trumpet | Printables | Trumpet | Working | Full-size working trumpet |
| Fully Printed Trombone 1.10 | MakerWorld | Trombone | Working | First fully printed trombone |
| Fully Printable Alto Trombone | MakerWorld | Trombone | Working | 904 downloads, proven |
| Working Piccolo Trombone | MakerWorld | Trombone | Working | 12.2K downloads, most popular |
| Parametric Pipe Instruments | CGTrader | Bugle/etc | Working | Parametric approach |
| Trumpet Mouthpiece (OpenSCAD) | STLFinder | Mouthpiece | Working | Parametric mouthpiece |

---

## 7. CONCLUSION

### Feasibility Summary:
- **Bugle/simple brass: EASY to add** — straightforward bore generation, no complex mechanisms
- **Slide instruments: MODERATE** — proven approach, but airtight sliding joints need careful design
- **Valve instruments: VERY HARD** — current FDM printing cannot achieve required tolerance for piston valves
- **Best entry point: Bugle** — simplest brass instrument, proves all core concepts

### Recommendation:
Add brass instruments in phases, starting with bugle/simple brass (Phase 1). This validates brass bore generation, OpenWInD LIPS simulation, and bell design without the complexity of valve mechanisms. Slide instruments (Phase 2) can follow. Traditional valve instruments should be deferred until the project matures and there's community demand.

### Key Insight:
The "slide-valve" approach (as demonstrated by the "Overly-Complicated Trumpet") is the most promising path for 3D printed chromatic brass instruments. It avoids the impossible tolerance requirements of piston valves while providing full chromatic capability. This should be the target for our brass instrument design tools.

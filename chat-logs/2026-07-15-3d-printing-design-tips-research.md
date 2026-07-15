# 3D Printed Instrument Design Tips Research
**Date:** 2026-07-15
**Researcher:** opencode (big-pickle)

## Overview

Comprehensive research on general and category-specific 3D printing tips for musical instruments, covering resolution, post-processing, materials, woodwind-specific considerations, and flute-specific design guidance.

---

## 1. GENERAL 3D PRINTING TIPS FOR MUSICAL INSTRUMENTS

### 1.1 Print Resolution (Layer Height)

**Key finding from research paper (Smolka et al., 2023 — Polymers 15, 02025):**
- Tested PLA, PET-G, and ASA at 0.1mm, 0.3mm, and 0.5mm layer heights
- **Higher layer height does NOT necessarily mean poor acoustic properties**
- For most infill patterns (Grid, Gyroid, Rectilinear), sound reflection coefficient was comparable across layer heights
- Exception: **Cubic infill showed unpredictable variations with layer height — avoid Cubic infill for instruments**
- Layer height of 0.2mm is a good sweet spot: reasonable print time, good acoustic properties
- Surface roughness (Sa) measured at 0.1mm layer height was ~3.8μm for PLA — smooth enough for acoustics

**Practical recommendation:**
- **0.1mm layer height:** Best for embouchure holes, tone holes, mouthpieces — any surface the player touches or where air turbulence matters
- **0.2mm layer height:** Good default for bore walls, body sections — best balance of speed and quality
- **0.3mm layer height:** Acceptable for large structural parts where acoustic properties are less critical
- **0.5mm layer height:** Only for non-acoustic structural parts (stands, cases)

**Source:** [MDPI Polymers 2023](https://www.mdpi.com/2073-4360/15/9/2025), [ScienceDirect 2025](https://www.sciencedirect.com/science/article/pii/S0022460X22006174)

### 1.2 Wall Thickness & Infill

**Critical rule from Demakein documentation (Paul Harrison, 2025):**
> "The number one problem people encounter is that any tiny holes in the instrument may prevent sound from be produced. These might be gaps between segments, or holes in the printed walls."

> "High wall thickness and infill produces a better tone, presumably less energy is lost to the walls the more solid they are. This also helps ensure there are no tiny leaks."

**Practical recommendations:**
- **Minimum 3 wall loops** for acoustic instruments (4+ recommended)
- **15-20% infill minimum** for acoustic parts; **40-100% for embouchure/head joints**
- **100% infill (solid) for mouthpieces** — critical for tone quality and preventing air leaks
- Increasing infill density beyond 60% shows diminishing returns for acoustic performance
- **Gyroid infill** is preferred — consistent acoustic properties at all layer heights, no resonant frequencies of its own
- **Rectilinear/Grid infill** also acceptable — predictable acoustic behavior
- **Avoid Cubic infill** — unpredictable acoustic variations

**Source:** [Demakein docs](http://www.logarithmic.net/pfh/design), [MDPI Polymers 2023](https://www.mdpi.com/2073-4360/15/9/2025)

### 1.3 Material Selection for Acoustic Instruments

**From the 3D Shopper filament guide (2024) and academic research:**

#### PLA (Polylactic Acid)
- **Best for:** Recorders, simple flutes, ocarinas, beginner instruments
- **Sound quality:** Bright, clear tones; good projection
- **Pros:** Easy to print, minimal warping, FDA food-safe variants available, inexpensive ($15-25/kg)
- **Cons:** Poor heat resistance (60°C glass transition), brittle under stress, degrades in sunlight
- **Acoustic note:** PLA has the highest sound reflection coefficient of the three tested materials — best acoustic performance on paper
- **Best practice:** Use PLA+ for improved strength without sacrificing acoustic quality

#### PETG (Polyethylene Terephthalate Glycol)
- **Best for:** Instruments that will be handled frequently, outdoor use, practice instruments
- **Sound quality:** Slightly warmer/duller than PLA due to higher damping
- **Pros:** Better impact resistance than PLA, good layer adhesion, food-safe, UV-resistant
- **Cons:** Stringing, harder to achieve fine detail, slightly flexible
- **Acoustic note:** Sound reflection coefficient slightly lower than PLA; acceptable for most applications

#### ASA (Acrylonitrile Styrene Acrylate)
- **Best for:** Outdoor instruments, professional instruments requiring durability
- **Sound quality:** Similar to ABS — warm, with good sustain
- **Pros:** UV-resistant, high temperature resistance (100°C), good mechanical properties
- **Cons:** Requires enclosure, strong fumes, harder to print
- **Acoustic note:** Comparable acoustic performance to PET-G

#### Nylon (PA)
- **Best for:** Key mechanisms, moving parts, flexible components
- **Sound quality:** High damping — deadens sound. Good for structural parts, bad for resonating bodies
- **Pros:** Excellent wear resistance, self-lubricating, flexible
- **Cons:** Absorbs moisture (warping), requires dry box, high print temps
- **Not recommended for:** Bore walls, resonating chambers

#### Resin (SLA/DLP)
- **Best for:** Mouthpieces, reed plates, precision small parts
- **Sound quality:** Excellent — smoothest possible surface finish, no layer lines
- **Pros:** Highest resolution (0.025mm), smoothest surface, isotropic properties
- **Cons:** Brittle, toxic uncured, limited build volume, expensive
- **Source:** Acta Acustica 2025 — SLA at 0.025mm resolution produces "negligible staircase effect"

**Source:** [3D Shopper 2024](https://3dshopper.net/3d-printed-musical-instruments-best-filaments-acoustics/), [MDPI Polymers 2023](https://www.mdpi.com/2073-4360/15/9/2025), [ScienceDirect 2024](https://www.sciencedirect.com/science/article/pii/S2214785324003146)

### 1.4 Post-Processing for Acoustic Instruments

**Critical post-processing steps (ranked by importance for instruments):**

#### Bore Smoothing (MOST IMPORTANT for wind instruments)
1. **Acetone vapor smoothing (ABS/ASA only):** Creates perfectly smooth bore surface. Soak paper towel in acetone, place in container with print, seal for 10-30 minutes. Produces glass-like interior finish.
2. **Epoxy resin coating:** Apply thin coat of epoxy to interior bore. Self-leveling, fills layer lines completely. Food-safe epoxy available. Most reliable method.
3. **PVA/wood glue coating:** Water-based alternative to epoxy. Apply diluted wood glue (1:1 with water), rotate to coat interior, drain excess. Multiple coats build up smooth surface.
4. **Acetone softening (PVC/PETG):** For tuning slides — acetone softens PVC/PETG allowing stretching over another pipe for tight-fitting joints. 24+ hour soak required.
5. **Sanding:** Only practical for large-bore instruments. Use progressively finer grits (120→220→400→800). Bore brushes help for cylindrical instruments.
6. **Chemical smoothing sprays:** Commercial products (PolySmooth, etc.) — less controlled but easier

**Research finding from Simian (2023) on shakuhachi:**
> "Interior smoothness, far from being a musician's myth, greatly affects sound production."
- SLS PA12 body was too rough even after abrasive polishing
- Multiple acrylic varnish coats were needed to achieve acceptable bore smoothness
- The blowing edge (utaguchi) required SLS PA11 + intensive hand polishing

#### External Finishing
1. **Support removal:** Use flush cutters, then sand attachment points. Water-soluble supports (PVA/HIPS) leave no marks.
2. **Sanding progression:** 120→220→400→800→1500 grit for smooth finish
3. **Primer + paint:** Fills remaining layer lines. High-build primer for FDM. Spray paint for even finish.
4. **Clear coat:** UV protection, moisture barrier, adds durability. Polyurethane or lacquer.
5. **Hydro dipping:** For decorative patterns on curved surfaces

#### Joint Sealing (Critical for multi-part instruments)
1. **Cyanoacrylate (superglue):** Standard for PLA joints. Fast, strong, fills small gaps.
2. **Epoxy resin:** Stronger than superglue, better gap-filling. 5-minute or 30-minute varieties.
3. **Thread seal tape (PTFE):** For removable joints (tuning slides). Non-permanent.
4. **O-rings:** For precision removable joints. Print groove for O-ring in design.
5. **Silicone sealant:** For waterproofing joints. Food-safe silicone for instruments.

**Source:** [BigRep Post-Processing Guide](https://bigrep.com/post-processing), [Wevolver 2025](https://www.wevolver.com/article/the-ultimate-guide-to-3d-printing-post-processing-techniques), [Demakein docs](http://www.logarithmic.net/pfh/design)

### 1.5 Print Orientation

**For cylindrical wind instruments:**
- **Vertical orientation (recommended by Demakein):** Each segment prints vertically. This means:
  - Bore is along Z-axis — layer lines are horizontal rings
  - Layer lines create slight ridges inside bore (can be smoothed)
  - Best structural integrity for thin walls
  - Requires joining segments post-print
- **Horizontal orientation:** Bore is along X/Y axis
  - Layer lines run along bore length — smoother interior but weaker circumferentially
  - Often requires internal supports
  - Can cause visible seam line along bore
- **45° orientation:** Compromise — neither optimal for bore smoothness nor strength

**Demakein approach:** Prints segments vertically, includes guide prongs for alignment during assembly.

**Source:** [Demakein docs](http://www.logarithmic.net/pfh/design), [Simian 2023](https://journals.sagepub.com/doi/10.1177/20592043231210653)

### 1.6 Thermal Expansion & Tolerances

- PLA shrinks ~0.3-0.5% during cooling
- PETG shrinks ~0.5-0.7%
- ABS shrinks ~0.8-1.2%
- **For press-fit joints:** Design 0.1-0.2mm clearance for PLA, 0.2-0.3mm for PETG
- **For friction-fit segments:** Design 0.05-0.1mm interference for tight fit
- **Scale compensation:** Most slicers offer horizontal expansion setting to fine-tune dimensions
- **Bore diameter tolerance:** ±0.2mm achievable with well-calibrated FDM printers
- **Tone hole tolerance:** ±0.1mm achievable at 0.1mm layer height

---

## 2. CATEGORY-SPECIFIC TIPS: WOODWIND INSTRUMENTS

### 2.1 Bore Design & Printing

**Cylindrical bores (clarinets, whistles):**
- Easiest to 3D print — straightforward geometry
- Print vertically for best results
- Join segments with superglue (PLA) or epoxy
- **Demakein tip:** Use `--join straight` for socketed joints if needed

**Conical bores (saxophones, oboes, shawms):**
- More challenging — overhangs increase with cone angle
- May require supports for sections with >45° overhang
- Print in multiple segments, each within printable overhang range
- Join carefully — any misalignment affects intonation
- **Demakein:** Can generate conical bore designs with custom `inner_diameters` and `initial_inner_fractions`

**Bore accuracy requirements:**
- **Soprano instruments:** ±0.5mm bore diameter tolerance acceptable
- **Alto/Tenor instruments:** ±1mm tolerance acceptable
- **Bass instruments:** ±1.5mm tolerance acceptable
- End correction formula: ΔL ≈ 0.6 × r (open end), ΔL ≈ 0.3 × r (flanged end)

**Source:** [Demakein docs](http://www.logarithmic.net/pfh/design), [Frontiers Signal Processing 2025](https://www.frontiersin.org/journals/signal-processing/articles/10.3389/frsip.2025.1519450/full)

### 2.2 Tone Hole Design & Printing

**Critical dimensions (from research):**
- **Minimum tone hole diameter:** 4mm (below this, air turbulence dominates and tone is unstable)
- **Maximum tone hole diameter:** Up to 0.8× bore diameter (larger holes = sharper pitch but weaker tone)
- **Chimney height (wall thickness at hole):** 2-5mm for best acoustic behavior
- **Chimney height affects:** Taller chimneys = stronger radiation losses, slightly flatter pitch
- **Tone hole edges:** Must be sharp/crisp — rounded edges affect pitch accuracy

**Printing tone holes:**
- **Best method:** Print bore vertically, tone holes are horizontal holes through wall
- **Drill after printing:** More accurate than printing holes — use drill bit, then ream to final size
- **Printed holes:** Work well at ≥6mm diameter; smaller holes may need post-print drilling
- **Plugged toneholes:** Still affect resonance (added mass and damping) — don't leave accidental holes

**Key mechanism for covering holes:**
- Leather pads: Traditional, effective, requires metal key mechanism
- Cork pads: Simpler, good seal, replaceable
- Silicone pads: Best seal, most durable, 3D-printable
- Silicone domes: For covered-hole systems (clarinet-style)
- 3D-printed compliant mechanisms: Monolithic flexible hinges — no assembly required

**Source:** [JASA 2025](https://pubs.aip.org/asa/jasa/article/158/1/210/3351934), [ResearchGate 2023](https://www.researchgate.net/publication/374695526), [OHMI Trust](https://www.ohmi.org.uk/woodwind.html)

### 2.3 Mouthpiece/Head Joint Design

**Embouchure hole (flutes/recorders):**
- **Shape:** Slightly D-shaped or rectangular with rounded corners works best
- **Edge sharpness:** CRITICAL — the striking edge must be crisp and sharp
- **Edge angle:** ~45° for flutes, ~30° for recorders
- **Width:** 10-15mm for soprano flutes, 15-20mm for alto
- **Printing:** Print at 0.1mm layer height minimum; consider resin for best edge quality
- **Post-process:** Hand-file the striking edge to razor sharpness after printing

**Reed mouthpieces (clarinets, saxophones):**
- **Tip opening:** 1.0-1.5mm for beginners, 1.5-2.5mm for advanced
- **Facing curve:** Complex 3D curve — best designed parametrically
- **Chamber shape:** Defines tone character (large = dark/warm, small = bright/loud)
- **SYOS approach:** ABS plastic, 1/100mm precision, 18 colors available
- **Academic research:** Acta Acustica 2021 — 3D printed sax mouthpiece personalization shows measurable acoustic differences from design variations

**Drinking-straw reeds (for shawms):**
- Demakein creates double-reed shawms using drinking straws as reeds
- Simple, effective, replaceable
- Straw diameter affects pitch and response

**Source:** [SYOS/Acta Acustica 2021](https://acta-acustica.edpsciences.org/articles/aacus/full_html/2021/01/aacus210019/F7.html), [Demakein docs](http://www.logarithmic.net/pfh/design)

### 2.4 Key Mechanisms

**3D-printed key approaches:**

1. **Traditional separate keys:** Print each key separately, attach with screws/pins
   - Requires metal springs for return action
   - Most accurate but most complex assembly
   - Metal rod/pin stock needed as axle

2. **Compliant mechanisms (3D-printed monolithic):**
   - Living hinges printed as part of the body
   - No assembly required — keys flex and return
   - PLA works well for compliant hinges (flexible at thin cross-sections)
   - Limited travel range (~2-3mm)
   - Best for simple open/close keys

3. **Print-in-place mechanisms:**
   - Moving parts designed to print already assembled
   - Requires precise tolerances (0.2-0.3mm clearance)
   - Works best with soluble supports

4. **Hybrid approach:**
   - 3D-printed key bodies with metal springs and screws
   - Best balance of printability and performance
   - Standard hardware (M3 screws, steel wire) from hardware store

**Source:** [OHMI Trust](https://www.ohmi.org.uk/woodwind.html), [Digital Reed Aerophone (WPI 2025)](https://wp.wpi.edu/musicalmachines/2025/10/14/digital-reed-aerophone/)

### 2.5 Segment Joining (Multi-Part Instruments)

**Demakein's approach (2025):**
- Prints instrument in multiple vertical segments
- Each segment includes **alignment prongs** for correct orientation
- Segments joined with cyanoacrylate (superglue)

**Joining methods ranked by reliability:**
1. **Epoxy resin (best):** Strong, gap-filling, waterproof. 30-minute epoxy for repositioning time.
2. **Cyanoacrylate (superglue):** Fast, strong, but brittle. Good for PLA.
3. **Solvent welding (ABS/ASA):** Acetone dissolves surface, creates chemical bond. Strongest joint.
4. **Press-fit with sealant:** O-ring groove + silicone sealant. Removable for maintenance.
5. **Threaded joints:** Print threads in design. M4-M8 threads work well in PLA at 0.2mm layer height.

**Common failure mode:**
> "Often the head part of the instrument produces sound, but when further segments are attached it stops working. This is very probably a problem with the joints, even if there is no obvious leak." — Demakein docs

**Source:** [Demakein docs](http://www.logarithmic.net/pfh/design)

### 2.6 One-Handed/Accessible Woodwind Design

**From OHMI Trust and related projects:**
- Additional key work to compensate for reach required to cover holes
- 3D-printed key mechanisms with lever ratios
- Servo-actuated keys for digital control
- Foam tape padding on key surfaces for comfort
- Cork pads for tone hole coverage
- Adjustable thumb rests and ring slings

**Source:** [OHMI Trust](https://www.ohmi.org.uk/woodwind.html)

---

## 3. CATEGORY-SPECIFIC TIPS: FLUTE INSTRUMENTS

### 3.1 Transverse Flute (Side-Blown)

**Embouchure hole design:**
- **Shape:** Rectangular with rounded ends, or slightly D-shaped
- **Width:** Typically 12-15mm for concert flute, 8-10mm for piccolo
- **Length:** 1.2-1.5× width
- **Striking edge:** Must be sharp, angled at ~45° downstream
- **Blow edge:** Rounded, smooth — air must flow cleanly over it
- **Labium depth:** 1-2mm (distance from outer wall to edge)

**Head joint geometry:**
- **Cork position:** Closes the far end, typically 17mm from center of embouchure hole
- **Cork material:** Natural cork, wine cork, or 3D-printed flexible plug
- **Head joint taper:** Slight conical taper toward cork end improves intonation
- **Material thickness:** Thicker walls = brighter tone, thinner = warmer tone

**Printing tips for transverse flutes:**
- Print head joint vertically — embouchure hole on top
- Use 0.1mm layer height for embouchure hole area
- Post-process: File embouchure edge to razor sharpness
- Test blowing across hole before final assembly
- **Tuning:** Adjust cork position and overall tube length against a tuner

**PVC pipe + 3D printed head joint (proven approach):**
- Use Schedule 40 PVC pipe for body (smooth bore, food-safe)
- 3D print head joint that fits PVC pipe ID
- Drill tone holes in PVC body after printing head joint
- Total cost: $5-15 materials + 30min print time

**Source:** [Instructables PVC Flute](https://www.scribd.com/document/635902567/Making-Simple-PVC-Flutes), [UOregon Blog 2023](https://blogs.uoregon.edu/scitechoutreach/2023/07/06/plumbing-pipe-music-building-a-pvc-flute/)

### 3.2 Fipple Flute (Recorder/Whistle)

**Fipple (mouthpiece) design:**
- **Windway:** Narrow channel directing air to striking edge. 1.5-3mm wide, 8-15mm long.
- **Block (fipple plug):** Fits inside tube, creates windway. Must be precisely shaped.
- **Striking edge (labium):** Sharp edge where air splits. ~45° angle.
- **Throat:** The gap between block and striking edge. Most critical dimension — controls response and pitch.

**Printing tips for fipple flutes:**
- Print block separately for best fit
- Windway can be printed horizontally for smooth air channel
- **Demakein folk flute:** Cylindrical bore, simple fipple, 6 finger holes. Easy first project.
- Adjust block position to tune — slightly forward = sharper, slightly back = flatter
- **Tuning slide method:** Acetone-softened PVC section slides over main body

**Source:** [Demakein examples](http://www.logarithmic.net/pfh/design), [Chiff and Fipple Forum](https://www.chiffandfipple.com/t/a-recorder-with-a-flute-embouchure/107021)

### 3.3 Shakuhachi (End-Blown Flute)

**From Simian (2023) — detailed AM shakuhachi case study:**
- **Standard dimensions:** 54.54cm bamboo, 5 finger holes (4 front, 1 thumb)
- **Blowing edge (utaguchi):** "Razor-sharp edge" — most critical feature
- **Material:** SLS PA11 for blowing end (best surface finish), PA12 for body
- **Post-processing:** Intensive hand abrasive polishing for blowing edge; acrylic varnish coats for bore
- **Key insight:** Interior smoothness directly affects sound production — not a myth
- **Weight concern:** Solid PLA/PETG is heavier than bamboo (which has air bubbles)
- **Design goal:** Produce thin, accurate, sharp blowing end from biocompatible material

**Print-on-demand shakuhachi:**
- Shaku6.com sells plans + 3D printable files
- ~$1 cost in materials, 30-minute build
- 20mm ID pipe, 55cm length

**Source:** [Simian 2023](https://journals.sagepub.com/doi/10.1177/20592043231210653)

### 3.4 Pan Flute

**Design considerations:**
- Graduated tube lengths (shortest = highest pitch, longest = lowest pitch)
- **Tube diameter:** 15-25mm ID depending on desired range
- **Number of pipes:** 8 (one octave) is standard for beginners
- **End closure:** One end sealed (cork, printed cap, or hot glue)
- **Blowing edge:** All pipes aligned at same height, edges in a straight line
- **Tube spacing:** 2-3mm gap between pipes for clean fingering

**Printing tips:**
- Print each pipe individually — vertical orientation
- Print end caps separately or use hot glue
- Assemble with hot glue gun — quick, adjustable, removable
- **Alternative:** Print entire pan flute as single piece with thin walls
- Materials cost: $10-15 for a basic 8-pipe pan flute

**Source:** [MakerWorld Pan Flute](https://makerworld.com/en/search/models?keyword=pan%20flute)

### 3.5 Native American Flute

**Two-chamber design:**
- **True sound hole (TSH):** Between slow air chamber and sound chamber
- **Fetish/bird:** Directs air from slow air chamber to TSH
- **Fetish position:** Controls pitch — forward = sharper, back = flatter
- **3D printed fetish:** Tinkercad design, 25×15×6mm with 2×10×18mm slot

**Materials:**
- 3/4" Schedule 40 PVC pipe (food-grade white, NOT gray drainage pipe)
- 3D printed air-flow director (fetish)
- Wine cork for end plug

**Printing tips:**
- Print fetish at 0.1mm layer height — most critical part
- Use PLA+ for durability
- Total print time: ~9 minutes for fetish
- **Key to success:** Get the fetish geometry right — air must be directed across TSH cleanly

**Source:** [UOregon Blog 2023](https://blogs.uoregon.edu/scitechoutreach/2023/07/06/plumbing-pipe-music-building-a-pvc-flute/)

### 3.6 Membrane Instruments

**From MakerWorld Membrane Flute:**
- Membrane vibrates as air passes across it
- Membrane materials: latex balloon, latex glove, nitrile glove
- Tightening screw stretches membrane — tighter = higher pitch
- **Print settings:** 0.2mm layer, 3 walls, 15% infill
- **Assembly:** CA glue membrane to ring, trim excess, screw onto body
- **Warning:** Can be VERY loud

**From Printables PVC Membrane Clarinet:**
- M3×10 bolt and nut for tension adjustment
- PLA, supports touching buildplate, 3 walls, 15% infill
- Thread adjustment: adjust flow rate and horizontal expansion if threads bind
- **Membrane adjustment:** Blow into mouthpiece, tighten ring until sound produced
- Different membrane materials alter tone (balloon vs. latex glove vs. thin paper)

**Source:** [MakerWorld](https://makerworld.com/en/models/1194021-membrane-flute), [Printables](https://www.printables.com/model/441519-pvc-membrane-clarinet)

### 3.7 Slide Whistle / Glissando Instruments

**Design principles:**
- Piston or slide mechanism varies effective tube length continuously
- **Piston seal:** Must be airtight but slide freely
- **Material:** PLA piston in PLA/PVC tube works with careful tolerance
- **Tolerance:** 0.15-0.2mm clearance between piston and bore
- **Lubrication:** Silicone grease or petroleum jelly for smooth sliding
- **Bore:** Must be perfectly cylindrical for consistent glissando

**Source:** [Glissonic research](https://chat-logs/2026-07-15-pvc-flute-and-extension-research.md)

### 3.8 Tuning Considerations for Flutes

**General tuning principles:**
- **Fundamental frequency:** f = v / (2L) for open pipe, f = v / (4L) for closed pipe
  - v = speed of sound (~343 m/s at 20°C)
  - L = effective acoustic length
- **End correction:** ΔL ≈ 0.6r (open end), where r = bore radius
- **Temperature dependence:** Pitch rises ~5.7 cents per °C for flutes
- **Moisture:** Condensation in bore raises pitch slightly

**Hole placement (simplified):**
- For chromatic scale: holes placed at positions calculated from bore resonance equations
- Demakein handles this automatically through numerical optimization
- **For custom scales:** Modify hole positions in Demakein's instrument designer class

**Fine-tuning after printing:**
- **Sharpen a note:** Enlarge the tone hole slightly (file or drill)
- **Flatten a note:** Fill hole partially with epoxy and re-drill smaller
- **Overall pitch:** Adjust cork position or overall tube length
- **Register tuning:** Adjust octave hole size/position (flutes) or register key venting (clarinets)

**Source:** [Demakein docs](http://www.logarithmic.net/pfh/design), [SelfCAD Blog 2025](https://www.selfcad.com/blog/3d-printed-musical-instruments)

---

## 4. TOOLS & SOFTWARE RECOMMENDATIONS

### 4.1 CAD Software
- **Fusion 360:** Free for personal use, parametric modeling, good for instrument design
- **Tinkercad:** Simple, browser-based, good for beginners and simple parts
- **OnShape:** Cloud-based, parametric, free for public projects
- **OpenSCAD:** Code-based, fully parametric, ideal for bore generation
- **Build123d:** Python-based, our project's export engine
- **SelfCAD:** All-in-one (modeling + slicing + printing), good for education
- **JSCAD:** JavaScript-based, our project's parametric generator

### 4.2 Slicer Settings (Recommended)
- **Layer height:** 0.1mm (mouthpieces) / 0.2mm (body) / 0.3mm (structural)
- **Walls:** 4 minimum, 6+ for acoustic parts
- **Infill:** 20% body, 60-100% head joint/mouthpiece
- **Infill pattern:** Gyroid or Rectilinear (avoid Cubic)
- **Speed:** 40-60mm/s for acoustic parts (slower = better quality)
- **Temperature:** PLA: 200-210°C, PETG: 230-240°C, ASA: 240-250°C
- **Cooling:** PLA: 100% fan, PETG: 50% fan, ASA: 0% fan (enclosed)

### 4.3 Essential Tools
- Digital calipers (0.01mm resolution)
- Set of drill bits (1-15mm)
- Half-round needle files
- Flush cutters
- Cyanoacrylate glue (thin and thick)
- 5-minute epoxy
- Sandpaper (120-1500 grit)
- Cork reamer (for adjusting cork joints)
- Electronic tuner (or tuner app)

---

## 5. KEY ACADEMIC REFERENCES

1. **Smolka et al. (2023)** — "Three-Dimensional Printing Process for Musical Instruments: Sound Reflection Properties of Polymeric Materials" — MDPI Polymers 15(9), 02025
2. **Simian (2023)** — "3D-Printed Musical Instruments: Lessons Learned from Five Case Studies" — SAGE Journals
3. **Acta Acustica (2021)** — "Towards 3D printed saxophone mouthpiece personalization: Acoustical analysis of design variations"
4. **Ciochon et al. (2023)** — "The impact of surface roughness on an additively manufactured acoustic material" — Journal of Sound and Vibration 546
5. **Umetani et al. (2016)** — "Printone: Interactive Resonance Simulation for Free-form Print-wind Instrument Design" — ACM SIGGRAPH Asia
6. **Frontiers Signal Processing (2025)** — "Discrete port-Hamiltonian system model of a single-reed woodwind instrument"
7. **JASA (2025)** — "Investigating the impact of tone hole geometry on the flow in wind instruments via PIV"

---

## Summary of Key Takeaways

1. **0.2mm layer height** is the sweet spot for most instrument parts; use 0.1mm for critical acoustic surfaces
2. **PLA is acoustically excellent** but use PLA+ or PETG for durability
3. **High wall count (4+) and infill (20-100%)** prevent leaks and improve tone
4. **Bore smoothing is essential** — epoxy coating is the most reliable method
5. **Gyroid infill** is preferred for consistent acoustic properties
6. **Avoid Cubic infill** — unpredictable acoustic behavior
7. **Drill tone holes after printing** for best accuracy
8. **Sharp embouchure edges** are critical — hand-file after printing
9. **Seal all joints** — even invisible micro-leaks kill the tone
10. **Print vertically** for cylindrical instruments; use alignment prongs for multi-part assembly

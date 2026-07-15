# PVC Pipe Instrument Design & Hardware Store Materials Research
**Date:** 2026-07-15

## 1. PVC Pipe Bass Clarinet Design Concept

### The Core Idea
A bass clarinet built around a standard **PVC pipe as the main cylindrical bore**, with **3D printed neck joint and bell** that fit perfectly onto the PVC pipe. Additional parts (key mechanisms, mouthpiece adapter, register vents) are also 3D printed.

### Why This Works
- Bass clarinet bore is **cylindrical** (unlike soprano clarinet which is polycylindrical) — a PVC pipe IS cylindrical
- PVC pipe is cheap ($2-10), available at any hardware store, and comes in precise standard sizes
- 3D printed adapters can bridge between different diameters (PVC pipe → mouthpiece, PVC pipe → bell)
- The cylindrical bore makes PVC an ideal substitute for the main body

### Bass Clarinet Bore Specifications
- **Inner diameter:** ~24mm (JDWoodwinds design uses exactly 24mm bore)
- **Total length:** ~1500mm (varies by model, some go to 1700mm+ for low C)
- **Bore type:** Cylindrical (from neck to just before bell)
- **Bell:** Conical flare (typically purchased from eBay from Chinese sellers)
- **Keys/holes:** 24 tone holes in standard Boehm system

---

## 2. PVC Pipe Dimensions (Hardware Store Standard)

### Schedule 40 PVC Pipe (Most Common)
| Nominal Size | Inner Diameter | Outer Diameter | Wall Thickness |
|---|---|---|---|
| 1/2" (12.7mm) | 15.8mm | 21.3mm | 2.8mm |
| 3/4" (19.05mm) | 20.9mm | 26.7mm | 2.9mm |
| **1" (25.4mm)** | **26.6mm** | **33.4mm** | **3.4mm** |
| 1-1/4" (31.75mm) | 35.1mm | 42.2mm | 3.6mm |
| 1-1/2" (38.1mm) | 40.9mm | 48.3mm | 3.7mm |
| 2" (50.8mm) | 52.5mm | 60.3mm | 3.9mm |

### Key Finding: 1" Schedule 40 PVC
- **Inner diameter: 26.6mm** — very close to the 24mm bass clarinet bore
- A 3D printed adapter ring can step down from 26.6mm to 24mm at the joints
- Or use Schedule 80 PVC (1" nominal): ID = 25.4mm — even closer to 24mm

### Schedule 80 PVC (Thicker Walls)
| Nominal Size | Inner Diameter | Outer Diameter |
|---|---|---|
| 1" | 25.4mm | 33.4mm |
| 1-1/4" | 34.4mm | 42.2mm |

### European PVC (DIN标准)
| Size | Inner Diameter |
|---|---|
| 16mm | 16.0mm |
| 20mm | 20.0mm |
| 25mm | 25.0mm (perfect match!) |
| 32mm | 32.0mm |

**25mm European PVC pipe has ID = 25mm — nearly identical to the 24mm bass clarinet bore!**

---

## 3. Alternative Pipes from Hardware Stores

### PEX Tubing (Cross-linked Polyethylene)
- Flexible, smooth bore
- Available in 1/2", 3/4", 1" sizes
- 1/2" PEX: ID ≈ 11.9mm (too small)
- 3/4" PEX: ID ≈ 18.4mm (usable for alto clarinet)
- **1" PEX: ID ≈ 24.1mm — excellent match for bass clarinet!**

### Copper Pipe
- Rigid, smooth bore, available in exact sizes
- 1" copper: ID = 26.6mm (Schedule 40 equivalent)
- 7/8" copper (rare): ID ≈ 22.2mm (close to bass clarinet)
- Expensive, requires soldering

### ABS Pipe (Drain pipe)
- Similar to PVC but black
- 1" ABS: ID ≈ 26.6mm (same as PVC)
- Less common for musical use

### Rubber/Silicone Tubing (For Flexible Joints)
- Available at hardware stores and Amazon
- Silicone tubing: ID from 1mm to 25mm+ (25mm = 1" ID)
- Useful for:
  - **Neck joint:** flexible silicone connector between mouthpiece adapter and PVC body
  - **Bell joint:** silicone gasket between PVC body and bell
  - **Sealing:** O-rings for airtight connections

### Garden Hose / Vacuum Hose
- Standard garden hose: ID ≈ 15.9mm (too small)
- Wet/dry vac hose: ID ≈ 50mm (too large, could work for contrabass)

---

## 4. Existing 3D Printed Bass Clarinet Projects

### A. JDWoodwinds Bass Clarinet in G ($100 STL files)
**Source:** jdwoodwind.com
**Key specs:**
- Bore: **24mm** (printed body, NOT PVC)
- Key work: Simplified Boehm System
- Range: Low E
- Build volume needed: 250mm x 200mm x 200mm
- Material: PLA+
- Perimeters: 4 (body/neck), 6 (keys)
- Layer height: 0.16mm
- Infill: 30-50%

**Parts NOT 3D printed (purchased):**
- 25mm OD x 24mm ID brass/carbon fiber tubing (neck tenons)
- 7mm OD x 6mm ID brass tube (register vent)
- Bass clarinet bell from eBay (Chinese)
- Stainless steel rod (2mm x 450mm) for key pins
- Music wire (0.38mm) for springs
- Neoprene foam pads
- Cork sheets
- PTFE sheet (Teflon)

**Critical dimensions:**
- Upper register vent: 13mm long, protruding 5mm
- Lower register vent: 18mm long, protruding 4mm
- Neck tenon 1: 30mm length (45mm total)
- Neck tenon 2: 21mm length (36mm total)

**Assembly notes:**
- All overhangs and tone holes MUST be sealed with thin CA glue
- Use finishing nails (20mm) as alignment pins between body sections
- Cork tenons for joints: 1/32" to 1/16" depending on joint

### B. Jared's 3D Printed Bass Clarinet (YouTube)
**Source:** Hackaday article (2022)
**Key approach:**
- Keyed in G (not Bb) — different key for experimentation
- Keys and levers printed LARGER than metal versions
- Reverted to historical clarinet designs for simpler keywork
- Used a standard clarinet bell (purchased)
- Sounded very similar to a genuine instrument

### C. PVC Membrane Clarinet (Fabien T.)
**Source:** Printables #441519
**Materials:**
- 16mm wide PVC tube (electrical IRL tubing)
- 3D printed mouthpiece, membrane ring, membrane collar
- M3x10 bolt and nut
- Balloon or latex glove membrane
- Drill holes for finger positions
- ~475mm length for E note

### D. Dan Bruner's PVC Clarinet (A3)
**Source:** geocities.ws/danielbruner/instruments/
**Approach:**
- Uses 1/2" Schedule 40 PVC pipe as body
- Alto sax reed (wider than PVC ID)
- Head joint shaped on belt sander for reed angle
- Reed secured with screw through PVC wall
- Finger holes tuned by ear using diatonic scale
- Critical: reed placement dramatically affects hole sizing

---

## 5. 3D Printed Adapter Designs for PVC Pipe Instruments

### A. PVC Pipe Connectors with Twist Locks (DangerousLadies)
**Source:** dangerousladies.ca
- Twist-lock connectors for PVC pipes
- Includes US Schedule 40 & 80, and European PN16 sizes
- Part A + Part B: internal tube slides into pipe ends, twists 3/4 turn to lock
- Print with 4 walls minimum, 30% infill
- Can be glued for permanent connections

### B. FlexiBuild PVC Pipe Connector System
**Source:** MakerWorld
- Full modular connector system for 1/2" (20mm) and 25mm PVC
- 90-degree joints, T-joints, rotational connectors
- Printed in PLA with 6 walls, 15% infill
- Originally for building enclosures, adaptable for instruments

### C. Adjustable Connector for 1/2" PVC (Wile E. 3D)
**Source:** MakerWorld
- Uses 1/4 x 1.25" bolt and nut
- Adjustable angle connector
- Small wire-routing holes

### D. 3D Printed Clarinet Bell (DarkArtsLab)
**Source:** MakerWorld #2510899
- Bb clarinet bell with cone bore
- Larger body = more projection + warmer tone
- Internal tuning notch for intonation
- Must match filament choice to bore size

---

## 6. Proposed Design: PVC Pipe Bass Clarinet

### Architecture
```
[3D Printed Mouthpiece Adapter] 
    → [3D Printed Neck Joint] 
        → [PVC PIPE BODY (1" Schedule 40 or 25mm Euro)]
            → [3D Printed Register Vent Housing]
            → [3D Printed Bottom Joint + Key Mounts]
        → [3D Printed Bell Adapter]
    → [Purchased or 3D Printed Bell]
```

### Bore Profile (CSV format for OpenWInD)
```
0.0     0.12    0.0133  0.0133  linear
0.12    1.3     0.0133  0.0133  linear
1.3     1.5     0.0133  0.025   linear
```
- First section: mouthpiece to body (cylindrical, 24mm ID = 12mm radius)
- Second section: main body (cylindrical PVC bore)
- Third section: bell flare (conical expansion)

### PVC Pipe Selection
**Option 1: 1" Schedule 40 PVC**
- ID = 26.6mm → 3D printed step-down adapter at 24mm
- Wall = 3.4mm
- OD = 33.4mm
- Cost: ~$3-5 per 10-foot length

**Option 2: 25mm European PVC (DIN)**
- ID = 25.0mm → 3D printed 1mm step-down adapter
- Closer match to 24mm bore
- May not be available at US hardware stores

**Option 3: 1" Schedule 80 PVC**
- ID = 25.4mm → only 0.7mm step-down needed
- Thicker walls = more rigid
- Dark grey color

### 3D Printed Parts Needed
1. **Mouthpiece adapter** — fits standard bass clarinet mouthpiece bore (23mm ID)
2. **Neck joint** — curves from mouthpiece down to PVC pipe, includes register vent
3. **Register vent housing** — 18mm long tube protruding 4mm from body
4. **Key mounting posts** — threaded inserts or snap-on mounts for keys
5. **Body section connectors** — join multiple PVC pipe sections
6. **Bell adapter** — transitions from PVC pipe OD to bell ID
7. **Key mechanisms** — simplified Boehm system, larger than metal
8. **Tone hole covers/pads** — Neoprene foam cut to shape

### Tone Hole Positions (for 24mm bore, Bb bass clarinet)
Based on standard bass clarinet calculations:
- Total acoustic length ≈ 1200mm (Bb fundamental)
- First tone hole ≈ 120mm from mouthpiece end
- Tone holes spaced ~40-80mm apart (larger spacing = lower notes)
- Hole diameters: 6mm-12mm depending on position
- Lower tone holes need larger diameters

### Hardware Store Shopping List
| Item | Size | Purpose | Est. Cost |
|---|---|---|---|
| PVC pipe | 1" Sch 40, 10ft | Main bore body | $3-5 |
| PVC end cap | 1" | Bottom closure | $0.50 |
| PVC coupling | 1" | Joining sections | $1 |
| PVC cement | Small can | Permanent joints | $5 |
| Silicone tubing | 1" ID x 1.25" OD, 6" | Neck joint seal | $3 |
| Silicone tubing | 25mm ID | Bell adapter seal | $3 |
| O-rings | Various | Airtight seals | $5 |
| Cork sheet | 1/32" to 1/16" | Tenon wrapping | $5 |
| Neoprene foam | 1/16" | Key pads | $5 |
| Stainless steel rod | 2mm x 450mm | Key pins | $5 |
| Music wire | 0.38mm | Springs | $5 |
| Bass clarinet bell | eBay/Chinese | Bell section | $30-60 |
| Bass clarinet mouthpiece | Standard | Sound production | $15-50 |
| Bass clarinet reed | Standard | Vibration source | $3-5 |

**Total estimated cost: $80-160** (vs $1000+ for a student bass clarinet)

---

## 7. Simulation Approach for PVC Pipe Bass Clarinet

### Using OpenWInD
1. **Model bore as CSV** — cylindrical sections with measured PVC dimensions
2. **Add tone holes** — OpenWInD supports Axianov tone holes
3. **Compute impedance** — find resonance frequencies, verify alignment with desired notes
4. **Simulate sound** — use `LIPS` player type for reed-coupled simulation
5. **Compare predicted vs actual** — record played notes, compare frequencies

### Key Considerations
- PVC pipe joints create **impedance discontinuities** — model as small radius changes
- 3D printed adapters have rougher surface than extruded PVC — may add damping
- Tone hole drilling in PVC creates burrs — must be cleaned for proper sealing
- Silicone/rubber joints are **lossy** — model with higher damping coefficient

---

## 8. Summary of Findings

### Best Pipes for Bass Clarinet Bore
1. **25mm European PVC** — closest to 24mm bore (1mm difference)
2. **1" Schedule 80 PVC** — ID = 25.4mm (1.4mm difference)
3. **1" Schedule 40 PVC** — ID = 26.6mm (2.6mm difference, needs bigger adapter)
4. **1" PEX tubing** — ID = 24.1mm (perfect match but flexible)

### Best 3D Printed Design Approach
1. Use PVC pipe for the main cylindrical bore (cheap, precise, rigid)
2. 3D print all adapter/transition pieces (neck, bell, register vent)
3. 3D print simplified key mechanisms (larger than metal keys)
4. Purchase: mouthpiece, reeds, bell, springs, pads, cork
5. Silicone tubing for flexible joints and seals

### Existing References
- **JDWoodwinds** — $100 STL files for complete 3D printed bass clarinet in G
- **Jared's YouTube** — 3D printed bass clarinet in G, simplified Boehm
- **Dan Bruner** — PVC clarinet in A3 using sax reed
- **Fabien T.** — PVC membrane clarinet with 3D printed mouthpiece
- **DangerousLadies** — 3D printed PVC twist-lock connectors
- **FlexiBuild** — Modular 3D printed PVC connector system

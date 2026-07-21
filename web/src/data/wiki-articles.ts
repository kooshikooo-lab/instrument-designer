export type WikiCategory =
  | "Instruments"
  | "3D Printing"
  | "Acoustics"
  | "Design"
  | "Tuning";

export type Difficulty = "Beginner" | "Intermediate" | "Expert";

export interface WikiArticle {
  id: string;
  title: string;
  category: WikiCategory;
  subcategory: string;
  tags: string[];
  difficulty: Difficulty;
  content: string;
  relatedArticles: string[];
  lastUpdated: string;
}

export const WIKI_CATEGORIES: WikiCategory[] = [
  "Instruments",
  "3D Printing",
  "Acoustics",
  "Design",
  "Tuning",
];

export const WIKI_ARTICLES: WikiArticle[] = [
  {
    id: "inst-flutes",
    title: "Flutes & Fipple Flutes",
    category: "Instruments",
    subcategory: "Flutes",
    tags: ["flute", "fipple", "recorder", "whistle", "folk", "pan-flute"],
    difficulty: "Beginner",
    lastUpdated: "2025-12-01",
    relatedArticles: ["inst-clarinets", "acoustics-bore", "printing-fdm-resin", "acoustics-tone-holes"],
    content: `## History

The flute family is one of the oldest in human archaeology. Bone flutes dating to roughly 40,000 years ago have been found in German caves. Over millennia the instrument diverged into two major branches: **edge-blown transverse flutes** (the Western concert flute, bansuri, and shakuhachi) and **fipple flutes** (recorders, tin whistles, ocarinas, and Native American flutes).

Medieval Europe saw the recorder rise to prominence. By the Renaissance, recorders were built in consorts from sopranino to great bass. The modern transverse flute evolved in the 17th-18th century, culminating in Theobald Boehm's 1847 ring-key system that standardized the modern orchestral flute.

## Acoustics & Bore Type

Most flutes operate as **open-open pipes** (or open-closed for vessel flutes like ocarinas). The pitch is determined primarily by the effective length of the air column. A half-closed finger hole shortens the effective length, raising the pitch.

- **Cylindrical bore** (tin whistle, recorder): Straight, consistent diameter. Produces a relatively pure tone with weaker odd harmonics in the lower register.
- **Conical bore** (some recorders, historical flutes): Tapers toward the foot. Enhances higher harmonics, producing a warmer, more complex tone.
- **Vessel bore** (ocarina, jug): Closed cavity. Pitch governed by the Helmholtz resonator formula; overtone structure is simpler, giving a characteristic pure tone.
- **Panaulic bore** (pan flute): Each tube is closed at one end. Only odd harmonics are present, producing a distinctly hollow, breathy sound.

## Key Mechanism

Simple-system flutes use **6 finger holes** plus a thumb hole, sometimes augmented by 1-2 keys for accidentals (typically Bb and F). The Boehm system uses a complex ring-key and axle mechanism to enable chromatic fingering across three octaves. For 3D-printed instruments, keyless designs are far simpler to fabricate; keys add mechanical complexity, require precise tolerances, and need padding materials.

## Playing Technique

- **Fipple flutes**: Air is directed across a fixed edge by the player's breath. Easier for beginners because embouchure is built into the instrument.
- **Transverse flutes**: The player must form a precise air stream with the lips across an embouchure hole. More expressive control but steeper learning curve.
- **Pan flutes**: Each tube produces one note. The player moves the instrument laterally, directing air across tube openings.

## 3D Printing Considerations

Fipple flutes are ideal first projects. The airway and labium geometry must be precise; print the mouthpiece vertically for best surface finish. Use 0.12mm layer height or finer. Test with a digital tuner after printing — minor bore adjustments via sanding or acetone smoothing can fine-tune pitch. Pan flutes print well as individual tubes joined with a printed bracket. Always seal PLA with clear coat if the instrument will contact moisture from breath.`,
  },
  {
    id: "inst-clarinets",
    title: "Clarinets & Single-Reed Woodwinds",
    category: "Instruments",
    subcategory: "Woodwinds",
    tags: ["clarinet", "single-reed", "chalumeau", "bass-clarinet", "saxophone"],
    difficulty: "Intermediate",
    lastUpdated: "2025-11-15",
    relatedArticles: ["inst-flutes", "inst-oboes", "acoustics-bore", "acoustics-impedance"],
    content: `## History

The clarinet evolved from the chalumeau, a simple single-reed folk instrument known since the 13th century. In 1700, Johann Christoph Denner of Nuremberg added a register key to the chalumeau, extending its range by a twelfth (19 semitones) — an acoustic property unique to cylindrical closed pipes. The instrument was named "clarinet" (little clarino) because its upper register resembled the trumpet.

Through the 18th and 19th centuries, keywork was gradually added. Hyacinthe Klose and Auguste Buffet adapted the Boehm flute system to the clarinet around 1843, producing the modern French system. The German (Oehler) system, refined by Ivan Muller, is still preferred in Germanic orchestras.

## Acoustics & Bore Type

The clarinet is a **cylindrical closed pipe** (closed by the reed, open at the bell). This gives it a unique property: it suppresses even-numbered harmonics in the lower register (chalumeau), producing a dark, hollow tone. The upper register (clarion) overblows at the twelfth rather than the octave, unlike virtually every other common instrument.

- **Bore diameter**: Typically 14.5-15mm for Bb soprano, up to 24mm for bass clarinet in G.
- **Bell flare**: Conical. The bell projects sound and tunes the lowest notes but has less effect on the upper register.
- **Register vent**: A small hole that destabilizes the fundamental mode, encouraging the instrument to speak in the next harmonic partial.

## Key Mechanism

Standard Boehm-system clarinets have 17 keys and 6 rings. For 3D-printed instruments, simplified key mechanisms (2-4 keys) are feasible. The keywork requires stainless steel rod, neoprene or leather pads, and springs. The "membrane clarinet" approach replaces the reed entirely with a thin plastic membrane, eliminating the need for keys and reed.

## Playing Technique

The clarinet requires a **single cane reed** (or synthetic equivalent) clamped to the mouthpiece by a ligature. Embouchure is formed by the lower lip covering the reed and the upper teeth resting on the mouthpiece. The player controls pitch via finger combinations, reed pressure, and air speed.

## 3D Printing Considerations

Print bore sections vertically for smooth interior surfaces. Use 100% infill for airtightness. Multi-part assembly with friction-fit or threaded joints allows tuning adjustments. For bass clarinets, combine 3D-printed parts with PVC pipe or brass tubing for the longest sections. A standard Bb clarinet mouthpiece works on many 3D-printed chalumeau designs. PETG or ABS is recommended over PLA for parts that contact moisture.`,
  },
  {
    id: "inst-oboes",
    title: "Oboes & Double-Reed Woodwinds",
    category: "Instruments",
    subcategory: "Woodwinds",
    tags: ["oboe", "bassoon", "double-reed", "shawm", "rackett"],
    difficulty: "Expert",
    lastUpdated: "2025-11-10",
    relatedArticles: ["inst-clarinets", "inst-flutes", "acoustics-bore", "acoustics-impedance"],
    content: `## History

Double-reed instruments date back to ancient Egypt and Mesopotamia. The European oboe descended from the shawm, a loud outdoor instrument brought to France by the Compagnie des hautbois around 1650. The French makers refined the shawm into the quieter, more expressive "hautbois" (oboe). The bassoon appeared around 1650 as a modification of the dulcian, with a folded conical bore enabling a practical length.

The modern orchestral oboe was standardized by the Triebert family in the 19th century. The German (Conservatoire) system uses a conservatoire key mechanism, while the simpler English system retains a more open tone.

## Acoustics & Bore Type

Double-reed instruments use a **conical bore** and behave acoustically as open pipes, unlike the clarinet. This means both even and odd harmonics are present, producing a richer, brighter tone. The narrow double reed acts as a high-impedance driver, giving the player exceptional control over intonation and dynamics.

- **Oboe bore**: Tapers from approximately 6.5mm (reed end) to 10mm (bell end).
- **Bassoon bore**: Tapers from ~5mm (bocal end) to ~35mm (bell end), folded back on itself for compactness.
- **Shawm bore**: Wider and more flared than the modern oboe, producing a louder, more penetrating tone.

The bocal (crook) connects the reed to the body, typically tapering from 4mm (reed) to 12mm (body) internal diameter over about 30cm.

## Key Mechanism

Modern oboes use 20+ keys. The Heckel bassoon system has 24 keys and 3 rings. For 3D printing, historical shawms with 0-3 keys are far more accessible. The rackett achieves bass range in a compact body by folding the bore into parallel channels.

## Playing Technique

Double reeds are made from cane (Arundo donax) split, shaped, and tied. The player blows into the narrow gap between the two blades, causing them to vibrate. The embouchure forms an airtight seal around the reed. Double-reed instruments are notoriously difficult to tune — small changes in reed shape or lip pressure cause large pitch shifts.

## 3D Printing Considerations

Double-reed instruments are among the hardest to 3D-print because the reed cannot be easily replicated in plastic. However, the body is straightforward: print bore sections vertically, seal with cyanoacrylate, and use a commercially available cane reed. The shawm is the most printable option — its wide bore and simple keywork are forgiving. For bassoon bocals, print as a mandrel and form brass tube over it.`,
  },
  {
    id: "inst-brass",
    title: "Brass Instruments",
    category: "Instruments",
    subcategory: "Brass",
    tags: ["brass", "trumpet", "trombone", "horn", "shofar", "valve", "slide"],
    difficulty: "Advanced",
    lastUpdated: "2025-11-20",
    relatedArticles: ["inst-flutes", "inst-clarinets", "acoustics-mouthpiece", "acoustics-bell"],
    content: `## History

The brass family evolved from natural lip-vibrated instruments (horns, shells, and animal horns) used for signaling across ancient civilizations. The modern trombone appeared in the 15th century as the "sackbut," using a slide to change pitch. Valved brass instruments emerged in the early 19th century — Heinrich Stolzel's piston valve (1818) made fully chromatic brass playing possible for the first time.

The trumpet evolved from cylindrical natural trumpets to valved instruments. The tuba, invented by Wilhelm Wieprecht and Johann Gottfried Moritz in 1835, provided a bass voice for the brass section.

## Acoustics

Brass instruments are **open pipes** played by buzzing the lips into a cup-shaped mouthpiece. The lip vibration acts as a valve, coupling the player's air column to the instrument's bore. The harmonic series is produced by varying lip tension and air speed.

- **Trumpet**: Cylindrical bore (~11.7mm) with a flared bell. Bright, projecting tone.
- **Trombone**: Cylindrical bore (~12.7mm), slide changes tube length. The most acoustically straightforward brass instrument.
- **French Horn**: Conical bore (mostly), ~11.5mm to ~17cm at the bell. Warm, mellow tone from the large bell flare.
- **Tuba**: Conical bore, largest standard brass instrument. Bore 18-20mm, bell up to 40cm diameter.

The **cutoff frequency** of the bell determines how many harmonics are radiated efficiently. Larger bells project lower harmonics more effectively.

## Key Mechanism

- **Piston valves**: Redirect air through additional tubing loops. Three valves give access to all chromatic notes.
- **Rotary valves**: Common on French horn and German brass. Faster mechanical action.
- **Slide**: The trombone slide changes length continuously, enabling true glissando.
- **Natural brass**: No valves — limited to the harmonic series of one tube length.

## 3D Printing Considerations

Fully 3D-printed trumpets and trombones are possible but challenging. The critical factors are airtightness and bore smoothness. Print sections at 100% infill with 0.12mm layers. Use threaded or friction-fit joints between sections. Valve mechanisms are the hardest part — the "Overly-Complicated Trumpet" uses slide-based valves instead of conventional pistons. For natural instruments (shofar, post horn), 3D printing works well since there are no moving parts.`,
  },
  {
    id: "inst-ocarinas",
    title: "Ocarinas & Vessel Flutes",
    category: "Instruments",
    subcategory: "Flutes",
    tags: ["ocarina", "vessel", "helmholtz", "chinese-xun", "sweet-potato"],
    difficulty: "Beginner",
    lastUpdated: "2025-12-10",
    relatedArticles: ["inst-flutes", "acoustics-bore", "acoustics-resonance", "printing-fdm-resin"],
    content: `## History

Vessel flutes are among the oldest musical instruments. The Chinese xun (bone or clay, ~7000 BCE) and the Greek aulos represent independent inventions across cultures. The modern ocarina was developed by Giuseppe Donati in Budrio, Italy around 1853, evolving from a folk toy ("bottle flute") into a chromatic musical instrument.

The 12-hole transverse ocarina became the standard form, capable of over an octave chromatic range. In East Asia, multi-chambered ocarinas maintain distinct traditions.

## Acoustics

Vessel flutes behave as **Helmholtz resonators**, not as open or closed pipes. The air inside the cavity oscillates as a mass-spring system, producing a fundamental frequency governed by:

    f = (c / 2pi) * sqrt(A / (V * L))

Where c is the speed of sound, A is the vent opening area, V is the cavity volume, and L is the vent neck length. Vessel flutes have a **very simple harmonic spectrum** — essentially a single resonant frequency with few overtones. The result is a pure, sweet tone with limited dynamic range.

Finger holes on ocarinas work by changing A (the effective vent area), not by shortening a tube. This is fundamentally different from cylindrical or conical flutes.

## Design Parameters

- **Volume vs. pitch**: Larger chamber = lower pitch. A bass ocarina might be 30cm across; a soprano pendant might be 5cm.
- **Number of holes**: 4-5 holes (simple) to 12 holes (full chromatic). More holes require more precise placement.
- **Vent placement**: Holes near the sounding edge (windway) affect pitch more than distant holes.

## 3D Printing Considerations

Ocarinas are **ideal for 3D printing**. They are single closed volumes with no bore to finish internally. Print with 100% infill for best resonance. The windway is the most critical geometry — print the mouthpiece section vertically. A small 5-hole ocarina can be printed in under an hour with no supports. Larger 12-hole designs may need to be split into halves, bonded with cyanoacrylate, and sealed.`,
  },
  {
    id: "inst-pan-flutes",
    title: "Pan Flutes & Multi-Pipe Instruments",
    category: "Instruments",
    subcategory: "Flutes",
    tags: ["pan-flute", "panpipes", "nai", "siku", "zampo\u00f1a"],
    difficulty: "Intermediate",
    lastUpdated: "2025-11-25",
    relatedArticles: ["inst-flutes", "inst-ocarinas", "acoustics-bore", "printing-material"],
    content: `## History

Pan flutes appear independently in cultures worldwide: the Romanian nai, the Andean siku/zampo\u00f1a, the Chinese sheng (which evolved into a free-reed instrument), and the Greek Pan's pipes. Legend attributes the instrument to the Greek god Pan.

The Andean siku comes in two sizes — ira (larger, lower) and arca (smaller, higher) — traditionally played in interlocking pairs (hocket). The Romanian nai, perfected by Gheorghe Zamfir, uses 20+ curved pipes arranged in a concave row.

## Acoustics

Each pipe in a pan flute is a **closed-end column** (closed at the bottom, open at the top). Only **odd harmonics** are present: f, 3f, 5f, 7f. This gives pan flutes their characteristic breathy, hollow timbre. The pitch is determined by the length of each tube:

    L = c / (4f)

Where c is the speed of sound (~343 m/s) and f is the desired frequency. For example, middle C (262 Hz) requires a tube approximately 32.7cm long.

## Design Considerations

- **Tube spacing**: Must match the player's mouth width for fast passages (typically 8-10mm center-to-center).
- **Tube diameter**: 10-15mm internal diameter is standard. Larger tubes are louder but harder to play softly.
- **Curve vs. flat arrangement**: Curved arrangements (like the nai) improve access to distant tubes.
- **Tuning**: Each tube is tuned individually by adjusting length.

## 3D Printing Considerations

Pan flutes are excellent 3D-printing projects. Print each tube separately (vertically for best bore finish) and join with a printed bracket, or print the entire assembly flat. No internal post-processing is needed. The "Whistle Pan Flute" design demonstrates a printable pan flute requiring no supports.`,
  },
  {
    id: "inst-shakuhachi",
    title: "Shakuhachi & End-Blown Flutes",
    category: "Instruments",
    subcategory: "Flutes",
    tags: ["shakuhachi", "end-blown", "japanese", "ney", "kaval"],
    difficulty: "Intermediate",
    lastUpdated: "2025-10-20",
    relatedArticles: ["inst-flutes", "inst-transverse", "acoustics-bore", "acoustics-mouthpiece"],
    content: `## History

The shakuhachi is a Japanese end-blown flute brought from China around the 8th century CE. Originally used in Japanese court music (gagaku), it became closely associated with the Fuke sect of Zen Buddhism. Komuso monks played the shakuhachi as a form of meditation ("blowing Zen").

The modern concert shakuhachi standardizes on five holes (1 thumb, 4 finger) with a notched blowing edge. Transverse embouchure variants exist in Scandinavian traditions and in the Turkish ney.

## Acoustics

The shakuhachi is a **closed-open cylindrical pipe** with a significant bore irregularity — the "nodo" (node), an internal thickening near the middle of the bore. The five-hole system, combined with half-holing and embouchure angle changes, produces a pentatonic minor scale (miyako-bushi) in the first octave.

Bore dimensions: Typically 20-25mm internal diameter, 50-60cm length. The blowing edge (utaguchi) is cut at a precise angle to create an efficient edge-tone oscillator.

## Playing Technique

The player blows across the notched edge at varying angles. Key techniques include:

- **Merkuri**: Sliding fingers over holes for continuous pitch bends
- **Yuri**: Vibrato achieved by head movement
- **Kari/Meri**: Head tilting to sharpen or flatten pitch

## 3D Printing Considerations

The PVC shakuhachi is one of the most accessible DIY instruments: a 55cm length of 20mm ID PVC pipe with 5 holes. For 3D-printed versions, the critical geometry is the utaguchi (blowing notch). Print the head section vertically, then cut the notch with a file. The bore should be printed at 100% infill.`,
  },
  {
    id: "inst-transverse",
    title: "Transverse Flutes (Side-Blown)",
    category: "Instruments",
    subcategory: "Flutes",
    tags: ["transverse", "side-blown", "bansuri", "irish-flute", "boehm"],
    difficulty: "Intermediate",
    lastUpdated: "2025-11-05",
    relatedArticles: ["inst-flutes", "inst-shakuhachi", "acoustics-bore", "acoustics-tone-holes"],
    content: `## History

Transverse flutes appeared in ancient China (dizi) and India (bansuri) millennia before reaching Europe. The Western transverse flute arrived in the 12th century via Byzantium. Baroque flutes (traverso) were conical, wooden, and used 1 or 2 keys. The 19th century brought Theobald Boehm's revolutionary 1847 design: a cylindrical bore, parabolic head joint, and a ring-key system.

Modern orchestral flutes use the Boehm system: a silver or nickel tube, C-foot or B-foot, with 16 keys. Simple-system flutes (6-hole, keyless or with 1-2 keys) survive in Irish traditional music.

## Acoustics

Transverse flutes are **open-open cylindrical pipes**. The embouchure hole acts as the excitation mechanism, creating an edge tone.

- **Head joint parabolic taper**: Tunes the second octave relative to the first.
- **Tone hole sizing**: Larger holes produce brighter tone and better intonation.
- **Cylindrical vs. conical**: Modern flutes are cylindrical; historical flutes are conical for a warmer tone.

The embouchure hole (typically 12-16mm for a concert flute) critically affects responsiveness and tone color.

## 3D Printing Considerations

6-hole transverse flutes (Irish flute style) are printable in 2-4 sections with friction-fit joints. The head joint with its embouchure hole requires the most care. The Axianov Irish Flute design is a proven printable model with hundreds of successful builds.`,
  },
  {
    id: "inst-overtone",
    title: "Overtone Flutes & Experimental Instruments",
    category: "Instruments",
    subcategory: "Flutes",
    tags: ["overtone", "fujara", "koncovka", "glissando", "experimental"],
    difficulty: "Beginner",
    lastUpdated: "2025-12-05",
    relatedArticles: ["inst-flutes", "inst-shakuhachi", "acoustics-harmonics", "acoustics-bore"],
    content: `## History

Overtone flutes produce different pitches by exciting successive harmonics of a single air column, rather than by covering finger holes. They appear in Slovak (fujara, koncovka), Scandinavian (seljefl\u00f8yte), and Romanian (tilinca) folk traditions.

In the experimental domain, instruments like the Glissotar use a sliding mechanism over a slit to achieve continuous pitch control.

## Acoustics

All wind instruments produce a harmonic series: f, 2f, 3f, 4f, 5f, etc. Overtone flutes exploit this directly. By varying air speed and lip tension, the player selects which harmonic speaks. Covering the open end shifts the entire series by an octave.

- **Fujara**: 140-200cm, bore 20-25mm. Three holes near the foot provide chromatic flexibility.
- **Koncovka**: 50-80cm, bore 15-18mm. May have 0-3 holes.
- **Tilinca**: 30-100cm, simplest form — just a hollow tube.

## 3D Printing Considerations

Overtone flutes are the simplest instruments to 3D print: a straight tube with a shaped mouthpiece. The Glissotar's slit-and-ribbon mechanism is printable but demands precision.`,
  },
  {
    id: "inst-hybrids",
    title: "Hybrid & Experimental Instruments",
    category: "Instruments",
    subcategory: "Hybrid",
    tags: ["hybrid", "cornett", "tarogato", "slide-sax", "experimental"],
    difficulty: "Expert",
    lastUpdated: "2025-10-15",
    relatedArticles: ["inst-brass", "inst-clarinets", "inst-oboes", "acoustics-bore"],
    content: `## History

Hybrid instruments combine elements from different instrument families. The cornett married a wooden body with finger holes to a brass-style cup mouthpiece, combining woodwind fingering with brass embouchure. The tarogato combines a single reed with a conical bore, producing a tone warmer than the saxophone.

## Acoustics

- **Cornett**: Conical bore with lip-vibrated excitation produces a rich harmonic spectrum with strong high partials.
- **Tarogato**: Single reed with conical bore produces a tone closer to the saxophone than the clarinet.
- **Slide saxophone**: Conical bore + slide creates unique intonation challenges.

## 3D Printing Considerations

Hybrids are the most challenging instruments to 3D print. The Zaxophone demonstrates a feasible approach: 3D-printed conical body with a commercial saxophone mouthpiece. These projects require intermediate to expert skills.`,
  },
  // ── 3D PRINTING ──
  {
    id: "printing-fdm-resin",
    title: "FDM vs Resin Printing for Instruments",
    category: "3D Printing",
    subcategory: "Process",
    tags: ["fdm", "resin", "sla", "pla", "petg", "comparison"],
    difficulty: "Beginner",
    lastUpdated: "2025-12-01",
    relatedArticles: ["printing-material", "printing-wall-thickness", "printing-surface-finish"],
    content: `## Overview

The two dominant 3D printing technologies for instrument making are **FDM** (Fused Deposition Modeling) and **Resin** (SLA/DLP).

## FDM Printing

FDM extrudes thermoplastic filament through a heated nozzle, depositing material layer by layer.

**Advantages for instruments:**
- Larger build volumes (up to 300x300x400mm) — sufficient for most flutes and clarinets
- Faster print times for large parts
- Lower material cost ($20-30/kg for PLA)
- Structural parts can withstand playing pressure

**Limitations:**
- Layer lines create internal bore roughness (affects tone)
- Anisotropic strength — weaker between layers
- Less detail on fine features

**Recommended for:** Flutes, recorders, pan flutes, ocarinas, didgeridoos, brass instrument bodies.

## Resin Printing (SLA/DLP)

Resin printers cure liquid photopolymer resin with UV light.

**Advantages for instruments:**
- Extremely smooth surfaces (0.025mm layer height)
- Fine detail — ideal for tone hole edges and embouchure geometry
- Isotropic strength (no layer-line weakness)
- Dimensional accuracy suitable for interlocking parts

**Limitations:**
- Small build volumes (typically 120x60x150mm)
- Resin is brittle unless using specialized formulations
- Post-processing required (UV cure, washing)
- Higher material cost ($30-60/L)

**Recommended for:** Mouthpieces, reed plates, small precision components, prototypes.

## Hybrid Approach

Many instrument makers use both: FDM for the main body (strength, size) and resin for precision components (mouthpieces, reed plates, key parts).`,
  },
  {
    id: "printing-material",
    title: "Material Selection Guide",
    category: "3D Printing",
    subcategory: "Materials",
    tags: ["pla", "petg", "abs", "asa", "tpu", "nylon"],
    difficulty: "Beginner",
    lastUpdated: "2025-11-20",
    relatedArticles: ["printing-fdm-resin", "printing-wall-thickness", "printing-post-processing"],
    content: `## Material Properties for Instruments

- **PLA**: High rigidity, bright tone. Low heat resistance (60\u00b0C). Easy to print. Food-safe when sealed. Best for practice instruments and prototypes.
- **PETG**: Medium rigidity, slightly warmer tone than PLA. Good moisture resistance (75\u00b0C). Excellent for playable instruments exposed to breath moisture.
- **ABS**: Medium rigidity. High heat resistance (100\u00b0C). Requires enclosed printer. Can be acetone-smoothed for polished bore surfaces.
- **ASA**: Like ABS but UV-resistant. Best for instruments stored in sunlight. 100\u00b0C heat resistance.
- **Nylon**: Excellent toughness and low friction. Good for key mechanisms and moving parts. Absorbs moisture — needs sealing for wind instruments.
- **TPU**: Flexible. Used for gaskets, pads, and seals between instrument sections. Not structural.

## Choosing for Instruments

- **Practice/prototype**: PLA — cheapest, easiest, fastest
- **Playable wind instrument**: PETG or ASA — moisture resistant, durable
- **Key mechanisms**: Nylon or PETG — low friction, strong
- **Seals and pads**: TPU — flexible, airtight
- **High-quality finish**: ABS with acetone vapor smoothing

## Sealing Breath-Contact Surfaces

All PLA and most FDM prints need sealing for wind instruments. Apply 2-3 coats of food-safe polyurethane, cyanoacrylate, or clear nail polish to the bore. PETG is naturally more moisture-resistant but still benefits from sealing.`,
  },
  {
    id: "printing-post-processing",
    title: "Post-Processing Techniques",
    category: "3D Printing",
    subcategory: "Techniques",
    tags: ["sanding", "smoothing", "sealing", "finishing", "acetone"],
    difficulty: "Intermediate",
    lastUpdated: "2025-11-18",
    relatedArticles: ["printing-material", "printing-surface-finish", "printing-wall-thickness"],
    content: `## Bore Finishing

The internal bore surface directly affects tone quality. Rough bore surfaces scatter sound waves and reduce projection.

1. **Sanding**: Start with 220 grit, progress through 400, 600, to 1000 grit. Wrap sandpaper around a dowel for cylindrical bores.
2. **Acetone smoothing** (ABS/ASA only): Place the part in a container with acetone vapor for 10-30 minutes. Produces a glass-smooth bore. Do not over-expose — geometry will distort.
3. **Cyanoacrylate coating**: Apply thin CA glue to the bore, let cure. Fill layer lines and seal porosity. Light sanding after cure.

## Exterior Finishing

1. **Fill layer lines**: Spot-fill with wood filler or UV resin, then sand smooth.
2. **Spray primer + paint**: Automotive filler primer fills imperfections. Finish with lacquer or enamel.
3. **Clear coat**: Protect against moisture and UV. Use polyurethane or lacquer.

## Assembly Finishing

- **Joint alignment**: Sand mating surfaces flat. Use a surface plate or glass for reference.
- **Friction fit tuning**: Apply PTFE tape to tenons for adjustable friction.
- **Gap filling**: Use cyanoacrylate with baking soda for instant, sandable gap fill.

## Sealing for Airtightness

1. Coat the entire bore with thin cyanoacrylate (thin CA wicks into micro-gaps)
2. For multi-part assemblies, apply silicone sealant or O-rings at joints
3. Test by blocking one end and blowing through the other — listen for hissing`,
  },
  {
    id: "printing-wall-thickness",
    title: "Wall Thickness & Structural Integrity",
    category: "3D Printing",
    subcategory: "Design",
    tags: ["wall-thickness", "infill", "structural", "airtight", "strength"],
    difficulty: "Beginner",
    lastUpdated: "2025-11-15",
    relatedArticles: ["printing-material", "printing-fdm-resin", "design-tolerances"],
    content: `## Minimum Wall Thickness

- **FDM**: Minimum 1.2mm (3 perimeters at 0.4mm nozzle). For airtight bores, use 1.6mm (4 perimeters).
- **Resin**: Minimum 0.8mm. Thinner walls are possible but fragile.

## Infill for Instruments

- **100% infill**: Required for wind instrument bores. Ensures airtightness and maximum rigidity. The slight weight increase is negligible for instruments.
- **15-20% infill**: Acceptable for non-acoustic parts (key mechanisms, stands, cases).
- **Gyroid infill**: Best pattern for partial infill — isotropic strength in all directions.

## Structural Considerations

- **Bore pressure**: Wind instruments experience internal pressure fluctuations of 1-5 Pa during normal playing. Even thin walls (1.2mm PLA) easily withstand this.
- **Drop resistance**: Instruments that may be dropped benefit from 3-4mm walls or impact-resistant materials (PETG, TPU shell over PLA core).
- **Joint stress**: Multi-part instruments experience stress at joints. Reinforce with wider walls (2mm+) at connection points.

## Airtightness Testing

After printing, test for air leaks:
1. Block one end of the bore with a finger or cork
2. Submerge in water and blow gently through the other end
3. Look for bubbles — these indicate leaks
4. Seal leaks with thin cyanoacrylate, then re-test`,
  },
  {
    id: "printing-surface-finish",
    title: "Surface Finish for Acoustic Performance",
    category: "3D Printing",
    subcategory: "Techniques",
    tags: ["surface-finish", "layer-height", "bore", "tone-quality", "roughness"],
    difficulty: "Intermediate",
    lastUpdated: "2025-11-12",
    relatedArticles: ["printing-post-processing", "printing-wall-thickness", "acoustics-bore"],
    content: `## Why Surface Finish Matters

The internal bore surface of a wind instrument affects how sound waves propagate. Rough surfaces create turbulence, reduce projection, and can cause unwanted noise (hissing or buzzing). A smooth bore produces a clearer, more focused tone.

## Layer Height Recommendations

- **0.20mm**: Acceptable for large-diameter bores (>20mm) and practice instruments
- **0.15mm**: Good balance of speed and quality for most instruments
- **0.12mm**: Recommended for instruments with small bores (<15mm) or where tone quality matters
- **0.08mm**: Best quality, but dramatically increases print time. Use for mouthpieces and precision parts

## Orientation Matters

Printing bore sections **vertically** (bore axis perpendicular to the build plate) produces the smoothest internal surfaces. Layer lines run around the bore circumference rather than along it, reducing the "staircase" effect on the bore wall.

## Post-Processing Comparison

| Method | Roughness Reduction | Time | Skill Needed |
|--------|-------------------|------|-------------|
| Sanding (400 grit) | 50-70% | 15 min | Low |
| Sanding (1000 grit) | 80-90% | 30 min | Low |
| CA glue coat | 60-80% | 10 min + cure | Low |
| Acetone vapor (ABS) | 95-99% | 15 min | Medium |
| Epoxy lining | 90-95% | 1 hr + cure | Medium |

## Acoustic Impact

Measurements on 3D-printed recorders show that bore surface roughness above Ra 10um measurably reduces sound pressure level at frequencies above 2kHz. Polishing the bore to Ra 1-2um (achievable with acetone smoothing on ABS) brings performance within range of traditional wooden instruments.`,
  },
  {
    id: "printing-overhangs",
    title: "Overhangs, Supports & Print Orientation",
    category: "3D Printing",
    subcategory: "Techniques",
    tags: ["overhangs", "supports", "orientation", "bridging", "printability"],
    difficulty: "Intermediate",
    lastUpdated: "2025-11-10",
    relatedArticles: ["printing-surface-finish", "printing-wall-thickness", "printing-post-processing"],
    content: `## Overhang Rules for Instruments

- **45-degree rule**: Overhangs up to 45 degrees from vertical print reliably without supports.
- **Bridge**: Horizontal spans (bridging) up to 5mm print well on most FDM printers. Longer bridges sag.
- **Internal supports**: Avoid supports inside bore sections — they are extremely difficult to remove. Design bores to print without internal supports.

## Orientation Strategies for Instruments

- **Fipple flute mouthpiece**: Print vertically with the airway pointing up. The narrow airway is the most critical geometry.
- **Bore sections**: Print vertically for best bore finish. Layer lines wrap around the circumference rather than creating ridges along the length.
- **Tone holes**: If the instrument has side tone holes, orient the part so holes face upward or at 45\u00b0 to avoid supports.
- **Multi-part assemblies**: Design each section to print vertically without supports. Use alignment features (pins, keys) printed separately if needed.

## Support Removal

If supports are unavoidable inside an instrument bore:
1. Use tree supports with 0.15mm interface gap for easy removal
2. Print support interface layers at 0.2mm gap
3. Remove supports before sealing — leftover support material in the bore ruins tone quality
4. Sand the bore smooth after support removal

## Design for Printability

- Add 0.5mm fillets to internal corners to reduce stress concentration
- Avoid horizontal holes in walls — make them slightly angled upward
- For snap-fit joints, account for 0.1-0.2mm clearance in the model
- Use chamfers instead of 45-degree overhangs where possible`,
  },
  {
    id: "printing-assembly",
    title: "Multi-Part Assembly Techniques",
    category: "3D Printing",
    subcategory: "Techniques",
    tags: ["assembly", "joint", "glue", "threaded", "friction-fit", "sealing"],
    difficulty: "Intermediate",
    lastUpdated: "2025-11-08",
    relatedArticles: ["printing-wall-thickness", "printing-post-processing", "design-tolerances"],
    content: `## Why Multi-Part?

Most wind instruments are too long to print in one piece. A soprano recorder is ~30cm; a bass clarinet neck is over 1m. Splitting into sections also allows:
- Printing each section with optimal orientation
- Tuning individual sections before final assembly
- Easy transport and storage
- Replacement of damaged sections

## Joint Types

**Friction fit (press fit)**
- Simplest method. Tenon (male) and socket (female) with 0.1-0.2mm interference.
- Apply PTFE tape to the tenon for adjustable fit.
- Good for: practice instruments, quick prototyping.

**Threaded joints**
- More secure. Print M8-M12 threads with 0.3mm clearance for smooth operation.
- Use thread-locking compound on the final assembly.
- Good for: instruments that need frequent disassembly.

**Cork/corkless joints**
- Traditional instrument joints use cork gaskets. 3D-printed alternatives: TPU sleeve or O-ring groove.
- Good for: production instruments, professional builds.

**Adhesive bonded**
- Cyanoacrylate (super glue) for permanent joints. Bonds PLA/PETG in seconds.
- Two-part epoxy for maximum strength. 5-minute cure time.
- Good for: permanent multi-part instruments.

## Alignment

Include alignment pins, keys, or flat sections to prevent rotation between joined parts. A 3mm alignment pin with 0.1mm clearance works well. For bore alignment, ensure the tenon is long enough (>10mm) to self-center.`,
  },
  // ── ACOUSTICS ──
  {
    id: "acoustics-bore",
    title: "Bore Theory: Cylindrical, Conical & Vessel",
    category: "Acoustics",
    subcategory: "Fundamentals",
    tags: ["bore", "cylindrical", "conical", "vessel", "pipe", "waveguide"],
    difficulty: "Intermediate",
    lastUpdated: "2025-11-20",
    relatedArticles: ["acoustics-impedance", "acoustics-harmonics", "acoustics-tone-holes", "inst-flutes"],
    content: `## Pipe Acoustics

A wind instrument's bore is the internal cavity through which air oscillates. The shape of the bore determines which frequencies are supported and how the instrument overblows.

## Cylindrical Bore

A pipe with constant cross-section. The simplest acoustic model.

- **Open-open pipe**: Supports all harmonics (f, 2f, 3f...). The fundamental wavelength is twice the pipe length. Examples: transverse flute, tin whistle.
- **Open-closed pipe**: Supports only odd harmonics (f, 3f, 5f...). The fundamental wavelength is four times the pipe length. Example: clarinet (closed by reed), shakuhachi.

The clarinet's cylindrical closed-pipe behavior is unique: it overblows at the 12th (3f) rather than the octave (2f), requiring more fingerings to cover the second register.

## Conical Bore

A pipe that tapers linearly from wider to narrower. Acoustically, a complete cone (closed at the narrow end) behaves like an open-open pipe — it supports all harmonics despite being closed. This is because the converging wavefronts reflect differently than in a cylinder.

- **Oboe**: Taper from 6.5mm to 10mm. Rich harmonic spectrum.
- **Saxophone**: Taper from ~12mm to ~70mm. Full harmonic series.
- **Bassoon**: Extreme taper, folded for compactness.

## Vessel (Helmholtz) Resonator

A closed cavity with one or more openings. The air oscillates as a mass-spring system:

    f = (c / 2pi) * sqrt(A / (V * L))

Where A = vent area, V = cavity volume, L = vent neck length. Vessel resonators produce essentially a single frequency with minimal overtones. This is why ocarinas have their characteristic pure, sweet sound.

## Hybrid Bores

Many instruments combine bore types:
- The clarinet has a cylindrical body with a conical bell
- The English horn has a conical bore with a spherical bell chamber (bulb)
- The fujara combines a cylindrical bore with a flared foot

These transitions affect impedance peaks and radiation efficiency at different frequencies.`,
  },
  {
    id: "acoustics-impedance",
    title: "Acoustic Impedance & Input Admittance",
    category: "Acoustics",
    subcategory: "Fundamentals",
    tags: ["impedance", "admittance", "resonance", "input-function", "peaks"],
    difficulty: "Expert",
    lastUpdated: "2025-11-15",
    relatedArticles: ["acoustics-bore", "acoustics-resonance", "acoustics-harmonics"],
    content: `## What is Acoustic Impedance?

Acoustic impedance (Z) is the ratio of acoustic pressure to volume flow rate at a given point in an instrument. It is analogous to electrical impedance in circuits.

    Z = P / U

Where P is sound pressure (Pa) and U is volume velocity (m\u00b3/s). High impedance means high pressure for a given flow — the instrument "resists" being driven at that frequency.

## Input Impedance

The input impedance measured at the embouchure (or mouthpiece) is the most important acoustic characteristic of a wind instrument. It is measured by:
1. Playing the instrument into a calibrated microphone
2. Sweeping a sine wave through the frequency range
3. Recording the pressure response

## Impedance Peaks and Playing

The player's lips (or reed) couple to the instrument at frequencies where the input impedance has **peaks**. At these frequencies, the instrument resonates strongly:
- The player does not need to exert much effort — the instrument "speaks" easily.
- The pitch is stable because small perturbations are corrected by the impedance peak.

At impedance **valleys** (minima), the instrument resists playing. These frequencies are avoided or produced weakly.

## Impedance and Tone Holes

Open tone holes create new impedance peaks by effectively shortening the air column. The lowest open hole dominates — it "vents" the column above it. Closed tone holes create side branches that affect peak heights and positions (cross-fingering effects).

## Practical Use

Impedance measurements help instrument designers:
- Predict the pitch of every fingering
- Identify weak or out-of-tune notes
- Compare prototypes to reference instruments
- Optimize tone hole size and position without extensive trial-and-error

The OpenWIND software (openwind.inria.fr) can simulate impedance curves for wind instruments with arbitrary bore profiles and tone hole configurations.`,
  },
  {
    id: "acoustics-resonance",
    title: "Resonance & Standing Waves",
    category: "Acoustics",
    subcategory: "Fundamentals",
    tags: ["resonance", "standing-wave", "harmonic", "fundamental", "mode"],
    difficulty: "Beginner",
    lastUpdated: "2025-11-22",
    relatedArticles: ["acoustics-bore", "acoustics-harmonics", "acoustics-tone-holes"],
    content: `## What is Resonance?

Resonance occurs when a system oscillates at its natural frequency with maximum amplitude. In a wind instrument, the air column inside the bore resonates at specific frequencies determined by its length, shape, and boundary conditions.

## Standing Waves

When sound waves bounce back and forth inside the bore, they interfere to form **standing waves** — stationary patterns of pressure variation. At resonance, the waves reinforce each other, producing a loud, stable tone.

- **Nodes**: Points of minimum pressure variation (maximum air movement)
- **Antinodes**: Points of maximum pressure variation (minimum air movement)
- An open end is a pressure node; a closed end is a pressure antinode

## Resonant Modes

The first few modes of common bore types:

**Open-open cylinder (length L):**
- Mode 1: f = c/(2L) — wavelength = 2L
- Mode 2: f = c/L — wavelength = L
- Mode 3: f = 3c/(2L) — wavelength = 2L/3

**Open-closed cylinder (length L):**
- Mode 1: f = c/(4L) — wavelength = 4L
- Mode 2: f = 3c/(4L) — wavelength = 4L/3
- Mode 3: f = 5c/(4L) — wavelength = 4L/5

## In Practice

The player excites the fundamental mode (lowest frequency) by default. To play higher notes, they either:
1. **Overblow**: Increase air speed to excite the next mode
2. **Vent**: Open a tone hole to shorten the effective length
3. **Register key**: Destabilize the fundamental, forcing the instrument to speak at a higher mode

The relationship between modes determines the fingering system. Cylindrical closed pipes (clarinet) have wider mode spacing than open pipes, requiring different fingering approaches.`,
  },
  {
    id: "acoustics-harmonics",
    title: "Harmonics & Overtone Series",
    category: "Acoustics",
    subcategory: "Fundamentals",
    tags: ["harmonics", "overtones", "spectrum", "timbre", "partial"],
    difficulty: "Beginner",
    lastUpdated: "2025-11-18",
    relatedArticles: ["acoustics-resonance", "acoustics-bore", "acoustics-tone-holes"],
    content: `## The Harmonic Series

Every vibrating air column produces not just one frequency, but a series of integer multiples called **harmonics** (or partials). For a fundamental frequency f:

- 1st harmonic (fundamental): f
- 2nd harmonic (first overtone): 2f
- 3rd harmonic: 3f
- 4th harmonic: 4f
- etc.

The relative strength of these harmonics determines the **timbre** (tone color) of the instrument.

## Harmonics and Bore Shape

Different bore types produce different harmonic spectra:

- **Open-open cylinder** (flute, tin whistle): All harmonics present, odd and even. Relatively pure tone.
- **Open-closed cylinder** (clarinet): Odd harmonics dominant in low register (f, 3f, 5f). Dark, hollow tone.
- **Conical bore** (oboe, saxophone): All harmonics present, often with strong higher partials. Bright, complex tone.
- **Vessel resonator** (ocarina): Essentially only the fundamental. Very pure, "hollow" sound.

## Timbre and Instrument Identification

The harmonic spectrum is why a clarinet and an oboe playing the same note sound different:
- Clarinet: Strong odd harmonics, weak even harmonics below the register break
- Oboe: Rich spectrum with strong 2nd, 3rd, and 4th harmonics

Players modify the harmonic spectrum by changing:
- Embouchure (lip tension and aperture)
- Air speed (faster = more high harmonics)
- Tongue position (affects oral cavity resonance)

## Overblowing

When a player overblows, they excite a higher harmonic mode. On a flute, overblowing the first mode produces the octave (2f). On a clarinet, overblowing produces the 12th (3f). This difference is why clarinet fingering systems are fundamentally different from flute systems.`,
  },
  {
    id: "acoustics-tone-holes",
    title: "Tone Holes: Size, Spacing & Venting",
    category: "Acoustics",
    subcategory: "Fundamentals",
    tags: ["tone-holes", "fingering", "venting", "cross-fingering", "chromatic"],
    difficulty: "Intermediate",
    lastUpdated: "2025-11-15",
    relatedArticles: ["acoustics-bore", "acoustics-impedance", "acoustics-harmonics", "inst-flutes"],
    content: `## How Tone Holes Work

Tone holes change the effective length of the air column by "venting" the bore. When a hole is opened, sound pressure at that point drops toward atmospheric, creating a new effective end for the vibrating column. The instrument sounds a higher pitch as the effective length shortens.

## Size and Venting Efficiency

Larger holes vent more efficiently — they lower the pitch more for a given position. The critical parameter is the ratio of hole diameter to bore diameter:

- **Small hole** (d/D < 0.3): Partially vents. The note above the hole is sharp and the tone is muffled.
- **Medium hole** (d/D = 0.3-0.5): Good compromise between playability and tone. Most 6-hole flutes use this range.
- **Large hole** (d/D > 0.5): Fully vents. Clean tone, accurate pitch, but harder to cover with fingers.

For 3D-printed instruments, oversized tone holes are often intentional — they can be filled with cork plugs or covered with tape for tuning.

## Hole Spacing

The standard 6-hole spacing for a diatonic flute follows a pattern based on the natural scale:
- Bottom hole: Determines the fundamental scale degree
- Successive holes: Spaced according to the logarithmic pitch scale
- Top holes are closer together than bottom holes (the bore tapers or the effective diameter changes)

## Cross-Fingerings

When not all lower holes are open, the closed holes below the open ones create side branches that affect pitch. This "cross-fingering" produces notes that are inherently out of tune and have different timbre than notes with all lower holes open. The clarinet and baroque recorder rely heavily on cross-fingerings for chromatic notes.

## Register Holes

A small hole (typically 2-3mm) placed at a specific position destabilizes the fundamental mode, forcing the instrument to speak at the next harmonic. This is how the clarinet and oboe extend their range into higher registers without requiring impractically small finger holes.`,
  },
  {
    id: "acoustics-bell",
    title: "Bell Design & Radiation",
    category: "Acoustics",
    subcategory: "Components",
    tags: ["bell", "flare", "radiation", "cutoff", "projector"],
    difficulty: "Intermediate",
    lastUpdated: "2025-11-12",
    relatedArticles: ["acoustics-bore", "acoustics-impedance", "inst-brass", "inst-oboes"],
    content: `## Function of the Bell

The bell serves three acoustic purposes:
1. **Impedance matching**: Couples the bore's internal sound to the open air, improving radiation efficiency
2. **Frequency-dependent radiation**: Larger bells project lower frequencies more effectively
3. **Tuning**: The bell primarily tunes the lowest notes (those with all tone holes closed)

## Bell Geometry

- **Flare rate**: How quickly the diameter increases. A gradual flare (exponential) radiates low frequencies efficiently. A sharp flare (hyperbolic) radiates higher frequencies.
- **Bell diameter**: Trumpet bells ~13cm, French horn ~30cm, tuba ~40cm. Larger = better low-frequency projection.
- **Bell cutoff frequency**: The frequency above which the bell radiates efficiently. Below this frequency, sound is mostly reflected back into the bore.

## Bell in Different Instruments

- **Clarinet**: Small bell flare. Projects sound but has minimal acoustic effect on the upper register. Most notes are unaffected by the bell.
- **Oboe**: Small, flared bell. Projects the lowest notes and adds warmth to the tone.
- **Trumpet**: Large, sharply flared bell. Major contributor to the instrument's projection and characteristic sound.
- **French horn**: Very large, slowly flared bell, often directed backward. The player's hand in the bell modifies the cutoff frequency for pitch and timbre control.

## 3D Printing Bells

Print bells with the opening facing up (or at 45\u00b0) to avoid supports. Layer lines should wrap around the flare for structural integrity. A parabolic or exponential flare profile is easiest to print and acoustically effective.`,
  },
  {
    id: "acoustics-mouthpiece",
    title: "Mouthpiece Physics: Reed & Lip-Vibrated",
    category: "Acoustics",
    subcategory: "Components",
    tags: ["mouthpiece", "reed", "embouchure", "lip-vibration", "cavity"],
    difficulty: "Intermediate",
    lastUpdated: "2025-11-10",
    relatedArticles: ["acoustics-bore", "acoustics-impedance", "inst-clarinets", "inst-brass"],
    content: `## Reed Mouthpieces (Single and Double)

A single reed (clarinet, saxophone) vibrates against a facing (tip opening) on the mouthpiece. The reed acts as a pressure-controlled valve:
- When lips compress the reed, the aperture closes, increasing pressure in the mouthpiece cavity
- The pressure increase pushes the reed open
- The cycle repeats at the resonant frequency of the coupled reed-bore system

**Key mouthpiece dimensions:**
- **Tip opening**: The gap between reed and facing at rest. Larger = more responsive, darker tone, harder to control. Smaller = easier to play, brighter tone.
- **Facing curve**: The profile of the mouthpiece facing. Longer facing = more reed vibration = warmer tone.
- **Chamber**: The internal cavity of the mouthpiece. Larger chamber = darker, more open sound. Smaller = brighter, more focused.
- **Baffle**: The top surface of the chamber. High baffle = bright, edgy tone (pop, jazz). Low baffle = dark, classical tone.

## Double Reed (Oboe, Bassoon)

The double reed has no mouthpiece body — the reed itself is the complete excitation system. Two cane blades vibrate against each other, creating a very narrow opening that opens and closes rapidly. The player's lips seal around the reed, and the internal reed geometry determines the tone.

## Brass Mouthpieces (Cup)

The brass mouthpiece has:
- **Cup**: The bowl-shaped cavity. Deeper cup = darker tone. Shallower = brighter.
- **Rim**: Where the lips rest. Flatter rim = more endurance, less flexibility.
- **Throat**: The constriction between cup and backbore. Affects air resistance and tone.
- **Backbore**: The taper from throat to shank. Controls projection and brightness.

## 3D Printed Mouthpieces

Mouthpieces are among the best candidates for 3D printing due to their small size and need for precise geometry. Resin printing excels here — the smooth surface finish and fine detail are ideal for facing curves and chambers. The 3D-printed clarinet mouthpiece on Printables uses a flexible bulb design that eliminates the need for cork.`,
  },
  // ── DESIGN ──
  {
    id: "design-parametric",
    title: "Parametric Design for Instruments",
    category: "Design",
    subcategory: "Methods",
    tags: ["parametric", "freecad", "openscad", "jscad", "variables", "formula"],
    difficulty: "Intermediate",
    lastUpdated: "2025-11-25",
    relatedArticles: ["design-export", "design-tolerances", "design-multi-part"],
    content: `## What is Parametric Design?

Parametric design defines a 3D model using variables (parameters) rather than fixed dimensions. Changing a parameter automatically updates the entire model. For instruments, this means you can create a single model that generates recorders in any key, flutes of any length, or ocarinas of any size.

## Why Parametric for Instruments?

- **Tuning**: Change the bore length parameter to retune the instrument without redrawing
- **Key selection**: Parameterize the fundamental frequency — all tone hole positions update automatically
- **Scaling**: Create soprano, alto, tenor, and bass variants from one model
- **Tolerance compensation**: Adjust for different printers by changing a clearance parameter

## Tools for Parametric Instrument Design

**OpenSCAD**
- Script-based 3D modeling. Write code that generates geometry.
- Excellent for bore profiles, tone hole arrays, and mathematical surfaces.
- Example: &#96;cylinder(h = bore_length, r1 = bore_top_radius, r2 = bore_bottom_radius);&#96;
- Free, cross-platform, large community.

**FreeCAD**
- GUI-based parametric CAD with spreadsheet-driven parameters.
- Part Design workbench for solid modeling. Path workbench for CNC.
- Better for complex shapes (bell flares, key mechanisms).
- Free, open-source, steep learning curve.

**JSCAD**
- JavaScript-based parametric CAD that runs in the browser.
- Good for web-integrated design tools (like Instrument Designer).
- Functions compose naturally in code. Export to STL.
- &#96;const bore = cylinder({ height: L, radius: R });&#96;

**Fusion 360 / Onshape**
- Cloud-based parametric CAD with built-in simulation.
- Free for personal use (Fusion 360) or educational (Onshape).
- Best GUI experience for complex mechanical assemblies.

## Tips

- Start with the acoustic parameters: bore length, diameter, tone hole positions
- Use a spreadsheet to calculate tone hole positions from the desired scale
- Parametric models are harder to set up but save enormous time in iteration
- Version control your design scripts — tuning is an iterative process`,
  },
  {
    id: "design-export",
    title: "Export Formats: STL, STEP & 3MF",
    category: "Design",
    subcategory: "Formats",
    tags: ["stl", "step", "3mf", "export", "mesh", "file-format"],
    difficulty: "Beginner",
    lastUpdated: "2025-11-20",
    relatedArticles: ["design-parametric", "design-tolerances", "printing-fdm-resin"],
    content: `## File Formats for 3D Printing

## STL (STereoLithography)

The universal format for 3D printing. Exports a triangulated mesh — no color, no internal structure, no units (assumed millimeters).

- **Binary STL**: Smaller file size. Default export from most CAD tools.
- **ASCII STL**: Human-readable, much larger files. Use for debugging.
- **Resolution**: STL has no inherent resolution. Finer meshes = smoother curves = larger files. Use 0.01mm chord tolerance for instruments.

**When to use STL**: Sending files to a slicer. Uploading to Printables/Thingiverse. Universal compatibility.

## STEP (Standard for the Exchange of Product Data)

A parametric CAD format that preserves exact geometry (NURBS surfaces, not triangles). Much larger files than STL but infinitely precise.

- **When to use STEP**: Archiving your design. Importing into another CAD program. CNC machining. 3D printing via services that accept STEP.

## 3MF (3D Manufacturing Format)

The modern replacement for STL. Supports:
- Color and materials
- Print settings (infill, supports, orientation)
- Lattice structures
- Unit specification

**When to use 3MF**: Multi-material prints. Sharing complete print setups. PrusaSlicer and Bambu Studio natively support 3MF.

## OBJ (Object File)

Wavefront OBJ format. Supports triangles, UV coordinates, and materials. Common in 3D modeling (Blender, Maya) but less useful for 3D printing.

## For Instrument Design

1. **Design** in your CAD tool (OpenSCAD, FreeCAD, etc.)
2. **Export STL** for printing — use fine mesh resolution for bore curves
3. **Export STEP** for archival and future modifications
4. **Export 3MF** if sharing with PrusaSlicer users who want your print settings
5. Use the **demakein preset** system to generate instruments from parameter files`,
  },
  {
    id: "design-tolerances",
    title: "Tolerances & Printer Calibration",
    category: "Design",
    subcategory: "Precision",
    tags: ["tolerance", "clearance", "calibration", "accuracy", "shrinkage"],
    difficulty: "Intermediate",
    lastUpdated: "2025-11-18",
    relatedArticles: ["design-parametric", "printing-wall-thickness", "printing-assembly"],
    content: `## What are Tolerances?

Tolerance is the allowable deviation from a designed dimension. In 3D printing, tolerances account for:
- Printer accuracy (typically +/-0.1-0.2mm for FDM, +/-0.05mm for resin)
- Material shrinkage (PLA: 0.3-0.5%, PETG: 0.5-1.0%, ABS: 0.8-1.5%)
- Layer adhesion effects

## Critical Dimensions in Instruments

**Bore diameter**: Tolerance of +/-0.2mm is acceptable for most instruments. The bore can be sanded or reamed after printing. Affects pitch by approximately 0.5% per 1% diameter change (minimal).

**Bore length**: This is the most critical dimension for pitch. A 300mm bore tuned to C (262 Hz) will be flat by ~1 semitone if printed at 316mm (5.3% error). Print a test section and measure before committing to the full instrument.

**Tone hole diameter**: +/-0.2mm tolerance is typical. Holes can be enlarged with a drill bit. Print undersize and ream to final diameter.

**Joint clearance**: For friction-fit joints, design 0.1-0.2mm clearance on FDM, 0.05-0.1mm on resin. Test on scrap pieces first.

## Calibration Steps

1. **Print a calibration cube** (20x20x20mm). Measure all sides. Calculate your printer's actual steps/mm.
2. **Print test cylinders** at target bore diameters. Measure with calipers.
3. **Print a bore section** at the target length. Play it with a known mouthpiece to verify pitch.
4. **Adjust your model** based on measured errors. A spreadsheet tracking nominal vs. actual dimensions is invaluable.

## Material Shrinkage Compensation

- PLA: Scale to 100.3-100.5% in X and Y (Z is usually accurate)
- PETG: Scale to 100.5-100.8%
- ABS: Scale to 100.8-101.5%
- These are starting points — measure your specific filament and adjust.`,
  },
  {
    id: "design-multi-part",
    title: "Multi-Part Instrument Assembly",
    category: "Design",
    subcategory: "Methods",
    tags: ["multi-part", "joint", "alignment", "modular", "tuning-section"],
    difficulty: "Intermediate",
    lastUpdated: "2025-11-15",
    relatedArticles: ["design-tolerances", "printing-assembly", "design-parametric"],
    content: `## Why Multi-Part?

Most wind instruments exceed the build volume of consumer 3D printers. A soprano recorder (~30cm) fits; a bass clarinet neck (>1m) does not. Multi-part design also enables:
- Printing each section with optimal orientation
- Tuning individual sections before final assembly
- Easy transport
- Replacement of damaged sections

## Splitting Strategy

- **At tone hole clusters**: Split between groups of tone holes. This preserves bore accuracy at critical points.
- **At natural joints**: Many instruments have natural break points (barrel, body, bell for clarinets).
- **At maximum diameter**: Split where the bore is widest for easiest printing.
- **Avoid splits near the embouchure or reed**: These areas need maximum precision and smoothness.

## Joint Design

**Tenon-and-socket**: The standard instrument joint. The tenon (male) slides into the socket (female).
- Tenon length: 15-25mm for stability
- Clearance: 0.1-0.2mm (FDM), 0.05mm (resin)
- Add a slight taper (0.5-1 degree) to the tenon for easy insertion

**Threaded joints**: For instruments that need frequent disassembly.
- Use trapezoidal or buttress threads (not V-threads) for better 3D printing
- Thread size: M10-M15 for most instruments
- Add thread-locking compound for permanent assembly

**Alignment features**: Pins, keys, or flats to prevent rotation between sections.
- 3mm alignment pin with 0.1mm clearance
- Printed or inserted (brass rod)

## Tuning Sections

Design one section (usually the barrel or head joint) to be adjustable:
- Sliding joint: Tenon slides in/out to adjust total bore length
- Screw adjustment: Threaded rod for fine-tuning (0.1mm resolution)
- Swappable sections: Print multiple sections at slightly different lengths

## Assembly Order

1. Print all sections with alignment marks
2. Dry-fit without adhesive to verify alignment
3. Apply cyanoacrylate or epoxy to permanent joints
4. Seal the complete bore with CA or polyurethane
5. Test with a tuner and adjust the tuning section`,
  },
  {
    id: "design-key-mechanisms",
    title: "Key Mechanism Design",
    category: "Design",
    subcategory: "Components",
    tags: ["keys", "mechanism", "boehm", "pad", "spring", "lever"],
    difficulty: "Expert",
    lastUpdated: "2025-11-10",
    relatedArticles: ["design-parametric", "design-tolerances", "inst-clarinets", "inst-flutes"],
    content: `## When Keys are Needed

Simple 6-hole instruments (folk flutes, whistles) play a diatonic scale without keys. Keys are needed for:
- **Chromatic notes**: Bb, F#, etc. that fall between the diatonic holes
- **Extended range**: Notes below the lowest open-hole position
- **Large holes**: Keys allow tone holes larger than a finger can cover, improving intonation and tone

## Key Mechanism Components

1. **Key cup**: The pad that covers the tone hole. Must seal airtight.
2. **Pad**: Soft material (neoprene, leather, cork) on the key cup that contacts the tone hole rim.
3. **Barrel/axle**: The pivot point around which the key rotates. Typically stainless steel rod.
4. **Lever/spatula**: The part the finger presses. Shaped for comfortable finger placement.
5. **Spring**: Provides return force to keep the key open or closed. Typically stainless steel wire.

## Simplified Keys for 3D Printing

Full Boehm-system keys (17+ on a clarinet) are extremely complex to 3D print. Instead:
- **Two-key systems**: Add Bb and F# keys to a 6-hole flute. Covers most chromatic needs.
- **Pinch keys**: Keys that the player squeezes between thumb and finger (like recorder Bb key).
- **Slide keys**: A sliding cover over a tone hole. Simpler mechanism, adjustable opening.

## Pad Material

- **Neoprene foam** (2mm): Cheap, easy to cut, decent seal. Good for practice instruments.
- **Leather pads**: Traditional. Excellent seal, long-lasting. Requires fitting.
- **Silicone O-rings**: Drop into a groove on the key cup. Self-sealing, durable.

## Tolerances for Keys

- Key cup to tone hole clearance: 1-2mm (must not bind)
- Axle hole diameter: rod diameter + 0.1mm
- Pad contact surface: must be flat within 0.1mm for airtight seal
- Spring attachment: 0.5mm hook or loop at the key barrel`,
  },
  // ── TUNING ──
  {
    id: "tuning-equal-temperament",
    title: "Equal Temperament (12-TET)",
    category: "Tuning",
    subcategory: "Systems",
    tags: ["equal-temperament", "12-tet", "equal-temperament", "conventional", "well-tempered"],
    difficulty: "Beginner",
    lastUpdated: "2025-12-01",
    relatedArticles: ["tuning-just-intonation", "tuning-historical", "tuning-microtonal", "acoustics-harmonics"],
    content: `## What is Equal Temperament?

Equal temperament divides the octave into 12 equally spaced semitones. Each semitone is a frequency ratio of the 12th root of 2 (~1.05946). This means:

- Every semitone has the same frequency ratio
- Any key can modulate to any other key with equal "out-of-tuneness"
- No interval (except the octave) is perfectly pure

The frequency of any note in 12-TET:

    f = 440 * 2^((n-69)/12)

Where n is the MIDI note number (A4 = 69 = 440 Hz).

## Why Equal Temperament Won

- **Modulation freedom**: Composers can change key mid-piece without retuning
- **Instrument standardization**: One set of fingerings works in all keys
- **Mass production**: Manufactured instruments and pianos can be tuned once and stay compatible

## Trade-offs

Every interval except the octave is slightly out of tune compared to the pure (just intonation) version:
- Perfect fifth: 700 cents (vs 702 cents just) — very close, barely noticeable
- Major third: 400 cents (vs 386 cents just) — noticeably sharp, especially in sustained chords
- Minor second: 100 cents (vs 112 cents just) — noticeably flat

## Implications for 3D-Printed Instruments

- **Design for 12-TET**: Most 3D-printed instruments are designed for equal temperament. Tone hole positions are calculated using equal-temperament formulas.
- **Flexible tuning**: Since 3D-printed instruments can be modified after printing (sanding, filling, or plugging tone holes), it's possible to retune to other systems.
- **Drone instruments**: Instruments like overtone flutes and didgeridoos are less bound to equal temperament because they produce fixed pitches.

## Alternatives in Practice

Some instruments naturally produce near-just intervals:
- Ocarinas (vessel flutes) produce pure intervals by nature of their Helmholtz resonance
- Overtone flutes produce the harmonic series, which is naturally just
- Fipple flutes with simple 6-hole fingering produce a just-intoned diatonic scale`,
  },
  {
    id: "tuning-just-intonation",
    title: "Just Intonation & Pure Intervals",
    category: "Tuning",
    subcategory: "Systems",
    tags: ["just-intonation", "pure-intervals", "ratio", "syntonic", "harmonic"],
    difficulty: "Intermediate",
    lastUpdated: "2025-11-25",
    relatedArticles: ["tuning-equal-temperament", "tuning-historical", "acoustics-harmonics"],
    content: `## What is Just Intonation?

Just intonation uses frequency ratios based on whole numbers from the harmonic series. Every interval is a pure, beating-free combination of harmonics.

Common just intervals:
- **Octave**: 2:1 — the most consonant interval
- **Perfect fifth**: 3:2 — almost identical to equal temperament (702 vs 700 cents)
- **Major third**: 5:4 — noticeably purer than equal temperament (386 vs 400 cents)
- **Minor third**: 6:5 — warmer and more resonant (316 vs 300 cents)
- **Major second**: 9:8 — the "whole step" (204 vs 200 cents)

## Advantages

- **Beating-free intervals**: Notes resonate together without the "roughness" caused by frequency beating in equal temperament
- **Richer chords**: Just-intoned major chords have a ringing, blended quality that equal temperament cannot match
- **Historical authenticity**: Medieval and Renaissance music sounds more "correct" in just intonation

## The Problem: Modulation

Just intonation works beautifully in one key but falls apart when modulating. In the key of C, a just-intoned D is 9:8 (= 204 cents), but a just-intoned D relative to G is 10:9 (= 182 cents). These are different pitches! This is why equal temperament was invented.

## 3D-Printed Just-Intonation Instruments

For fixed-key instruments (folk flutes, drone instruments, ocarinas), just intonation is easy to implement:
- Calculate tone hole positions using the exact ratios of the desired scale
- No need for chromatic flexibility — the instrument plays in one key
- The Ocarina can naturally produce just intervals due to its Helmholtz resonance

## Comma and Syntonic Comma

The difference between 5:4 and 81:64 (the Pythagorean major third) is the **syntonic comma** (~21.5 cents). This small interval is the source of tuning problems when trying to maintain pure thirds in a modulating system.`,
  },
  {
    id: "tuning-historical",
    title: "Historical Tuning Systems",
    category: "Tuning",
    subcategory: "Systems",
    tags: ["pythagorean", "meantone", "well-temperament", "historical", "zarlino"],
    difficulty: "Expert",
    lastUpdated: "2025-11-20",
    relatedArticles: ["tuning-equal-temperament", "tuning-just-intonation", "tuning-microtonal"],
    content: `## Pythagorean Tuning (Ancient Greece - Medieval)

Based on stacking perfect fifths (3:2). Starting from C:
C - G - D - A - E - B - F# - C#...

Every interval is derived from 3:2 and 2:1 ratios. Perfect fifths are pure, but thirds are harsh (81:64, ~408 cents — much sharper than the just 5:4 at 386 cents).

Used extensively in medieval European music. The circle of fifths does not close — the final fifth (from the stacked series back to the starting note) is a Pythagorean comma (~23.5 cents) flat.

## Meantone Temperament (15th-18th Century)

Distributes the Pythagorean comma across several fifths to produce pure or near-pure major thirds.

**Quarter-comma meantone**: Each fifth is narrowed by 1/4 of a syntonic comma, producing exactly pure major thirds (5:4 = 386 cents). The remaining intervals are well-distributed.

The "wolf fifth" (an unusably out-of-tune interval) appears in keys far from the home key. Instrument builders designed keyboards with split accidentals to tame the wolf.

## Well-Temperament (18th-19th Century)

Unlike equal temperament, well-temperament distributes the octave unevenly. Keys close to C are nearly just; keys far from C are more tempered. Each key has a distinct character.

Werckmeister III (1691) and Kirnberger III (1779) are famous well-temperament schemes. Bach's "Well-Tempered Clavier" was likely written for a well-temperament, not equal temperament.

## Implications for 3D-Printed Instruments

Historical tuning is highly relevant for:
- **Recorder consort**: Renaissance recorder consorts were tuned to a meantone or well-temperament system. A 3D-printed recorder consort tuned to quarter-comma meantone sounds markedly more resonant than one in equal temperament.
- **Shawm and cornett**: Historical instruments used Pythagorean tuning for thirds. Modern players on historical reproductions follow this.
- **Drone instruments**: Natural overtone drones are in just intonation by definition.

Retuning a 3D-printed instrument is as simple as enlarging or filling tone holes — a unique advantage over traditional instruments.`,
  },
  {
    id: "tuning-microtonal",
    title: "Microtonal Systems & Beyond 12-TET",
    category: "Tuning",
    subcategory: "Systems",
    tags: ["microtonal", "quarter-tone", "maqam", "raga", "24-tet", "edq"],
    difficulty: "Intermediate",
    lastUpdated: "2025-11-15",
    relatedArticles: ["tuning-equal-temperament", "tuning-just-intonation", "acoustics-tone-holes"],
    content: `## What are Microtones?

Microtones are intervals smaller than a semitone (100 cents). Many musical traditions around the world use scales with intervals between 50 and 300 cents — well outside the 12-TET framework.

## 24-TET (Quarter-Tone System)

Divides the octave into 24 equal parts of 50 cents each. A superset of 12-TET that adds quarter-tones between every semitone. Used in:
- **Arabic maqam music**: Many maqam scales use quarter-tone intervals (particularly the "half-flat" and "half-sharp")
- **20th-century Western music**: Composers like Charles Ives, Alois Haba, and Krzysztof Penderecki explored quarter-tone harmony
- **Turkish makam**: Uses comma-based divisions with up to 53 parts per octave

## Common Non-12 Scales

- **19-TET**: 19 equal divisions. Better major thirds than 12-TET (379 cents vs 386 cents just). Used in some microtonal guitar music.
- **31-TET**: 31 equal divisions. Excellent approximation of meantone temperament. Near-pure thirds and fifths.
- **53-TET**: 53 equal divisions. Near-perfect just intonation for all intervals up to the 7th harmonic. Used in Turkish theory (the comma system).
- **72-TET**: 72 equal divisions. Standard for modern Arabic music theory. Allows precise maqam intonation.

## Maqam and Raga

- **Arabic maqam**: 9 primary scales with characteristic intervals. Many use quarter-tones. The hijaz maqam (roughly Phrygian dominant) is widely known.
- **Indian raga**: 72 melakarta ragas in Carnatic music. Some use microtonal shrutis (22 per octave in theory). Just intonation principles apply.

## Designing Microtonal Instruments

3D-printed instruments are ideal for microtonal experimentation:
- **Tone hole placement**: Calculate positions for any scale using the same formulas as 12-TET, just with different interval sizes
- **Adjustable design**: Print with undersized holes and ream to the exact diameter for each interval
- **Multi-scale**: Some designers create instruments with switchable scales using removable plugs
- **Ocarinas**: Vessel resonators naturally produce microtonal intervals by varying hole size`,
  },
];

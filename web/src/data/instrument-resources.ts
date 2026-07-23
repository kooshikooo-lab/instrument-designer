import type { InstrumentResources, ResourceLink } from "./instruments";

export const INSTRUMENT_RESOURCES: Record<string, InstrumentResources> = {
  "Penny Whistle (Tin Whistle)": {
    tips: [
      "Start by blowing gently across the mouthpiece ÔÇö think of saying 'whew' quietly",
      "Cover finger holes completely with the flat part of your fingers, not the tips",
      "The first octave is played softly; blow harder for the second octave",
      "If a note sounds squeaky, check that all holes are fully covered",
      "Use a tuner app (like TonalEnergy) to check your pitch while practicing",
    ],
    links: [
      { title: "Chiff & Fipple ÔÇö Tin Whistle Guide", url: "https://www.chiffandfipple.com/", type: "tutorial", description: "Comprehensive beginner's guide to tin whistle" },
      { title: "Tin Whistle Tutorial for Beginners", url: "https://www.youtube.com/watch?v=DMZcX8joXG8", type: "video", description: "YouTube tutorial covering basics" },
      { title: "Irish Tin Whistle Sheet Music", url: "https://www.irishtune.info/", type: "other", description: "Collection of Irish tunes with whistle tabs" },
    ],
    faq: [
      { question: "Why does my whistle squeak?", answer: "Usually caused by not covering holes fully, or blowing too hard. Try softer breath and check finger placement." },
      { question: "Can I use a D whistle to play in other keys?", answer: "Yes, but you'll need to learn cross-fingering or half-holing techniques for chromatic notes." },
    ],
  },

  "Folk Flute": {
    tips: [
      "This is a Demakein-generated flute ÔÇö the bore is tapered for better intonation",
      "Print at 100% infill to mimic wood density and improve resonance",
      "Use 0.12mm layer height for smooth bore interior",
      "Assemble segments with acetone welding (ABS) or epoxy (PLA)",
      "Sand interior seams after assembly for clean airflow",
    ],
    links: [
      { title: "Paul Harrison's Flute Designs", url: "https://www.thingiverse.com/pfh/designs", type: "tutorial", description: "Original Demakein folk flute designs" },
      { title: "Demakein Design Tool", url: "https://logarithmic.net/pfh/design", type: "tutorial", description: "Generate custom wind instrument designs" },
    ],
  },

  "Recorder (Soprano)": {
    tips: [
      "Baroque fingering: the lowest hole is split for the little fingers",
      "Blow gently ÔÇö recorders are fipple flutes and don't need much pressure",
      "To play the upper octave, cover the thumb hole only halfway (pinch)",
      "Clean the windway periodically with a thin cloth to maintain tone quality",
    ],
    links: [
      { title: "Soprano Recorder Fingering Chart", url: "https://www.recorderhomepage.net/fingering-charts/", type: "tutorial", description: "Complete fingering diagram for Baroque recorder" },
      { title: "Team Recorder YouTube", url: "https://www.youtube.com/@teamrecorder", type: "video", description: "Excellent recorder tutorial series by Sarah Jeffery" },
    ],
  },

  "Pan Flute": {
    tips: [
      "Each pipe is tuned by its length ÔÇö sealed at the bottom, open at the top",
      "Blow across the top of each pipe at a slight angle, like blowing over a bottle",
      "Roll the instrument slightly to move between pipes smoothly",
      "Cover pipes with wax or hot glue to seal the bottom ends",
      "Tune each pipe by adding or removing wax from the sealed end",
    ],
    links: [
      { title: "Pan Flute Tuning Calculator", url: "https://www.omnicalculator.com/physics/pipe", type: "tutorial", description: "Calculate pipe lengths for any note" },
      { title: "Gheorghe Zamfir ÔÇö Pan Flute Master", url: "https://www.youtube.com/watch?v=0hnsJ-42Vns", type: "video", description: "Famous pan flute performance" },
    ],
    faq: [
      { question: "How many pipes do I need for a full octave?", answer: "You need 12 pipes for a chromatic octave, or 7 for a diatonic (major) scale." },
    ],
  },

  "Slide Whistle": {
    tips: [
      "Pull the piston out slowly for lower notes, push in for higher notes",
      "The slide works best when the inner tube is smooth and well-lubricated",
      "Try wrapping Teflon tape around the piston for a tighter seal",
      "Great for learning about the relationship between tube length and pitch",
    ],
    links: [
      { title: "How Slide Whistles Work", url: "https://www.youtube.com/watch?v=Q3rYRUG6Q2I", type: "video", description: "Demonstration of slide whistle acoustics" },
    ],
  },

  "Transverse Flute (C)": {
    tips: [
      "The embouchure hole is blown across (not into) ÔÇö like blowing over a bottle",
      "Position the flute so the blow hole is directly under your bottom lip",
      "Tilt the flute slightly downward to direct air across the hole",
      "G finger hole may be slightly flat ÔÇö half-hole to correct",
      "Glue head joint and body together permanently after test-fitting",
    ],
    links: [
      { title: "Transverse Flute Fingering Chart", url: "https://www.printables.com/model/577149", type: "tutorial", description: "PDF fingering chart included with the STL files" },
      { title: "How to Play Transverse Flute", url: "https://www.youtube.com/watch?v=7aEyHc3N4BY", type: "video", description: "Video demonstration" },
    ],
  },

  "Axianov Irish Flute (D)": {
    tips: [
      "This is a keyless design based on pre-Boehm 1600s flutes",
      "Print with 100% infill for proper resonance and weight",
      "The embouchure hole is larger than concert flute ÔÇö requires more air",
      "Use hot glue to join segments (reversible) or epoxy (permanent)",
      "Hundreds of successful builds worldwide ÔÇö check community for tips",
    ],
    links: [
      { title: "Axianov Irish Flute on Printables", url: "https://www.printables.com/model/1097180", type: "tutorial", description: "Full build instructions and community comments" },
      { title: "Irish Flute Tutorial", url: "https://www.youtube.com/watch?v=tF9X-xXbwEQ", type: "video", description: "Playing demonstration" },
      { title: "Marat Axianov ÔÇö Original Design", url: "https://www.thingiverse.com/thing:6639850", type: "other", description: "Original Thingiverse design by Axianov" },
    ],
  },

  "Glissonardo": {
    tips: [
      "Print with whistle head on build plate, no supports needed",
      "Use 15% grid infill and 2 wall loops for best results",
      "Make sure slot plane is parallel to print bed rails on moving-bed printers",
      "Play by covering the slot with your closed hand, then open fingers one by one",
      "This is based on Leonardo da Vinci's Codex Atlanticus fissure flute sketches",
    ],
    links: [
      { title: "Glissonardo on Printables", url: "https://www.printables.com/model/1516682", type: "tutorial", description: "STL, 3MF, and STEP files with build guide" },
      { title: "Glissonardo Sound Demo", url: "https://youtube.com/shorts/NSQ5zJAe3m4", type: "video", description: "Short video of the Glissonardo being played" },
      { title: "Glissonic Instruments", url: "https://glissonic.com/", type: "other", description: "The broader Glissonic instrument family" },
    ],
  },

  "Glissotar Purpleheart (Original)": {
    tips: [
      "Uses a magnetic ribbon mechanism instead of traditional tone holes",
      "Based on soprano saxophone ÔÇö overblows by an octave",
      "Range: ~2.5 octaves (low Ab to high Db) in concert pitch",
      "Can use standard soprano saxophone mouthpiece",
      "The magnetic strap can be pressed anywhere for continuous pitch control",
    ],
    links: [
      { title: "Glissonic Official Site", url: "https://glissonic.com/", type: "shop", description: "Order the Glissotar and learn more" },
      { title: "Glissotar Playing Demo", url: "https://www.youtube.com/watch?v=35HX0DXYB_0", type: "video", description: "D├íniel V├íczi demonstrating the Glissotar" },
      { title: "Guthman Competition 2022", url: "https://guthman.gatech.edu/2022-competition", type: "article", description: "Where Glissotar won First Prize and People's Choice" },
      { title: "Organology.net ÔÇö Glissotar", url: "https://organology.net/instrument/glissotar/", type: "article", description: "Detailed organological description" },
    ],
    faq: [
      { question: "How much does the Glissotar cost?", answer: "The Purpleheart model costs approximately $2,994 from authorized dealers like SAX.co.uk. Lead time is 3-6 months." },
      { question: "Can saxophone players adapt easily?", answer: "Yes ÔÇö it uses a soprano sax mouthpiece, has a conical bore, and overblows by an octave. The main challenge is learning the new ribbon fingering system." },
    ],
  },

  "Glissotar Jam (3D-Printed)": {
    tips: [
      "Same form and function as the Purpleheart model",
      "Made of durable bio-composite ÔÇö robust against moisture",
      "Slightly brighter tone with more upper harmonics than wooden version",
      "More affordable option for exploring the glissonic system",
    ],
    links: [
      { title: "Glissotar Jam ÔÇö Glissonic", url: "https://glissonic.com/shop/", type: "shop", description: "Purchase the 3D-printed Glissotar Jam" },
      { title: "Purpleheart vs Jam Comparison", url: "https://www.youtube.com/watch?v=dauNK-PqWys", type: "video", description: "Side-by-side playing comparison" },
    ],
  },

  "Glissopipe": {
    tips: [
      "Recorder-style form factor ÔÇö easier for beginners than the Glissotar",
      "Uses the same glissonic magnetic ribbon system",
      "Available in sopranino (F''), soprano (C''), and alto (G') tunings",
      "Three colors: orange, white, and blue",
      "Designed for beginners, educators, and families",
    ],
    links: [
      { title: "Glissopipe Official Site", url: "https://www.glissopipe.com/", type: "other", description: "Official Glissopipe information" },
      { title: "Glissopipe Kickstarter", url: "https://www.kickstarter.com/projects/gryllussamu/glissopipe-intuitive-acoustic-instrument", type: "shop", description: "Support the Glissopipe launch" },
      { title: "Team Recorder ÔÇö Glissopipe Review", url: "https://www.youtube.com/watch?v=WkO2SY7WfpI", type: "video", description: "Sarah Jeffery's review and demo" },
    ],
  },

  "PVC Shakuhachi": {
    tips: [
      "Use 20mm ID PVC pipe (Schedule 40 white, food-grade only)",
      "Total length: 55cm, sounding length: 54.3cm",
      "Cut mouthpiece from PVC joint pipe at 45┬░ angle",
      "Drill 10mm diameter holes at specified positions",
      "Use a tuner app to adjust hole sizes for accurate pitch",
    ],
    build_notes: [
      "Materials: PVC pipe (ID=20mm) + PVC joint pipe, ruler, scissors, cutter, saw, pen",
      "Cost: approximately $1 for materials",
      "Build time: 30 minutes with electric drill, half day without",
      "The sound will be as beautiful as a genuine shakuhachi",
      "Can use a scissors to make holes if no drill available (slower but works)",
    ],
    links: [
      { title: "shaku6.com ÔÇö PVC Shakuhachi Guide", url: "https://shaku6.com/pvc.php", type: "tutorial", description: "Complete step-by-step construction guide" },
      { title: "Shakuhachi Tuning App", url: "https://shaku6.com/mtuner/", type: "other", description: "Free tuner specifically for shakuhachi" },
      { title: "Monty Levenson ÔÇö Shakuhachi Making", url: "http://www.shakuhachi.com/Q-PCBStory.html", type: "article", description: "Precision Cast Bore technique using PVC as gauge" },
    ],
  },

  "PVC Native American Flute (G)": {
    tips: [
      "Use 3/4\" Schedule 40 white PVC pipe (food-grade, NOT gray drainage pipe)",
      "The 3D printed air-flow director (fetish) is the key component",
      "Air director dimensions: 25 x 15 x 6mm with 2 x 10 x 18mm slot",
      "Insert wine cork into one end of the pipe",
      "Much easier to play than transverse flutes ÔÇö fipple mouthpiece",
    ],
    build_notes: [
      "Print the air-flow director in Tinkercad (9 minutes print time)",
      "Mark finger hole positions with a pencil and ruler",
      "Drill holes slowly with progressive bit sizes",
      "Tune by adjusting hole positions while playing",
      "Based on PhreshAyer YouTube tutorial design",
    ],
    links: [
      { title: "PhreshAyer ÔÇö Build Tutorial", url: "https://www.youtube.com/watch?v=misjPOhd-9o", type: "video", description: "Detailed step-by-step build video" },
      { title: "UO DeArmond Makerspace", url: "https://blogs.uoregon.edu/scitechoutreach/2023/07/06/plumbing-pipe-music-building-a-pvc-flute/", type: "article", description: "Build experience writeup with photos" },
    ],
  },

  "PVC Pan Flute (8-Pipe)": {
    tips: [
      "Each pipe is tuned by its length ÔÇö closed at bottom, open at top",
      "Use 1/2\" PVC pipe for most notes, graduated lengths for scale",
      "Seal bottom ends with hot glue, epoxy, or PVC cement",
      "Glue pipes together in a flat or curved row",
      "Tune each pipe by trimming the open end (shorter = higher pitch)",
    ],
    build_notes: [
      "No 3D printer needed ÔÇö all hardware store materials",
      "Materials: PVC pipe, end caps or hot glue, sandpaper",
      "For a C major scale: pipe lengths from ~6cm (high C) to ~33cm (low C)",
      "Curve the arrangement for better ergonomics",
    ],
    links: [
      { title: "DIY PVC Pipe Flutes ÔÇö Instructables", url: "https://www.instructables.com/DIY-PVC-Pipe-Flutes/", type: "tutorial", description: "CC BY-SA 4.0 open source PVC flute guide" },
      { title: "Pan Flute Pipe Length Calculator", url: "https://www.omnicalculator.com/physics/pipe", type: "tutorial", description: "Calculate exact pipe lengths for any tuning" },
    ],
  },

  "3D Printable Soprano Recorder (pfh)": {
    tips: [
      "Designed by Paul Harrison using Demakein software",
      "Simple 6-hole fingering system, two octaves in tune",
      "Tapered bore for better intonation across the range",
      "Print at 100% infill to mimic wood density",
      "Available as 1-piece through 5-piece assembly",
    ],
    links: [
      { title: "Thingiverse ÔÇö Folk Flute Collection", url: "https://www.thingiverse.com/thing:162490", type: "tutorial", description: "All sizes: Soprano D, Alto G, Alto F, Tenor D, Tenor E" },
      { title: "MakerWorld Remix", url: "https://makerworld.com/en/models/1230415", type: "tutorial", description: "Remixed with print profiles and decorative rings" },
      { title: "Pflute (Chromatic Flute)", url: "https://makerworld.com/en/models/1387331", type: "tutorial", description: "Chromatic version with recorder-style fingering" },
      { title: "Demakein Design Tool", url: "https://logarithmic.net/pfh/design", type: "tutorial", description: "Generate your own custom instrument designs" },
    ],
  },

  "Saxophone Low A Extension": {
    tips: [
      "This extends Bb baritone sax range by one semitone to low A",
      "Use 4\" ID PVC pipe (Schedule 20 or 40), cut to 6\" length",
      "3D print an adapter to fit between extension tube and sax bell",
      "Foam weatherstrip seal provides press-fit without permanent modification",
      "Test with PVC cement only after confirming pitch accuracy",
    ],
    build_notes: [
      "Materials: 4\" PVC pipe (~$10), 3D printed adapter, foam weatherstrip seal",
      "The extension adds ~6 inches to the bell of the saxophone",
      "May require adjustment of low Bb reed response due to changed bell impedance",
    ],
    links: [
      { title: "DIY Saxophone Modifications", url: "https://www.youtube.com/results?search_query=saxophone+low+a+extension+pvc", type: "video", description: "Video tutorials for saxophone modifications" },
    ],
  },

  "Bass Clarinet Low C Extension (Modular)": {
    tips: [
      "Each U-tube section adds one semitone below standard low Eb",
      "Use 1 section for low D, 2 sections for low C",
      "Bore: ~30-35mm diameter, ~15-20cm per semitone",
      "Neoprene pads provide airtight seal at joints",
      "Stainless steel rods connect sections mechanically",
    ],
    build_notes: [
      "Print sections in PLA or PETG with 100% infill",
      "Test each section individually before connecting",
      "May need to adjust register vent timing for extended range",
    ],
    links: [
      { title: "Bass Clarinet Range Extensions", url: "https://www.youtube.com/results?search_query=bass+clarinet+low+c+extension", type: "video", description: "Tutorials on bass clarinet modifications" },
    ],
  },

  "Bassoon Bocal / Crook": {
    tips: [
      "The bocal transfers reed vibration to the bassoon body",
      "Heckel system: #1 (shortest, brightest) to #5 (longest, darkest)",
      "Length: ~30cm, tapers from ~4mm (reed) to ~12mm (body) ID",
      "Traditional materials: brass or German silver",
      "3D printing a bocal is experimental ÔÇö metal preferred for performance",
    ],
    links: [
      { title: "Bassoon Bocal Guide", url: "https://www.youtube.com/results?search_query=bassoon+bocal+guide", type: "video", description: "How to choose and maintain bassoon bocals" },
      { title: "Heckel Bocal Comparison", url: "https://www.bassword.com/bocals.html", type: "article", description: "Detailed comparison of Heckel bocal systems" },
    ],
    faq: [
      { question: "Which bocal number should I use?", answer: "#2 is the most common all-around choice. #1 for brighter/aggressive playing, #3-5 for darker/softer tone. Most players own multiple bocals." },
    ],
  },

  "JDWoodwinds Bass Clarinet in G": {
    tips: [
      "24mm bore with simplified Boehm keywork",
      "Requires: brass tubing for tenons, stainless steel rod for keys",
      "Neoprene pads, springs, and cork for key mechanisms",
      "Chinese bass clarinet bell from eBay needed",
      "Expert-level project combining 3D printing and clarinet repair skills",
    ],
    links: [
      { title: "JDWoodwinds Official", url: "https://jdwoodwind.com/", type: "shop", description: "STL files and build information" },
    ],
  },

  "PVC Pipe Bass Clarinet (Hybrid)": {
    tips: [
      "Uses 1\" Schedule 40 PVC pipe (ID: 26.6mm) as main bore",
      "3D printed adapters step down from 26.6mm to 24mm",
      "Hardware store materials: PVC pipe, silicone tubing, fittings",
      "Estimated total cost: $80-160 (vs $1000+ student bass clarinet)",
      "Use twist-lock connectors by DangerousLadies for joining pipe sections",
    ],
    build_notes: [
      "Shopping list: PVC pipe, 3D printed neck joint, bell adapter, register vent",
      "Bass clarinet mouthpiece required (not included)",
      "Bell can be sourced from eBay (Chinese student bass clarinet)",
      "Silicone tubing provides flexible joints at neck and bell connections",
    ],
    links: [
      { title: "JDWoodwinds ÔÇö PVC Bass Clarinet Info", url: "https://jdwoodwind.com/", type: "tutorial", description: "Bore specifications and build notes" },
      { title: "FlexiBuild PVC Connectors", url: "https://www.thingiverse.com/thing:5425215", type: "other", description: "Modular PVC connector system for 25mm pipe" },
    ],
  },

  "PVC Membrane Clarinet": {
    tips: [
      "Uses 16mm PVC electrical tubing as the body",
      "3D printed mouthpiece with balloon/latex membrane",
      "Adjust membrane tension by screwing the cap tighter or looser",
      "Easy to play ÔÇö no reed technique needed",
      "Based on Nicolas Bras' design, made by Fabien T.",
    ],
    links: [
      { title: "Printables ÔÇö PVC Membrane Clarinet", url: "https://www.printables.com/model/441519", type: "tutorial", description: "STL files and build instructions" },
      { title: "Nicolas Bras ÔÇö Membrane Clarinet Demo", url: "https://www.youtube.com/watch?v=Jk7J4_bneZo", type: "video", description: "Video demonstration of the instrument" },
    ],
  },

  "Inline Membrane Clarinet": {
    tips: [
      "Similar to Nicolas Bras design but inline like a traditional clarinet",
      "Uses O-rings (3/4\" ID, 7/8\" OD) to seal membrane compartment",
      "Includes modular PEX adapter for connecting to different pipe sizes",
      "PTFE tape recommended for sealing all threaded connections",
      "By Chad Allen ÔÇö tested and documented design",
    ],
    links: [
      { title: "Printables ÔÇö Inline Membrane Mouthpiece", url: "https://www.printables.com/model/487374", type: "tutorial", description: "STL files and detailed build guide" },
    ],
  },

  "Ultra-Compact Bass Clarinet": {
    tips: [
      "Experimental compact form factor for the bass clarinet family",
      "Folds the bore into a compact shape for portability",
      "Available on MakerWorld ÔÇö check print profiles for best results",
    ],
    links: [
      { title: "MakerWorld ÔÇö Compact Clarinet", url: "https://makerworld.com/en/models/2021364-clarinet-mustache", type: "tutorial", description: "STL files and print profile" },
    ],
  },

  "Dan Bruner's PVC Clarinet (A3)": {
    tips: [
      "Uses 1/2\" Schedule 40 PVC pipe body with alto sax reed",
      "Reed is wider than pipe ID ÔÇö shaped on belt sander for proper angle",
      "Finger holes tuned by ear using diatonic scale",
      "Reed secured with screw through PVC wall",
      "Modular design: same mouthpiece fits different 'note pipes' for different keys",
    ],
    links: [
      { title: "Dan Bruner's PVC Clarinet", url: "https://www.geocities.ws/danielbruner/instruments/clarA3.html", type: "tutorial", description: "Original build page with photos and instructions" },
    ],
  },

  "Alto Saxophone Hybrid (Zaxophone)": {
    tips: [
      "Combines alto sax mouthpiece with recorder-like body",
      "Conical bore produces saxophone-like tone",
      "Uses standard saxophone reed and mouthpiece",
    ],
    links: [
      { title: "Zaxophone on Cults3D", url: "https://cults3d.com/en/3d-model/gadget/3d-printable-alto-saxophone-hybrid-instrument", type: "tutorial", description: "STL files and description" },
    ],
  },

  "3DP Minisax (Pocket Sax)": {
    tips: [
      "Compact single-reed instrument ÔÇö variant of Xaphoon/MiniSax",
      "Uses a saxophone or clarinet reed",
      "Fits in a pocket ÔÇö great travel instrument",
    ],
    links: [
      { title: "Thingiverse ÔÇö 3DP Minisax", url: "https://www.thingiverse.com/thing:4732605", type: "tutorial", description: "STL files and community builds" },
    ],
  },

  "Classical Oboe (Lohner Copy / Yamamoto 2025)": {
    tips: [
      "Oboe is a CONICAL bore instrument — our current TMM optimizer only supports cylindrical bores",
      "The Yamamoto paper is the key reference: CT scan → 3D model → FDM print → validated acoustically",
      "FDM printer accuracy: finger hole diameter error <2.7%, inner bore diameter error ~1.3%",
      "Harmonic damping ratio error vs original: <0.2% — barely affects timbre",
      "Blind listening tests: subjects could NOT distinguish PLA replicas from original on short tones",
      "Material (PLA vs woody-PLA) made no significant difference — bore geometry dominates",
      "Key lesson: manufacturing tolerance is the bottleneck, not material physics",
    ],
    build_notes: [
      "YAMAMOTO CASE STUDY (2025): 'Reproduction of classical oboe using additive manufacturing and timbre evaluation'",
      "DOI: https://doi.org/10.1250/ast.e24.92  |  Journal: Acoustical Science & Technology 46(4)",
      "Original instrument: Johann Andreas Lohner (Nürnberg, c.1800), housed in Japanese museum collection",
      "Method: X-ray CT scan → Autodesk Fusion360 3D model → QIDI X-MAX FDM printer",
      "Two filament types tested: PLA (Mutoh Industries) and woody PLA (40% wood fiber composite)",
      "No significant timbre difference between PLA and woody-PLA — bore geometry is what matters",
      "HARMONIC ANALYSIS: Compared amplitude and damping ratio across multiple notes",
      "  - Amplitude of harmonics matched original at most notes",
      "  - Harmonic damping ratio error <0.2% vs original",
      "LISTENING TESTS: One-pair comparison, general one-tailed test",
      "  - Short tones: subjects could NOT distinguish replicas from original (p>0.05)",
      "  - Short musical phrases: experienced wind players COULD distinguish (p<0.05)",
      "  - Non-musicians could not distinguish even in phrases",
      "PRINTING SPECS: QIDI X-MAX FDM, output accuracy: finger hole Ø error <2.7%, bore Ø error ~1.3%",
      "RELATED: Coltman (referenced in paper) found same result with flutes — plastic head joints indistinguishable from silver/wood",
      "RELATED: RCM London project scanned/printed clarinets, recorders, cornetts from museum collection",
      "RELATED: Ricardo Simian (Oslo) — AM twin copies enable double-blind testing, color strongly influences perceived timbre",
      "IMPLICATION FOR US: Bore geometry dominates over material. Our optimizer needs to get geometry right to ±1.3% (FDM) or ±0.5% (SLA)",
      "IMPLICATION FOR US: Conical bore TMM is needed before we can optimize oboe designs",
      "JDWoodwinds (jdwoodwind.com) sells STL files for Denner-copy bass oboe — only commercial oboe STL I found",
      "Oboe dimensions: ~65cm total length, bore starts ~6mm (top) expanding conically to ~57mm at bell",
    ],
    links: [
      { title: "Yamamoto et al. (2025) — Full Paper", url: "https://doi.org/10.1250/ast.e24.92", type: "article", description: "Primary reference: CT scan → 3D print → acoustic validation of classical oboe" },
      { title: "J-STAGE PDF", url: "https://www.jstage.jst.go.jp/article/ast/46/4/46_e24.92/_pdf", type: "article", description: "Full paper PDF (Open Access, CC BY-ND 4.0)" },
      { title: "ResearchGate", url: "https://www.researchgate.net/publication/389795393", type: "article", description: "ResearchGate page with figures and citations" },
      { title: "RCM 3D Printed Musical Instruments Project", url: "https://www.rcm.ac.uk/research/projects/3dprintedmusicalinstruments/", type: "article", description: "Royal College of Music — CT scanning and printing historical instruments (clarinets, recorders, cornetts)" },
      { title: "Ricardo Simian — Tackling Complexity with AM (2025)", url: "https://journals.sagepub.com/doi/10.1177/20592043251387639", type: "article", description: "AM twin copies for double-blind testing, bore complexity analysis" },
      { title: "JDWoodwinds — Bass Oboe STL Files", url: "https://jdwoodwind.com/shop/p/bass-oboe", type: "shop", description: "Commercial STL files for Denner-copy bass oboe (A=440Hz)" },
      { title: "Oboe Dimensions Guide", url: "https://www.dimensionsguide.com/oboe-dimensions", type: "other", description: "Baroque, Classical, Viennese, Modern oboe dimensions" },
      { title: "Kreedo — Oboe Cane Shape Dimensions", url: "https://www.kreedo.de/en/oboe/oboe-shape-dimensions/", type: "other", description: "Detailed cane/shape dimensions for oboe family" },
    ],
    faq: [
      { question: "Why can't we optimize oboe designs yet?", answer: "The oboe has a CONICAL bore. Our current TMM (tmm_acoustics.py) only handles cylindrical bores (open-open and closed-open pipes). Conical bores require different wave equation solutions — the resonance modes follow a harmonic series (f, 2f, 3f...) like open-open cylindrical, but the impedance calculation is different. We need to implement conical bore TMM before oboe optimization is possible." },
      { question: "What did the Yamamoto paper actually prove?", answer: "Three things: (1) CT scanning can capture bore geometry accurate enough for acoustic replication (~1.3% bore error). (2) FDM 3D printing preserves harmonic structure (damping ratio error <0.2%). (3) Listeners cannot distinguish PLA replicas from originals in short tones — bore geometry dominates over material. The limitation: they didn't OPTIMIZE the design, they REPLICATED an existing one." },
      { question: "What manufacturing accuracy do we need?", answer: "Yamamoto achieved ~1.3% bore error with FDM and got acoustically valid instruments. SLA printing typically achieves ±0.05-0.1mm, which for a 6mm oboe bore is ~0.8-1.7% error. For our <3 cents computational target, we need manufacturing error below ~0.5% (achievable with calibrated SLA + shrinkage compensation)." },
    ],
  },

  "Modern Conservatory Oboe": {
    tips: [
      "The modern oboe has a CONICAL bore — requires conical bore TMM support (not yet implemented)",
      "Range: Bb3 to A6 (~2.5 octaves), key of C (soprano)",
      "25-34 keys on conservatory system, semi-automatic octave mechanism",
      "Tuning note A440 is traditionally provided by the oboist",
    ],
    links: [
      { title: "Oboe at Organology.net", url: "https://organology.net/instrument/oboe/", type: "other", description: "Comprehensive oboe overview with history and acoustics" },
    ],
  },

  "Baroque Oboe (Hautbois)": {
    tips: [
      "Baroque oboe has a CONICAL bore — requires conical bore TMM support",
      "3 sections: top joint, bottom joint, bell — held together with cork tenons",
      "Only 2-3 keys; chromatic notes via cross-fingerings (darker, less uniform tone)",
      "Reed: 88mm total (blades + staple). Staple: 63mm long, bottom Ø5.5mm",
      "Modern copies exist from museum CT scans (RCM London project)",
    ],
    links: [
      { title: "RCM 3D Printed Musical Instruments", url: "https://www.rcm.ac.uk/research/projects/3dprintedmusicalinstruments/", type: "article", description: "CT scanning and printing historical instruments including oboes" },
    ],
  },

  "Rackett (Sausage Bassoon)": {
    tips: [
      "Renaissance-era double reed instrument in a compact body",
      "Achieves very low bass range through folded bore design",
      "Requires a double reed (can be purchased or made from cane)",
    ],
    links: [
      { title: "Printables ÔÇö Rackett", url: "https://www.printables.com/model/1014532", type: "tutorial", description: "STL files for 3D printing" },
    ],
  },

  "Mini Ophicleide (Keyless Serpent)": {
    tips: [
      "Historical bass brass instrument with 6 finger holes",
      "Similar to a serpent but more compact",
      "Uses a brass or cornet mouthpiece",
    ],
    links: [
      { title: "Printables ÔÇö Mini Ophicleide", url: "https://www.printables.com/model/478359", type: "tutorial", description: "STL files and build notes" },
    ],
  },

  "PrintBone Trombone": {
    tips: [
      "Fully 3D-printed playable trombone with 8.5-inch bell",
      "Fits a Bach 42 slide connector",
      "PLA bell works surprisingly well acoustically",
      "OpenSCAD parametric design ÔÇö customizable",
    ],
    links: [
      { title: "Printables ÔÇö PrintBone v1.1", url: "https://www.printables.com/model/80017", type: "tutorial", description: "STL files, OpenSCAD source, and build guide" },
      { title: "PrintBone Demo", url: "https://www.youtube.com/watch?v=H_VVgddzFDI", type: "video", description: "Sound demonstration" },
    ],
  },

  "BASS Tin Whistle (in A)": {
    tips: [
      "Very low-pitched tin whistle ÔÇö uses 46mm ID tube (75cm long)",
      "Requires 1.5m of M4 threaded rod and 48 M4 nuts for key mechanism",
      "1mm thick rubber sheet for airtight valve seals",
      "Uses key mechanism similar to bassoon or saxophone keys",
      "Guido Gonzato's whistle guide is essential reading before building",
    ],
    links: [
      { title: "Printables ÔÇö BASS Tin Whistle", url: "https://www.printables.com/model/475125", type: "tutorial", description: "14 STL files with detailed build instructions" },
      { title: "Guido Gonzato ÔÇö Whistle Guide", url: "https://www.guidogonzato.it/whistle/", type: "tutorial", description: "Essential reference for whistle construction" },
    ],
  },

  "Daphnis Pan Flute": {
    tips: [
      "Tuned 3D-printable pan flute with curved pipe arrangement",
      "Graduated pipes for easy playability",
    ],
    links: [
      { title: "Printables ÔÇö Daphnis Pan Flute", url: "https://www.printables.com/model/439762", type: "tutorial", description: "STL files for the Daphnis pan flute v10" },
    ],
  },

  "Side-Blown Flute in A Major": {
    tips: [
      "3-part side-blown flute in A major with 6 finger holes",
      "Glue-together assembly ÔÇö test fit before gluing",
    ],
    links: [
      { title: "Printables ÔÇö Side-Blown Flute", url: "https://www.printables.com/model/1001883", type: "tutorial", description: "STL files and build guide" },
      { title: "Nicolas Bras ÔÇö Flute Demo", url: "https://www.youtube.com/watch?v=UJITjxPpH4E", type: "video", description: "Playing demonstration" },
    ],
  },

  "Traditional Bansuri B Natural": {
    tips: [
      "Traditional keyless North Indian bansuri with large bore",
      "Productions a deep, mellow sound characteristic of Hindustani music",
      "Blow across the embouchure hole at an angle",
    ],
    links: [
      { title: "Bansuri on Cults3D", url: "https://cults3d.com/en/3d-model/gadget/traditional-keyless-north-indian-bansuri-b-natural-transverse-flute", type: "tutorial", description: "STL files for the bansuri" },
    ],
  },

  "Dragon Recorder": {
    tips: [
      "Fully playable soprano recorder shaped like a dragon",
      "Uses Baroque fingering system",
      "Decorative but functional ÔÇö great gift or display piece",
    ],
    links: [
      { title: "Printables ÔÇö Dragon Recorder", url: "https://www.printables.com/model/400647", type: "tutorial", description: "STL files with print profiles" },
    ],
  },

  "12-Hole Ocarina (Alto C)": {
    tips: [
      "Fully playable 12-hole ocarina covering over an octave",
      "Accurate tuning ÔÇö play along with piano or other instruments",
      "Hold with both hands, thumb holes on bottom, finger holes on top",
    ],
    links: [
      { title: "Printables ÔÇö 12-Hole Ocarina", url: "https://www.printables.com/model/24540", type: "tutorial", description: "STL files with makes and comments" },
    ],
  },

  "Small 5-Hole Ocarina": {
    tips: [
      "Small ocarina for kids ÔÇö range C5 to D6",
      "Prints without supports, plays right off the build plate",
      "Great introduction to wind instruments for children",
    ],
    links: [
      { title: "Printables ÔÇö Small Ocarina", url: "https://www.printables.com/model/249010", type: "tutorial", description: "STL files designed for kids" },
    ],
  },

  "Reedpipe": {
    tips: [
      "Simple single-reed pipe ÔÇö like a clarinet practice chanter",
      "Great introduction to reed instruments before moving to clarinet/saxophone",
      "Uses a single reed (can be 3D printed or use a clarinet reed)",
    ],
    links: [
      { title: "Demakein Reedpipe", url: "https://github.com/pfh/demakein", type: "tutorial", description: "Generate custom reedpipe designs with Demakein" },
    ],
  },

  "Modern Chalumeau in C": {
    tips: [
      "Simple clarinet in C with two extension keys",
      "3-part body: bell, barrel, and main section",
      "Historical precursor to the modern clarinet",
    ],
    links: [
      { title: "Printables ÔÇö Chalumeau", url: "https://www.printables.com/model/752555", type: "tutorial", description: "STL files for the modern chalumeau" },
    ],
  },

  "C Clarinet Remix (14mm Bore)": {
    tips: [
      "Remix of Tom's Chalumeau with 14mm bore",
      "3-part split body for easier printing and assembly",
      "Adjustable tuning via sliding joints",
    ],
    links: [
      { title: "Printables ÔÇö C Clarinet Remix", url: "https://www.printables.com/model/888905", type: "tutorial", description: "STL files and remix notes" },
    ],
  },

  "Membrane Clarinet": {
    tips: [
      "Fully 3D-printed ÔÇö no metal keys or reeds needed",
      "Uses a thin plastic sheet as a membrane reed",
      "Screw-together assembly for easy disassembly",
    ],
    links: [
      { title: "Printables ÔÇö Membrane Clarinet", url: "https://www.printables.com/model/495171", type: "tutorial", description: "STL files and build guide" },
      { title: "Membrane Clarinet Demo", url: "https://www.youtube.com/watch?v=Jk7J4_bneZo", type: "video", description: "Sound demonstration" },
    ],
  },

  "Curvy Clarinet": {
    tips: [
      "Compact curvy design with soprano saxophone mouthpiece",
      "6-note pentatonic layout ÔÇö easy to play melodies",
    ],
    links: [
      { title: "Printables ÔÇö Curvy Clarinet", url: "https://www.printables.com/model/1605969", type: "tutorial", description: "STL files for the curvy clarinet" },
    ],
  },

  "Clarinet Mouthpiece (Playable)": {
    tips: [
      "Playable Bb clarinet mouthpiece",
      "Flexible bulb eliminates need for cork",
      "Can be used on any Bb clarinet as a replacement mouthpiece",
    ],
    links: [
      { title: "Printables ÔÇö Clarinet Mouthpiece", url: "https://www.printables.com/model/557889", type: "tutorial", description: "STL files for the mouthpiece" },
    ],
  },

  "Trumpet Mouthpiece 3C": {
    tips: [
      "Based on Kanstul comparator profiles",
      "3C is a medium cup ÔÇö versatile for most playing situations",
      "Print on its side for strength and better bore finish",
    ],
    links: [
      { title: "Printables ÔÇö 3C Mouthpiece", url: "https://www.printables.com/model/446505", type: "tutorial", description: "STL files with comparator data" },
    ],
  },

  "Trumpet Mouthpiece 7C": {
    tips: [
      "Standard 7C ÔÇö the most common beginner mouthpiece",
      "Shallower cup than 3C ÔÇö easier for beginners",
      "Print on its side for best results",
    ],
    links: [
      { title: "Printables ÔÇö 7C Mouthpiece", url: "https://www.printables.com/model/100591", type: "tutorial", description: "STL files for the 7C mouthpiece" },
    ],
  },

  "Trumpet Mouthpiece Puller": {
    tips: [
      "Tool for removing stuck mouthpieces from trumpets",
      "Uses 1/4-20 hardware (nuts and bolts)",
      "Print in strong material (PETG or ABS) for durability",
    ],
    links: [
      { title: "Printables ÔÇö Mouthpiece Puller", url: "https://www.printables.com/model/692679", type: "tutorial", description: "STL files and hardware list" },
    ],
  },

  "D5 Drone Flute": {
    tips: [
      "Drone flute tuned to the Hijaz maqam (middle-eastern scale)",
      "Melody pipe and separate drone pipe sound simultaneously",
    ],
    links: [
      { title: "MakerWorld ÔÇö D5 Drone Flute", url: "https://makerworld.com/en/models/566278", type: "tutorial", description: "STL files for the D5 drone flute" },
    ],
  },

  "Double Native American Flute": {
    tips: [
      "Two pipes: melody pipe and separate drone pipe",
      "Tuned to F# ÔÇö a common key for Native American flutes",
    ],
    links: [
      { title: "Printables ÔÇö Double Flute", url: "https://www.printables.com/model/452234", type: "tutorial", description: "STL files for the double flute" },
    ],
  },

  "Overly-Complicated Trumpet": {
    tips: [
      "Fully 3D-printed trumpet with 6 slide-based valves",
      "Based on Bb trumpet tubing lengths",
      "Impressively complex mechanical design",
    ],
    links: [
      { title: "Printables ÔÇö Overly-Complicated Trumpet", url: "https://www.printables.com/model/492588", type: "tutorial", description: "STL files and build instructions" },
    ],
  },

  "Kudu Horn Trumpet (Shofar)": {
    tips: [
      "Functional Kudu horn trumpet inspired by the Jewish shofar",
      "Smooth spiral shape ÔÇö plays as a natural brass instrument",
    ],
    links: [
      { title: "Printables ÔÇö Kudu Horn", url: "https://www.printables.com/model/217052", type: "tutorial", description: "STL files for the shofar" },
    ],
  },

  "Kazoo": {
    tips: [
      "Hum into it ÔÇö don't blow. The membrane vibrates with your voice",
      "Replace the membrane with balloon rubber or wax paper if it wears out",
    ],
    links: [
      { title: "Printables ÔÇö Kazoo", url: "https://www.printables.com/model/30637", type: "tutorial", description: "Classic kazoo STL files" },
    ],
  },

  "HEXADIDG Didgeridoo": {
    tips: [
      "Produces a deep drone tone using circular breathing",
      "Hexagonal shape reduces print time while maintaining acoustic properties",
      "Two sizes available: full and mini",
    ],
    links: [
      { title: "Printables ÔÇö HEXADIDG", url: "https://www.printables.com/model/734618", type: "tutorial", description: "STL files for the hexagonal didgeridoo" },
    ],
  },

  "Folk Shawm": {
    tips: [
      "Double-reed folk instrument ÔÇö related to oboe and bombarde",
      "Uses compact hole placement for easier fingering",
      "A double reed is needed (can be purchased or made from cane)",
    ],
    links: [
      { title: "Demakein Folk Shawm", url: "https://github.com/pfh/demakein", type: "tutorial", description: "Generate custom shawm designs" },
    ],
  },

  "Shawm": {
    tips: [
      "Full-size double-reed shawm ÔÇö larger and more powerful than folk version",
      "Medieval/Renaissance era instrument",
    ],
    links: [
      { title: "Demakein Shawm", url: "https://github.com/pfh/demakein", type: "tutorial", description: "Generate custom shawm designs" },
    ],
  },

  "Reed Drone": {
    tips: [
      "Continuous-sounding reed drone pipe for bagpipe use",
      "Tie or tape the reed shut for continuous sound",
    ],
    links: [
      { title: "Demakein Reed Drone", url: "https://github.com/pfh/demakein", type: "tutorial", description: "Generate custom drone designs" },
    ],
  },

  "Three-Hole Whistle (Tabor Pipe)": {
    tips: [
      "Medieval three-hole tabor pipe ÔÇö played one-handed",
      "The other hand plays a drum (tabor)",
      "Can produce a surprising range with overblowing",
    ],
    links: [
      { title: "Demakein Tabor Pipe", url: "https://github.com/pfh/demakein", type: "tutorial", description: "Generate custom tabor pipe designs" },
    ],
  },

  "Dorian Whistle": {
    tips: [
      "Tuned to the Dorian mode ÔÇö moody, minor-style scale",
      "Ideal for folk music, Celtic, and medieval styles",
    ],
    links: [
      { title: "Demakein Dorian Whistle", url: "https://github.com/pfh/demakein", type: "tutorial", description: "Generate custom whistle designs" },
    ],
  },

  "Koncovka (Slovak Overtone Flute)": {
    tips: [
      "Overtone flute ÔÇö no finger holes needed for basic play",
      "Blow gently into the fipple; overblow to jump to higher harmonics",
      "Open and close the bottom end with your palm to switch between even+odd and odd-only harmonics",
      "The harmonic series gives you a diatonic Mixolydian-like scale",
      "Print the 3D head at 0.2mm layer, 4 walls, 15% infill for best sound",
      "Use 16-20mm PVC pipe, cut to length for your desired key (50-80cm for C-G)",
    ],
    build_notes: [
      "3D printed head: BY BRAS 20mm system or custom design",
      "PVC pipe body: friction fit with tape wrap for airtight seal",
      "Optional: add 3 holes near the end for extended diatonic access",
      "End correction: add ~5mm to calculated tube length",
    ],
    links: [
      { title: "BY BRAS Overtone Flute System", url: "https://instrumentsbybras.com", type: "shop", description: "3D printed overtone flute heads + PVC pipe system" },
      { title: "Fujara.sk ÔÇö Slovak Overtone Flutes", url: "https://fujara.sk", type: "article", description: "Traditional Slovak koncovka and fujara history" },
      { title: "Build Your Own Overtone Flute (YouTube)", url: "https://www.youtube.com/watch?v=BY_BRAS_overtone", type: "video", description: "Step-by-step BY BRAS system build tutorial" },
    ],
    faq: [
      { question: "Why can't I produce any sound?", answer: "Make sure the fipple edge is clean and sharp. Blow gently across the hole, not into it. The air jet should strike the sharp edge at an angle." },
      { question: "How do I play different notes?", answer: "Blow harder to jump to higher harmonics (overblowing). Cover/uncover the bottom end with your palm to switch between open (even+odd harmonics) and closed (odd harmonics only) tube modes." },
    ],
  },

  "Fujara (Large Slovak Overtone Flute)": {
    tips: [
      "Very large instrument (140-200cm) ÔÇö played standing, held vertically",
      "The 3 holes near the end extend the diatonic scale",
      "Deep, meditative sound ÔÇö great for drone music and meditation",
      "Use a neck strap or rest the bottom on the floor",
      "PVC version: use 20-25mm pipe, 3D printed head with larger bore fipple",
    ],
    build_notes: [
      "Main pipe: 20-25mm PVC, 140-200cm length for key of G",
      "3D printed head with 25mm bore fipple",
      "Tone holes: 10-12mm diameter, positioned per BY BRAS blueprints",
      "Add a floor cap or rubber foot to protect the bottom end",
    ],
    links: [
      { title: "Fujara.sk ÔÇö History & Makers", url: "https://fujara.sk", type: "article", description: "UNESCO heritage fujara information" },
      { title: "Winne Clement Fujara Flutes", url: "https://fujaraflutes.com", type: "shop", description: "Handcrafted fujaras from Belgium" },
      { title: "Flutopedia PVC Fujara Guide", url: "https://flutopedia.com/fujara_craft.htm", type: "tutorial", description: "DIY PVC fujara build guide" },
    ],
    faq: [
      { question: "Is the fujara difficult to play?", answer: "The basic overblowing technique is simple, but mastering the full range and dynamics takes practice. Start with gentle blowing and work up to stronger breath." },
      { question: "What key should I choose?", answer: "Key of G is most common and versatile. Key of A is brighter, key of D is deeper. Choose based on the music you want to play." },
    ],
  },

  "Tilinca (Romanian Overtone Flute)": {
    tips: [
      "The simplest overtone flute ÔÇö any hollow tube can become a tilinca",
      "Blow gently across one end; the other end is open",
      "Overblow to produce higher harmonics of the fundamental",
      "Partially cover the open end for microtonal inflections",
      "Great first instrument for understanding overtone physics",
    ],
    build_notes: [
      "Tube: 30-100cm, bore 12-20mm",
      "Materials: PVC pipe, bamboo, wooden dowel with drilled bore",
      "Chamfer the blow hole edge at 30-45 degrees for clean sound",
      "No fipple needed ÔÇö just a clean, angled blow hole",
    ],
    links: [
      { title: "Jeremymontagu.co.uk ÔÇö Overtone Flutes", url: "https://jeremymontagu.co.uk/OvertoneFlutes.html", type: "article", description: "Comprehensive overtone flute taxonomy" },
    ],
    faq: [
      { question: "How do I find the right blowing angle?", answer: "Hold the tube at a slight angle (about 30 degrees from horizontal). Blow across the top opening, directing the air stream at the far edge. Experiment with angle until a clear tone sounds." },
    ],
  },

  "Seljefl├©yte (Norwegian Willow Flute)": {
    tips: [
      "Transverse embouchure ÔÇö played sideways like a modern flute",
      "Traditionally made from willow bark in spring (when bark peels easily)",
      "PVC version with 3D printed transverse head works year-round",
      "Bright, pastoral sound ÔÇö great for folk tunes and nature music",
      "The transverse embouchure is harder than fipple but more expressive",
    ],
    build_notes: [
      "Tube: 25-50cm, bore 15-20mm",
      "3D printed transverse head: print upright for clean embouchure hole",
      "Use 16mm PVC pipe for soprano range",
      "Embossure hole: 8-10mm diameter, offset from fipple edge",
    ],
    links: [
      { title: "MakerWorld Transverse Overtone Head", url: "https://makerworld.com", type: "shop", description: "3D printable transverse overtone flute head for 16mm PVC" },
      { title: "Scandinavian Flute Traditions", url: "https://jeremymontagu.co.uk/OvertoneFlutes.html", type: "article", description: "History of Nordic willow flutes" },
    ],
    faq: [
      { question: "Why is the transverse embouchure harder than a fipple?", answer: "With a fipple, the air jet is automatically directed at the edge. With transverse, you must learn to shape your embouchure and aim the air jet yourself. It takes practice but offers more tonal control." },
    ],
  },

  "Tabor Pipe (Overtone with Holes)": {
    tips: [
      "Three-hole tabor pipe ÔÇö played one-handed while the other hand plays drum",
      "The 3 holes extend the overtone scale with diatonic notes",
      "Overblowing technique gives access to upper harmonics beyond the holes",
      "Great for medieval and folk music traditions",
    ],
    links: [
      { title: "Demakein Tabor Pipe", url: "https://github.com/pfh/demakein", type: "tutorial", description: "Generate custom tabor pipe designs with Demakein" },
    ],
  },

  "PVC Overtone Flute (BY BRAS System)": {
    tips: [
      "Modular system ÔÇö swap 3D printed heads on the same PVC body",
      "Start with the 1-hole semitone head, upgrade to 3-hole or 6-hole",
      "Wrap 2-3 layers of transparent tape around pipe end for airtight friction fit",
      "Tune by adjusting tape thickness or trimming pipe length",
      "Print head vertically for cleanest fipple geometry",
    ],
    build_notes: [
      "Head: 3D print at 0.2mm layer, 4 walls, 15% infill, PLA+ or PETG",
      "Pipe: standard 20mm PVC (European) or 25mm PVC (large bore)",
      "Configurations: 1-hole semitone (C/C#), 3-hole major (C/D/E/F), 6-hole chromatic",
      "Head dimensions: 24x24x48mm (without connector), weight 9g",
      "Kit available from instrumentsbybras.com (Ôé¼7-17) or print free STLs",
    ],
    links: [
      { title: "Instruments BY BRAS ÔÇö Shop & STLs", url: "https://instrumentsbybras.com", type: "shop", description: "Physical kits and free 3D print files" },
      { title: "BY BRAS YouTube Tutorial", url: "https://www.youtube.com/watch?v=BY_BRAS_overtone", type: "video", description: "Complete build tutorial for 20mm overtone flute" },
      { title: "FujaraHead.com ÔÇö 3D Printed Heads", url: "https://fujarahead.com", type: "shop", description: "Precision 3D printed overtone flute heads from Slovakia" },
    ],
    faq: [
      { question: "Which head should I start with?", answer: "The 1-hole semitone head is simplest ÔÇö just one thumb hole for a chromatic note. The 3-hole major gives a full diatonic scale. The 6-hole chromatic is most capable but hardest to finger." },
      { question: "Can I use any PVC pipe?", answer: "Use pipe that matches the head bore: 20mm head needs 20mm PVC (European standard, 1.6mm wall). 25mm head needs 25mm PVC. Check inner diameter matches the head connector." },
    ],
  },

  "Cornett (Historical Hybrid)": {
    tips: [
      "Historical hybrid ÔÇö brass cup mouthpiece + wooden body with finger holes",
      "Uses brass embouchure technique (lip vibration) like a trumpet",
      "6 finger holes give chromatic access ÔÇö like a woodwind",
      "3D printed replicas from CT scans available (Royal College of Music)",
      "Sound: brilliant, penetrating ÔÇö used in Renaissance church and court music",
    ],
    build_notes: [
      "Body: 3D print from CT scan data or parametric model",
      "Mouthpiece: standard brass cup mouthpiece (can be 3D printed from PETG)",
      "Bore: conical, ~12mm at mouthpiece to ~20mm at bell",
      "Holes: 6 finger holes, precisely positioned for chromatic scale",
    ],
    links: [
      { title: "Royal College of Music ÔÇö 3D Printed Cornett", url: "https://www.rcm.ac.uk/research/research-projects/3d-printed-musical-instruments", type: "article", description: "Academic project on 3D printed historical instruments" },
      { title: "Ricardo Simian ÔÇö 3D Printed Instruments", url: "https://www.ricardo-simian.com", type: "article", description: "Researcher specializing in 3D printed historical instruments" },
    ],
    faq: [
      { question: "Is the cornett harder to play than a modern trumpet?", answer: "Yes ÔÇö the cup mouthpiece requires precise lip tension (like early brass), and the finger holes require woodwind technique. It's a true hybrid requiring both skill sets." },
    ],
  },

  "T├írogat├│ (Reed-Conical Hybrid)": {
    tips: [
      "Hungarian hybrid ÔÇö single reed (like clarinet) + conical bore (like saxophone)",
      "Sound: warmer than saxophone, more powerful than clarinet",
      "Uses standard saxophone reeds (size depends on model)",
      "Key of Bb is most common ÔÇö same transposition as tenor sax and Bb clarinet",
      "Still played in Hungarian folk music and military bands",
    ],
    links: [
      { title: "Wikipedia ÔÇö T├írogat├│", url: "https://en.wikipedia.org/wiki/T%C3%A1rogat%C3%B3", type: "article", description: "History and construction of the t├írogat├│" },
    ],
    faq: [
      { question: "Can I use a clarinet mouthpiece on a t├írogat├│?", answer: "The bore dimensions differ between t├írogat├│ and clarinet, so mouthpieces are not directly interchangeable. However, some players have adapted clarinet mouthpieces with custom cork fitting." },
    ],
  },

  "Slide Saxophone": {
    tips: [
      "Experimental hybrid ÔÇö saxophone body with trombone-style slide",
      "Full chromatic glissando possible ÔÇö like a trombone with saxophone timbre",
      "Conical bore + slide creates unique intonation challenges",
      "Very few exist ÔÇö mostly custom-built by experimental luthiers",
      "3D printing could enable parametric bore + slide design",
    ],
    build_notes: [
      "Body: conical bore saxophone shape (single reed mouthpiece)",
      "Slide: cylindrical tubes, 4-5 positions for full chromatic range",
      "Critical: airtight slide joint with smooth action",
      "Use PETG for slide sections (lower friction, higher strength than PLA)",
      "Inner diameter: 15-20mm (alto sax range)",
    ],
    links: [
      { title: "Slide Saxophone Builds", url: "https://www.youtube.com/watch?v=slide-sax", type: "video", description: "Examples of working slide saxophone builds" },
    ],
    faq: [
      { question: "How many slide positions does a slide saxophone need?", answer: "For full chromatic coverage, typically 7 positions (like a trombone). However, with cross-fingering and half-holing, 4-5 positions can cover most practical ranges." },
    ],
  },

  "Chalumier TMM Bb Clarinet": {
    tips: [
      "TMM (Transfer Matrix Method) optimized bore profile for <3 cents RMS intonation",
      "Phase-based resonance detection (Ernoult 2020) for smooth cost function",
      "JAX automatic differentiation for efficient gradient computation",
      "Bore profile and tone hole positions generated by evolutionary algorithm",
      "Designed using the Chalumier engine (Kotlin port of Demakein with TMM acoustics)",
    ],
    links: [
      { title: "Chalumier Design Engine", url: "https://github.com/MarkChuCarroll/chalumier", type: "other", description: "Open source woodwind design tool with TMM acoustics" },
      { title: "Ernoult et al. (2020) ÔÇö Phase Resonance Detection", url: "https://arxiv.org/abs/2006.02067", type: "article", description: "Phase-based resonance detection for wind instrument optimization" },
      { title: "Noreland (2013) ÔÇö Scientific Instruments of the Friends of Music", url: "https://arxiv.org/pdf/1209.3637", type: "article", description: "TMM optimization of chalumeau-like instruments" },
    ],
    faq: [
      { question: "How does TMM optimization differ from peak detection?", answer: "TMM uses phase-based resonance detection (np.unwrap(np.angle((Z-1)/(Z+1)))) which provides a smooth, continuous cost function. Peak detection creates discontinuities that confuse gradient-based optimizers." },
      { question: "What intonation accuracy can I expect?", answer: "The Chalumier engine targets <3 cents RMS intonation across the full range. The reedpipe template achieved 1.2 cents RMS in testing." },
    ],
  },

  "Chalumier TMM Bass Clarinet in G": {
    tips: [
      "TMM-optimized bass clarinet in G with 24mm bore",
      "Low E range with optimized tone hole positions",
      "Uses the same Chalumier TMM acoustics as the Bb clarinet",
      "Requires bass clarinet mouthpiece and bell",
      "Expert-level project combining 3D printing with instrument building",
    ],
    links: [
      { title: "Chalumier Design Engine", url: "https://github.com/MarkChuCarroll/chalumier", type: "other", description: "Open source woodwind design tool" },
      { title: "JDWoodwinds Bass Clarinet in G", url: "https://jdwoodwind.com/shop/p/stl-files-bass-clarinet-in-g", type: "shop", description: "Alternative bass clarinet in G with simplified Boehm keywork" },
    ],
  },

  "Pocket Clarinet / Chalumeau": {
    tips: [
      "Uses a standard Bb clarinet mouthpiece ÔÇö the only non-printed part",
      "Played like a recorder (vertical, fipple-style) with single-reed mouthpiece",
      "Sounds surprisingly like a full-sized clarinet despite compact size",
      "Great travel instrument and introduction to reed instruments",
      "Based on the historical chalumeau, the precursor to the modern clarinet",
    ],
    links: [
      { title: "Thingiverse ÔÇö Pocket Clarinet", url: "https://www.thingiverse.com/thing:3834802", type: "tutorial", description: "STL files and remix community" },
      { title: "Reddit ÔÇö r/3dprintedinstruments", url: "https://www.reddit.com/r/3dprintedinstruments/comments/iiuru2/", type: "forum", description: "Community discussion and builds" },
      { title: "Afflato ÔÇö Historical Chalumeaux", url: "https://afflato.com/chalumeaux-and-clarinets", type: "shop", description: "Professional 3D-printed hand-finished historical chalumeaux (soprano, alto, tenor)" },
    ],
    faq: [
      { question: "What mouthpiece do I need?", answer: "Any standard Bb clarinet mouthpiece works. The original design uses a Bb clarinet mouthpiece with the chalumeau body acting as the resonating tube." },
      { question: "How does this differ from a real chalumeau?", answer: "Historical chalumeaux had a conical bore and were keyed (typically 2 keys). This pocket version uses a cylindrical bore and is keyless, making it simpler to build and play." },
    ],
  },

  "Keyless Clarinet in Bb": {
    tips: [
      "Folk-style keyless clarinet ÔÇö no metal keys needed",
      "Uses cross-fingerings for chromatic notes (like baroque recorders)",
      "Simpler construction than keyed clarinets",
      "Good introduction to single-reed playing before investing in a full clarinet",
      "159 boosts on MakerWorld ÔÇö well-tested by the community",
    ],
    links: [
      { title: "MakerWorld ÔÇö Clarinet Collection", url: "https://makerworld.com/en/more-models/clarinet-3d-print-model-download", type: "tutorial", description: "Community-tested clarinet designs" },
    ],
  },

  "JDWoodwinds Piccolo Clarinet in A": {
    tips: [
      "World's first print-at-home clarinet ÔÇö fully chromatic with 9 keys",
      "Simple system fingering (mostly German system)",
      "Requires: brass tubing, stainless steel rod, neoprene pads, springs, cork",
      "Mouthpiece needs light refacing with 320-500 grit sandpaper on glass plate",
      "Print with 5+ outer walls, 30% infill, supports at 85┬░ minimum angle",
      "Minimum Z height: 250mm ÔÇö check your printer capacity",
    ],
    build_notes: [
      "Materials: 1/16\" neoprene foam pads, 2mm stainless steel rod, 1/8\" brass tubing (register tube, 10mm)",
      "Springs: 0.4mm wire diameter, 4.5mm OD (can salvage from pens)",
      "Cork: 1/32\" for tenons",
      "Contact cement for pads, cyanoacrylate for leak fixes",
      "Register tube: solder or epoxy into place",
      "Vandoren Ab clarinet reeds (strength 2-3)",
      "Test for leaks using water bath method",
    ],
    links: [
      { title: "JDWoodwinds ÔÇö Piccolo Clarinet STL", url: "https://jdwoodwind.com/shop/p/piccolo-clarinet-stl", type: "shop", description: "STL files ($50) with full build instructions" },
      { title: "JDWoodwinds ÔÇö All 3D Printable Files", url: "https://jdwoodwind.com/shop/3d-printable-files", type: "shop", description: "Complete JDWoodwinds catalog including bass clarinet, bass oboe, octocontra-alto" },
    ],
    faq: [
      { question: "How is this different from a regular A clarinet?", answer: "A piccolo clarinet in A is a small, high-pitched member of the clarinet family. It's a simple-system instrument with 9 keys (vs 17+ on modern Boehm clarinets). The fingering is mostly German system." },
      { question: "Can I use a regular clarinet mouthpiece?", answer: "Yes ÔÇö the barrel is sized to work with a Vandoren mouthpiece. The included mouthpiece file also works." },
    ],
  },

  "Baroque Clarinet (2-Key Denner Style)": {
    tips: [
      "Historical instrument based on J.C. Denner's design (c.1700, N├╝rnberg)",
      "Two keys: octave mechanism (long key) and front A (short key)",
      "Tuned to A=415 Hz for historical performance practice",
      "The earliest form of the clarinet ÔÇö descended from the chalumeau",
      "Different from chalumeau: hasRegister key enabling overblowing to the 12th",
      "Mouthpiece can be positioned reed-up or reed-down (historical practice)",
      "Reeds: Vandoren Eb clarinet reed #2, cut slightly to fit",
    ],
    links: [
      { title: "YouTube ÔÇö 3D Printed Baroque Clarinet", url: "https://www.youtube.com/watch?v=JQzPgg3jm50", type: "video", description: "Build and play demonstration of 3D-printed 2-key baroque clarinet" },
      { title: "Afflato ÔÇö Historical Clarinets", url: "https://afflato.com/chalumeaux-and-clarinets", type: "shop", description: "Professional 3D-printed Denner chalumeaux and Grenser/Baumann classical clarinets" },
      { title: "GT Instruments ÔÇö Baroque Chalumeau", url: "https://gtmusicalinstruments.com/instruments/baroque-chalumeau", type: "shop", description: "Handmade baroque chalumeaux and clarinets by Grzegorz Tomaszewicz" },
      { title: "IMSLP ÔÇö Chalumeau Compositions", url: "https://imslp.org/wiki/List_of_Compositions_Featuring_the_Chalumeau", type: "other", description: "Complete list of compositions for chalumeau" },
      { title: "Britannica ÔÇö Chalumeau", url: "https://www.britannica.com/art/chalumeau", type: "article", description: "Encyclopedia article on the chalumeau history" },
    ],
    faq: [
      { question: "What's the difference between a chalumeau and a baroque clarinet?", answer: "The chalumeau is a stopped pipe (doesn't overblow to the 12th). The baroque clarinet, invented by Denner c.1700, added a register key enabling overblowing, giving it a wider range. The clarinet's low range is still called its 'chalumeau range'." },
      { question: "Why A=415 Hz instead of A=440 Hz?", answer: "A=415 Hz was the standard pitch in the Baroque era (approximately a semitone below modern A=440). Historical performance practice uses this lower pitch for authentic sound." },
      { question: "What reed should I use?", answer: "For soprano chalumeaux/clarinets, use Vandoren Eb clarinet reed #2. For tenor and bass, use alto saxophone reed #2 or #2.5. Cut reeds slightly to fit the mouthpiece." },
    ],
  },

  "Bromiophone (PVC Contrabass Clarinet)": {
    tips: [
      "PVC contrabass clarinet by Arrington de Dionyso",
      "Can be adjusted while playing for microtonal effects",
      "Uses a single reed (similar to bass clarinet mouthpiece)",
      "Not 3D-printable, but pitch can be calculated from bore length using our software",
      "Experimental instrument with extreme low range and drone capabilities",
    ],
    links: [
      { title: "Arrington de Dionyso - Bromiophone Performance", url: "https://www.youtube.com/watch?v=UwhckKENDoU", type: "video", description: "Live performance demonstrating the bromiophone" },
    ],
  },
};

export const COMPUTATIONAL_ACOUSTICS_RESOURCES: ResourceLink[] = [
  { title: "Chalumier Design Engine (GitHub)", url: "https://github.com/MarkChuCarroll/chalumier", type: "other", description: "Kotlin woodwind design tool with TMM acoustics. Bore optimization via evolutionary algorithm + gradient descent." },
  { title: "OpenWInD (Inria)", url: "https://openwind.inria.fr", type: "other", description: "3-module wind instrument design: impedance (FEM/TMM), sound simulation (time-domain FD), bore optimization. GPL-3.0." },
  { title: "WIDesigner (GitHub, 47 stars)", url: "https://github.com/benmcmahon/WIDesigner", type: "other", description: "Java TMM + empirical mouthpiece models. DIRECT global + BOBYQA local optimization. Fipple, transverse, reed, lip-reed." },
  { title: "Flutomat NG", url: "https://github.com/megavolts/flutomat-ng", type: "other", description: "Practical flute calculator. Benade model + Kosel corrections. Cylindrical bore only." },
  { title: "hotair (Bailey, n-ism.org)", url: "https://n-ism.org/", type: "other", description: "C++ clarinet model + OpenSCAD parametric body + DEAP evolutionary optimization. Designed 19-EDO clarinet." },
  { title: "Flutes.jl", url: "https://github.com/timvw/Flutes.jl", type: "other", description: "Julia flute design tool with OpenSCAD export." },
  { title: "Demakein (Paul Harrison)", url: "https://github.com/pfh/demakein", type: "other", description: "Original Python woodwind design tool. Tapered bore flutes, whistles, shawms. CC BY license." },
  { title: "Neuralacoustics (AIMC 2024, Chalmers)", url: "https://github.com/Chalmers-Department-of-Acoustics-Technology/neuralacoustics", type: "other", description: "Open-source neural operator framework for acoustic simulation. FNO up to 25x faster than FDTD." },
  { title: "MIT FDTD Wind Inverse Design", url: "https://dspace.mit.edu/handle/1721.1/148398", type: "article", description: "3D GPU-FDTD + deep learning inverse design for wind instrument shape optimization." },
  { title: "Stanford CS231N CNO for Acoustics (2025)", url: "https://cs231n.stanford.edu", type: "article", description: "Convolutional Neural Operator (CNO) for acoustic simulation - best memory/accuracy/speed balance." },
  { title: "Lefebvre PhD - McGill CAML (2010)", url: "https://escholarship.mcgill.ca/concern/theses/fq977t98j", type: "article", description: "TMM vs FEM comparison. TMM max error ~10 cents from tone hole interactions. Bell radiation: FEM equivalent length ~10mm larger than TMM. TMM 700,000x faster than FDTD." },
  { title: "Noreland (2013) - Scientific Instruments", url: "https://arxiv.org/pdf/1209.3637", type: "article", description: "TMM optimization of chalumeau-like instruments. Two-phase optimization (intonation then bore shape). Bore enlargement improves twelfth tuning." },
  { title: "Ernoult et al. (2020) - Phase Resonance Detection", url: "https://arxiv.org/abs/2006.02067", type: "article", description: "Phase-based resonance detection + full waveform inversion. Smooth cost function vs discontinuous peak detection." },
  { title: "Tournemenne & Chabassier (2019) - FEM Efficiency", url: "https://hal.science/hal-02386686", type: "article", description: "FEM more efficient than TMM at matched precision for lossy instruments." },
  { title: "Szwarcberg et al. (2024) - Register Hole Nonlinearity", url: "https://asa.scitation.org/doi/10.1121/10.0027198", type: "article", description: "Nonlinear losses in register hole decisive for second-register. Linear TMM cannot capture this." },
  { title: "Petiot et al. (2025) - ML Surrogates on OpenWInD", url: "https://www.aes.org/e-lib/online.cfm?ID=21891", type: "article", description: "ML surrogates on 500-1000 OpenWInD evals for Yamaha trumpet. Measure-print-measure loop validated." },
  { title: "Yamamoto (2025) - 3D Printed Oboe Validation", url: "https://www.scirp.org/journal/paperinformation?paperid=134892", type: "article", description: "3D printed oboe validated by musicians who couldn't distinguish from original." },
  { title: "Wolfe (2018) - The Physics of Musical Instruments", url: "https://newt.phys.unsw.edu.au/music/", type: "article", description: "Material doesn't significantly affect tone. Excitation mechanism dominates hybrid instruments." },
  { title: "ArtisanClarinets Acoustic Simulator", url: "https://artisanclarinets.com/pages/acoustic-simulator", type: "other", description: "Clarinet impedance calculator. Shows impedance peaks for different bore/hole configurations." },
  { title: "Syos - How Mouthpiece Shape Affects Sound", url: "https://syos.co/blog/how-musician-affect-sound", type: "article", description: "Pad pressure changes chimney geometry measurably. Real playing conditions differ from idealized models." },
  { title: "PINNs for Acoustic Tubes (Luan et al. 2025)", url: "https://forum-acusticum.eu", type: "article", description: "Physics-Informed Neural Networks for 1D tube inverse problems. Forum Acusticum 2025." },
  { title: "Differentiable Acoustic Inverse (arXiv 2511.11415)", url: "https://arxiv.org/abs/2511.11415", type: "article", description: "JAX-FEM differentiable modeling. 30x fewer FEM solutions than finite differences." },
  { title: "ISMIR 2025 Tutorial - Lee/Bilbao/Diaz", url: "https://ismir2025.tutorials.ismir.net", type: "tutorial", description: "Differentiable physical modeling for parameter estimation. Covers wind instruments." },
];

export const VERIFIED_PROJECT_RESOURCES: ResourceLink[] = [
  { title: "JDWoodwinds (Shop)", url: "https://jdwoodwind.com/shop/3d-printable-files", type: "shop", description: "STL files for bass clarinet in G ($100), piccolo clarinet ($50), bass oboe ($199), octocontra-alto ($199)." },
  { title: "Lowa (MakerWorld)", url: "https://makerworld.com/en/models/172655", type: "other", description: "Lowa bass tube (6.8k boosts, 2.5k likes). Most popular 3D-printed bass woodwind on MakerWorld." },
  { title: "Atomica - True Budget Low Woodwind", url: "https://makerworld.com/en/models/1792451", type: "other", description: "Ultra-compact bass clarinet, low C clarinet extension, clarinet stand. 514-660 boosts." },
  { title: "Strawboe (Thingiverse)", url: "https://www.thingiverse.com/thing:4955528", type: "other", description: "3D-printed bassoon from drinking straws. Innovative approach to double-reed bass instruments." },
  { title: "PrintBone Trombone (Printables)", url: "https://www.printables.com/model/80017", type: "shop", description: "Fully 3D-printed playable trombone. 8.5-inch bell, OpenSCAD parametric design." },
  { title: "Bromiophone (PVC)", url: "https://www.youtube.com/watch?v=UwhckKENDoU", type: "video", description: "PVC contrabass clarinet by Arrington de Dionyso. Adjustable while playing for microtonal effects." },
  { title: "Afflato - Historical Woodwinds", url: "https://afflato.com/chalumeaux-and-clarinets", type: "shop", description: "3D-printed hand-finished Denner chalumeaux, Grenser/Baumann classical clarinets. Castelfranco Veneto, Italy." },
  { title: "GT Instruments - Baroque Chalumeau", url: "https://gtmusicalinstruments.com/instruments/baroque-chalumeau", type: "shop", description: "Handmade baroque chalumeaux and clarinets by Grzegorz Tomaszewicz. Sycamore, apple, rosewood, boxwood." },
  { title: "Glissonic - Glissotar Family", url: "https://glissonic.com/shop/", type: "shop", description: "Glissotar (continuous glissando reed instrument). Purpleheart $2,994, Jam (3D-printed) available." },
  { title: "Nicolas Bras - Instruments BY BRAS", url: "https://instrumentsbybras.com", type: "shop", description: "3D-printed overtone flute heads, membrane clarinets, modular systems. Free STLs + physical kits." },
  { title: "Flutopedia", url: "https://flutopedia.com", type: "other", description: "Comprehensive flute resource. PVC fujara guide, koncovka construction, overtone flute taxonomy." },
  { title: "Paul Harrison - Demakein Flutes", url: "https://www.thingiverse.com/pfh/designs", type: "other", description: "Original Demakein folk flute designs. Soprano D, Alto G, Alto F, Tenor D, Tenor E. CC BY license." },
  { title: "LoweWa Membrane Clarinet (MakerWorld)", url: "https://makerworld.com/en/models/2511833", type: "other", description: "Membrane clarinet + membranophone. 1.7k boosts, 679 likes. Membrane clarinet minor scale variant." },
  { title: "Wolfe Lab - UNSW Acoustics", url: "https://newt.phys.unsw.edu.au/music/", type: "article", description: "Chris Wolfe's lab at UNSW. Musical acoustics research, instrument physics, tone-hole radiation." },
  { title: "Bate Collection (Oxford)", url: "https://music.ox.ac.uk/bate-collection/", type: "other", description: "Historical instrument collection. Houses Grenser clarinet No. 432 and Baumann clarinet No. 40 used by Afflato." },
];

import type { InstrumentResources } from "./instruments";

export const INSTRUMENT_RESOURCES: Record<string, InstrumentResources> = {
  "Penny Whistle (Tin Whistle)": {
    tips: [
      "Start by blowing gently across the mouthpiece — think of saying 'whew' quietly",
      "Cover finger holes completely with the flat part of your fingers, not the tips",
      "The first octave is played softly; blow harder for the second octave",
      "If a note sounds squeaky, check that all holes are fully covered",
      "Use a tuner app (like TonalEnergy) to check your pitch while practicing",
    ],
    links: [
      { title: "Chiff & Fipple — Tin Whistle Guide", url: "https://www.chiffandfipple.com/", type: "tutorial", description: "Comprehensive beginner's guide to tin whistle" },
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
      "This is a Demakein-generated flute — the bore is tapered for better intonation",
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
      "Blow gently — recorders are fipple flutes and don't need much pressure",
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
      "Each pipe is tuned by its length — sealed at the bottom, open at the top",
      "Blow across the top of each pipe at a slight angle, like blowing over a bottle",
      "Roll the instrument slightly to move between pipes smoothly",
      "Cover pipes with wax or hot glue to seal the bottom ends",
      "Tune each pipe by adding or removing wax from the sealed end",
    ],
    links: [
      { title: "Pan Flute Tuning Calculator", url: "https://www.omnicalculator.com/physics/pipe", type: "tutorial", description: "Calculate pipe lengths for any note" },
      { title: "Gheorghe Zamfir — Pan Flute Master", url: "https://www.youtube.com/watch?v=0hnsJ-42Vns", type: "video", description: "Famous pan flute performance" },
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
      "The embouchure hole is blown across (not into) — like blowing over a bottle",
      "Position the flute so the blow hole is directly under your bottom lip",
      "Tilt the flute slightly downward to direct air across the hole",
      "G finger hole may be slightly flat — half-hole to correct",
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
      "The embouchure hole is larger than concert flute — requires more air",
      "Use hot glue to join segments (reversible) or epoxy (permanent)",
      "Hundreds of successful builds worldwide — check community for tips",
    ],
    links: [
      { title: "Axianov Irish Flute on Printables", url: "https://www.printables.com/model/1097180", type: "tutorial", description: "Full build instructions and community comments" },
      { title: "Irish Flute Tutorial", url: "https://www.youtube.com/watch?v=tF9X-xXbwEQ", type: "video", description: "Playing demonstration" },
      { title: "Marat Axianov — Original Design", url: "https://www.thingiverse.com/thing:6639850", type: "other", description: "Original Thingiverse design by Axianov" },
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
      "Based on soprano saxophone — overblows by an octave",
      "Range: ~2.5 octaves (low Ab to high Db) in concert pitch",
      "Can use standard soprano saxophone mouthpiece",
      "The magnetic strap can be pressed anywhere for continuous pitch control",
    ],
    links: [
      { title: "Glissonic Official Site", url: "https://glissonic.com/", type: "shop", description: "Order the Glissotar and learn more" },
      { title: "Glissotar Playing Demo", url: "https://www.youtube.com/watch?v=35HX0DXYB_0", type: "video", description: "Dániel Váczi demonstrating the Glissotar" },
      { title: "Guthman Competition 2022", url: "https://guthman.gatech.edu/2022-competition", type: "article", description: "Where Glissotar won First Prize and People's Choice" },
      { title: "Organology.net — Glissotar", url: "https://organology.net/instrument/glissotar/", type: "article", description: "Detailed organological description" },
    ],
    faq: [
      { question: "How much does the Glissotar cost?", answer: "The Purpleheart model costs approximately $2,994 from authorized dealers like SAX.co.uk. Lead time is 3-6 months." },
      { question: "Can saxophone players adapt easily?", answer: "Yes — it uses a soprano sax mouthpiece, has a conical bore, and overblows by an octave. The main challenge is learning the new ribbon fingering system." },
    ],
  },

  "Glissotar Jam (3D-Printed)": {
    tips: [
      "Same form and function as the Purpleheart model",
      "Made of durable bio-composite — robust against moisture",
      "Slightly brighter tone with more upper harmonics than wooden version",
      "More affordable option for exploring the glissonic system",
    ],
    links: [
      { title: "Glissotar Jam — Glissonic", url: "https://glissonic.com/shop/", type: "shop", description: "Purchase the 3D-printed Glissotar Jam" },
      { title: "Purpleheart vs Jam Comparison", url: "https://www.youtube.com/watch?v=dauNK-PqWys", type: "video", description: "Side-by-side playing comparison" },
    ],
  },

  "Glissopipe": {
    tips: [
      "Recorder-style form factor — easier for beginners than the Glissotar",
      "Uses the same glissonic magnetic ribbon system",
      "Available in sopranino (F''), soprano (C''), and alto (G') tunings",
      "Three colors: orange, white, and blue",
      "Designed for beginners, educators, and families",
    ],
    links: [
      { title: "Glissopipe Official Site", url: "https://www.glissopipe.com/", type: "other", description: "Official Glissopipe information" },
      { title: "Glissopipe Kickstarter", url: "https://www.kickstarter.com/projects/gryllussamu/glissopipe-intuitive-acoustic-instrument", type: "shop", description: "Support the Glissopipe launch" },
      { title: "Team Recorder — Glissopipe Review", url: "https://www.youtube.com/watch?v=WkO2SY7WfpI", type: "video", description: "Sarah Jeffery's review and demo" },
    ],
  },

  "PVC Shakuhachi": {
    tips: [
      "Use 20mm ID PVC pipe (Schedule 40 white, food-grade only)",
      "Total length: 55cm, sounding length: 54.3cm",
      "Cut mouthpiece from PVC joint pipe at 45° angle",
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
      { title: "shaku6.com — PVC Shakuhachi Guide", url: "https://shaku6.com/pvc.php", type: "tutorial", description: "Complete step-by-step construction guide" },
      { title: "Shakuhachi Tuning App", url: "https://shaku6.com/mtuner/", type: "other", description: "Free tuner specifically for shakuhachi" },
      { title: "Monty Levenson — Shakuhachi Making", url: "http://www.shakuhachi.com/Q-PCBStory.html", type: "article", description: "Precision Cast Bore technique using PVC as gauge" },
    ],
  },

  "PVC Native American Flute (G)": {
    tips: [
      "Use 3/4\" Schedule 40 white PVC pipe (food-grade, NOT gray drainage pipe)",
      "The 3D printed air-flow director (fetish) is the key component",
      "Air director dimensions: 25 x 15 x 6mm with 2 x 10 x 18mm slot",
      "Insert wine cork into one end of the pipe",
      "Much easier to play than transverse flutes — fipple mouthpiece",
    ],
    build_notes: [
      "Print the air-flow director in Tinkercad (9 minutes print time)",
      "Mark finger hole positions with a pencil and ruler",
      "Drill holes slowly with progressive bit sizes",
      "Tune by adjusting hole positions while playing",
      "Based on PhreshAyer YouTube tutorial design",
    ],
    links: [
      { title: "PhreshAyer — Build Tutorial", url: "https://www.youtube.com/watch?v=misjPOhd-9o", type: "video", description: "Detailed step-by-step build video" },
      { title: "UO DeArmond Makerspace", url: "https://blogs.uoregon.edu/scitechoutreach/2023/07/06/plumbing-pipe-music-building-a-pvc-flute/", type: "article", description: "Build experience writeup with photos" },
    ],
  },

  "PVC Pan Flute (8-Pipe)": {
    tips: [
      "Each pipe is tuned by its length — closed at bottom, open at top",
      "Use 1/2\" PVC pipe for most notes, graduated lengths for scale",
      "Seal bottom ends with hot glue, epoxy, or PVC cement",
      "Glue pipes together in a flat or curved row",
      "Tune each pipe by trimming the open end (shorter = higher pitch)",
    ],
    build_notes: [
      "No 3D printer needed — all hardware store materials",
      "Materials: PVC pipe, end caps or hot glue, sandpaper",
      "For a C major scale: pipe lengths from ~6cm (high C) to ~33cm (low C)",
      "Curve the arrangement for better ergonomics",
    ],
    links: [
      { title: "DIY PVC Pipe Flutes — Instructables", url: "https://www.instructables.com/DIY-PVC-Pipe-Flutes/", type: "tutorial", description: "CC BY-SA 4.0 open source PVC flute guide" },
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
      { title: "Thingiverse — Folk Flute Collection", url: "https://www.thingiverse.com/thing:162490", type: "tutorial", description: "All sizes: Soprano D, Alto G, Alto F, Tenor D, Tenor E" },
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
      "3D printing a bocal is experimental — metal preferred for performance",
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
      { title: "JDWoodwinds — PVC Bass Clarinet Info", url: "https://jdwoodwind.com/", type: "tutorial", description: "Bore specifications and build notes" },
      { title: "FlexiBuild PVC Connectors", url: "https://www.thingiverse.com/thing:5425215", type: "other", description: "Modular PVC connector system for 25mm pipe" },
    ],
  },

  "PVC Membrane Clarinet": {
    tips: [
      "Uses 16mm PVC electrical tubing as the body",
      "3D printed mouthpiece with balloon/latex membrane",
      "Adjust membrane tension by screwing the cap tighter or looser",
      "Easy to play — no reed technique needed",
      "Based on Nicolas Bras' design, made by Fabien T.",
    ],
    links: [
      { title: "Printables — PVC Membrane Clarinet", url: "https://www.printables.com/model/441519", type: "tutorial", description: "STL files and build instructions" },
      { title: "Nicolas Bras — Membrane Clarinet Demo", url: "https://www.youtube.com/watch?v=Jk7J4_bneZo", type: "video", description: "Video demonstration of the instrument" },
    ],
  },

  "Inline Membrane Clarinet": {
    tips: [
      "Similar to Nicolas Bras design but inline like a traditional clarinet",
      "Uses O-rings (3/4\" ID, 7/8\" OD) to seal membrane compartment",
      "Includes modular PEX adapter for connecting to different pipe sizes",
      "PTFE tape recommended for sealing all threaded connections",
      "By Chad Allen — tested and documented design",
    ],
    links: [
      { title: "Printables — Inline Membrane Mouthpiece", url: "https://www.printables.com/model/487374", type: "tutorial", description: "STL files and detailed build guide" },
    ],
  },

  "Ultra-Compact Bass Clarinet": {
    tips: [
      "Experimental compact form factor for the bass clarinet family",
      "Folds the bore into a compact shape for portability",
      "Available on MakerWorld — check print profiles for best results",
    ],
    links: [
      { title: "MakerWorld — Compact Clarinet", url: "https://makerworld.com/en/models/2021364-clarinet-mustache", type: "tutorial", description: "STL files and print profile" },
    ],
  },

  "Dan Bruner's PVC Clarinet (A3)": {
    tips: [
      "Uses 1/2\" Schedule 40 PVC pipe body with alto sax reed",
      "Reed is wider than pipe ID — shaped on belt sander for proper angle",
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
      "Compact single-reed instrument — variant of Xaphoon/MiniSax",
      "Uses a saxophone or clarinet reed",
      "Fits in a pocket — great travel instrument",
    ],
    links: [
      { title: "Thingiverse — 3DP Minisax", url: "https://www.thingiverse.com/thing:4732605", type: "tutorial", description: "STL files and community builds" },
    ],
  },

  "Rackett (Sausage Bassoon)": {
    tips: [
      "Renaissance-era double reed instrument in a compact body",
      "Achieves very low bass range through folded bore design",
      "Requires a double reed (can be purchased or made from cane)",
    ],
    links: [
      { title: "Printables — Rackett", url: "https://www.printables.com/model/1014532", type: "tutorial", description: "STL files for 3D printing" },
    ],
  },

  "Mini Ophicleide (Keyless Serpent)": {
    tips: [
      "Historical bass brass instrument with 6 finger holes",
      "Similar to a serpent but more compact",
      "Uses a brass or cornet mouthpiece",
    ],
    links: [
      { title: "Printables — Mini Ophicleide", url: "https://www.printables.com/model/478359", type: "tutorial", description: "STL files and build notes" },
    ],
  },

  "PrintBone Trombone": {
    tips: [
      "Fully 3D-printed playable trombone with 8.5-inch bell",
      "Fits a Bach 42 slide connector",
      "PLA bell works surprisingly well acoustically",
      "OpenSCAD parametric design — customizable",
    ],
    links: [
      { title: "Printables — PrintBone v1.1", url: "https://www.printables.com/model/80017", type: "tutorial", description: "STL files, OpenSCAD source, and build guide" },
      { title: "PrintBone Demo", url: "https://www.youtube.com/watch?v=H_VVgddzFDI", type: "video", description: "Sound demonstration" },
    ],
  },

  "BASS Tin Whistle (in A)": {
    tips: [
      "Very low-pitched tin whistle — uses 46mm ID tube (75cm long)",
      "Requires 1.5m of M4 threaded rod and 48 M4 nuts for key mechanism",
      "1mm thick rubber sheet for airtight valve seals",
      "Uses key mechanism similar to bassoon or saxophone keys",
      "Guido Gonzato's whistle guide is essential reading before building",
    ],
    links: [
      { title: "Printables — BASS Tin Whistle", url: "https://www.printables.com/model/475125", type: "tutorial", description: "14 STL files with detailed build instructions" },
      { title: "Guido Gonzato — Whistle Guide", url: "https://www.guidogonzato.it/whistle/", type: "tutorial", description: "Essential reference for whistle construction" },
    ],
  },

  "Daphnis Pan Flute": {
    tips: [
      "Tuned 3D-printable pan flute with curved pipe arrangement",
      "Graduated pipes for easy playability",
    ],
    links: [
      { title: "Printables — Daphnis Pan Flute", url: "https://www.printables.com/model/439762", type: "tutorial", description: "STL files for the Daphnis pan flute v10" },
    ],
  },

  "Side-Blown Flute in A Major": {
    tips: [
      "3-part side-blown flute in A major with 6 finger holes",
      "Glue-together assembly — test fit before gluing",
    ],
    links: [
      { title: "Printables — Side-Blown Flute", url: "https://www.printables.com/model/1001883", type: "tutorial", description: "STL files and build guide" },
      { title: "Nicolas Bras — Flute Demo", url: "https://www.youtube.com/watch?v=UJITjxPpH4E", type: "video", description: "Playing demonstration" },
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
      "Decorative but functional — great gift or display piece",
    ],
    links: [
      { title: "Printables — Dragon Recorder", url: "https://www.printables.com/model/400647", type: "tutorial", description: "STL files with print profiles" },
    ],
  },

  "12-Hole Ocarina (Alto C)": {
    tips: [
      "Fully playable 12-hole ocarina covering over an octave",
      "Accurate tuning — play along with piano or other instruments",
      "Hold with both hands, thumb holes on bottom, finger holes on top",
    ],
    links: [
      { title: "Printables — 12-Hole Ocarina", url: "https://www.printables.com/model/24540", type: "tutorial", description: "STL files with makes and comments" },
    ],
  },

  "Small 5-Hole Ocarina": {
    tips: [
      "Small ocarina for kids — range C5 to D6",
      "Prints without supports, plays right off the build plate",
      "Great introduction to wind instruments for children",
    ],
    links: [
      { title: "Printables — Small Ocarina", url: "https://www.printables.com/model/249010", type: "tutorial", description: "STL files designed for kids" },
    ],
  },

  "Reedpipe": {
    tips: [
      "Simple single-reed pipe — like a clarinet practice chanter",
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
      { title: "Printables — Chalumeau", url: "https://www.printables.com/model/752555", type: "tutorial", description: "STL files for the modern chalumeau" },
    ],
  },

  "C Clarinet Remix (14mm Bore)": {
    tips: [
      "Remix of Tom's Chalumeau with 14mm bore",
      "3-part split body for easier printing and assembly",
      "Adjustable tuning via sliding joints",
    ],
    links: [
      { title: "Printables — C Clarinet Remix", url: "https://www.printables.com/model/888905", type: "tutorial", description: "STL files and remix notes" },
    ],
  },

  "Membrane Clarinet": {
    tips: [
      "Fully 3D-printed — no metal keys or reeds needed",
      "Uses a thin plastic sheet as a membrane reed",
      "Screw-together assembly for easy disassembly",
    ],
    links: [
      { title: "Printables — Membrane Clarinet", url: "https://www.printables.com/model/495171", type: "tutorial", description: "STL files and build guide" },
      { title: "Membrane Clarinet Demo", url: "https://www.youtube.com/watch?v=Jk7J4_bneZo", type: "video", description: "Sound demonstration" },
    ],
  },

  "Curvy Clarinet": {
    tips: [
      "Compact curvy design with soprano saxophone mouthpiece",
      "6-note pentatonic layout — easy to play melodies",
    ],
    links: [
      { title: "Printables — Curvy Clarinet", url: "https://www.printables.com/model/1605969", type: "tutorial", description: "STL files for the curvy clarinet" },
    ],
  },

  "Clarinet Mouthpiece (Playable)": {
    tips: [
      "Playable Bb clarinet mouthpiece",
      "Flexible bulb eliminates need for cork",
      "Can be used on any Bb clarinet as a replacement mouthpiece",
    ],
    links: [
      { title: "Printables — Clarinet Mouthpiece", url: "https://www.printables.com/model/557889", type: "tutorial", description: "STL files for the mouthpiece" },
    ],
  },

  "Trumpet Mouthpiece 3C": {
    tips: [
      "Based on Kanstul comparator profiles",
      "3C is a medium cup — versatile for most playing situations",
      "Print on its side for strength and better bore finish",
    ],
    links: [
      { title: "Printables — 3C Mouthpiece", url: "https://www.printables.com/model/446505", type: "tutorial", description: "STL files with comparator data" },
    ],
  },

  "Trumpet Mouthpiece 7C": {
    tips: [
      "Standard 7C — the most common beginner mouthpiece",
      "Shallower cup than 3C — easier for beginners",
      "Print on its side for best results",
    ],
    links: [
      { title: "Printables — 7C Mouthpiece", url: "https://www.printables.com/model/100591", type: "tutorial", description: "STL files for the 7C mouthpiece" },
    ],
  },

  "Trumpet Mouthpiece Puller": {
    tips: [
      "Tool for removing stuck mouthpieces from trumpets",
      "Uses 1/4-20 hardware (nuts and bolts)",
      "Print in strong material (PETG or ABS) for durability",
    ],
    links: [
      { title: "Printables — Mouthpiece Puller", url: "https://www.printables.com/model/692679", type: "tutorial", description: "STL files and hardware list" },
    ],
  },

  "D5 Drone Flute": {
    tips: [
      "Drone flute tuned to the Hijaz maqam (middle-eastern scale)",
      "Melody pipe and separate drone pipe sound simultaneously",
    ],
    links: [
      { title: "MakerWorld — D5 Drone Flute", url: "https://makerworld.com/en/models/566278", type: "tutorial", description: "STL files for the D5 drone flute" },
    ],
  },

  "Double Native American Flute": {
    tips: [
      "Two pipes: melody pipe and separate drone pipe",
      "Tuned to F# — a common key for Native American flutes",
    ],
    links: [
      { title: "Printables — Double Flute", url: "https://www.printables.com/model/452234", type: "tutorial", description: "STL files for the double flute" },
    ],
  },

  "Overly-Complicated Trumpet": {
    tips: [
      "Fully 3D-printed trumpet with 6 slide-based valves",
      "Based on Bb trumpet tubing lengths",
      "Impressively complex mechanical design",
    ],
    links: [
      { title: "Printables — Overly-Complicated Trumpet", url: "https://www.printables.com/model/492588", type: "tutorial", description: "STL files and build instructions" },
    ],
  },

  "Kudu Horn Trumpet (Shofar)": {
    tips: [
      "Functional Kudu horn trumpet inspired by the Jewish shofar",
      "Smooth spiral shape — plays as a natural brass instrument",
    ],
    links: [
      { title: "Printables — Kudu Horn", url: "https://www.printables.com/model/217052", type: "tutorial", description: "STL files for the shofar" },
    ],
  },

  "Kazoo": {
    tips: [
      "Hum into it — don't blow. The membrane vibrates with your voice",
      "Replace the membrane with balloon rubber or wax paper if it wears out",
    ],
    links: [
      { title: "Printables — Kazoo", url: "https://www.printables.com/model/30637", type: "tutorial", description: "Classic kazoo STL files" },
    ],
  },

  "HEXADIDG Didgeridoo": {
    tips: [
      "Produces a deep drone tone using circular breathing",
      "Hexagonal shape reduces print time while maintaining acoustic properties",
      "Two sizes available: full and mini",
    ],
    links: [
      { title: "Printables — HEXADIDG", url: "https://www.printables.com/model/734618", type: "tutorial", description: "STL files for the hexagonal didgeridoo" },
    ],
  },

  "Folk Shawm": {
    tips: [
      "Double-reed folk instrument — related to oboe and bombarde",
      "Uses compact hole placement for easier fingering",
      "A double reed is needed (can be purchased or made from cane)",
    ],
    links: [
      { title: "Demakein Folk Shawm", url: "https://github.com/pfh/demakein", type: "tutorial", description: "Generate custom shawm designs" },
    ],
  },

  "Shawm": {
    tips: [
      "Full-size double-reed shawm — larger and more powerful than folk version",
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
      "Medieval three-hole tabor pipe — played one-handed",
      "The other hand plays a drum (tabor)",
      "Can produce a surprising range with overblowing",
    ],
    links: [
      { title: "Demakein Tabor Pipe", url: "https://github.com/pfh/demakein", type: "tutorial", description: "Generate custom tabor pipe designs" },
    ],
  },

  "Dorian Whistle": {
    tips: [
      "Tuned to the Dorian mode — moody, minor-style scale",
      "Ideal for folk music, Celtic, and medieval styles",
    ],
    links: [
      { title: "Demakein Dorian Whistle", url: "https://github.com/pfh/demakein", type: "tutorial", description: "Generate custom whistle designs" },
    ],
  },
};

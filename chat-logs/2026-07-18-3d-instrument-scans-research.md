# 3D Scans & Models of Professional Acoustic Instruments
## Research Findings — 2026-07-18

---

## 1. Sketchfab Instrument 3D Models

### Summary
Sketchfab has a large collection of instrument models, but **nearly all are external-shell-only artistic renders**. Very few include internal bore geometry.

### Instruments Available
- **Clarinet**: ~20+ models (yusuferdem, Alaa Said, eline.nijhuis, Zihan Chi, etc.)
- **Flute**: ~10+ models
- **Saxophone**: Large tag page with dozens of models
- **Trumpet**: ~15+ models (Kagelok, lena-wachs, etc.)
- **Recorder**: ~5 models
- **Oboe**: ~3 models

### Quality
- Triangle counts range from 14k (low-poly) to 1.5M (high-poly)
- Most are hand-modeled in Blender/Maya from visual references, NOT scans
- A few (like yusuferdem's clarinet, 1.5M triangles) claim to use personal instruments as reference
- CGTrader's "Clarinet by Amati Kraslice" (high-poly, Substance Painter textures, 4K wood) is one of the most detailed

### Download Formats
- GLB, glTF, OBJ, USDZ (Sketchfab native)
- FBX, Blender (some models)

### License
- Free: CC-BY, CC0 (many models)
- Paid: "Fab" store models ($5-$50)

### Internal Bore Geometry
**❌ CRITICAL LIMITATION: No models include internal bore geometry. All are external shells.**

### URLs
- https://sketchfab.com/search?type=models&q=clarinet
- https://sketchfab.com/tags/saxophone
- https://sketchfab.com/search?type=models&q=flute
- https://www.cgtrader.com/3d-models/sports/music/clarinet-by-amati-kraslice (paid, most detailed clarinet)

---

## 2. Smithsonian 3D Collection — Instrument Models

### Summary
The Smithsonian has a few instrument 3D scans. The most notable is **Charlie Parker's alto saxophone**.

### Instruments Available
- **Charlie Parker's Alto Saxophone** — full 3D scan (body, neck, mouthpieces, ligatures, reed)
- **Pandereta (drum)** — Puerto Rican hand drum
- **Concerto Candelas Guitar** (Jose Feliciano's guitar)
- **Vina/Tamburi** — Indian stringed instrument
- **Cowbell** — small percussion instrument
- Various stringed instruments (vina, tamburi)

### Quality
- Charlie Parker sax: multiple resolution levels available (low-res preview + full-res)
- Industrial CT scanning / structured light scanning

### Download Formats
- **OBJ, GLB, glTF, USDZ** (full resolution + low-res versions)
- Charlie Parker sax files: `2019-10-1a-g_001-150k-4096_std.glb`, etc.

### License
- **Non-commercial, educational, and personal use only** (per 3d.si.edu disclaimer)

### Internal Bore Geometry
**❌ No internal bore geometry available. External scans only.**

### URLs
- https://3d.si.edu/object/3d/alto-saxophone-owned-and-played-charlie-parker:c7c58ff8-fd1f-4cf6-9813-6bca3cd0b8b3
- https://3d.si.edu/collections
- https://3d.si.edu/object/3d/pandereta
- https://3d.si.edu/object/3d/concerto-candelas-guitar-played-jose-feliciano

---

## 3. Printables.com Instrument Models

### Summary
Printables has a strong maker community creating **functional, playable** 3D-printed instruments. Several include internal bore geometry by design (since they're designed to be played).

### Instruments Available
- **Clarinet**: Curvy Clarinet (pentatonic, soprano sax mouthpiece), Modern Chalumeau in C, C Clarinet Remix (bore increased to 14mm), Tiny Clarinet (visual)
- **Flute**: Axianov Irish Flute (fully playable, key of D), Naust Traverso Flute (historical), Flutinet (clarinet mouthpiece + flute body hybrid)
- **Saxophone**: Flaxinet (hybrid flute/sax/clarinet), Trisax in B (mini saxophone), Foonki Instrument
- **Trumpet**: Overly-Complicated Trumpet (fully 3D printed, 6 valves/slides)
- **Membrane Clarinet**: Fully printed with plastic membrane reed

### Quality
- Functional instruments with documented bore dimensions
- Many are parametric (OpenSCAD-based or parametric STL)
- Bore dimensions explicitly designed (e.g., C Clarinet Remix bore = 14mm)

### Download Formats
- **STL** (primary)

### License
- Most are CC-BY or free/open

### Internal Bore Geometry
**✅ YES — These models INCLUDE internal bore geometry by design. Bore profiles are explicitly specified.**

### URLs
- https://www.printables.com/model/1605969-curvy-clarinet
- https://www.printables.com/model/1097180-axianov-irish-flute
- https://www.printables.com/model/492588-overly-complicated-trumpet
- https://www.printables.com/model/752555-clarinet-modern-chalumeau-in-c
- https://www.printables.com/model/477801-flaxinet
- https://www.printables.com/model/475112-flutinet
- https://www.printables.com/model/495171-membrane-clarinet
- https://www.printables.com/model/1721709-naust-traverso-flute
- https://www.printables.com/model/124694-trisax-in-b-mini-saxophoneclarinet

---

## 4. Thingiverse Instrument Models

### Summary
Thingiverse has some notable functional instruments, particularly the **PrintBone trombone** and various **Demakein-generated instruments**.

### Instruments Available
- **PrintBone**: Fully parametric 3D-printed trombone generator (7-inch and 8.5-inch bell)
- **Clarinet Mouthpiece**: Basic 3D-printable clarinet mouthpiece
- Various Demakein-generated flutes, whistles, shawms

### Quality
- PrintBone is extremely well-documented with acoustic modeling
- Bore profiles are parametric and acoustically validated

### Download Formats
- **STL** (primary)

### Internal Bore Geometry
**✅ YES — PrintBone explicitly models bore profiles using Bessel curves from academic research (Braden PhD thesis, University of Edinburgh)**

### URLs
- https://www.thingiverse.com/thing:2437630 (PrintBone)
- https://www.thingiverse.com/thing:12367 (Clarinet Mouthpiece)

---

## 5. MorphoSource — Scientific 3D Scans

### Summary
MorphoSource is a massive repository of scientific CT/3D scan data, but it focuses on **biological specimens (primate skulls, bones)**, NOT musical instruments.

### Instruments Available
**❌ No musical instruments found.** The database contains primate skeletal morphology data from museum collections.

### Quality
- Extremely high quality (microCT, medical CT, structured light scanning)
- Meshes in PLY format; CT stacks in DICOM/TIFF

### Download Formats
- PLY, DICOM, TIFF, OBJ

### License
- CC BY-NC for most academic datasets

### Internal Bore Geometry
**❌ Not applicable — no instruments in the collection**

### URLs
- https://www.morphosource.org/
- Note: MorphoSource could potentially host instrument CT data if contributed by researchers

---

## 6. Museum Collections with 3D — Instruments

### Germanisches Nationalmuseum (GNM), Nuremberg
**THE SINGLE MOST IMPORTANT SOURCE FOR INSTRUMENT 3D DATA**

### MUSICES Project (2014-2018)
- **100+ historically significant instruments** CT-scanned with industrial CT
- Instruments spanning 5 centuries (16th-20th)
- Includes: violins, flutes, clarinets, oboes, trumpets, viols, harps, organs
- Materials: wood, metal, mixed (woodwind with metal keys)
- Spatial resolution: **50 µm or better** (industrial CT at Fraunhofer EZRT)
- Data available via **MUSICES database** at musices.gnm.de
- CT data in **DICOM format** (open, non-proprietary)
- Best practice guide published: "Recommendations for the Three-Dimensional Computed Tomography of Musical Instruments"

### Instruments Scanned (examples from published papers):
- **MI5**: Viola da Gamba by Hanns Vogel (1563, Nuremberg) — 1725mm height
- **MI419**: Violin by Hummel — highest resolution scan (50 µm detail)
- Various **clarinets, oboes, flutes** (mixed-material instruments = hardest to scan)
- **Box-valve trumpet** — reveals internal valve mechanism
- **Basset horn**

### Quality
- Industrial CT resolution far beyond medical CT
- 60-9,000 keV radiation energy range
- Dual-energy material analysis capability
- Sub-100 µm spatial resolution

### Download Formats
- **DICOM** (primary — open standard for CT data)
- 3D reconstructions available through the MUSICES database

### License
- Data made available to broad public (open access per project goals)
- Metadata compatible with CIDOC-CRM, MIMO-LIDO, LIDO standards

### Internal Bore Geometry
**✅✅ YES — This is the GOLD STANDARD for internal bore geometry. Full volumetric CT data of the entire instrument including bore, tone holes, key mechanisms, material densities.**

### URLs
- https://musices.gnm.de/ (MUSICES database — searchable)
- http://objektkatalog.gnm.de/recherche (GNM object catalog)
- https://www.ndt.net/article/ctc2019/papers/iCT2019_Full_paper_64.pdf (published paper)
- https://www.gnm.de/your-museum-in-nuremberg/collections/collections-a-z/musical-instruments
- https://gepris.dfg.de/gepris/projekt/248476191 (DFG project page)

### Metropolitan Museum of Art
- ~5,000 instruments in collection (6 continents, 300 BCE to present)
- Has photogrammetry capability (sophisticated outfit as of 2024)
- 3D scanning program active since ~2016
- **Stradivari violins, Persian instruments, African drums, American pipe organ**
- Notable: Bartolomeo Cristofori piano (1720), Ming dynasty pipa
- **No publicly downloadable CT scan data found** (internal research use)

### URLs
- https://www.metmuseum.org/departments/musical-instruments

### British Museum / Other Museums
- Various museums have instrument collections but **no systematic public 3D instrument scanning programs found**

---

## 7. CT Scans of Instruments — Published Data

### MUSICES Project (see #6 above)
The primary source. 100+ instruments scanned.

### Bressan Recorder CT Scan (University of Southampton µ-VIS)
- **Pierre Jaillard "Peter Bressan" treble recorder** — "probably the most influential 18th Century recorder in any collection"
- CT scanned at µ-VIS X-ray Imaging Centre, University of Southampton
- **Full internal bore geometry including**:
  - Windway geometry (chamfer angles, edge position)
  - Tone hole undercutting in 3D (first time ever visualized)
  - 300-year bore distortion mapped
  - Wall thickness variations
- Resolution sufficient to see 50 µm details
- **Result: modern makers can now copy the original geometry**

### URLs
- https://www.southampton.ac.uk/muvis/case-studies/bressan.page
- https://muvis.org/case-study/recording-old-recorders-the-inner-world-of-bressan

### Pitt Rivers Museum / Cranfield University
- **18th-century ivory recorder** from Bate Collection, Oxford
- Scanned on Nikon XT H225 micro-CT at Cranfield University
- Revealed wood-boring beetle damage in the block
- Converted to STL for 3D printing

### URLs
- https://www.prm.ox.ac.uk/plastic-fantastic-ct-scan

### University of Turin CT Scans
- **Piccolo flute** (boxwood/ ivory, English/American origin)
- **Baroque transverse flute** (Lorenzo Cerino, Italian, late 18th century)
- CT scan resolution: **46 µm voxel size**
- Goal: create 3D-printable replicas for acoustic testing
- Used Hamamatsu Microfocus L8121-03 X-ray source

### URLs
- https://doi.org/10.3390/jimaging8100260 (published paper)
- https://www.ndt.net/article/art2023/papers/art2023_p129.pdf

### Virtual 3D Clarinet Museum (2025)
- **147 historical clarinets** documented (1750-2024)
- Acoustic impedance spectroscopy + laser Doppler vibrometry + 3D photogrammetry
- Bore profiles measured at 5mm intervals
- CT revealed internal structures at 0.02mm resolution
- Formant analysis: grenadilla (2.3 kHz) vs boxwood (1.8 kHz)

### URLs
- https://doi.org/10.5216/mh.v25.83307

### Full Waveform Inversion for Bore Reconstruction
- Academic method to reconstruct bore geometry from acoustic measurements
- Successfully reconstructed a cylindrical tube with 4 side holes (14 design variables)
- Results match physical measurements within ~0.3mm accuracy
- Computation time: ~1 minute on laptop

### URLs
- https://acta-acustica.edpsciences.org/articles/aacus/full_html/2021/01/aacus210048/aacus210048.html

---

## 8. Photogrammetry of Instruments — Guides & Datasets

### Published Guides
- **Formlabs Photogrammetry Guide**: Step-by-step tutorial comparing software options (Agisoft, RealityCapture, 3DF Zephyr, etc.)
- **InstrumentHeritage.com**: Comprehensive guide for instrument preservation using 3D scanning (structured light, laser, photogrammetry, CT)

### Academic Papers
- **Patrucco et al. (2018)**: "Image and Range-Based 3D Acquisition and Modeling of Popular Musical Instruments" — SAMIC project, Italy
  - Compared laser scanning (Hexagon RS3, 30µm accuracy) vs photogrammetry (Canon EOS 5DSR, 50.3MP)
  - Created sub-millimeter accuracy models
  - Published via 3DHOP open-source viewer
  - DOI: https://doi.org/10.35492/docam/5/2/9

- **Llorca-Bofí et al. (2018)**: "3D modelling photogrammetry to support acoustic measurements"
  - 171 photos, Agisoft Photoscan
  - DOI: https://doi.org/10.2581/zenodo.2583208

### Datasets
- **SAMIC project** (Italy): 14 3D models of folk instruments from "Museo del Paesaggio Sonoro"
  - Models available via 3DHOP platform
  - Instruments: torototela, clay whistle, whirling disc, bull roarer, hunting calls, mirlitons

### Key Challenges for Instrument Photogrammetry
- **Reflective metal parts** need special setup (scanning spray, matte coating)
- **Thin edges** (reeds, labia) difficult to capture
- **Internal bore geometry** cannot be captured by photogrammetry (external only)
- **Moving parts** (keys, mechanisms) must be immobilized

### URLs
- https://formlabs.com/blog/photogrammetry-guide-and-software-comparison/
- https://instrumentheritage.com/3d-scanning-technology-preservation/
- https://doi.org/10.35492/docam/5/2/9

---

## 9. 3D Scan of Clarinet/Flute/Oboe — Specific Searches

### Clarinet 3D Scans
- **MUSICES/GNM**: Historical clarinets CT-scanned (mixed material = most challenging)
- **Amati Kraslice ACL 312** (CGTrader): High-poly hand-modeled, not a scan but claims "wall thickness of the wooden part and the radius of its hole" are accurate
- **Charlie Parker's Saxophone** (Smithsonian) — closest to professional wind instrument scan publicly available
- **Virtual 3D Clarinet Museum**: 147 historical clarinets documented (2025)

### Flute 3D Scans
- **Bressan recorder** (µ-VIS): Full internal CT scan, bore profile + tone hole undercutting
- **University of Turin flutes**: Piccolo + baroque transverse flute, 46µm resolution CT
- **RCM Museum (London)**: 3D-printed copies of 8 historical woodwinds including recorders, flute, clarinet, oboe, cornett
- **Willisau Knochenflöte Project**: CT scan of a bone flute for replication

### Oboe 3D Scans
- **MUSICES/GNM**: Historical oboes scanned (mixed material with metal keys)
- Less specific public data than flutes/clarinets

### URLs
- https://www.rcm.ac.uk/about/news/all/2024-02-223dprintedinstruments.aspx
- https://research.3dmusicinstruments.com/

---

## 10. Open-Source CAD Models — GrabCAD, TraceParts, 3D ContentCentral

### 3D ContentCentral (Dassault Systèmes)
- **Trumpet (TR300)**: Brass trumpet CAD model available in SOLIDWORKS format
- Free download for registered users

### 3D CAD Browser
- **Trumpet**: STEP, IGES formats (compatible with SolidWorks, AutoCAD, Fusion 360, etc.)
- **Tenor Recorder Flute**: STEP, IGES formats
- **Clarinet**: Various models
- Polygonal versions in MAX, FBX, OBJ, BLEND, C4D

### CGTrader (Commercial)
- **Clarinet by Amati Kraslice**: Most detailed — "complete and detailed copy of the original with such details as the size, shape of the buttons, the thickness of the walls of the wooden part and the radius of its hole"
- **Parametric Music Pipe Trumpet/Trombone/Bugle/Clarinet**: Free parametric 3D-printable model
- **Wood Clarinet**: Manifold geometry, no N-gons, 2K textures, PBR materials

### TraceParts
- General industrial parts library; limited musical instrument content

### Internal Bore Geometry
**❌ Generally NO — CAD models on these platforms are external shells only**

### URLs
- https://www.3dcontentcentral.com/Download-Model.aspx?catalogid=171&id=183275
- https://www.3dcadbrowser.com/3d-model/trumpet-51631
- https://www.3dcadbrowser.com/3d-model/tenor-recorder-flute
- https://www.cgtrader.com/3d-models/sports/music/clarinet-by-amati-kraslice
- https://www.cgtrader.com/free-3d-print-models/hobby-diy/hobby-accessories/parametric-music-pipe-trumpet-trombone-bugle-clarinet

---

## 11. Parametric Instrument Models — OpenSCAD/FreeCAD/Build123d

### OpenSCAD Instruments

#### PrintBone (Trombone Generator) ⭐⭐⭐
- **Fully parametric** trombone generator in OpenSCAD
- Bore profiles based on **Bessel curves** from Braden PhD thesis (University of Edinburgh, 2006)
- Can generate any trombone design with any bell profile
- Includes modern bore shapes AND baroque models
- Tested 7-inch and 8.5-inch bell versions
- Compatible with commercial trombone parts (Bach 42, Conn 48H/6H)

#### OpenSCAD Alphorn
- Fully parametric F alphorn (3880mm total length)
- 19 sections with bayonet couplings
- All parameters adjustable (length, wall thickness, curve angle, etc.)

#### Demakein-derived instruments
- Multiple OpenSCAD files from Demakein lineage

### FreeCAD Instruments

#### 3DGuitar Module
- FreeCAD module for parametric guitar generation
- Adjustable: body dimensions, fretboard, neck, cutaway, pickups

#### 3D-printed Labial Pipe (Organ Pipes)
- OpenSCAD + FreeCAD files for labial pipe components
- Parametric: labium angle, bore dimensions, wall thickness

### Build123d / CadQuery Instruments

#### pylele (Python Ukulele Generator)
- Python library using CadQuery, Blender, Trimesh, SolidPython2, Manifold3D
- Generates parametric ukulele/string instrument bodies
- Multiple backend support (CadQuery most accurate)

### TaPAS Project
- Python-based tool for acoustic physical modelling of saxophones
- Uses **OpenWInD** library for acoustic simulation
- **CadQuery** for 3D modeling (via FreeCAD integration)
- JUCE for VST plugin development
- Goal: real-time virtual instrument from physical bore parameters

### URLs
- https://github.com/pieterbos/PrintBone
- https://github.com/dankney/alphorn
- https://github.com/bguan/pylele
- https://github.com/benjaminwand/3d-printed-labial-pipe
- https://github.com/jptned/3DGuitar
- https://github.com/alexxior/TaPAS

---

## 12. GitHub Repos with Instrument 3D Data

### Demakein ⭐⭐⭐⭐ (MOST IMPORTANT)
- **URL**: https://github.com/pfh/demakein
- Python 3 tools for **designing and making woodwind instruments**
- **Design stage**: Numerical optimization of bore shape + finger hole placement/size/depth
- **Make stage**: Generates 3D objects, segments for 3D printing or CNC milling
- Built-in instruments: flutes, whistles, shawms
- Parametric — transposable to any key
- **Internal bore geometry: YES — this is the core data**
- Generates STL files for 3D printing

### Chalumier
- **URL**: https://github.com/MarkChuCarroll/chalumier
- Woodwind design tool **based on Demakein**
- Uses evolutionary algorithm (faster than Demakein's approach)
- Goal: design a modern 3D-printable basset horn
- Generates instrument design SVGs + JSON parameters
- Output: bore profile, hole positions, intonation analysis

### Lutherie_3D
- **URL**: https://github.com/melROLL/Lutherie_3D
- **25+ instrument designs** tested and working
- Wind instruments: Alto Trombone, Duduk (3 variants), Pan Flute, Serpent, Shakuachi, Trisax, Micro/Nano Trumpet, Zurna_Duduk, Kitty Bone, Squarebone
- String instruments: Oud, Saz, Baglama, Kokyu, various guitars/ukuleles

### openNSP_Project (Northumbrian Small-Pipes)
- **URL**: https://github.com/Z-QIAO/openNSP_Project
- OpenSCAD model of Northumbrian small-pipes
- Based on historical measurements from Mike Nelson
- Accurate chanter modeling with tone hole data

### 3D Modeling of Musical Instruments
- **URL**: https://github.com/ZhiyuAlexZhang/3d-modeling-of-musical-instruments
- MIT License
- Saxophone mouthpiece (Rhino), saxophone reed (OpenSCAD)
- STL files included

### Other Notable Repos
- **Fujara**: https://github.com/tonykoop/fujara — parametric Slovak overtone flute
- **Chalumeau**: https://github.com/tonykoop/chalumeau — parametric chalumeau family (SolidWorks + OpenSCAD)
- **gugulele**: https://github.com/bguan/gugulele — parametric ukulele (OpenSCAD)

---

## 13. Academic 3D Scan Datasets

### Historical Small Bassoon Datasets (Zenodo) ⭐⭐⭐
- **URL**: https://www.historical-bassoon.ch/datasets-links-to-zenodo/
- **60+ detailed datasets** of fagottini and tenoroons (18th-19th century)
- Contains:
  - Bore diameters at regular intervals (external + internal)
  - Tone hole dimensions and angles
  - Bocal dimensions
  - Photographic/video material
  - **Bore profile measurements** (inner bore dimensions)
- 4 instruments also **CT-scanned and 3D-printed** (FT40, FT44)
- Published by Schola Cantorum Basiliensis (SNSF research projects)
- Open access on Zenodo

### Datasets (individual examples on Zenodo):
- FT47 Riva 13-key tenoroon: comprehensive measurement dataset
  - https://doi.org/10.5281/zenodo.3246324

### Arthur H. Benade Archive (Stanford CCRMA)
- **URL**: https://ccrma.stanford.edu/marl/Benade/research.html
- Contains:
  - Clarinet mouthpiece measurements
  - Clarinet bore and hole measurements, positions of resonances
  - **Oboe bore measurements** and calculations
  - **Flute dimensions and resonance measurements**
  - Bassoon blueprints
  - Flute headjoint taper perturbation data
- Historical acoustic measurement data (1960s-1990s)

### Wolfe Lab Impedance Databases (UNSW Sydney)
- **Clarinet acoustics database**: Impedance spectra + sound spectra for all fingerings
- **Saxophone acoustics database**: Impedance spectra for soprano and tenor sax
- Bore angle measurements:
  - Soprano sax half-angle: 1.74°
  - Tenor sax half-angle: 1.52°
  - Oboe half-angle: 0.71°
  - Bassoon half-angle: 0.41°

### URLs
- https://www.historical-bassoon.ch/
- https://www.historical-bassoon.ch/datasets-links-to-zenodo/
- https://ccrma.stanford.edu/marl/Benade/research.html
- https://www.phys.unsw.edu.au/jw/bore-angle.html
- https://newt.phys.unsw.edu.au/jw/reprints/Wolfe_AT2018.pdf

---

## 14. Instrument Maker 3D Scans

### Royal College of Music Museum (London) ⭐⭐⭐
- Created **8 3D-printed copies of historical woodwind instruments**
- Instruments: 3 recorders, flute, clarinet, oboe, Renaissance cornett
- Spanning mid-17th to mid-18th centuries
- Several originally made of ivory
- **"Reverse engineered to virtually repair any cracks, dents and imperfections"**
- Printed copies suitable for **professional performance**
- Collaboration: Prof. Gabriele Rossi Rognoni + Prof. Gabriele Ricchiardi (University of Turin)

### URLs
- https://www.rcm.ac.uk/about/news/all/2024-02-223dprintedinstruments.aspx

### Flutemaker Lab (Software)
- **URL**: https://sites.google.com/view/flutemaker-lab
- Professional software for designing bore profiles
- Features: bore measurement tables, cross-section view, bore profile comparison, perturbation analysis
- Used by professional flute makers

### research.3dmusicinstruments.com
- **URL**: https://research.3dmusicinstruments.com/
- Research hub for 3D-printed musical instruments
- Applications:
  - Replicas of museum instruments
  - Reconstruction of damaged historical instruments
  - Development of new/custom instruments
  - Scaled replicas for modern pitch standards
  - Interpolation between different instrument models
- Examples: Willisau Knochenflöte Project, special cornetto, reed shapers

---

## 15. Hornbostel-Sachs 3D Collection

### Summary
**No systematic 3D collection based on Hornbostel-Sachs classification exists.** However, the classification system itself is digitized:

### Digital H-S Classification
- **ACDH-CH/DARIAH Vocabularies**: SKOS format taxonomy
  - https://vocabs.acdh.oeaw.ac.at/hsinstruments_thesaurus/en/

### MIMO (Musical Instrument Museums Online)
- 2011 revision of H-S by MIMO Consortium
- International directory of musical instrument collections
- Linked Open Data API:
  - https://vocabulary.mimo-international.com/HornbostelAndSachs/en/
- **No 3D scan component** — primarily 2D images and metadata

### MODAVIS Project (GitHub)
- **URL**: https://github.com/modavis-project/musical-instrument-classes
- JSON databases of H-S classifications with 2724 instrument translations
- Designed for LLM integration
- MIMO page references for each instrument

### URLs
- https://icom-music.mini.icom.museum/resources/classification-of-musical-instruments/
- https://github.com/philharmoniedeparis/mimo/
- https://github.com/modavis-project/musical-instrument-classes

---

## 16. Cross-Section Data / Bore Profiles

### Published Bore Profiles

#### Bressan Recorder Bore Measurements
- Detailed bore profiles of 5 alto recorders by Peter Bressan
- Measured at regular intervals using custom tools
- Published bore profile graphs (10:1 diameter-to-length ratio)
- Key finding: "surprisingly great variation in length and bore profiles" between instruments
- **URL**: https://www.fomrhi.org/uploads/bulletins/Fomrhi-118/Comm%201929.pdf

#### Danish Recorder CT Bore Profile
- Soprano recorder (c.1650-1675), ivory, Musikhistorisk Museum Copenhagen
- CT scan bore profile with dimensions at multiple cross-sections
- Windway measurements, step geometry, labium angles
- Playing test data with wind pressure and cents deviation
- **URL**: https://en.natmus.dk/fileadmin/user_upload/Editor/natmus/musikmuseet/Dokumenter/sopraninoblokfloejte.pdf

#### Benade Archive Bore Data
- Oboe bore measurements and calculations
- Flute dimensions and resonance measurements
- Clarinet bore and hole measurements
- **URL**: https://ccrma.stanford.edu/marl/Benade/research.html

#### Flute Headjoint Taper Data
- Benade's flute headjoint taper perturbation data
- Fulton Wright's data (1972) on flutes

### Bore Reconstruction from Acoustics
- **Full Waveform Inversion (FWI)**: Reconstruct bore geometry from impedance measurements
- Successfully tested on cylindrical tube with 4 side holes
- Can recover: bore length, bore radii, hole positions, hole radii, chimney heights
- **Accuracy**: within 0.3mm of physical measurements

### URLs
- https://www.fomrhi.org/uploads/bulletins/Fomrhi-118/Comm%201929.pdf
- https://acta-acustica.edpsciences.org/articles/aacus/full_html/2021/01/aacus210048/aacus210048.html

---

## 17. TaPAS Project / OpenWInD + CadQuery + FreeCAD

### TaPAS
- **URL**: https://github.com/alexxior/TaPAS
- Goal: VST plugin for acoustic physical modelling of saxophones
- Stack:
  - **OpenWInD**: Acoustic simulation library (Python, GPL-3)
  - **CadQuery**: Parametric 3D modeling (via FreeCAD)
  - **JUCE**: Audio plugin framework
- Real-time virtual instrument from physical bore parameters

### OpenWInD ⭐⭐⭐⭐
- **URL**: https://openwind.inria.fr/
- **Open-source Python library** for wind instrument simulation
- Three modules:
  1. **Impedance computation**: Telegrapher's equations, FEM, Transfer Matrix Method
  2. **Sound simulation**: Reed/lips coupled to pipe (time domain)
  3. **Instrument geometry optimization**: Bore reconstruction from measured impedance
- Supports: cylinders, cones, splines, Bessel Horn, any axisymmetric bore shape
- Thermo-viscous losses, radiation conditions, tone holes, valves
- **GUI available**: https://demo-openwind.inria.fr/
  - Define bore geometry interactively
  - Compute impedance
  - **Generate 3D STL export** directly from the web interface
  - Specify wall thickness, hole positions, fingering chart
- Published scientific papers backing the acoustics

### URLs
- https://openwind.inria.fr/
- https://demo-openwind.inria.fr/
- https://pypi.org/project/openwind/
- https://github.com/alexxior/TaPAS
- https://pub.dega-akustik.de/ISMA2019/data/articles/000047.pdf

---

## 18. Demakein — Internal Geometry Data

### Demakein ⭐⭐⭐⭐⭐ (MOST IMPORTANT FOR AI INSTRUMENT DESIGN)

**URL**: https://github.com/pfh/demakein
**Author**: Paul Harrison (pfh@logarithmic.net)
**License**: Open source

### What Demakein Generates Internally

#### Design Stage (Acoustic Optimization)
- **Bore profile**: Piecewise linear inner diameter specification
  - First element = bore diameter at base
  - Last element = bore diameter at top
  - Intervening elements = bore diameter boundaries between pieces (kinks)
  - Exact placement determined by numerical optimization
- **Bore shape**: Supports cylindrical, conical, stepped bores
- **Finger hole parameters** (optimized for correct pitch):
  - Position along bore (distance from reference point)
  - Radius (size)
  - Chimney height (depth through wall)
- **Outer diameter profile**: Defines wall thickness (depth of finger holes)
- **Register hole**: Optional, position and size optimized
- **Closed/open top**: Configurable boundary conditions

#### Configuration Options
```
closed_top: bool (reed/brass = closed, ney = open, flute = open)
inner_diameters: list of floats [or tuples (low,high) for steps]
initial_inner_fractions: list of floats (minimum segment sizes)
outer_diameters: list of floats (or independent of bore)
outer_add: bool (additive vs independent outer diameter)
```

#### Built-In Instrument Types
1. **Folk Flute** (open bore, open top)
2. **Conical Flute** (conical bore)
3. **Whistle/Tin Whistle** (fipple mouthpiece)
4. **Shawm** (double reed, conical bore)
5. **Reed Pipe** (single reed, closed top)

#### Make Stage (3D Object Generation)
- Segments instrument for 3D printing (vertical orientation)
- Socketed joints optional
- CNC milling mode available
- Outputs: **STL files** for each segment

### Usage Example
```bash
# Design a folk flute transposed up 12 semitones
demakein design-folk-flute: myflute --transpose 12

# Generate 3D printing files
demakein make-flute: myflute

# Or generate CNC milling files
demakein make-flute: myflute --mill yes --open yes --prefix milling
```

### Chalumier (Demakein Fork)
- **URL**: https://github.com/MarkChuCarroll/chalumier
- Written in Java (vs Demakein's Python)
- Uses evolutionary algorithm (much faster)
- Same core bore/hole optimization approach
- Goal: 3D-printable basset horn

### What You Get from Demakein
- **Bore profile** (complete internal geometry)
- **Hole positions, sizes, depths** (optimized for intonation)
- **3D printable STL** of the complete instrument
- **Acoustic simulation** (impedance computation)

### Internal Bore Geometry
**✅✅✅ YES — Demakein's entire purpose is computing the optimal bore profile and hole layout. The bore geometry IS the design output.**

---

## Summary: Best Sources by Use Case

### For Internal Bore Geometry (Critical for Acoustic Design)

| Source | Instruments | Data Quality | Access |
|--------|-------------|--------------|--------|
| **MUSICES/GNM** | 100+ historical (all types) | Industrial CT, 50µm | Open (DICOM) |
| **Demakein** | Flutes, whistles, shawms (any key) | Parametric bore profiles | Open source |
| **OpenWInD** | Any wind instrument | FEM acoustic simulation + 3D export | Open source |
| **Historical Bassoon (Zenodo)** | 60+ fagottini/tenoroons | Manual bore measurements + 4 CT scans | Open access |
| **Bressan Recorder (µ-VIS)** | 1 recorder | MicroCT, ~50µm | Published data |
| **Benade Archive** | Clarinet, oboe, flute, bassoon | Historical measurements | Academic |
| **Wolfe Lab (UNSW)** | Clarinet, saxophone | Impedance spectra + bore angles | Academic |

### For External 3D Reference Models

| Source | Count | Quality | Format |
|--------|-------|---------|--------|
| **Sketchfab** | 100+ | Variable (artistic to detailed) | GLB, OBJ |
| **CGTrader** | 50+ | Professional (PBR, manifold) | OBJ, FBX, STL |
| **Smithsonian** | ~6 instruments | Museum-quality scans | OBJ, GLB, USDZ |
| **Printables** | 20+ playable | Functional (bore included) | STL |
| **3D CAD Browser** | 10+ | CAD solid models | STEP, IGES |

### For Playable 3D-Printed Instruments

| Source | Instruments | Notes |
|--------|-------------|-------|
| **Printables** | Clarinet, flute, trumpet, sax hybrids | Community-tested |
| **Thingiverse/PrintBone** | Trombone | Acoustically validated |
| **Demakein** | Flutes, whistles, shawms | Optimal intonation |
| **Lutherie_3D** | 25+ instruments | Many tested |
| **RCM Museum** | Historical copies | Professional performance quality |

---

## Key Takeaways for AI Instrument Design

1. **External-only models are nearly useless for acoustic design** — Sketchfab, CGTrader, and most museum 3D data only capture the outside.

2. **MUSICES/GNM is the gold standard** for internal bore data, but access may require research collaboration.

3. **Demakein + OpenWInD together form a complete pipeline**: Demakein computes optimal bore profiles, OpenWInD simulates acoustics, CadQuery generates CAD geometry.

4. **Printables has the best community of functional instrument makers** — their models include bore geometry because they're designed to actually play.

5. **CT scanning is the only way to get internal geometry of existing instruments** — photogrammetry and structured light scanning cannot capture bore profiles.

6. **Bore profile data exists in academic literature** (Benade Archive, Wolfe Lab, Bressan studies) but often as measurements/tables rather than 3D models.

7. **No systematic 3D collection exists organized by Hornbostel-Sachs** — this would be valuable to create.

8. **The TaPAS project (OpenWInD + CadQuery + FreeCAD) is the closest to an end-to-end AI instrument design pipeline** — it connects acoustic simulation to 3D modeling to audio plugin.

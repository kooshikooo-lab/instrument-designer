# Verified References (from ChatGPT research, Jul 2026)

## Bass Clarinet
1. Range/dimensions — martinfreres.net, "Exploring the Bass Clarinet"
   https://martinfreres.net/exploring-the-bass-clarinet-an-essential-guide-for-musicians/

2. Bb clarinet total length & bore — Vienna Symphonic Library
   https://www.vsl.co.at/academy/woodwinds/clarinet

3. 1911-era bass clarinet bore (42-43in) — Theodora Encyclopedia
   https://theodora.com/encyclopedia/b/bass_clarinet.html

4. Register hole position (84mm/588mm length) — Szwarcberg 2024
   arXiv:2404.07540 — "Second register production on the clarinet: nonlinear losses in the register hole as the decisive physical phenomenon"
   https://arxiv.org/pdf/2404.07540

5. Register tube dimensions (Buffet Crampon Festival: 13mm length, 3mm diameter) — Szwarcberg 2025
   arXiv:2601.01981 — "How localized nonlinear losses condition the acoustical design of a self-sustained oscillator: the clarinet and its register hole"
   https://arxiv.org/pdf/2601.01981

6. Bass clarinet tonehole optimization methodology — "Virtual Bass-Clarinet In Modalys"
   https://www.academia.edu/107985181/Virtual_Bass_Clarinet_In_Modalys

## Trumpet
7. Bach 180-37 bore/bell specs — Schmitt Music
   https://www.schmittmusic.com/products/bach-stradivarius-18037-bb-trumpet

8. Trumpet tubing length (1.475m) & valve slide lengths — Trumpet Heroes
   https://trumpetheroes.com/trumpet-valves/

9. Valve slide lengths (Yamaha: V1=160mm, V2=70mm, V3=270mm)
   https://www.yamaha.com/en/musical_instrument_guide/trumpet/mechanism/mechanism002.html

10. Compound slide-length error on valve combinations — CMUSE
    https://www.cmuse.org/trumpet-valve-length-calculator

## Acoustics & Optimization
11. Clarinet twelfths tuning optimization — Debut, Kergomard, Laloë (2005)
    Applied Acoustics 66, 365-409. arXiv:physics/0309051
    https://arxiv.org/pdf/physics/0309051

12. Bass clarinet register intonation (~20c flat/sharp) — US Patent 10380980
    https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10380980

13. Speaker hole placement rule (~1/3 from reed) — S. Fox Clarinets
    http://www.sfoxclarinets.com/baclac_art.htm

14. Bessel horn flare parameter definition — Duke Physics
    https://webhome.phy.duke.edu/~dtl/136126/36hg_wnd.html

15. Horn cutoff frequency/reflectance behavior — PMC3316681
    https://pmc.ncbi.nlm.nih.gov/articles/PMC3316681/

16. Bessel horn brass bore optimization thesis — Braden, U. Edinburgh (2006)
    https://www.acoustics.ed.ac.uk/wp-content/uploads/Theses/Braden_Alistair__PhDThesis_UniversityOfEdinburgh_2006.pdf

## Key Findings from ChatGPT Analysis (2026-07-23)

### Trumpet
- Keep 1.335m tube length (do NOT lengthen to 1.392m — that fixes one resonance but distorts all higher ones)
- Mouthpiece ≠ 140mm of cylinder. Model explicitly: cup (17mm, r=8.5) + throat (8mm, r=1.83) + backbore (55mm, taper 1.83→2.9) + receiver (25mm, taper 2.9→4.38)
- Expected mouthpiece effect: ~15-35c (243Hz → 236-239Hz). Remaining 5-10c from receiver geometry, bell profile, temperature.
- 72c error is too large for mouthpiece alone. Tube geometry slightly short acoustically.

### Bass Clarinet
- Register hole diameter: 3.2-3.8mm (NOT 5-6mm or 8-10mm)
- Register hole chimney height: 2.5-4mm (NOT ~22mm)
- Primary vent position: 540-560mm from reed (for ~1650mm effective length)
- Two-vent systems: mechanically linked, not always open
- Debut et al. finding: register vent is NOT the dominant source of twelfth tuning error. Bell, toneholes, taper all produce comparable shifts that partially cancel.

## General Acoustics & Woodwind Design References

1. **Benade, A.H. (1976).** *Fundamentals of Musical Acoustics.* Oxford University Press. — Classic text covering clarinet bore acoustics, bells, toneholes, and register vents (Chapters 20-24).

2. **Benade, A.H. (1990).** *Fundamentals of Musical Acoustics,* 2nd ed. Dover. — Expanded treatment of impedance, tonehole lattices, and woodwind design.

3. **Keefe, D.H. (1981).** "Acoustical wave propagation in cylindrical ducts: Transmission line parameter approximations for isothermal and nonisothermal boundary conditions." *Journal of the Acoustical Society of America,* 70(1), 58-62. — Transmission-matrix methods for woodwinds.

4. **Keefe, D.H. (1982).** "Theory of the single woodwind tone hole." *Journal of the Acoustical Society of America,* 72(3), 676-687. — Standard analytical treatment of tonehole impedance and interactions.

5. **Nederveen, C.J. (1998).** *Acoustical Aspects of Woodwind Instruments.* Northern Illinois University Press. — Comprehensive reference on bore geometry, bells, toneholes, radiation, and register mechanisms.

6. **Dalmont, J.P. & Kergomard, J. (1990s-2000s).** Multiple papers in *Journal of the Acoustical Society of America* on clarinet input impedance, radiation, and bore perturbations. — Extensive experimental validation.

7. **Bordeaux Woodwind Acoustics Group (Université de Bordeaux).** Publications by Kergomard, Dalmont, and colleagues on transfer-matrix and finite-element methods for clarinet modeling. — Basis for modern closed-top tonehole model.

8. **Szwarcberg, A. (2025).** "A Direct Measurement of an Acoustic Field inside a Clarinet: The Register Hole and the Twelfth." *arXiv:2601.01981.* — Measured soprano clarinet register tube: 13mm length × 3mm diameter (Buffet Crampon Festival).

## Bell Design & Harmonic Distortion Notes (2026-07-23, ChatGPT)
- Bell flare inherently distorts harmonic series: the fundamental (1st register) is lowered more than the 3rd harmonic (2nd register), widening the 12th ratio above 3:1
- Quadratic flare (r=r0+dr*(x/L)²) preserves harmonics significantly better than Bessel (r=r0*(1+x/L)^n) or exponential flares
- Short bell (80mm, 36mm exit) with quadratic flare gives only +1c 12th error; longer/wider bells increase distortion quadratically
- 160mm bell with 44mm exit gives +26c plain-tube 12th error; with toneholes the full instrument gives ~41c RMS twelfths
- The register hole cannot fully compensate for bell-induced harmonic distortion
- Real clarinet bells (180-260mm, 50-55mm ID) accept significant harmonic distortion for timbre/projection reasons
- Bell affects mostly lowest 2-3 notes; higher notes radiate primarily through open toneholes
- References: Benade (1976, 1990), Keefe (1981, 1982), Nederveen (1998), ChatGPT research (2026-07-23)

## Bell Distortion Analysis (2026-07-23, ChatGPT)

### Key Findings
- Professional bass clarinet bells do NOT cause 40-400 cent twelfth distortion. Real instruments have ±10-30c twelfths.
- The bell is ONE OF THE SMALLEST contributors to twelfth error (Benade, Keefe, Nederveen).
- Three likely causes if TMM shows 100-400c bell-induced distortion:
  1. Incomplete tonehole lattice (7 holes vs 22-25 in real instruments) — the missing hole lattice removes distributed radiation that shields the bell from most modes
  2. Bell radiation boundary condition — a flared bell needs frequency-dependent radiation impedance, not simple open-pipe termination
  3. Transfer-matrix implementation artifact in the stepped-cylinder bell section

### Recommended Investigations (priority order)
1. Compute input impedance |Z(f)| before/after adding bell — does the bell shift only the first peak or all peaks?
2. Compare TMM vs OpenWind for identical geometries — this isolates numerical vs physical effects
3. Add open toneholes incrementally (1, 2, 3...) to observe how bell influence decreases with distributed radiation
4. Discretization convergence study: 80 → 160 → 320 → 640 segments
5. Audit the bell radiation boundary condition in the TMM implementation

### Most Likely Hypothesis
The 7-hole model leaves a long uninterrupted tube (359mm from last hole to bell start in worst case) which gives the bell far more influence than it has on a real instrument with 22-25 holes providing distributed shunt impedance.

### Sources
- ChatGPT analysis based on: Benade (1976), Keefe (1982), Nederveen (1998), Dalmont & Kergomard (1990s-2010s)
- Full context in prompt_bell_distortion.md

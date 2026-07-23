# Bass Clarinet Design Automation — Status

## Code Structure
- `backend/tmm_acoustics.py` — TMM engine (phase-based, ported from chalumier)
- `backend/optimizer_global.py` — **NEW**: Global fingering-chart optimizer (DE + L-BFGS-B)
- `backend/tmm_optimizer_sequential.py` — Sequential Bordeaux optimizer (works for ≤8 holes)
- `backend/bass_clarinet_full_test.py` — Validated 7-hole D major + register (uniform cyl)
- `config/bass_clarinet_7hole.json` — Working 7-hole config (9.5c RMS twelfths)
- `config/bass_clarinet_7hole_bell.json` — 7-hole + quadratic bell (41c twelfths)

## What Works
1. **7-hole D major diatonic** — 0.00c RMS 1st register, 7.96c RMS 2nd register, 9.5c RMS twelfths
2. **Register hole** — optimized 80mm/2.5mm/3mm (position/diameter/chimney)
3. **Global optimizer** — reproduces sequential results for 7-hole case
4. **2nd register optimization** — 7.96c RMS with 11mm holes on 25mm bore
5. **Phase sweep diagnostics** — working for model validation

## What's Blocking
1. **12+ hole chromatic** — best result 15-20c RMS (vs 0.00c for 7-hole)
   - Sequential optimizer clusters last holes (200-600c errors)
   - Global optimizer (DE) finds 20.67c RMS, takes 2.5 min
   - Global optimizer (L-BFGS-B only) finds 15.43c RMS
2. **Bell flare validation** — 41c RMS may be TMM artifact, need OpenWind comparison
3. **OpenRouter API** — expired, need replacement for AI-assisted coding

## Theoretical Questions (Research Needed)
1. **TMM tonehole model** — Is the phase-based approach with tanner/untanner correct at 70-150Hz?
2. **Chromatic optimization** — What algorithms work for 12+ holes?
3. **Hole size graduation** — Optimal size progression from reed to bell
4. **Cross-fingerings** — What patterns produce better chromatic tuning?

## Key Decisions
- **11mm holes on 25mm bore** — correct for bass clarinet proportions (S_hole/S_bore = 19%)
- **n_register=2 for 12th** — 3rd harmonic on closed-open pipe
- **Register at 80mm/2.5mm** — optimal from position/diameter scan
- **Bell deferred to OpenWind** — TMM may overestimate bell distortion
- **Global optimization needed** — sequential breaks for 12+ holes

## Next Steps
1. Research: submit 4 prompts to ChatGPT/Claude (TMM validation, chromatic optimization, hole sizes, fingerings)
2. Code: implement graduated hole sizes in optimizer
3. Code: add cross-fingering chart support
4. Code: try DE with fewer variables (optimize diameters AND positions)
5. Code: implement phase-based cost function (faster than peak-matching)
6. Push: git commit + LAN chat to laptop

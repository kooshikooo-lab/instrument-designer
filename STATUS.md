# Bass Clarinet Design Automation — Status

## Results Summary

| Configuration | Reg1 RMS | Reg2 RMS | Method |
|---|---|---|---|
| 7-hole diatonic, uniform 11mm | 6.19c | 9.51c | Two-register optimizer |
| 12-hole chromatic, sequential | 15.38c | 15.46c | Physics-limited, any hole size |
| 12-hole with cross-fingerings | 47.33c | 46.41c | Ad-hoc chart, needs proper design |

## Key Findings (Week of 2026-07-23)

**TMM model is correct.** tanner/untanner = normalized admittance in tangent form. -0.5 phase for open hole = R=-1 reflection. Valid deep in plane-wave regime (8kHz cutoff, 70Hz operating).

**Sequential chromatic is hard-limited.** 12 sequential fingerings on 1211mm bore can't achieve <15c RMS regardless of hole size (tested 8-20mm). The last note (D3) consistently has -300 to -350c error. This is a physics limit of the sequential fingering approach.

**Graduated diameters don't help sequential.** Optimal for 12 holes converges to ~10.5mm uniform (inverse of real clarinet graduation: slightly smaller at bell). The small (8mm) holes near reed hurt more than large (14mm) holes near bell help.

**Cross-fingerings are the only path forward.** Real clarinets achieve chromatic intonation through 150+ years of refined fingering patterns. We need a proper fingering chart before optimization can succeed.

## Research Prompts Created (Ready for ChatGPT/Claude)
1. `prompt_tmm_validation.md` — TMM model theory validation (already analyzed)
2. `prompt_chromatic_optimization.md` — Algorithms for chromatic optimization
3. `prompt_hole_sizes.md` — Graduated hole sizes from literature
4. `prompt_fingerings.md` — Cross-fingering design (basic)
5. `prompt_cross_fingerings.md` — Detailed cross-fingering chart for 12 holes (NEW)

## Next Steps
1. Submit `prompt_cross_fingerings.md` to ChatGPT for a proper fingering chart
2. Implement the chart once confirmed
3. Re-run 12-hole global optimizer with proper cross-fingerings
4. Add bore taper as optimization variable
5. Validate with OpenWind FEM

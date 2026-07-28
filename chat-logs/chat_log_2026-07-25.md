ede73b4 fix: naming consistency — contra-alto / contra-bass (hyphenated), octo-contra-bass (not octo-contrabass)
d3c2873 feat: Add professional low clarinets (contra-alto, contra-bass, octo-contra) + baritone saxes + mouthpieces
325a2ab Merge branch 'refactor/architecture-redesign' into experiment/cadquery-test
8ce7708 Merge remote-tracking branch 'origin/refactor/architecture-redesign' into refactor/architecture-redesign
a23a466 test: add test_module.py for CadQuery instrument generation
7eec5ba chore: add test output artifacts to .gitignore
339d02c test: CadQuery instrument generation, STL validation, test infrastructure
773316a feat: CadQuery export button, Tauri binary transport, UTF-8 fixes, tuning preset corrections
fcfdefe feat: CadQuery instrument library (55 instruments) + STL export endpoints
919dc5d feat: TMM acoustic engine improvements — reed tube, whistle clip, true_wavelength_near, coordinate convention fixes
a12264d fix: CadQuery test - fix imports and unicode encoding
81f2ae5 feat: CadQuery instrument CAD test - cylindrical, conical, parametric bores
6f4eef8 exp: add external solver wrappers for chalumier and OpenWind
5f9c1a7 feat: add Stage 1 optimizer with spacing and register vent constraints
fff63b6 exp: add trust-region regularization for Stage 3 optimization
1930da2 exp: add impedance-first solver design (ChatGPT recommendation)
56e2e23 feat: implement KeefeLoss plugin for viscothermal losses
5d0ad9e fix: register vent bug, speed of sound mismatch, optimizer result fields
66fceaf Merge branch 'refactor/architecture-redesign' of https://github.com/kooshikooo-lab/instrument-designer into refactor/architecture-redesign
96d3642 feat: add OpenWInD FEM solver with plugin interface
0064ab7 fix: coordinate system — position 0=bell (open end), position L=reed (closed end)
4405786 refactor: modular architecture redesign following ChatGPT recommendations
1ee0df1 BREAKTHROUGH: 4.3c RMS chromatic intonation with 12-hole sequential
dd133ac Cross-fingering optimization session: honest results, phase-cost analysis
0fb72ad chore: remove .git-rewrite from tracking, add to .gitignore
e06a629 feat: bass clarinet 12-hole tests + cross-fingering charts + bell-first validation
9f7c59f docs: session recovery log 2026-07-24 — tmm_acoustics.py merged to option-a-tauri, 7-hole validated 0.45c RMS
fe5a5c5 Merge branch 'option-a-tauri' of https://github.com/kooshikooo-lab/instrument-designer into experiment/trumpet-openwind
6f81716 Final state documentation
82c6e42 Bass clarinet chromatic optimization + baroque clarinet config

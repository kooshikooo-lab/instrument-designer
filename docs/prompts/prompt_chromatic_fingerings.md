# Bass Clarinet Chromatic Fingering Design for TMM Optimization

## Problem
Our SequentialBoreOptimizer (Bordeaux method) achieves 0.00c RMS for diatonic scales (6-8 holes) but fails for full chromatic (12+ holes) because cumulative closed-hole loading overwhelms the sequential placement. Holes 8-12 cluster at the bore end with errors of 200-600c.

We need a way to design chromatic clarinet fingerings that works with our TMM optimization framework.

## Current Working Model
- 7-hole D major diatonic: 0.00c RMS 1st reg, 7.96c 2nd reg, 9.5c twelfths
- 12.5mm bore radius, 1171mm length (uniform cylinder), 11mm tonehole diameter
- Register hole at 80mm, 2.5mm diameter
- Bordeaux method: sequential holes, each placed with all previous closed, new hole open
- Works for 7 holes but NOT for 12+ holes

## Key Questions

### Clarinet Fingering Systems
1. How does a real bass clarinet achieve a full chromatic scale? Describe the complete fingering system.
2. Are clarinet fingerings SIMPLY sequential (1 open, 2 open, 3 open...) or are they more complex?
3. How are cross-fingerings used (e.g., fork F/F#, throat Bb, side keys)?
4. What are the "ring key" mechanisms and how do they affect the acoustic model?
5. Do bass clarinets typically use plateau keys (covered holes) or ring keys (open holes)?

### Tonehole Design
1. What tonehole diameters are used for each hole on a bass clarinet? Does diameter decrease for higher holes?
2. Are undercut toneholes used? What's the typical undercut angle?
3. What is the ratio of tonehole diameter to bore diameter for each register?
4. How does the chimney height of toneholes vary along the instrument?

### Acoustic Modeling
1. How does one model cross-fingerings in a TTM framework? A cross-fingering leaves holes closed BEYOND an open hole — how does the TMM handle this?
2. What fingering system minimizes cumulative closed-hole loading? (e.g., "open all holes above the fingered note" vs "close all holes below")
3. Can the sequential hole placement be modified to place holes using HARMONIC or SEMITONE intervals rather than absolute positions?
4. How do real clarinet makers decide hole positions — is it empirical, physics-based, or both?

### Alternative Approaches
1. Simple system woodwinds (e.g., tin whistle, simple-system flute) use sequential open holes. Could this work for bass clarinet? What are the trade-offs?
2. Should we design a "simplified clarinet" with purely sequential fingerings first, then add complexity?
3. Are there published clarinet tonehole position tables we could adapt?

## Known Resources
- Benade (1976, 1990): Chapters on clarinet toneholes and register mechanisms
- Nederveen (1998): Tonehole acoustics, radiation, cross-fingerings
- Keefe (1982): Theory of the single woodwind tone hole (JASA 72(3))
- Debut, Kergomard, et al. (2005): Clarinet tonehole lattice optimization
- Szwarcberg (2025): Measured register hole on Buffet Crampon Festival soprano
- instrument-measurements.md: 700+ lines of measured bass clarinet dimensions

## Test Command
```bash
python backend/test_chromatic.py
```

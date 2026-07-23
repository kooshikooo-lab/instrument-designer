# Research: Clarinet Chromatic Fingering Systems
## Goal: Find/design a fingering chart that enables full chromatic play with ~12 toneholes

## Context
Our optimizer currently uses simple sequential fingerings (each note opens one more hole).
This works for diatonic scales but produces 15-20c errors for full chromatic.
Real clarinets use cross-fingerings, half-holing, register keys, and other mechanisms.

## The Sequential Fingering Problem
- 12 sequentially opening holes: last hole near bore end must produce highest note
- Early holes near reed don't change frequency enough (small Δf)
- Late holes near bell change frequency too much (large Δf)
- Result: non-uniform semitones

## Questions
1. What are the standard chromatic fingerings for a Boehm system clarinet?
2. How do cross-fingerings work acoustically (e.g., F/F# on clarinet)?
3. German vs French fingering systems: what are the tradeoffs?
4. What is the minimum number of holes needed for full chromatic range?
5. Can we design a fingering chart that is more "optimizer-friendly" (smooth frequency transitions)?
6. How do real clarinets handle the register break (throat tones)?
7. What is the role of the register key in chromatic playing?
8. Should we use forked fingerings (open-close-open patterns) for better tuning?

## References
- Backus, J. (1976). "The Acoustical Foundations of Music."
- Ridley, E.A.K. "The Clarinet: A Comprehensive Guide."
- Debut, V., Kergomard, J., & Laloë, F. (2005). "Analysis and optimization of the tuning of the toneholes of a clarinet." arXiv:physics/0309051.

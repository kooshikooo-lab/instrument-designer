# Research: Full-Chromatic Clarinet Optimization Algorithms
## Goal: Find/derive algorithms that can optimize 12-25 hole clarinets for full chromatic range

## Context
We have a working SequentialBoreOptimizer (Bordeaux-style) that gives 0.00c for 7-hole diatonic.
We have a GlobalFingeringOptimizer (DE + L-BFGS-B) that gives 15-20c RMS for 12-hole chromatic.
The global optimizer is 100x slower (16 min vs 10s) and still doesn't converge to 0.00c.

## The Problem
Sequential placement breaks for 12+ holes because:
- Cumulative closed-hole loading clusters holes at bore end
- Holes 8-12 within last 100mm
- 200-600c errors for last notes

Global optimization is slow because:
- 12 variables in DE = 576 evaluations × 13 TMM calls each
- 16+ minutes per run
- Still only finds 15-20c RMS

## Questions
1. How do the Bordeaux group (Debut, Kergomard, Dalmont) handle full chromatic optimization?
2. What algorithms are used in modern instrument design (Szwarcberg 2024-2025)?
3. Is there a hybrid approach: sequential for coarse placement + global for fine-tuning?
4. Can we use surrogate modeling (Gaussian process, neural network) to speed up evaluation?
5. What cost function works best for full chromatic: phase-based, peak-based, or perceptual?
6. Can we reduce the optimization to 2-4 "master variables" (bore profile parameters) instead of individual hole positions?
7. What is the role of cross-fingerings in chromatic optimziation?

## References
- Debut, V., Kergomard, J., & Laloë, F. (2005). "Analysis and optimization of the tuning of the toneholes of a clarinet." arXiv:physics/0309051.
- Szwarcberg, S. et al. (2024). "Designing toneholes of a clarinet using optimization." arXiv:2404.07540.
- Szwarcberg, S. et al. (2025). "Tonehole optimization of a clarinet using adjoint method." arXiv:2601.01981.
- Ernoult, A. (2020). "Phase-based cost function for woodwind optimization."
- Lefebvre, A. (2011). "Computational acoustic methods for the design of woodwind instruments."

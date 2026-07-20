# Noreland Clarinet & Woodwind Optimization Research

**Date:** 2026-07-20
**Goal:** Understand what the Noreland "logical clarinet" can teach us about bore optimization

---

## The Noreland Clarinet (2013) — Key Facts

**Paper:** "The logical clarinet: numerical optimization of the geometry of woodwind instruments"
**Authors:** D. Noreland, J. Kergomard, F. Laloë, C. Vergez, P. Guillemain, A. Guilloteau
**Published:** Acta Acustica united with Acustica, 99(4), 615–628 (2013)

### Method
- **Acoustic model:** 1D transmission line with visco-thermal losses (same as OpenWInD)
- **Optimization:** Gradient-based least-squares (finite-difference gradients) — NOT evolutionary
- **Design variables:** 58 total (19 tone holes × 2 params [position, radius] + chimney heights + bore sections)
- **Targets:** Resonance frequencies of input impedance peaks matched to equal-temperament chromatic scale
- **Strategy:** 3-step sequential optimization:
  1. Single-register first (18 notes, first register only)
  2. Add second register (18 notes × 2 registers)
  3. Fine-tune with amplitude ratios

### Results
| Configuration | Description | Fundamental RMS | 2nd Register RMS |
|---|---|---|---|
| (a) | No dedicated register hole | >5 cents | >10 cents |
| (c) | Dedicated register hole | **2.4 cents** | **3.8 cents** |
| (d) | Register hole + bore enlargement | **0.49 cents** | **2.4 cents** |
| (e) | Full second register optimization | Best | Best |

### Physical Prototype Results
- Built a fully chromatic clarinet from optimized design
- Tested with artificial blowing machine at 5.5 kPa
- Measured intonation: **~11 cents flat offset** (easily corrected by adjusting instrument length)
- After removing offset: **remaining errors <5 cents**
- Mean square deviation: 2.8–3.6 cents across two runs
- **"Better than what is usually obtained with real clarinets"**

### Key Design Insights
1. **Tone hole geometry varies regularly** over the instrument length (unlike conventional clarinets)
2. **Gradually larger tone holes toward the bell** (confirms conventional wisdom)
3. **Dedicated register hole is essential** — dual-function holes (register + tone) compromise intonation
4. **Bore enlargement helps** — non-cylindrical bore improves second register
5. **Optimized geometry is fundamentally different** from traditional instruments but produces superior intonation

---

## What We Can Learn From Noreland

### 1. Gradient-Based vs Evolutionary Optimization
- Noreland used **gradient-based** (L-BFGS-B or similar) with finite-difference gradients
- We use **NSGA-II evolutionary** (pymoo)
- **Trade-off:** Gradient methods converge faster (fewer evaluations) but get stuck in local minima. Evolutionary methods explore more broadly but need many more evaluations (~1.7s each with OpenWInD).
- **Lesson:** Our 1.7s/eval × 2000 evals = 58 min is comparable to what gradient methods would need for convergence. But gradient methods would need far fewer total evaluations.

### 2. Sequential Optimization Strategy
- Noreland's 3-step approach (single-register → dual-register → fine-tune) is critical
- **We don't do this.** We optimize all targets simultaneously from the start
- **Lesson:** Consider implementing staged optimization — start with fewer targets, use result as initial guess for full optimization

### 3. Resonance Definition Matters
- Ernoult (2020) showed that the traditional peak-finding approach creates **discontinuous cost functions** that hamper optimization
- Noreland used peak frequencies directly (with finite differences)
- Ernoult introduced **regularized unwrapped angle of reflection function** for smoother optimization
- **Lesson:** Our peak-finding + cents error approach may have discontinuities. Consider Ernoult's formulation for smoother optimization landscape.

### 4. What We Optimize vs What They Optimize
| Aspect | Noreland | Us (current) |
|--------|----------|--------------|
| Bore profile | Fixed cylindrical | Variable (12 control points) |
| Tone hole positions | Optimized (19 holes) | Not applicable (no tone holes) |
| Tone hole radii | Optimized | Not applicable |
| Chimney heights | Optimized | Not applicable |
| Objectives | Single (least-squares freq error) | 3 (freq + evenness + projection) |
| Constraints | Hole size bounds | None (monotonicity missing!) |

**Critical gap:** Noreland optimized tone hole geometry on a FIXED bore. We optimize the BORE itself (no tone holes). These are complementary problems. For a simple flute/whistle (no tone holes), bore optimization is the right approach. For clarinets with tone holes, Noreland's approach is more appropriate.

### 5. Accuracy Benchmark
- Noreland achieved **0.49 cents RMS** computationally (config d)
- Physical prototype achieved **<5 cents** after removing global offset
- **Our target should be:** <1 cent computational, <10 cents physical (accounting for manufacturing)

---

## Related Work: Ernoult et al. (2020)

**Paper:** "Woodwind instrument design optimization based on impedance characteristics with geometric constraints"
**Published:** JASA, 148(5), 2864–2877 (2020)
**Affiliation:** Inria/CNRS + **Buffet Crampon** (industrial partner)

### Key Advances Over Noreland
1. **New resonance definition** using regularized unwrapped angle of reflection function
   - Avoids discontinuous cost function from traditional peak-finding
   - Enables gradient-based optimization to work reliably
2. **Geometric constraints** from manufacturer requirements
   - Non-cylindrical bore profiles
   - Side holes with various radii and chimney heights
3. **Multi-fingered optimization** — simultaneously optimizes across all fingerings
4. **38 design variables** — demonstrates scalability

### Key Finding
- Traditional resonance definition leads to **non-smooth cost function** with parallel valleys
- Ernoult's regularized formulation creates **smoother landscape** for gradient methods
- **Valleys in design space** exist where moving along bore radius + chimney height directions creates parallel local minima

### Implication for Us
- Our NSGA-II evolutionary approach doesn't need smooth gradients
- But our **peak-finding may still miss peaks** or find wrong ones during optimization
- Consider implementing Ernoult's reflection-function-based approach as alternative objective

---

## Related Work: Lefebvre (2010, McGill PhD)

**Thesis:** "Computational Acoustic Methods for the Design of Woodwind Instruments"

### Key Contributions
- Used **L-BFGS-B** with finite-difference gradients
- Designed flute-like, clarinet-like, and saxophone-like instruments with 6-7 tone holes
- **Built physical prototypes** — validated the approach
- Found that tone hole interactions (not captured by TMM) create errors up to **10 cents**

### Key Finding
- TMM (Transmission Matrix Method) has inherent accuracy limit due to ignoring tone-hole interactions
- Error is **<10 cents** for typical instruments
- This is a **fundamental limit** of the acoustic model, not the optimization

---

## Actionable Lessons for Our Optimizer

### Immediate (No Code Changes)
1. **Noreland's 0.49 cents is achievable** — our target of <1 cent computational is realistic
2. **Physical prototype <5 cents** is achievable — our target of <10 cents physical is conservative
3. **Bore optimization alone (without tone holes) is valid** for simple instruments (flutes, whistles)

### Short-Term (Code Changes)
1. **Add monotonicity constraint** — Noreland's designs are always monotonically non-decreasing
2. **Consider staged optimization** — start with fewer targets, gradually add more
3. **Profile single evaluation** — at 1.7s, OpenWInD is the bottleneck. Consider:
   - Caching more aggressively
   - Using lower n_freqs for early generations
   - Switching to faster acoustic model for initial exploration

### Medium-Term (Architecture Changes)
1. **Consider gradient-based optimization** for final refinement
   - NSGA-II for global exploration → gradient descent for local refinement
   - Could reduce total evaluations by 10-100x
2. **Implement Ernoult's reflection-function approach** for smoother optimization
3. **Add tone hole optimization** for clarinet-like instruments (future)

### Long-Term (Research Directions)
1. **Hybrid bore + tone hole optimization** (combine Noreland + our approach)
2. **Multi-register optimization** (Noreland's 3-step strategy)
3. **Amplitude ratio optimization** (not just frequency matching)

---

*Compiled from: Noreland et al. (2013), Ernoult et al. (2020), Lefebvre (2010), Szwarcberg et al. (2025)*

# P0 Questions for Human Decision (2026-08-07)

Blocking Phase 0 P0 fixes. Need decisions before proceeding.

---

## 1. Impossible Outer Diameters in `benchmark_all.py`

**Context**: Architecture audit found impossible outer diameters in benchmark targets. Need correct wall thickness specification.

**Options**:
- A: Use standard clarinet wall thickness (~3-4mm)
- B: Derive from CT-scanned reference instruments
- C: Keep as-is and document as known limitation

**Recommendation**: Option A (standard 3.5mm) for now, refine with CT data later.

---

## 2. Missing Tone Holes in `build_bass_chalumeau_Bb()`

**Context**: `backend/modular_components.py:699` `build_bass_chalumeau_Bb()` has no tone holes, but `benchmark_all.py` expects 8-note fingering chart.

**Options**:
- A: Add 7-8 tone holes matching benchmark target (positions from chalumier scaling)
- B: Remove bass chalumeau from `benchmark_all.py` INSTRUMENTS dict
- C: Mark benchmark as "known broken" and skip

**Recommendation**: Option A — add holes. Desktop branch already has fix; laptop doesn't.

---

## 3. Two-Phase Optimizer Scope

**Context**: Two-phase optimizer is default `ACCURATE` strategy. Has register detection bug for bass instruments.

**Options**:
- A: **P0 bugs only** — fix register freeze, bore_length_bounds, hardcoded params; defer P1 import fixes
- B: **P0 + P1** — include the 45-file import fixes from PR #62 in same session
- C: **Full overhaul** — rewrite two-phase with proper register tracking per fingering

**Recommendation**: Option A — minimal P0 fixes only. PR #62 already merged handles imports.

---

## 4. Bass Chalumeau Merge Conflict

**Context**: Desktop branch has tone-hole fix in `build_bass_chalumeau_Bb()`; laptop branch doesn't. Naive merge would lose the fix.

**Action needed**: Before any laptop→desktop merge, manually diff `backend/modular_components.py` `build_bass_chalumeau_Bb()` to preserve tone holes.

**Options**:
- A: Desktop merges laptop, manually restores tone holes after
- B: Laptop merges desktop first (preferred — desktop has more recent fixes)
- C: Create dedicated merge branch, resolve conflict there

**Recommendation**: Option B — laptop merges `origin/opencode/main/desktop` → `opencode/main/laptop`, then opens PR to `opencode/main/desktop`.

---

## Decision Format

Reply in Discussion #23 with:
```
1. [A/B/C] - [brief reasoning if not A]
2. [A/B/C] - [brief reasoning if not A]
3. [A/B/C] - [brief reasoning if not A]
4. [A/B/C] - [brief reasoning if not B]
```

Or just "1A 2A 3A 4B" if agreeing with recommendations.
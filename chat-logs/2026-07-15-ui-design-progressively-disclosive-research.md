# UI Design Research: Progressive Disclosure for Beginner+Expert Interfaces
**Date:** 2026-07-15
**Researcher:** opencode (big-pickle)

## Overview

Research on UI design patterns that serve both non-technical beginners and power users, specifically for web-based instrument design tools. Core principle: **less customized, not less quality**.

---

## 1. PROGRESSIVE DISCLOSURE — The Core Pattern

### What It Is
Progressive disclosure is a UX technique that gradually reveals information and functionality as needed, reducing cognitive load on initial interaction while keeping advanced features accessible.

### Key Principles (from GitHub Primer, NN/g, commons-os)

1. **Maintain context** — don't disorient users when revealing/hiding info
2. **Layered complexity** — primary layer for most users, subsequent layers for experts
3. **Reduce cognitive load** — show only what's needed at any given time
4. **User control and reversibility** — users can always show/hide advanced options
5. **Clear signifiers** — use universally understood icons (chevrons, toggles, "Show Advanced")
6. **Limit layers** — one secondary screen is typically sufficient; don't bury functionality

### Our Application

**Current state:** DesignTab.tsx shows everything at once (preset selector, server connectivity, STL generation, STEP export, impedance plot, microphone analysis, parametric generator). This is overwhelming for beginners.

**Target state:**
- **Beginner mode (default):** Pick instrument → see preview → download STL. ~3 clicks.
- **Expert mode (toggle):** Full parametric control, impedance analysis, STEP export, custom bore profiles.

---

## 2. THE 4 TYPES OF PROGRESSIVE DISCLOSURE

### Type 1: Steering (Guided Path)
**Best for:** First-time users, linear workflows
**Pattern:** Wizard/step-by-step flow
**Example:** Setup wizards, onboarding flows

**Our app equivalent:**
```
Step 1: Pick instrument family (Flute, Woodwind, Brass)
Step 2: Pick specific instrument (Recorder in D, Folk Flute, etc.)
Step 3: See preview + print recommendations
Step 4: Download STL
```

### Type 2: Progressive Prevention (Guard Rails)
**Best for:** Preventing errors, enforcing constraints
**Pattern:** Disable invalid options, show warnings before destructive actions
**Example:** Greyed-out buttons, confirmation dialogs

**Our app equivalent:**
- Disable "Export STEP" when backend server isn't running
- Show "This requires the backend server" instead of silent failure
- Validate parameters before submission (bore length, wall thickness)

### Type 3: Front-loading (Simplified Default)
**Best for:** Most-used features, reducing choices
**Pattern:** Show essential options first, hide rest behind "More options"
**Example:** Google's simple search → Advanced search

**Our app equivalent:**
- Default to preset-based generation (no raw parameters shown)
- "Simple" tab shows: instrument picker + generate button
- "Advanced" tab shows: bore profile editor, tone hole placement, impedance settings

### Type 4: Delayed Disclosure (On-Demand)
**Best for:** Expert features, rarely-used tools
**Pattern:** Collapsible sections, "Show Expert Options" toggle
**Example:** Notion's database filters, Photoshop's tool options

**Our app equivalent:**
- Collapsible "Advanced Settings" section in DesignTab
- Impedance plot hidden by default, revealed by "Analyze Acoustics" button
- Parametric generator behind "Create Custom Instrument" link

---

## 3. UI PATTERNS FOR DUAL-MODE INTERFACES

### Pattern A: Mode Toggle
**Description:** Explicit switch between "Simple" and "Expert" modes
**Pros:** Clear mental model, user chooses their level
**Cons:** Two code paths to maintain, may confuse users who don't know which to pick
**Examples:** Figma (Simple/Advanced toggle), Ableton (Session/Arrangement view)

**Best for:** When the two modes have fundamentally different layouts

### Pattern B: Collapsible Sections (Recommended)
**Description:** Advanced options hidden behind expandable accordions
**Pros:** Single interface, user reveals what they need, familiar pattern
**Cons:** Can still look cluttered if too many sections
**Examples:** Google Advanced Search, GitHub repo settings, Notion databases

**Best for:** When advanced options are related to the same workflow

### Pattern C: Progressive Tabs
**Description:** Tabs that reveal more detail as user progresses
**Pros:** Natural workflow progression, keeps context
**Cons:** May hide important features behind later tabs
**Examples:** VS Code (Explorer → Search → Git → Debug), Chrome DevTools

**Best for:** When tasks are distinct but related

### Pattern D: Smart Defaults + Override
**Description:** Pre-fill everything with sensible defaults, allow overriding
**Pros:** Zero-config for beginners, full control for experts
**Cons:** Defaults must be good, overriding requires knowledge
**Examples:** Canva (templates + custom), VS Code (settings.json)

**Best for:** When most users want the same thing,少数 users want customization

---

## 4. SPECIFIC RECOMMENDATIONS FOR INSTRUMENT DESIGNER

### 4.1 Library Tab (Browser)
**Current:** Search + filters + instrument list + detail panel
**Improvement:**
- Keep as-is (already well-designed)
- Add "Featured Instruments" section at top (curated 5-6 popular picks)
- Add difficulty badges with color coding (already done)
- Add "Quick Generate" button directly on instrument cards (skip detail view)

### 4.2 Design Tab (Major Redesign Needed)
**Current:** 324-line monolith with 12+ state variables
**Recommended layout:**

```
┌─────────────────────────────────────────────────┐
│  [Instrument: Recorder in D ▼]  [Generate STL]  │  ← Simple mode (always visible)
├─────────────────────────────────────────────────┤
│  ▶ Advanced Options                              │  ← Collapsible section
│  ┌─────────────────────────────────────────────┐│
│  │ Server URL: [http://localhost:8000    ]     ││
│  │ Transpose: [0] semitones                    ││
│  │ Wall Thickness: [2.0] mm                    ││
│  └─────────────────────────────────────────────┘│
├─────────────────────────────────────────────────┤
│  ▶ Acoustic Analysis                            │  ← Collapsible section
│  ┌─────────────────────────────────────────────┐│
│  │ [Impedance Plot]  [Microphone Analyzer]     ││
│  │ [Predicted vs Measured]                     ││
│  └─────────────────────────────────────────────┘│
├─────────────────────────────────────────────────┤
│  ▶ Custom Instrument Generator                  │  ← Collapsible section
│  ┌─────────────────────────────────────────────┐│
│  │ [Parametric Bore Editor]                    ││
│  │ [JSCAD Generator]                           ││
│  └─────────────────────────────────────────────┘│
├─────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────┐│
│  │           [3D STL Viewer]                    ││  ← Always visible after generation
│  │                                              ││
│  └─────────────────────────────────────────────┘│
└─────────────────────────────────────────────────┘
```

### 4.3 Error Handling for Humans
**Current:** Raw error messages ("Connection refused", "OpenWInD computation failed")
**Recommended:**

| Current Message | Better Message |
|----------------|----------------|
| "Connection refused" | "Can't reach the design server. Make sure it's running on port 8000. [How to start the server →]" |
| "OpenWInD computation failed" | "Acoustic simulation failed. Check that the bore profile is valid. [Troubleshooting →]" |
| "STL generation failed" | " Couldn't generate the 3D model. Try a different preset or check the server logs. [Help →]" |
| "Job not found" | "This design job has expired. Please generate a new one." |

### 4.4 Print Settings Helper
**After STL download, show:**
```
Print Settings for Recorder in D:
├ Material: PLA or PLA+ (recommended)
├ Layer Height: 0.12mm (for smooth bore)
├ Infill: 100% (solid for best tone)
├ Walls: 4+ loops
├ Supports: None needed
├ Print Time: ~2 hours
├ Assembly: Glue 3 segments with superglue
└ Tools Needed: Sandpaper (220 grit), electronic tuner
```

### 4.5 Guided Workflow (Steering Pattern)
**For complete beginners, offer a "Start Here" path:**
1. "What instrument do you want to make?" → Visual card picker
2. "What's your skill level?" → Beginner / Intermediate / Expert
3. "Do you have a 3D printer?" → Yes / No (links to print services)
4. Show personalized result with step-by-step build guide

### 4.6 Tooltip Strategy
**Every technical parameter should have a plain-language tooltip:**
- "Bore Diameter" → "The width of the hollow inside of the instrument. Wider = deeper sound."
- "Wall Thickness" → "How thick the instrument walls are. Thicker = stronger but heavier."
- "Transpose" → "Shift the pitch up or down by semitones. Leave at 0 for standard tuning."
- "Impedance" → "A measure of how well the instrument resonates at each frequency. Peaks = notes it plays well."

---

## 5. COMPARABLE APPLICATIONS STUDIED

### Notion
- Starts with simple table view
- Advanced filters/sorts hidden behind menus
- Power users can add formulas, relations, rollups
- **Lesson:** Simple defaults + progressive complexity works

### Google Search
- One text box = extreme simplicity
- Advanced search hidden at google.com/advanced_search
- **Lesson:** The most complex features can be completely hidden

### Ableton Live
- Session view (simple, loop-based) vs Arrangement view (complex, timeline)
- Toggle between modes with Tab key
- **Lesson:** Two distinct modes can coexist with a simple switch

### Figma
- Simple mode: drag-and-drop, basic shapes
- Advanced: component variants, auto-layout, variables
- Community plugins extend functionality
- **Lesson:** Core experience is simple, extensibility is opt-in

### Tinkercad vs Fusion 360
- Tinkercad: Simple browser-based 3D modeling for beginners
- Fusion 360: Full parametric CAD for professionals
- Both made by Autodesk
- **Lesson:** Sometimes separate tools are better than one tool with modes

### Bambu Studio / PrusaSlicer
- Simple view: material, quality, support toggles
- Advanced view: hundreds of parameters
- Toggle between Simple/Advanced/Custom modes
- **Lesson:** slicer-style mode switching is well-understood by 3D printing community

---

## 6. IMPLEMENTATION PRIORITIES

### Phase 1: Quick Wins (1-2 days)
1. ✅ Add collapsible sections to DesignTab (Advanced Options, Acoustic Analysis, Custom Generator)
2. ✅ Fix error messages to be human-readable
3. ✅ Add tooltips to all parameters
4. ✅ Wire the server URL input to actually work

### Phase 2: Guided Experience (3-5 days)
1. "Start Here" guided workflow for beginners
2. Print settings recommendations after download
3. "Featured Instruments" section in library
4. Quick Generate button on instrument cards

### Phase 3: Expert Power Features (1 week)
1. Custom bore profile editor (CSV upload or visual editor)
2. Impedance measurement import (microphone → comparison)
3. Batch generation (multiple instruments at once)
4. Preset sharing (community-contributed presets)

---

## 7. KEY TAKEAWAYS

1. **Progressive disclosure is the right pattern** — not separate modes, not separate apps
2. **Collapsible sections** are the simplest implementation with highest impact
3. **Smart defaults** eliminate 90% of configuration for beginners
4. **Tooltips** bridge the knowledge gap without cluttering the interface
5. **Error messages** are part of UX — "for humans" means explaining what to do, not what went wrong
6. **Print settings** are a huge untapped opportunity — most beginners don't know what infill means
7. **The library tab is already good** — focus improvements on DesignTab
8. **Don't hide quality behind complexity** — the preset-based path must produce identical output to the manual path

---

## Sources

- [GitHub Primer — Progressive Disclosure](https://primer.github.io/design/ui-patterns/progressive-disclosure)
- [commons-os — Progressive Disclosure Patterns](https://commons-os.github.io/patterns/progressive-disclosure)
- [NN/g — Design Pattern Guidelines](https://www.nngroup.com/articles/design-pattern-guidelines/)
- [Interaction Design Foundation — Progressive Disclosure](https://ixdf.org/literature/topics/progressive-disclosure)
- [LogRocket — Progressive Disclosure Types and Use Cases](https://blog.logrocket.com/ux-design/progressive-disclosure-ux-types-use-cases/)
- [UI-Patterns.com — Progressive Disclosure](https://ui-patterns.com/patterns/ProgressiveDisclosure)
- [Lollypop Design — Progressive Disclosure in SaaS](https://lollypop.design/blog/2025/may/progressive-disclosure/)
- [Medium — Progressive Disclosure Key Patterns](https://medium.com/@dinu8220001/progressive-disclosure-in-ux-ui-design-key-patterns-and-examples-2b858bc24d9c)
- [Medium — LLM App Progressive Disclosure](https://medium.com/@dtianshan7/principles-for-building-user-friendly-llm-applications-progressive-disclosure-as-a-core-design-6e182b61b14c)
- [ResearchGate — 3D Printer Software Interface for Home Users](https://www.researchgate.net/publication/334717939)

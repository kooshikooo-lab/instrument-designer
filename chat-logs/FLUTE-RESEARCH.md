# Flute & Overtone Flute Research
## experiment/flute-pvc branch — Desktop Session 9 (2026-07-21)

---

## Why Flutes First

Flutes are the **simplest wind instruments** to validate our algorithms:

1. **Cylindrical bore** — just a tube, no complex profile to optimize
2. **All harmonics** (open-open pipe) — simpler than clarinet's odd-only
3. **OpenWInD can simulate them** — 1D FEM handles cylinders perfectly
4. **PVC pipe** — standardized dimensions, no woodworking needed
5. **Known reference designs** — Flutomat, demakein, UNSW measurements
6. **Large maker community** — easy to get physical validation
7. **Overtone flutes** — even simpler, no tone holes at all

---

## Acoustic Classification

### Open-Open Pipes (Flutes)
- **All harmonics**: f, 2f, 3f, 4f, 5f...
- Overblows at octave (2nd harmonic)
- Operates at **impedance minima** (low pressure, high flow)
- Embouchure hole acts as open end

### Closed-Open Pipes (Clarinets, Duduk)
- **Odd harmonics only**: f, 3f, 5f, 7f...
- Overblows at twelfth (3rd harmonic)
- Operates at **impedance maxima** (high pressure, low flow)
- Reed acts as pressure node (nearly closed end)

### Closed Tubes (Pan pipes, Overtone flutes)
- **Odd harmonics dominant**: f, 3f, 5f, 7f...
- Even harmonics appear with offset embouchure
- No overblowing mechanism needed — player controls register

### Vessel Flutes (Ocarina, Xun)
- **Fundamental dominant** — weak overtones
- Helmholtz resonator: f = (c/2π)√(S/VL)
- All-holes-open principle

---

## PVC Pipe Dimensions (Schedule 40)

| Nominal | ID (mm) | OD (mm) | Wall (mm) | Best For |
|---------|---------|---------|-----------|----------|
| 1/2" | 15.8 | 21.3 | 2.8 | High flutes (D, Eb) |
| **3/4"** | **20.9** | **26.7** | **2.9** | **D, C, Bb flutes (sweet spot)** |
| 1" | 26.1 | 33.4 | 3.4 | Low flutes (Bb, A) |
| 1-1/4" | 34.5 | 42.2 | 3.6 | Very low (G, F) |

**Key ratio**: Bore:length ≈ 1:21 for good tone quality.

---

## Overtone Flutes (No Tone Holes)

The simplest wind instruments — different notes come from overblowing the harmonic series.

### Seljeflöyte (Norwegian Willow Flute)
- **Material**: Willow bark (selje = willow)
- **Construction**: Strip bark from branch, re-insert as tube, seal with wax
- **Bore**: ~16-20mm ID
- **Length**: 40-80cm depending on key
- **Notes**: Harmonic series of closed tube (odd harmonics dominant)
- **Playing**: Overblow to change register, half-hole for even harmonics
- **Key resource**: https://www.blasemaker.no/en/ressursar/tools/overtone-flute-calculator/

### Koncovka (Slovak Overtone Flute)
- **Bore**: 16mm typical
- **Length by key**: G=86cm, A=72cm, C=63cm, D=58cm, E=54cm, F=48cm
- **Scale**: Lydian (sharp 4th) or Mixolydian (flat 7th)
- **Key resource**: https://fujara.sk/instruments/folkart_slovakia/shepherd_pipes/overtone_flute.htm

### Fujara (Slovak Giant Overtone Flute)
- **Length**: 160-200cm (5-6.5 feet!)
- **Bore**: ~20mm
- **Notes**: 3 finger holes + overtone series
- **UNESCO heritage**: Since 2008
- **3D printable**: https://github.com/tonykoop/fujara

### Pitkähuilu (Finnish Long Flute)
- **Similar to koncovka/fujara**
- **Resource**: https://overtoneflute.fi/

### Kalyuka (Russian Overtone Flute)
- **Resource**: https://organology.net/instrument/kalyuka/

### Tilinca (Romanian Overtone Flute)
- **Resource**: https://eliznik.org.uk/traditions-in-romania/traditional-music/pipes/

---

## Membrane Flutes

### Chinese Dizi (笛子)
- **Membrane (dimo 膜)**: Reed/bamboo inner membrane, glued over a hole
- **Effect**: Vibrates with acoustic pressure, adds bright buzzing quality
- **Acoustics**: Shifts resonances 20-70 cents, creates odd-harmonic predominance
- **Types**: Bangdi (high), Qudi (low), Xindi (chromatic 11-hole)
- **Academic**: Tsai 2003/2004, Luan et al. 2022/2025, Ng et al. 2021

### Korean Daegeum (대금)
- **Membrane**: Reed epidermis, similar to dizi
- **80cm bore, 6 finger holes**

### Bawu (巴乌)
- **Free reed + closed cylindrical pipe**
- **Acoustics**: Reed pulls pitch above natural frequency
- **Clarinet-like tone** in upper range

### Hulusi (葫芦丝)
- **Gourd windchest + multiple pipes (melody + drones)**
- **Free reed excitation**

---

## The Duduk Family

### Armenian Duduk (დუდუკი)
- **Double reed + cylindrical bore** (oboe reed + clarinet bore = unique!)
- **Key finding** (Maugeais & Dalmont 2024): Low reed resonance frequency creates "dark, velvety timbre"
- **Bore**: ~15mm ID, 28-41cm long
- **10 holes** (8 front + 2 back), range ~1 octave + 4th
- **3D printed**: https://www.thingiverse.com/thing:4601952

### Related: Balaban (Azerbaijani), Mey (Turkish), Guanzi (Chinese), Hichiriki (Japanese), Piri (Korean)

---

## Ancient Instruments

### Aulos (Greek)
- **Cylindrical bore + double reed** (like duduk!)
- **Reconstruction**: Hagel 2023, Bellia 2018
- **3D printed**: Bellia's virtual reconstruction

### Bone Flutes (oldest instruments)
- **Divje Babe** (~60,000 years): Cave bear femur, 4 holes, 3.5 octave range
- **Hohle Fels** (~40,000+ years): Vulture radius, 5 holes
- **3D printed replica**: https://mattgilbert.net/projects/divje_babe_bone_flute/

### Pan Pipes (Syrinx)
- **Closed tubes** — simplest possible wind instrument
- **Odd harmonics dominant** (even harmonics appear with offset embouchure)
- **3D printed**: https://www.printables.com/model/439762-daphnis-a-3d-printable-pan-flute-v10

---

## Software Tools Summary

| Tool | Type | Language | Key Feature | URL |
|------|------|----------|-------------|-----|
| **OpenWInD** | Acoustic sim | Python | 1D FEM, gold standard | openwind.inria.fr |
| **Demakein** | Design+Make | Python | Full pipeline, STL output | github.com/pfh/demakein |
| **Chalumier** | Design+Make | Kotlin | Faster demakein | github.com/MarkChuCarroll/chalumier |
| **WIDesigner** | Design+Optimize | Java | TMM + BOBYQA/DIRECT | github.com/edwardkort/WWIDesigner |
| **Flutomat NG** | Calculator | JS | Quick hole placement | unityrobot.github.io/Flutomat |
| **DidgeLab** | Inverse design | Python | Didgeridoo optimization | didgitaldoo.github.io/didgelab |
| **Printone** | CAD+Sim | C++ | Interactive BEM | doi.org/10.1145/2980179.2980250 |
| **Flutes.jl** | Parametric CAD | Julia+OpenSCAD | Shrink compensation | github.com/arizonahanson/Flutes.jl |
| **Build123d** | Parametric CAD | Python | Revolution/loft bodies | build123d.readthedocs.io |

---

## Key Acoustic Formulas

### Open Pipe (Flute)
```
L = c / (2f) - end_corrections
c = 331.3 + 0.606 * T  (speed of sound, m/s)
end_correction = 0.6 * r (each end)
```

### Closed Pipe (Clarinet, Overtone Flute)
```
L = c / (4f) - end_corrections
end_correction = 0.6 * r (open end only)
```

### Tone Hole Placement (Flute)
```
distance_from_embouchure = c / (2 * f_hole) - embouchure_correction - end_correction
embouchure_correction ≈ 50mm (concert flute)
tone_hole_correction ≈ 0.4 * bore_radius
```

### Overtone Series (Closed Pipe)
```
f_n = n * c / (4L)  where n = 1, 3, 5, 7, 9, 11, 13...
(accessible harmonics depend on blowing technique)
```

---

*Created: 2026-07-21 (Desktop Session 9)*
*Status: Research complete, building tools*

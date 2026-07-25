# Instrument Library

## Overview

91 instruments across 10 families. All with verified bore profiles and fingering charts.

## Families

| Family | Count | Acoustic Type | Examples |
|--------|-------|---------------|---------|
| Flutes | 8 | open-open | Concert, alto, PVC, bass, piccolo, baroque, bansuri, shakuhachi |
| Clarinets | 12 | closed-open | Bb, bass, contra-alto (EEb), contra-bass (BBb), octo-contra (EEEb/BBBb), basset |
| Saxophones | 12 | open-open | Soprano, alto, tenor, baritone, bass, sopranino, C melody, straight |
| Whistles | 6 | open-open | Tin (D/G), penny, low, fife, slide |
| Chalumeaux | 8 | closed-open | Diatonic (C/Bb), bass, 7-hole, 12-hole, keyless |
| Recorders | 8 | open-open | Soprano, alto, tenor, bass, great bass, sopranino, garklein |
| Ocarinas | 6 | open-open | 4-hole, 6-hole, 12-hole, transverse, pendant, bass |
| Brass | 8 | open-open | Trumpet, cornet, flugelhorn, trombone, horn, tuba, cornetto, serpent |
| Membrane | 5 | closed-open | Diplica, sipsi, zummara, membrane clarinet, duduk |
| Mouthpieces | 18 | varies | Bass/contrabass clarinet, baritone/bass sax, alto/tenor sax, trumpet, trombone |

## Naming Convention

- **Hyphenated:** contra-alto, contra-bass, octo-contra-bass (all lowercase)
- **Transposition:** instrument key noted (e.g., "Soprano Sax Bb")
- **Professional models:** brand names included (e.g., "Selmer Mark VI Baritone Sax")
- **Consistency locked:** contra-alto, contra-bass, octo-contra-bass (not contrabass, not contra alto)

## Benchmark Results (Absolute RMS)

| Instrument | Type | RMS (c) | Time |
|-----------|------|---------|------|
| Chalumeau C | closed-open | 0.00 | 4.8s |
| Bass Chalumeau Bb | closed-open | 0.00 | 14.3s |
| Soprano Sax Bb | open-open | 0.03 | 93.9s |
| Xaphoon C | open-open | 0.00 | 10.7s |
| Alto Sax Eb | open-open | 0.15 | 106.2s |
| Tin Whistle D | open-open | 0.91 | 101.6s |
| Concert Flute C | open-open | 0.00 | — |
| Alto Flute G | open-open | 0.00 | — |
| PVC Flute D | open-open | 0.00 | — |
| Recorder C | open-open | 0.00 | 178.6s |

## Adding Instruments

Each instrument requires:
1. **Bore profile** — radius array (mm)
2. **Fingering chart** — list of hole states per note
3. **Target frequencies** — equal temperament for the instrument's key
4. **Acoustic type** — open-open or closed-open
5. **Bore radius** — initial estimate for optimizer

See `backend/cadquery_export.py` for implementation.

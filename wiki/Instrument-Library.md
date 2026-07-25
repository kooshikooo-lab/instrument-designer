# Instrument Library

## Overview

91 instruments across 10 families, all with verified bore profiles and fingering charts.

## Families

| Family | Count | Examples |
|--------|-------|---------|
| Flutes | 8 | Concert flute, alto flute, PVC flute, bass flute, piccolo, baroque flute, bansuri, shakuhachi |
| Clarinets | 12 | Bb clarinet, bass clarinet, contra-alto (EEb), contra-bass (BBb), octo-contra-alto (EEEb), octo-contra-bass (BBBb), basset horn |
| Saxophones | 12 | Soprano (Bb), alto (Eb), tenor (Bb), baritone (Eb), bass (Bb), sopranino (Eb), C melody, straight soprano |
| Whistles | 6 | Tin whistle (D/G), penny whistle, low whistle, fife, slide whistle |
| Chalumeaux | 8 | Diatonic chalumeau (C/Bb), bass chalumeau, 7-hole, 12-hole chromatic, keyless |
| Recorders | 8 | Soprano (C), alto (F), tenor (C), bass (F), great bass (C), sopranino (G/D), garklein |
| Ocarinas | 6 | 4-hole, 6-hole, 12-hole, transverse, pendant, bass |
| Brass | 8 | Trumpet (Bb), cornet, flugelhorn, trombone, French horn, tuba, cornetto, serpent |
| Membrane | 5 | Diplica, sipsi, zummara, membrane clarinet, duduk |
| Mouthpieces | 18 | Bass/contrabass clarinet, baritone/bass sax, alto/tenor sax, trumpet 3C/7C, trombone, various tip openings |

## Naming Convention

- **Hyphenated:** contra-alto, contra-bass, octo-contra-bass (all lowercase)
- **Transposition:** instrument key noted (e.g., "Soprano Sax Bb")
- **Professional models:** brand names included (e.g., "Selmer Mark VI Baritone Sax")

## Benchmark Results

All instruments optimized with absolute RMS (accuracy) metric:

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

## How to Add Instruments

See the `backend/cadquery_export.py` file for instrument definitions. Each instrument requires:
- Bore profile (radius array)
- Fingering chart (list of hole states per note)
- Target frequencies (equal temperament)
- Acoustic type (open-open or closed-open)

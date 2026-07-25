# Instrument Designer

An open-source computational tool for designing 3D-printable woodwind instruments with sub-cent intonation accuracy.

## What Is This?

Instrument Designer optimizes bore profiles and tone hole placements for woodwind instruments using the Transfer Matrix Method (TMM). It produces playable instruments that match equal temperament within computational error.

## Quick Start

1. **Install** — See [[Getting-Started]]
2. **Browse instruments** — [[Instrument-Library]] (91 instruments, 10 families)
3. **Design** — Run the optimizer on a preset or custom configuration
4. **Print** — Export STL and print with SLA resin (see [[3D-Printing-Guide]])

## Features

- **TMM acoustic engine** with viscothermal losses (Keefe 1984)
- **Multi-stage optimizer** (DE → L-BFGS-B → Nelder-Mead)
- **91 instruments** across 10 families (flutes, clarinets, saxophones, whistles, recorders, chalumeaux, ocarinas, brass, membrane, mouthpieces)
- **3D STL export** via CadQuery (build123d)
- **Tauri desktop app** with Three.js visualization
- **AI-assisted design** via OpenRouter integration

## Links

- [[Getting-Started]] — Installation and first design
- [[Instrument-Library]] — All 91 instruments
- [[3D-Printing-Guide]] — Print settings and materials
- [[FAQ]] — Common questions
- [[Internal:Home]] — Developer documentation (internal)

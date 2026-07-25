# Branch: experiment/trumpet-openwind

> Trumpet model using OpenWind FEM. Side branch, not needed on laptop.

## Purpose

Trumpet bore optimization using OpenWind's 1D FEM with visco-thermal losses. Models valves as deviation pipes with proper junction physics.

## What It Has

| Feature | Status |
|---------|--------|
| OpenWind trumpet model | ✅ |
| Valve combinations | ✅ |
| Bore tuning | ✅ |
| Leadpipe optimization | ✅ |
| 34 unique commits | ✅ |

## What It Doesn't Have

| Feature | Reason |
|---------|--------|
| Woodwind instruments | Different acoustic model |
| TMM engine | Uses FEM instead |
| Optimizer integration | Standalone model |

## Status

All content is merged into laptop. This branch is kept as a reference for trumpet-specific work.

## When to Use

- When working on brass instruments specifically
- When OpenWind FEM validation is needed
- When trumpet bore optimization is required

## Related

- `ROADMAP-Trumpet.md` — Trumpet-specific roadmap
- OpenWind FEM approach vs TMM approach comparison

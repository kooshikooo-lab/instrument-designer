# Branch: main

> Stable shared branch. Integration target for all work.

## Purpose

The `main` branch is the stable integration point. It should contain only tested, working code that both machines (laptop and desktop) can rely on.

## Current State

- Laptop is 77 commits ahead of main
- Main has the original Python + PySide6 codebase
- Main does NOT have KeefeLoss, two-phase optimizer, 91 instruments, or absolute RMS metric

## What main Has

| Feature | Status |
|---------|--------|
| Original TMM engine | ✅ |
| Basic optimizer (sequential + DE) | ✅ |
| 55 instruments | ✅ |
| Web UI (React + Three.js) | ✅ |
| FastAPI server | ✅ |
| PySide6 desktop GUI | ✅ |

## What main Doesn't Have

| Feature | Branch |
|---------|--------|
| KeefeLoss | laptop |
| Two-phase optimizer | laptop |
| 91 instruments | laptop |
| Absolute RMS metric | laptop |
| Tauri sidecar | laptop |
| AI assistant | option-a-tauri |
| Architecture redesign | laptop (synced) |

## Merge Plan

After laptop merges its pending branches:
1. Laptop merges `laptop` → `main`
2. Desktop pulls `main`
3. Both machines now have KeefeLoss, correct metrics, 91 instruments

## Guidelines

- Never force-push to main
- All changes go through feature branches
- Test before merging
- Coordinate merges between laptop and desktop via GitHub issues

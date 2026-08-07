# A.I Prompt Answers

Central archive of AI-generated answers to the project's research/design prompts,
organized **by topic** (physically in subfolders). Every file here is a **copy** —
originals remain in `chat-logs/` and `docs/prompts/`.

## Importance legend

- **[IMPORTANT]** — high-value, verified, or decision-driving content (see `IMPORTANT/`).
- Prompts live in a `prompts/` subfolder next to their answers.

## Structure

```
ai-prompt-answers/
├── IMPORTANT/
│   ├── critical-insights-and-advice/      — ChatGPT architecture recs, maker compromises, benchmark audit
│   └── important-and-verified-research/   — RESEARCH-REPORT, deep research, comprehensive deep-dive
├── acoustics-tmm/                         — TMM physics, chalumier, OpenWInD, Keefe losses, + prompts
├── instrument-design/                     — clarinet/chalumeau/saxophone/flute designs, + prompts
├── optimization/                          — optimizer benchmarking, convergence, tone-hole results
├── ai-ml-tools/                           — AI agents, CrewAI/pymoo, free AI coding, API options, + prompts
├── cad-3d-printing/                       — build123d, Fusion 360, 3D scans, 3D-printed instruments
├── sound-and-analysis/                    — sound samples, intonation accuracy
├── metamaterials/                         — acoustic metamaterial implementation research
├── deployment-infra/                      — Linux/WSL deployment, compute needs, Tailscale
├── references/                            — academic references & textbooks
├── research-reports/                      — deep-research findings, comprehensive reports, + prompts
└── branch-audits/                         — branch/merge audits (incl. Cursor three-branch audit 2026-08-07)
```

## Index by topic

### IMPORTANT
| File | Why |
|------|-----|
| `IMPORTANT/critical-insights-and-advice/chatgpt-architecture-recommendations.md` | ChatGPT's five-layer architecture + AcousticNetwork data model + research priorities |
| `IMPORTANT/critical-insights-and-advice/2026-07-25-instrument-maker-compromises.md` | How pro makers trade intonation/timbre/playability |
| `IMPORTANT/critical-insights-and-advice/2026-07-25-benchmark-audit.md` | Sub-0.1c RMS results are misleading — model-truth only |
### important-and-verified-research
| File | Why |
|------|-----|
| `RESEARCH-REPORT.md` (+ `.pdf`) | Full research report: TMM + OpenWInD bore optimization |
| `2026-07-21-deep-research-findings.md` | Deep research findings, desktop session 7 |
| `2026-07-22-comprehensive-research-deep-dive.md` | Modeling software + CAD + physics-AI deep dive |

### critical-insights-and-advice
| File | Why |
|------|-----|
| `chatgpt-architecture-recommendations.md` | ChatGPT's five-layer architecture + AcousticNetwork data model + research priorities |
| `2026-07-25-instrument-maker-compromises.md` | How pro makers trade intonation/timbre/playability |
| `2026-07-25-benchmark-audit.md` | Sub-0.1c RMS results are misleading — model-truth only |

### acoustics-tmm
| Answer | Prompt |
|--------|--------|
| `acoustic-simulation-evaluation.md` | `prompts/prompt_acoustics_research.md` |
| `chalumier-research.md` | — |
| `noreland-research.md` | — |
| `differentiable-acoustics-deep-dive.md` | — |
| `jax-tmm-implementation.md` | `prompts/prompt_tmm_validation.md` |
| `tmm-integration-session.md` | — |
| `tone-hole-optimization-results.md` | — |
| — | `prompts/prompt_trumpet_fundamental.md` |

> Data artifact `chat-logs/tmm-6target-result.json` not archived here (JSON not allowed in `docs/`).

### instrument-design
| Answer | Prompt |
|--------|--------|
| `clarinet-expansion-and-resources.md` | `prompts/prompt_bass_clarinet_dimensions.md`, `prompts/prompt_bass_clarinet_register.md` |
| `instrument-expansion.md` | — |
| `saxophone-research.md` | — |
| `FLUTE-RESEARCH.md` | — |
| `first-instrument-candidate.md` | — |
| `problems-report.md` | `prompts/prompt_fingerings.md`, `prompts/prompt_hole_sizes.md`, `prompts/prompt_cross_fingerings.md`, `prompts/prompt_chromatic_fingerings.md`, `prompts/prompt_chromatic_optimization.md`, `prompts/prompt_bell_and_chromatic.md`, `prompts/prompt_bell_distortion.md`, `prompts/research_prompts_chalumeau.md` |

> Data artifact `chat-logs/flute-calculations.json` not archived here (JSON not allowed in `docs/`).

### optimization
| Answer | Prompt |
|--------|--------|
| `optimizer-benchmark-and-modular-design.md` | — |
| `optimizer-convergence-fix.md` | — |

### ai-ml-tools
| Answer | Prompt |
|--------|--------|
| `ai-agents-for-instrument-design.md` | — |
| `ai-electromechanical-instrument-design.md` | — |
| `ai-instrument-design-real-examples.md` | — |
| `ai-novel-instrument-design-research.md` | — |
| `crewai-pymoo-deep-dive.md` | — |
| `hybrid-compute-and-ai-instrument-design.md` | — |
| `ai-tools-research.md` | — |
| `free-ai-coding-research.md` | — |
| `ai-assistant-setup.md` | — |
| `api-integration-research.md` | — |
| `laptop-to-desktop.md` | `prompts/claude_prompt.md` |

### cad-3d-printing
| Answer | Prompt |
|--------|--------|
| `build123d-mcp-deep-dive.md` | — |
| `3d-instrument-scans-research.md` | — |
| `fusion-personal-use-research.md` | — |

### sound-and-analysis
| Answer | Prompt |
|--------|--------|
| `instrument-sound-samples-research.md` | — |
| `intonation-accuracy-research.md` | — |

### metamaterials
| Answer | Prompt |
|--------|--------|
| `metamaterial-implementation-research.md` | — |

### deployment-infra
| Answer | Prompt |
|--------|--------|
| `linux-deployment-research.md` | — |
| `wsl2-setup-attempt.md` | — |
| `compute-analysis.md` | — |
| `tailscale-research.md` | — |

### references
| Answer | Prompt |
|--------|--------|
| `research-references.md` | — |

### research-reports
| Answer | Prompt |
|--------|--------|
| `deep-research-findings.md` | `prompts/prompt_project_review.md` |
| `comprehensive-research-deep-dive.md` | `prompts/research_prompts.md` |
| `FULL-REPORT.md` | — |
| `RESEARCH-REPORT.md` (+ `.pdf`) | — |

### branch-audits
| File | Why |
|------|-----|
| `2026-08-07-cursor-three-branch-audit.md` | Cursor agent's audit of main / desktop / laptop branches + recommended merge sequence |

## Maintenance

- Add new AI answers as copies into the matching topic folder; update this index.
- Keep `IMPORTANT/` for content that is verified, decision-driving, or critical advice.
- Originals are authoritative; this archive is for quick reference by topic.

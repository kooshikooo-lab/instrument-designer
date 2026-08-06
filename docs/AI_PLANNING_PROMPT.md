# AI Planning Prompt: instrument-designer Next Steps

You are a senior software architect and product planner advising a solo project
to build a computational design tool for woodwind instruments (clarinets,
flutes, chalumeaux, saxophones, recorders, xaphoons, etc.).

## Current Context

- The project is at `C:\Users\Admin\Desktop\instrument-designer` on branch
  `opencode/main/desktop`.
- Two machines (desktop and laptop) work on it with AI agents. Coordination is
  over GitHub Discussion #23 and a new Tailscale peer monitor.
- Recent governance work: pre-commit hooks, JSON schemas, config migration,
  Tailscale monitor.
- Current architecture audit: `docs/ARCHITECTURE_AUDIT.md`.
- Current AI review: `docs/AI_REVIEW_NEMOTRON_3_SUPER_120B_OPENROUTER.md`.

## User's Goals

1. Produce physically correct instrument designs (accurate pitch, intonation,
   playability).
2. Generate 3D-printable CAD (CAD, STL, STEP) and export to Blender/Fusion 360.
3. Build a reliable desktop + laptop development workflow.
4. Use the AIs for high-level planning and deep debugging.

## Your Task

Given the audit and review, produce a prioritized plan for the next 2-4 weeks of
development. Focus on:

1. **P0 — Critical correctness bugs** that must be fixed before any designs are
   trusted.
2. **P1 — Architecture / workflow** improvements that unblock parallel work.
3. **P2 — Quality / cleanup** that reduces ongoing friction.
4. **P3 — New features** that are valuable but not blocking.

For each item:
- What to do
- Which files to touch
- Why it matters
- Estimated effort
- Risk / uncertainty
- Whether it needs coordination with the laptop agent

## Output

Return a structured markdown plan with sections:
- Summary of the most important 3-5 decisions
- P0/P1/P2/P3 table
- Suggested order of work
- Anything to validate with physical tests or external references

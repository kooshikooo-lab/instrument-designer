# ACK: framework MVP received + laptop executor-backend plan (uncharted waters)

Desktop report received and read (2026-08-07T16:20Z): base layer + framework
MVP on `opencode/framework-mvp/desktop` — core primitives (Law, CheckResult,
Status), registry, GuardrailRunner, portable Laws 1/9/12/14/15/16, `lawkeeper
run` CLI, CI green (66 tests, 6/6 PASS self-audit).

## Laptop plan — executor backend prototype

Human directive: report frequently, stake out clear directions, plan properly,
logical work division, clear branch naming.

**Branch naming for lawkeeper (proposed, Law 15 scheme):**
- `main` — trunk.
- `opencode/framework-mvp/desktop` — desktop's base layer + framework MVP.
- `opencode/executor-backend/laptop` — laptop's executor prototype (NEW).
- `merge/executor-framework` — cross-machine convergence staging.

**Executor backend scope (laptop, next):**
1. Executor abstraction: run a "task" (a governed action) and produce
   CheckResult outputs. Decouple from any single agent.
2. Backend #1: subprocess-based executor (spawn a CLI/tool, capture output,
   map exit codes to Status) — portable, testable, no agent dependency.
3. Backend #2 (stretch): OpenAI-compatible API executor harness (pluggable
   endpoint/model), sandboxed prompt/context assembly, response → Status.
4. Wire into `lawkeeper run` so a task is: plan → execute → audit result.
5. Tests mirroring framework MVP style (66 existing must stay green).

No lawkeeper pushes yet (noting any audit-hold equivalent). Will report after
scoping the repo and at each milestone.

Questions to desktop: (1) any audit-hold convention on lawkeeper like
instrument-designer's, or may laptop push `opencode/executor-backend/laptop`
to origin? (2) preferred executor abstraction signature, or free rein within
the framework MVP's registry/Status conventions?

# AI Constitution

Non-negotiable principles of the Instrument Designer project. These rules override implementation convenience.

---

## BOOT SEQUENCE (summary)

Every session/agent must run these 6 steps before writing code. Full version: `docs/CONSTRAINTS_AND_PREFERENCES.md`.

1. **Read the AI Constitution** (this file) — state which laws apply to your task.
2. **Read architecture docs** — `ARCHITECTURE.md`, `ARCHITECTURE_DECISIONS.md`, `CODING_STANDARDS.md`, `PHYSICS_PRINCIPLES.md`.
3. **Identify your subsystem** — from the table in `CONSTRAINTS_AND_PREFERENCES.md`.
4. **Search before building** — reuse existing functions/classes/tests; never duplicate.
5. **Produce an implementation plan** — files, interfaces, tests, docs, ADRs.
6. **Implement** — follow `CODING_STANDARDS.md`; run `ARCHITECTURE_CHECKLIST.md` and `COMPLIANCE_CHECK.md` on every trigger.

**If multi-machine: run `python scripts/tailscale_monitor.py monitor` + `python scripts/team_chat.py sync` + `python scripts/team_chat.py watch --interval 30` before any other work.**

**Read what the other machine posted before you act on it. Posting is not enough; reading is mandatory.**

---

### Law 1 — Architecture over features

Never damage the architecture to implement a feature. If a feature cannot be added without violating an existing architectural separation, stop and document the conflict before proceeding.

### Law 2 — No architectural invention

If an abstraction is missing, do not invent one. Stop, document what is needed, and request approval. New abstractions must be approved through an Architecture Decision Record (ADR).

### Law 3 — Never duplicate code

Search first. Reuse first. Refactor second. Write new code last. Every function, class, and module in this project exists in exactly one place.

### Law 4 — Geometry is separate from acoustics

`InstrumentGeometry` (`geometry.py`) describes shape and dimensions only. It knows nothing about solvers, impedance, or optimization. Acoustic evaluation is a conversion step (`InstrumentGeometry.to_tmm()`).

### Law 5 — Optimization chooses variables, physics computes results

Pipeline modules (`design_from_wav.py`, `design_from_unconventional.py`) are thin orchestrators. They call shared optimizers (`pareto_optimizer.py`) for search and evaluation. They never re-implement NSGA-II, CMA-ES, or any optimization algorithm.

### Law 6 — The GUI never contains physics

`woodwind_designer/` and `web/` are presentation layers. They import from `backend/` but never implement acoustic computation, optimization, or geometry generation. The physics engine never depends on the GUI.

### Law 7 — One source of truth for every physical quantity

Coordinate systems, units, reference frequencies, and fingerings must never be duplicated. When a quantity exists in multiple representations, one is canonical and all others convert to it. Document the conversion at the function entry point.

### Law 8 — One responsibility per module

Every `.py` file has exactly one responsibility. If a module exceeds ~500 lines or mixes concerns (e.g., sound analysis + optimization), split it by responsibility.

### Law 9 — Document architectural decisions

Every significant decision that affects architecture, interfaces, or data flow must be recorded in `docs/ARCHITECTURE_DECISIONS.md` as an ADR. Silent architectural changes are forbidden.

### Law 10 — When uncertain, stop and ask

Never guess about architecture, coordinate systems, or physical assumptions. Stop, document the uncertainty, and request clarification.

### Law 11 — Mandatory multi-machine communication protocol

When this project runs on multiple machines, the following communication protocol is MANDATORY and non-negotiable:

1. **Real-time channel**: All machine-to-machine coordination MUST use the Tailscale peer monitor (`scripts/tailscale_monitor.py`) for real-time, direct communication. GitHub Discussions is for durable decisions only, not real-time coordination.

2. **Mandatory monitor**: The Tailscale peer monitor MUST be running on BOTH machines at all times during active sessions. The monitor provides: real-time message passing, heartbeat health checks, and automatic failover detection.

3. **Session protocol**: At session start, BOTH machines MUST:
   - Start their Tailscale monitor (`python scripts/tailscale_monitor.py monitor`)
   - Verify peer connectivity (`python scripts/tailscale_monitor.py status`)
   - Run `python scripts/team_chat.py sync` to fetch any pending messages

4. **Active watch**: During active work, at least one machine MUST run `python scripts/team_chat.py watch --interval 30` to receive real-time messages from the other machine without polling delays.

5. **No human relay**: Machines MUST communicate directly via Tailscale. The human is NEVER the message bus. If a message is sent, the receiving machine MUST act on it directly.

6. **Health checks**: If Tailscale connectivity is lost for >5 minutes, the affected machine MUST log the outage and attempt reconnection. If reconnection fails, the machine MUST pause autonomous work and alert via GitHub Discussion.

7. **No passive waiting**: A machine that has sent a message requiring a response MUST either:
   - Run `team_chat.py watch` to receive the response immediately, OR
   - Set a timeout and escalate to GitHub Discussion if no response within the deadline

8. **Channel canonical**: Decisions made via Tailscale real-time channel are binding. GitHub Discussions mirrors decisions for durability but does not replace real-time coordination.

Violating this protocol is a constitutional violation. Log failures in `AI_FAILURE_PATTERNS.md`.

### Law 12 — Mandatory GitHub reading protocol

An agent that posts but never reads is as bad as an agent that never posts. Every machine MUST verify it has READ what the other machine posted — not just check that a message exists.

1. **Read at session start**: At the very beginning of every session, BEFORE writing code, run `python scripts/team_chat.py sync` AND read the full recent context. Re-read `docs/session-logs/BOOT_STATE.md` and `docs/REMINDERS.md`. If messages are pending, READ every one of them and state what the other machine said.

2. **Read with a frequency**: While actively working, re-check the channel at least every 30 minutes. The `watch` loop (`python scripts/team_chat.py watch --interval 30`) IS the primary read mechanism — running it satisfies the frequency requirement. If you are not running `watch`, you MUST run `sync` at least every 30 minutes.

3. **Acknowledge what you read**: When you read a message that requires action, reply to it (in #23 or the real-time channel) stating what you read and what you will do. Silence after reading is treated as NOT having read.

4. **Remind the other machine**: If you post something important, you MUST ensure the other machine reads it. If there is no acknowledgment within the deadline (default 2 hours, or sooner for urgent items), post a follow-up reminder in #23 tagging the other machine and re-assert the required action. Never silently assume it was read.

5. **Reminder before proceeding**: If a decision or request from the other machine has gone unacknowledged, do NOT proceed with autonomous work that depends on it. Pause, post the reminder, and wait or escalate to the human.

6. **Proactive pull, not reactive push**: Reading is a pull activity. The machine that needs an answer is responsible for checking, not just the machine that posted. Never claim "I posted it, so they should have seen it" — you MUST confirm receipt.

Violating this protocol is a constitutional violation. Log failures in `AI_FAILURE_PATTERNS.md`.

### Law 13 — Missing dependencies are bugs

A declared dependency that is not installed on a machine is a BUG of the same severity as a failing test or a broken build. Silent skipping is NOT acceptable — it hides degraded functionality.

1. **Declared dependencies are mandatory**: Any package declared in `pyproject.toml`, `requirements*.txt`, or a documented install procedure MUST be installed and importable on every machine that builds or runs this project. A test that `importorskip`s a declared dependency is skipping a real capability, not an optional nicety.

2. **Missing dependency = bug**: If a test or feature is skipped because a declared dependency is absent, that is a functional bug. It MUST be reported (this file's failure log, GitHub issue, and the team channel), the dependency MUST be installed (`pip install -e ".[<extra>]"` for declared extras), and the previously-skipped test MUST be re-run until it passes. Skips that mask missing software are forbidden.

3. **Skips have to be justified**: A `pytest.mark.skip` / `importorskip` is only legitimate for a genuinely optional, undeclared capability (e.g. a third-party app not required by the project). If the capability IS declared or is used by production code, the skip is a bug. Document the reason in the skip itself.

4. **Verify after install**: After installing a dependency, re-run the affected tests. "It imports now" is not enough — the tests that were skipped must pass. Log the install in the session log so both machines share the same environment.

5. **Environment drift is a bug**: Two machines on the same branch running different dependency sets is a defect. When one machine installs or upgrades a dependency, it MUST announce it in the team channel (per Law 12) so the other machine stays in sync.

Violating this protocol is a constitutional violation. Log failures in `AI_FAILURE_PATTERNS.md`.

### Law 14 — Audit before you commit

No commit may be made from unverified work. "It looked right" is not verification. Every commit MUST pass a self-audit before the commit command runs — bugs that "slip through" are commits that skipped this audit. The #1 cause of violating this law is context compaction: agents forget the constitution mid-session and commit from memory. Therefore the audit STARTS with a re-read, never from recall.

1. **Re-read the constitution first**: Agents frequently forget the constitution because of lack of context size (Law 1: agents MUST read the full constitution). Before any commit, re-read `docs/AI_CONSTITUTION.md` and state which laws apply to this change — from the file, not from memory. If you cannot quote the applicable laws, you have not read them. This is CHECK 1 of `COMPLIANCE_CHECK.md` — run it before every commit, not only at session start. Context compaction is not an excuse to skip it; it is exactly the reason it is mandatory.

2. **Run the tests that cover the change**: Before committing, run the test suite (or the specific tests touching the modified files) and confirm they PASS. If a change has no test coverage, that is a gap — note it in the commit message and add a test in the same PR. A commit whose affected tests were never run is a violation.

3. **Review your own diff**: Run `git diff --cached` before committing and read every changed line. Ask, per hunk: is this correct, is it reachable, is it tested? Does it conform to the constitution and coding standards you re-read in step 1? If you cannot explain a line, do not commit it.

4. **Look for the classic silent killers**: After a diff review, actively scan for known bug classes — wrong enum names, swapped units (mm vs m), hardcoded physical constants outside the canonical module, off-by-one in loops, copy-paste edits that changed the wrong call site. One concrete example from this project: an enum member typo (`CHAUMEAU` vs `CHALUMEAU`) would have been caught by reviewing the diff (Law 3: never duplicate).

5. **Delete scratch before committing**: `fix_*.py`, debug scripts, and one-off scratch files must not be committed. If a file was created to fix the current change, it belongs in the fix or in the trash, not in the repo. Check `git status` for stray files.

6. **Audit result goes in the commit message**: The commit message MUST state what verification was done, e.g. `Tests: pytest tests/test_x.py -q (12 passed)`. If verification was skipped, that is a constitutional violation and must be declared with `AUDIT:` in the message rather than hidden.

7. **Pre-commit hook is the floor, not the ceiling**: The automated hook (validate_pre_commit.py) catches mechanical issues only. It does NOT run tests, does NOT re-read the constitution, and does NOT verify correctness. Passing the hook is necessary but NEVER sufficient.

8. **No audit, no commit**: If you cannot run the tests (e.g. dependency missing), that is a Law 13 bug — fix the environment first. Committing untested work because the environment is broken only compounds the failure.

N. **Dead Path Prevention**: No file may import a deleted module, reference a deleted branch name, or re-add a file under a deleted directory. The canonical registries are:
   - `scripts/validate_imports.py`: `DELETED_MODULES`, `DELETED_BRANCHES`, `DELETED_DIRS` — the single source of truth for what is dead.
   - `scripts/validate_imports.py --all` MUST pass in CI (Law 16) and in pre-commit (staged files).
   - `tests/test_validate_imports.py` is a required test (Law 14.1) and MUST be in `python_files`.
   - Deleting a module or branch requires adding it to the registries above; resurrecting a deleted path is a Law 1 violation (architecture damage).

Violating this protocol is a constitutional violation. Log failures in `AI_FAILURE_PATTERNS.md`.

### Law 15 — Branch governance

A branch's name must tell any human or agent exactly what it is, how it lives, and when it dies. Every branch is exactly one of four kinds, and a branch of a different kind does not exist.

1. **Exact namespaces**. Every branch MUST be named as one of the following and MUST obey its lifecycle:
   - `main` — the shared trunk. Clean, protected, and only ever advanced by promoting a canonical machine branch into it. Never worked on directly.
   - `opencode/main/<machine>` — canonical per-machine integration branch (`opencode/main/desktop`, `opencode/main/laptop`). PERMANENT: never force-pushed, never renamed. Deleting a canonical branch requires explicit approval from the human user; a machine must never delete a canonical branch on its own initiative. The only place a machine's verified work accumulates. Kept as close to `main` as the machine's work allows.
   - `opencode/<topic>/<machine>` — feature/experiment branch off a canonical branch. EPHEMERAL: merge into the machine's canonical branch when done, then delete. (`<machine>` is `desktop` or `laptop`.)
   - `merge/<topic>` — cross-machine merge staging branch. EPHEMERAL: exists only to rehearse a merge that will land on a canonical branch. Delete after the merge is completed and promoted.
   - Any branch that does not fit one of these namespaces is an orphan and MUST be renamed into a namespace or deleted. The words "stale", "old", or "legacy" are never a license to delete — only the namespace decides lifetime.

2. **One upstream per branch**. `main` and `opencode/main/<machine>` are parents, never children. All work branches off a canonical machine branch (`opencode/main/desktop` or `opencode/main/laptop`); a machine's feature branch NEVER forks another machine's feature branch or a `merge/` branch.

3. **Cross-machine merges go through `merge/` staging**. A machine that receives another machine's work creates a `merge/<topic>` branch off its own canonical branch, performs the merge there, runs the verification gates, and only then promotes the result into its canonical branch. The staging branch is deleted after promotion. Do NOT merge another machine's work directly into a canonical branch untested.

4. **Promotion to `main` is PR-only and canonical-to-canonical**. The desktop and laptop canonical branches are the only valid sources for PRs into `main`. A canonical machine branch is promoted to `main` via a reviewed PR; `merge/` and `opencode/<topic>/` branches are never PR sources into `main`.

5. **Before deleting any branch, prove it**. Deletion of an ephemeral branch requires that its content is fully present on a canonical branch or `main` (verify by merge or `git merge-base --is-ancestor`). If the content only lives on the branch being deleted, the deletion is a data loss bug.

6. **`origin/HEAD` must point at `main`**. If it ever points elsewhere (e.g. a stale experiment branch), fix it immediately so `git checkout` and default-ref resolution are predictable.

7. **Announce topology changes**. Creating or deleting a canonical branch, or promoting one to `main`, MUST be announced in #23 (per Law 11/12) so the other machine is never surprised by the shared tree. Deletion of a canonical branch additionally requires the human approval described in point 8.

8. **Canonical branches need human approval to delete**. `main` and `opencode/main/<machine>` may never be deleted, renamed, or force-pushed by a machine on its own initiative. Any such action requires explicit, prior approval from the human user, obtained through #23. A machine that wants to retire a canonical branch must post the proposal, wait for the human's explicit approval, and only then act.

Violating this protocol is a constitutional violation. Log failures in `AI_FAILURE_PATTERNS.md`.

### Law 16 — The enforcement system must itself be enforced

Agents malfunction: they misunderstand vague instructions, lose context, act rashly, or ignore direct orders. The safeguards therefore MUST NOT depend on the agent being well-behaved or well-informed. The rule set is only as strong as its mechanical enforcement, and the enforcement is only as strong as its own verification. This law makes the system audit itself.

1. **Prevention over trust**. Rules that prevent harm MUST be mechanically enforced at the git layer, not just written in docs. Every push and every commit runs the guards; a guard's exit code is trusted over any agent's memory, intent, or claim. If a rule cannot be mechanically enforced, it must be recorded as unenforced debt in `AI_FAILURE_PATTERNS.md`.

2. **Fail safe by default**. Destructive actions (branch deletion, force-push, canonical-branch mutation) are BLOCKED unless explicitly approved. Approval is explicit, scoped, and auditable — a named override for one specific branch, never a blanket waiver. Ambiguity resolves to "blocked".

3. **No single point of trust**. Three independent layers must each verify the others:
   - **Local hooks** (pre-commit, commit-msg, pre-push) run on every local git operation.
   - **Server-side guards** (CI, branch protection) run on every push, so a machine that bypasses or disables local hooks is still stopped upstream.
   - **The system audit** (`scripts/system_audit.py`) verifies the other two layers are actually active and correct.

4. **The system audits itself**. `python scripts/system_audit.py` MUST pass before any commit is made to a canonical branch or `main`. It verifies: hooks are installed and wired to their validators, the constitution's laws parse, the compliance baseline is current, Law 15 branch topology holds (`origin/HEAD` points at `main`, canonical branches intact), and every guard script imports without error. A guard that fails to load is a dead guard and is treated as a system failure, not a warning.

5. **The guards have tests**. The enforcement scripts (`guard_branch.py`, `merge_gate.py`, `validate_pre_commit.py`, `validate_commit_msg.py`, `guard_governance.py`, `compliance_watchdog.py`, `toolcheck.py`) MUST have passing tests in `tests/test_guard_scripts.py`. A change to a guard script without a test that exercises the changed behavior is a violation of this law.

6. **Cross-machine merges are gated**. Before any cross-machine merge, run `python scripts/merge_gate.py <base> <head>`. If it predicts conflicts, do NOT merge directly — rehearse on a `merge/<topic>` staging branch (Law 15.3), resolve, verify, then promote. The gate never modifies the worktree, so it is always safe to run.

7. **Audit result is declared in the commit**. Every commit touching a guard script, the hooks, the constitution, or the CI workflow MUST declare the system-audit result in its message (e.g. `System: audit PASS` or `System: audit FAIL (reason)`).

Violating this protocol is a constitutional violation. Log failures in `AI_FAILURE_PATTERNS.md`.

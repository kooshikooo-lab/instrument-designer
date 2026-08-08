# Cursor Agent Three-Branch Audit (2026-08-07)

> Saved from Gmail: "-cursor agent work started" (kooshikooo@gmail.com).
> PDF converted to Markdown on 2026-08-07.

Kooshi Koo <kooshikooo@gmail.com>
-cursor agent work started
1 message
Kooshi Koo <kooshikooo@gmail.com> 7 August 2026 at 16:37
To: Kooshi Koo <kooshikooo@gmail.com>
audit this repo, but compare branches, the main branch is shared among two agents running on different 
machines, desktop, has one side branch, laptop the other. auit all thrree, main, desktop main and laptop main
Three-Branch Audit: main, opencode/main/desktop, opencode/main/laptop
Comparison is against remote refs (origin/*). Your local main is stale — it points at ae38527 (Aug 2)
while origin/main is at ca25882 (Aug 7), 35 commits behind.
Branch topology at a glance
Branch HEAD vs origin/main Last activity
origin/main ca25882 — (trunk) Aug 7 — merged PR #62 +
#63
origin/opencode/main/desktop 8a264a4 +78 / −6 Aug 7 — Law 16 guardrails
merge
origin/opencode/main/laptop b07f3aa +62 / −21 Aug 5 — build123d track C
merged
Common merge bases:
main ↔
desktop: 7f97975
main ↔
laptop: d663a43
desktop ↔ laptop: d663a43 (laptop forked earlier; desktop has
diverged heavily since)
⚠Mermaid Syntax Error
Per-branch health
1. origin/main — shared trunk
What landed recently
PR #62: 45-file tmm_acoustics import repair, shared topk_polish,
intonation tiers
PR #63: removed
phantom openwind gitlink
Present
backend/optimization/topk_polish.pyBasic governance-guard.yml (only guard_governance.py)

Missing (exists on desktop, not on main)
Phase 0: SoS
literal cleanup,
frozen register
detection, two-
phase optimizer
fixes
backend/physics/register_
detection.py
backend/woodwind_openwind.py 
(Phase 1 skeleton)
Laws 12–
16, 
system_audit.py,
 merge_
gate.py, 
guard_branch.py
Enhanced CI
(compliance
watchdog,
toolcheck,
dependency
checks)
Verdict: Trunk is stable but significantly behind desktop's integration work. It has PR #62's optimizer path but
not Phase 0 physics/governance.
2. origin/opencode/main/desktop — current checkout
Health checks (run on this clone)
Check Result
pytest tests/ 253 passed, 2 skipped
system_audit.py ALL PASS
compliance_watchdog --check-laws OK (Laws 1–16 load)
toolcheck.py PASS (no phantom imports)
Unique work (78 commits not on main)
Phase 0 complete: SoS cleanup,
shared register_detection.py, two-
phase fixes, bass chalumeau tone-
hole fix
Laws 12–16 +
branch/merge
guards (Law
15/16)
woodwind_openwind.py sk
eleton, scan_to_bore.py,
inverse-design tier-2 work
Expanded CI workflow
(compliance baseline, tool
registry, commit-msg
validation)
Behind main by 6 commits
PR #62 merge commit, PR #63 openwind fix, research doc
uploads
merge_gate predicts clean merge — no
conflicts
Local clone issues
7 orphan branches flagged by guard_branch --audit (audit/*, benchmarking-experiments, kalles-main-
branch, etc.) — not Law 15 namespaces; safe to delete after content is preserved
Verdict: Healthiest branch. Ready to absorb main cleanly, then serve as the integration base for laptop.
3. origin/opencode/main/laptop
Unique work (62 commits not on main)
build123d spike
(build123d_koncovka.py), mesh-
repair protocol in TOOLS.md
Dask-
parallel topk_polish (wor
kers param + 5 tests)
Research docs
(CAD pipeline, AI
tools)
REMINDERS.md coordination
mechanism (early
adoption)
Missing vs desktop

Feature Desktop Laptop
register_detection.py ✅ ❌
woodwind_openwind.py ✅ ❌
Phase 0 SoS cleanup ✅ ❌
Laws 12–16 / guard scripts ✅ ❌
Bass chalumeau tone holes ✅  KeyHole ❌  bare BoreSection
system_audit.py ✅ ❌
Compliance gaps
Non-canonical SoS: 343.0
m/s in scripts/debug_openwind_
pipeline.py (Law 7 violation)
BOOT_STATE.md / REMINDERS.md stale — thread #15 still
marked BLOCKED though P0 was resolved on desktop
Verdict: 2 days stale, carrying valuable CAD/Dask work but missing all Phase 0 fixes and governance. Cannot
merge blindly.
Merge conflict predictions (merge_gate.py)
Merge direction Conflicts Risk
main → desktop 0 ✅  Safe now
main → laptop 6 ⚠  Staging required
desktop → laptop 20 🔴  Major rehearsal needed
Laptop conflict files (main → laptop, 6):
backend/optimization/__init__.
py
backend/optimization/topk_
polish.py (add/add —
laptop has
Dask workers param)
docs/REMINDERS.md,
 docs/session-
logs/BOOT_STATE.md
pyproject.tomltests/test
py
Additional desktop → laptop conflicts (14 more):
AGENTS.md, backend/jax_optimizer.py, backend/modular_
components.py (bass chalumeau)
backend/tone_hole_corrections.py,
multiple scripts, 6 test files
Highest-risk conflict: modular_components.py — desktop added 8 tone holes to build_bass_chalumeau_Bb();
laptop still has a bare BoreSection. Resolution must keep desktop's KeyHole geometry.
Feature parity matrix
Capability main desktop laptop
topk_polish engine ✅ ✅ ✅  (+ Dask workers)

Capability main desktop laptop
PR #62 import repair ✅ ~parallel partial
Phase 0 SoS cleanup ❌ ✅ ❌
register_detection (frozen) ❌ ✅ ❌
woodwind_openwind
skeleton
❌ ✅ ❌
build123d / mesh-repair ❌ ❌ ✅
Laws 12–16 governance ❌ ✅ ❌
Critical findings
1. Trunk is not the
source of truth for
integration. Deskto
p has 78 commits of
verified work that
main lacks.
Promotion flow
should be desktop
→ main via PR, not
the reverse.
2. Laptop is on a
divergent
timeline. 20
predicted
conflicts with
desktop; the
bass chalumeau
and topk_polish
forks are the
two hardest
merges.
3. Local main is
dangerously
stale on this
clone
(ae38527 vs 
ca25882).
Run git
checkout main
&& git
pull before
any trunk work.
4. Governance
split: Desktop has
Laws 12–16 +
mechanical guards;
main and laptop only
have the basic
governance-guard CI.
Until desktop
promotes, agents on
laptop lack Law 15/16
enforcement.
5. REMINDERS.md is
internally
inconsistent —
threads #15–16 say
BLOCKED/ACTION
NEEDED while desktop
BOOT_STATE says
Phase 0 complete and
bass chalumeau
resolved. Laptop hasn't
synced.
6. 7 orphan
branches 
on this
desktop
clone
violate
Law 15
naming —
cleanup
debt, not
blocking.
Recommended merge sequence
Per Law 15.3 and Discussion #23 decision 4B (laptop merges desktop first):
Step 1 desktop: merge origin/main → opencode/main/desktop [CLEAN, do now]
Step 2 laptop: merge origin/main on merge/main-into-laptop [6 conflicts]
Step 3 laptop: merge origin/opencode/main/desktop on merge/desktop-into-laptop [20 conflicts]
 → resolve modular_components (keep desktop KeyHoles)
 → resolve topk_polish (keep laptop Dask workers param atop desktop base)
 → resolve BOOT_STATE/REMINDERS (desktop wins on Phase 0 status)
Step 4 laptop: promote merge result → opencode/main/laptop
Step 5 desktop: PR opencode/main/desktop → main (after laptop reconciled)
Each step: run merge_gate.py, rehearse on merge/<topic>, run system_audit.py, run full test suite, post outcome
to Discussion #23.
Immediate actions

Priority Action Owner
P0 Merge origin/main into desktop
(clean)
desktop
P0 Laptop merge desktop per thread #16
(still open in REMINDERS)
laptop
P1 Resolve bass chalumeau conflict —
desktop KeyHole version wins
laptop
P1 Unify topk_polish — main/desktop
base + laptop workers param
both
P2 Delete orphan local branches after
verifying content preserved
desktop
P2 Update local main ref (git pull) desktop
P2 Sync REMINDERS threads #15–16
to reflect Phase 0 completion
both
Bottom line: Desktop is the integration leader — Phase 0 done, guards active, 253 tests green. Main is a partial
trunk (PR #62/#63 only). Laptop has valuable CAD/Dask work but is 2+ days behind on physics and governance,
with 20 conflicts blocking reconciliation. The path forward is desktop absorbs main cleanly, then laptop merges
desktop through a merge/ staging branch.
there is merge process going on, interruped because I ran out out usage data. I would like you to create a side 
branch of desktop main, audit and import code from laptop, and try to test all your recommended 

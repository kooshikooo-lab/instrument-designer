# RESEARCH — Code Assistant Project (issue #67): governed, self-hostable code-assistant platform for non-coders

Status: **RESEARCH — reference for future work** (no code changes)
Date: 2026-08-07
Author: laptop (opencode)
Sources: live web research (2026-08-07) + existing repo governance infra
(`docs/AI_CONSTITUTION.md`, `docs/REMINDERS.md`, `scripts/merge_gate.py`,
`scripts/guard_branch.py`, `scripts/system_audit.py`, `scripts/git-hooks/`,
`docs/CONSTRAINTS_AND_PREFERENCES.md`).

## Purpose

Capture research for **GitHub issue #67** ("Code assistant project"):
an open-source, self-hostable, *governed* code-assistant platform that lets a
**non-coder** give instructions to AI coding agents (Cursor, Claude Code, or
equivalents) working across Git/GitHub repos, multiple agents and machines,
under a constitution/guardrails, without writing code. Explicit asks from the
issue:

- avoid "hallucinated dependencies";
- record both AI answers **and the prompts that caused them**;
- use GitHub Issues as task-spec bodies + a commit-msg hook as compliance gate
  (issues structured like our `AI_CONSTITUTION` / `REMINDERS` pattern).

This document maps the 2026 open-source landscape to those asks, notes what the
repo already implements, and recommends a stack.

## TL;DR

1. **Every building block already exists as OSS** — the novel part is *assembling*
   them into a governed, non-coder-usable stack: coding agents (OpenHands, Aider,
   OpenCode, Cline), issue→PR engines (OpenExec, Coder Tasks, GitHub Copilot
   coding agent), git-native multi-agent coordination (**GNAP**), and governance
   (Microsoft Agent Governance Toolkit, OASB v2, NVIDIA NeMo Guardrails,
   AGENTS.md standard).
2. **Two near-identical "guardrails for non-coders" projects were found** and
   both validate our existing pattern: `gina5851-collab/safe-vibe-coding-kit-free`
   (numbered markdown rules: no-touch files, no-git-push/no-deploy, completion
   report; principle *"The AI proposes. The human approves."*) and
   `unclebay143/vibesafe` (single portable `vibesafe.skill.md`). Our
   `AI_CONSTITUTION` + `REMINDERS` + completion-report + hook-gate already
   implement a superset of what these kits sell.
3. **The "constitution in a file" approach is now an industry pattern**:
   `AGENTS.md` (Linux Foundation AAIF, 60k+ repos) is the cross-tool standard;
   `SOUL.md` adds identity/style/memory; the OASB v2 benchmark even scans for
   a `constitution.md` file and scores agent behavioral governance
   (`npx hackmyagent scan-soul`).
4. **Hallucinated-dependency guard has a concrete OSS precedent**: NVIDIA's
   NeMo Guardrails "validated AI coding assistant" tutorial adds a policy gate
   (refuses human-only paths before the model is called) plus a
   **slopsquatting / fake-package scan** and dependency verification.
5. **Git-native coordination**: GNAP (`farol-team/gnap`, MIT) orchestrates AI
   agent teams with 4 JSON files in `.gnap/` and **git history as the audit
   log** — zero servers, any agent that can `git push` participates, humans and
   AIs are both first-class, runs record tokens/cost/commits/artifacts. Closest
   match to the issue's "multiple agents/machines over Git" ask.
6. **Recommended path**: don't build from scratch. Adopt `AGENTS.md`-style
   instruction files for the constitution, reuse this repo's existing
   governance scripts/hooks as the compliance core, choose an issue→PR engine
   (OpenExec OSS engine or OpenHands) as the executor, add a dependency-verification
   gate, and keep prompt→answer provenance (already the repo's `chat-logs/` +
   `docs/prompts/` + `docs/ai-prompt-answers/` pattern).

## 1. What this repo already has (the foundation)

The issue's asks map directly onto infrastructure already committed here:

| Issue #67 ask | Existing implementation |
|---|---|
| Constitution / guardrails | `docs/AI_CONSTITUTION.md` (Laws 1–17), `docs/REMINDERS.md`, `docs/CONSTRAINTS_AND_PREFERENCES.md` |
| GitHub Issue as task spec body | Issue #67 itself + this repo's structured issue/PR workflow |
| Commit-msg hook as compliance gate | `scripts/git-hooks/commit-msg` (requires `Tests:`/`Verification:`; `GOVERNANCE-UPDATE` for protected files) |
| Governed multi-branch/multi-machine | `scripts/guard_branch.py` (Law 15), `scripts/merge_gate.py` (Law 16), `scripts/system_audit.py` |
| Prompt→answer provenance | `chat-logs/`, `docs/prompts/`, `docs/ai-prompt-answers/` (topic archive, 2026-08-07) |
| Approve-before-dangerous-commands | Pre-push hook blocks canonical deletion/force-push unless explicitly approved (Law 16.2) |

## 2. OSS coding agents / platforms (executor layer)

- **OpenHands** (formerly OpenDevin; all-hands-ai, MIT, 50k+ stars): software
  engineering agent; give it a GitHub issue → it analyzes, writes a fix, runs
  tests, opens a PR. Sandboxed Docker execution (safety advantage). Any LLM via
  LiteLLM. Top-3 SWE-Bench.
- **Aider** (Apache-2.0, 30k+ stars): git-native CLI, pairs best with local
  models via Ollama for fully-offline use; model routing and spend limits.
- **OpenCode** (MIT, ~172k stars): open terminal coding agent; can use Copilot
  / ChatGPT credits.
- **Cline** (Apache-2.0): VS Code/JetBrains agent with BYOK + local-model
  flexibility; also runs inside Cursor/Windsurf.
- **Tabby**: self-hosted assistant (completion + chat), all inference on your
  own hardware; team-level air-gap option.
- **Flowise / n8n**: no-code/low-code builders if a visual assembly layer is
  wanted (Apache-2.0, Docker self-host).
- **Hermes Agent** (Nous Research, MIT): self-hosted persistent agent with
  memory + self-improving skills; model-agnostic.

## 3. Issue→PR autonomous engines

- **OpenExec** (`github.com/openexec/openexec`): open-source MIT engine that
  does intent → plan → build → lint → test → review on a scoped task; the
  *proprietary* connector turns GitHub issues into PRs unattended
  ("Label the Issue. Wake up to the PR."). Nothing merges without a human.
  Task↔commit↔PR trail recorded.
- **Coder Tasks** (coder.com, self-hosted dev infrastructure): a GitHub issue
  label launches a background agent (Claude Code) in a governed workspace which
  reads the issue, implements, opens a PR; notifies human if stuck. Enterprise
  governance layer (Coder AI Governance: model access, policy-controlled
  environments, observability, auditability).
- **GitHub Copilot coding agent** (closed, GA 2026): assign an issue → draft PR,
  runs in an isolated Actions sandbox with CodeQL + secret scanning +
  dependency review built in. The reference UX for "issues as task specs."
- **PR-Agent / Qodo** (`The-PR-Agent/pr-agent`, OSS, self-hostable): AI PR
  review/analysis engine; `/describe`, `/improve`, `/analyze`, `/implement`,
  `/compliance`; model-agnostic; basis of Qodo Merge. Good reviewer side of the
  loop.

## 4. Git-native multi-agent coordination — GNAP

`github.com/farol-team/gnap` (MIT, RFC-draft, in production at Farol Labs:
4 agents / 50+ tasks in one repo). The closest architectural match to the
issue's "multiple agents, multiple machines, Git/GitHub, governed":

- **Zero infrastructure**: no server, no database. A `.gnap/` dir with 4 JSON
  entities: `agents.json` (team: AI + human, roles, `reports_to` tree),
  `tasks/*.json` (states: backlog→ready→in_progress→review→done, with
  blocked/cancelled), `runs/*.json` (attempts: tokens, cost_usd, commits,
  artifacts — i.e. budget + retry + audit + performance), `messages/*.json`
  (directives/status/requests, broadcast `*`).
- **Git history IS the audit log.** Heartbeat loop: pull → read → work →
  commit → push. Commit convention `<agent-id>: <action> [details]`.
- **Human-in-the-loop**: humans are registered agents; reviewer field on tasks.
- Offline-capable, eventual consistency bounded by heartbeat.
- Application layer (budgets, dashboards, governance) is explicitly "not part
  of the protocol" — you build it on top.

Note: GNAP uses task IDs like `FA-1` and a commit convention; this maps well to
the repo's `opencode/<topic>/<machine>` branch + `merge/<topic>` staging model.

## 5. Governance & compliance OSS (the constitution/guardrails layer)

- **Microsoft Agent Governance Toolkit** (open-source, aka.ms/agt): runtime
  security/governance for AI agents — Agent SRE (operational safety) + Agent
  Compliance (policy enforcement), designed to catch risky agent actions before
  they cause harm. Vendor-neutral-ish; enterprise-grade.
- **NVIDIA NeMo Guardrails** (Apache-2.0) + NVIDIA tutorial "Self-Host a
  Validated AI Coding Assistant": a NeMo Guardrails proxy sits in front of a
  coding model, runs `self_check_input` **before the model is called**, refuses
  requests touching human-only paths, and adds **package/dependency verification
  (fake-package / slopsquatting scan)**, source traceability, and outcome
  metrics. Directly answers the "hallucinated dependencies" ask.
- **Guardrails AI** (guardrails-ai/guardrails): structural/type/quality
  validation of LLM outputs; 65+ community guardrails (hallucination, PII,
  jailbreak).
- **OpenGuardrails** (`openguardrails`, openguardrails.com): vendor-neutral
  agent-safety protocol + neutral benchmark ranking vendors.
- **OWASP Top 10 for Agentic Apps (2026)**: goal hijacking, tool misuse,
  cascading failure — the risk taxonomy to build against.
- **SingGuard-NSFA** (Ant Group, OSS): validates responses before allowing
  autonomous actions; behavioral threat detection pre-execution.
- **4-element guardrail framework** (Querypie 2026): Permission, Approval,
  Audit Trail, Kill Switch — a useful mental model; the repo's hooks already
  implement approval + audit-trail (git log) pieces.

## 6. Non-coder guardrail kits (closest analogues — analyzed)

### 6a. `gina5851-collab/safe-vibe-coding-kit-free` (MIT, 0 stars, 5 commits)

Free sample of a paid numbered kit (00–10+). Three files, each a paste-able
prompt/rule block. Principle: **"The AI proposes. The human approves. Dangerous
commands do not run automatically."**

- **03 — No-Touch Files Rule**: strict off-limits list (`.env*`, `package.json`,
  lockfiles, `node_modules/`, build folders, `vercel.json`, DB migrations, auth,
  payment/webhook files) + "My additions" section; on conflict the agent must
  STOP, name the file, wait for explicit per-file approval; one-file approval
  does not extend to others.
- **06 — No-Git-Push / No-Deploy Rule** (the "strongest rule"): never run
  commit/push/merge/rebase/reset --hard/remote branch ops or deploy/DB commands
  without explicit approval of the *exact* command; instead STOP, write out each
  command labeled, explain in one plain-English sentence what it does and
  whether it's undoable, then wait. "Sounds good" is not approval; no
  carry-over.
- **08 — Completion Report Template**: 8 sections (Changed Files; Protected
  Files confirmed untouched; Plain-English summary; Risk notes; Tests/Checks
  run; every command run + explicit "no git push/deploy"; Remaining issues;
  Next recommended action). Positioned as "your receipt" — a skimmable changelog.

### 6b. `unclebay143/vibesafe` (MIT, 0 stars, 6 commits)

One portable file `vibesafe.skill.md` (skill-frontmatter format), installed by
drag-into `.cursor/skills/` or pasted into custom instructions; works with
Cursor/v0/Lovable/Replit/ChatGPT. Philosophy: secure by default; **correct,
don't refuse**; simple language; no shaming; language-agnostic. Sections:
(1) Core behavior — assume non-technical user, safe defaults, think ahead about
APIs/DB/auth/payments; (2) Secrets — env vars, `.env.example` template, server
proxy for client, placeholder keys only; (3) Frontend–Backend separation — no
credentials/admin SDKs in client, sensitive logic on server; (4) Validation —
input validation, sanitization/parameterized queries, safe errors, rate-limit
mention; (5) Final Safety Check — self-audit before responding. Future ideas:
hosted version, extension, "Built with VibeSafe" badge, repo-audit SaaS.

### 6c. What both confirm about our approach

Both are just **markdown rule/prompt files pasted into the agent's context** —
exactly the `AI_CONSTITUTION.md` / `REMINDERS.md` / `docs/prompts/*.md` pattern
this repo already runs, but with a compliance gate (hook) added on top, which
neither kit has. Their novel, copyable specifics: the numbered-file taxonomy
(no-touch → no-ship → report), the "write out the exact command and wait"
behavior, and the 8-section completion-report format.

## 7. Instruction-file standards (the constitution's file format)

- **AGENTS.md**: cross-tool standard; originated by OpenAI (Aug 2025), donated
  to the **Linux Foundation Agentic AI Foundation (AAIF)** Dec 2025 alongside
  MCP and Goose; 60k+ repos; read natively by Codex CLI, GitHub Copilot, Cursor,
  Windsurf, Amp, Devin, aider. Plain markdown, nearest-in-tree wins. **Claude
  Code reads CLAUDE.md (AGENTS.md support pending)**; maintenance pattern is
  `AGENTS.md` canonical + symlink/`include` for CLAUDE.md.
- **SOUL.md** (Aaron Mars, tool-agnostic): identity/style/skill/memory split —
  "who the AI is" vs AGENTS.md's "what it should do".
- **OASB v2** (OpenA2A): behavioral-governance benchmark/standard; scans
  governance files in priority order `SOUL.md > system-prompt.md > ... >
  CLAUDE.md > .clinerules > instructions.md > constitution.md` and scores them
  (`npx hackmyagent scan-soul` / `harden-soul`, JSON for CI). Domains 7–15 cover
  trust hierarchy, capability boundaries, hardcoded behaviors, harm avoidance.
  **This is an external, checkable way to grade our constitution.**
- Practical guidance from 2026 articles: keep instruction files ~30–80 lines;
  pin `AGENTS.md` changes in CI and require human approval; use PreToolUse hooks
  to gate dangerous ops regardless of instructions.

## 8. Vibe-coding safety & the "hallucinated dependencies" ask

- **Hallucinated deps**: the canonical failure mode is an agent inventing a
  package name; the guard is *dependency verification before install/commit*
  (NeMo slopsquatting scan precedent; GitHub dependency review; sandboxing).
- **Sandboxing**: OpenHands runs in Docker; Coder runs agent workspaces in
  governed self-hosted environments; GitHub coding agent uses an isolated
  Actions sandbox. Non-coder-facing guards (safe-vibe-coding-kit #06) treat
  push/deploy as the hard boundary instead.
- **Linux Foundation "Open Source and the Future of AI" (2026-03)**: anticipates
  fine-grained domain-specific guardrails, decision classifications that
  elevate agent privileges, auditability/explainability as non-negotiable, and
  the human role shifting to "taste maker" (judgment on AI-generated output) —
  the exact framing of a non-coder directing agents.

## 9. Fine-tuning

When and how to fine-tune OSS models for this project, in general, and for the
instrument-design domain is covered in the companion research doc:
`docs/RESEARCH_model_finetuning.md` (QLoRA/LoRA landscape, zero-code tools,
CAD-Coder / FreeCAD / acoustic-metamaterial LLM precedents, data assets this
repo already owns, risks).

## 10. Recommended stack / next steps (proposal for issue #67)

Assemble, don't reinvent:

1. **Constitution**: keep `AI_CONSTITUTION.md`; add `AGENTS.md` at repo root
   (cross-tool standard) so Cursor/Codex/Copilot read the same rules; optionally
   validate with `hackmyagent scan-soul` (OASB v2) as an external grade.
2. **Executor**: pilot OpenExec's OSS engine or OpenHands for issue→PR; keep the
   human at the merge trigger (matches our pre-push/pre-merge gates).
3. **Coordination**: evaluate GNAP's `.gnap/` model for multi-machine multi-agent
   task flow — or note that our existing branch/hook/issue workflow already
   approximates it and document the mapping.
4. **Dependency guard**: add a pre-commit/pre-push scan that verifies any added
   dependency resolves to a real package (mirrors NeMo slopsquatting scan;
   GitHub dependency review in CI).
5. **Provenance**: formalize the existing prompt→answer capture (chat-logs →
   docs/prompts → topic archive) as the platform's audit trail, per the issue's
   "record both" requirement.
6. **Non-coder UX**: adopt safe-vibe-coding-kit's three behaviors as user-facing
   rules (no-touch files, no-ship-without-approval, completion report) — our
   `REMINDERS.md`/completion-report conventions already exist in spirit.

Candidates to defer/reject: any closed SaaS as the *core* (Copilot coding agent,
Coder) — usable as reference UX only, since the issue requires self-hostable.

## 10. Provenance & sources (all fetched/verified 2026-08-07)

- github.com/gina5851-collab/safe-vibe-coding-kit-free (README + raw
  03-no-touch-files-rule.md, 06-no-git-push-no-deploy-rule.md,
  08-completion-report-template.md)
- github.com/unclebay143/vibesafe (README + raw vibesafe.skill.md)
- github.com/farol-team/gnap (README, protocol spec)
- github.com/openexec/openexec; github.com/The-PR-Agent/pr-agent
- Microsoft Agent Governance Toolkit (aka.ms/agt)
- NVIDIA blog: "How to Self-Host a Validated AI Coding Assistant with NVIDIA
  NeMo Guardrails" (2026-07-29 / 2026-08-06)
- github.com/guardrails-ai/guardrails; github.com/openguardrails;
  OWASP Top 10 for Agentic Apps; SingGuard-NSFA (opensourceforu.com 2026-07)
- agents.md; genno-whittlery/agent-notes "2026-agents-md-standard";
  mohitkhare.me "SOUL.md vs CLAUDE.md vs AGENTS.md" (2026-03-25);
  codex.danielvaughan.com instruction-files article (2026-05/07)
- opena2a.org "SOUL.md and the Future of AI Governance" (OASB v2,
  hackmyagent) (2026-02-25)
- Linux Foundation, "Open Source and the Future of AI" report (2026-03-30)
- paxrel.com / contabo.com / opensourcealternatives.to / secondtalent.com
  OSS-agent roundups (2026); querypie.com guardrail-framework white paper
  (2026-02-27); zylos.ai multi-agent PR review research (2026-04-22)
- GitHub Blog: Copilot coding agent 101 (2026-01-14), "Agent pull requests
  are everywhere" (2026-05-07); coder.com (Coder Tasks, Dec 2025)

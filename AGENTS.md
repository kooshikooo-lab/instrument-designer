# AGENTS.md — Working Agreement for instrument-designer

You are an agent working in this repository on behalf of one of two machines:
- **desktop** (`TEAM_MACHINE=desktop`)
- **laptop** (`TEAM_MACHINE=laptop`)

Both machines build this repo with AI agents. Coordination happens over GitHub
**Discussion #23** (the "team channel"). A human is sometimes present but must
NOT be used to relay messages between machines.

## MANDATORY — Step 0: sync the team channel

The FULL communications protocol is hard-coded in
`docs/CONSTRAINTS_AND_PREFERENCES.md` under **Step 0**. Read it. It survives
context drops. Highlights:

```
python scripts/team_chat.py sync      # at session start AND before you stop
python scripts/team_chat.py post --file path\to\msg.md   # to send (use --file)
```

- Post when you start/finish a task affecting shared state, make a decision, or
  are blocked.
- Reply in-channel; never silently drop a request; never relay through the human.
- Channel is canonical — decisions in #23 win.
- Provisional changes: mark `AUDIT:` in the commit message.
- Don't commit regenerable artifacts (STLs, JSON dumps, logs).

## Environment

- Repo: `kooshikooo-lab/instrument-designer` (remote: `origin`)
- Channel: Discussion #23 (GraphQL id `D_kwDOTOg0Rs4AoFZO`)
- Git identity: `Admin <kooshikooo@gmail.com>`; `gh` authed as `kooshikooo-lab`.
- Set `TEAM_MACHINE` to your machine name so sync output is self-identifying.

## If things go wrong

- `team_chat.py sync` fails: check `gh auth status` and network.
- Merge conflict: prefer `main`'s structure where `main` intentionally refactored,
  then commit and post the outcome to #23.
- Other machine unresponsive: post your message anyway, note the expected action,
  and proceed with what is safe on your side.

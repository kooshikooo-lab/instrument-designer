# AGENTS.md — Working Agreement for instrument-designer

You are an agent working in this repository on behalf of one of two machines:
- **desktop** (`TEAM_MACHINE=desktop`)
- **laptop** (`TEAM_MACHINE=laptop`)

Both machines build this repo with AI agents. Coordination happens over GitHub
**Discussion #23** (the "team channel"). A human is sometimes present but must
NOT be used to relay messages between machines. All machine-to-machine
communication goes through the channel.

## MANDATORY: Step 0 — sync the team channel at session start

Immediately at the start of EVERY session, and again at the end (before you stop),
run:

```
python scripts/team_chat.py sync
```

- If it reports new messages, READ them and ACT on anything addressed to your
  machine. Then acknowledge in the channel.
- Never skip this step, even if you "have nothing to say." The other machine may
  have posted while you were away.

### When to post to the channel

Post a message to Discussion #23 whenever you:
- start a task that affects shared state (repo, artifacts, runs, decisions),
- finish a task the other machine needs to know about,
- make a decision or change a convention the other machine relies on,
- are blocked and need the other machine to do something.

Post with:
```
python scripts/team_chat.py post --file C:\path\to\message.md
```
Use `--file` (not inline text) for anything longer than a single short line.
For other threads (e.g. Discussion #46), pass `--discussion N`.

### Replying to messages

- Reply inside Discussion #23 to the relevant comment via `gh`:
  ```
  gh api repos/kooshikooo-lab/instrument-designer/discussions/23/comments \
    -f body="your reply" -f reply_to_id=<parent_comment_id>
  ```
- Answer what was asked; if you cannot fully act, state exactly what you did and
  what remains. Do not silently drop a request.

## Protocol rules

1. **Never relay through the human.** If the other machine posted something, act
   on it directly.
2. **Keep the channel canonical.** Decisions made in #23 win. If a conversation
   also happens in a doc or another thread, mirror the binding decision back to #23.
3. **Read docs/CONSTRAINTS_AND_PREFERENCES.md** — it contains the governance
   model, decisions, and Step 0. Do not overwrite it with an older copy.
4. **Never lose work.** If you cannot finish something, leave a checkpoint commit
   or a clearly marked stub, and say so in the channel.
5. **Prefer direct-to-main, then audit.** Commits go to `main`; work lives in
   feature branches that merge into `main`. If a change is provisional, mark it
   for audit in the commit message (e.g. `AUDIT:` prefix) and say so in the channel.
6. **Do not commit regenerable artifacts** (STLs, large JSON dumps, logs). The
   `.gitignore` covers most; check with `git status` before committing.

## Environment

- Repo: `kooshikooo-lab/instrument-designer` (remote: `origin`)
- Channel: Discussion #23 (GraphQL id `D_kwDOTOg0Rs4AoFZO`)
- Git identity: `Admin <kooshikooo@gmail.com>`
- `gh` is authenticated as `kooshikooo-lab`.
- Set `TEAM_MACHINE` to your machine name so sync output is self-identifying.

## If things go wrong

- `python scripts/team_chat.py sync` fails: check `gh auth status` and network.
- You see a merge conflict: resolve it, prefer `main`'s structure where `main`
  intentionally refactored, then commit and post the outcome to #23.
- The other machine is unresponsive: post your message anyway, note the expected
  action, and proceed with what is safe on your side.

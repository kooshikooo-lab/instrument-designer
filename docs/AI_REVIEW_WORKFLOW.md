# AI Review Workflow

This repo can call frontier models via OpenRouter for code review, planning, and
debugging. The script is `scripts/ai_review.py`.

## Why it exists

The user wants to use frontier AIs frequently for high-level planning and deep
debugging without manually copying files into a chat UI. This script packages a
prompt + source files and sends them to an OpenRouter model, then saves the
response.

## Setup

1. Ensure `OPENROUTER_API_KEY` is set in your environment.
   The desktop agent already has this.
2. Install/update requests: `pip install requests` (usually already present).

## Usage

### Review

```powershell
$env:OPENROUTER_API_KEY="..."
python scripts/ai_review.py `
    --prompt docs/AI_REVIEW_PROMPT.md `
    --files backend/benchmark_all.py backend/jax_optimizer.py backend/two_phase_optimizer.py `
    --model nvidia/nemotron-3-super-120b-a12b:free `
    --output docs/AI_REVIEW_NEMOTRON_3_SUPER_120B_OPENROUTER.md
```

### Planning

```powershell
python scripts/ai_review.py `
    --prompt docs/AI_PLANNING_PROMPT.md `
    --model nvidia/nemotron-3-super-120b-a12b:free `
    --output docs/PLAN_2026-08-06.md
```

### Debug a specific file

```powershell
python scripts/ai_review.py `
    --prompt docs/AI_DEBUG_PROMPT.md `
    --files backend/two_phase_optimizer.py `
    --model nvidia/nemotron-3-super-120b-a12b:free `
    --output docs/DEBUG_two_phase_optimizer.md
```

### List available models

```powershell
python scripts/ai_review.py --list-models
```

## Prompt templates

- `docs/AI_REVIEW_PROMPT.md` — full architecture / correctness review
- `docs/AI_PLANNING_PROMPT.md` — high-level planning
- `docs/AI_DEBUG_PROMPT.md` — deep debugging of specific files

## Choosing a model

- `nvidia/nemotron-3-super-120b-a12b:free` — free, large context, good for review
- `google/gemma-4-31b-it:free` — free, but may be rate-limited
- `moonshotai/kimi-k3` — paid; the model that produced the previous review
- `anthropic/claude-opus-5` — paid; high reasoning quality

Free models are sufficient for routine review. Paid frontier models are worth
it for high-stakes planning or tricky debugging.

## Environment variables

- `OPENROUTER_API_KEY` — required
- `OPENROUTER_REFERER` — optional, defaults to the GitHub repo URL
- `OPENROUTER_TITLE` — optional, defaults to "instrument-designer"

## Outputs

Review files are saved in `docs/` with the model name and timestamp. They are
checked into git so both machines can read them. The script adds a header
comment with model, prompt, files, and generation time.

## Note on cost

The script truncates each file to ~12,000 characters by default. For very long
files, narrow the file list or add a file-summarization step before sending.

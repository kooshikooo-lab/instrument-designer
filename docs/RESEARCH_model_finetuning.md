# RESEARCH — Fine-tuning Open-Source Models: code-assistant project (issue #67), general methods, and instrument-design domain

Status: **RESEARCH — reference for future work** (no code changes)
Date: 2026-08-07
Author: laptop (opencode)
Sources: live web research (2026-08-07) + existing repo research/docs
(`docs/RESEARCH_code_assistant_project.md`, `docs/RESEARCH_openwind_fem_and_surrogates.md`,
`docs/RESEARCH_acoustic_metamaterials.md`, `chat-logs/`, `docs/ai-prompt-answers/`,
`backend/tmm_acoustics.py`, `backend/design_desk.py`, `backend/build123d_export.py`).

## Purpose

Research how to fine-tune open-source models (a) for the **code-assistant
project (issue #67)** — a governed, self-hostable assistant for non-coders —
(b) **in general** (methods, tools, cost, evaluation), and (c) **for the
instrument-design domain and this repo** (acoustics, CAD/B-rep code, woodwind
design). This complements `docs/RESEARCH_code_assistant_project.md`, which maps
the *assemble-not-reinvent* stack; here we answer "when and how would we
fine-tune our own models on top of it."

## TL;DR

1. **Fine-tune only after prompting and RAG fail.** The 2026 consensus gate:
   few-shot prompting → RAG (knowledge gap) → only then fine-tune, and only if
   you have ~500+ clean examples. Fine-tuning is for *reliable format /
   domain-language / compressed-behavior* — not for adding knowledge.
2. **The accessible 2026 stack is QLoRA + Unsloth on a consumer GPU.** A 7B
   model fine-tunes in ~6–10 GB VRAM (QLoRA, 4-bit NF4 + paged optimizer); a
   free Colab T4 can do it; 27B-class fits under ~22 GB VRAM. Reported cost:
   ~$0.30–0.50 per 1k examples on rented GPUs; local 3090 = electricity only,
   ~25 min for a 7B run. A documented case study (Gemma 2 9B) took Python code
   accuracy from 42% → 73% for under $15.
3. **Zero-code fine-tuning exists** — LLaMA Factory's Web UI (100+ models) and
   Axolotl's YAML config mean a *non-coder* can run a fine-tune; this matters
   for the code-assistant project's own ethos.
4. **For the code-assistant project**: fine-tune *format/compliance/tool-use*
   behavior (constitution following, structured output, dependency verification
   prompts) using SFT then DPO/RLAIF. The strongest precedent — NVIDIA's NeMo
   "validated coding assistant" — keeps guardrails/CI/traceability fixed and
   drops in a *domain-adapted* model, so fine-tuning never bypasses the policy
   gate. This repo already has a first-class training-data asset: **chat-logs
   (prompt→answer pairs) + `docs/ai-prompt-answers/`**, exactly the data shape
   needed.
5. **For instrument design (directly applicable to this repo):**
   - **CAD-Coder** (open VLM, arXiv 2505.14646) generates editable **CadQuery**
     Python from images — 100% valid syntax, beats GPT-4.5; built from a 163k
     image→code dataset (**GenCAD-Code**). This repo already uses CadQuery +
     build123d, so a GenCAD-Code-style dataset can be synthesized from existing
     models/tests.
   - **"From dialogue to design"** (Computer-Aided Design, 2026-07): fine-tuned
     LLMs automate FreeCAD parametric modeling/sizing; **~2000 samples sufficed**
     for high-accuracy design automation. Mirrors this repo's
     `design_desk.py` / `design_pipeline.py`.
   - **Nature Sci. Rep. 2026**: fine-tuning **DeepSeek-R1-1.5b** on acoustic-
     metamaterial data for forward prediction + inverse design beat a
     conventional ResNet ML model. This is a direct precedent for this repo's
     metamaterial/acoustics work — and the training data already exists here
     (`tmm-6target-result.json`, `flute-calculations.json`, TMM code).
6. **Risks**: catastrophic forgetting (regression check with
   `lm-evaluation-harness`), hallucinated dependencies are *not* fixed by
   fine-tuning (keep the dependency-verification gate), and fine-tuned models
   must be evaluated at target quantization.

## 1. The decision gate: fine-tune only when prompt/RAG fail

Consensus from 2026 guides (Kunal Ganglani; Hélain Zimmermann; BentoML; Noqta):

1. **Can prompting solve it?** Test few-shot with 5–10 examples. If accuracy
   clears your threshold, stop.
2. **Can RAG solve it?** If the gap is *knowledge*, not *format*, build
   retrieval (vector store over docs) first.
3. **Do you have 500+ clean examples?** If not, invest in data collection
   before GPU time. Practical guidance elsewhere: 200–500 high-quality examples
   is a viable starting point for narrow task adapters.
4. **Pick the base model.** Mid-2026 sweet spot for local fine-tuning: Gemma 4
   12B (best bang-per-VRAM) for general tasks; Qwen2.5-Coder-family for code;
   DeepSeek-R1-family for reasoning; a 1T-param open MoE (MiMo-V2.5-Pro, MIT)
   matches Claude Opus-class SWE-bench at 8x lower API cost if self-host
   resources allow.
5. **QLoRA + Unsloth.** Fits 27B in <22 GB VRAM, ~1.6x faster, ~60% less memory
   than stock HF training; QLoRA reaches near-full-fine-tune quality (Guanaco:
   99.3% of ChatGPT on Vicuna, 24 h single GPU).

Fine-tuning is worth it when you need: consistent output format/schema across
thousands of outputs; domain-specific terminology/units the base model gets
wrong; a long system-prompt template compressed into learned behavior; or lower
per-request cost by dropping the giant prompt.

## 2. General fine-tuning landscape (2026)

### Methods

- **Full fine-tuning**: ~12x model size in memory (weights + gradients +
  optimizer states). Only for large domain shifts with big proprietary data.
- **LoRA**: freezes base, trains small low-rank adapters (up to 10,000x fewer
  trainable params). ~18–20 GB VRAM for 7B @16-bit.
- **QLoRA**: adds 4-bit NormalFloat quantization of the frozen base → ~6–10 GB
  VRAM for 7B. Best practice: double quantization with NF4, paged optimizers,
  LoRA on **all layers** (not just q/k/v) for max quality.
- **Alignment stage**: SFT first (format/behavior), then preference
  optimization (DPO/RLHF) or **RLAIF** — self-critique against a constitution,
  which is the same *self-critique-loop* pattern as Constitutional AI and OASB
  v2 governance (§4 of `RESEARCH_code_assistant_project.md`).
- **Adapter composition**: keep separate adapters (`adapter_constitution`,
  `adapter_cad`, `adapter_acoustics`, `adapter_tools`) and load/merge per
  context — fits the multi-agent, multi-domain shape of both projects.

### Tools

| Tool | Notes |
|---|---|
| **Unsloth** | Fastest + lowest memory; Colab-friendly; context-length FT to 500k+ |
| **Axolotl** | YAML-config, Docker, multi-GPU (FSDP/DeepSpeed); full FT/LoRA/QLoRA/ReLoRA |
| **LLaMA Factory** | 100+ models; **Web UI = zero-code fine-tuning** (non-coder accessible) |
| **TRL + PEFT** | HF-native SFT/DPO/chat-format utilities |
| **Torchtune** | PyTorch-native, transparent/reproducible |
| **Ollama / llama.cpp** | Serve the fine-tuned GGUF locally (offline inference) |

### Hardware / cost (2026, per Noqta)

| Setup | GPU | ~Cost / 1k examples | ~Time (7B) |
|---|---|---|---|
| Google Colab Pro | T4 16 GB | ~$0.50 | ~45 min |
| RunPod | RTX 4090 | ~$0.30 | ~20 min |
| Lambda Labs | A100 80 GB | ~$0.15 | ~8 min |
| Local GPU | RTX 3090 | electricity only | ~25 min |

### Evaluation (set up *before* training)

- Hold out 10–15% of data; never train on it.
- Task metric + **regression check** with EleutherAI `lm-evaluation-harness`
  on base vs fine-tuned (catastrophic forgetting).
- Compare against your best prompt baseline; a 2% gain may not justify
  maintaining a custom model.
- **Evaluate at deployment quantization** (e.g. Q4_K_M GGUF), not full
  precision.
- Prefer deterministic gates (schema/format/regression suites) over LLM-judge
  eyeballing.

## 3. Fine-tuning for the code-assistant project (issue #67)

### What to fine-tune (and what not to)

- **Do tune**: constitution/format compliance (structured task specs,
  completion reports, no-touch/no-ship rule adherence), tool-call discipline,
  plain-language explanation to non-coders, and compressing the long
  constitution prompt into reliable behavior.
- **Do NOT rely on fine-tuning for**: factual knowledge (use RAG over repo
  docs), and **hallucinated-dependency prevention** — keep the deterministic
  dependency-resolution gate (NeMo slopsquatting precedent) as a *pipeline*
  guard, not a model behavior.
- **Keep governance outside the model**: NVIDIA's validated-coding-assistant
  tutorial is the template — the NeMo Guardrails proxy refuses human-only paths
  *before* the model is called; a domain-adapted model drops into the pipeline
  without changing guardrails, CI, traceability, or metrics. Same idea as our
  hook-based gates (commit-msg/pre-push) that work regardless of which model is
  driving the agent.

### Training data we already own (a genuine asset)

The issue explicitly asks to record prompts + answers. That is also the SFT
dataset shape. In-repo sources:

- `chat-logs/` (raw prompt→answer pairs), `docs/prompts/` (prompts),
  `docs/ai-prompt-answers/` (topic-archived answers with importance flags)
- `docs/AI_CONSTITUTION.md`, `docs/REMINDERS.md` (behavioral targets)
- `docs/session-logs/BOOT_STATE.md`, `docs/RESEARCH_*.md` (reasoning traces)
- `tests/` + `scripts/` (verifiable format examples for structured output)

Filter to high-quality pairs, dedupe, and format as instruction/chat examples
(role-based, system prompt = constitution excerpt). ~500+ curated examples is
the realistic starting bar.

### Precedents

- **NeMo validated coding assistant** (policy gate + dependency scan +
  traceability + domain-adapted model) — the architectural template.
- **Gemma 2 9B → Python code SFT** (QLoRA, single GPU): 42% → 73% accuracy for
  <$15 — evidence a narrow, well-scoped SFT moves a coding model a lot.
- **Open coding-agent models**: MiMo-V2.5-Pro (MIT, 1T MoE, SWE-bench near
  Claude Opus 4.6 at 8x lower cost) and Xiaomi-adjacent open MoE agents show
  self-hosting a strong coding base is now practical.
- **AGENTS.md / SOUL.md / OASB v2** (from the companion research doc): a
  fine-tuned model still needs a *scanned, graded* governance file (OASB v2
  `hackmyagent scan-soul`) — fine-tuning and governance files are complementary.

## 4. Fine-tuning for instrument design (this repo's domain)

### 4a. CAD / B-rep code generation

- **CAD-Coder** (arXiv 2505.14646; github `anniedoris/CAD-Coder`): open VLM
  fine-tuned to generate **editable CadQuery Python** from images; built on
  **GenCAD-Code** (163k image→code pairs); 100% valid syntax; beats GPT-4.5 and
  Qwen2.5-VL-72B on 3D-solid similarity; some generalization to unseen
  operations. **Directly relevant**: this repo generates instruments with
  CadQuery + build123d (`backend/cadquery_export.py`, `backend/build123d_export.py`,
  `backend/experiments/build123d_koncovka.py`). A repo-scale GenCAD-Code-style
  dataset can be *synthesized* from existing parametric models and their
  rendered/exported geometry + tests.
- **CAD-MLLM** (LoRA fine-tuning for multimodal CAD generation), **BlenderLLM**
  (LLM → CAD scripts → Blender), **CQAsk** (LLM CAD tool): same family, good
  to survey before committing.
- **"From dialogue to design"** (Computer-Aided Design, vol. 196, 104065,
  2026-07, Rosnitschek et al.): fine-tuned LLMs for parameter extraction,
  sizing, and FreeCAD macro-code generation; **~2000 samples sufficient**;
  extended hyperparameters + early stopping improve quality without overhead;
  architecture split into Chatbot / Designbot / Chatbot-Calculator-Code
  Generator. This is the closest published template for automating
  *parametric instrument sizing* (e.g., mapping a target frequency set to
  bore dimensions → CAD code), which is literally this repo's design loop
  (`backend/flute_calculator.py`, `backend/target_frequencies.py`,
  `backend/design_pipeline.py`).

### 4b. Acoustics / metamaterial design (LLM as physics tool)

- **Nature Sci. Rep. 16:517 (2026)** (Jiang et al., DOI
  10.1038/s41598-025-29930-2): two data-driven strategies for acoustic-
  metamaterial design with **no ML expertise required**:
  1. *Agent interaction*: ChatGPT as agent maps structural params ↔ sound
     absorption coefficients via dialogue (forward + inverse design in <1 min);
  2. *LLM fine-tuning*: fine-tuned **DeepSeek-R1-1.5b** on metamaterial datasets
     (mixed fp32/fp16, gradient clip 1.0, batch 3, 3 epochs) — **outperformed a
     conventional ResNet**; continuous fine-tuning turns it into a domain
     specialist.
- Relevance: this repo has `backend/metamaterial_low_clarinets.py`,
  `backend/tmm_acoustics.py` (JAX TMM), and prior acoustics research
  (`docs/RESEARCH_acoustic_metamaterials.md`, `docs/RESEARCH_openwind_fem_and_surrogates.md`).
  The Nature strategy is the *language-level* complement to the repo's numeric
  surrogates (LassoLars descriptor model precedent in the OpenWInD research):
  fine-tune a small OSS LLM to reason about impedance/acoustic behavior and do
  forward/inverse design from natural language.
- Training data exists in-repo: `tmm-6target-result.json`, `flute-calculations.json`,
  plus the TMM/physics backend can synthesize paired (params → impedance/freq)
  rows on demand (which also satisfies "no hallucinated dependencies" — data is
  self-generated from verified physics code).

### 4c. Physics-informed hybrid (recommended shape for this repo)

1. Keep the **JAX TMM / OpenWInD FEM** as the ground-truth computation.
2. Use a fine-tuned **small LLM (e.g., DeepSeek-R1-1.5b or Qwen2.5-Coder)** as
   the natural-language interface + design reasoner (forward/inverse queries,
   explaining choices in plain language to a non-coder).
3. Use the repo's numeric surrogate work (descriptor models) for fast
   intermediate predictions; validate everything against physics code; gate all
   mutations through the existing hooks.

## 5. Risks & guardrails

- **Catastrophic forgetting**: narrow SFT degrades general coding/acoustic
  ability — always run `lm-evaluation-harness` regression + a held-out task set.
- **Hallucinated dependencies / physics nonsense**: fine-tuning does NOT fix
  this. Keep deterministic gates (dependency-resolution scan, physics-solver
  validation, pre-commit hooks) in the pipeline; the model only *proposes*.
- **Data quality**: 200–2000 curated examples beat 100k noisy ones; for this
  repo, synthetic data generated from verified physics/CAD code is preferred
  over scraping.
- **License hygiene**: check base-model + dataset licenses (Gemma, Qwen, DeepSeek,
  CadQuery-derived code). Keep adapters and datasets separately versioned.
- **Evaluation at quantization**: a Q4 model that passes at fp16 may not at
  Q4_K_M — test at deployment precision.
- **Governance unchanged**: a fine-tuned model must still be covered by the
  constitution files and hook gates — fine-tuning is an *executor* improvement,
  not a governance replacement (Law 17: safe local work; approvals for
  shared-state actions remain).

## 6. Recommendation summary

1. **Code-assistant project**: start with prompt+RAG (AGENTS.md-style
   constitution + repo docs); curate 500+ prompt→answer pairs from `chat-logs/`
   and `docs/ai-prompt-answers/`; SFT a small OSS model (LLaMA Factory Web UI
   for zero-code runs) for constitution/format/tool-use discipline; keep the
   NeMo-style policy gate and dependency scan as non-model guards.
2. **Instrument-design domain**: two candidate fine-tunes, both LoRA/QLoRA on a
   single consumer GPU:
   - CAD adapter over a code model (Qwen2.5-Coder class) fine-tuned on
     CadQuery/build123d pairs synthesized from this repo's models — following
     CAD-Coder / "From dialogue to design" (~2000 samples).
   - Acoustics adapter over a small reasoning model (DeepSeek-R1-1.5b class)
     fine-tuned on TMM-generated (params → impedance/frequency) data for
     forward/inverse design — following the Nature 2026 precedent.
3. Evaluate both against held-out physics/CAD test cases and
   `lm-evaluation-harness`; measure at target quantization; version adapters +
   datasets independently; never bypass hooks or the dependency gate.

## 7. Provenance & sources (all fetched/verified 2026-08-07)

- dasroot.net "Fine-Tuning Open Source LLMs with LoRA and QLoRA" (2026-04-13)
- kunalganglani.com "Fine-Tune Open-Source LLMs: LoRA, QLoRA, Gemma 4 [2026]"
  (2026-07-02) — decision checklist, Unsloth+QLoRA stack, Gemma code-gen case study
- helain-zimmermann.com LoRA/QLoRA + RAG integration (2026-02-10)
- noqta.tn "Fine-Tuning LLMs with LoRA & QLoRA: 2026 Developer Guide"
  (2026-05-12) — cost/hardware table
- techbloat.com "Fine-Tune LLMs with LoRA and QLoRA: 2026 Guide" (2026-05-25) —
  TRL/W&B; tech-insider.org LoRA 12-steps (2026-07-24)
- bentoml.com "LLM fine-tuning" (LLM Inference Handbook) — Axolotl/Unsloth/
  Torchtune/LLaMA Factory overview; hosted-FT lifecycle warning
- arXiv 2505.14646 "CAD-Coder" (+ github.com/anniedoris/CAD-Coder);
  CAD-MLLM (cad-mllm.github.io); github.com/FreedomIntelligence/BlenderLLM;
  github.com/OpenOrion/CQAsk
- ScienceDirect S0010448526000357 "From dialogue to design" (Comput.-Aided
  Design, 2026-07)
- Nature Sci. Rep. 16:517 (2026), Jiang et al., DOI 10.1038/s41598-025-29930-2
  "A data-driven design for sound absorption of acoustic metamaterials based on
  large language models"
- NVIDIA blog "How to Self-Host a Validated AI Coding Assistant with NVIDIA
  NeMo Guardrails" (2026-07/08) — policy gate + domain-adapted model drop-in
- effloow.com MiMo-V2.5-Pro open coding agent writeup (2026-05-02)
- EleutherAI `lm-evaluation-harness`; HF PEFT/TRL; Unsloth; Axolotl; LLaMA Factory
- Companion: `docs/RESEARCH_code_assistant_project.md` (stack, governance,
  AGENTS.md/SOUL.md/OASB v2); repo files listed in header for data-source notes

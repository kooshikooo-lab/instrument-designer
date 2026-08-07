# Free AI Coding Assistance Research — 2026-07-23

## TL;DR: Best Options (Ranked)

### 1. OpenRouter Free Models (RECOMMENDED)
- **URL:** https://openrouter.ai
- **Free models:** Kimi K2, DeepSeek R1, Step-3.5-Flash, GPT-OSS-120B
- **Setup:** Get API key, use with Claude Code or any OpenAI-compatible tool
- **Rate limit:** Varies by model, generally generous
- **Quality:** Kimi K2 is surprisingly good for coding

### 2. NVIDIA NIM (40 req/min free)
- **URL:** https://build.nvidia.com/settings/api-keys
- **Models:** GLM-4.7, Kimi K2 Thinking, Step-3.5-Flash
- **Setup:** Get free API key, use with free-claude-code proxy
- **Best for:** Daily driver, generous free tier

### 3. Free.ai (50K tokens/day free)
- **URL:** https://free.ai
- **CLI:** `pip install freeai-code` → `free-code`
- **Models:** Qwen 2.5 Coder 32B (default), 346+ models
- **BYOK:** Bring your own API keys (no markup)
- **Good for:** Terminal coding assistant

### 4. FreeModel ($100 signup bonus)
- **URL:** https://freemodel.dev
- **Bonus:** $100 upfront + $67/week recurring
- **Models:** Claude Opus 4.8, GPT-5, etc. via proxy
- **Setup:** Change ANTHROPIC_BASE_URL to https://api.freemodel.dev
- **Warning:** Credits deplete fast with heavy usage

### 5. Gemini Free Tier + Aider
- **URL:** https://aistudio.google.com/app/apikey
- **Setup:** Get free API key, use with Aider (`pip install aider-chat`)
- **Command:** `export GEMINI_API_KEY=your_key aider --model gemini/gemini-1.5-pro-latest`
- **Best for:** High-quality free coding assistant

### 6. Local Models (Fast Options)
Since Ollama was slow, try these smaller/faster models:

| Model | Size | VRAM | Speed | Quality |
|-------|------|------|-------|---------|
| Qwen2.5-Coder-3B | 3B | ~2GB | ~88 tok/s | Good |
| Qwen3-Coder-30B (MoE) | 30B/3B active | ~22GB | ~220 tok/s | Excellent |
| Gemma 4 26B A4B (MoE) | 26B/4B active | ~12GB | ~136 tok/s | Very good |
| DeepSeek-Coder-Lite | 7B | ~4GB | Fast | Good |

**Recommendation for laptop:** Try Qwen2.5-Coder-3B or Gemma 4 26B A4B (MoE = fast)

## Setup Instructions

### OpenRouter + Claude Code
```json
// .claude/settings.json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://openrouter.ai/api",
    "ANTHROPIC_API_KEY": "your-openrouter-key",
    "ANTHROPIC_MODEL": "open_router/deepseek/deepseek-r1-0528:free"
  }
}
```

### NVIDIA NIM + free-claude-code
```bash
pip install free-claude-code
# Set .env:
# NVIDIA_NIM_API_KEY=nvapi-your-key
# MODEL=nvidia_nim/z-ai/glm4.7
free-claude-code
```

### Free.ai CLI
```bash
pip install freeai-code
free-code config set token sk-free-xxx
free-code  # start coding session
```

## Key Insight
The user tried "pi model with gemini" — this likely means they tried using a Pi (Raspberry Pi?) which is too slow for LLM inference. The laptop needs at minimum 8GB RAM for 3B models, 16GB+ for larger ones.

## Sources
- OpenRouter: https://openrouter.ai
- NVIDIA NIM: https://build.nvidia.com
- Free.ai: https://free.ai
- FreeModel: https://freemodel.dev
- free-claude-code: https://github.com/Ranke84/free-claude-code
- SmallCode agent: https://github.com/Doorman11991/smallcode

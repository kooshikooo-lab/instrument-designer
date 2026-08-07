# AI Assistant Setup & Test Results - 2026-07-23

## OpenRouter Free Models (verified working)
| Model | Speed | Best For | Notes |
|-------|-------|----------|-------|
| cohere/north-mini-code:free | 10-50s | Coding | Clean Python output, 256K ctx |
| openai/gpt-oss-20b:free | 5-30s | Fast queries | Weaker on specialized topics |
| nvidia/nemotron-nano-9b-v2:free | 20s+ | Reasoning | Has reasoning chain |

## Usage
```python
from backend.ai_assistant import get_researcher, get_coder, prepare_research_prompt

# API coding agent
coder = get_coder()
code = coder.generate_code("Write a trumpet impedance evaluator")

# API research agent
researcher = get_researcher()
result = researcher.ask("How does bell flare compress harmonics?")

# Generate prompt for ChatGPT/Claude web interface
prompt = prepare_research_prompt("trumpet valve physics", context_file="trumpet_openwind.py")
# Copy-paste into chatgpt.com or claude.ai
```

## Key API gotcha
Reasoning models return `content: null` with output in `reasoning` field.
Fixed in `_make_request()`: `content = msg.get('content') or msg.get('reasoning')`

## API Key
Set as OPENROUTER_API_KEY environment variable (persistent).
Free tier: ~100 requests/day, no credit card.

## Recommendation
- **Coding**: Use API (Cohere North, integrated into workflow)
- **Deep research**: Use ChatGPT/Claude web interfaces with prepare_research_prompt()
- **Quick questions**: Use API (GPT-OSS, 5s)

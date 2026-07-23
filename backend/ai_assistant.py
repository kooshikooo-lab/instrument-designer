"""
AI Research & Coding Assistant - hybrid approach for maximum free compute.

== Research Agent ==
Best done via web interfaces (stronger models, free):
- ChatGPT free tier: GPT-4o-mini (paste context + question)
- Claude free tier: Claude Sonnet (strong analysis, citations)
- Gemini free: Gemini 2.5 Pro (1M context for large files)
Also via API: nvidia/nemotron-3-ultra-550b (550B, 1M ctx, free on OpenRouter)

== Coding Agent ==
Best done via API (integrated into workflow):
- cohere/north-mini-code:free (code-specialized, 256K ctx)
- poolside/laguna-m.1:free (code-specialized)

== Usage ==
    from backend.ai_assistant import get_researcher, get_coder, prepare_research_prompt
    
    # Automated coding via API
    coder = get_coder()
    code = coder.generate_code("Write a trumpet impedance evaluator")
    
    # Research via API
    researcher = get_researcher()
    result = researcher.ask("How does bell flare compress harmonics?")
    
    # Research via web interface (paste into ChatGPT/Claude)
    prompt = prepare_research_prompt("trumpet valve physics", context_file="trumpet_openwind.py")
    print(prompt)  # Copy-paste into ChatGPT or Claude
"""

import os
import json
import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


# Free model tiers (verified working 2026-07-23)
# Tested speeds: GPT-OSS ~5-30s, Cohere-North ~10-50s, Nemotron-Nano ~20s+
# NOTE: Larger models (550B) time out on free tier. Stick to smaller fast models.
RESEARCH_MODEL = 'cohere/north-mini-code:free'                 # fastest reliable (~10-50s)
CODING_MODEL = 'cohere/north-mini-code:free'                   # code-specialized, 256K ctx
FAST_MODEL = 'openai/gpt-oss-20b:free'                        # fastest (~5s) but weaker
DEEP_MODEL = 'nvidia/nemotron-nano-9b-v2:free'                 # has reasoning chain, ~20s+
# For deep research: use ChatGPT/Claude web interfaces with prepare_research_prompt()


class AIAssistant:
    """AI coding and research assistant using free APIs."""
    
    PROVIDERS = {
        'openrouter': {
            'base_url': 'https://openrouter.ai/api/v1',
            'env_key': 'OPENROUTER_API_KEY',
        },
    }
    
    def __init__(self, provider: str = 'openrouter', model: str = '', api_key: str = ''):
        self.provider = provider
        config = self.PROVIDERS.get(provider, self.PROVIDERS['openrouter'])
        
        self.base_url = config['base_url']
        self.api_key = api_key or os.environ.get(config['env_key'], '')
        self.model = model or RESEARCH_MODEL
        
        # System prompts
        self.code_system = (
            "You are an expert software engineer and acoustician. "
            "Help with Python code, acoustic simulation, instrument design, "
            "and optimization. Be concise and practical. "
            "Always return working code, not pseudocode."
        )
        self.research_system = (
            "You are a research assistant specializing in musical acoustics, "
            "instrument design, and computational modeling. "
            "Cite sources when possible. Be thorough but concise. "
            "Focus on actionable findings and measurable results."
        )
    
    def _make_request(self, messages: List[Dict], model: str = '', 
                      system: str = '', max_tokens: int = 4096) -> str:
        """Make API request to chosen provider."""
        if not self.api_key:
            return f"[ERROR] No API key for {self.provider}. Set {self.PROVIDERS[self.provider]['env_key']} environment variable."
        
        model = model or self.model
        
        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # OpenRouter specific headers
        if self.provider == 'openrouter':
            headers["HTTP-Referer"] = "https://github.com/instrument-designer"
            headers["X-OpenRouter-Title"] = "Instrument Designer AI Assistant"
        
        payload = {
            "model": model,
            "messages": all_messages,
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }
        
        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            msg = data['choices'][0]['message']
            # Reasoning models put output in 'reasoning' field, content=null
            content = msg.get('content') or msg.get('reasoning') or ''
            if not content:
                return f"[ERROR] Empty response from model. Raw: {str(msg)[:200]}"
            return content
        except requests.exceptions.RequestException as e:
            return f"[ERROR] API request failed: {e}"
        except (KeyError, IndexError) as e:
            return f"[ERROR] Unexpected response format: {e}"
    
    def ask(self, question: str, context: str = '') -> str:
        """Ask a general question."""
        content = question
        if context:
            content = f"Context:\n```\n{context[:2000]}\n```\n\nQuestion: {question}"
        
        return self._make_request(
            messages=[{"role": "user", "content": content}],
            system=self.research_system,
        )
    
    def generate_code(self, description: str, language: str = 'python',
                      context: str = '') -> str:
        """Generate code from description."""
        content = f"Write {language} code for: {description}"
        if context:
            content = f"Existing code context:\n```\n{context[:2000]}\n```\n\n{content}"
        
        return self._make_request(
            messages=[{"role": "user", "content": content}],
            system=self.code_system,
        )
    
    def analyze_code(self, code: str, question: str = 'Review this code and suggest improvements') -> str:
        """Analyze existing code."""
        content = f"Code to analyze:\n```\n{code[:4000]}\n```\n\n{question}"
        
        return self._make_request(
            messages=[{"role": "user", "content": content}],
            system=self.code_system,
        )
    
    def debug_error(self, code: str, error: str) -> str:
        """Debug an error."""
        content = (
            f"Code:\n```\n{code[:3000]}\n```\n\n"
            f"Error:\n```\n{error[:1000]}\n```\n\n"
            f"Fix this error and explain what went wrong."
        )
        
        return self._make_request(
            messages=[{"role": "user", "content": content}],
            system=self.code_system,
        )
    
    def research_topic(self, topic: str, existing_findings: str = '') -> str:
        """Research a topic and provide findings."""
        content = f"Research topic: {topic}"
        if existing_findings:
            content += f"\n\nExisting findings to build on:\n{existing_findings[:2000]}"
        content += "\n\nProvide a comprehensive summary with key findings, references, and actionable recommendations."
        
        return self._make_request(
            messages=[{"role": "user", "content": content}],
            system=self.research_system,
            max_tokens=8192,
        )
    
    def optimize_prompt(self, code: str, goal: str) -> str:
        """Get optimization suggestions."""
        content = (
            f"Code to optimize:\n```\n{code[:3000]}\n```\n\n"
            f"Optimization goal: {goal}\n\n"
            f"Suggest specific optimizations with code examples."
        )
        
        return self._make_request(
            messages=[{"role": "user", "content": content}],
            system=self.code_system,
        )
    
    def list_models(self) -> str:
        """List available models."""
        if self.provider == 'openrouter' and self.api_key:
            try:
                resp = requests.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10,
                )
                models = resp.json().get('data', [])
                free = [m['id'] for m in models if ':free' in m['id']]
                return f"Free models ({len(free)}):\n" + "\n".join(free[:20])
            except Exception as e:
                return f"Error listing models: {e}"
        
        return f"Provider: {self.provider}\nFree models: {self.PROVIDERS[self.provider]['free_models']}"


# ============================================================================
# Convenience constructors
# ============================================================================

def get_researcher(model: str = '') -> AIAssistant:
    """Get a research-focused AI assistant (550B model, 1M context)."""
    return AIAssistant(provider='openrouter', model=model or RESEARCH_MODEL)

def get_coder(model: str = '') -> AIAssistant:
    """Get a coding-focused AI assistant (code-specialized model)."""
    return AIAssistant(provider='openrouter', model=model or CODING_MODEL)

def get_fast(model: str = '') -> AIAssistant:
    """Get a fast AI assistant for simple tasks."""
    return AIAssistant(provider='openrouter', model=model or FAST_MODEL)


# ============================================================================
# Web interface helper - generate prompts for ChatGPT/Claude/Gemini
# ============================================================================

def prepare_research_prompt(topic: str, context_file: str = '',
                            context_code: str = '', extra_notes: str = '') -> str:
    """
    Generate a ready-to-paste prompt for web-based AI (ChatGPT, Claude, Gemini).
    
    Usage:
        prompt = prepare_research_prompt(
            "trumpet valve deviation pipe geometry",
            context_file="backend/trumpet_openwind.py"
        )
        print(prompt)  # Copy-paste into ChatGPT/Claude
    """
    parts = [
        f"RESEARCH QUESTION: {topic}",
        "",
    ]
    
    if context_file:
        try:
            with open(context_file, 'r', encoding='utf-8') as f:
                code = f.read()
            # Truncate if too long for web interface
            if len(code) > 8000:
                code = code[:8000] + "\n... [truncated] ..."
            parts.extend([
                "CONTEXT CODE:",
                "```python",
                code,
                "```",
                "",
            ])
        except FileNotFoundError:
            parts.append(f"[Warning: Could not read {context_file}]")
    
    if context_code:
        parts.extend([
            "CONTEXT:",
            "```",
            context_code,
            "```",
            "",
        ])
    
    if extra_notes:
        parts.extend([extra_notes, ""])
    
    parts.extend([
        "Please provide:",
        "1. A clear explanation of the physics/mechanics involved",
        "2. What's likely going wrong and why",
        "3. Specific, actionable fixes with code if applicable",
        "4. Any references to relevant literature",
    ])
    
    return "\n".join(parts)


def save_session_log(filename: str, entries: list):
    """Save a session log for later reference or handoff to laptop."""
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# Session Log: {timestamp}\n\n")
        for entry in entries:
            f.write(f"## {entry.get('title', 'Entry')}\n")
            f.write(f"**Role**: {entry.get('role', 'unknown')}\n")
            f.write(f"**Model**: {entry.get('model', 'unknown')}\n\n")
            f.write(f"{entry.get('content', '')}\n\n---\n\n")
    print(f"Session log saved to {filename}")


# ============================================================================
# Main - quick test
# ============================================================================

if __name__ == "__main__":
    print("=== AI Assistant Module ===\n")
    
    # Test research agent
    researcher = get_researcher()
    print(f"Research model: {researcher.model}")
    print(f"API key: {'SET' if researcher.api_key else 'NOT SET'}")
    
    # Test coding agent
    coder = get_coder()
    print(f"Coding model: {coder.model}")
    
    # Test prompt generator
    print("\n--- Example prompt for ChatGPT/Claude ---")
    prompt = prepare_research_prompt(
        "Why does pressing valve 3 on a trumpet make the resonance go HIGHER instead of lower?",
        extra_notes="Valve 3 deviation pipe is 270mm long, reconnects at 0.82m. "
                    "Main bore total length is 1.335m. Bessel horn bell flare."
    )
    print(prompt[:500])
    
    if researcher.api_key:
        print("\n--- Live API test ---")
        result = researcher.ask("What is 2+2? Reply with just the number.")
        print(f"Response: {result}")
    else:
        print("\nSet OPENROUTER_API_KEY to enable API calls.")

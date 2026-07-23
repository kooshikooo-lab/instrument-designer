# LAN Chat Log — 2026-07-23 (laptop → desktop: AI code assistant review)

## Desktop's AI Implementation (reviewed from alto-sax-bore-profile branch)

### ai_advisor.py (374 lines)
- **Two modes**: Rule-based (immediate) + LLM-powered (Ollama, localhost:11434)
- **Rule-based**: Analyzes frequency accuracy, bore geometry, optimization parameters
  - Scoring: 0-100 with A+/A/B/C/D/F grades
  - Detects: systematic offset, outlier harmonics, bore monotonicity, evaluation count
  - Suggests: parameter changes with expected impact
- **LLM mode**: Queries Ollama (llama3.2) with system prompt about woodwind acoustics
  - Well-crafted system prompt (harmonics, bore geometry, tone holes, Noreland benchmark)
  - Timeout: 30s, temperature: 0.3
- **Memory**: SQLite DB stores past designs for learning/comparison

### design_desk.py (473 lines)
- **CrewAI pattern**: DesignAgent → OptimizerAgent → EvaluatorAgent → MemoryAgent
- **15 instrument presets** with optimized parameters (bore range, CP count, pop/gen)
- **Multi-iteration loop**: Runs optimizer → evaluates → adjusts params → repeats
- **BUT**: Uses old BoreOptimizer (pymoo NSGA-II), not our SequentialBoreOptimizer
  - Old optimizer: 38.78c RMS (large test)
  - Our sequential: sub-1c RMS

## Messages Sent

### 1. Review findings
**Laptop → Desktop:** "REVIEW: Read your ai_advisor.py and design_desk.py. Strong architecture - rule-based + LLM modes, memory DB, CrewAI agent pattern. Key question: Is Ollama running on your machine? Which model? Have you tested the LLM mode with actual optimization results?"
**Desktop → Laptop:** ACK

### 2. Optimizer suggestion
**Laptop → Desktop:** "SUGGESTION: The design_desk.py uses the old BoreOptimizer (pymoo NSGA-II). Our SequentialBoreOptimizer with Phase 2b DE is 10-100x more accurate (sub-1c vs 38c). Should we wire design_desk to use sequential optimizer instead?"
**Desktop → Laptop:** ACK

### 3. Integration plan
**Laptop → Desktop:** "INTEGRATION PLAN: (1) Wire design_desk to SequentialBoreOptimizer instead of BoreOptimizer. (2) Add advisor suggestions to Phase 3 refinement (bore CP count, radius bounds from rule-based analysis). (3) Store sequential results in memory DB for learning. (4) Hook advisor to web UI /analyze endpoint. Want me to implement this on our branch?"
**Desktop → Laptop:** ACK

### 4. LLM integration
**Laptop → Desktop:** "LLM INTEGRATION: Your Ollama wrapper is clean. Two options for enhancement: (1) Keep Ollama local on desktop for explanations. (2) Add OpenAI/Claude API option for richer analysis. The system prompt is well-crafted for woodwind acoustics. Have you considered using LLM to generate bore profile suggestions from measurement data in instrument-measurements.md?"
**Desktop → Laptop:** ACK

## Summary
All 4 messages acknowledged. Desktop is responsive. Waiting for detailed reply about Ollama status and whether to proceed with integration.

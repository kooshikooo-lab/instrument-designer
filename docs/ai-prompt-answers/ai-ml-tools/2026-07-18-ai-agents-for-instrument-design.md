# AI Agents for Instrument Design — Landscape Report

**Date:** 2026-07-18  
**Purpose:** Comprehensive survey of autonomous AI agents that can plan, reason, and execute multi-step instrument design workflows.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [AI Agents That Design Physical Objects](#2-ai-agents-that-design-physical-objects)
3. [LLM Agents With CAD Tool Use](#3-llm-agents-with-cad-tool-use)
4. [Autonomous Research Agents](#4-autonomous-research-agents)
5. [Multi-Agent Systems for Engineering Design](#5-multi-agent-systems-for-engineering-design)
6. [Code-Writing AI Agents for CAD](#6-code-writing-ai-agents-for-cad)
7. [Agent Frameworks (CrewAI, LangGraph, AutoGen, OpenHands)](#7-agent-frameworks)
8. [Voyager-Style Skill-Learning Agents](#8-voyager-style-skill-learning-agents)
9. [AI Agents for Music/Sound Design](#9-ai-agents-for-musicsound-design)
10. [Computer Use Agents for CAD Software](#10-computer-use-agents-for-cad-software)
11. [3D Generation AI (Meshy, Tripo3D, Shap-E, Rodin)](#11-3d-generation-ai)
12. [Google DeepMind GNoME / Materials Science Agents](#12-materials-science-agents)
13. [Agent Frameworks Specifically for Physical Design](#13-agent-frameworks-for-physical-design)
14. [Tauri Desktop App Integration Assessment](#14-tauri-desktop-app-integration)
15. [Recommendations for Instrument Design](#15-recommendations)
16. [Key Links and Resources](#16-links)

---

## 1. Executive Summary

The landscape of AI agents for physical/engineering design has exploded in 2025-2026. The key developments:

- **MEDA** (ASME 2025): Multi-agent framework that achieves 99% script execution success on 200 CAD prompts, with 56% improvement in accuracy over prior work. Uses division of labor across specialized agents. **OPEN SOURCE** — https://github.com/AnK-Accelerated-Komputing/MEDA
- **TO-Agents** (MIT, May 2026): Multi-agent AI pipeline for topology optimization using natural-language design intent → solver → visual critique → revision loop. Produces end-to-end intent-to-prototype designs. Published by Faez Ahmed's group at MIT.
- **Design Agents for Car Design** (IDETC-CIE 2025): Multi-agent framework where VLM agents interpret sketches, LLM agents generate parametric CAD, and simulation agents run CFD — all autonomously.
- **FreeCAD AI** (376 GitHub stars): AI-powered assistant workbench for FreeCAD with plan/act modes, 50+ structured tool operations, skill optimizer, hooks, MCP integration. **OPEN SOURCE, LGPL-2.1** — https://github.com/ghbalf/freecad-ai
- **build123d-mcp**: MCP server exposing build123d CAD operations as tools for AI assistants. Can drive GPT-5 on CADGenBench. **OPEN SOURCE** — https://github.com/pzfreo/build123d-mcp
- **CAD Agent**: Self-contained rendering server that gives AI agents visual feedback for build123d code. **OPEN SOURCE** — https://github.com/Svetlana-DAO-LLC/cad-agent
- **Zoo / Zookeeper**: Conversational CAD agent generating parametric B-rep from natural language. GPU-native kernel. Free to try.
- **MecAgent**: AI CAD copilot for SolidWorks/Inventor. $3M raised. Automates macros, drawing generation, text-to-STEP/STL. **Proprietary, freemium.**
- **VibeCAD (desktop app)**: Local-first, agent-native desktop app wrapping Claude Code/OpenCode/Codex over OpenSCAD or build123d. **OPEN SOURCE** — https://github.com/andrejvysny/vibecad

---

## 2. AI Agents That Design Physical Objects

### 2.1 MEDA — Mechanical Engineering Design Agents
- **What:** Autonomous multi-agent framework using MLLMs to create parametric CAD models
- **How:** Multiple agents with division of labor — one generates code, one analyzes visual output, one refines
- **Results:** 99% script execution success rate on 200 CAD prompts; 56% reduction in point cloud distance vs prior work
- **Open Source:** YES — https://github.com/AnK-Accelerated-Komputing/MEDA
- **Local:** Requires LLM API calls (GPT-4 etc.)
- **Maturity:** Research (published at IDETC-CIE 2025)
- **Tauri Integration:** Could wrap the agent pipeline; needs Python backend for CAD execution

### 2.2 TO-Agents — Topology Optimization Multi-Agent Pipeline
- **What:** Multi-agent AI framework connecting natural-language design intent with iterative topology optimization
- **How:** Converts NL description → validated solver inputs → topology optimization → multi-view vision reasoning → judge agent critiques → parameter revision → manufacturing agent post-processes
- **Results:** 60% preference-aligned designs in 4 revision cycles; 6x more successful than ablated pipeline
- **Open Source:** Research paper (arXiv:2605.21622), code not yet public
- **Local:** Requires LLM API + FEA solver
- **Maturity:** Research (MIT, May 2026)
- **Tauri Integration:** Architecture is directly applicable — could build a multi-agent design loop

### 2.3 Design Agents for Car Design (Elrefaie et al.)
- **What:** Multi-agent framework for aesthetic + aerodynamic car design
- **Agents:** Styling agents (VLM → photorealistic rendering), Geometry agents (LLM → parametric CAD), Simulation agents (automated meshing + CFD)
- **Open Source:** Paper published, code referenced at mohamedelrefaie.github.io
- **Maturity:** Research (IDETC-CIE 2025)
- **Key Insight:** Directly applicable to instrument design — replace "car" with "instrument," replace "aerodynamics" with "acoustics"

### 2.4 Autodesk Neural CAD / Physically-Aware Foundation Models
- **What:** Foundation models embedding physical reasoning into design (forces, materials, motion)
- **How:** AI-first CAD where intent, constraints, and physics are co-represented
- **Status:** Production — claims automates 80-90% of routine design tasks
- **Open Source:** NO (proprietary Autodesk)
- **Maturity:** Production (2025-2026)
- **Tauri Integration:** Would require API access; not local

### 2.5 Siemens Eigen Engineering Agent
- **What:** AI agent for physical-world engineering (announced at Automate 2025)
- **Claims:** 50% productivity gains for manufacturers
- **Maturity:** Production/enterprise
- **Open Source:** NO

---

## 3. LLM Agents With CAD Tool Use

### 3.1 FreeCAD AI Workbench
- **What:** AI assistant workbench for FreeCAD — natural language → 3D models
- **Features:**
  - Chat interface with streaming LLM responses
  - Plan/Act modes (review code before execution)
  - 50 structured FreeCAD operations via tool calling
  - Tool reranking for token efficiency
  - Skills system (reusable instruction sets)
  - Skill optimizer (iterative test-evaluate-modify loop)
  - Hooks for lifecycle events
  - Vision routing (auto-detects LLM vision capability)
  - MCP server integration
  - Supports OpenAI, Anthropic, Ollama (local)
- **Open Source:** YES — LGPL-2.1 — https://github.com/ghbalf/freecad-ai
- **Local:** YES (Ollama support)
- **Maturity:** Alpha (early development, but 318 commits)
- **Tauri Integration:** EXCELLENT — could serve as core engine; FreeCAD runs headlessly, UI via Tauri

### 3.2 build123d-mcp (MCP Server)
- **What:** MCP server exposing build123d CAD operations as tools for AI assistants
- **How:** Agent creates geometry → server renders views → queries dimensions → catches errors
- **Results:** Drives GPT-5 on CADGenBench leaderboard (June 2026)
- **Open Source:** YES — Apache 2.0 — https://github.com/pzfreo/build123d-mcp
- **Local:** YES (Python package)
- **Maturity:** Production-ready MCP server
- **Tauri Integration:** PERFECT — MCP is the ideal protocol for Tauri desktop apps

### 3.3 CAD Agent (Svetlana-DAO-LLC)
- **What:** Self-contained rendering server letting AI agents see what they're building
- **How:** Agent sends HTTP/MCP commands → build123d modeling → VTK rendering → PNG output → agent evaluates
- **Architecture:** Docker container with build123d + VTK
- **Open Source:** YES — https://github.com/Svetlana-DAO-LLC/cad-agent
- **Local:** YES (Docker)
- **Maturity:** Active development (36 commits)
- **Tauri Integration:** EXCELLENT — visual feedback loop for instrument design

### 3.4 FreeCAD MCP Server
- **What:** MCP server connecting Claude/Cursor to FreeCAD for natural-language CAD control
- **Features:** Inspect drawings, list layers, create/edit geometry, measure distances, automate workflows
- **Open Source:** YES (multiple implementations)
- **Local:** YES
- **Maturity:** Active (FreeCAD MCP addon available)
- **Tauri Integration:** EXCELLENT — bridges Tauri frontend to FreeCAD backend

### 3.5 CADAM
- **What:** Open-source web app converting text/images to parametric 3D CAD models
- **How:** Dual-agent AI system — one for conversational interpretation, one for OpenSCAD code generation. In-browser via OpenSCAD-WASM.
- **Features:** Interactive sliders for parameter adjustment, regex-based tweaks without LLM
- **Open Source:** YES — https://github.com/Adam-CAD/CADAM
- **Local:** YES (runs in browser, no server)
- **Maturity:** Active development
- **Tauri Integration:** EXCELLENT — could adapt the WASM approach to Tauri webview

### 3.6 AutoCAD + Claude Connector (Uchuva)
- **What:** Windows plugin connecting AutoCAD with AI assistants via MCP
- **Features:** Natural language to inspect, create, edit AutoCAD drawings
- **Open Source:** NO ($1/month subscription)
- **Local:** YES (runs locally)
- **Maturity:** Production
- **Tauri Integration:** Possible but proprietary

---

## 4. Autonomous Research Agents

### 4.1 DelveAgent
- **What:** Multi-agent framework for autonomous deep research in physical sciences
- **Features:** Adaptive planning, memory architecture for complex multi-step reasoning
- **Results:** Outperforms Gemini Deep Research on PhySciBench (33.5% accuracy baseline)
- **Maturity:** Research
- **Relevance:** Could adapt for instrument design literature research

### 4.2 ArchGen AI (Newton)
- **What:** Self-learning agent for semiconductor physical design
- **How:** Reads reports, identifies root causes, proposes floorplan/flow changes, learns from prior runs
- **Features:** Design memory across runs — preserves context, timing paths, congestion issues
- **Open Source:** NO (startup)
- **Maturity:** Production (ranked #1 in HRT macro placement challenge)
- **Tauri Integration:** Architecture is directly applicable — agent that learns from instrument design iterations

---

## 5. Multi-Agent Systems for Engineering Design

### 5.1 ASME IDETC-CIE 2025: Multi-Agent Car Design Framework
- **Architecture:** Styling agents → Geometry agents → Simulation agents
- **Key Insight:** Agent specialization by design phase
- **Open Source:** Partially (research code)
- **Tauri Integration:** Pattern directly applicable

### 5.2 TO-Agents (Topology Optimization)
- **Architecture:** Description → Solver Setup → TO Solver → Visual Critique → Manufacturing Agent
- **Key Innovation:** Judge agent provides visual feedback with multi-view VLM reasoning
- **Open Source:** Research paper only

### 5.3 Cadence ChipStack AI Super Agent
- **What:** Level-5 autonomous virtual engineer for chip design
- **How:** Evaluates intermediate results, determines next actions, iterates across specification → RTL → verification → simulation → debugging
- **Status:** Production (enterprise)
- **Key Insight:** Demonstrates Level-5 autonomy is achievable in engineering

### 5.4 Multi-Agent Topology Optimization
- **Research Area:** Using RL + multi-agent systems for topology optimization
- **Key Paper:** PPO-based framework achieving 40% weight reduction with manufacturability constraints
- **Tauri Integration:** The TO workflow could be wrapped in Tauri

---

## 6. Code-Writing AI Agents for CAD

### 6.1 VibeCAD (Desktop App)
- **What:** Local-first, agent-native desktop app for 3D parametric CAD
- **How:** Wraps AI coding agents (Claude Code, OpenCode, Codex) over OpenSCAD or build123d modeling backends
- **Architecture:** Chat interface → agent writes/edits model file → backend-specific skill
- **Open Source:** YES — https://github.com/andrejvysny/vibecad
- **Local:** YES
- **Maturity:** Early development
- **Tauri Integration:** EXCELLENT — essentially a Tauri-like app already; could serve as reference architecture

### 6.2 Text2CAD (NeurIPS 2024 Spotlight)
- **What:** First AI framework for text-to-parametric CAD models
- **How:** End-to-end transformer auto-regressive network generating CAD construction sequences from text
- **Dataset:** ~170K models, ~660K text annotations
- **Open Source:** YES (code and annotations public)
- **Local:** Model inference can run locally
- **Maturity:** Research (NeurIPS 2024)
- **Tauri Integration:** Could serve as the generative backend

### 6.3 NURBGen
- **What:** First framework generating high-fidelity 3D CAD models from text using NURBS
- **How:** Fine-tuned LLM translates text → JSON with NURBS parameters → Python BRep conversion
- **Open Source:** Will be released publicly
- **Maturity:** Research (2026)
- **Key Innovation:** Generates actual NURBS geometry, not just meshes

### 6.4 CADSmith
- **What:** Multi-agent CAD generation with programmatic geometric validation
- **How:** Generation agents (Claude Sonnet) + Judge agent (Claude Opus) + RAG over API docs
- **Key Innovation:** VLM Judge with three-view rendered inspection + kernel metrics; no fine-tuning needed
- **Open Source:** Research paper (alphaXiv:2603.26512)
- **Tauri Integration:** Architecture directly applicable

### 6.5 DayDream
- **What:** Browser tool generating OpenSCAD code from LLM with parallel preview
- **Features:** Multi-turn editing, parameter customization widgets, distributed rendering
- **Open Source:** Unclear (web service)
- **Maturity:** Development phase
- **Tauri Integration:** Could adapt to desktop

### 6.6 ParametricPrint
- **What:** Streamlit app — natural language to OpenSCAD via GPT-4
- **Open Source:** YES (MIT) — https://github.com/Rizzy-IRE/ParametricPrint
- **Local:** NO (requires OpenAI API)
- **Maturity:** Prototype
- **Tauri Integration:** Simple to adapt

### 6.7 CAD-Genesis
- **What:** Open-source AI-powered add-in for NL-driven parametric CAD in SolidWorks and Fusion 360
- **Open Source:** YES (MIT license)
- **Maturity:** Academic publication
- **Tauri Integration:** Would need SolidWorks/Fusion API bridge

### 6.8 Zoo / Zookeeper
- **What:** Conversational CAD agent + GPU-native B-Rep kernel + KCL language
- **How:** Natural language → parametric B-rep (not mesh) with feature tree
- **API:** REST + WebSocket (KittyCAD Design API)
- **Open Source:** API free to try; core kernel proprietary
- **Local:** API-based (cloud)
- **Maturity:** Production
- **Tauri Integration:** Could use API; but cloud-dependent

---

## 7. Agent Frameworks

### 7.1 LangGraph (LangChain)
- **What:** Graph-based (nodes, edges, typed state) orchestration for multi-agent systems
- **Production Maturity:** HIGH — largest production deployment footprint in 2026
- **Best For:** Enterprise production, explicit state management, compliance
- **Complex Tasks:** 62% completion rate (8+ steps)
- **Open Source:** YES
- **Local:** YES (with local LLM)
- **Tauri Integration:** EXCELLENT — Python backend, graph-based workflow perfect for design loops

### 7.2 CrewAI
- **What:** Role-based crews with hierarchical collaboration
- **Production Maturity:** MEDIUM — strongest demo-to-prototype ergonomics
- **Best For:** Rapid prototyping, role-based tasks
- **Speed:** 5.76x faster than LangGraph on certain QA tasks
- **Complex Tasks:** 54% completion rate
- **Open Source:** YES (core); commercial managed platform
- **Local:** YES
- **Tauri Integration:** EXCELLENT — define agents by roles (bore designer, simulation agent, evaluator)

### 7.3 Microsoft AutoGen / AG2
- **What:** Conversational agents with debate and verification patterns
- **Status:** Maintenance mode (Oct 2025); successor is Microsoft Agent Framework
- **Best For:** Research, prototyping, human-in-the-loop
- **Complex Tasks:** 58% completion rate
- **Open Source:** YES
- **Tauri Integration:** Good for research prototypes

### 7.4 OpenHands (formerly OpenDevin)
- **What:** Open-source platform for AI software development agents
- **Features:** Terminal access, file editing, web browsing, MCP integration, model-agnostic
- **Results:** 77.6% on SWE-Bench
- **Open Source:** YES (MIT) — https://github.com/OpenHands/OpenHands
- **Local:** YES
- **Maturity:** Beta production (64K+ GitHub stars)
- **Tauri Integration:** EXCELLENT — could adapt for CAD automation tasks

### 7.5 OpenAI Agents SDK
- **What:** Native multi-agent orchestration (launched Feb 2026)
- **Features:** Agents, Handoffs, function tools, tracing
- **Open Source:** YES (MIT)
- **Tauri Integration:** Good — standard API patterns

### 7.6 Google Agent Development Kit (ADK)
- **What:** Modular agent definitions with Vertex AI integration
- **Best For:** GCP-native deployments
- **Tauri Integration:** Moderate (cloud dependency)

---

## 8. Voyager-Style Skill-Learning Agents

### 8.1 Voyager (Original)
- **What:** LLM-powered lifelong learning agent in Minecraft
- **Key Components:**
  1. Automatic curriculum (maximizes exploration)
  2. Skill library of executable code (stores and retrieves complex behaviors)
  3. Iterative prompting with environment feedback + self-verification
- **Results:** 3.3x more unique items; 15.3x faster tech tree milestones
- **Key Insight:** Skills stored as CODE (not natural language); retrieved by embedding similarity
- **Open Source:** YES — https://github.com/MineDojo/Voyager
- **Relevance:** DIRECTLY APPLICABLE to instrument design

### 8.2 Voyager Pattern Applied to CAD
- **Concept:** Agent writes reusable build123d/OpenSCAD functions → stores in skill library → retrieves and composes for new instruments
- **Implementation Path:**
  1. Agent designs instrument component (e.g., bore profile)
  2. Successful design saved as executable skill
  3. Next instrument reuses/composes prior skills
  4. Library grows over time = compounding capability
- **FreeCAD AI Already Has This:** Skills system with `/optimize-skill` command

### 8.3 SAGE (RL + Skill Library)
- **What:** Extends Voyager with reinforcement learning for skill acquisition
- **Innovation:** Skills refined through reward signal, not just success/failure
- **Paper:** arXiv:2512.17102

---

## 9. AI Agents for Music/Sound Design

### 9.1 AI Instruments (Virtual)
- **ACE Studio AI Instruments:** Realistic virtual instrument performances using AI
- **Kits.AI Instruments:** Transform audio into any instrument sound (royalty-free)
- **TwoShot AI Instrument Generator:** Create virtual instruments from audio
- **Relevance:** These are digital sound generation, NOT physical instrument design. But the concept of exploring sound design spaces is relevant.

### 9.2 Suno.AI / AIVA / Boomy
- **What:** AI music composition platforms
- **Relevance:** These generate music, not instruments. But the workflow (describe → generate → iterate) is analogous.

### 9.3 AI Sound Design Tools
- **Neural Synthesizers:** Generate new instruments from training data
- **Voice-to-Instrument Converters:** Transform vocal inputs into instrumental performances
- **Cross-modal Systems:** Generate sounds from images, text, or emotional parameters
- **Relevance:** Could inform acoustic property optimization for physical instruments

### 9.4 Interactive AI Music Installations
- **Examples:** Gesture-controlled piano + AI music + real-time visuals; AI DJ sets; neural beatbox
- **Relevance:** Demonstrates AI understanding of music/sound relationships

### 9.5 Key Gap
**No existing AI agent combines physical instrument design (CAD) with acoustic simulation (sound).** This is the white space your project could fill.

---

## 10. Computer Use Agents for CAD Software

### 10.1 Claude Computer Use
- **What:** Anthropic's desktop agent — sees screen, controls mouse/keyboard
- **Status:** Production (March 2026 launch for Pro/Max subscribers)
- **Cost:** $20-200/month
- **Platforms:** macOS (Windows coming)
- **Benchmark:** 72.5% on OSWorld (up from 42.0%)
- **Security:** Recommended in Docker/VM sandbox
- **CAD Application:** Could control FreeCAD, OpenSCAD, etc. via GUI
- **Limitation:** macOS only currently; screen-based (slow for CAD workflows)

### 10.2 OpenAI Operator (now ChatGPT agent mode)
- **What:** Browser-based desktop automation
- **Status:** Browser-only (not full desktop)
- **Cost:** $200/month (deprecated, now ChatGPT agent mode)
- **CAD Application:** Limited — browser-only

### 10.3 MIT VideoCAD
- **What:** AI agent that learns to use CAD software like a human (click by click)
- **How:** Trained on 41,000+ examples of 3D model construction videos
- **Results:** Translates high-level design commands into precise UI interactions
- **Open Source:** Research paper (NeurIPS 2025)
- **Relevance:** Could train an agent to operate FreeCAD GUI

### 10.4 Claude Skills for FreeCAD
- **What:** Skill package for Claude Code — AI-powered FreeCAD automation
- **Features:** Natural language processing, batch processing, parametric design, marine engineering
- **Install:** `npx skills add https://github.com/vamseeachanta/workspace-hub --skill freecad-automation`
- **Open Source:** YES

### 10.5 Key Insight for Tauri
**Better than Computer Use:** Instead of pixel-based GUI control, use MCP servers that expose CAD operations programmatically. This is faster, more reliable, and doesn't need screen capture. build123d-mcp and FreeCAD-MCP are the right patterns.

---

## 11. 3D Generation AI

### 11.1 Meshy AI
- **What:** Text/image → textured 3D models
- **Users:** 6M+
- **Export:** GLB, OBJ, FBX, USDZ, STL, BLEND
- **Plugins:** Blender, Unity, Unreal
- **Cost:** Free tier + $20/month Pro
- **Open Source:** NO
- **Local:** NO (cloud)
- **Instrument Use:** Could generate concept shapes, but NOT parametric/CAD

### 11.2 Tripo3D
- **What:** 200B+ parameter model; text/image → rigged, textured 3D in ~20 seconds
- **Features:** SmartMesh, 8K textures, clean topology
- **Cost:** Free tier + paid plans
- **Open Source:** NO
- **Local:** NO
- **Instrument Use:** Concept visualization, not engineering CAD

### 11.3 Hyper3D Rodin
- **What:** Highest-fidelity single-image-to-3D conversion
- **Cost:** Free trial + $24/month
- **Open Source:** NO
- **Instrument Use:** Visual concept exploration

### 11.4 OpenAI Shap-E
- **What:** Text/images → 3D (meshes, point clouds, implicit surfaces)
- **Open Source:** YES — https://github.com/openai/shap-e
- **Local:** YES (Python)
- **Maturity:** Research/prototype
- **Instrument Use:** Rapid prototyping concepts; not engineering-grade

### 11.5 OpenAI Point-E
- **What:** Text → point clouds
- **Open Source:** YES
- **Local:** YES
- **Instrument Use:** Early-stage concept exploration

### 11.6 Hunyuan3D
- **What:** Open-source 3D generation from Tencent
- **Open Source:** YES
- **Local:** YES
- **Best For:** Open-source local 3D generation

### 11.7 Zoo (Text-to-CAD)
- **What:** Parametric B-rep from text (NOT mesh — actual CAD)
- **Key Differentiator:** Generates editable parametric CAD with feature tree
- **Open Source:** API free to try; kernel proprietary
- **Instrument Use:** BEST OPTION for generating parametric instrument geometry

### 11.8 Key Distinction
**Mesh generators (Meshy, Tripo, Rodin)** produce triangle meshes — NOT usable for engineering/manufacturing.  
**CAD generators (Zoo, build123d-based agents)** produce parametric B-rep — USABLE for engineering.

---

## 12. Materials Science Agents

### 12.1 Google DeepMind GNoME
- **What:** Graph Networks for Materials Exploration
- **Results:** 2.2 million new crystal structures; 380,000 stable materials
- **Impact:** Multiplied known technologically viable materials by 10x
- **Open Source:** YES — https://github.com/google-deepmind/materials_discovery
- **License:** Apache 2.0
- **Local:** YES (model code available)
- **Maturity:** Research + database (Materials Project)
- **Instrument Relevance:** Could discover novel materials for instrument bodies, reeds, strings, resonators

### 12.2 Microsoft MatterGen
- **What:** Generative model predicting new material structures based on targeted properties
- **Status:** Production research
- **Key Difference from GNoME:** GENERATES materials with desired properties (vs screening)

### 12.3 A-Lab (Berkeley Lab + DeepMind)
- **What:** Autonomous robotic synthesis guided by AI predictions
- **Results:** 71% success rate synthesizing 41 predicted compounds in 17 days
- **Limitation:** Nature correction (Jan 2026) found compounds were largely already catalogued

### 12.4 The Synthesis Gap
- **Key Challenge:** Thermodynamic stability on computer ≠ manufacturable material
- **Current State:** Prediction is cheap; synthesis validation is the bottleneck
- **Instrument Relevance:** GNoME database could be queried for materials with specific acoustic properties

### 12.5 Autonomous Chemical Research
- **Paper:** "Autonomous chemical research with large language models" (Nature 2023)
- **What:** LLM agents that plan and execute chemistry experiments autonomously
- **Relevance:** Pattern applicable to instrument material discovery

---

## 13. Agent Frameworks for Physical Design

### 13.1 Agentic AI for Physical Design R&D (ISPD 2026)
- **Key Paper:** "Invited: Agentic AI for Physical Design R&D: Status and Prospects"
- **Content:** Surveys agentic AI for physical design — tool-integrated agents, autonomous heuristic exploration, multi-agent workflows
- **Key Insight:** Agents can comprehend specs, modify code, run EDA tools, analyze results, reason multi-step, and iteratively refine
- **Tauri Relevance:** Validates the approach of building agent-driven physical design tools

### 13.2 Colab Software — AI Agents for Engineering Design
- **What:** Production-ready AI agents for engineering workflows
- **Types Identified:**
  1. Consistency-critical workflows
  2. Multi-step setup processes
  3. Cross-system data translation
- **Key Insight:** Agents must be workflow-specific with defined triggers and handoff points

### 13.3 NVIDIA GTC 2026 Physical AI
- **What:** Physical AI infrastructure at industrial scale
- **Key Players:** FANUC, ABB, KUKA, Yaskawa integrating Omniverse
- **PTC + NVIDIA:** Cloud CAD → physical simulation via OpenUSD
- **Relevance:** Design-simulation-deploy pipeline becoming seamless

### 13.4 CAD/CAE Copilot (GitHub)
- **What:** AI-native CAD/CAE workbench for agents
- **Features:** Text-to-CAD, text-to-CAE, real build123d/OpenSCAD geometry, editable parameters, MCP server tools
- **Open Source:** YES — https://github.com/armpro24-blip/cad-cae-copilot
- **Tauri Integration:** EXCELLENT — directly applicable

---

## 14. Tauri Desktop App Integration Assessment

### Best Candidates for Tauri Integration (Ranked)

| Tool | Tauri Fit | Why |
|------|-----------|-----|
| **build123d-mcp** | ★★★★★ | MCP protocol is perfect for Tauri IPC; Python backend runs headlessly |
| **FreeCAD AI** | ★★★★★ | FreeCAD headless + Python API; Tauri provides the UI layer |
| **CAD Agent** | ★★★★★ | Docker container with HTTP/MCP; perfect for local Tauri integration |
| **VibeCAD** | ★★★★★ | Already a desktop app wrapping agents over OpenSCAD/build123d |
| **CADAM** | ★★★★☆ | OpenSCAD-WASM runs in webview; zero external deps |
| **CrewAI/LangGraph** | ★★★★☆ | Python orchestration layer; Tauri invokes via sidecar |
| **Shap-E/Point-E** | ★★★☆☆ | Local inference, but mesh output (not parametric) |
| **GNoME** | ★★★☆☆ | Material database + prediction model; useful as reference DB |
| **Zoo API** | ★★☆☆☆ | Cloud-dependent; latency issues |
| **Meshy/Tripo** | ★★☆☆☆ | Cloud-only; mesh output |

### Recommended Architecture for Tauri Instrument Designer

```
┌─────────────────────────────────────────────────────┐
│                  Tauri Desktop App                   │
│  ┌───────────┐  ┌────────────┐  ┌───────────────┐  │
│  │ React UI  │  │ 3D Viewer  │  │ Agent Chat    │  │
│  └─────┬─────┘  └─────┬──────┘  └───────┬───────┘  │
│        └───────────────┼────────────────┘           │
│                        │ IPC                         │
├────────────────────────┼────────────────────────────┤
│                   Rust Core                          │
│  ┌─────────────────────┼─────────────────────────┐  │
│  │     MCP Client ─────┼───► build123d-mcp       │  │
│  │     MCP Client ─────┼───► FreeCAD-MCP         │  │
│  │     MCP Client ─────┼───► CAD-Agent            │  │
│  │     Ollama Client ──┼───► Local LLM            │  │
│  │     GNoME Query ────┼───► Materials DB          │  │
│  └─────────────────────┼─────────────────────────┘  │
│                        │                             │
│  ┌─────────────────────┼─────────────────────────┐  │
│  │    Sidecar: Python  │                          │  │
│  │    - build123d      │                          │  │
│  │    - OpenSCAD       │                          │  │
│  │    - FEA solver     │                          │  │
│  │    - Acoustic sim   │                          │  │
│  └─────────────────────┼─────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 15. Recommendations

### Immediate Actions (Week 1-2)
1. **Clone and test build123d-mcp** — this is the lowest-friction path to agent-driven CAD
2. **Clone and test CAD Agent** — visual feedback loop is critical for autonomous design
3. **Test FreeCAD AI workbench** — 50 structured operations + skills system is powerful
4. **Install VibeCAD** — reference architecture for Tauri-like agent-native CAD app

### Short-Term (Month 1)
1. **Build MCP-based pipeline:** Tauri UI → MCP Client → build123d-mcp → instrument geometry
2. **Integrate Ollama** for local LLM inference (no cloud dependency)
3. **Implement Voyager-style skill library** for instrument design patterns
4. **Query GNoME database** for materials with suitable acoustic properties

### Medium-Term (Month 2-3)
1. **Multi-agent architecture:** Design Agent + Simulation Agent + Materials Agent + Evaluator
2. **Acoustic simulation integration** (COMSOL, OpenFOAM, or custom)
3. **Voyager curriculum:** Agent explores instrument design space autonomously
4. **Build instrument-specific skill library:** bore profiles, reed geometries, resonator shapes

### Long-Term (Month 3+)
1. **Autonomous design loop:** Describe instrument → agent designs → simulates acoustics → iterates → produces manufacturing-ready CAD
2. **Material discovery:** Use GNoME + acoustic property requirements to find novel materials
3. **Multi-physical optimization:** Acoustic performance + structural integrity + manufacturability
4. **Community skill sharing:** Instrument design skills shared across users

---

## 16. Key Links and Resources

### Open Source Projects (High Priority)
| Project | URL | License |
|---------|-----|---------|
| build123d-mcp | https://github.com/pzfreo/build123d-mcp | Apache 2.0 |
| CAD Agent | https://github.com/Svetlana-DAO-LLC/cad-agent | Open Source |
| FreeCAD AI | https://github.com/ghbalf/freecad-ai | LGPL-2.1 |
| VibeCAD | https://github.com/andrejvysny/vibecad | Open Source |
| MEDA | https://github.com/AnK-Accelerated-Komputing/MEDA | Open Source |
| CADAM | https://github.com/Adam-CAD/CADAM | Open Source |
| OpenHands | https://github.com/OpenHands/OpenHands | MIT |
| LangGraph | https://github.com/langchain-ai/langgraph | MIT |
| CrewAI | https://github.com/crewAIInc/crewAI | Open Source |
| GNoME | https://github.com/google-deepmind/materials_discovery | Apache 2.0 |
| Shap-E | https://github.com/openai/shap-e | MIT |
| CAD/CAE Copilot | https://github.com/armpro24-blip/cad-cae-copilot | Open Source |

### Research Papers
| Paper | Venue | Key Contribution |
|-------|-------|-----------------|
| TO-Agents | arXiv:2605.21622 (May 2026) | Multi-agent topology optimization with visual feedback |
| MEDA | IDETC-CIE 2025 | Multi-agent parametric CAD creation |
| Design Agents | IDETC-CIE 2025 | Multi-agent car design (sketch → CAD → CFD) |
| Text2CAD | NeurIPS 2024 | Text-to-parametric CAD transformer |
| NURBGen | 2026 | LLM-driven NURBS CAD generation |
| CADSmith | alphaXiv:2603.26512 | Multi-agent CAD with geometric validation |
| VideoCAD | MIT, NeurIPS 2025 | AI learns to use CAD software via video |
| Agentic AI for Physical Design | ISPD 2026 | Survey of agents in physical design R&D |

### Commercial Tools
| Tool | URL | Pricing |
|------|-----|---------|
| Zoo / Zookeeper | https://zoo.dev | Free to try, API-based |
| MecAgent | https://mecagent.com | Freemium ($0-?) |
| Meshy AI | https://meshy.ai | Free + $20/mo |
| Tripo3D | https://tripo3d.ai | Free + paid |
| VibeCAD (enterprise) | https://vibecad.de | Enterprise pricing |

### MCP Servers for CAD
| Server | Protocol | CAD Backend |
|--------|----------|-------------|
| build123d-mcp | MCP | build123d |
| FreeCAD-MCP | MCP | FreeCAD |
| CAD Agent | HTTP/MCP | build123d + VTK |
| Uchuva AutoCAD | MCP | AutoCAD |
| OpenSCAD-MCP | MCP | OpenSCAD |

---

## Summary: The Gap This Project Fills

**What exists:** Individual AI agents that can generate CAD, run simulations, discover materials, or explore design spaces — but in isolation.

**What doesn't exist (yet):** An integrated multi-agent system that:
1. Takes a high-level description of a novel instrument
2. Decomposes it into acoustic, structural, and aesthetic requirements
3. Designs parametric geometry (bore, reeds, resonator, body)
4. Simulates acoustic properties (frequency response, harmonics, projection)
5. Evaluates against instrument design principles
6. Iterates autonomously using Voyager-style skill accumulation
7. Discovers optimal materials via GNoME-style queries
8. Produces manufacturing-ready parametric CAD

**This is the white space.** No one is combining instrument-specific acoustic knowledge with autonomous multi-agent CAD design. The tools to build this all exist today — they just need to be composed.

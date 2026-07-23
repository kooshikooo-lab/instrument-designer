# Deep Dive: CrewAI + pymoo for AI Instrument Design

**Date:** 2026-07-18
**Purpose:** Research two tools for multi-agent and evolutionary instrument design

---

# Part 1: CrewAI for Multi-Agent Instrument Design

## 1. How CrewAI Works

CrewAI is an open-source Python framework for orchestrating autonomous AI agents. It has two core abstractions:

### Agents
Autonomous units with defined `role`, `goal`, and `backstory`. Each agent can:
- Perform specific tasks
- Make decisions based on its role/goal
- Use tools to accomplish objectives
- Communicate and collaborate with other agents
- Maintain memory of interactions
- Delegate tasks (when `allow_delegation=True`)

Key agent parameters:
```python
agent = Agent(
    role="Acoustic Engineer",
    goal="Design bore geometry for target impedance",
    backstory="Expert in wind instrument acoustics...",
    llm="ollama/llama3.2",            # or "gpt-4o"
    tools=[OpenWInDTool(), FrequencyAnalyzer()],
    allow_delegation=False,
    max_iter=20,
    reasoning=True,                    # enables planning before execution
    memory=True,                       # enables cross-task memory
    max_reasoning_attempts=3,
)
```

### Tasks
Specific assignments with description, expected output, and assigned agent:
```python
task = Task(
    description="Design a soprano saxophone bore with fundamental F4...",
    expected_output="JSON with bore parameters and predicted impedance",
    agent=designer_agent,
    output_pydantic=BoreDesign,        # structured Pydantic output
)
```

Tasks can have:
- `context=[previous_task]` — pass output from prior tasks
- `guardrail=validation_function` — validate output before passing downstream
- `output_json` / `output_pydantic` — enforce structured output
- `human_input=True` — pause for human review

### Crews
Teams of agents executing tasks. Two process types:

```python
# Sequential: tasks run in order, output of one feeds next
crew = Crew(
    agents=[designer, simulator, evaluator],
    tasks=[design_task, sim_task, eval_task],
    process=Process.sequential,
)

# Hierarchical: manager agent delegates and validates
crew = Crew(
    agents=[designer, simulator, evaluator],
    tasks=[design_task, sim_task, eval_task],
    process=Process.hierarchical,
    manager_llm="gpt-4o",  # or custom manager_agent
)
```

### Flows (Production Architecture)
Event-driven orchestration layer that wraps Crews:
```python
class InstrumentDesignFlow(Flow[DesignState]):
    @start()
    def initialize(self):
        self.state.generation = 0
        return {"instrument_type": "soprano_sax"}

    @listen(initialize)
    def design_cycle(self, params):
        design_crew = Crew(agents=[...], tasks=[...], process=Process.sequential)
        return design_crew.kickoff(inputs=params)

    @router(design_cycle)
    def evaluate(self, result):
        if result.score > 0.85:
            return "good_enough"
        return "needs_iteration"

    @listen(or_("needs_iteration", "design_cycle"))
    def iterate(self):
        self.state.generation += 1
        # loop back with feedback
```

Flows support:
- `@start()` — entry points
- `@listen(method_or_string)` — triggered by upstream
- `@router(method)` — conditional routing
- `@human_feedback` — human-in-the-loop gates
- `or_()` / `and_()` — logical composition
- `@persist` — checkpoint/resume

## 2. Custom Tools for CAD/Simulation

Two ways to create tools:

### @tool Decorator (simple)
```python
from crewai.tools import tool
from pydantic import BaseModel

@tool("Compute Input Impedance")
def compute_impedance(bore_diameters: str, bore_lengths: str, temperature: float = 20.0) -> str:
    """Compute the acoustic input impedance of a wind instrument bore given
    diameter and length arrays. Returns JSON with frequency, impedance_magnitude, impedance_phase."""
    import json
    import numpy as np
    from openwind import impedance_computation

    diameters = json.loads(bore_diameters)
    lengths = json.loads(bore_lengths)
    freq, Z = impedance_computation(diameters, lengths, temperature=temperature)
    return json.dumps({"frequency": freq.tolist(), "impedance": Z.tolist()})
```

### BaseTool Class (structured)
```python
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class BoreInput(BaseModel):
    bore_diameters: list[float] = Field(..., description="Diameter at each segment (m)")
    bore_lengths: list[float] = Field(..., description="Length of each segment (m)")
    temperature: float = Field(20.0, description="Temperature in Celsius")

class ImpedanceResult(BaseModel):
    resonances: list[float]
    impedance_curve: list[list[float]]

class OpenWInDTool(BaseTool):
    name: str = "openwind_impedance"
    description: str = "Compute acoustic input impedance of a wind instrument bore using OpenWInD library"
    args_schema: type[BaseModel] = BoreInput
    # output_model can be added for typed output

    def _run(self, bore_diameters, bore_lengths, temperature=20.0) -> str:
        # Call OpenWInD
        from openwind import impedance_computation
        freq, Z = impedance_computation(bore_diameters, bore_lengths, temperature=temperature)
        return json.dumps({"resonances": find_peaks(freq, Z), "curve": [freq.tolist(), Z.tolist()]})

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)
```

### CAD Tool Example
```python
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class CADParams(BaseModel):
    instrument_type: str
    design_variables: dict

class CADTool(BaseTool):
    name: str = "generate_cad_model"
    description: str = "Generate a 3D CAD model of the instrument bore and tone holes"
    args_schema: type[BaseModel] = CADParams

    def _run(self, instrument_type, design_variables) -> str:
        # Use cadquery, FreeCAD, or similar
        import cadquery as cq
        # Build the bore profile
        result = (
            cq.Workplane("XY")
            .lineTo(design_variables["bore_end"], design_variables["length"])
            .revolve()
        )
        # Export STEP file
        cq.exporters.export(result, f"designs/{instrument_type}_bore.step")
        return f"CAD model exported: designs/{instrument_type}_bore.step"
```

## 3. Ollama / Local LLM Integration

CrewAI fully supports Ollama via its `LLM` class, which uses LiteLLM under the hood.

```python
from crewai import LLM, Agent

llm = LLM(
    model="ollama/llama3.2",
    base_url="http://localhost:11434",
    api_key="ollama",        # dummy key, Ollama ignores it
    temperature=0.3,
    timeout=120,
)

agent = Agent(
    role="Acoustic Designer",
    goal="Optimize bore geometry",
    backstory="...",
    llm=llm,
)
```

**Requirements:**
- Ollama v0.5.0+ running (`ollama serve`)
- Model pulled: `ollama pull llama3.2`
- Must set `OPENAI_API_KEY=NA` (CrewAI validates its presence at startup)
- Model name must be exactly `ollama/<model_name>` for LiteLLM routing
- For multi-agent with tools: Qwen 2.5 or Llama 3 work better than smaller models (tool calling support)
- Set `OLLAMA_NUM_PARALLEL=3` for concurrent agent runs
- Increase `num_ctx` to 8192+ for multi-turn agent dialogues

**Best models for tool-heavy agents on Ollama:**
| Task | Recommended Model |
|------|------------------|
| Text-only reasoning | Mistral 7B |
| Tool calling | Qwen 2.5 7B, Llama 3 8B |
| Complex planning | Llama 3 70B (if GPU available) |

## 4. Design Loop Implementation

### Pattern 1: Flow with Iteration (Recommended)
```python
from crewai import Flow, Agent, Crew, Task, Process
from pydantic import BaseModel

class DesignState(BaseModel):
    instrument_type: str = "soprano_sax"
    generation: int = 0
    best_score: float = 0.0
    design_variables: dict = {}
    feedback: str = ""

class InstrumentDesignFlow(Flow[DesignState]):
    @start()
    def design(self):
        designer = Agent(role="Bore Designer", ...)
        task = Task(
            description="Design bore with variables: {design_vars}",
            agent=designer,
            output_pydantic=BoreDesign,
        )
        crew = Crew(agents=[designer], tasks=[task])
        return crew.kickoff(inputs={"design_vars": self.state.design_variables})

    @listen(design)
    def simulate(self, design):
        simulator = Agent(role="Acoustic Simulator", ...)
        task = Task(
            description="Run OpenWInD simulation on this design: {design}",
            agent=simulator,
            output_pydantic=SimulationResult,
        )
        crew = Crew(agents=[simulator], tasks=[task])
        return crew.kickoff(inputs={"design": design})

    @listen(simulate)
    def evaluate(self, sim_result):
        evaluator = Agent(role="Acoustic Evaluator", ...)
        task = Task(
            description="Evaluate this simulation: {sim}",
            context=[],
            agent=evaluator,
            output_pydantic=EvaluationResult,
        )
        crew = Crew(agents=[evaluator], tasks=[task])
        return crew.kickoff(inputs={"sim": sim_result})

    @router(evaluate)
    def decide_next(self, eval_result):
        if eval_result.score > 0.85 or self.state.generation >= 10:
            return "done"
        self.state.feedback = eval_result.feedback
        self.state.generation += 1
        return "iterate"

    @listen("iterate")
    def update_and_redesign(self):
        # Feed feedback back to designer, loop continues
        pass

    @listen("done")
    def finalize(self):
        return self.state
```

### Pattern 2: Self-Evaluation Loop (Official CrewAI Example)
The `crewAI-examples` repo has `flows/self_evaluation_loop_flow` that demonstrates:
1. `GenerateCrew` produces output
2. `ReviewCrew` evaluates it
3. If rejected, flow loops back to `GenerateCrew` with feedback
4. Continues until valid or max retries

### Pattern 3: pymoo Ask/Tell + CrewAI
```python
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import ElementwiseProblem

class InstrumentProblem(ElementwiseProblem):
    def __init__(self):
        super().__init__(n_var=8, n_obj=3, n_ieq_constr=2,
                         xl=np.array([0.003, 0.005, 0.1, 0.001, ...]),
                         xu=np.array([0.020, 0.015, 0.5, 0.005, ...]))

    def _evaluate(self, x, out, *args, **kwargs):
        # Call CrewAI agent for each evaluation
        crew = build_design_crew(x)
        result = crew.kickoff()
        out["F"] = [result.freq_deviation, result.scale_evenness, -result.projection]
        out["G"] = [result.min_wall - 0.001, 0.015 - result.max_bore]

# Use Ask/Tell for custom loop
algorithm = NSGA2(pop_size=40)
algorithm.setup(InstrumentProblem(), termination=('n_gen', 50))

while algorithm.has_next():
    pop = algorithm.ask()
    # Parallel evaluation with CrewAI
    X = pop.get("X")
    F, G = parallel_evaluate(X)  # use multiprocessing
    static = StaticProblem(InstrumentProblem(), F=F, G=G)
    Evaluator().eval(static, pop)
    algorithm.tell(infills=pop)
```

## 5. Real Engineering Examples

CrewAI has been demonstrated for:
- **Multi-agent research pipelines** (researcher → analyst → writer)
- **Code generation and review** (coder → reviewer → fixer)
- **Data analysis workflows** (data collector → analyzer → reporter)
- **Self-evaluation loops** (generate → evaluate → iterate)

For engineering design specifically, the pattern maps to:
- **Design agent** (uses CAD tools, physics knowledge)
- **Simulation agent** (runs FEM/acoustic simulation)
- **Evaluation agent** (compares against targets, scores design)
- **Iteration manager** (adjusts parameters based on feedback)

No published examples of CrewAI specifically for instrument design exist yet, but the architecture directly applies.

## 6. Python Integration Patterns

```python
# Pattern A: Direct Python integration
from crewai import Agent, Task, Crew, Process

designer = Agent(role="Designer", ..., tools=[my_tool])
crew = Crew(agents=[designer], tasks=[task])
result = crew.kickoff(inputs={"bore_type": "conical"})
print(result.pydantic)  # structured output

# Pattern B: As module in larger system
class InstrumentDesignSystem:
    def __init__(self):
        self.memory = Memory(...)  # unified memory
        self.flow = InstrumentDesignFlow()

    def design(self, requirements):
        return self.flow.kickoff(inputs=requirements)

# Pattern C: CLI integration
# crewai run  (reads crew.jsonc, runs all tasks)

# Pattern D: Async for web/production
result = await crew.akickoff(inputs={...})
```

## 7. Memory: Voyager-Style Skill Library

CrewAI's unified `Memory` class (v1.15+) is extremely relevant:

### How It Works
```python
from crewai import Memory, Crew

memory = Memory(
    llm="gpt-4o-mini",
    storage="lancedb",                    # vector DB backend
    recency_weight=0.3,
    semantic_weight=0.5,
    importance_weight=0.2,
    recency_half_life_days=30,
    consolidation_threshold=0.85,         # merge near-duplicates
    exploration_budget=1,                 # depth of recall
)

# Hierarchical scopes (like a filesystem)
memory.remember(
    content="Conical bore with taper ratio 1:1.8 produced best impedance peaks for Bb clarinet",
    scope="/instruments/clarinet/designs",
    importance=0.9,
)

# Recall with composite scoring
results = memory.recall(
    query="bore geometry for clarinet with good intonation",
    scope="/instruments/clarinet",
)
```

### Voyager-Style Pattern for Instrument Design
```python
# After each design iteration
design_memory = Memory(..., scope="/designs/generation_{}".format(gen))

# Extract what worked
memory.remember(
    content=f"Design #{gen}: bore taper 1:{taper_ratio}, "
            f"scale evenness={evenness:.3f}, "
            f"key insight: wider bell improves projection above 2kHz",
    scope="/designs/lessons_learned",
    categories=["acoustic_findings", instrument_type],
)

# Before next design cycle
past_designs = memory.recall(
    f"What bore parameters produced the best scale evenness for {instrument_type}?",
    depth="deep",
)

# Agents get this as context automatically
agent = Agent(
    role="Designer",
    knowledge_sources=[],  # OR use crew-level knowledge
)
crew = Crew(agents=[...], memory=memory, ...)
```

### Atomic Memory Extraction
```python
# After a design task completes
memories = memory.extract_memories(task_output)
for mem in memories:
    memory.remember(mem, scope="/designs/learned_patterns")
```

This is effectively a **Voyager-style skill library** — each successful design is decomposed into atomic facts, stored with scope/importance/recency, and recalled with composite scoring that blends similarity + recency + importance.

## 8. CrewAI vs LangGraph

| Dimension | CrewAI | LangGraph |
|-----------|--------|-----------|
| **Architecture** | Role-based teams, agents/tasks/crews | Graph-based state machine, nodes/edges |
| **Abstraction** | High (roles, goals, stories) | Low (typed state, explicit transitions) |
| **Control flow** | Sequential/hierarchical + Flows | Explicit conditional edges, cycles |
| **State** | Implicit (task outputs) | Explicit typed state object |
| **Checkpointing** | @persist decorator | Built-in at every node |
| **Human-in-the-loop** | @human_feedback decorator | Built-in interrupt nodes |
| **Learning curve** | 1-2 days | 3-5 days |
| **Time to first agent** | 15-30 min | 1-2 hours |
| **Lines of code** | ~50 for 2-agent system | ~80 for equivalent |
| **Debugging** | Verbose logs | Graph state inspection, replay |
| **Best for** | Role-based collaboration | Complex branching, production reliability |

### Recommendation for Instrument Design

**Use CrewAI if:**
- The workflow maps naturally to roles: "designer", "simulator", "evaluator"
- You want rapid prototyping of multi-agent design loops
- The iteration logic is relatively straightforward (design → simulate → evaluate → loop)
- You want fast time to a working prototype

**Use LangGraph if:**
- You need fine-grained control over state transitions
- Complex branching: "if impedance fails, try different bore shape; if scale is uneven, adjust tone hole positions"
- You need checkpointing for long optimization runs
- You want replay/debug capabilities

**Hybrid approach (recommended):**
- Use **pymoo** for the evolutionary optimization loop (it handles population management, crossover, mutation)
- Use **CrewAI** for the "intelligent" parts: interpreting simulation results, suggesting design improvements, explaining trade-offs
- Use **Flows** to orchestrate the overall pipeline: pymoo Ask/Tell → CrewAI evaluation → human feedback → next generation

## 9. Installation & Dependencies

```bash
# Install uv (recommended package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# or
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Install CrewAI CLI
uv tool install crewai

# Create a project
crewai create crew instrument-designer
cd instrument-designer

# Install project dependencies
crewai install

# Key requirements:
# Python >=3.10, <3.14
# openai >= 1.13.3
# pydantic >= 2.11.9
# lancedb >= 0.29.2 (for memory)
# chromadb ~= 1.1.0 (for knowledge)
```

### Key Dependencies (from pyproject.toml)
```
crewai-core==1.15.4
pydantic <2.13,>=2.11.9
lancedb <0.30.1,>=0.29.2
chromadb ~=1.1.0
openai <3,>=2.30.0
litellm <2,>=1.84.0  (for Ollama support)
```

## 10. Tauri/Rust Integration Patterns

CrewAI is Python-only. For Tauri integration:

```rust
// src-tauri/src/main.rs
use tauri::command;

#[command]
async fn run_design_crew(instrument_type: String, design_vars: Vec<f64>) -> Result<String, String> {
    // Call Python via PyO3 or command
    let output = std::process::Command::new("python")
        .arg("scripts/run_crew.py")
        .arg("--instrument")
        .arg(&instrument_type)
        .arg("--vars")
        .arg(serde_json::to_string(&design_vars).unwrap())
        .output()
        .map_err(|e| e.to_string())?;

    Ok(String::from_utf8(output.stdout).unwrap())
}

// Or use PyO3 for direct Python embedding
use pyo3::prelude::*;

#[pyfunction]
fn run_design_crew(py: Python, instrument_type: &str) -> PyResult<String> {
    let crewai = py.import("scripts.run_crew")?;
    let result = crewai.call_method1("run_crew", (instrument_type,))?;
    Ok(result.extract()?)
}
```

**Better pattern: IPC via HTTP**
- Tauri frontend sends HTTP request to a local Python FastAPI server running CrewAI
- CrewAI runs as a background service
- Tauri communicates via fetch/axios
- Supports streaming results via WebSocket

---

# Part 2: pymoo for Evolutionary Instrument Design

## 1. NSGA-II API

### Basic Setup
```python
import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.optimize import minimize

algorithm = NSGA2(
    pop_size=40,
    n_offsprings=10,
    sampling=FloatRandomSampling(),
    crossover=SBX(prob=0.9, eta=15),
    mutation=PM(eta=20),
    eliminate_duplicates=True,
)

res = minimize(
    problem,
    algorithm,
    ('n_gen', 50),
    seed=1,
    save_history=True,
    verbose=True,
)

# Results
X = res.X    # design variables
F = res.F    # objective values
```

### Problem Definition
```python
from pymoo.core.problem import ElementwiseProblem

class InstrumentDesign(ElementwiseProblem):
    def __init__(self):
        super().__init__(
            n_var=8,           # number of design variables
            n_obj=3,           # number of objectives
            n_ieq_constr=2,    # inequality constraints
            n_eq_constr=0,     # equality constraints
            xl=np.array([...]), # lower bounds
            xu=np.array([...]), # upper bounds
        )

    def _evaluate(self, x, out, *args, **kwargs):
        # x is a 1D numpy array of length n_var
        # Write objective values to out["F"]
        # Write constraint violations to out["G"] (must be <= 0)
        out["F"] = [f1, f2, f3]
        out["G"] = [g1, g2]
```

Three problem definition styles:
1. **ElementwiseProblem** — `_evaluate(x, out)` receives one solution at a time (supports parallelization)
2. **Problem** — `_evaluate(X, out)` receives entire population matrix (vectorized, faster)
3. **FunctionalProblem** — define each objective/constraint as a lambda

### Ask/Tell Interface (for custom loops)
```python
algorithm = NSGA2(pop_size=40)
algorithm.setup(problem, termination=('n_gen', 50), seed=1)

while algorithm.has_next():
    pop = algorithm.ask()           # get solutions to evaluate
    X = pop.get("X")               # design variable matrix
    F = evaluate(X)                 # custom evaluation
    static = StaticProblem(problem, F=F)
    Evaluator().eval(static, pop)
    algorithm.tell(infills=pop)     # feed results back

res = algorithm.result()
```

## 2. Instrument Design Variables

```python
# Example: saxophone bore design
design_variables = {
    # Bore geometry
    "bore_start_diameter": (0.005, 0.020),     # m (mouthpiece end)
    "bore_end_diameter": (0.010, 0.040),        # m (bell end)
    "bore_length": (0.3, 0.8),                  # m
    "bore_taper_ratio": (1.0, 3.0),             # end/start diameter

    # Tone holes
    "tone_hole_diameter": (0.003, 0.012),        # m
    "tone_hole_spacing": (0.015, 0.050),         # m
    "num_tone_holes": (6, 20),                   # integer

    # Wall thickness
    "wall_thickness": (0.001, 0.005),            # m

    # Bell
    "bellflare_exponent": (1.0, 4.0),            # bell shape parameter
    "bell_length": (0.05, 0.20),                 # m
}

# pymoo implementation
import numpy as np

class SaxophoneDesign(ElementwiseProblem):
    def __init__(self):
        # [bore_start, bore_end, length, taper, hole_diam, hole_spacing, wall_thick, bell_exponent]
        super().__init__(
            n_var=8,
            n_obj=3,
            n_ieq_constr=3,
            xl=np.array([0.005, 0.010, 0.3, 1.0, 0.003, 0.015, 0.001, 1.0]),
            xu=np.array([0.020, 0.040, 0.8, 3.0, 0.012, 0.050, 0.005, 4.0]),
        )

    def _evaluate(self, x, out, *args, **kwargs):
        bore_start, bore_end, length, taper, hole_diam, hole_spacing, wall_thick, bell_exp = x

        # Build instrument geometry
        bore = build_bore(bore_start, bore_end, length, taper)
        holes = place_tone_holes(bore, hole_diam, hole_spacing)

        # Run acoustic simulation
        freq, Z = compute_impedance(bore, holes, temperature=20.0)
        resonances = find_resonance_peaks(freq, Z)

        # Objectives
        target_freqs = [277.2, 311.1, 349.2, ...]  # Bb clarinet scale
        f1 = np.sum((resonances[:len(target_freqs)] - target_freqs)**2)  # freq accuracy
        f2 = np.std(np.diff(resonances[:len(target_freqs)]))              # scale evenness
        f3 = -np.mean(Z[resonance_indices])                                # projection (negate for max)

        out["F"] = [f1, f2, f3]

        # Constraints
        out["G"] = [
            wall_thick - 0.001,                    # minimum wall thickness
            0.040 - bore_end,                       # maximum bore diameter
        ]
```

## 3. Objectives for Instrument Design

| Objective | What it Measures | pymoo Formulation |
|-----------|------------------|-------------------|
| **Target frequency** | How close resonances are to desired pitches | `f1 = sum((resonances - target)**2)` |
| **Scale evenness** | Uniformity of intervals across the scale | `f2 = std(diff(resonances))` |
| **Projection** | Loudness / radiation efficiency | `f3 = -mean(impedance_at_resonances)` |
| **Ease of blowing** | How low the input impedance peaks are | `f4 = -mean(peak_heights)` (lower peaks = easier) |
| **Intonation** | Deviation from equal temperament | `f5 = max(abs(ratio_errors))` |
| **Tonal richness** | Harmonic content of the sound | `f6 = -spectral_centroid` |

### Constraints
| Constraint | Description | Formulation |
|------------|-------------|-------------|
| Minimum wall thickness | Structural integrity | `wall >= 0.001` → `g1 = 0.001 - wall <= 0` |
| Maximum bore diameter | Manufacturability | `bore <= 0.040` → `g2 = bore - 0.040 <= 0` |
| Total length | Ergonomic limits | `length <= 0.8` |
| Minimum tone hole spacing | Manufacturing constraint | `spacing >= 0.015` |

## 4. pymoo + OpenWInD Integration

OpenWInD is a Python library for wind instrument simulation (from Inria). It computes:
- **Input impedance** (frequency domain) — resonance frequencies
- **Sound simulation** (time domain) — actual audio output

### Integration Pattern
```python
from pymoo.core.problem import ElementwiseProblem
import numpy as np

# OpenWInD import
from openwind import impedance_computation, InstrumentGeometry

class OpenWInDProblem(ElementwiseProblem):
    def __init__(self, target_frequencies, temperature=20.0):
        self.target_freqs = target_frequencies
        self.temperature = temperature
        n_targets = len(target_frequencies)
        super().__init__(
            n_var=6,
            n_obj=3,      # freq_accuracy, evenness, projection
            n_ieq_constr=2,
            xl=np.array([0.005, 0.012, 0.35, 1.5, 0.003, 0.001]),
            xu=np.array([0.018, 0.035, 0.70, 2.5, 0.010, 0.004]),
        )

    def _evaluate(self, x, out, *args, **kwargs):
        bore_start, bore_end, length, taper, hole_diam, wall = x

        # Build geometry for OpenWInD
        # OpenWInD accepts bore shape as a list of (radius, position) pairs
        n_segments = 20
        positions = np.linspace(0, length, n_segments)
        radii = bore_start + (bore_end - bore_start) * (positions / length) ** taper

        geometry = InstrumentGeometry(
            main_bore=list(zip(radii, positions)),
            # tone holes, bell radiation, etc.
        )

        # Compute impedance using OpenWInD
        freq, Z = impedance_computation(geometry, temperature=self.temperature)

        # Find resonance peaks
        from scipy.signal import find_peaks
        peak_indices, _ = find_peaks(np.abs(Z), height=1e6)
        resonances = freq[peak_indices]

        # Match resonances to target scale
        n = min(len(self.target_freqs), len(resonances))
        freq_error = np.sum((resonances[:n] - self.target_freqs[:n])**2) / n
        evenness = np.std(np.diff(resonances[:n])) if n > 1 else 1e6
        projection = -np.mean(np.abs(Z[peak_indices[:n]]))  # higher = better

        out["F"] = [freq_error, evenness, projection]
        out["G"] = [
            0.001 - wall,          # minimum wall thickness
            bore_end - 0.040,      # max bore diameter
        ]
```

### OpenWInD API Notes
```python
# Frequency domain (impedance)
from openwind.impedance_computation import compute_impedance
freq, Z = compute_impedance(bore_profile, temperature=20.0, n_freqs=1000)

# Time domain (sound)
from openwind.sound_simulation import compute_sound
pressure, flow = compute_sound(bore_profile, reed_params, duration=0.5)

# Sensitivity analysis (gradient of impedance w.r.t. geometry)
from openwind.sensitivity import compute_sensitivity
dZ_dgeo = compute_sensitivity(bore_profile, freq_range=[200, 4000])
```

## 5. Parallel Evaluation

pymoo supports parallelization for elementwise problems:

### Starmap (multiprocessing)
```python
from multiprocessing.pool import ThreadPool
from pymoo.parallelization.starmap import StarmapParallelization

# Must set elementwise_evaluation=True in problem
class ParallelInstrumentProblem(ElementwiseProblem):
    def __init__(self):
        super().__init__(..., elementwise_evaluation=True)
        # ... 

# Thread pool (good for I/O-bound OpenWInD calls)
pool = ThreadPool(4)
runner = StarmapParallelization(pool.starmap)
problem = ParallelInstrumentProblem(elementwise_runner=runner)

res = minimize(problem, NSGA2(pop_size=40), ('n_gen', 50))
pool.close()
```

### Joblib (more configurable)
```python
from pymoo.parallelization.joblib import JoblibParallelization

runner = JoblibParallelization(
    n_jobs=4,
    backend="loky",      # process-based
    timeout=30.0,
    batch_size="auto",
)
problem = InstrumentProblem(elementwise_runner=runner)
```

### Custom Parallelization
```python
from concurrent.futures import ProcessPoolExecutor

class CustomParallelProblem(ElementwiseProblem):
    def __init__(self, n_workers=4):
        self.n_workers = n_workers
        super().__init__(...)

    def _evaluate(self, X, out, *args, **kwargs):
        def eval_single(x):
            # OpenWInD simulation
            return compute_objectives(x)

        with ProcessPoolExecutor(max_workers=self.n_workers) as executor:
            results = list(executor.map(eval_single, X))

        out["F"] = np.array([r["F"] for r in results])
        out["G"] = np.array([r["G"] for r in results])
```

### Notes on Parallelization
- **Thread pool** works for I/O-bound simulations (OpenWInD calling C libraries)
- **Process pool** works for CPU-bound pure Python evaluations
- Must use `if __name__ == "__main__":` guard on Windows
- `elementwise_evaluation=True` must be set for starmap/joblib runners
- For mixed variable problems, use custom parallelization (starmap doesn't work with MixedVariableProblem)

## 6. Real Examples of pymoo for Acoustic/Physical Design

### Published Research
1. **Guitar Soundboard Optimization** (Nandalal et al., 2025)
   - Geometric shape optimization of guitar soundboard using parametric reduced-order FEM
   - 7-dimensional parameter space (shape outline, sound hole, length, thickness)
   - Objectives: match target eigenfrequencies and eigenmodes
   - Used mesh morphing + parametric model order reduction for speed

2. **Trumpet Bore Optimization** (Poirson et al., 2006/2007)
   - User-centered design using genetic algorithms
   - Design variables: bore radii r2, r3, r4 of leadpipe sections
   - 5 objectives: deviation from target frequency ratios
   - Used GA with population of 60, produced Pareto front of non-dominated solutions
   - Sensory analysis correlated with acoustic impedance measurements

3. **Metallophone Shape Optimization** (Berg et al., 2015)
   - Optimized 2D/3D shapes to produce target frequency/amplitude spectra
   - Used Latin Complement Sampling for efficient landscape exploration
   - Produced shapes that match professionally manufactured instruments

4. **String Instrument Optimization** (Hellenic Mediterranean University)
   - FEM + ESPI + machine learning for vibroacoustic analysis
   - Studied carbon fiber vs wood bouzouki
   - Parametric optimization of material, geometry, thickness

### OpenWInD Integration Projects
- **TaPAS** (GitHub: alexxior/TaPAS) — physical modelling of saxophones using OpenWInD + CadQuery + FreeCAD
- Plans to use deep learning to predict acoustic properties from geometry (accelerating optimization)
- OpenWInD itself has sensitivity analysis: `compute_sensitivity()` returns gradients of impedance w.r.t. geometry

## 7. Visualization

### Pareto Front (2D)
```python
import matplotlib.pyplot as plt
from pymoo.visualization.scatter import Scatter

# Basic Pareto front
plot = Scatter(title="Instrument Design Pareto Front")
plot.add(res.F, label="Solutions")
plot.show()

# With highlight of selected solutions
plot = Scatter()
plot.add(res.F, s=30, facecolors='none', edgecolors='b')
plot.add(res.F[selected_idx], s=100, color='red', label="Best compromise")
plot.show()
```

### Parallel Coordinates (high-dimensional)
```python
from pymoo.visualization.pcp import PCP

plot = PCP(
    title="Design Variables & Objectives",
    labels=["bore_start", "bore_end", "length", "taper", "freq_err", "evenness", "projection"],
    n_ticks=10,
    legend=(True, {"loc": "upper left"}),
)
plot.set_axis_style(color="grey", alpha=0.5)
plot.add(res.F, color="grey", alpha=0.3)        # all solutions
plot.add(res.F[best_idx], linewidth=3, color="red", label="Selected")
plot.show()
```

### Radar Plot
```python
from pymoo.visualization.radar import Radar

plot = Radar(
    bounds=[ideal_point, nadir_point],
    labels=["Freq Accuracy", "Scale Evenness", "Projection"],
)
plot.add(res.F[:5], color="blue", alpha=0.5)
plot.show()
```

### Convergence Plot
```python
import matplotlib.pyplot as plt
from pymoo.indicators.hv import HV

hv = HV(ref_point=np.array([1.0, 1.0, 1.0]))
n_evals = []
hv_values = []

for algo in res.history:
    n_evals.append(algo.evaluator.n_eval)
    feas = np.where(algo.opt.get("feasible"))[0]
    hv_values.append(hv(algo.opt.get("F")[feas]))

plt.plot(n_evals, hv_values)
plt.xlabel("Function Evaluations")
plt.ylabel("Hypervolume")
plt.title("Convergence")
plt.yscale("log")
plt.show()
```

### Radviz (high-dimensional projection)
```python
from pymoo.visualization.radviz import Radviz

plot = Radviz(
    title="Design Trade-offs",
    labels=["freq_err", "evenness", "projection", "blowing_ease", "intonation"],
)
plot.add(res.F, color="grey", s=20)
plot.add(res.F[best_idx], color="red", s=70, label="Best")
plot.show()
```

## 8. Installation & Dependencies

```bash
# Core installation
pip install pymoo

# With all optional dependencies
pip install 'pymoo[all]'

# Minimal for instrument design
pip install pymoo numpy scipy matplotlib

# For JAX GPU acceleration
pip install pymoo jax jaxlib

# For parallelization
pip install pymoo joblib

# For checkpoints
pip install dill

# Version: pymoo 0.6.2 (latest stable)
# Python: >= 3.8
# NumPy: >= 1.20
# Matplotlib: >= 3.0 (for visualization)
```

## 9. Save/Load Optimization State (Checkpoints)

### Using dill (recommended)
```python
import dill

# Save during optimization
algorithm = NSGA2(pop_size=100)
algorithm.setup(problem, seed=1, termination=('n_gen', 50))

for k in range(10):
    algorithm.next()
    # Save checkpoint every 5 generations
    if k % 5 == 0:
        with open(f"checkpoint_gen_{algorithm.n_gen}.pkl", "wb") as f:
            dill.dump(algorithm, f)

# Load and resume
with open("checkpoint_gen_10.pkl", "rb") as f:
    checkpoint = dill.load(f)

# Set new termination (must extend beyond current generation)
checkpoint.termination = MaximumGenerationTermination(50)

# Resume optimization
res = minimize(problem, checkpoint, seed=1, copy_algorithm=False)
```

### Save full results
```python
# Save complete result object
with open("full_result.pkl", "wb") as f:
    dill.dump(res, f)

# Load later
with open("full_result.pkl", "rb") as f:
    res = dill.load(f)

X, F = res.opt.get("X", "F")
```

### Callback for lightweight tracking
```python
from pymoo.core.callback import Callback

class DesignTracker(Callback):
    def __init__(self):
        super().__init__()
        self.n_evals = []
        self.hv_values = []
        self.best_solutions = []

    def notify(self, algorithm):
        self.n_evals.append(algorithm.evaluator.n_eval)
        opt = algorithm.opt
        if len(opt) > 0:
            self.hv_values.append(hv(opt.get("F")))
            self.best_solutions.append(opt[0].get("X").copy())

tracker = DesignTracker()
res = minimize(problem, algorithm, ('n_gen', 50), callback=tracker)

# tracker.n_evals, tracker.hv_values, tracker.best_solutions are now available
```

## 10. pymoo + JAX Integration

pymoo has built-in JAX support for GPU-accelerated, gradient-aware optimization.

### JAX Problem Definition
```python
import jax.numpy as jnp
import jax
from functools import partial
from pymoo.core.problem import Problem

# Enable float64 for precision
jax.config.update("jax_enable_x64", True)
jax.config.update('jax_disable_jit', False)

class JAXInstrumentProblem(Problem):
    def __init__(self):
        super().__init__(n_var=8, n_obj=3, n_ieq_constr=2,
                         xl=jnp.array([...]), xu=jnp.array([...]))

    def _evaluate(self, x, out, *args, **kwargs):
        _x = jnp.array(x)
        f = self._eval_F(_x)
        g = self._eval_G(_x)
        out["F"] = np.asarray(f)
        out["G"] = np.asarray(g)

    @partial(jax.jit, static_argnums=0)
    def _eval_F(self, x):
        # Vectorized objective evaluation on GPU
        # Example: simplified impedance calculation
        bore_start, bore_end, length, taper = x[0], x[1], x[2], x[3]
        # ... compute resonances using JAX ops ...
        freq_error = jnp.sum((resonances - targets) ** 2)
        evenness = jnp.std(jnp.diff(resonances))
        projection = -jnp.mean(impedance_at_peaks)
        return jnp.array([freq_error, evenness, projection])

    @partial(jax.jit, static_argnums=0)
    def _eval_G(self, x):
        return jnp.array([
            0.001 - x[5],   # wall thickness constraint
            x[1] - 0.040,   # bore diameter constraint
        ])

problem = JAXInstrumentProblem()
```

### Automatic Differentiation
```python
from pymoo.gradient.automatic import AutomaticDifferentiation

# Wraps your problem with auto-differentiation
problem = AutomaticDifferentiation(MyProblem(), backend='jax')

# Now you can get gradients
F, dF = problem.evaluate(X, return_values_of=["F", "dF"])
# dF shape: (n_solutions, n_objectives, n_variables)
```

### pymoo Gradient Backends
```python
# Available backends:
from pymoo.gradient import BACKENDS
# {'numpy': 'numpy', 'autograd': 'autograd.numpy', 'jax': 'jax.numpy'}

# Switch backend
from pymoo.gradient import activate
activate("jax")  # all problems now use JAX for gradients
```

### JAX Benefits for Instrument Design
- **GPU acceleration**: Run 1000+ simulations per second for simple models
- **Automatic differentiation**: Get gradients of impedance w.r.t. geometry for gradient-enhanced algorithms
- **JIT compilation**: First call compiles, subsequent calls are fast
- **Batch processing**: `jax.vmap` for vectorized evaluation of entire populations

### Example: GPU-Accelerated Evaluation
```python
import jax
import jax.numpy as jnp

@jax.jit
def batch_evaluate(X):
    """Evaluate entire population on GPU"""
    # X shape: (pop_size, n_vars)
    bore_starts = X[:, 0]
    bore_ends = X[:, 1]
    lengths = X[:, 2]

    # Vectorized impedance computation
    # (simplified - real implementation would use JAX-based FEM)
    resonances = jax.vmap(compute_resonances)(bore_starts, bore_ends, lengths)

    # Vectorized objective computation
    freq_errors = jnp.sum((resonances - targets) ** 2, axis=1)
    evenness = jnp.std(jnp.diff(resonances, axis=1), axis=1)

    return jnp.column_stack([freq_errors, evenness])
```

---

# Integration Blueprint: CrewAI + pymoo + OpenWInD

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Tauri/Rust Frontend                    │
│              (3D visualization, controls)                │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP/WebSocket
┌─────────────────────▼───────────────────────────────────┐
│                Python FastAPI Server                      │
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │              pymoo NSGA-II (Orchestrator)         │   │
│  │  Ask/Tell interface for custom evaluation loop    │   │
│  │  - Population management                          │   │
│  │  - Crossover, mutation, selection                 │   │
│  │  - Pareto front tracking                          │   │
│  └──────────────┬───────────────────┬───────────────┘   │
│                 │ ask()              │ tell(infills)      │
│  ┌──────────────▼───────────────────▼───────────────┐   │
│  │           Parallel Evaluation Pool                 │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐          │   │
│  │  │ Worker 1│  │ Worker 2│  │ Worker 3│  ...      │   │
│  │  │         │  │         │  │         │           │   │
│  │  │ OpenWInD│  │ OpenWInD│  │ OpenWInD│           │   │
│  │  │ Simulate│  │ Simulate│  │ Simulate│           │   │
│  │  └─────────┘  └─────────┘  └─────────┘          │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │          CrewAI Agents (Intelligence Layer)       │   │
│  │  - Design Advisor: interprets Pareto front        │   │
│  │  - Physics Expert: suggests parameter changes     │   │
│  │  - Evaluation Agent: scores & explains trade-offs │   │
│  │  Memory: stores past designs + lessons learned    │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │           Persistent Storage                       │   │
│  │  - LanceDB: design memory, lessons learned        │   │
│  │  - dill checkpoints: optimization state           │   │
│  │  - SQLite: design history, user preferences       │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Workflow

1. **User specifies requirements** (target scale, instrument type, constraints)
2. **pymoo initializes population** of N random bore designs
3. **Parallel workers evaluate** each design using OpenWInD
4. **pymoo applies selection/crossover/mutation** to produce next generation
5. **CrewAI agents analyze** the Pareto front, identify interesting trade-offs
6. **User selects** preferred design or lets algorithm continue
7. **Memory stores** the design + evaluation + user feedback
8. **Repeat** from step 3 until satisfied

## Key Files

```
instrument-designer/
├── src/
│   ├── problems/
│   │   └── instrument_problem.py    # pymoo ElementwiseProblem
│   ├── tools/
│   │   ├── openwind_tool.py         # CrewAI tool wrapping OpenWInD
│   │   ├── cad_tool.py              # CrewAI tool for CAD generation
│   │   └── frequency_tool.py        # Frequency analysis
│   ├── agents/
│   │   ├── designer_agent.py        # Bore design agent
│   │   ├── simulator_agent.py       # Simulation agent
│   │   └── evaluator_agent.py       # Evaluation agent
│   ├── flows/
│   │   └── design_flow.py           # CrewAI Flow for design loop
│   ├── memory/
│   │   └── design_memory.py         # Voyager-style skill library
│   └── server/
│       └── api.py                   # FastAPI server
├── src-tauri/                       # Tauri frontend
├── checkpoints/                     # dill optimization checkpoints
└── pyproject.toml
```

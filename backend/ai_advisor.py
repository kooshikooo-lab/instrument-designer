"""
ai_advisor.py — AI-powered design advisor for woodwind instruments.

Analyzes optimization results, bore profiles, and impedance data to provide
actionable suggestions for improving intonation accuracy.

Supports two modes:
1. Rule-based (no LLM needed): heuristic analysis of optimization results
2. LLM-powered (Ollama/GPT): natural language explanations via CrewAI-style agents

The rule-based mode works immediately. The LLM mode activates when Ollama
is running locally (default: http://localhost:11434).

Architecture follows the CrewAI pattern from chat-logs/2026-07-18-crewai-pymoo-deep-dive.md:
- AcousticAdvisor: analyzes frequency accuracy and bore geometry
- DesignReviewer: evaluates trade-offs and suggests parameter changes
- MemoryStore: remembers past designs for learning
"""

import json
import os
import sqlite3
import math
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional


# ── Design Memory ────────────────────────────────────────────────────────

MEMORY_DB = Path(__file__).parent.parent / "design_memory.db"


def _init_memory_db():
    """Create design memory table if it doesn't exist."""
    conn = sqlite3.connect(str(MEMORY_DB))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS designs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            instrument_type TEXT,
            target_frequencies TEXT,
            bore_profile TEXT,
            n_control_points INTEGER,
            pop_size INTEGER,
            n_generations INTEGER,
            frequency_accuracy REAL,
            scale_evenness REAL,
            projection REAL,
            n_evaluations INTEGER,
            bore_length REAL,
            suggestions TEXT,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()


def store_design(design_data: dict):
    """Store an optimization result in design memory."""
    _init_memory_db()
    conn = sqlite3.connect(str(MEMORY_DB))
    conn.execute("""
        INSERT INTO designs (
            instrument_type, target_frequencies, bore_profile,
            n_control_points, pop_size, n_generations,
            frequency_accuracy, scale_evenness, projection,
            n_evaluations, bore_length, suggestions, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        design_data.get("instrument_type", ""),
        json.dumps(design_data.get("target_frequencies", [])),
        json.dumps(design_data.get("bore_profile", [])),
        design_data.get("n_control_points", 0),
        design_data.get("pop_size", 0),
        design_data.get("n_generations", 0),
        design_data.get("frequency_accuracy", 0),
        design_data.get("scale_evenness", 0),
        design_data.get("projection", 0),
        design_data.get("n_evaluations", 0),
        design_data.get("bore_length", 0),
        json.dumps(design_data.get("suggestions", [])),
        design_data.get("notes", ""),
    ))
    conn.commit()
    conn.close()


def get_design_history(limit: int = 20) -> list[dict]:
    """Retrieve recent designs from memory."""
    _init_memory_db()
    conn = sqlite3.connect(str(MEMORY_DB))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM designs ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_best_design(instrument_type: str = "") -> Optional[dict]:
    """Get the best design (lowest frequency_accuracy) optionally filtered by type."""
    _init_memory_db()
    conn = sqlite3.connect(str(MEMORY_DB))
    conn.row_factory = sqlite3.Row
    if instrument_type:
        row = conn.execute(
            "SELECT * FROM designs WHERE instrument_type = ? ORDER BY frequency_accuracy ASC LIMIT 1",
            (instrument_type,),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT * FROM designs ORDER BY frequency_accuracy ASC LIMIT 1"
        ).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Rule-Based Advisor ──────────────────────────────────────────────────

@dataclass
class AdvisorSuggestion:
    category: str          # "parameter", "geometry", "strategy", "warning"
    priority: str          # "high", "medium", "low"
    title: str
    description: str
    action: str            # suggested action
    impact: str            # expected impact estimate


@dataclass
class AdvisorResult:
    score: float           # 0-100 quality score
    grade: str             # A/B/C/D/F
    suggestions: list[AdvisorSuggestion] = field(default_factory=list)
    analysis: str = ""
    comparison: dict = field(default_factory=dict)


def _cents_to_error_hz(freq: float, cents: float) -> float:
    """Convert cents error to Hz error."""
    return freq * (2 ** (cents / 1200) - 1)


def analyze_optimization_result(result: dict, target_frequencies: list[float]) -> AdvisorResult:
    """
    Analyze an optimization result and produce suggestions.

    This is the core rule-based advisor. It examines:
    - Frequency accuracy (RMS and per-harmonic)
    - Bore geometry (length, radius range, monotonicity)
    - Optimization parameters (pop_size, n_generations, control_points)
    - Convergence behavior
    """
    suggestions = []
    analysis_parts = []

    best = result.get("best_candidates", [{}])[0] if result.get("best_candidates") else {}
    matched = best.get("matched_frequencies", [])
    bore = best.get("bore_profile", [])
    objectives = best.get("objectives", {})

    freq_accuracy = objectives.get("frequency_accuracy", 999)
    scale_evenness = objectives.get("scale_evenness", 999)
    n_evals = result.get("n_evaluations", 0)
    bore_length = result.get("bore_length", 0)
    n_gen = result.get("n_generations", 0)

    # ── Score calculation ──
    if freq_accuracy <= 1:
        score, grade = 95 + min(5, 1 - freq_accuracy) * 5, "A+"
    elif freq_accuracy <= 3:
        score, grade = 80 + (3 - freq_accuracy) / 2 * 15, "A"
    elif freq_accuracy <= 5:
        score, grade = 65 + (5 - freq_accuracy) / 2 * 15, "B"
    elif freq_accuracy <= 10:
        score, grade = 45 + (10 - freq_accuracy) / 5 * 20, "C"
    elif freq_accuracy <= 20:
        score, grade = 25 + (20 - freq_accuracy) / 10 * 20, "D"
    else:
        score, grade = max(0, 25 - freq_accuracy / 5), "F"

    # ── Frequency accuracy analysis ──
    if matched:
        errors = [m.get("error_cents", 0) for m in matched]
        abs_errors = [abs(e) for e in errors]
        mean_abs = sum(abs_errors) / len(abs_errors) if abs_errors else 0
        max_err = max(abs_errors) if abs_errors else 0
        rms = math.sqrt(sum(e ** 2 for e in errors) / len(errors)) if errors else 0

        # Check for systematic offset (all same sign)
        positive = sum(1 for e in errors if e > 0)
        negative = sum(1 for e in errors if e < 0)
        if positive == len(errors) or negative == len(errors):
            suggestions.append(AdvisorSuggestion(
                category="warning",
                priority="high",
                title="Systematic pitch offset detected",
                description=f"All {len(errors)} harmonics are {'sharp' if positive == len(errors) else 'flat'}. "
                           f"This indicates a global bore length error, not a shape problem.",
                action="Adjust bore length: the instrument is systematically "
                      f"{'sharp (reduce length)' if positive == len(errors) else 'flat (increase length)'}. "
                      f"A ~0.1mm change shifts pitch by ~1-3 cents.",
                impact="Could reduce RMS error by 50-80%"
            ))

        # Check for individual outliers
        for m in matched:
            err = abs(m.get("error_cents", 0))
            if err > mean_abs * 2:
                suggestions.append(AdvisorSuggestion(
                    category="geometry",
                    priority="medium",
                    title=f"Harmonic at {m.get('target', 0):.0f} Hz has large error ({m.get('error_cents', 0):.1f} cents)",
                    description=f"This harmonic is {err / mean_abs:.1f}x worse than average. "
                               f"The bore shape may not support this frequency well.",
                    action="Increase control points to allow more bore flexibility at this region, "
                          "or check if this harmonic is naturally weak for this instrument type.",
                    impact="Could reduce peak error by 30-50%"
                ))

        analysis_parts.append(
            f"Frequency accuracy: {freq_accuracy:.2f} cents RMS, "
            f"mean |error|: {mean_abs:.1f} cents, max: {max_err:.1f} cents"
        )

    # ── Bore geometry analysis ──
    if bore:
        radii = [p.get("radius", 0) if isinstance(p, dict) else (p[1] if isinstance(p, (list, tuple)) else 0) for p in bore]
        positions = [p.get("position", 0) if isinstance(p, dict) else (p[0] if isinstance(p, (list, tuple)) else 0) for p in bore]

        if radii:
            min_r = min(radii) * 1000  # to mm
            max_r = max(radii) * 1000
            r_range = max_r - min_r

            analysis_parts.append(f"Bore: {bore_length * 1000:.0f}mm long, radius {min_r:.1f}-{max_r:.1f}mm")

            # Check monotonicity
            monotonic = all(radii[i] <= radii[i + 1] for i in range(len(radii) - 1))
            if not monotonic:
                n_violations = sum(1 for i in range(len(radii) - 1) if radii[i] > radii[i + 1])
                suggestions.append(AdvisorSuggestion(
                    category="geometry",
                    priority="high",
                    title="Bore is not monotonically increasing",
                    description=f"{n_violations} radius decrease(s) detected. Woodwind bores should "
                               f"generally taper outward (increasing radius toward bell).",
                    action="Add monotonicity constraint or increase smoothness penalty. "
                          "Non-monotonic bores are hard to manufacture and often acoustically worse.",
                    impact="Improves manufacturability and often improves intonation"
                ))

            # Check if bore uses its radius range effectively
            if r_range < 1.0:
                suggestions.append(AdvisorSuggestion(
                    category="geometry",
                    priority="medium",
                    title="Narrow bore radius range",
                    description=f"Radius varies only {r_range:.1f}mm ({min_r:.1f} to {max_r:.1f}). "
                               f"Most woodwinds have a wider taper.",
                    action="Increase max_radius or decrease min_radius constraints. "
                          "A wider taper gives more acoustic control.",
                    impact="More design freedom for the optimizer"
                ))

    # ── Optimization parameter analysis ──
    n_cp = len(bore) if bore else 0

    if n_evals < 200:
        suggestions.append(AdvisorSuggestion(
            category="strategy",
            priority="high",
            title=f"Low evaluation count ({n_evals})",
            description="The optimizer hasn't explored enough of the design space. "
                       "Noreland (2013) used ~2000 evaluations for 0.49 cents RMS.",
            action=f"Increase population to {max(40, n_evals // 2)} and generations to "
                  f"{max(20, n_evals // 10)} for {max(400, n_evals * 2)}+ evaluations.",
            impact="Likely to improve accuracy by 30-60%"
        ))
    elif n_evals < 500:
        suggestions.append(AdvisorSuggestion(
            category="strategy",
            priority="medium",
            title=f"Moderate evaluation count ({n_evals})",
            description="Getting into useful territory. Most improvement happens in the first 500-1000 evaluations.",
            action="Try pop=40, gen=30 for 1200 evaluations. Enable parallel mode for speed.",
            impact="Could push below 2 cents RMS"
        ))

    if n_cp < 8:
        suggestions.append(AdvisorSuggestion(
            category="parameter",
            priority="medium",
            title=f"Few control points ({n_cp})",
            description="The bore profile has limited flexibility. Complex instruments need more DOF.",
            action="Increase to 12-16 control points for more bore shape flexibility.",
            impact="More expressive bore profiles, better intonation"
        ))
    elif n_cp > 20:
        suggestions.append(AdvisorSuggestion(
            category="parameter",
            priority="low",
            title=f"Many control points ({n_cp})",
            description="High DOF risks overfitting and jagged bores. Ensure smoothness constraint is active.",
            action="Add smoothness constraint penalizing large radius jumps between adjacent points.",
            impact="Smoother bore, easier to manufacture"
        ))

    # ── Compare to best-known ──
    best_known = get_best_design()
    comparison = {}
    if best_known and best_known.get("frequency_accuracy"):
        prev_acc = best_known["frequency_accuracy"]
        if freq_accuracy < prev_acc:
            comparison["improvement"] = f"{((prev_acc - freq_accuracy) / prev_acc * 100):.1f}%"
            comparison["previous_best"] = prev_acc
            analysis_parts.append(f"Improvement over previous best: {comparison['improvement']}")

    # ── Sort suggestions by priority ──
    priority_order = {"high": 0, "medium": 1, "low": 2}
    suggestions.sort(key=lambda s: priority_order.get(s.priority, 99))

    return AdvisorResult(
        score=round(score, 1),
        grade=grade,
        suggestions=suggestions,
        analysis="; ".join(analysis_parts),
        comparison=comparison,
    )


# ── Sequential Optimizer Adapter ────────────────────────────────────────

def analyze_sequential_result(result: dict, target_frequencies: list[float]) -> AdvisorResult:
    """
    Analyze a SequentialBoreOptimizer result and produce suggestions.

    Translates SequentialBoreOptimizer output format to the internal
    analysis format. Adds sequential-specific suggestions for:
    - Hole spacing quality (gaps between adjacent holes)
    - Diameter consistency across holes
    - Phase 2b DE improvement potential
    - Bore radius uniformity
    """
    suggestions = []
    analysis_parts = []

    rms = result.get("final_rms_cents", 999)
    peak = result.get("peak_error_cents", 999)
    bore_length = result.get("bore_length_mm", 0)
    bore_radii = result.get("bore_radii", [])
    hole_positions = result.get("hole_positions", [])
    hole_diameters = result.get("hole_diameters", [])
    matched = result.get("matched_frequencies", [])
    wall_time = result.get("wall_time", 0)

    # ── Score from RMS ──
    if rms <= 0.5:
        score, grade = 95 + min(5, (0.5 - rms) / 0.1 * 5), "A+"
    elif rms <= 1:
        score, grade = 85 + (1 - rms) / 0.5 * 10, "A"
    elif rms <= 3:
        score, grade = 70 + (3 - rms) / 2 * 15, "B"
    elif rms <= 10:
        score, grade = 50 + (10 - rms) / 7 * 20, "C"
    elif rms <= 20:
        score, grade = 30 + (20 - rms) / 10 * 20, "D"
    else:
        score, grade = max(0, 30 - rms / 2), "F"

    # ── Frequency accuracy analysis ──
    if matched:
        errors = [m.get("error_cents", 0) for m in matched]
        abs_errors = [abs(e) for e in errors]
        mean_abs = sum(abs_errors) / len(abs_errors) if abs_errors else 0
        max_err = max(abs_errors) if abs_errors else 0

        positive = sum(1 for e in errors if e > 0)
        negative = sum(1 for e in errors if e < 0)
        if positive == len(errors) or negative == len(errors):
            suggestions.append(AdvisorSuggestion(
                category="warning",
                priority="high",
                title="Systematic pitch offset detected",
                description=f"All {len(errors)} harmonics are {'sharp' if positive == len(errors) else 'flat'}. "
                           f"This indicates a global bore length error.",
                action="Adjust bore length by ~0.1mm per 1-3 cents of offset. "
                      f"Current length: {bore_length:.1f}mm.",
                impact="Could reduce RMS error by 50-80%"
            ))

        for m in matched:
            err = abs(m.get("error_cents", 0))
            if err > mean_abs * 2 and err > 1.0:
                suggestions.append(AdvisorSuggestion(
                    category="geometry",
                    priority="medium",
                    title=f"Note at {m.get('target', 0):.0f} Hz has large error ({m.get('error_cents', 0):.1f}c)",
                    description=f"This note is {err / max(mean_abs, 0.01):.1f}x worse than average. "
                               f"May indicate a hole position or diameter issue.",
                    action="Check hole spacing around this note's position. Consider increasing "
                          "diameter bounds or adding a refinement stage.",
                    impact="Could reduce peak error by 30-50%"
                ))

        analysis_parts.append(
            f"RMS: {rms:.2f}c, Peak: {peak:.2f}c, "
            f"mean |error|: {mean_abs:.1f}c"
        )

    # ── Sequential-specific: hole spacing analysis ──
    if len(hole_positions) >= 2:
        gaps = [hole_positions[i+1] - hole_positions[i] for i in range(len(hole_positions)-1)]
        mean_gap = sum(gaps) / len(gaps)
        max_gap = max(gaps)
        min_gap = min(gaps)
        gap_ratio = max_gap / max(min_gap, 1)

        if gap_ratio > 3:
            suggestions.append(AdvisorSuggestion(
                category="geometry",
                priority="high",
                title="Uneven hole spacing detected",
                description=f"Gaps range from {min_gap:.0f}mm to {max_gap:.0f}mm "
                           f"(ratio {gap_ratio:.1f}x). Large gaps can cause "
                           f"register breaks where TMM can't find resonances.",
                action="Run Phase 2b DE again with adjusted bounds to redistribute "
                      "holes more evenly. Try tighter bounds on large gaps.",
                impact="Could reduce RMS by 50-90% for open-open instruments"
            ))

        # Check clustering (two holes very close)
        if min_gap < 15:
            suggestions.append(AdvisorSuggestion(
                category="geometry",
                priority="medium",
                title="Holes clustered too close",
                description=f"Minimum gap is only {min_gap:.0f}mm between holes. "
                           f"This may cause cross-fingering issues and is hard to 3D print.",
                action="Increase minimum hole spacing constraint to 15-20mm "
                      "and re-optimize.",
                impact="Better printability and cross-fingering behavior"
            ))

        analysis_parts.append(f"Holes: {len(hole_positions)} at mean gap {mean_gap:.0f}mm")

    # ── Diameter analysis ──
    if len(hole_diameters) >= 2:
        dia_range = max(hole_diameters) - min(hole_diameters)
        if dia_range > 3:
            suggestions.append(AdvisorSuggestion(
                category="geometry",
                priority="low",
                title="Large hole diameter variation",
                description=f"Diameters range {min(hole_diameters):.1f}-{max(hole_diameters):.1f}mm "
                           f"(range {dia_range:.1f}mm). Large variation complicates manufacturing.",
                action="Narrow diameter bounds or add a smoothness penalty on diameters "
                      "to encourage more uniform sizes.",
                impact="Simpler manufacturing, similar acoustic performance"
            ))

    # ── Bore radius analysis (if profile has multiple segments) ──
    if len(bore_radii) >= 2:
        rad_range = max(bore_radii) - min(bore_radii)
        if rad_range < 0.5:
            suggestions.append(AdvisorSuggestion(
                category="parameter",
                priority="low",
                title="Nearly uniform bore radius",
                description=f"Bore radii vary only {rad_range:.1f}mm. "
                           f"A tapered bore can improve intonation.",
                action="Enable bore profile optimization (n_bore_cp > 0) "
                      "to allow non-uniform bore shape.",
                impact="Moderate intonation improvement for complex instruments"
            ))

    # ── Speed analysis (optional) ──
    if rms > 1 and wall_time > 60:
        suggestions.append(AdvisorSuggestion(
            category="strategy",
            priority="low",
            title=f"Optimization took {wall_time:.0f}s",
            description=f"RMS of {rms:.2f}c achieved in {wall_time:.0f}s. "
                       f"The sequential optimizer converges quickly.",
            action="If this accuracy is acceptable, consider reducing DE "
                  "maxiter or popsize for faster iteration.",
            impact="Faster design iteration"
        ))

    # ── Compare to best-known ──
    best_known = get_best_design()
    comparison = {}
    if best_known and best_known.get("frequency_accuracy"):
        prev_acc = best_known["frequency_accuracy"]
        if rms < prev_acc:
            improvement = ((prev_acc - rms) / prev_acc * 100)
            if improvement > 0:
                comparison["improvement"] = f"{improvement:.1f}%"
                comparison["previous_best"] = prev_acc
                analysis_parts.append(f"Improvement over previous best: {comparison['improvement']}")

    priority_order = {"high": 0, "medium": 1, "low": 2}
    suggestions.sort(key=lambda s: priority_order.get(s.priority, 99))

    return AdvisorResult(
        score=round(score, 1),
        grade=grade,
        suggestions=suggestions,
        analysis="; ".join(analysis_parts),
        comparison=comparison,
    )


def sequential_result_for_llm(result: dict) -> dict:
    """Translate SequentialBoreOptimizer result to format expected by get_llm_suggestion."""
    return {
        "best_candidates": [{
            "bore_profile": [
                {"position": i * 10, "radius": r}
                for i, r in enumerate(result.get("bore_radii", []))
            ],
            "matched_frequencies": result.get("matched_frequencies", []),
            "objectives": {
                "frequency_accuracy": result.get("final_rms_cents", 0),
                "scale_evenness": 0,
            },
        }],
        "n_evaluations": max(100, int(result.get("wall_time", 0) * 2)),
        "n_generations": 1,
        "bore_length": result.get("bore_length_mm", 0) / 1000.0,
    }


# ── LLM-Powered Advisor (Optional) ──────────────────────────────────────

OLLAMA_BASE = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")


def _query_ollama(prompt: str, model: str = "llama3.2") -> Optional[str]:
    """Query Ollama for a natural language response. Returns None if unavailable."""
    import urllib.request
    import urllib.error

    try:
        data = json.dumps({
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 1024}
        }).encode()
        req = urllib.request.Request(
            f"{OLLAMA_BASE}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result.get("response", "")
    except (urllib.error.URLError, ConnectionRefusedError, TimeoutError):
        return None


def _check_ollama_available() -> dict:
    """Check if Ollama is running and what models are available."""
    import urllib.request
    import urllib.error

    try:
        with urllib.request.urlopen(f"{OLLAMA_BASE}/api/tags", timeout=5) as resp:
            data = json.loads(resp.read())
            models = [m.get("name", "") for m in data.get("models", [])]
            return {"available": True, "models": models}
    except (urllib.error.URLError, ConnectionRefusedError):
        return {"available": False, "models": []}


ADVISOR_SYSTEM_PROMPT = """You are an expert woodwind instrument acoustician and design advisor.
You help analyze bore optimization results and suggest improvements.

Key facts about woodwind acoustics:
- Cylindrical closed pipes (clarinets) produce only odd harmonics: f, 3f, 5f, 7f...
- Cylindrical open pipes (flutes) produce all harmonics: f, 2f, 3f, 4f...
- Conical bores (saxophones, oboes) produce all harmonics even when closed
- Bore length determines fundamental pitch (longer = lower)
- Bore taper (radius profile) affects intonation between harmonics
- Bell radiation affects projection and upper register response
- Tone hole placement affects venting and cross-fingerings

When analyzing optimization results:
1. Check if systematic offset exists (all harmonics sharp/flat → bore length issue)
2. Check which harmonics have largest errors (specific bore regions need adjustment)
3. Check if bore is monotonic (non-monotonic = manufacturing problem)
4. Suggest specific parameter changes with expected impact
5. Reference Noreland 2013 (0.49 cents RMS) as accuracy benchmark

Be concise and actionable. Focus on the highest-impact improvements first."""


def get_llm_suggestion(optimization_result: dict, target_frequencies: list[float],
                       model: str = "llama3.2") -> Optional[str]:
    """Get an LLM-powered analysis of optimization results."""
    best = optimization_result.get("best_candidates", [{}])[0] if optimization_result.get("best_candidates") else {}
    matched = best.get("matched_frequencies", [])

    context = f"""Analyze this woodwind bore optimization result:

Target frequencies: {target_frequencies} Hz
Bore length: {optimization_result.get('bore_length', 0) * 1000:.1f} mm
N evaluations: {optimization_result.get('n_evaluations', 0)}
N generations: {optimization_result.get('n_generations', 0)}

Matched frequencies:
"""
    for m in matched:
        context += f"  Target: {m.get('target', 0):.1f} Hz, Actual: {m.get('actual', 0):.1f} Hz, Error: {m.get('error_cents', 0):.1f} cents\n"

    context += f"""
Objectives:
  Frequency accuracy: {best.get('objectives', {}).get('frequency_accuracy', 0):.2f} cents RMS
  Scale evenness: {best.get('objectives', {}).get('scale_evenness', 0):.4f}

Provide a concise analysis with:
1. What's working well
2. Top 3 improvement suggestions (most impactful first)
3. Recommended parameter changes for the next optimization run"""

    prompt = f"{ADVISOR_SYSTEM_PROMPT}\n\n{context}"
    return _query_ollama(prompt, model)


def get_advisor_status() -> dict:
    """Check advisor capabilities."""
    ollama = _check_ollama_available()
    history = get_design_history(limit=5)
    return {
        "rule_based": True,
        "llm_available": ollama["available"],
        "llm_models": ollama["models"],
        "ollama_url": OLLAMA_BASE,
        "memory_designs": len(history),
        "memory_db": str(MEMORY_DB),
    }

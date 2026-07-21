"""
test_integration.py — Integration test for all new desktop features.

Run this to verify everything works:
    python test_integration.py

Tests:
1. Target frequency generation
2. SVG export
3. AI advisor (rule-based)
4. Design desk agent
5. Server endpoints (if server running)
"""

import sys
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

PASS = 0
FAIL = 0


def test(name, fn):
    global PASS, FAIL
    try:
        result = fn()
        if result is not False:
            print(f"  PASS  {name}")
            PASS += 1
        else:
            print(f"  FAIL  {name}")
            FAIL += 1
    except Exception as e:
        print(f"  FAIL  {name}: {e}")
        FAIL += 1


def test_target_frequencies():
    print("\n[1] Target Frequencies")
    from backend.target_frequencies import get_targets, get_preset_info, freq_from_note

    test("freq_from_note(C4)=261.6", lambda: abs(freq_from_note("C4") - 261.6) < 0.1)
    test("freq_from_note(Bb3)=233.1", lambda: abs(freq_from_note("Bb3") - 233.1) < 0.1)

    clarinet_targets = get_targets("clarinet_Bb", fundamental=233.1, n_notes=6)
    test("clarinet_Bb has 6 targets", lambda: len(clarinet_targets) == 6)
    test("clarinet_Bb first target is fundamental", lambda: abs(clarinet_targets[0] - 233.1) < 0.1)
    test("clarinet_Bb second target is 3x fundamental", lambda: abs(clarinet_targets[1] - 699.3) < 0.5)
    test("clarinet_Bb targets are odd harmonics", lambda: all(clarinet_targets[i] / 233.1 == 2*i+1 for i in range(6)))

    whistle_targets = get_targets("folk_whistle", fundamental=293.7, n_notes=6)
    test("folk_whistle has 6 targets", lambda: len(whistle_targets) == 6)
    test("folk_whistle targets are all harmonics", lambda: all(abs(whistle_targets[i] / 293.7 - (i+1)) < 0.1 for i in range(6)))

    preset = get_preset_info("clarinet_Bb")
    test("get_preset_info returns data", lambda: preset is not None)
    test("get_preset_info has targets", lambda: len(preset["targets"]) > 0)


def test_svg_export():
    print("\n[2] SVG Export")
    from backend.svg_export import bore_to_svg, bore_to_cross_section_svg

    profile = [[0, 0.005], [0.1, 0.006], [0.2, 0.007], [0.3, 0.008]]
    svg = bore_to_svg(profile, "Test Bore", [0.05, 0.15], [0.003, 0.004])

    test("SVG is string", lambda: isinstance(svg, str))
    test("SVG starts with <svg", lambda: svg.strip().startswith("<svg"))
    test("SVG contains title", lambda: "Test Bore" in svg)
    test("SVG contains hole markers", lambda: "#ff6b6b" in svg)
    test("SVG contains bore line", lambda: "#00d4ff" in svg)

    cross_svg = bore_to_cross_section_svg(profile, "Test Cross")
    test("Cross-section SVG is valid", lambda: cross_svg.strip().startswith("<svg"))

    empty_svg = bore_to_svg([], "Empty")
    test("Empty SVG is valid", lambda: empty_svg.strip().startswith("<svg"))


def test_ai_advisor():
    print("\n[3] AI Advisor")
    from backend.ai_advisor import analyze_optimization_result, store_design, get_design_history

    result = {
        "best_candidates": [{
            "bore_profile": [{"position": i * 0.05, "radius": 0.005 + i * 0.0003} for i in range(6)],
            "objectives": {"frequency_accuracy": 5.0, "scale_evenness": 0.01},
            "matched_frequencies": [
                {"target": 261.6, "actual": 261.5, "error_cents": -0.6},
                {"target": 784.8, "actual": 784.0, "error_cents": -1.8},
            ],
        }],
        "bore_length": 0.3,
    }
    targets = [261.6, 784.8]

    analysis = analyze_optimization_result(result, targets)
    test("analysis has score", lambda: hasattr(analysis, "score"))
    test("analysis has grade", lambda: hasattr(analysis, "grade"))
    test("analysis has suggestions", lambda: hasattr(analysis, "suggestions"))
    test("score is numeric", lambda: isinstance(analysis.score, (int, float)))
    test("grade is string", lambda: isinstance(analysis.grade, str))

    test("store_design works", lambda: store_design({
        "instrument_type": "test",
        "target_frequencies": targets,
        "bore_profile": [],
        "n_control_points": 6,
        "pop_size": 10,
        "n_generations": 5,
        "frequency_accuracy": 5.0,
        "scale_evenness": 0.01,
        "n_evaluations": 50,
        "bore_length": 0.3,
    }))

    history = get_design_history(5)
    test("get_design_history returns list", lambda: isinstance(history, list))
    test("history has entries", lambda: len(history) > 0)


def test_design_desk():
    print("\n[4] Design Desk Agent")
    from backend.design_desk import DesignDesk, INSTRUMENT_CONFIGS

    test("INSTRUMENT_CONFIGS has entries", lambda: len(INSTRUMENT_CONFIGS) > 0)
    test("clarinet_Bb in configs", lambda: "clarinet_Bb" in INSTRUMENT_CONFIGS)
    test("folk_whistle in configs", lambda: "folk_whistle" in INSTRUMENT_CONFIGS)

    progress = []
    desk = DesignDesk(on_progress=lambda msg: progress.append(msg))
    result = desk.auto_design("folk_whistle", max_iterations=1, max_total_evals=50)
    test("auto_design returns result", lambda: hasattr(result, "best_accuracy"))
    test("result has log", lambda: len(result.log) > 0)
    test("result has iterations", lambda: len(result.iterations) > 0)
    test("progress was captured", lambda: len(progress) > 0)


def test_server_endpoints():
    print("\n[5] Server Endpoints")
    import urllib.request
    import urllib.error

    base = "http://localhost:8000"
    try:
        urllib.request.urlopen(f"{base}/health", timeout=2)
    except (urllib.error.URLError, OSError):
        print("  SKIP  Server not running — skipping endpoint tests")
        return

    test("GET /health", lambda: urllib.request.urlopen(f"{base}/health", timeout=5).status == 200)
    test("GET /design-desk/instruments", lambda: urllib.request.urlopen(f"{base}/design-desk/instruments", timeout=5).status == 200)
    test("GET /advisor/status", lambda: urllib.request.urlopen(f"{base}/advisor/status", timeout=5).status == 200)


def main():
    print("=" * 60)
    print("INTEGRATION TEST — Desktop Features")
    print("=" * 60)

    test_target_frequencies()
    test_svg_export()
    test_ai_advisor()
    test_design_desk()
    test_server_endpoints()

    print("\n" + "=" * 60)
    print(f"RESULTS: {PASS} passed, {FAIL} failed")
    print("=" * 60)

    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

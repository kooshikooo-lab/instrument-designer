"""End-to-end test of the optimization pipeline.

Tests: ClarinetBuilder → BoreOptimizer → FingeringOptimizer → TMMSolver
"""
import sys, os
import numpy as np
import copy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.instruments.clarinet import ClarinetBuilder
from backend.optimization.bore_optimizer import BoreOptimizer
from backend.optimization.fingering_optimizer import FingeringOptimizer
from backend.solvers.tmm_solver import TMMSolver
from backend.core.network import Port, NodeType


def build_bass_clarinet_network():
    """Build a 7-hole bass clarinet: 1200mm bore, 12.5mm radius."""
    builder = ClarinetBuilder()
    builder.set_bore(length=1200, radius=12.5)

    hole_positions = np.linspace(400, 1050, 7).tolist()
    hole_radii = [3.5] * 7
    hole_lengths = [3.0] * 7

    builder.add_toneholes(hole_positions, hole_radii, hole_lengths)
    builder.set_register_vent(position=80, radius=2.5, length=3.0)

    return builder.build()


def create_bell_first_fingering_sets(n_ports=8):
    """Bell-first ascending: open from LAST index (nearest bell) first.

    Port order (sorted reed→bell):
      0: register vent (80mm) — always closed in chalumeau
      1–7: toneholes (400→1050mm)
    """
    sets = []
    for n_open in range(n_ports):
        f = ["closed"] * n_ports
        for i in range(n_open):
            f[n_ports - 1 - i] = "open"
        sets.append(f)
    return sets


def main():
    print("=" * 60)
    print("E2E Optimization Pipeline Test")
    print("=" * 60)

    targets = [73.4, 82.4, 92.5, 98.0, 110.0, 123.5, 138.6, 146.8]

    # ---- 1. Build network ----
    print("\n[1] Building bass clarinet network...")
    network = build_bass_clarinet_network()
    n_th = len([p for p in network.ports if p.node_type == NodeType.TONEHOLE])
    n_rv = len([p for p in network.ports if p.node_type == NodeType.REGISTER_VENT])
    print(f"    Bore: {network.total_length} mm, radius: 12.5 mm")
    print(f"    Ports: {n_th} toneholes + {n_rv} register vent")
    for p in network.ports:
        print(f"      pos={p.position:.0f}mm  r={p.radius:.1f}mm  type={p.node_type.value}")

    # ---- 2. Fingering sets ----
    print("\n[2] Bell-first ascending fingering sets (chalumeau register):")
    fingering_sets = create_bell_first_fingering_sets(len(network.ports))
    for i, fs in enumerate(fingering_sets):
        open_idx = [j for j, s in enumerate(fs) if s == "open"]
        label = f"indices {open_idx}" if open_idx else "none"
        print(f"    Note {i}: {label} open")

    # ---- 3. Baseline physics ----
    print("\n[3] Baseline physics (before optimization):")
    solver = TMMSolver()
    wl_targets = [network.speed_of_sound / f for f in targets]
    baseline_freqs = solver.compute_frequencies(network, wl_targets, fingering_sets, 1)
    for i, (t, f) in enumerate(zip(targets, baseline_freqs)):
        cents = 1200 * np.log2(f / t)
        print(f"    Note {i}: target {t:.1f} Hz  actual {f:.1f} Hz  ({cents:+.1f} cents)")

    ascending = all(
        baseline_freqs[i] < baseline_freqs[i + 1]
        for i in range(len(baseline_freqs) - 1)
    )
    print(f"    Monotonic pitch rise: {'PASS' if ascending else 'FAIL'}")

    # ---- 4. BoreOptimizer ----
    print("\n[4] Running BoreOptimizer (bore length only)...")
    bore_opt = BoreOptimizer(
        network=network,
        target_frequencies=targets,
        fingering_sets=fingering_sets,
        n_register=1,
        bore_length_bounds=(900, 1500),
    )
    bore_result = bore_opt.optimize()
    bore_len = bore_result.parameters["bore_length"]
    print(f"    Optimized bore length: {bore_len:.1f} mm")
    print(f"    Cost (RMS cents):      {bore_result.cost:.2f}")
    print(f"    Evaluations: {bore_result.n_evaluations}  wall time: {bore_result.wall_time:.1f}s")
    print(f"    Converged: {bore_result.success}")

    # ---- 5. Update network with optimised bore ----
    optimized_network = copy.deepcopy(network)
    optimized_network.segments[0].length = bore_len
    optimized_network.boundary_bell.position = bore_len

    # ---- 6. FingeringOptimizer ----
    print("\n[5] Running FingeringOptimizer (hole positions)...")
    fing_opt = FingeringOptimizer(
        network=optimized_network,
        target_frequencies=targets,
        fingering_sets=fingering_sets,
        n_register=1,
    )
    fing_result = fing_opt.optimize()
    hole_pos = fing_result.parameters["hole_positions"]
    print(f"    Optimized hole positions: {[f'{p:.1f}' for p in hole_pos]}")
    print(f"    Cost (RMS cents):        {fing_result.cost:.2f}")
    print(f"    Evaluations: {fing_result.n_evaluations}  wall time: {fing_result.wall_time:.1f}s")
    print(f"    Converged: {fing_result.success}")

    # ---- 7. Build final network, compute final frequencies ----
    print("\n[6] Final intonation (after both optimisers):")
    final_network = copy.deepcopy(optimized_network)
    orig_th = [p for p in network.ports if p.node_type == NodeType.TONEHOLE]
    new_ports = []
    for i, pos in enumerate(hole_pos):
        new_ports.append(Port(
            position=pos,
            radius=orig_th[i].radius,
            length=orig_th[i].length,
            is_open=True,
            node_type=NodeType.TONEHOLE,
        ))
    for p in final_network.ports:
        if p.node_type == NodeType.REGISTER_VENT:
            new_ports.append(p)
    new_ports.sort(key=lambda p: p.position)
    final_network.ports = new_ports

    final_freqs = solver.compute_frequencies(
        final_network, wl_targets, fingering_sets, 1
    )

    cents_errors = []
    for i, (t, f) in enumerate(zip(targets, final_freqs)):
        cents = 1200 * np.log2(f / t)
        cents_errors.append(cents)
        print(f"    Note {i}: target {t:.1f} Hz  actual {f:.1f} Hz  ({cents:+.1f} cents)")

    cents_arr = np.array(cents_errors)
    offset = np.median(cents_arr)
    rms = float(np.sqrt(np.mean((cents_arr - offset) ** 2)))
    peak = float(np.max(np.abs(cents_arr - offset)))

    print(f"\n    Global offset:      {offset:+.1f} cents")
    print(f"    RMS error (relative): {rms:.1f} cents")
    print(f"    Peak error (relative): {peak:.1f} cents")

    ascending_final = all(
        final_freqs[i] < final_freqs[i + 1]
        for i in range(len(final_freqs) - 1)
    )
    print(f"    Monotonic pitch rise: {'PASS' if ascending_final else 'FAIL'}")

    # ---- 8. Summary ----
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Bore length:    {bore_len:.1f} mm")
    print(f"  Hole positions: {[f'{p:.1f}' for p in hole_pos]}")
    print(f"  RMS cents:      {rms:.1f}")
    print(f"  Peak cents:     {peak:.1f}")
    pipeline_ok = bore_result.success and fing_result.success
    print(f"  Pipeline:       {'PASS' if pipeline_ok else 'PARTIAL (review needed)'}")
    print(f"  Physics check:  {'PASS' if ascending_final else 'FAIL'}")


if __name__ == "__main__":
    main()

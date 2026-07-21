"""Quick test of L-BFGS-B two-phase optimizer."""
import sys
sys.path.insert(0, '.')


def main():
    from backend.bore_optimizer_lbfgs import LBFGSBoreOptimizer

    targets = [261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6]
    opt = LBFGSBoreOptimizer(
        targets,
        n_control_points=12,
        bore_length=0.66,
        min_radius=0.005,
        max_radius=0.020,
        seed=42,
    )
    result = opt.run(verbose=True, phase2=True)
    print()
    print("FINAL: {:.4f} cents RMS in {:.1f}s".format(result["rms_cents"], result["wall_time"]))


if __name__ == "__main__":
    main()

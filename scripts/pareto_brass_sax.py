import sys, os, json, time
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.pareto_optimizer import pareto_sweep
from backend.jax_optimizer import refine_sequential, safe_eval
from backend.stl_export import make_capped_bore

os.makedirs("test_output/instruments", exist_ok=True)

def gen_stl(cfg, label, stl_filename, wall_mm, L, radii, hp, hd, hl):
    n_profile = 128
    profile_pos = np.linspace(0, float(L), n_profile)
    radii_arr = np.array(list(radii))
    if len(radii_arr) == 6:
        cp_pos = np.linspace(0, float(L), 6)
        profile_radii = np.interp(profile_pos, cp_pos, radii_arr)
    else:
        cp_pos = np.linspace(0, float(L), len(radii_arr))
        profile_radii = np.interp(profile_pos, cp_pos, radii_arr)

    hole_diam = float(cfg["hole_diameter"]) if cfg.get("hole_diameter") else None
    if hole_diam and hp:
        for hpos in sorted(hp):
            idx = int(hpos / max(float(L), 1.0) * (n_profile - 1))
            if 0 <= idx < n_profile:
                profile_radii[idx] = max(profile_radii[idx], hole_diam / 2.0)

    solid = make_capped_bore(
        profile_pos.astype(float), profile_radii.astype(float),
        wall_thickness=wall_mm, n_angular=64, cap_thickness=wall_mm * 0.67,
    )
    stl_path = "test_output/instruments/%s" % stl_filename
    solid.export(stl_path)
    stl_size_kb = os.path.getsize(stl_path) / 1024
    return stl_path, stl_size_kb


# --- Tenor Trombone (Bb, open-open, no holes) ---
TROMBONE_CFG = {
    "desc": "Tenor Trombone in Bb (open-open brass, slide)",
    "closed_top": False,
    "bore_radius": 10.5,
    "outer_diameter": 52.0,
    "hole_diameter": 0,
    "hole_length": 0,
    "targets": [58.27, 61.74, 65.41, 73.42, 82.41, 87.31, 98.00, 110.00, 116.54, 130.81],
    "names": ["Bb1", "C2", "D2", "Eb2", "F2", "G2", "A2", "Bb2", "C3", "D3"],
    "fingerings": [["open"] * 2] * 10,
    "n_registers": [2] * 10,
}

# --- Alto Saxophone in Eb (open-open, conical, 23 holes) ---
ALTO_SAX_CFG = {
    "desc": "Alto Saxophone in Eb (open-open, conical, Boehm)",
    "closed_top": False,
    "bore_radius": 8.5,
    "outer_diameter": 34.0,
    "hole_diameter": 6.5,
    "hole_length": 2.5,
    "targets": [311.1, 349.2, 392.0, 440.0, 493.9, 554.4, 587.3, 622.3, 659.3, 698.5, 784.0, 880.0],
    "names": ["Eb4", "F4", "G4", "Ab4", "Bb4", "C5", "D5", "Eb5", "F5", "G5", "A5", "Bb5"],
    "fingerings": [
        ["closed"]*23, ["open"]+["closed"]*22,
        ["closed","open"]+["closed"]*21, ["closed"]*2+["open"]+["closed"]*19,
        ["closed"]*3+["open"]+["closed"]*18, ["closed"]*4+["open"]+["closed"]*17,
        ["closed"]*5+["open"]+["closed"]*16, ["closed"]*6+["open"]+["closed"]*15,
        ["closed"]*7+["open"]+["closed"]*14, ["closed"]*8+["open"]+["closed"]*13,
        ["closed"]*9+["open"]+["closed"]*12, ["closed"]*10+["open"]+["closed"]*11,
    ],
    "n_registers": [2] * 12,
}

# --- F Horn (conical brass, non-regular key) ---
F_HORN_CFG = {
    "desc": "F Horn in F (conical brass, single F)",
    "closed_top": False,
    "bore_radius": 12.0,
    "outer_diameter": 60.0,
    "hole_diameter": 0,
    "hole_length": 0,
    "targets": [87.31, 98.00, 110.00, 116.54, 130.81, 146.83, 155.56, 174.61, 196.00, 220.00],
    "names": ["F2", "G2", "A2", "Bb2", "C3", "D3", "Eb3", "F3", "G3", "A3"],
    "fingerings": [["open"]*2] * 10,
    "n_registers": [2] * 10,
}


def run_instrument(cfg, label, stl_name, wall_mm):
    t_total = time.time()
    print("\n" + "=" * 60)
    print("Pareto sweep: %s" % label)
    print("=" * 60)

    sweep = pareto_sweep(cfg, n_cp=6, seed=42, n_weights=8, maxiter=100, verbose=True)

    sweep_time = time.time() - t_total
    # Knee point
    min_int = min(r[1] for r in sweep)
    max_int = max(r[1] for r in sweep)
    min_timb = min(r[2] for r in sweep)
    max_timb = max(r[2] for r in sweep)
    int_r = max(max_int - min_int, 0.001)
    tim_r = max(max_timb - min_timb, 0.001)
    knee = min(sweep, key=lambda r: ((r[1]-min_int)/int_r)**2 + ((r[2]-min_timb)/tim_r)**2)
    best_w = knee[0]
    print("\nKnee: w_int=%.2f, int=%.4f c, timbre=%.4f" % (best_w, knee[1], knee[2]))

    # Run refine_sequential at w_int=1.0 baseline for validated params
    rms, L, radii, hp, hd, hl, t_refine = refine_sequential(
        cfg, verbose=False, use_jax_bore=False, w_int=1.0, w_mono=0.3,
    )
    n_holes = len(hp)
    rms_val = float(rms)
    L_val = float(L)
    print("  Baseline RMS=%.4f c, L=%.1fmm, %d holes (%.1fs)" % (rms_val, L_val, n_holes, t_refine))

    # STL
    stl_path, stl_kb = gen_stl(cfg, label, stl_name, wall_mm, L_val, radii, hp, hd, hl)

    total = time.time() - t_total
    return {
        "label": label, "desc": cfg["desc"],
        "target_note": cfg.get("target_note", ""),
        "target_freq_hz": cfg["targets"][0] if cfg["targets"] else 0,
        "pareto_sweep_points": len(sweep),
        "knee_w_int": best_w,
        "knee_intonation_c": knee[1],
        "knee_timbre_cost": knee[2],
        "final_rms_c": rms_val,
        "bore_length_mm": L_val,
        "holes": n_holes,
        "wall_thickness_mm": wall_mm,
        "total_time_s": round(total, 1),
        "stl_file": stl_path,
        "stl_size_kb": stl_kb,
        "test_instrument": True,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("Brass & Saxophone Pareto Optimization")
    print("Method: pareto_sweep + refine_sequential (default)")
    print("=" * 60)

    all_results = {}
    for label, cfg, stl_name, wall in [
        ("Tenor Trombone", TROMBONE_CFG, "tenor_trombone_pareto.stl", 3.0),
        ("Alto Saxophone", ALTO_SAX_CFG, "alto_sax_pareto.stl", 2.5),
        ("F Horn", F_HORN_CFG, "f_horn_pareto.stl", 4.0),
    ]:
        all_results[label] = run_instrument(cfg, label, stl_name, wall)

    json_path = "test_output/pareto_brass_sax_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, default=str)
    print("\nResults saved to %s" % json_path)
    print("Done. No commits made.")
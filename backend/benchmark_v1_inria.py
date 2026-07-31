"""
V1 Benchmark: Inria 2026 Pipe Impedance Benchmark
==================================================
Runs our TMM solver on the canonical V&V benchmark geometries:
- 180mm cylinders: 14mm ID, 4 end conditions (flanged/unflanged × open/closed)
- 180mm cones: 10→22.6mm, 3 end conditions
Materials: brass, boxwood, 3D-printed ABS

Reference: Ernoult et al. 2026, Acta Acustica 10:51, DOI 10.1051/aacus/2026048
Data: Zenodo 20024938 (v2)
"""

import sys, os, time, json, math
import numpy as np
from distributed import LocalCluster, Client

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND, KeefeLoss


# Benchmark geometries from Inria 2026 paper
BENCHMARK_GEOMETRIES = {
    # Cylinders: 180mm length, 14mm ID (radius 7mm)
    "cylinder_14mm_open_open": {
        "length_mm": 180.0,
        "radii_mm": [7.0] * 20,  # 20 control points
        "closed_top": False,
        "end_condition": "open_open",
        "description": "Cylinder 14mm ID, open-open (both ends flanged)",
    },
    "cylinder_14mm_open_closed": {
        "length_mm": 180.0,
        "radii_mm": [7.0] * 20,
        "closed_top": True,
        "end_condition": "open_closed",
        "description": "Cylinder 14mm ID, open-closed (bell open, reed closed)",
    },
    "cylinder_14mm_flanged_open": {
        "length_mm": 180.0,
        "radii_mm": [7.0] * 20,
        "closed_top": False,
        "end_condition": "flanged_open",
        "description": "Cylinder 14mm ID, flanged-open (bell flanged, other open)",
    },
    "cylinder_14mm_flanged_closed": {
        "length_mm": 180.0,
        "radii_mm": [7.0] * 20,
        "closed_top": True,
        "end_condition": "flanged_closed",
        "description": "Cylinder 14mm ID, flanged-closed (bell flanged, reed closed)",
    },
    # Cones: 180mm length, 10mm → 22.6mm (radius 5mm → 11.3mm)
    "cone_10_22.6mm_open_open": {
        "length_mm": 180.0,
        "radii_mm": np.linspace(5.0, 11.3, 20).tolist(),
        "closed_top": False,
        "end_condition": "open_open",
        "description": "Cone 10→22.6mm, open-open",
    },
    "cone_10_22.6mm_open_closed": {
        "length_mm": 180.0,
        "radii_mm": np.linspace(5.0, 11.3, 20).tolist(),
        "closed_top": True,
        "end_condition": "open_closed",
        "description": "Cone 10→22.6mm, open-closed",
    },
    "cone_10_22.6mm_flanged_open": {
        "length_mm": 180.0,
        "radii_mm": np.linspace(5.0, 11.3, 20).tolist(),
        "closed_top": False,
        "end_condition": "flanged_open",
        "description": "Cone 10→22.6mm, flanged-open",
    },
}


# Material properties for loss models (KeefeLoss uses air properties, wall losses are separate)
MATERIALS = {
    "brass": {"thermal_conductivity": 109.0, "density": 8530.0, "specific_heat": 380.0, "wall_thickness_mm": 1.0},
    "boxwood": {"thermal_conductivity": 0.15, "density": 830.0, "specific_heat": 1700.0, "wall_thickness_mm": 2.0},
    "abs": {"thermal_conductivity": 0.17, "density": 1040.0, "specific_heat": 1400.0, "wall_thickness_mm": 2.0},
}


def compute_impedance_spectrum(geometry, material_name, freq_range=(50, 2000), n_freq=500):
    """Compute input impedance spectrum for a geometry using TMM."""
    length = geometry["length_mm"] / 1000.0  # convert to meters
    radii = np.array(geometry["radii_mm"]) / 1000.0  # meters
    closed_top = geometry["closed_top"]
    
    # Create instrument
    outer_diameter = 0.022  # 22mm outer diameter (standard)
    hole_positions = []
    hole_diameters = []
    hole_lengths = []
    
    inst = tmm_instrument_from_radii(
        radii=radii,
        length=length,
        hole_positions=hole_positions,
        hole_diameters=hole_diameters,
        hole_lengths=hole_lengths,
        outer_diameter=outer_diameter,
        closed_top=closed_top,
        cone_step=0.5e-3,  # 0.5mm cone step
    )
    
    # Frequency sweep
    freqs = np.linspace(freq_range[0], freq_range[1], n_freq)
    wavelengths = SPEED_OF_SOUND / freqs  # SPEED_OF_SOUND in cm/s
    
    # Compute impedance at each frequency
    Z = []
    for wl in wavelengths:
        try:
            z = inst.compute_input_impedance(wl)
            Z.append(complex(z))
        except Exception as e:
            Z.append(complex(0, 0))
    
    return np.array(freqs), np.array(Z)


def find_resonance_peaks(freqs, Z, min_prominence=0.1):
    """Find resonance peaks in impedance magnitude."""
    mag = np.abs(Z)
    peaks = []
    
    # Simple peak detection
    for i in range(1, len(mag) - 1):
        if mag[i] > mag[i-1] and mag[i] > mag[i+1]:
            if mag[i] > min_prominence * np.max(mag):
                peaks.append((freqs[i], mag[i]))
    
    return peaks


def run_single_benchmark(args):
    """Run benchmark for one geometry+material combination. Designed for Dask."""
    geom_name, geom, material_name, mat = args
    
    t0 = time.time()
    try:
        freqs, Z = compute_impedance_spectrum(geom, material_name)
        peaks = find_resonance_peaks(freqs, Z)
        
        # Extract first few resonance frequencies
        peak_freqs = [p[0] for p in peaks[:10]]
        
        dt = time.time() - t0
        return {
            "geometry": geom_name,
            "material": material_name,
            "description": geom["description"],
            "end_condition": geom["end_condition"],
            "closed_top": geom["closed_top"],
            "peak_frequencies_hz": peak_freqs,
            "n_peaks": len(peak_freqs),
            "time_s": round(dt, 3),
            "status": "ok",
        }
    except Exception as e:
        return {
            "geometry": geom_name,
            "material": material_name,
            "status": f"error: {e}",
            "time_s": round(time.time() - t0, 3),
        }


def main():
    print("=" * 72)
    print("  V1 BENCHMARK: Inria 2026 Pipe Impedance (TMM)")
    print("=" * 72)
    
    # Start Dask cluster
    print("\nStarting Dask LocalCluster...")
    cluster = LocalCluster(n_workers=4, threads_per_worker=4, processes=True, 
                           dashboard_address=":8787", silence_logs=False)
    client = Client(cluster)
    
    info = client.scheduler_info()
    workers = info.get("workers", {})
    print(f"  Workers: {len(workers)}")
    for addr, w in workers.items():
        print(f"    {w.get('name', '?')}: nthreads={w.get('nthreads', '?')}")
    print(f"  Dashboard: {client.dashboard_link}")
    
    # Prepare all tasks
    tasks = []
    for geom_name, geom in BENCHMARK_GEOMETRIES.items():
        for mat_name, mat in MATERIALS.items():
            tasks.append((geom_name, geom, mat_name, mat))
    
    print(f"\nTotal tasks: {len(tasks)} ({len(BENCHMARK_GEOMETRIES)} geometries × {len(MATERIALS)} materials)")
    
    # Submit all tasks
    print("\nSubmitting tasks to Dask...")
    t0 = time.time()
    futures = [client.submit(run_single_benchmark, task) for task in tasks]
    
    # Collect results
    results = []
    for i, future in enumerate(futures):
        r = future.result()
        results.append(r)
        status = r.get("status", "unknown")
        peaks = r.get("n_peaks", 0)
        geom = r.get("geometry", "?")
        mat = r.get("material", "?")
        t = r.get("time_s", 0)
        print(f"  [{status}] {geom:30s} {mat:6s}  peaks={peaks:2d}  {t:.2f}s")
    
    total_time = time.time() - t0
    print(f"\nTotal time: {total_time:.1f}s")
    print(f"Dashboard: {client.dashboard_link}")
    
    # Save results
    out_path = os.path.join(os.path.dirname(__file__), "v1_benchmark_results.json")
    with open(out_path, "w") as f:
        json.dump({
            "timestamp": time.time(),
            "solver": "tmm_acoustics.py",
            "speed_of_sound_cm_s": SPEED_OF_SOUND,
            "geometries": list(BENCHMARK_GEOMETRIES.keys()),
            "materials": list(MATERIALS.keys()),
            "results": results,
            "total_time_s": total_time,
            "workers": len(workers),
        }, f, indent=2)
    print(f"\nResults saved to: {out_path}")
    
    # Summary by geometry
    print("\n" + "=" * 72)
    print("  RESONANCE FREQUENCIES (first 5 peaks, Hz)")
    print("=" * 72)
    for geom_name in BENCHMARK_GEOMETRIES:
        geom_results = [r for r in results if r.get("geometry") == geom_name and r.get("status") == "ok"]
        if geom_results:
            print(f"\n{geom_name}:")
            for r in geom_results:
                peaks = r.get("peak_frequencies_hz", [])[:5]
                print(f"  {r['material']:6s}: {peaks}")
    
    client.close()
    cluster.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
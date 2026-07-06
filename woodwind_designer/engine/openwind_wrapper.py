import os
import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

try:
    from openwind import ImpedanceComputation, InstrumentGeometry
    import matplotlib.pyplot as plt
    HAVE_OPENWIND = True
except ImportError:
    HAVE_OPENWIND = False


@dataclass
class SimulationResult:
    frequencies: np.ndarray = field(default_factory=lambda: np.array([]))
    impedance: np.ndarray = field(default_factory=lambda: np.array([]))
    Zc: float = 0.0
    peak_freqs: list = field(default_factory=list)
    peak_notes: list = field(default_factory=list)
    output_dir: str = ""
    plot_path: str = ""
    log: str = ""
    success: bool = False


class OpenWindSimulator:
    def __init__(self, output_base: str = "simulations"):
        self.output_base = Path(output_base)
        self.output_base.mkdir(parents=True, exist_ok=True)
        self._last_result: Optional[SimulationResult] = None

    def simulate_from_yaml(self, yaml_path: str, output_dir: Optional[str] = None,
                           f_min: float = 20, f_max: float = 3000,
                           n_points: int = 2000) -> SimulationResult:
        if not HAVE_OPENWIND:
            return SimulationResult(
                log="OpenWInD library not installed. Run: pip install openwind",
                success=False
            )

        import yaml
        if not os.path.exists(yaml_path):
            return SimulationResult(
                log=f"YAML file not found: {yaml_path}",
                success=False
            )

        with open(yaml_path, "r") as f:
            config = yaml.safe_load(f)

        sim_dir = output_dir or str(self.output_base / Path(yaml_path).stem)
        os.makedirs(sim_dir, exist_ok=True)

        try:
            bore_data = config.get("bore_profile", [])
            holes_data = config.get("tone_holes", [])
            bore_length = config.get("bore_length", 0.65)

            bore_lines = [[pos, radius] for pos, radius in bore_data]

            hole_lines = [
                [h.get("position"), h.get("radius"), h.get("chimney_height", 0.008)]
                for h in holes_data
            ]

            freqs = np.linspace(f_min, f_max, n_points)

            impedance_data = self._compute_impedance(bore_lines, hole_lines, freqs)

            if impedance_data is None:
                return SimulationResult(
                    output_dir=sim_dir,
                    log="Impedance computation returned no data. Check geometry.",
                    success=False
                )

            freqs_out, impedances, Zc = impedance_data

            peaks = self._find_peaks(freqs_out, impedances)
            peak_notes = [self._freq_to_note(f) for f in peaks]

            plot_path = os.path.join(sim_dir, "impedance_plot.png")
            self._save_plot(freqs_out, impedances, peaks, plot_path)

            result = SimulationResult(
                frequencies=freqs_out,
                impedance=impedances,
                Zc=Zc,
                peak_freqs=peaks,
                peak_notes=peak_notes,
                output_dir=sim_dir,
                plot_path=plot_path,
                success=True,
                log=f"Simulation completed. Found {len(peaks)} resonance peaks."
            )
            self._last_result = result
            return result

        except Exception as e:
            import traceback
            return SimulationResult(
                output_dir=sim_dir,
                log=f"Simulation error: {e}\n{traceback.format_exc()}",
                success=False
            )

    def _compute_impedance(self, bore_lines, hole_lines, freqs):
        try:
            geom = InstrumentGeometry(main_bore=bore_lines, unit="mm")
            imp = ImpedanceComputation(
                freqs, main_bore=bore_lines,
                holes_valves=hole_lines if hole_lines else [],
                temperature=25.0, losses=True,
                unit="mm",
            )
            return freqs, imp.impedance, imp.Zc
        except Exception as e:
            return None

    def _find_peaks(self, freqs, impedances):
        peaks = []
        z_mag = np.abs(impedances)
        for i in range(1, len(z_mag) - 1):
            if z_mag[i] > z_mag[i - 1] and z_mag[i] > z_mag[i + 1]:
                if z_mag[i] > np.mean(z_mag) * 1.5:
                    peaks.append(float(freqs[i]))
        return peaks[:20]

    def _freq_to_note(self, freq):
        A4 = 440.0
        semitones = 12 * np.log2(freq / A4)
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        n = int(round(semitones))
        octave = 4 + (n + 9) // 12
        note = note_names[(n + 9) % 12]
        cents = int((semitones - round(semitones)) * 100)
        return f"{note}{octave} ({cents:+#}ct)"

    def _save_plot(self, freqs, impedances, peaks, path):
        if not HAVE_OPENWIND:
            return
        plt.figure(figsize=(10, 5))
        plt.plot(freqs, np.abs(impedances), 'b-', linewidth=1.5)
        for pf in peaks:
            plt.axvline(x=pf, color='r', linestyle='--', alpha=0.3)
        plt.xlabel("Frequency (Hz)")
        plt.ylabel("Impedance magnitude")
        plt.title("Input Impedance")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(path, dpi=150)
        plt.close()

    def save_results_json(self, result: SimulationResult, path: Optional[str] = None):
        save_path = path or os.path.join(result.output_dir, "simulation_results.json")
        data = {
            "peak_frequencies": result.peak_freqs,
            "peak_notes": result.peak_notes,
            "Zc": result.Zc,
            "n_peaks": len(result.peak_freqs),
            "plot_path": result.plot_path,
        }
        with open(save_path, "w") as f:
            json.dump(data, f, indent=2)
        return save_path

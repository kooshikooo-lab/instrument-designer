"""
External solver wrappers - use chalumier and OpenWind as libraries/tools.

This avoids porting and keeps physics consistent with reference implementations.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import numpy as np
import subprocess
import json
import tempfile
import os
from pathlib import Path


class ExternalSolver(ABC):
    """Base class for external acoustic solvers."""

    @abstractmethod
    def compute_impedance(
        self,
        network,
        frequencies: np.ndarray,
        fingering: List[str],
    ) -> np.ndarray:
        """Compute input impedance Z(f)."""
        pass

    @abstractmethod
    def find_resonance(
        self,
        network,
        wavelength_near: float,
        fingering: List[str],
        n_register: int = 1,
    ) -> float:
        """Find resonant wavelength."""
        pass

    @abstractmethod
    def compute_frequencies(
        self,
        network,
        target_wavelengths: List[float],
        fingering_sets: List[List[str]],
        n_register: int = 1,
    ) -> np.ndarray:
        """Compute resonant frequencies."""
        pass


class ChalumierSolver(ExternalSolver):
    """
    Wrapper for chalumier Kotlin TMM solver.

    Uses chalumier's design CLI or direct JVM calls.
    Requires chalumier.jar built with `gradle shadowJar`.
    """

    def __init__(self, jar_path: str = None, java_cmd: str = "java"):
        self.jar_path = jar_path or self._find_jar()
        self.java_cmd = java_cmd

    def _find_jar(self) -> Optional[str]:
        """Find chalumier shadow jar."""
        chalumier_dir = Path("chalumier")
        if not chalumier_dir.exists():
            return None
        jars = list(chalumier_dir.glob("app/build/libs/*-all.jar"))
        if jars:
            return str(jars[0])
        return None

    def _build_jar(self) -> bool:
        """Build chalumier shadow jar."""
        chalumier_dir = Path("chalumier")
        if not chalumier_dir.exists():
            return False
        result = subprocess.run(
            ["./gradlew", "shadowJar"],
            cwd=chalumier_dir,
            capture_output=True,
            text=True,
            timeout=300,
        )
        return result.returncode == 0

    def _run_chalumier(
        self,
        bore_profile: List[Tuple[float, float]],
        hole_positions: List[float],
        hole_diameters: List[float],
        hole_lengths: List[float],
        target_wavelengths: List[float],
        fingerings: List[List[str]],
        n_register: int = 1,
    ) -> dict:
        """Run chalumier via subprocess."""
        if not self.jar_path:
            if not self._build_jar():
                raise RuntimeError("Failed to build chalumier")
            self.jar_path = self._find_jar()

        # Create temporary input file for chalumier
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Write instrument specification
            spec = {
                "bore_profile": bore_profile,
                "hole_positions": hole_positions,
                "hole_diameters": hole_diameters,
                "hole_lengths": hole_lengths,
                "target_wavelengths": target_wavelengths,
                "fingerings": fingerings,
                "n_register": n_register,
            }
            spec_file = tmpdir / "spec.json"
            spec_file.write_text(json.dumps(spec))

            # Run chalumier
            cmd = [
                self.java_cmd, "-jar", self.jar_path,
                "compute", "--spec", str(spec_file),
                "--output", str(tmpdir / "result.json")
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60
            )

            if result.returncode != 0:
                raise RuntimeError(f"Chalumier failed: {result.stderr}")

            output_file = tmpdir / "result.json"
            if output_file.exists():
                return json.loads(output_file.read_text())
            else:
                raise RuntimeError("No output from chalumier")

    def compute_frequencies(
        self,
        network,
        target_wavelengths: List[float],
        fingering_sets: List[List[str]],
        n_register: int = 1,
    ) -> np.ndarray:
        # Convert network to chalumier format
        bore_profile = network.to_bore_profile()  # [(pos, radius), ...]
        hole_pos, hole_rad, hole_len = network.to_hole_data()

        result = self._run_chalumier(
            bore_profile, hole_pos, hole_rad * 2, hole_len,
            target_wavelengths, fingering_sets, n_register
        )
        return np.array(result["frequencies"])

    def find_resonance(
        self,
        network,
        wavelength_near: float,
        fingering: List[str],
        n_register: int = 1,
    ) -> float:
        result = self._run_chalumier(
            network.to_bore_profile(),
            *network.to_hole_data(),
            [wavelength_near], [fingering], n_register
        )
        return result["wavelengths"][0]

    def resonance_phase(
        self,
        network,
        wavelength: float,
        fingering: List[str],
    ) -> float:
        result = self._run_chalumier(
            network.to_bore_profile(),
            *network.to_hole_data(),
            [wavelength], [fingering], 1
        )
        return result["phases"][0]


class OpenWindSolver(ExternalSolver):
    """
    Wrapper for OpenWind FEM solver.

    Uses openwind Python library directly (pip install openwind).
    """

    def __init__(
        self,
        temperature: float = 25.0,
        losses: bool = True,
        radiation_category: str = "unflanged",
        compute_method: str = "FEM",
    ):
        try:
            from openwind import ImpedanceComputation
            self.ImpedanceComputation = ImpedanceComputation
        except ImportError:
            raise ImportError("OpenWind not installed: pip install openwind")

        self.temperature = temperature
        self.losses = losses
        self.radiation_category = radiation_category
        self.compute_method = compute_method

    def _network_to_openwind(self, network) -> Tuple[list, list]:
        """Convert AcousticNetwork to OpenWind format (meters)."""
        # Bore: list of [x1, x2, r1, r2, 'linear']
        bore_list = []
        pos = 0.0
        for seg in network.segments:
            x1 = pos / 1000.0
            x2 = (pos + seg.length) / 1000.0
            r1 = seg.radius_in / 1000.0
            r2 = seg.radius_out / 1000.0
            bore_list.append([x1, x2, r1, r2, 'linear'])
            pos += seg.length

        # Holes: list with header + [label, position, radius, length]
        hole_list = [['label', 'position', 'radius', 'length']]
        for i, port in enumerate(network.ports):
            hole_list.append([
                f'hole{i+1}',
                port.position / 1000.0,
                port.radius / 1000.0,
                port.length / 1000.0,
            ])

        return bore_list, hole_list

    def _build_fingering_chart(self, network, fingering: List[str]) -> list:
        """Build OpenWind fingering chart."""
        if not network.ports:
            return []

        labels = [f'hole{i+1}' for i in range(len(network.ports))]
        chart = [['label', 'note1']]
        for i, port in enumerate(network.ports):
            state = fingering[i] if i < len(fingering) else 'closed'
            chart.append([labels[i], 'o' if state == 'open' else 'x'])
        return chart

    def compute_impedance(
        self,
        network,
        frequencies: np.ndarray,
        fingering: List[str],
    ) -> np.ndarray:
        bore_list, hole_list = self._network_to_openwind(network)

        kwargs = dict(
            frequencies=frequencies,
            main_bore=bore_list,
            holes_valves=hole_list if network.n_ports > 0 else [],
            temperature=self.temperature,
            losses=self.losses,
            radiation_category=self.radiation_category,
            compute_method=self.compute_method,
            nondim=True,
            unit='m',
        )

        if fingering and network.ports:
            chart = self._build_fingering_chart(network, fingering)
            kwargs['fingering_chart'] = chart
            kwargs['note'] = 'note1'

        result = self.ImpedanceComputation(**kwargs)
        return result.impedance

    def find_resonance(
        self,
        network,
        wavelength_near: float,
        fingering: List[str],
        n_register: int = 1,
    ) -> float:
        c = network.speed_of_sound
        freq_near = c / wavelength_near
        f_min = max(10, freq_near * 0.5)
        f_max = freq_near * 2.0
        frequencies = np.linspace(f_min, f_max, 10000)

        imp = self.compute_impedance(network, frequencies, fingering)
        mag = np.abs(imp)

        # Find peaks
        peaks = []
        for i in range(1, len(mag) - 1):
            if mag[i] > mag[i-1] and mag[i] > mag[i+1]:
                peaks.append(i)

        if not peaks:
            return wavelength_near

        peak_freqs = [frequencies[i] for i in peaks]
        peak_mags = [mag[i] for i in peaks]

        # Sort by magnitude
        sorted_peaks = sorted(zip(peak_freqs, peak_mags), key=lambda x: -x[1])

        if len(sorted_peaks) >= n_register:
            return c / sorted_peaks[n_register - 1][0]
        return c / sorted_peaks[0][0]

    def compute_frequencies(
        self,
        network,
        target_wavelengths: List[float],
        fingering_sets: List[List[str]],
        n_register: int = 1,
    ) -> np.ndarray:
        c = network.speed_of_sound
        f_min = max(10, c / (max(target_wavelengths) * 2))
        f_max = c / (min(target_wavelengths) * 0.5)
        frequencies = np.linspace(f_min, f_max, 20000)

        results = []
        bore_list, hole_list = self._network_to_openwind(network)

        for fingering in fingering_sets:
            kwargs = dict(
                frequencies=frequencies,
                main_bore=bore_list,
                holes_valves=hole_list if network.n_ports > 0 else [],
                temperature=self.temperature,
                losses=self.losses,
                radiation_category=self.radiation_category,
                compute_method=self.compute_method,
                nondim=True,
                unit='m',
            )

            if fingering and network.ports:
                chart = self._build_fingering_chart(network, fingering)
                kwargs['fingering_chart'] = chart
                kwargs['note'] = 'note1'

            result = self.ImpedanceComputation(**kwargs)
            freqs = result.resonance_frequencies(k=n_register + 2)

            if len(freqs) >= n_register:
                results.append(freqs[n_register - 1])
            elif freqs:
                results.append(freqs[0])
            else:
                results.append(np.nan)

        return np.array(results)


def get_solver(name: str, **kwargs) -> ExternalSolver:
    """Factory function to get solver by name."""
    if name == "chalumier":
        return ChalumierSolver(**kwargs)
    elif name == "openwind":
        return OpenWindSolver(**kwargs)
    else:
        raise ValueError(f"Unknown solver: {name}")
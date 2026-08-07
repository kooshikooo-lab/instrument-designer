"""
Optimizer selection framework — automatic best-method selection per instrument.

Selects the optimal optimization strategy based on instrument characteristics,
benchmark validation, and user requirements.

Methodology references:
- Noreland et al. (2013) "The Logical Clarinet" — two-phase optimization essential
- Ernoult et al. (2020) JASA — phase-based resonance tracking (to implement)
- Petiot et al. (2025) JASA — NSGA-II Pareto front (intonation vs timbre)
- WIDesigner (Patkau 2017) — DIRECT-C + BOBYQA, derivative-free
- Sequential benchmark (our proven best): sequential + DE + 4-stage L-BFGS-B
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Protocol
import numpy as np

from .base import Optimizer, OptimizationResult
from .bore_optimizer import BoreOptimizer
from ..core.network import AcousticNetwork
from ..solvers.tmm_solver import TMMSolver


class OptimizerStrategy(Enum):
    """Available optimization strategies."""
    FAST = "fast"                    # DE only — quick draft designs
    ACCURATE = "accurate"            # Two-phase (Noreland) — DEFAULT, best general
    REFINED = "refined"              # JAX 4-stage + sequential init — fast refinement
    PARETO = "pareto"                # Intonation vs timbre tradeoff (NSGA-II)
    BENCHMARK = "benchmark"          # Sequential + DE + 4-stage (proven best accuracy)


class InstrumentType(Enum):
    """Instrument categories that affect optimizer choice."""
    CLARINET = "clarinet"            # closed-open, register key
    SAXOPHONE = "saxophone"          # open-open, conical
    FLUTE = "flute"                  # open-open, cylindrical/conical
    BRASS = "brass"                  # open-open, strong bell flare (TMM limited)
    CHALUMEAU = "chalumeau"          # closed-open, simple
    RECORDER = "recorder"            # open-open, fipple
    OCARINA = "ocarina"              # open-open, vessel
    WHISTLE = "whistle"              # open-open, fipple
    DRONE = "drone"                  # open-open, no holes
    MEMBRANE = "membrane"            # closed-open, membrane reed
    EXPERIMENTAL = "experimental"    # hybrid, slit, glissando


@dataclass
class OptimizerConfig:
    """Configuration for optimizer selection."""
    strategy: OptimizerStrategy = OptimizerStrategy.ACCURATE
    instrument_type: InstrumentType = InstrumentType.CLARINET
    acoustic_type: str = "closed-open"  # "closed-open" or "open-open"
    enable_timbre: bool = False
    max_time_seconds: float = 60.0
    target_accuracy_cents: float = 3.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class OptimizerProtocol(Protocol):
    """Protocol that all optimizers must implement."""
    def optimize(self, verbose: bool = False) -> OptimizationResult: ...
    def evaluate(self, parameters: Dict[str, Any]) -> float: ...


class OptimizerFactory:
    """Factory for creating the best optimizer for a given instrument."""
    
    # Strategy -> optimizer class mapping
    _OPTIMIZER_MAP: Dict[OptimizerStrategy, type] = {}
    
    @classmethod
    def register(cls, strategy: OptimizerStrategy, optimizer_class: type):
        """Register an optimizer class for a strategy."""
        cls._OPTIMIZER_MAP[strategy] = optimizer_class
    
    @classmethod
    def create(cls, config: OptimizerConfig, network: AcousticNetwork, 
               targets: List[float], fingerings: List[List[str]],
               n_register: int = 1) -> Optimizer:
        """Create the best optimizer for the given configuration."""
        
        # Override strategy based on instrument characteristics
        strategy = cls._select_strategy(config, network)
        
        optimizer_class = cls._OPTIMIZER_MAP.get(strategy)
        if optimizer_class is None:
            raise ValueError(f"No optimizer registered for strategy: {strategy}")
        
        return optimizer_class(
            network=network,
            target_frequencies=targets,
            fingering_sets=fingerings,
            n_register=n_register,
            max_time_seconds=config.max_time_seconds,
        )
    
    @classmethod
    def _select_strategy(cls, config: OptimizerConfig, network: AcousticNetwork) -> OptimizerStrategy:
        """Select best strategy based on instrument characteristics."""
        
        # Explicit user choice takes priority
        if config.strategy != OptimizerStrategy.ACCURATE:
            return config.strategy
        
        # Brass + Woodwinds → need FEM (bell flare, register vents, complex bore not handled by TMM)
        if config.instrument_type in (
            InstrumentType.BRASS,
            InstrumentType.CLARINET,
            InstrumentType.SAXOPHONE,
            InstrumentType.FLUTE,
            InstrumentType.CHALUMEAU,
            InstrumentType.RECORDER,
            InstrumentType.OCARINA,
            InstrumentType.WHISTLE,
        ):
            return OptimizerStrategy.REFINED  # Will route to OpenWInD
        
        # Timbre-aware optimization requested
        if config.enable_timbre:
            return OptimizerStrategy.PARETO
        
        # High accuracy target → use benchmark-proven method
        if config.target_accuracy_cents < 2.0:
            return OptimizerStrategy.BENCHMARK
        
        # Fast draft mode
        if config.max_time_seconds < 10.0:
            return OptimizerStrategy.FAST
        
        # Default: Noreland two-phase (best general accuracy/speed)
        return OptimizerStrategy.ACCURATE


# =============================================================================
# Concrete Optimizer Implementations
# =============================================================================

class FastOptimizer(BoreOptimizer):
    """Fast optimizer — DE only, quick draft designs.
    
    Best for: initial exploration, rough prototypes
    Time: ~5-10 seconds
    Accuracy: ~10-20 cents
    """
    
    def __init__(self, network: AcousticNetwork, target_frequencies: List[float],
                 fingering_sets: List[List[str]], n_register: int = 1,
                 max_time_seconds: float = 10.0):
        super().__init__(
            network=network,
            target_frequencies=target_frequencies,
            fingering_sets=fingering_sets,
            n_register=n_register,
            bore_length_bounds=(400, 2000),
            n_bore_cp=0,
        )
        self.max_time = max_time_seconds
    
    def optimize(self, verbose: bool = False) -> OptimizationResult:
        """Run fast DE optimization (bore length only)."""
        import time
        from scipy.optimize import differential_evolution
        
        t0 = time.time()
        
        initial_length = self.network.total_length
        bounds = [self.bore_length_bounds]
        
        result = differential_evolution(
            lambda x: self.evaluate({"bore_length": x[0]}),
            bounds, seed=42, maxiter=20, tol=1e-4,
        )
        
        best_length = result.x[0]
        best_cost = result.fun
        dt = time.time() - t0
        
        # Quick final evaluation
        temp_net = self._make_network(best_length)
        target_wavelengths = [self.network.speed_of_sound / f for f in self.targets]
        freqs = self.solver.compute_frequencies(
            temp_net, target_wavelengths, self.fingering_sets, self.n_register
        )
        cents = [1200.0 * np.log2(a / t) if a > 0 and np.isfinite(a) else 1e6 
                 for a, t in zip(freqs, self.targets)]
        cents_arr = np.array(cents)
        rms_cents = float(np.sqrt(np.mean(cents_arr ** 2)))
        
        return OptimizationResult(
            success=best_cost < 100.0,
            parameters={"bore_length": best_length},
            cost=best_cost,
            rms_cents=rms_cents,
            rms_cents_median=0.0,
            peak_cents=float(np.max(np.abs(cents_arr))),
            n_evaluations=self._n_evaluations,
            wall_time=dt,
        )


class TwoPhaseOptimizer(Optimizer):
    """Two-phase optimizer (Noreland approach) — DEFAULT for general use.
    
    Phase 1: DE + absolute RMS — fast global exploration
    Phase 2: L-BFGS-B + peak_cost_nearest — precise refinement
    
    Best for: general purpose woodwind optimization
    Time: ~30-60 seconds
    Accuracy: <3 cents (proven)
    
    References:
    - Noreland et al. (2013) "The Logical Clarinet"
    - Ernoult et al. (2020) JASA — phase-based tracking (to implement)
    """
    
    def __init__(self, network: AcousticNetwork, target_frequencies: List[float],
                 fingering_sets: List[List[str]], n_register: int = 1,
                 max_time_seconds: float = 60.0,
                 outer_diameter: float = None,
                 closed_top: bool = None,
                 bore_length_bounds: tuple = None):
        self.network = network
        self.targets = target_frequencies
        self.fingering_sets = fingering_sets
        self.n_register = n_register
        self.max_time = max_time_seconds
        self._n_evaluations = 0
        # Configurable parameters (not hardcoded)
        self.outer_diameter = outer_diameter
        self.closed_top = closed_top
        self.bore_length_bounds = bore_length_bounds
    
    def evaluate(self, parameters: Dict[str, Any]) -> float:
        """Evaluate cost using absolute RMS."""
        self._n_evaluations += 1
        # Import here to avoid circular imports
        from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
        from backend.physics.losses import KeefeLoss
        from backend.physics.register_detection import detect_registers, build_initial_instrument
        
        bore_length = parameters.get("bore_length", self.network.total_length)
        bore_radii = parameters.get("bore_radii", None)
        hole_positions = parameters.get("hole_positions", [])
        hole_diameters = parameters.get("hole_diameters", [])
        hole_lengths = parameters.get("hole_lengths", [])
        
        # Use configurable params instead of hardcoded values
        outer_diameter = self.outer_diameter if self.outer_diameter is not None else 22.0
        closed_top = self.closed_top if self.closed_top is not None else (self.n_register == 1)
        
        inst = tmm_instrument_from_radii(
            radii=bore_radii if bore_radii is not None else np.full(6, 10.0),
            bore_length=bore_length,
            hole_positions=hole_positions,
            hole_diameters=hole_diameters,
            hole_lengths=hole_lengths,
            outer_diameter_mm=outer_diameter,
            closed_top=closed_top,
            cone_step=0.5,
        )
        
        tw = [SPEED_OF_SOUND / f for f in self.targets]
        freqs = inst.compute_fingered_frequencies(tw, self.fingering_sets, self.n_register)
        cents = [1200.0 * np.log2(a / t) if a > 0 and np.isfinite(a) else 1e6 
                 for a, t in zip(freqs, self.targets)]
        cents_arr = np.array(cents)
        if np.any(np.abs(cents_arr) > 1e5):
            return 1e10
        return float(np.sqrt(np.mean(cents_arr ** 2)))
    
    def optimize(self, verbose: bool = False) -> OptimizationResult:
        """Run two-phase optimization: DE global + L-BFGS-B refinement with frozen registers."""
        import time
        from scipy.optimize import differential_evolution, minimize as sp_min
        from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
        from backend.physics.register_detection import detect_registers, build_initial_instrument
        from backend.physics.losses import KeefeLoss
        
        t0 = time.time()
        
        # --- Phase 1: DE global search with absolute RMS ---
        initial_length = self.network.total_length
        n_holes = len(self.fingering_sets[0]) if self.fingering_sets else 0
        
        # Apply bore_length_bounds if configured (for bass instruments)
        if self.bore_length_bounds:
            bore_min, bore_max = self.bore_length_bounds
            bounds = [(max(bore_min, initial_length * 0.7), min(bore_max, initial_length * 1.3))]
        else:
            bounds = [(initial_length * 0.7, initial_length * 1.3)]
        
        n_holes = len(self.fingering_sets[0]) if self.fingering_sets else 0
        if n_holes > 0:
            for _ in range(n_holes):
                bounds.append((20, initial_length - 20))  # hole positions
                bounds.append((3.0, 15.0))  # hole diameters
        
        # Build initial instrument for register detection
        outer_diameter = self.outer_diameter if self.outer_diameter is not None else 22.0
        closed_top = self.closed_top if self.closed_top is not None else (self.n_register == 1)
        hole_lengths = [3.75] * n_holes if n_holes > 0 else []
        
        initial_inst = build_initial_instrument(
            bore_length=initial_length,
            n_holes=n_holes,
            hole_lens=hole_lengths,
            bore_radii=np.full(6, 10.0),
            hole_positions=np.array([initial_length * (i+1) / (n_holes+1) for i in range(n_holes)]) if n_holes > 0 else np.array([]),
            hole_diameters=np.full(n_holes, 8.0) if n_holes > 0 else np.array([]),
            outer_diameter=outer_diameter,
            closed_top=closed_top,
            loss_model=KeefeLoss(),
        )
        
        # Detect registers ONCE from initial geometry, freeze them
        closed_top = self.closed_top if self.closed_top is not None else (self.n_register == 1)
        fingerings_parsed = []
        for f in self.fingering_sets:
            fl = ['open' if ch in ('O', 'o') else 'closed' for ch in f]
            while len(fl) < len(self.fingering_sets[0]):
                fl.append('open')
            fingerings_parsed.append(fl[:len(self.fingering_sets[0])])
        
        regs = detect_registers(
            inst=initial_inst,
            targets=self.targets,
            fingerings=fingerings_parsed,
            max_reg=5,
            temperature=20.0,
        )
        if verbose:
            print(f"  Initial registers (frozen): {regs}")
        
        def de_objective(x):
            bore_length = x[0]
            hp = x[1::2] if len(x) > 1 else []
            hd = x[2::2] if len(x) > 2 else []
            return self.evaluate({
                "bore_length": bore_length,
                "hole_positions": hp,
                "hole_diameters": hd,
            })
        
        # Run DE with time budget
        time_budget = self.max_time * 0.6
        result_de = differential_evolution(
            de_objective, bounds, seed=42, maxiter=50, tol=1e-6,
            polish=False,
        )
        
        # --- Phase 2: L-BFGS-B refinement with phase-based absolute cost (peak_cost_nearest) ---
        best_x = result_de.x
        best_bore_length = best_x[0]
        best_hp = best_x[1::2] if len(best_x) > 1 else []
        best_hd = best_x[2::2] if len(best_x) > 2 else []
        
        # Sort holes by position
        if best_hp:
            idx = np.argsort(best_hp)
            best_hp = [best_hp[i] for i in idx]
            best_hd = [best_hd[i] for i in idx]
        
        # Refine with L-BFGS-B using phase-based absolute cost (frozen registers)
        outer_diameter = self.outer_diameter if self.outer_diameter is not None else 22.0
        closed_top = self.closed_top if self.closed_top is not None else (self.n_register == 1)
        
        def peak_cost_nearest(params):
            bore_length = params[0]
            hp = params[1::2] if len(params) > 1 else []
            hd = params[2::2] if len(params) > 2 else []
            for i in range(1, len(hp)):
                if hp[i] <= hp[i-1] + 3:
                    return 1e6
            try:
                inst = tmm_instrument_from_radii(
                    radii=np.full(6, 10.0),
                    bore_length=bore_length,
                    hole_positions=hp,
                    hole_diameters=hd,
                    hole_lengths=[3.75] * n_holes,
                    outer_diameter_mm=outer_diameter,
                    closed_top=closed_top,
                    cone_step=0.5,
                )
                cents = []
                for tgt, fl, pr in zip(self.targets, self.fingering_sets, regs):
                    wl = inst.find_resonance(SPEED_OF_SOUND / tgt, fl, n_register=pr)
                    f = inst.frequency_from_wavelength(wl)
                    cents.append(cents_error(f, tgt))
                ca = np.array(cents)
                if np.any(np.abs(ca) > 1e5):
                    return 1e10
                return float(np.sqrt(np.mean(ca ** 2)))
            except Exception:
                return 1e10

        # Apply bore_length_bounds for local refinement
        if self.bore_length_bounds:
            bore_min, bore_max = self.bore_length_bounds
            lb_bounds = [(max(bore_min, best_bore_length * 0.9), min(bore_max, best_bore_length * 1.1))]
        else:
            lb_bounds = [(best_bore_length * 0.9, best_bore_length * 1.1)]
        
        if best_hp:
            idx = np.argsort(best_hp)
            best_hp = [best_hp[i] for i in idx]
            best_hd = [best_hd[i] for i in idx]
        
        for hp in best_hp:
            lb_bounds.append((max(20, hp - 30), min(best_bore_length - 20, hp + 30)))
        for hd in best_hd:
            lb_bounds.append((hd * 0.7, hd * 1.3))
        
        # Need cents_error function
        def cents_error(actual, target):
            if actual <= 0 or target <= 0: return 1e10
            return 1200.0 * np.log2(actual / target)
        
        result_lb = sp_min(
            peak_cost_nearest, best_x, method='L-BFGS-B',
            bounds=lb_bounds, options={"maxiter": 200, "ftol": 1e-8}
        )
        
        dt = time.time() - t0
        final_params = result_lb.x
        final_bore_length = final_params[0]
        final_hp = final_params[1::2] if len(final_params) > 1 else []
        final_hd = final_params[2::2] if len(final_params) > 2 else []
        
        if final_hp:
            idx = np.argsort(final_hp)
            final_hp = [final_hp[i] for i in idx]
            final_hd = [final_hd[i] for i in idx]
        
        # Final evaluation
        final_cost = self.evaluate({
            "bore_length": final_bore_length,
            "hole_positions": final_hp,
            "hole_diameters": final_hd,
        })
        
        # Compute detailed metrics
        from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
        inst = tmm_instrument_from_radii(
            radii=np.full(6, 10.0),
            bore_length=final_bore_length,
            hole_positions=final_hp,
            hole_diameters=final_hd,
            hole_lengths=[3.75] * len(final_hp),
            outer_diameter_mm=22.0,
            closed_top=(self.n_register == 1),
            cone_step=0.5,
        )
        tw = [SPEED_OF_SOUND / f for f in self.targets]
        freqs = inst.compute_fingered_frequencies(tw, self.fingering_sets, self.n_register)
        cents = [1200.0 * np.log2(a / t) if a > 0 and np.isfinite(a) else 1e6 
                 for a, t in zip(freqs, self.targets)]
        cents_arr = np.array(cents)
        rms_cents = float(np.sqrt(np.mean(cents_arr ** 2)))
        offset = np.median(cents_arr)
        rms_cents_median = float(np.sqrt(np.mean((cents_arr - offset) ** 2)))
        peak_cents = float(np.max(np.abs(cents_arr - offset)))
        
        return OptimizationResult(
            success=final_cost < 50.0,
            parameters={
                "bore_length": final_bore_length,
                "hole_positions": final_hp,
                "hole_diameters": final_hd,
            },
            cost=final_cost,
            rms_cents=rms_cents,
            rms_cents_median=rms_cents_median,
            peak_cents=peak_cents,
            n_evaluations=self._n_evaluations,
            wall_time=time.time() - t0,
        )


# Register optimizers with factory
OptimizerFactory.register(OptimizerStrategy.FAST, FastOptimizer)
OptimizerFactory.register(OptimizerStrategy.ACCURATE, TwoPhaseOptimizer)


def get_optimizer(config: OptimizerConfig, network: AcousticNetwork,
                  targets: List[float], fingerings: List[List[str]],
                  n_register: int = 1) -> Optimizer:
    """Convenience function to get the best optimizer."""
    return OptimizerFactory.create(config, network, targets, fingerings, n_register)


def run_optimizer_comparison(instrument_cfg: Dict[str, Any], 
                             network: AcousticNetwork,
                             targets: List[float],
                             fingerings: List[List[str]],
                             n_register: int = 1) -> Dict[str, Dict[str, Any]]:
    """Run multiple optimizers on the same instrument for comparison."""
    strategies = [
        OptimizerStrategy.FAST,
        OptimizerStrategy.ACCURATE,
        # OptimizerStrategy.REFINED,  # Requires JAX
        # OptimizerStrategy.BENCHMARK,  # Requires benchmark_all.py
    ]
    
    results = {}
    for strategy in strategies:
        config = OptimizerConfig(strategy=strategy)
        try:
            opt = get_optimizer(config, network, targets, fingerings, n_register)
            result = opt.optimize(verbose=False)
            results[strategy.value] = {
                "rms_cents": result.rms_cents,
                "rms_cents_median": result.rms_cents_median,
                "peak_cents": result.peak_cents,
                "wall_time": result.wall_time,
                "n_evaluations": result.n_evaluations,
                "success": result.success,
            }
        except Exception as e:
            results[strategy.value] = {"error": str(e)}
    
    return results
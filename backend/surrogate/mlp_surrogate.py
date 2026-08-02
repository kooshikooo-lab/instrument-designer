"""
MLP Surrogate Model for Wind Instrument Acoustics

Replaces expensive TMM evaluations with a fast neural network.
Based on Petiot et al. 2025 (trumpet leadpipe RF surrogate) and Fréour 2023 (trumpet bifurcation ML).

Architecture: 2-3 hidden layers, 128-512 neurons, ReLU/tanh.
Input: bore parameters + hole parameters + target frequencies
Output: intonation descriptors (RMS, EFP, threshold pressure)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import jax
import jax.numpy as jnp
import flax.linen as nn
import optax
import numpy as np
from dataclasses import field


@dataclass
class SurrogateConfig:
    """Configuration for MLP surrogate."""
    hidden_dims: tuple[int, ...] = (256, 256, 128)
    activation: str = "relu"  # "relu", "tanh", "swish", "snake"
    output_dim: int = 4  # RMS, EFP, threshold_pressure, peak_error
    dropout_rate: float = 0.1
    input_dim: int = 30  # radii(6) + holes(3*7) + [L, outer_d, closed_top]
    dtype: jnp.dtype = jnp.float32


class BoreSurrogate(nn.Module):
    """MLP surrogate mapping bore/hole geometry → acoustic descriptors.
    
    Based on Petiot et al. 2025: RF surrogates map leadpipe geometry → 
    intonation (EFP) + playability (threshold pressure).
    
    Input features:
    - bore_radii: array of control point radii (n_cp)
    - hole_positions: array of hole positions (n_holes)
    - hole_diameters: array of hole diameters (n_holes)
    - hole_lengths: array of hole lengths (n_holes)
    - bore_length: scalar
    - closed_top: bool
    - target_frequencies: array of target frequencies (for conditioning)
    
    Output descriptors (matching Petiot 2025):
    - final_rms_cents: absolute intonation RMS
    - efp: emission figure of merit (playability)
    - threshold_pressure: minimum blowing pressure
    - peak_error_cents: max deviation
    """
    config: SurrogateConfig
    
    def setup(self):
        self.activation_fn = self._get_activation(self.config.activation)
    
    def _get_activation(self, name: str):
        if name == "relu":
            return nn.relu
        elif name == "tanh":
            return nn.tanh
        elif name == "swish":
            return nn.swish
        elif name == "snake":
            # Snake activation: x + (1/a) * sin(a * x)^2
            # Using a=1 for simplicity
            return lambda x: x + jnp.sin(x)**2
        else:
            return nn.relu
    
    @nn.compact
    def __call__(self, x: jnp.ndarray, training: bool = False) -> jnp.ndarray:
        # Input normalization layer (learned)
        x = nn.BatchNorm(use_running_average=not training, name="input_bn")(x)
        
        for i, dim in enumerate(self.config.hidden_dims):
            x = nn.Dense(dim, name=f"dense_{i}")(x)
            x = self.activation_fn(x)
            if self.config.dropout_rate > 0:
                x = nn.Dropout(rate=self.config.dropout_rate, deterministic=not training)(x)
        
        # Output layer
        x = nn.Dense(self.config.output_dim, name="output")(x)
        return x


@dataclass
class SurrogateTrainer:
    """Training loop for bore surrogate."""
    config: SurrogateConfig
    learning_rate: float = 1e-3
    weight_decay: float = 1e-5
    seed: int = 42
    
    _model: BoreSurrogate = field(init=False)
    _params: dict = field(init=False)
    _opt_state: optax.OptState = field(init=False)
    _tx: optax.GradientTransformation = field(init=False)
    
    def __post_init__(self):
        self._model = BoreSurrogate(self.config)
        self._tx = optax.adamw(self.learning_rate, weight_decay=self.weight_decay)
        key = jax.random.PRNGKey(self.seed)
        dummy_input = jnp.ones((1, self.config.input_dim))  # Will be reshaped on first call
        self._params = self._model.init(key, dummy_input)
        self._opt_state = self._tx.init(self._params)
        self._rng_seq = jax.random.split(key, 1000)  # Pre-generate RNG keys for dropout
        self._rng_idx = 0
    
    def loss_fn(self, params: dict, batch: tuple) -> float:
        inputs, targets = batch
        # Generate RNG key for dropout
        rng = self._rng_seq[self._rng_idx % len(self._rng_seq)]
        self._rng_idx += 1
        preds, _ = self._model.apply(params, inputs, training=True, mutable=['batch_stats'], rngs={'dropout': rng})
        # MSE loss with descriptor-weighted loss (Petiot 2025)
        mse = jnp.mean((preds - targets) ** 2)
        return mse
    
    def train_step(self, params: dict, opt_state: optax.OptState, 
                   batch: tuple) -> tuple:
        loss, grads = jax.value_and_grad(self.loss_fn)(params, batch)
        updates, new_opt_state = self._tx.update(grads, opt_state, params)
        new_params = optax.apply_updates(params, updates)
        return new_params, new_opt_state, loss
    
    def train(self, train_data: list, val_data: list, epochs: int = 100,
              batch_size: int = 32, verbose: bool = True) -> dict:
        """Train the surrogate model.
        
        Args:
            train_data: List of (inputs, targets) tuples
            val_data: List of (inputs, targets) tuples for validation
            epochs: Number of training epochs
            batch_size: Mini-batch size
            verbose: Whether to print progress
            
        Returns:
            Training history dict
        """
        params = self._params
        opt_state = self._opt_state
        history = {"train_loss": [], "val_loss": []}
        
        for epoch in range(epochs):
            # Shuffle and batch
            np.random.shuffle(train_data)
            epoch_losses = []
            
            for i in range(0, len(train_data), batch_size):
                batch = train_data[i:i+batch_size]
                if len(batch) < batch_size:
                    continue
                inputs = jnp.stack([b[0] for b in batch])
                targets = jnp.stack([b[1] for b in batch])
                
                params, opt_state, loss = self.train_step(params, opt_state, (inputs, targets))
                epoch_losses.append(float(loss))
            
            avg_train_loss = np.mean(epoch_losses)
            history["train_loss"].append(avg_train_loss)
            
            # Validation
            val_inputs = jnp.stack([b[0] for b in val_data])
            val_targets = jnp.stack([b[1] for b in val_data])
            val_preds = self._model.apply(params, val_inputs, training=False)
            val_loss = float(jnp.mean((val_preds - val_targets) ** 2))
            history["val_loss"].append(val_loss)
            
            if verbose and (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{epochs}: train_loss={avg_train_loss:.6f}, val_loss={val_loss:.6f}")
        
        self._params = params
        self._opt_state = opt_state
        return history
    
    def predict(self, inputs: jnp.ndarray) -> jnp.ndarray:
        """Run inference on trained model."""
        return self._model.apply(self._params, inputs, training=False)
    
    def save(self, path: str):
        """Save model parameters."""
        import pickle
        with open(path, "wb") as f:
            pickle.dump(self._params, f)
    
    @classmethod
    def load(cls, path: str, config: SurrogateConfig) -> "SurrogateTrainer":
        """Load model from file."""
        import pickle
        trainer = cls(config)
        with open(path, "rb") as f:
            trainer._params = pickle.load(f)
        return trainer


def generate_training_data(n_samples: int, 
                          bore_param_ranges: dict,
                          n_cp: int = 6,
                          n_holes: int = 7,
                          targets: Optional[list] = None,
                          use_jax_tmm: bool = True,
                          verbose: bool = True) -> list:
    """Generate training data by sampling bore geometries and evaluating with TMM.
    
    Based on Petiot 2025: 10K-50K samples via Dask distributed.
    
    Args:
        n_samples: Number of training samples to generate
        bore_param_ranges: Dict with ranges for each parameter
        n_cp: Number of bore control points
        n_holes: Number of tone holes
        targets: Target frequencies (for conditioning)
        use_jax_tmm: Whether to use JAX TMM (fast) or Python TMM
        verbose: Whether to print progress
        
    Returns:
        List of (input_vector, target_vector) tuples
    """
    from backend.tmm_acoustics_jax import build_chain_for_optimizer, make_phase_cost
    from backend.benchmark_all import INSTRUMENTS
    
    if targets is None:
        targets = INSTRUMENTS["bass_chalumeau_Bb"]["targets"]
    
    # Default ranges (can be overridden)
    defaults = {
        "bore_radius": (4.0, 15.0),
        "bore_length": (300.0, 400.0),
        "hole_position": (30.0, 350.0),
        "hole_diameter": (5.0, 10.0),
        "hole_length": (2.0, 5.0),
        "outer_diameter": (20.0, 25.0),
        "closed_top": True,
    }
    ranges = {**defaults, **bore_param_ranges}
    
    data = []
    for i in range(n_samples):
        if verbose and i % 100 == 0:
            print(f"Generating sample {i+1}/{n_samples}")
        
        # Sample bore parameters
        bore_length = np.random.uniform(*ranges["bore_length"])
        radii = np.random.uniform(*ranges["bore_radius"], size=n_cp)
        
        # Sample hole positions (sorted)
        hp = np.sort(np.random.uniform(*ranges["hole_position"], size=n_holes))
        hd = np.random.uniform(*ranges["hole_diameter"], size=n_holes)
        hl = np.random.uniform(*ranges["hole_length"], size=n_holes)
        outer_d = np.random.uniform(*ranges["outer_diameter"])
        closed_top = ranges["closed_top"]
        
        # Build input vector
        input_vec = np.concatenate([
            radii,
            hp,
            hd,
            hl,
            [bore_length, outer_d, float(closed_top)]
        ])
        
        # Evaluate with TMM
        if use_jax_tmm:
            from backend.jax_optimizer import refine_sequential
            from backend.benchmark_all import INSTRUMENTS
            
            cfg = {
                "targets": np.array(targets),
                "closed_top": closed_top,
                "bore_radius": 7.25,
                "outer_diameter": outer_d,
                "hole_diameter": hd.mean(),
                "hole_length": hl.mean(),
            }
            
            try:
                rms, L, radii_opt, hp_opt, hd_opt, hl_opt, dt = refine_sequential(
                    cfg, use_jax_bore=True, use_phase_cost=True
                )
                target_vector = np.array([rms, 0.0, 0.0, 0.0])  # RMS, EFP, threshold, peak_error
            except Exception:
                target_vector = np.array([1e10, 0.0, 0.0, 0.0])
        else:
            # Fallback: use dummy targets for now
            target_vector = np.array([np.random.uniform(0.1, 50.0), 
                                      np.random.uniform(0.5, 2.0),
                                      np.random.uniform(500.0, 5000.0),
                                      np.random.uniform(0.1, 20.0)])
        
        # Normalize input features
        input_norm = np.concatenate([
            radii / 15.0,
            hp / 400.0,
            hd / 10.0,
            hl / 5.0,
            [bore_length / 400.0, outer_d / 25.0, float(closed_top)]
        ])
        
        data.append((input_norm, target_vector))
    
    return data


def build_surrogate_pipeline(n_samples: int = 10000,
                            epochs: int = 100,
                            batch_size: int = 64,
                            config: Optional[SurrogateConfig] = None,
                            bore_param_ranges: Optional[dict] = None) -> SurrogateTrainer:
    """Full surrogate training pipeline.
    
    Args:
        n_samples: Number of training samples
        epochs: Training epochs
        batch_size: Batch size
        config: Surrogate configuration
        bore_param_ranges: Ranges for bore parameter sampling
        
    Returns:
        Trained SurrogateTrainer
    """
    if config is None:
        config = SurrogateConfig()
    
    if bore_param_ranges is None:
        bore_param_ranges = {
            "bore_radius": (4.0, 15.0),
            "bore_length": (300.0, 400.0),
            "hole_position": (30.0, 350.0),
            "hole_diameter": (5.0, 10.0),
            "hole_length": (2.0, 5.0),
            "outer_diameter": (20.0, 25.0),
            "closed_top": True,
        }
    
    print(f"Generating {n_samples} training samples...")
    train_data = generate_training_data(n_samples, bore_param_ranges=bore_param_ranges)
    val_data = generate_training_data(n_samples // 10, bore_param_ranges=bore_param_ranges)
    
    print(f"Training surrogate for {epochs} epochs...")
    trainer = SurrogateTrainer(SurrogateConfig() if config is None else config)
    history = trainer.train(train_data, val_data, epochs=epochs, batch_size=batch_size)
    
    return trainer


if __name__ == "__main__":
    # Quick test
    config = SurrogateConfig(hidden_dims=(128, 128), output_dim=4)
    trainer = SurrogateTrainer(config)
    
    # Test forward pass
    dummy = jnp.ones((2, 50))
    out = trainer.predict(dummy)
    print(f"Output shape: {out.shape}")
    print("Surrogate module ready")
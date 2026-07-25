# Gaussian Process Correction Model — Experimental Design

## Goal
Learn TMM→FEM residual: Δf(geometry) = f_FEM - f_TMM
Use GP for uncertainty quantification and active learning (not neural networks).

## Why GP over Neural Network?
- FEM samples: hundreds/thousands (not millions)
- GP provides uncertainty → active learning
- Physics-friendly: kernel can encode known symmetries
- Easier debugging: no hidden layers
- Active learning reduces FEM runs by 10x

## Architecture

```python
class GPCorrector:
    """Physics-informed GP correction for TMM predictions."""
    
    def __init__(self, kernel="matern_3_2", active_learning=True):
        self.gp = GaussianProcessRegressor(kernel=kernel)
        self.X_train = []  # geometry features
        self.y_train = []  # FEM - TMM residuals (cents)
        self.active_learning = active_learning
    
    def features(self, network: AcousticNetwork) -> np.ndarray:
        """Extract geometry features for GP."""
        return np.array([
            network.total_length,
            network.segments[0].radius_in,
            network.n_toneholes,
            np.mean([p.radius for p in network.tonehole_ports]),
            np.std([p.position for p in network.tonehole_ports]),
            # ... more features
        ])
    
    def train(self, networks: List[AcousticNetwork], residuals: List[float]):
        """Train on (geometry, FEM - TMM) pairs."""
        X = np.array([self.features(n) for n in networks])
        y = np.array(residuals)
        self.gp.fit(X, y)
    
    def predict(self, network: AcousticNetwork) -> Tuple[float, float]:
        """Return (correction_cents, uncertainty)."""
        x = self.features(network).reshape(1, -1)
        mean, std = self.gp.predict(x, return_std=True)
        return mean[0], std[0]
    
    def active_learning_step(self, candidate_networks: List[AcousticNetwork]) -> int:
        """Select network with highest GP uncertainty for next FEM run."""
        uncertainties = [self.predict(n)[1] for n in candidate_networks]
        return np.argmax(uncertainties)
```

## Active Learning Loop

```
1. Start with 20-50 random geometries
2. Compute TMM + FEM for each → training data
3. Train GP on (geometry, FEM - TMM)
4. Optimizer proposes new geometry
5. GP predicts correction + uncertainty
6. If uncertainty > threshold → run FEM, add to training
7. Else use GP correction directly
8. Repeat from step 3
```

## Kernel Design

Physics-informed kernel combining:
- RBF for smooth variations
- Matern 3/2 for non-smooth boundaries (tonehole edges)
- Periodic for register harmonicity
- Linear for bore length scaling

```python
kernel = (
    1.0 * RBF(length_scale=100) +
    1.0 * Matern(length_scale=50, nu=1.5) +
    0.5 * ExpSineSquared(length_scale=1200, periodicity=3)  # harmonic spacing
)
```

## Integration with Optimization

```python
def corrected_cost(network, targets, gp_corrector):
    tmm_freqs = tmm_solver.compute_frequencies(network, targets)
    correction, uncertainty = gp_corrector.predict(network)
    corrected_freqs = tmm_freqs * 2**(correction/1200)
    return intonation_cost(corrected_freqs, targets) + lambda * uncertainty
```

## Expected Impact
- 10x reduction in FEM evaluations
- Uncertainty-aware optimization
- Identifies where TMM model breaks down
- Natural path to neural network when data scales

## ChatGPT Reference
From 2026-07-24 review: "GP advantages: uncertainty estimates, active learning, identifies regions needing FEM, physics-friendly, easier debugging. Active learning loop: Optimizer → TMM → GP uncertainty → Choose next FEM sample → Retrain. Could reduce FEM runs by order of magnitude."
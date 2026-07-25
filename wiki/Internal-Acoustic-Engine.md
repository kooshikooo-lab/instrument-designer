# Acoustic Engine

## Transfer Matrix Method (TMM)

The TMM models sound propagation through cylindrical/conical pipe segments by tracking acoustic impedance (or admittance) from one end to the other.

### Phase Convention

```python
SPEED_OF_SOUND = 346100.0  # cm/s (matches chalumier)

def tanner(phase):
    """Convert phase to tangent domain (normalized admittance)."""
    return math.tan(phase * math.pi)

def untanner(x):
    """Convert from tangent domain back to phase."""
    return math.atan(x) / math.pi

def pipe_reply_phase(phase_end, length_on_wavelength):
    """Advance phase through a pipe segment: φ += 2L/λ"""
    return phase_end + length_on_wavelength * 2.0
```

### Core Operations

| Operation | Function | Purpose |
|-----------|----------|---------|
| `tanner(φ)` | `tan(π·φ)` | Phase → normalized admittance |
| `untanner(x)` | `atan(x)/π` | Admittance → phase |
| `pipe_reply_phase(φ, L/λ)` | `φ + 2L/λ` | Phase advance through cylinder |
| `junction2_reply_phase(a0, a1, p1)` | Area-weighted sum | Bore diameter step |
| `junction3_reply_phase(a0, a1, a2, p1, p2)` | Parallel admittance | Tone hole junction |

### Resonance Condition

Starting from the mouthpiece end (phase = 0.5 for open, 0.0 for closed), phase is walked through all segments. At the far open end, +0.5 is added. Resonance occurs when total phase is an integer:

```
Open-open:   0.5 (mouth) + 2L/λ + 0.5 (bell) = n  →  λ = 2L/(n-1)
Closed-open: 0.0 (reed) + 2L/λ + 0.5 (bell) = n  →  λ = 4L/(2n-1)
```

### n_register

| n_register | Open-open (flute/sax) | Closed-open (clarinet) |
|-----------|----------------------|----------------------|
| 1 | DC (f=0) — not physical | Fundamental |
| 2 | **Fundamental** | 3rd harmonic |
| 3 | 2nd harmonic (octave key) | 5th harmonic |

Auto-detection: `n_register = 1 if closed_top else 2`

## Viscothermal Losses (KeefeLoss)

### Model

Keefe (1984) with Sutherland's temperature correction:

```python
class KeefeLoss:
    def bore_loss(self, freq, radius, length):
        """Complex loss factor for bore propagation."""
        # Skin depth: δ = sqrt(2η / ρω)
        # Loss factor: exp(-k·L·(1+j)·√(f/f_crit))
        # Temperature correction via Sutherland's law
        return complex_loss_factor

    def hole_loss(self, freq, radius, chimney_height):
        """Complex loss factor for tone hole propagation."""
        return complex_loss_factor
```

### Integration

Losses are applied per pipe segment in the action chain:

```python
# In tmm_acoustics.py
def pipe_reply_phase_with_loss(phase_end, length_on_wavelength, loss_factor):
    """Phase advance with viscothermal losses."""
    # Phase shift from losses
    loss_phase = np.angle(loss_factor) / np.pi
    # Amplitude attenuation
    loss_mag = np.abs(loss_factor)
    return phase_end + length_on_wavelength * 2.0 + loss_phase, loss_mag
```

### Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Dynamic viscosity (η) | 1.846e-5 Pa·s | Air at 20°C |
| Density (ρ) | 1.204 kg/m³ | Air at 20°C |
| Ratio of specific heats (γ) | 1.4 | Diatomic gas |
| Sutherland temperature | 291.15 K | Standard |
| Prandtl number | 0.71 | Air |

## Tone Hole Modeling

### Junction3 (Tone Hole)

```python
def junction3_reply_phase(a0, a1, a2, p1, p2):
    """a0 = bore before, a1 = bore after, a2 = hole area"""
    return untanner(a1/a0 * tanner(p1) + a2/a0 * tanner(p2))
```

### Length Corrections (Keefe/Nederveen)

- **Open hole:** `correction = a · (inner + outer)` where `inner = 1.3 - 0.9·d_hole/d_bore`, `outer = 0.7`
- **Closed hole:** correction = 0 (acts as closed side branch)
- **End flange (Nederveen):** `a · (0.821 - 0.13 · (0.42 + w/a)^(-0.54))`

## Radiation Models

Simplified end corrections. Full FEM radiation available via OpenWInD solver.

## Speed of Sound

| Module | Value | Temperature | Notes |
|--------|-------|-------------|-------|
| tmm_acoustics.py | 346100 cm/s | ~25°C | Matches chalumier |
| tmm_optimizer_v2.py | 343400 cm/s | 20°C | Inconsistent |
| bore_optimizer.py | 343500 cm/s | 20°C | Inconsistent |
| losses.py | 343200 cm/s | ~20°C | Inconsistent |

**Needs standardization.** All modules should use the same value.

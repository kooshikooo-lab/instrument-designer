# Laptop Task — OpenWInD v0.13 Integration Testing

## Overview
Test OpenWInD v0.13 as a validation/benchmark tool for our TMM optimizer.

## Steps

### 1. Install OpenWInD
```bash
pip install openwind
```

### 2. Test Basic TMM
```python
from openwind import InstrumentGeometry, run_tmm
# Create a simple cylindrical bore (diameter=20mm, length=500mm)
# Compare impedance peaks with our tmm_acoustics.py
```

### 3. Test FEM Optimization
```python
from openwind.optimization import optimize_bore
# Use our known-good Buffet R13 bore as starting point
# Test impedance-based reconstruction
```

### 4. Validate Against Our Results
- Compare resonance frequencies for Buffet R13 bore
- Measure accuracy and computation time
- Document any discrepancies

### 5. Document Findings
- Write results to `chat-logs/2026-07-23-openwind-validation.md`
- Commit to `experiment/flute-pvc` branch
- Push to GitHub for cross-machine access

## Expected Output
- Comparison table: OpenWInD vs our TMM (frequency, computation time)
- Recommendation: Is OpenWInD suitable as validation tool?
- Any integration issues or limitations found

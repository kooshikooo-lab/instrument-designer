import numpy as np
from backend.tmm_acoustics import tmm_instrument_from_radii, KeefeLoss

# Test basic creation with loss model
loss = KeefeLoss()
inst = tmm_instrument_from_radii(
    np.array([7.5]*10), 600.0, 
    [100, 200], [5.0, 5.0], [3.0, 3.0],
    loss_model=loss
)
print('Instrument created with loss model:', inst.loss_model is not None)

# Test loss calculation
factor = loss.bore_loss(100.0, 7.5, 500.0)
print(f'Bore loss factor: {factor}')
print('Test passed!')
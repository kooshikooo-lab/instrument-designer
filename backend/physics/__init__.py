"""Physics plugins package."""
from .propagation import PropagationModel, LosslessPropagation
from .junction import JunctionModel, LosslessJunction
from .tonehole import ToneholeModel, SimpleTonehole
from .radiation import RadiationModel, BesselRadiation
from .losses import LossModel, NoLoss
from .excitation import ExcitationModel, ReedExcitation

__all__ = [
    "PropagationModel", "LosslessPropagation",
    "JunctionModel", "LosslessJunction",
    "ToneholeModel", "SimpleTonehole",
    "RadiationModel", "BesselRadiation",
    "LossModel", "NoLoss",
    "ExcitationModel", "ReedExcitation",
]

"""Bass clarinet builder.

Builds an AcousticNetwork specifically for bass clarinet.
"""
from typing import List
import numpy as np

from .clarinet import ClarinetBuilder
from ..core.network import AcousticNetwork


class BassClarinetBuilder(ClarinetBuilder):
    """Build an AcousticNetwork for bass clarinet.

    Convenience wrapper with typical bass clarinet defaults.
    """

    def __init__(self):
        super().__init__()
        # Default bass clarinet dimensions
        self._segments = []
        self._ports = []
        self._register_vent = None
        self._bell_radius = None

    @classmethod
    def standard(cls, bore_length: float = 1200.0, bore_radius: float = 12.5):
        """Create a standard bass clarinet.

        Args:
            bore_length: bore length in mm (default 1200)
            bore_radius: bore radius in mm (default 12.5, giving 25mm diameter)
        """
        builder = cls()
        builder.set_bore(length=bore_length, radius=bore_radius)
        builder.set_register_vent(position=80.0, radius=1.25, length=3.0)
        return builder

    @classmethod
    def extended(cls, bore_length: float = 1470.0, bore_radius: float = 12.5):
        """Create an extended (low C) bass clarinet."""
        builder = cls()
        builder.set_bore(length=bore_length, radius=bore_radius)
        builder.set_register_vent(position=80.0, radius=1.25, length=3.0)
        return builder

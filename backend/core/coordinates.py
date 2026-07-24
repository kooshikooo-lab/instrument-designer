"""Coordinate transform module.

Every coordinate conversion goes through this module.
No code outside this module should ever convert coordinates directly.

Coordinate systems:
- Chalumier: position 0 = bell (open end), position L = reed (closed end)
- Internal:  position 0 = reed (closed end), position L = bell (open end)
- OpenWInD:  position 0 = mouthpiece (closed end), position L = bell (open end)
"""


class CoordinateTransform:
    """Centralized coordinate conversion between different TMM/FEM conventions."""

    @staticmethod
    def chalumier_to_internal(x_chalumier: float, bore_length: float) -> float:
        """Convert chalumier position to internal position.

        Chalumier: 0 = bell, L = reed
        Internal:  0 = reed, L = bell
        """
        return bore_length - x_chalumier

    @staticmethod
    def internal_to_chalumier(x_internal: float, bore_length: float) -> float:
        """Convert internal position to chalumier position."""
        return bore_length - x_internal

    @staticmethod
    def openwind_to_internal(x_openwind: float) -> float:
        """Convert OpenWInD position to internal position.

        Both use same convention: 0 = closed end, L = open end.
        This is an identity transform for now, but kept for future-proofing.
        """
        return x_openwind

    @staticmethod
    def internal_to_openwind(x_internal: float) -> float:
        """Convert internal position to OpenWInD position."""
        return x_internal

    @staticmethod
    def chalumier_to_openwind(x_chalumier: float, bore_length: float) -> float:
        """Convert chalumier position to OpenWInD position."""
        return bore_length - x_chalumier

    @staticmethod
    def openwind_to_chalumier(x_openwind: float, bore_length: float) -> float:
        """Convert OpenWInD position to chalumier position."""
        return bore_length - x_openwind

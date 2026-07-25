"""Coordinate transform module.

Every coordinate conversion goes through this module.
No code outside this module should ever convert coordinates directly.

Coordinate systems:
- Chalumier: position 0 = bell (open end), position L = reed (closed end)
- Internal:  position 0 = bell (open end), position L = reed (closed end)
- OpenWInD:  position 0 = mouthpiece (closed end), position L = bell (open end)

Our internal convention matches chalumier: 0 = bell, L = reed.
TMM walk starts at position 0 with phase = 0.5 (open end / bell)
and walks toward position L (closed end / reed).
"""


class CoordinateTransform:
    """Centralized coordinate conversion between different TMM/FEM conventions."""

    @staticmethod
    def chalumier_to_internal(x_chalumier: float, bore_length: float = 0.0) -> float:
        """Convert chalumier position to internal position.

        Both use same convention: 0 = bell, L = reed.
        Identity transform.
        """
        return x_chalumier

    @staticmethod
    def internal_to_chalumier(x_internal: float, bore_length: float = 0.0) -> float:
        """Convert internal position to chalumier position.

        Both use same convention: 0 = bell, L = reed.
        Identity transform.
        """
        return x_internal

    @staticmethod
    def openwind_to_internal(x_openwind: float, bore_length: float = 0.0) -> float:
        """Convert OpenWInD position to internal position.

        OpenWInD: 0 = mouthpiece (closed end), L = bell (open end)
        Internal: 0 = bell (open end), L = reed (closed end)
        """
        return bore_length - x_openwind

    @staticmethod
    def internal_to_openwind(x_internal: float, bore_length: float = 0.0) -> float:
        """Convert internal position to OpenWInD position.

        Internal: 0 = bell, L = reed
        OpenWInD: 0 = mouthpiece (closed end), L = bell
        """
        return bore_length - x_internal

    @staticmethod
    def chalumier_to_openwind(x_chalumier: float, bore_length: float = 0.0) -> float:
        """Convert chalumier position to OpenWInD position.

        Chalumier: 0 = bell, L = reed
        OpenWInD:  0 = mouthpiece (closed end), L = bell
        """
        return bore_length - x_chalumier

    @staticmethod
    def openwind_to_chalumier(x_openwind: float, bore_length: float = 0.0) -> float:
        """Convert OpenWInD position to chalumier position.

        OpenWInD:  0 = mouthpiece (closed end), L = bell
        Chalumier: 0 = bell, L = reed
        """
        return bore_length - x_openwind

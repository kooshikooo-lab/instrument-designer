"""Coordinate transform module.

Every coordinate conversion goes through this module.
No code outside this module should ever convert coordinates directly.

Coordinate systems:
- Chalumier: position 0 = bell (open end), position L = reed (closed end)
- Internal:  position 0 = bell (open end), position L = reed (closed end)
- OpenWind:  position 0 = mouthpiece (closed end), position L = bell (open end)

Our internal convention matches chalumier: 0 = bell, L = reed.
TMM walk starts at position 0 with phase = 0.5 (open end / bell)
and walks toward position L (closed end / reed).

All transforms require an explicit ``bore_length``.  A missing length must
fail loudly (``TypeError``) rather than silently producing negative or
mirrored positions, and every position is bounds-checked against
``[0, bore_length]``.
"""

__all__ = ["CoordinateTransform"]


class CoordinateTransform:
    """Centralized coordinate conversion between different TMM/FEM conventions."""

    @staticmethod
    def _check(x: float, bore_length: float, name: str) -> None:
        if not (0.0 <= x <= bore_length):
            raise ValueError(
                f"{name} position {x} out of bounds [0, {bore_length}]"
            )

    @staticmethod
    def chalumier_to_internal(x_chalumier: float, bore_length: float) -> float:
        """Convert chalumier position to internal position.

        Both use the same convention: 0 = bell, L = reed.
        Identity transform.
        """
        CoordinateTransform._check(x_chalumier, bore_length, "chalumier")
        return x_chalumier

    @staticmethod
    def internal_to_chalumier(x_internal: float, bore_length: float) -> float:
        """Convert internal position to chalumier position.

        Both use the same convention: 0 = bell, L = reed.
        Identity transform.
        """
        CoordinateTransform._check(x_internal, bore_length, "internal")
        return x_internal

    @staticmethod
    def openwind_to_internal(x_openwind: float, bore_length: float) -> float:
        """Convert OpenWind position to internal position.

        OpenWind: 0 = mouthpiece (closed end), L = bell (open end)
        Internal: 0 = bell (open end), L = reed (closed end)
        """
        CoordinateTransform._check(x_openwind, bore_length, "openwind")
        return bore_length - x_openwind

    @staticmethod
    def internal_to_openwind(x_internal: float, bore_length: float) -> float:
        """Convert internal position to OpenWind position.

        Internal: 0 = bell, L = reed
        OpenWind: 0 = mouthpiece (closed end), L = bell
        """
        CoordinateTransform._check(x_internal, bore_length, "internal")
        return bore_length - x_internal

    @staticmethod
    def chalumier_to_openwind(x_chalumier: float, bore_length: float) -> float:
        """Convert chalumier position to OpenWind position.

        Chalumier: 0 = bell, L = reed
        OpenWind:  0 = mouthpiece (closed end), L = bell
        """
        CoordinateTransform._check(x_chalumier, bore_length, "chalumier")
        return bore_length - x_chalumier

    @staticmethod
    def openwind_to_chalumier(x_openwind: float, bore_length: float) -> float:
        """Convert OpenWind position to chalumier position.

        OpenWind:  0 = mouthpiece (closed end), L = bell
        Chalumier: 0 = bell, L = reed
        """
        CoordinateTransform._check(x_openwind, bore_length, "openwind")
        return bore_length - x_openwind

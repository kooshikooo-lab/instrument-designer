import pytest
import backend.tmm_acoustics


def test_import_tmm_acoustics():
    assert backend.tmm_acoustics is not None, "Failed to import backend.tmm_acoustics"


if __name__ == "__main__":
    test_import_tmm_acoustics()
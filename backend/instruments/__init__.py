"""Instrument definitions.

Each instrument type builds an AcousticNetwork from parameters.
The instrument does NOT know which solver will process it.
"""
from .clarinet import ClarinetBuilder
from .bass_clarinet import BassClarinetBuilder
from .brass import BrassBuilder

__all__ = ["ClarinetBuilder", "BassClarinetBuilder", "BrassBuilder"]

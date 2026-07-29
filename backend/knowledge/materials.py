"""Core enums and dataclasses for instrument physics."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BoreType(Enum):
    CYLINDRICAL = "cylindrical"
    CONICAL = "conical"
    PARABOLIC = "parabolic"
    EXPONENTIAL = "exponential"
    BESSEL = "bessel"
    COMPOUND = "compound"


class ExcitationType(Enum):
    REED = "reed"
    DOUBLE_REED = "double_reed"
    FLUTE_LIP = "flute_lip"
    LIP_REED = "lip_reed"
    AIR_REED = "air_reed"


class MaterialType(Enum):
    BRASS = "brass"
    WOOD = "wood"
    PLASTIC = "plastic"
    PVC = "pvc"
    BAMBOO = "bamboo"
    CARBON_FIBER = "carbon_fiber"
    ALUMINUM = "aluminum"
    SILVER = "silver"
    BELL_METAL = "bell_metal"


@dataclass
class MaterialProperties:
    """Acoustic properties of construction materials."""
    name: str
    density_kg_m3: float
    speed_of_sound_m_s: float
    surface_roughness_um: float
    loss_factor: float
    radiation_efficiency: float
    thermal_conductivity: float
    description: str = ""

    @property
    def loss_quality(self) -> str:
        if self.loss_factor < 0.01:
            return "low_loss"
        elif self.loss_factor < 0.05:
            return "medium_loss"
        return "high_loss"


MATERIALS: dict[MaterialType, MaterialProperties] = {
    MaterialType.BRASS: MaterialProperties(
        name="Brass",
        density_kg_m3=8500,
        speed_of_sound_m_s=3480,
        surface_roughness_um=2.0,
        loss_factor=0.001,
        radiation_efficiency=0.95,
        thermal_conductivity=120.0,
        description="Standard brass instrument material. High radiation efficiency, low loss.",
    ),
    MaterialType.WOOD: MaterialProperties(
        name="Wood (grenadilla)",
        density_kg_m3=1200,
        speed_of_sound_m_s=4500,
        surface_roughness_um=10.0,
        loss_factor=0.02,
        radiation_efficiency=0.7,
        thermal_conductivity=0.2,
        description="Traditional clarinet/oboe material. Higher surface roughness adds warmth.",
    ),
    MaterialType.PLASTIC: MaterialProperties(
        name="Plastic (ABS/PLA)",
        density_kg_m3=1050,
        speed_of_sound_m_s=2100,
        surface_roughness_um=5.0,
        loss_factor=0.03,
        radiation_efficiency=0.75,
        thermal_conductivity=0.15,
        description="3D-printable material. Affordable, consistent, moderate losses.",
    ),
    MaterialType.PVC: MaterialProperties(
        name="PVC",
        density_kg_m3=1400,
        speed_of_sound_m_s=2300,
        surface_roughness_um=3.0,
        loss_factor=0.02,
        radiation_efficiency=0.72,
        thermal_conductivity=0.16,
        description="Common DIY instrument material. Smooth bore, easy to work.",
    ),
    MaterialType.BAMBOO: MaterialProperties(
        name="Bamboo",
        density_kg_m3=700,
        speed_of_sound_m_s=5000,
        surface_roughness_um=20.0,
        loss_factor=0.04,
        radiation_efficiency=0.6,
        thermal_conductivity=0.16,
        description="Traditional material for flutes, shakuhachi, bansuri. High roughness.",
    ),
    MaterialType.CARBON_FIBER: MaterialProperties(
        name="Carbon Fiber",
        density_kg_m3=1600,
        speed_of_sound_m_s=1300,
        surface_roughness_um=1.0,
        loss_factor=0.005,
        radiation_efficiency=0.9,
        thermal_conductivity=7.0,
        description="Modern high-performance material. Very smooth, low loss, lightweight.",
    ),
    MaterialType.ALUMINUM: MaterialProperties(
        name="Aluminum",
        density_kg_m3=2700,
        speed_of_sound_m_s=6300,
        surface_roughness_um=1.5,
        loss_factor=0.002,
        radiation_efficiency=0.92,
        thermal_conductivity=237.0,
        description="Lightweight metal. Used in marching band instruments.",
    ),
    MaterialType.SILVER: MaterialProperties(
        name="Silver",
        density_kg_m3=10500,
        speed_of_sound_m_s=3650,
        surface_roughness_um=1.0,
        loss_factor=0.0008,
        radiation_efficiency=0.96,
        thermal_conductivity=429.0,
        description="Premium brass material. Excellent radiation, very low loss.",
    ),
    MaterialType.BELL_METAL: MaterialProperties(
        name="Bell Metal",
        density_kg_m3=8800,
        speed_of_sound_m_s=3400,
        surface_roughness_um=2.5,
        loss_factor=0.0005,
        radiation_efficiency=0.98,
        thermal_conductivity=110.0,
        description="High-copper brass alloy. Maximum radiation, used for bells.",
    ),
}
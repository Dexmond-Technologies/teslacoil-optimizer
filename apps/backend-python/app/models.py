from pydantic import BaseModel, Field
from typing import Optional, List

class CoilSpecs(BaseModel):
    turns: float = Field(..., gt=0)
    wire_gauge_awg: int = Field(..., ge=-10, le=40) # Allow huge gauges for MW
    diameter_mm: float = Field(..., gt=0)
    height_mm: float = Field(..., gt=0)
    material: str = Field("Copper", description="Copper, Aluminum, or NbTi_Superconductor")
    cooling_system: str = Field("Air", description="Air, Oil, or LN2_Cryo")

class CapacitorSpecs(BaseModel):
    capacitance_nf: float = Field(..., gt=0)
    voltage_rating_kv: float = Field(..., gt=0)

class ToroidSpecs(BaseModel):
    major_diameter_mm: float = Field(..., gt=0)
    minor_diameter_mm: float = Field(..., gt=0)

class PowerSource(BaseModel):
    voltage_v: float = Field(..., gt=0)
    frequency_hz: float = Field(..., gt=0)
    type: str = Field(..., description="NST, MOT, SSTC, DRSSTC, or MW_Grid_Tap")

class InfrastructureSpecs(BaseModel):
    target_distance_km: float = Field(1.0, ge=0)
    phased_array_nodes: int = Field(1, ge=1)
    sync_ms: float = Field(0.0, ge=0)

class EnvironmentalSpecs(BaseModel):
    altitude_m: float = Field(0.0)
    humidity_pct: float = Field(50.0)

class OptimizationInput(BaseModel):
    primary_coil: CoilSpecs
    secondary_coil: CoilSpecs
    top_load: ToroidSpecs
    primary_capacitor: CapacitorSpecs
    power_source: PowerSource
    infrastructure: InfrastructureSpecs
    environment: EnvironmentalSpecs
    frontier_mode: bool = Field(False)

class SafetyFlags(BaseModel):
    level: str  # "Green", "Yellow", "Red", "Frontier"
    warnings: List[str]

class OptimizationResult(BaseModel):
    primary_resonant_frequency_khz: float
    secondary_resonant_frequency_khz: float
    coupling_k: float
    efficiency_estimate_pct: float
    estimated_spark_length_m: float
    city_power_delivery_kw: float
    safety_profile: SafetyFlags

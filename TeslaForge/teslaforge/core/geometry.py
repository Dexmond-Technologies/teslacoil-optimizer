"""
Parametric geometry models for Tesla Coil components.
Uses Pydantic for validation to ensure physical constraints are met.
"""
from pydantic import BaseModel, Field, model_validator
import math

class Wire(BaseModel):
    diameter_mm: float = Field(..., gt=0, description="Bare wire diameter in mm")
    insulation_thickness_mm: float = Field(0.0, ge=0, description="Insulation thickness in mm")

    @property
    def outer_diameter_mm(self) -> float:
        return self.diameter_mm + 2 * self.insulation_thickness_mm

class PrimaryCoil(BaseModel):
    inner_radius_mm: float = Field(..., gt=0, description="Inner radius of the primary coil in mm")
    turns: float = Field(..., gt=0, description="Number of turns")
    wire: Wire
    turn_spacing_mm: float = Field(..., ge=0, description="Edge-to-edge spacing between turns")
    
    @property
    def outer_radius_mm(self) -> float:
        return self.inner_radius_mm + self.turns * (self.wire.outer_diameter_mm + self.turn_spacing_mm)
        
    @property
    def average_radius_mm(self) -> float:
        return (self.inner_radius_mm + self.outer_radius_mm) / 2.0
        
    @property
    def width_mm(self) -> float:
        return self.outer_radius_mm - self.inner_radius_mm

class SecondaryCoil(BaseModel):
    radius_mm: float = Field(..., gt=0, description="Radius of the secondary coil form in mm")
    turns: int = Field(..., gt=0, description="Number of turns")
    wire: Wire
    turn_spacing_mm: float = Field(0.0, ge=0, description="Edge-to-edge spacing between turns (usually 0 for close-wound)")
    
    @property
    def height_mm(self) -> float:
        # Number of turns * (wire diameter + spacing)
        return self.turns * (self.wire.outer_diameter_mm + self.turn_spacing_mm)
        
    @property
    def wire_length_m(self) -> float:
        return (2 * math.pi * (self.radius_mm + self.wire.outer_diameter_mm/2.0) * self.turns) / 1000.0

class Topload(BaseModel):
    major_diameter_mm: float = Field(..., gt=0, description="Overall outer diameter in mm")
    minor_diameter_mm: float = Field(..., gt=0, description="Cord/tube diameter in mm")

    @model_validator(mode='after')
    def check_diameters(self):
        if self.minor_diameter_mm >= self.major_diameter_mm:
            raise ValueError("Minor diameter must be strictly less than major diameter")
        return self

import math
import numpy as np
from teslaforge.core.physics import (
    calc_helical_inductance_wheeler,
    calc_resonant_frequency,
    calc_toroid_capacitance,
    calc_mutual_inductance_neumann,
)


def test_wheeler_inductance():
    r_m = 0.1016
    h_m = 0.508
    turns = 1000

    L = calc_helical_inductance_wheeler(r_m, h_m, turns)
    assert math.isclose(L, 0.06779, rel_tol=1e-3)


def test_resonant_freq():
    L = 100e-6  # 100 uH
    C = 100e-9  # 100 nF
    F = calc_resonant_frequency(L, C)
    assert math.isclose(F, 50329.21, rel_tol=1e-3)


def test_toroid_cap():
    C = calc_toroid_capacitance(24 * 0.0254, 6 * 0.0254)
    assert math.isclose(C, 24.36 * 1e-12, rel_tol=1e-2)


def test_neumann_mutual_inductance():
    # Coaxial loops separated by some distance
    # Turn 1: r=100mm, z=0
    # Turn 2: r=100mm, z=50mm
    r_pri = np.array([0.1])
    z_pri = np.array([0.0])
    r_sec = np.array([0.1])
    z_sec = np.array([0.05])

    M = calc_mutual_inductance_neumann(r_pri, z_pri, r_sec, z_sec)
    # Expected value from analytical physics: around 0.111 uH (1.1126e-7 H)
    assert math.isclose(M, 1.1126e-07, rel_tol=1e-2)


def test_skin_effect_and_ac_resistance():
    from teslaforge.core.physics import calc_skin_depth, calc_ac_resistance

    # 1. Skin depth at 100 kHz (should be approx 0.206 mm for copper)
    delta_100k = calc_skin_depth(100e3)
    assert math.isclose(delta_100k, 0.000206, rel_tol=1e-2)

    # 2. DC frequency check (delta should be inf)
    assert calc_skin_depth(0) == float("inf")

    # 3. AC resistance check
    r_dc = 10.0
    wire_radius = 0.0005  # 1mm diameter wire (0.5mm radius)

    # At DC, R_ac == R_dc
    assert calc_ac_resistance(r_dc, wire_radius, 0) == r_dc

    # At high freq (e.g. 1 MHz), R_ac should be significantly larger than R_dc
    r_ac_1m = calc_ac_resistance(r_dc, wire_radius, 1e6)
    assert r_ac_1m > r_dc


def test_secondary_coil_resistances():
    from teslaforge.core.geometry import Wire, SecondaryCoil

    # Use a thicker wire so that the radius (1.0mm) is larger than 2 * skin_depth at 100 kHz (0.412mm)
    wire = Wire(diameter_mm=2.0, insulation_thickness_mm=0.05)
    sec = SecondaryCoil(radius_mm=50, turns=500, wire=wire)

    # Verify DC resistance is calculated correctly
    assert sec.dc_resistance_ohms > 0.0

    # Verify AC resistance increases with frequency
    r_dc = sec.dc_resistance_ohms
    r_ac_100k = sec.ac_resistance_ohms(100e3)
    r_ac_1m = sec.ac_resistance_ohms(1e6)

    assert r_ac_100k > r_dc
    assert r_ac_1m > r_ac_100k


def test_dowell_proximity_effect():
    from teslaforge.core.physics import calc_dowell_proximity_factor, calc_ac_resistance
    from teslaforge.core.geometry import Wire, SecondaryCoil

    # 1. Verification of baseline boundary cases
    # Skin depth of infinity means no HF losses -> factor should be 1.0
    factor_dc = calc_dowell_proximity_factor(0.001, float("inf"), 0.002)
    assert math.isclose(factor_dc, 1.0)

    # 2. Multi-layer loss increase verification
    # Two layers should have higher proximity loss factor than one layer
    factor_1layer = calc_dowell_proximity_factor(0.001, 0.0002, 0.002, layers=1)
    factor_2layers = calc_dowell_proximity_factor(0.001, 0.0002, 0.002, layers=2)
    assert factor_2layers > factor_1layer

    # 3. Integration verification on SecondaryCoil
    wire = Wire(diameter_mm=1.0, insulation_thickness_mm=0.02)
    sec = SecondaryCoil(radius_mm=50, turns=400, wire=wire, turn_spacing_mm=0.1)

    # AC resistance with proximity effect (pitch passed) should be higher than skin effect alone
    r_dc = sec.dc_resistance_ohms
    r_ac_skin_only = calc_ac_resistance(r_dc, 0.0005, 200e3, pitch_m=None)
    r_ac_proximity = sec.ac_resistance_ohms(200e3)

    assert r_ac_proximity > r_ac_skin_only
    assert r_ac_proximity > r_dc

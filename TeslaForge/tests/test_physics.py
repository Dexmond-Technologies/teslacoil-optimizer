import math
import numpy as np
from teslaforge.core.physics import (
    calc_helical_inductance_wheeler,
    calc_resonant_frequency,
    calc_toroid_capacitance,
    calc_mutual_inductance_neumann,
    calc_coupling_coefficient
)

def test_wheeler_inductance():
    r_m = 0.1016
    h_m = 0.508
    turns = 1000
    
    L = calc_helical_inductance_wheeler(r_m, h_m, turns)
    assert math.isclose(L, 0.06779, rel_tol=1e-3)

def test_resonant_freq():
    L = 100e-6 # 100 uH
    C = 100e-9 # 100 nF
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

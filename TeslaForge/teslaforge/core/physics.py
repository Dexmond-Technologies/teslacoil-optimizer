"""
Rigorous mathematical calculations for Tesla Coil engineering.
Implements formulas from Wheeler, Medhurst, and Neumann's Mutual Inductance via Elliptic Integrals.
"""
import math
import numpy as np
from scipy.special import ellipk, ellipe

MU_0 = 4.0 * math.pi * 1e-7  # Permeability of free space (H/m)
EPSILON_0 = 8.8541878128e-12 # Permittivity of free space (F/m)
C_LIGHT = 299792458 # Speed of light (m/s)

def calc_helical_inductance_wheeler(radius_m: float, height_m: float, turns: float) -> float:
    """
    Wheeler's formula for helical coils.
    Accurate for single-layer solenoids.
    Returns inductance in Henrys.
    """
    r_in = radius_m * 39.3701
    h_in = height_m * 39.3701
    if r_in <= 0 or h_in <= 0:
        return 0.0
    L_uH = (r_in**2 * turns**2) / (9 * r_in + 10 * h_in)
    return L_uH * 1e-6

def calc_flat_spiral_inductance_wheeler(inner_radius_m: float, outer_radius_m: float, turns: float) -> float:
    """
    Wheeler's formula for flat spiral (pancake) coils.
    Returns inductance in Henrys.
    """
    avg_r_in = ((inner_radius_m + outer_radius_m) / 2.0) * 39.3701
    width_in = (outer_radius_m - inner_radius_m) * 39.3701
    if avg_r_in <= 0 or width_in <= 0:
        return 0.0
    L_uH = (avg_r_in**2 * turns**2) / (8 * avg_r_in + 11 * width_in)
    return L_uH * 1e-6

def calc_medhurst_capacitance(radius_m: float, height_m: float) -> float:
    """
    Medhurst formula for self-capacitance of a solenoid.
    Returns capacitance in Farads.
    """
    D = 2.0 * radius_m
    H = height_m
    if D <= 0 or H <= 0:
        return 0.0
    
    ratio = H / D
    D_cm = D * 100.0
    ratio = max(ratio, 0.1)
    
    C_pF = D_cm * (0.1126 * ratio + 0.08 + 0.27 / math.sqrt(ratio))
    return C_pF * 1e-12

def calc_toroid_capacitance(major_dia_m: float, minor_dia_m: float) -> float:
    """
    Isotropic capacity of a torus.
    Returns capacitance in Farads.
    """
    d1_in = (major_dia_m - minor_dia_m) * 39.3701
    d2_in = minor_dia_m * 39.3701
    
    if d1_in <= 0 or d2_in <= 0:
        return 0.0
        
    C_pF = 1.4 * (1.2781 - (d2_in / d1_in)) * math.sqrt(math.pi * d2_in * d1_in)
    return C_pF * 1e-12

def calc_resonant_frequency(L_henrys: float, C_farads: float) -> float:
    """
    Calculate resonant frequency f = 1 / (2 * pi * sqrt(L * C)).
    Returns frequency in Hertz.
    """
    if L_henrys <= 0 or C_farads <= 0:
        return 0.0
    return 1.0 / (2 * math.pi * math.sqrt(L_henrys * C_farads))

def calc_mutual_inductance_neumann(
    r_pri_turns: np.ndarray, 
    z_pri_turns: np.ndarray, 
    r_sec_turns: np.ndarray, 
    z_sec_turns: np.ndarray
) -> float:
    """
    Calculates the mutual inductance between primary and secondary using Neumann's formula
    summed over all turn combinations (filamentary method).
    
    :param r_pri_turns: 1D array of radii of each primary turn (m)
    :param z_pri_turns: 1D array of axial positions of each primary turn (m)
    :param r_sec_turns: 1D array of radii of each secondary turn (m)
    :param z_sec_turns: 1D array of axial positions of each secondary turn (m)
    :return: Mutual inductance in Henrys
    """
    if len(r_pri_turns) == 0 or len(r_sec_turns) == 0:
        return 0.0
        
    # Broadcast to compute all pairs
    R = r_pri_turns[:, np.newaxis] # (N_pri, 1)
    r = r_sec_turns[np.newaxis, :] # (1, N_sec)
    dz = z_pri_turns[:, np.newaxis] - z_sec_turns[np.newaxis, :] # (N_pri, N_sec)
    
    # k^2 parameter for elliptic integrals
    k2 = (4.0 * R * r) / ((R + r)**2 + dz**2)
    # Clip to avoid division by zero or domain errors at identical positions
    k2 = np.clip(k2, 1e-9, 1.0 - 1e-9)
    k = np.sqrt(k2)
    
    K = ellipk(k2)
    E = ellipe(k2)
    
    # Neumann mutual inductance between single turns
    M_pairs = MU_0 * np.sqrt(R * r) * ((2.0/k - k) * K - (2.0/k) * E)
    return float(np.sum(M_pairs))

def calc_coupling_coefficient(M: float, L1: float, L2: float) -> float:
    """ Calculate k = M / sqrt(L1 * L2) """
    if L1 <= 0 or L2 <= 0:
        return 0.0
    return M / math.sqrt(L1 * L2)

def est_freau_spark_length(power_watts: float) -> float:
    """
    Freau's empirical formula for spark length.
    Returns length in meters.
    """
    if power_watts <= 0:
        return 0.0
    length_inches = 1.7 * math.sqrt(power_watts)
    return length_inches * 0.0254

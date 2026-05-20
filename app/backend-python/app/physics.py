import math

def calculate_helical_inductance_uh(radius_mm, height_mm, turns):
    """
    Calculates inductance of a helical coil using Wheeler's formula.
    L (uH) = (r^2 * N^2) / (9*r + 10*h) where r and h are in inches.
    """
    r_in = radius_mm / 25.4
    h_in = height_mm / 25.4
    if r_in <= 0 or h_in <= 0:
        return 0.0
    return (r_in**2 * turns**2) / (9 * r_in + 10 * h_in)

def calculate_flat_spiral_inductance_uh(inner_radius_mm, outer_radius_mm, turns):
    """
    Wheeler's formula for flat spiral coil.
    L (uH) = (r^2 * N^2) / (8*r + 11*w) where r is average radius, w is width in inches.
    """
    r_in = ((inner_radius_mm + outer_radius_mm) / 2) / 25.4
    w_in = (outer_radius_mm - inner_radius_mm) / 25.4
    if r_in <= 0 or w_in <= 0:
        return 0.0
    return (r_in**2 * turns**2) / (8 * r_in + 11 * w_in)

def calculate_toroid_capacitance_pf(major_diameter_mm, minor_diameter_mm):
    """
    Approximation for isotropic capacity of a torus.
    C (pF) = 1.4 * (1.2781 - minor/major) * sqrt(pi * minor * (major - minor))
    Where dimensions are in inches.
    """
    d1 = (major_diameter_mm - minor_diameter_mm) / 25.4  # Center to center diameter
    d2 = minor_diameter_mm / 25.4 # Tube diameter
    if d1 <= 0 or d2 <= 0:
        return 0.0
    return 1.4 * (1.2781 - (d2/d1)) * math.sqrt(math.pi * d2 * d1)

def calculate_resonant_frequency_khz(inductance_uh, capacitance_nf):
    if inductance_uh <= 0 or capacitance_nf <= 0:
        return 0.0
    l_henry = inductance_uh * 1e-6
    c_farad = capacitance_nf * 1e-9
    freq_hz = 1 / (2 * math.pi * math.sqrt(l_henry * c_farad))
    return freq_hz / 1000.0

def estimate_spark_length_cm(input_power_watts):
    """
    Freau's empirical formula: Length (inches) = 1.7 * sqrt(Power)
    Convert to cm.
    """
    if input_power_watts <= 0:
        return 0.0
    length_inches = 1.7 * math.sqrt(input_power_watts)
    return length_inches * 2.54

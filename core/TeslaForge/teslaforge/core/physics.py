"""
Rigorous mathematical calculations for Tesla Coil engineering.
Implements formulas from Wheeler, Medhurst, and Neumann's Mutual Inductance via Elliptic Integrals.
"""

import math
import numpy as np
from scipy.special import ellipk, ellipe

MU_0 = 4.0 * math.pi * 1e-7  # Permeability of free space (H/m)
EPSILON_0 = 8.8541878128e-12  # Permittivity of free space (F/m)
C_LIGHT = 299792458  # Speed of light (m/s)


def calc_helical_inductance_wheeler(
    radius_m: float, height_m: float, turns: float
) -> float:
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


def calc_flat_spiral_inductance_wheeler(
    inner_radius_m: float, outer_radius_m: float, turns: float
) -> float:
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


try:
    import numba

    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False

if HAS_NUMBA:

    @numba.jit(nopython=True, cache=True)
    def _agm_elliptic_k_e(m: float):
        """
        Complete elliptic integrals of the first (K) and second (E) kind using AGM.
        Converges quadratically to double-precision accuracy.
        """
        if m == 0.0:
            return math.pi / 2.0, math.pi / 2.0
        if m >= 1.0:
            m = 1.0 - 1e-15

        a = 1.0
        b = math.sqrt(1.0 - m)
        c = math.sqrt(m)

        sum_c = 0.5 * (c**2)
        factor = 1.0

        for i in range(1, 10):
            a_next = 0.5 * (a + b)
            b_next = math.sqrt(a * b)
            c_next = 0.5 * (a - b)

            sum_c += factor * (c_next**2)
            factor *= 2.0

            a = a_next
            b = b_next
            c = c_next

            if abs(c) < 1e-15:
                break

        K = math.pi / (2.0 * a)
        E = K * (1.0 - sum_c)
        return K, E

    @numba.jit(nopython=True, cache=True, parallel=True)
    def _jit_neumann_sum(
        r_pri: np.ndarray,
        z_pri: np.ndarray,
        r_sec: np.ndarray,
        z_sec: np.ndarray,
        mu_0: float,
    ) -> float:
        """
        Accelerated O(1) memory parallel filamentary mutual inductance sum.
        """
        n_pri = len(r_pri)
        n_sec = len(r_sec)
        m_sum = 0.0

        for i in numba.prange(n_pri):
            R = r_pri[i]
            zp = z_pri[i]

            local_sum = 0.0
            for j in range(n_sec):
                r = r_sec[j]
                zs = z_sec[j]

                dz = zp - zs
                k2 = (4.0 * R * r) / ((R + r) ** 2 + dz**2)

                if k2 < 1e-9:
                    k2 = 1e-9
                elif k2 > 1.0 - 1e-9:
                    k2 = 1.0 - 1e-9

                k = math.sqrt(k2)
                K, E = _agm_elliptic_k_e(k2)

                m_pair = mu_0 * math.sqrt(R * r) * ((2.0 / k - k) * K - (2.0 / k) * E)
                local_sum += m_pair

            m_sum += local_sum

        return m_sum


def calc_mutual_inductance_neumann(
    r_pri_turns: np.ndarray,
    z_pri_turns: np.ndarray,
    r_sec_turns: np.ndarray,
    z_sec_turns: np.ndarray,
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

    if HAS_NUMBA:
        return _jit_neumann_sum(
            r_pri_turns, z_pri_turns, r_sec_turns, z_sec_turns, MU_0
        )

    # Broadcast to compute all pairs
    R = r_pri_turns[:, np.newaxis]  # (N_pri, 1)
    r = r_sec_turns[np.newaxis, :]  # (1, N_sec)
    dz = z_pri_turns[:, np.newaxis] - z_sec_turns[np.newaxis, :]  # (N_pri, N_sec)

    # k^2 parameter for elliptic integrals
    k2 = (4.0 * R * r) / ((R + r) ** 2 + dz**2)
    # Clip to avoid division by zero or domain errors at identical positions
    k2 = np.clip(k2, 1e-9, 1.0 - 1e-9)
    k = np.sqrt(k2)

    K = ellipk(k2)
    E = ellipe(k2)

    # Neumann mutual inductance between single turns
    M_pairs = MU_0 * np.sqrt(R * r) * ((2.0 / k - k) * K - (2.0 / k) * E)
    return float(np.sum(M_pairs))


def calc_coupling_coefficient(M: float, L1: float, L2: float) -> float:
    """Calculate k = M / sqrt(L1 * L2)"""
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


def calc_skin_depth(
    freq_hz: float,
    resistivity_ohm_m: float = 1.68e-8,
    relative_permeability: float = 1.0,
) -> float:
    """
    Calculate electromagnetic skin depth for a conductor.
    Default resistivity is for copper at 20C (1.68e-8 Ohm-m).
    Relative permeability defaults to 1.0 (non-magnetic copper).
    Returns skin depth in meters.
    """
    if freq_hz <= 0:
        return float("inf")
    mu = relative_permeability * MU_0
    return math.sqrt(resistivity_ohm_m / (math.pi * freq_hz * mu))


def calc_dowell_proximity_factor(
    wire_diameter_m: float,
    skin_depth_m: float,
    pitch_m: float,
    layers: int = 1,
) -> float:
    """
    Calculates Dowell's proximity-effect correction factor (R_ac / R_dc)
    for high-frequency winding losses.

    :param wire_diameter_m: Diameter of the bare copper wire (m)
    :param skin_depth_m: Skin depth of conductor at operational frequency (m)
    :param pitch_m: Winding pitch (m), center-to-center distance between adjacent turns
    :param layers: Number of layers in the winding (defaults to 1)
    :return: Dowell AC resistance multiplier (F_R = R_ac / R_dc)
    """
    if skin_depth_m <= 0 or skin_depth_m == float("inf"):
        return 1.0

    # Porosity / packing factor eta = wire_diameter / pitch, capped to avoid numerical instability
    eta = min(wire_diameter_m / pitch_m, 0.98) if pitch_m > 0 else 0.98

    # Normalized conductor thickness xi for round wire
    xi = (math.pi / 4.0) ** 0.75 * (wire_diameter_m / skin_depth_m) * math.sqrt(eta)

    # Avoid hyperbolic overflow for large xi
    if xi > 15.0:
        # Asymptotically, F_R approaches xi for large xi
        return xi

    sinh_2xi = math.sinh(2.0 * xi)
    sin_2xi = math.sin(2.0 * xi)
    cosh_2xi = math.cosh(2.0 * xi)
    cos_2xi = math.cos(2.0 * xi)

    term1 = (sinh_2xi + sin_2xi) / (cosh_2xi - cos_2xi)

    if layers > 1:
        sinh_xi = math.sinh(xi)
        sin_xi = math.sin(xi)
        cosh_xi = math.cosh(xi)
        cos_xi = math.cos(xi)
        term2 = (2.0 / 3.0) * (layers**2 - 1) * (sinh_xi - sin_xi) / (cosh_xi + cos_xi)
        return xi * (term1 + term2)

    return xi * term1


def calc_ac_resistance(
    dc_resistance_ohms: float,
    wire_radius_m: float,
    freq_hz: float,
    resistivity_ohm_m: float = 1.68e-8,
    pitch_m: float = None,
    layers: int = 1,
) -> float:
    """
    Estimate AC resistance of a coil winding using Dowell's Proximity Effect model.
    Falls back to skin depth AC resistance if winding pitch is not specified.
    """
    if freq_hz <= 0:
        return dc_resistance_ohms

    delta = calc_skin_depth(freq_hz, resistivity_ohm_m)
    if delta == float("inf") or delta >= wire_radius_m:
        return dc_resistance_ohms

    if pitch_m is not None and pitch_m > 0:
        wire_dia = 2.0 * wire_radius_m
        f_r = calc_dowell_proximity_factor(wire_dia, delta, pitch_m, layers)
        return dc_resistance_ohms * max(1.0, f_r)

    # Fallback skin depth approximation
    ratio = wire_radius_m / (2.0 * delta)
    return dc_resistance_ohms * max(1.0, ratio)

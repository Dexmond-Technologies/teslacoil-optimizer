"""
Multi-objective optimization engine powered by Optuna and SciPy.
Combines global Bayesian/Genetic optimization (NSGA-II) with fine-grained local gradient tuning.
"""
import optuna
from optuna.trial import Trial
import numpy as np
import math
from scipy.optimize import minimize
from ..core.geometry import PrimaryCoil, SecondaryCoil, Wire, Topload
from ..core.physics import (
    calc_helical_inductance_wheeler,
    calc_flat_spiral_inductance_wheeler,
    calc_medhurst_capacitance,
    calc_toroid_capacitance,
    calc_resonant_frequency,
    calc_mutual_inductance_neumann,
    calc_coupling_coefficient
)

# Disable default Optuna logs for clean CLI output
optuna.logging.set_verbosity(optuna.logging.WARNING)

class TeslaForgeOptimizer:
    def __init__(self, target_power_w: float, primary_cap_f: float, target_fres_hz: float = None):
        """
        :param target_power_w: The design power input in Watts.
        :param primary_cap_f: MMC / primary capacitor size in Farads.
        :param target_fres_hz: (Optional) specific resonant frequency target.
        """
        self.target_power_w = target_power_w
        self.primary_cap_f = primary_cap_f
        self.target_fres_hz = target_fres_hz

    def _generate_turn_coords(self, primary: PrimaryCoil, secondary: SecondaryCoil, pri_z_offset_m: float = 0.0):
        """
        Generates 2D coordinates (r, z) for every turn of the primary and secondary.
        Used for Neumann mutual inductance calculations.
        """
        # Secondary turns (helical: constant radius, linearly increasing height)
        sec_turns_int = int(math.ceil(secondary.turns))
        sec_r = np.full(sec_turns_int, secondary.radius_mm / 1000.0)
        sec_z = np.linspace(0.0, secondary.height_mm / 1000.0, sec_turns_int)

        # Primary turns (flat spiral: increasing radius, constant height offset)
        pri_turns_int = int(math.ceil(primary.turns))
        pri_r = np.linspace(primary.inner_radius_mm / 1000.0, primary.outer_radius_mm / 1000.0, pri_turns_int)
        pri_z = np.full(pri_turns_int, pri_z_offset_m)

        return pri_r, pri_z, sec_r, sec_z

    def objective(self, trial: Trial):
        """
        The evaluation function for Optuna global optimization.
        Objectives:
        1. Minimize frequency mismatch between primary and secondary.
        2. Minimize secondary wire length (lowering cost and ESR).
        """
        import math
        
        # Sample Secondary coil bounds
        sec_radius_mm = trial.suggest_float("sec_radius_mm", 50.0, 200.0)
        sec_turns = trial.suggest_int("sec_turns", 800, 2500)
        sec_wire_dia = trial.suggest_categorical("sec_wire_dia", [0.2, 0.3, 0.4, 0.5]) # mm
        
        # Sample Primary coil bounds (flat spiral)
        pri_clearance_mm = trial.suggest_float("pri_clearance_mm", 20.0, 100.0)
        pri_inner_radius_mm = sec_radius_mm + pri_clearance_mm
        pri_turns = trial.suggest_float("pri_turns", 3.0, 15.0)
        pri_spacing_mm = trial.suggest_float("pri_spacing_mm", 2.0, 10.0)
        pri_wire_dia = 6.0 # 6mm tubing
        
        # Sample Topload bounds
        top_minor_mm = trial.suggest_float("top_minor_mm", 50.0, 150.0)
        top_major_mm = trial.suggest_float("top_major_mm", top_minor_mm * 2 + 50.0, 1000.0)
        
        # Build models
        sec_wire = Wire(diameter_mm=sec_wire_dia, insulation_thickness_mm=0.02)
        secondary = SecondaryCoil(radius_mm=sec_radius_mm, turns=sec_turns, wire=sec_wire, turn_spacing_mm=0.0)
        
        pri_wire = Wire(diameter_mm=pri_wire_dia, insulation_thickness_mm=0.0)
        primary = PrimaryCoil(
            inner_radius_mm=pri_inner_radius_mm, 
            turns=pri_turns, 
            wire=pri_wire, 
            turn_spacing_mm=pri_spacing_mm
        )
        
        topload = Topload(major_diameter_mm=top_major_mm, minor_diameter_mm=top_minor_mm)
        
        # Physics calculations
        L_sec = calc_helical_inductance_wheeler(secondary.radius_mm/1000.0, secondary.height_mm/1000.0, secondary.turns)
        C_sec_self = calc_medhurst_capacitance(secondary.radius_mm/1000.0, secondary.height_mm/1000.0)
        C_top = calc_toroid_capacitance(topload.major_diameter_mm/1000.0, topload.minor_diameter_mm/1000.0)
        C_sec_total = C_sec_self + C_top
        
        F_sec = calc_resonant_frequency(L_sec, C_sec_total)
        
        L_pri = calc_flat_spiral_inductance_wheeler(primary.inner_radius_mm/1000.0, primary.outer_radius_mm/1000.0, primary.turns)
        F_pri = calc_resonant_frequency(L_pri, self.primary_cap_f)
        
        # 1. Tuning penalty
        tuning_error = abs(F_pri - F_sec)
        
        # 2. Minimize secondary wire length (cost/resistance)
        wire_length = secondary.wire_length_m
        
        # 3. Penalty if resonant freq is too far from target (if set)
        freq_penalty = 0
        if self.target_fres_hz:
            freq_penalty = abs(F_sec - self.target_fres_hz)
            
        objective_1 = tuning_error + freq_penalty
        objective_2 = wire_length
        
        return objective_1, objective_2

    def local_tune_primary_turns(self, best_params: dict) -> float:
        """
        Uses SciPy local minimization (Nelder-Mead) to hyper-tune primary turns
        to hit an exact frequency match (0.0 Hz tuning error).
        """
        import math
        
        sec_wire = Wire(diameter_mm=best_params["sec_wire_dia"], insulation_thickness_mm=0.02)
        secondary = SecondaryCoil(
            radius_mm=best_params["sec_radius_mm"], 
            turns=best_params["sec_turns"], 
            wire=sec_wire, 
            turn_spacing_mm=0.0
        )
        
        topload = Topload(
            major_diameter_mm=best_params["top_major_mm"], 
            minor_diameter_mm=best_params["top_minor_mm"]
        )
        
        # Get target secondary frequency
        L_sec = calc_helical_inductance_wheeler(secondary.radius_mm/1000.0, secondary.height_mm/1000.0, secondary.turns)
        C_sec_self = calc_medhurst_capacitance(secondary.radius_mm/1000.0, secondary.height_mm/1000.0)
        C_top = calc_toroid_capacitance(topload.major_diameter_mm/1000.0, topload.minor_diameter_mm/1000.0)
        C_sec_total = C_sec_self + C_top
        F_sec = calc_resonant_frequency(L_sec, C_sec_total)

        # Local optimization function for primary turns
        def tune_fn(turns):
            turns = max(turns[0], 1.0) # bound check
            pri_wire = Wire(diameter_mm=6.0, insulation_thickness_mm=0.0)
            primary = PrimaryCoil(
                inner_radius_mm=best_params["sec_radius_mm"] + best_params["pri_clearance_mm"],
                turns=turns,
                wire=pri_wire,
                turn_spacing_mm=best_params["pri_spacing_mm"]
            )
            L_pri = calc_flat_spiral_inductance_wheeler(
                primary.inner_radius_mm/1000.0, 
                primary.outer_radius_mm/1000.0, 
                primary.turns
            )
            F_pri = calc_resonant_frequency(L_pri, self.primary_cap_f)
            return (F_pri - F_sec)**2

        initial_guess = [best_params["pri_turns"]]
        res = minimize(tune_fn, initial_guess, method="Nelder-Mead")
        return float(max(res.x[0], 1.0))

    def optimize(self, n_trials=500):
        # 1. Global Multi-Objective Optimization
        study = optuna.create_study(directions=["minimize", "minimize"])
        study.optimize(self.objective, n_trials=n_trials)
        return study

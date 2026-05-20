import random
import numpy as np
from scipy.optimize import differential_evolution
from app.physics import calculate_helical_inductance_uh, calculate_resonant_frequency_khz
from app.models import OptimizationInput

def evaluate_fitness(x, base_params):
    # x = [sec_turns, sec_height, top_major, top_minor]
    sec_turns, sec_height, top_major, top_minor = x
    
    # Example complex fitness function simulating city-scale delivery
    l_s = calculate_helical_inductance_uh(
        base_params.secondary_coil.diameter_mm / 2,
        sec_height,
        sec_turns
    )
    
    # Penalize if resonance mismatch
    target_freq = 150.0 # Khz arbitrary target for MW
    f_s = calculate_resonant_frequency_khz(l_s, 5.0) # 5nf dummy cap
    
    mismatch_penalty = abs(f_s - target_freq) * 10
    
    # Reward massive scale (Frontier mode)
    scale_reward = (sec_height / 1000.0) * 50 + (top_major / 1000.0) * 20
    
    # Return negative because differential_evolution MINIMIZES
    return mismatch_penalty - scale_reward

def krittr_evolutionary_optimization(base_params: OptimizationInput):
    bounds = [
        (100, 10000), # sec_turns
        (500, 50000), # sec_height (up to 50m)
        (300, 20000), # top major (up to 20m)
        (100, 5000)   # top minor
    ]
    
    result = differential_evolution(
        evaluate_fitness, 
        bounds, 
        args=(base_params,), 
        maxiter=100, 
        popsize=20,
        mutation=(0.5, 1.5),
        recombination=0.7
    )
    
    optimized = base_params.copy()
    optimized.secondary_coil.turns = result.x[0]
    optimized.secondary_coil.height_mm = result.x[1]
    optimized.top_load.major_diameter_mm = result.x[2]
    optimized.top_load.minor_diameter_mm = result.x[3]
    
    return optimized, -result.fun

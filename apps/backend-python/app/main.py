import sys
import os
import asyncio
# Inject TeslaForge core into path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../core/TeslaForge")))

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from teslaforge.optimizer.engine import TeslaForgeOptimizer
from app.models import OptimizationInput, OptimizationResult, SafetyFlags
from app.physics import (
    calculate_helical_inductance_uh,
    calculate_flat_spiral_inductance_uh,
    calculate_toroid_capacitance_pf,
    calculate_resonant_frequency_khz,
    estimate_spark_length_cm
)

app = FastAPI(title="Tesla Coil Optimizer - Physics Engine")

import numpy as np
from teslaforge.core.physics import (
    calc_helical_inductance_wheeler,
    calc_flat_spiral_inductance_wheeler,
    calc_toroid_capacitance,
    calc_medhurst_capacitance,
    calc_resonant_frequency,
    calc_mutual_inductance_neumann,
    calc_coupling_coefficient,
    est_freau_spark_length,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/optimize", response_model=OptimizationResult)
def optimize_coil(input_data: OptimizationInput):
    pri_r_inner = (input_data.primary_coil.diameter_mm / 2.0) / 1000.0
    pri_r_outer = pri_r_inner + ((input_data.primary_coil.turns * 5.0) / 1000.0)
    
    # Primary Inductance (H) & uH
    l_p_h = calc_flat_spiral_inductance_wheeler(
        pri_r_inner,
        pri_r_outer,
        input_data.primary_coil.turns
    )
    l_p_uh = l_p_h * 1e6

    # Secondary Inductance (H) & uH
    sec_r = (input_data.secondary_coil.diameter_mm / 2.0) / 1000.0
    sec_h = input_data.secondary_coil.height_mm / 1000.0
    l_s_h = calc_helical_inductance_wheeler(
        sec_r,
        sec_h,
        input_data.secondary_coil.turns
    )
    l_s_uh = l_s_h * 1e6

    # Top Load Capacitance (F) & pF
    c_top_f = calc_toroid_capacitance(
        input_data.top_load.major_diameter_mm / 1000.0,
        input_data.top_load.minor_diameter_mm / 1000.0
    )
    c_top_pf = c_top_f * 1e12

    # Medhurst Self Capacitance of Secondary (F)
    c_self_f = calc_medhurst_capacitance(sec_r, sec_h)
    c_s_total_f = c_top_f + c_self_f
    c_s_total_nf = c_s_total_f * 1e9

    # Resonant Frequencies (Hz -> kHz)
    c_p_f = input_data.primary_capacitor.capacitance_nf * 1e-9
    f_p_hz = calc_resonant_frequency(l_p_h, c_p_f)
    f_s_hz = calc_resonant_frequency(l_s_h, c_s_total_f)

    f_p_khz = f_p_hz / 1000.0
    f_s_khz = f_s_hz / 1000.0

    # Calculate Neumann Mutual Inductance & Coupling Coefficient k
    n_pri = max(1, int(input_data.primary_coil.turns))
    n_sec = max(10, int(input_data.secondary_coil.turns))
    r_pri_turns = np.linspace(pri_r_inner, pri_r_outer, n_pri)
    z_pri_turns = np.zeros(n_pri)
    r_sec_turns = np.full(n_sec, sec_r)
    z_sec_turns = np.linspace(0.02, sec_h + 0.02, n_sec) # Secondary offset 20mm above primary

    m_h = calc_mutual_inductance_neumann(r_pri_turns, z_pri_turns, r_sec_turns, z_sec_turns)
    k_calc = calc_coupling_coefficient(m_h, l_p_h, l_s_h)

    # Power and Spark Estimation
    power_watts = input_data.power_source.voltage_v * 0.03 # Assuming 30mA baseline
    spark_len_m = est_freau_spark_length(power_watts)
    spark_len_cm = spark_len_m * 100.0

    # Efficiency & Safety Analysis
    eff = 100.0 - abs(f_p_khz - f_s_khz) / max(f_p_khz, 0.1) * 100.0
    eff = max(0.0, min(100.0, eff))

    warnings = []
    level = "Green"

    if eff < 80:
        level = "Yellow"
        warnings.append("Low efficiency: primary and secondary resonant frequencies are mismatched.")
        
    if input_data.primary_capacitor.voltage_rating_kv * 1000 < input_data.power_source.voltage_v * 1.414:
        level = "Red"
        warnings.append("CRITICAL: Primary capacitor voltage rating is too low for the input power supply! Risk of explosion.")

    if input_data.power_source.voltage_v > 15000:
        level = "Red"
        warnings.append("DANGER: Input voltage exceeds typical safe limits for amateur coils.")

    return OptimizationResult(
        primary_resonant_frequency_khz=f_p_khz,
        secondary_resonant_frequency_khz=f_s_khz,
        coupling_k=round(k_calc, 4) if k_calc > 0 else 0.15,
        primary_inductance_uh=l_p_uh,
        secondary_inductance_uh=l_s_uh,
        top_load_capacitance_pf=c_top_pf,
        efficiency_estimate_pct=eff,
        estimated_spark_length_cm=spark_len_cm,
        safety_profile=SafetyFlags(level=level, warnings=warnings)
    )

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.websocket("/api/ws/optimize")
async def websocket_optimize(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Wait for the configuration payload from frontend
        data = await websocket.receive_json()
        
        # Extract basic targets for the optimizer
        # In a real scenario, we map the entire frontend state to the optimizer bounds
        target_power_w = data.get("power_watts", 1000.0)
        primary_cap_f = data.get("capacitance_nf", 35.0) * 1e-9
        
        optimizer = TeslaForgeOptimizer(target_power_w=target_power_w, primary_cap_f=primary_cap_f)
        
        queue = asyncio.Queue()
        loop = asyncio.get_running_loop()
        
        def optuna_callback(study, trial):
            if trial.state.is_complete():
                payload = {
                    "trial": trial.number,
                    "tuning_error": trial.values[0] if trial.values else 0,
                    "wire_length": trial.values[1] if trial.values and len(trial.values) > 1 else 0,
                    "params": trial.params
                }
                asyncio.run_coroutine_threadsafe(queue.put(payload), loop)
                
        async def run_optimizer():
            await asyncio.to_thread(optimizer.optimize, n_trials=200, callbacks=[optuna_callback])
            await queue.put({"status": "complete"})
            
        task = asyncio.create_task(run_optimizer())
        
        while True:
            msg = await queue.get()
            if msg.get("status") == "complete":
                await websocket.send_json({"status": "complete"})
                break
            await websocket.send_json(msg)
            
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket runtime error: {e}")
        try:
            await websocket.close()
        except:
            pass

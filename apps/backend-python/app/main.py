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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/optimize", response_model=OptimizationResult)
def optimize_coil(input_data: OptimizationInput):
    # Primary Inductance
    l_p = calculate_flat_spiral_inductance_uh(
        input_data.primary_coil.diameter_mm / 2, 
        (input_data.primary_coil.diameter_mm / 2) + (input_data.primary_coil.turns * 5), # Approx 5mm spacing
        input_data.primary_coil.turns
    )
    
    # Secondary Inductance
    l_s = calculate_helical_inductance_uh(
        input_data.secondary_coil.diameter_mm / 2,
        input_data.secondary_coil.height_mm,
        input_data.secondary_coil.turns
    )
    
    # Top Load Capacitance
    c_top = calculate_toroid_capacitance_pf(
        input_data.top_load.major_diameter_mm,
        input_data.top_load.minor_diameter_mm
    )
    
    # Self-capacitance of secondary (Medhurst formula approx: 0.5 * height in inches)
    c_self = 0.5 * (input_data.secondary_coil.height_mm / 25.4)
    c_s_total_pf = c_top + c_self
    c_s_total_nf = c_s_total_pf / 1000.0
    
    # Resonant Frequencies
    f_p = calculate_resonant_frequency_khz(l_p, input_data.primary_capacitor.capacitance_nf)
    f_s = calculate_resonant_frequency_khz(l_s, c_s_total_nf)
    
    # Power and Spark
    # Assumes arbitrary current limit if not provided. E.g. Power = V * I. Assuming 30mA for NST
    power_watts = input_data.power_source.voltage_v * 0.03 
    spark_len = estimate_spark_length_cm(power_watts)
    
    # Efficiency & Safety
    eff = 100 - abs(f_p - f_s) / max(f_p, 0.1) * 100
    eff = max(0, min(100, eff))
    
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
        primary_resonant_frequency_khz=f_p,
        secondary_resonant_frequency_khz=f_s,
        coupling_k=0.15, # Approximation placeholder
        primary_inductance_uh=l_p,
        secondary_inductance_uh=l_s,
        top_load_capacitance_pf=c_top,
        efficiency_estimate_pct=eff,
        estimated_spark_length_cm=spark_len,
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

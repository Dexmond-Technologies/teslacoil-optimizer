from teslaforge.optimizer.engine import TeslaForgeOptimizer


def test_optimizer_workflow():
    # Initialize optimizer with 1000W target power and 20nF primary capacitance
    opt = TeslaForgeOptimizer(target_power_w=1000.0, primary_cap_f=20e-9)

    # Run a small genetic study (10 trials to be extremely fast in tests)
    study = opt.optimize(n_trials=10)

    # Verify trials were run and best trials are recorded
    assert len(study.trials) == 10

    # Extract one of the best trials parameter sets
    # For multi-objective, we look at the Pareto front
    best_trials = study.best_trials
    assert len(best_trials) > 0

    best_params = best_trials[0].params

    # Verify parameter ranges
    assert 50.0 <= best_params["sec_radius_mm"] <= 200.0
    assert 800 <= best_params["sec_turns"] <= 2500
    assert 3.0 <= best_params["pri_turns"] <= 15.0

    # 2. Local Tuning test using SLSQP
    # Let's perform local tuning to find the exact primary turns required for resonance
    tuned_turns = opt.local_tune_primary_turns(best_params)

    # Verify tuned turns are physically valid
    assert 1.0 <= tuned_turns <= 30.0

    # Verify that the tuned turns indeed achieve extremely close resonance mismatch
    from teslaforge.core.geometry import Wire, SecondaryCoil, PrimaryCoil, Topload
    from teslaforge.core.physics import (
        calc_helical_inductance_wheeler,
        calc_medhurst_capacitance,
        calc_toroid_capacitance,
        calc_resonant_frequency,
        calc_flat_spiral_inductance_wheeler,
    )

    sec_wire = Wire(
        diameter_mm=best_params["sec_wire_dia"], insulation_thickness_mm=0.02
    )
    secondary = SecondaryCoil(
        radius_mm=best_params["sec_radius_mm"],
        turns=best_params["sec_turns"],
        wire=sec_wire,
        turn_spacing_mm=0.0,
    )
    topload = Topload(
        major_diameter_mm=best_params["top_major_mm"],
        minor_diameter_mm=best_params["top_minor_mm"],
    )

    # Secondary resonance
    L_sec = calc_helical_inductance_wheeler(
        secondary.radius_mm / 1000.0, secondary.height_mm / 1000.0, secondary.turns
    )
    C_sec_self = calc_medhurst_capacitance(
        secondary.radius_mm / 1000.0, secondary.height_mm / 1000.0
    )
    C_top = calc_toroid_capacitance(
        topload.major_diameter_mm / 1000.0, topload.minor_diameter_mm / 1000.0
    )
    F_sec = calc_resonant_frequency(L_sec, C_sec_self + C_top)

    # Primary resonance with tuned turns
    pri_wire = Wire(diameter_mm=6.0, insulation_thickness_mm=0.0)
    primary = PrimaryCoil(
        inner_radius_mm=best_params["sec_radius_mm"] + best_params["pri_clearance_mm"],
        turns=tuned_turns,
        wire=pri_wire,
        turn_spacing_mm=best_params["pri_spacing_mm"],
    )
    L_pri = calc_flat_spiral_inductance_wheeler(
        primary.inner_radius_mm / 1000.0,
        primary.outer_radius_mm / 1000.0,
        primary.turns,
    )
    F_pri = calc_resonant_frequency(L_pri, opt.primary_cap_f)

    # The SLSQP tuned turns should achieve perfect alignment (mismatch < 1 Hz)
    assert abs(F_pri - F_sec) < 1.0

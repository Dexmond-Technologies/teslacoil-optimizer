# Milestone 1: Core Optimizer Engine

TeslaForge's Core Optimizer Engine uses advanced genetic algorithms (NSGA-II) combined with rigorous electromagnetic formulas to design perfectly tuned Tesla Coils from scratch.

## Features
- **Parametric Geometry Model:** Strictly typed dimensional validation using Pydantic.
- **Advanced Physics Engine:** Evaluates Wheeler's inductance, Medhurst self-capacitance, and toroid capacitance formulas with high precision.
- **Multi-Objective Optimization:** Powered by Optuna, the engine simultaneously solves for resonance (tuning) while minimizing material cost (wire length) and keeping dimensions physically realizable.

## Architecture
- `teslaforge.core.geometry`: Classes defining `PrimaryCoil`, `SecondaryCoil`, `Topload`.
- `teslaforge.core.physics`: High-speed analytical functions.
- `teslaforge.optimizer.engine`: Optuna wrapper that defines the multi-objective fitness function.

## Quickstart
1. Install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```
2. Run the optimization example:
   ```bash
   python -m examples.basic_optimization
   ```
3. Run test suite:
   ```bash
   pytest tests/
   ```

# 🤝 Contributing to Tesla Coil Optimizer (TCO)

Thank you for choosing to help make the **Tesla Coil Optimizer (TCO)** the most powerful open-source electromagnetic resonant engineering system on Earth! We are excited to collaborate with you.

Before contributing, please read this guide to ensure a smooth, professional, and efficient development experience.

---

## 🏗️ Repository Architecture Overview

TCO is structured as a clean monorepo:

*   `core/TeslaForge/`: The standalone python physics engine, containing physical closed-form formulas and multi-objective solvers.
*   `apps/frontend/`: The cyber-industrial tactical telemetry HUD, built in React, Vite, and TypeScript.
*   `apps/backend-python/`: FastAPI REST service that interfaces with the physics engine.
*   `apps/integration-java/`: (Optional) The Spring Boot enterprise integration proxy gateway.
*   `reference_repos/`: A `.gitignore`d directory containing local copies of community reference calculators, interrupters, and MIDI players.

---

## ⚙️ Development Environment Setup

### 1. Python Environment (TeslaForge Physics)
To get started with the computational engine:
```bash
cd core/TeslaForge
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install package in editable development mode along with testing tools
pip install -e .[dev,accel]
```

### 2. Frontend Environment (React Telemetry HUD)
To get started with the HUD interface:
```bash
cd apps/frontend
npm install
npm run dev
```
Navigate to `http://localhost:5173` to see it live. It connects directly to the FastAPI server running on `http://localhost:8000`.

### 3. Containerized Orchestration (Docker Compose)
To start the entire microservices stack locally with one command:
```bash
cd apps
# Start standard open-source stack
docker compose up --build
```
For enterprise runs that include the Spring Boot gateway service:
```bash
cd apps
docker compose --profile enterprise up --build
```

---

## 🧪 Testing & Linting Standards

We maintain a strict quality barrier to keep TCO accurate and reliable. Always test your changes before submitting!

### 1. Run Physics Unit Tests
We use `pytest` for all mathematical and physical calculations:
```bash
cd core/TeslaForge
source .venv/bin/activate
pytest tests/
```

### 2. Check Formatting and Style
We use **Ruff** for unified formatting and linting.
```bash
# Run Ruff lint check
ruff check teslaforge/ tests/

# Run Ruff format check
ruff format --check teslaforge/ tests/

# Automatically fix lint issues and format code
ruff check --fix teslaforge/ tests/
ruff format teslaforge/ tests/
```

---

## 📬 Pull Request Process

1.  **Fork the Repository**: Clone your fork locally.
2.  **Create a Feature Branch**: Use descriptive branch names: `git checkout -b feature/skin-effect-losses` or `git checkout -b fix/resonant-freq-wheeler`.
3.  **Implement & Test**: Ensure all tests pass. If you add new formulas, **always write accompanying unit tests** in `tests/`.
4.  **Format**: Format your code with `black`.
5.  **Submit a PR**: Write a detailed summary of what was added, referencing any issues.

---

## 🛡️ Community Conduct

*   **Safety First**: Tesla coils contain lethal voltages. While this is simulation software, do not encourage high-risk hardware behaviors in PR comments or descriptions. Always advocate standard isolation safety procedures.
*   **Scientific Rigor**: Ground all physics updates in verified formulas (e.g., Medhurst, Wheeler, Neumann equations) and include literature citations in your docstrings.

*Developed with ⚡ by Dexmond Technologies and the High-Voltage Engineering Community.*

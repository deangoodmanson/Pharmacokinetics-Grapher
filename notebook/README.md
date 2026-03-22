# Pharmacokinetics Notebook

Visualize medication concentration curves over time using one-compartment pharmacokinetic modeling. Available as a Jupyter notebook, a marimo notebook, or as a standalone Python library (`pk_core`).

> **Educational use only.** This tool shows approximate relative concentration curves based on simplified PK models. Not for medical dosing decisions. Always follow prescriptions from licensed healthcare providers.

## Quick Start

### Option A: marimo notebook (recommended)

The marimo notebook (`pharmacokinetics.py`) uses [PEP 723](https://peps.python.org/pep-0723/) inline script metadata, so compatible tools can install dependencies automatically.

**With `uv` (no pre-install needed):**

```bash
cd notebook
uvx marimo edit pharmacokinetics.py
```

`uv` reads the PEP 723 `# /// script` block at the top of the file and installs `marimo`, `numpy`, and `matplotlib` automatically into an isolated environment.

**With marimo installed:**

```bash
cd notebook
marimo edit pharmacokinetics.py
```

**With `pipx`:**

```bash
cd notebook
pipx run marimo edit pharmacokinetics.py
```

### Option B: Jupyter notebook

```bash
cd notebook
pip install numpy matplotlib jupyter
jupyter notebook pharmacokinetics.ipynb
```

Or with a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install numpy matplotlib jupyter
jupyter notebook pharmacokinetics.ipynb
```

### Option C: Use `pk_core` as a library

The core calculation engine is a standalone Python package you can import directly:

```python
from pk_core import Prescription, accumulate_doses, compute_steady_state_metrics

rx = Prescription(name="Ibuprofen", dose=400, half_life=2.0, uptake=0.5, peak=1.5,
                  frequency="tid", times=["08:00", "14:00", "20:00"])

t, c = accumulate_doses(rx, end_hours=48)
metrics = compute_steady_state_metrics(rx)
```

## Project Structure

```
notebook/
├── pk_core/                       # Core calculation library (no UI dependencies)
│   ├── models.py                  # Prescription, DoseStep, constants
│   ├── calculator.py              # Single-dose PK equations
│   ├── accumulation.py            # Multi-dose accumulation engine
│   ├── milestones.py              # PK milestone event calculation
│   ├── analysis.py                # Steady-state metrics
│   ├── serialization.py           # JSON I/O (web app compatible)
│   └── tests/                     # 83 unit tests
├── pharmacokinetics.ipynb         # Jupyter notebook
├── pharmacokinetics.py            # marimo notebook (PEP 723)
├── PLAN.md                        # Implementation plan
└── README.md                      # This file
```

## What It Does

The notebook models how drug concentrations rise and fall in the body after dosing, using the **one-compartment first-order absorption model**:

```
C(t) = Dose * [ka/(ka-ke)] * (e^(-ke*t) - e^(-ka*t))
```

### Features

- **Single-dose curves** — visualize absorption, peak, and elimination phases
- **Multi-dose accumulation** — see how repeated dosing builds to steady-state
- **Multi-drug comparison** — overlay multiple medications on one graph
- **Metabolite tracking** — plot active metabolite curves alongside parent drug
- **PK milestone timeline** — tabular view of dose, peak, and half-life events
- **Steady-state analysis** — accumulation factor, peak/trough, swing metrics
- **Parameter sensitivity** — explore how changing half-life or uptake affects the curve
- **Frequency comparison** — same daily dose across different schedules (bid vs tid vs qid)
- **Titration/taper schedules** — variable-dose protocols with step visualization
- **JSON import/export** — share prescriptions with the web application

## API Reference

### Core Functions

| Function | Module | Description |
|----------|--------|-------------|
| `calculate_concentration(t, dose, half_life, uptake)` | `calculator` | Single-dose concentration curve (raw, unnormalized) |
| `calculate_metabolite_concentration(t, dose, parent_hl, met_hl, fm)` | `calculator` | Metabolite concentration (sequential metabolism) |
| `accumulate_doses(rx, start, end, interval)` | `accumulation` | Multi-dose accumulation, normalized to peak=1.0 |
| `accumulate_metabolite_doses(rx, start, end, interval)` | `accumulation` | Multi-dose metabolite accumulation |
| `accumulate_schedule(rx, steps, interval)` | `accumulation` | Titration/taper with variable doses |
| `generate_frequency_variants(rx, frequencies)` | `accumulation` | Same daily dose across different frequencies |
| `calculate_milestones(rx, start, end)` | `milestones` | Dose, peak, half-life decay events |
| `compute_steady_state_metrics(rx)` | `analysis` | tau, accumulation factor, SS peak/trough/swing |
| `prescription_to_dict(rx)` / `prescription_from_dict(d)` | `serialization` | JSON conversion (web app compatible) |
| `save_prescriptions(rxs, path)` / `load_prescriptions(path)` | `serialization` | File I/O |

### Data Models

| Class | Fields |
|-------|--------|
| `Prescription` | `name`, `dose`, `half_life`, `uptake`, `peak`, `frequency`, `times`, `metabolite_life`, `relative_metabolite_level`, `metabolite_name`, `duration`, `duration_unit` |
| `DoseStep` | `dose`, `duration_days` |

## Input Parameters

All values come from pharmacy inserts (package inserts provide ranges; pick a representative value):

| Parameter | Unit | Description |
|-----------|------|-------------|
| `name` | — | Drug name |
| `dose` | mg | Amount per dose |
| `frequency` | — | Dosing frequency: qd, bid, tid, qid, q6h, q8h, q12h, once, custom |
| `times` | HH:MM | Dosing times in 24-hour format (must match frequency count) |
| `half_life` | hours | Elimination half-life (0.1–240h) |
| `uptake` | hours | Absorption time (0.1–24h) |
| `peak` | hours | Time to peak concentration, Tmax (stored for reference) |
| `metabolite_life` | hours | Metabolite half-life (optional) |
| `relative_metabolite_level` | ratio | Metabolite level vs. normal metabolizer, 0.1–10.0 (optional) |

## Output

- **Y-axis**: Relative concentration normalized to peak = 1.0 (not absolute mg/L)
- **X-axis**: Time in hours from first dose
- Curves show the **shape and timing** of concentration changes, not absolute blood levels

## Frequency Reference

| Code | Meaning | Doses/Day |
|------|---------|-----------|
| `once` | Single dose | 1 |
| `qd` | Once daily | 1 |
| `bid` | Twice daily | 2 |
| `tid` | Three times daily | 3 |
| `qid` | Four times daily | 4 |
| `q6h` | Every 6 hours | 4 |
| `q8h` | Every 8 hours | 3 |
| `q12h` | Every 12 hours | 2 |
| `custom` | User-defined times | varies |

## Running Tests

```bash
cd notebook
python -m pytest pk_core/tests/ -v
```

83 tests covering all core modules: models, calculator, accumulation, milestones, analysis, and serialization.

## Interoperability

The notebook uses the same JSON prescription format as the [Pharmacokinetics Grapher](../) web application. Export from the web app and load directly into the notebook, or vice versa. Legacy formats (`metaboliteConversionFraction`, nested `metaboliteHalfLife`) are automatically migrated on import.

## Assumptions & Limitations

- One-compartment model (uniform drug distribution)
- First-order elimination (linear kinetics, no saturation)
- Complete absorption (bioavailability F = 1.0)
- No drug-drug interactions modeled
- Relative concentrations only — absolute levels require patient-specific volume of distribution (Vd)

# Pharmacokinetics Notebook

A Jupyter notebook for visualizing medication concentration curves over time using one-compartment pharmacokinetic modeling.

> **Educational use only.** This tool shows approximate relative concentration curves based on simplified PK models. Not for medical dosing decisions. Always follow prescriptions from licensed healthcare providers.

## Quick Start

### Requirements

- Python 3.9+
- Jupyter Notebook or JupyterLab

### Install & Run

```bash
cd notebook
pip install numpy matplotlib ipywidgets pandas
jupyter notebook pharmacokinetics.ipynb
```

Or with a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install numpy matplotlib ipywidgets pandas jupyter
jupyter notebook pharmacokinetics.ipynb
```

## What It Does

The notebook models how drug concentrations rise and fall in the body after dosing, using the **one-compartment first-order absorption model**:

```
C(t) = Dose × [ka/(ka-ke)] × (e^(-ke×t) - e^(-ka×t))
```

### Features

- **Single-dose curves** — visualize absorption, peak, and elimination phases
- **Multi-dose accumulation** — see how repeated dosing builds to steady-state
- **Multi-drug comparison** — overlay multiple medications on one graph
- **Metabolite tracking** — plot active metabolite curves alongside parent drug
- **PK milestone timeline** — tabular view of dose, peak, and half-life events
- **Parameter sensitivity** — explore how changing half-life or uptake affects the curve
- **JSON import/export** — share prescriptions with the web application

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

## Interoperability

The notebook uses the same JSON prescription format as the [Pharmacokinetics Grapher](../) web application. Export from the web app and load directly into the notebook, or vice versa.

## Assumptions & Limitations

- One-compartment model (uniform drug distribution)
- First-order elimination (linear kinetics, no saturation)
- Complete absorption (bioavailability F = 1.0)
- No drug-drug interactions modeled
- Relative concentrations only — absolute levels require patient-specific volume of distribution (Vd)

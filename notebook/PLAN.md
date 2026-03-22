# Pharmacokinetics Notebook — Implementation Plan

## Goal

Create a standalone Python pharmacokinetics toolkit with notebook frontends (Jupyter and marimo) that replicates the core PK calculation and visualization engine from the web application, making it accessible to researchers, students, and clinicians who prefer a Python/notebook workflow.

---

## Architecture

All core business logic lives in the `pk_core/` Python package, independently testable and importable. The notebooks are thin presentation layers that import from `pk_core` and add plotting/formatting.

```
notebook/
├── pk_core/                       # Core calculation library
│   ├── __init__.py                # Public API re-exports
│   ├── models.py                  # Prescription, DoseStep, constants
│   ├── calculator.py              # Single-dose PK equations
│   ├── accumulation.py            # Multi-dose accumulation engine
│   ├── milestones.py              # PK milestone event calculation
│   ├── analysis.py                # Steady-state metrics computation
│   ├── serialization.py           # JSON I/O, legacy format handling
│   └── tests/                     # 83 unit tests (pytest)
│       ├── test_models.py         #   9 tests — dataclasses, constants
│       ├── test_calculator.py     #  17 tests — PK equations, edge cases
│       ├── test_accumulation.py   #  27 tests — multi-dose, schedules
│       ├── test_milestones.py     #   9 tests — timeline events
│       ├── test_analysis.py       #   8 tests — steady-state metrics
│       └── test_serialization.py  #  13 tests — JSON round-trip, legacy
├── pharmacokinetics.ipynb         # Jupyter notebook (presentation)
├── pharmacokinetics.py            # marimo notebook (presentation, PEP 723)
├── PLAN.md                        # This file
└── README.md                      # End-user guide
```

### Module Dependency Chain

```
models.py (no external deps, uses math stdlib only)
    ↓
calculator.py (numpy)
    ↓
accumulation.py (numpy, calculator, models)
    ↓
milestones.py (numpy, accumulation, models)
analysis.py (numpy, accumulation, models)
serialization.py (json stdlib, models)
```

---

## Phase 1: Minimal — Single-Dose Visualization ✅

**Status**: Complete

### Deliverables

1. **`pk_core/models.py`** — `Prescription` dataclass, `DoseStep` dataclass, `FREQUENCY_MAP`, `DEFAULT_TIMES`, `KA_KE_TOLERANCE`, `LN2` constants
2. **`pk_core/calculator.py`** — `calculate_concentration()` and `calculate_metabolite_concentration()` using one-compartment first-order absorption model with ka ≈ ke fallback
3. **Single-dose plot** in both notebooks — Ibuprofen 400mg example

### Validation Criteria
- [x] Single-dose curve shape matches web app output
- [x] ka ≈ ke fallback produces smooth curve (test with uptake = half_life)
- [x] Zero/negative dose returns flat zero line
- [x] Zero/negative half_life or uptake returns zeros (no ZeroDivisionError)
- [x] Unit tests pass (17 calculator tests)

---

## Phase 2: Core Functionality — Multi-Dose Accumulation & Comparison ✅

**Status**: Complete

### Deliverables

1. **`pk_core/accumulation.py`** — `parse_time()`, `expand_dose_times()`, `dosing_end_hours()`, `accumulate_doses()`, `accumulate_metabolite_doses()`, `accumulate_schedule()`, `generate_frequency_variants()`
2. **`pk_core/milestones.py`** — `calculate_milestones()` returning event dicts
3. **`pk_core/serialization.py`** — `prescription_to_dict()`, `prescription_from_dict()` (with legacy format migration), `save_prescriptions()`, `load_prescriptions()`
4. **Multi-drug comparison plot** in notebooks — Ibuprofen vs Acetaminophen overlay
5. **Milestone timeline display** — formatted table (print in Jupyter, `mo.md` table in marimo)
6. **JSON I/O** — compatible with web app export format

### Validation Criteria
- [x] Multi-dose curve shows accumulation toward steady-state (~5 half-lives)
- [x] Normalized peak = 1.0 for each drug independently
- [x] Metabolite returns None when data incomplete, scales to `relative_metabolite_level` when complete
- [x] JSON round-trip preserves all fields
- [x] Legacy format migration works (`metaboliteConversionFraction`, nested `metaboliteHalfLife`)
- [x] Duration-limited dosing stops doses but continues observation
- [x] `generate_frequency_variants` skips 'custom', preserves daily dose total
- [x] Unit tests pass (27 accumulation + 9 milestones + 13 serialization tests)

---

## Phase 3: Analysis — Deeper PK Insights ✅

**Status**: Complete

### Deliverables

1. **`pk_core/analysis.py`** — `compute_steady_state_metrics()` returning dict with tau, accumulation factor, t_ss, ss_peak, ss_trough, swing
2. **Steady-state display** — formatted output in both notebooks (print in Jupyter, markdown table in marimo)
3. **Parameter sensitivity plot** — family of curves varying one parameter (e.g., half-life)
4. **Dosing frequency comparison** — same daily dose across bid/tid/qid/q6h using `generate_frequency_variants()`
5. **Titration/taper visualization** — `accumulate_schedule()` with `DoseStep` list, Prednisone taper example

### Validation Criteria
- [x] Accumulation factor matches analytical formula `1 / (1 - exp(-ke * tau))`
- [x] Steady-state peak >= trough, swing = peak - trough
- [x] SS peak near 1.0 for normalized curves
- [x] Unit tests pass (8 analysis tests)

---

## Future Recommendations

Items beyond the three phases, for consideration as the project matures:

1. **Two-Compartment Model** — distribution phase (alpha/beta elimination) for IV drugs and tissue redistribution
2. **Population PK (Monte Carlo)** — inter-individual variability with log-normal parameter distributions and confidence bands
3. **Bioavailability (F < 1.0)** — parameter for incomplete oral absorption; compare IV vs. oral
4. **Drug-Drug Interactions** — model enzyme inhibition/induction effects on ke (e.g., CYP3A4)
5. **Therapeutic Window Overlay** — MEC/MTC horizontal bands (requires absolute concentration via Vd)
6. **Real Patient Data Fitting** — import measured drug levels, fit parameters with scipy.optimize
7. **Interactive Dashboard (Panel/Voila)** — standalone web dashboard deployable to cloud
8. **Colab / Binder Integration** — one-click launch badges for zero-install access
9. **Input Validation** — port `validatePrescription()` from TypeScript to `pk_core/models.py`
10. **AUC Computation** — trapezoidal integration for area-under-curve comparisons

---

## Technical Notes

### Design Decisions

- **`math.log(2)` in models.py** — avoids numpy dependency in the models module; value is identical to `np.log(2)`
- **`dosing_end_hours()` is public** — shared by `accumulation.py` and `milestones.py`, renamed from `_dosing_end_hours`
- **`compute_steady_state_metrics()` returns dict** — separates computation from display; notebooks wrap with formatting
- **`generate_frequency_variants()` returns list** — separates dose adjustment logic from plotting
- **Dose filtering uses strict `<`** — matches TypeScript `t < dosingEndHours` (dose at exact end has zero observation time)

### Dependencies

| Package | Purpose | Required By |
|---------|---------|-------------|
| `numpy` | Array math, exponentials | `pk_core` (calculator, accumulation, milestones, analysis) |
| `matplotlib` | Plotting | Notebooks only |
| `marimo` | Reactive notebook runtime | `pharmacokinetics.py` only |
| `pytest` | Test runner | `pk_core/tests/` only |

### Running Tests

```bash
cd notebook
python -m pytest pk_core/tests/ -v
```

# Pharmacokinetics Notebook — Implementation Plan

## Goal

Create a standalone Jupyter notebook (`pharmacokinetics.ipynb`) that replicates the core PK calculation and visualization engine from the web application, making it accessible to researchers, students, and clinicians who prefer a Python/notebook workflow.

---

## Phase 1: Minimal — Single-Dose Visualization

**Objective**: Get a working notebook that plots a single drug's concentration curve from user-provided parameters.

### Deliverables

1. **Dependencies & Setup Cell**
   - `numpy`, `matplotlib` — standard scientific stack, no exotic dependencies
   - Brief markdown header with educational disclaimer

2. **Prescription Data Structure**
   - Python dataclass `Prescription` mirroring the TypeScript model:
     - `name`, `dose`, `half_life`, `uptake`, `peak`, `frequency`, `times`
   - Frequency constants (`FREQUENCY_MAP`, `DEFAULT_TIMES`)

3. **Core PK Equation — Single Dose**
   - `calculate_concentration(t, dose, half_life, uptake)` — one-compartment first-order absorption
   - Standard formula: `C(t) = dose * (ka/(ka-ke)) * (exp(-ke*t) - exp(-ka*t))`
   - ka ≈ ke fallback: `C(t) = dose * ka * t * exp(-ke*t)` when `|ka - ke| < 0.001`
   - Edge cases: zero/negative dose → 0, negative time → 0

4. **Single-Dose Plot**
   - Time axis (hours), relative concentration axis (0–1 normalized)
   - Clear axis labels: "Time (hours)", "Relative Concentration (peak = 1.0)"
   - Example: Ibuprofen 400mg, half-life 2h, uptake 0.5h

5. **Interactive Parameter Input** (optional enhancement)
   - `ipywidgets` sliders for dose, half-life, uptake — live-updating plot
   - Fallback: plain variables at top of cell if widgets unavailable

### Validation Criteria
- [ ] Single-dose curve shape matches web app output
- [ ] ka ≈ ke fallback produces smooth curve (test with uptake = half_life)
- [ ] Zero dose returns flat zero line

---

## Phase 2: Core Functionality — Multi-Dose Accumulation & Comparison

**Objective**: Match the web app's primary value — multi-dose accumulation curves with multi-drug overlay.

### Deliverables

1. **Dose Expansion**
   - `expand_dose_times(times, num_days)` — generate all dose administration times across simulation window
   - Respect frequency-to-times mapping (bid → 2 times, tid → 3, etc.)

2. **Multi-Dose Accumulation**
   - `accumulate_doses(prescription, start_hours, end_hours, interval_minutes=15)`
   - Sum raw contributions from all prior doses at each timepoint
   - Normalize total curve to peak = 1.0
   - Duration-limited dosing: if `duration` field set, stop administering doses after that window but continue observation

3. **Metabolite Curves** (optional)
   - `calculate_metabolite_concentration(t, dose, parent_half_life, metabolite_half_life, fm)`
   - Sequential metabolism model with ka ≈ ke fallback
   - Dashed line rendering, normalized to `relative_metabolite_level`

4. **Multi-Drug Comparison Plot**
   - Overlay multiple prescriptions on same axes with distinct colors
   - Legend with drug name + frequency
   - Example: Compare Ibuprofen (tid) vs. Acetaminophen (q6h)

5. **Prescription I/O**
   - Load prescriptions from JSON (same format as web app export)
   - Save/export prescription sets to JSON
   - Example JSON files bundled for quick-start

6. **PK Milestone Timeline**
   - `calculate_milestones(prescription, start, end)` — dose, absorption end, peak, half-life decay events
   - Tabular display (pandas DataFrame or formatted markdown)
   - Annotate key milestones on the plot (vertical lines or markers at dose times, peak markers)

### Validation Criteria
- [ ] Multi-dose curve shows accumulation toward steady-state (~5 half-lives)
- [ ] Normalized peak = 1.0 for each drug independently
- [ ] Metabolite dashed line appears when both `metabolite_life` and `relative_metabolite_level` provided
- [ ] JSON round-trip: export → import produces identical curves
- [ ] Milestone table matches web app timeline output

---

## Phase 3: Analysis — Deeper PK Insights

**Objective**: Leverage the notebook medium for analysis that goes beyond the web app's visualization.

### Deliverables

1. **Steady-State Analysis**
   - Compute and display steady-state peak/trough ratio
   - Time-to-steady-state estimate (5× half-life)
   - Accumulation factor: `1 / (1 - exp(-ke × tau))` where tau = dosing interval
   - Compare theoretical vs. simulated steady-state values

2. **Parameter Sensitivity Analysis**
   - Vary one parameter (e.g., half-life ±20%) while holding others constant
   - Plot family of curves showing sensitivity
   - Heatmap: peak concentration vs. (half-life, uptake) parameter space

3. **Dosing Schedule Comparison**
   - Side-by-side: same total daily dose, different frequencies (e.g., 600mg tid vs. 900mg bid)
   - Highlight differences in peak-trough swing
   - Table of metrics: peak, trough, AUC (area under curve via trapezoidal integration), swing ratio

4. **Titration/Taper Visualization**
   - `DosageSchedule` support: steps with varying doses over time
   - Plot showing dose changes and resulting concentration trajectory
   - Useful for visualizing medication start-up or discontinuation protocols

5. **Export & Reporting**
   - Matplotlib figures saved as PNG/SVG
   - Summary statistics exported to CSV
   - Notebook convertible to PDF via `nbconvert` for sharing

### Validation Criteria
- [ ] Accumulation factor matches analytical formula
- [ ] AUC computed via numpy trapezoid agrees with analytical AUC for simple cases
- [ ] Sensitivity plots show expected monotonic relationships
- [ ] Titration curves show smooth dose transitions

---

## Future Recommendations

Items beyond the three phases, for consideration as the notebook matures:

1. **Two-Compartment Model**
   - Add distribution phase (alpha/beta elimination)
   - Relevant for IV drugs and drugs with tissue redistribution
   - Would require additional parameters (Vd_central, Vd_peripheral, inter-compartmental clearance)

2. **Population PK (Monte Carlo)**
   - Add inter-individual variability (IIV) to parameters
   - Simulate population of virtual patients with log-normal parameter distributions
   - Plot confidence bands (5th/95th percentile) around mean curve

3. **Bioavailability (F < 1.0)**
   - Currently assumes F = 1.0 (complete absorption)
   - Add bioavailability parameter for oral drugs with incomplete absorption
   - Compare IV (F=1.0) vs. oral (F<1.0) administration

4. **Drug-Drug Interactions**
   - Model enzyme inhibition/induction effects on ke
   - Example: CYP3A4 inhibitor increasing half-life of co-administered drug

5. **Therapeutic Window Overlay**
   - Add horizontal bands for MEC (minimum effective concentration) and MTC (minimum toxic concentration)
   - Requires absolute concentration values (needs Vd parameter)
   - Visual indicator of time-in-therapeutic-range

6. **Real Patient Data Fitting**
   - Import measured drug levels (blood draws)
   - Fit model parameters to observed data using scipy.optimize
   - Bayesian estimation of individual PK parameters

7. **Interactive Dashboard (Panel/Voila)**
   - Convert notebook into standalone web dashboard
   - Full widget-based UI without requiring Jupyter
   - Deployable to cloud (Heroku, Railway, etc.)

8. **Colab / Binder Integration**
   - One-click launch badge for Google Colab
   - Binder configuration for zero-install access
   - Pre-install dependencies in environment.yml

---

## Technical Notes

### Porting Strategy
- The TypeScript calculation engine uses pure functions with no UI dependencies — direct port to Python
- NumPy vectorization replaces the TypeScript loop-based approach for better performance
- Matplotlib replaces Chart.js; both handle line charts well for this use case
- JSON prescription format is identical between web app and notebook

### Dependencies (Minimal)
| Package | Purpose | Phase |
|---------|---------|-------|
| `numpy` | Array math, exponentials | 1 |
| `matplotlib` | Plotting | 1 |
| `ipywidgets` | Interactive sliders (optional) | 1 |
| `pandas` | Milestone tables, CSV export | 2 |
| `scipy` | Trapezoidal AUC, future curve fitting | 3 |

### File Structure
```
notebook/
├── PLAN.md                    # This file
├── README.md                  # End-user guide
└── pharmacokinetics.ipynb     # The notebook
```

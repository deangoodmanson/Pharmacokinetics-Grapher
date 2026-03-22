import marimo

__generated_with = "0.13.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    mo.md(
        r"""
        # Pharmacokinetics Grapher

        Visualize medication concentration curves using one-compartment pharmacokinetic modeling.

        > **Educational use only.** Approximate relative concentration curves based on simplified PK models. Not for medical dosing decisions.
        """
    )
    return


@app.cell
def _():
    import numpy as np
    import matplotlib.pyplot as plt
    from dataclasses import dataclass, field
    from typing import Optional, List
    import json

    plt.rcParams["figure.figsize"] = (12, 5)
    plt.rcParams["figure.dpi"] = 100

    LN2 = np.log(2)  # 0.6931471805599453 — matches Math.LN2 in web app
    return LN2, List, Optional, dataclass, field, json, np, plt


@app.cell
def _(mo):
    mo.md(
        r"""
        ---
        ## Phase 1: Minimal — Single-Dose Visualization

        ### Prescription Model
        """
    )
    return


@app.cell
def _(List, Optional, dataclass, field):
    FREQUENCY_MAP = {
        "once": 1, "qd": 1, "bid": 2, "tid": 3, "qid": 4,
        "q3h": 8, "q6h": 4, "q8h": 3, "q12h": 2, "custom": None,
    }

    DEFAULT_TIMES = {
        "once": ["09:00"], "qd": ["09:00"],
        "bid": ["09:00", "21:00"],
        "tid": ["08:00", "14:00", "20:00"],
        "qid": ["08:00", "12:00", "16:00", "20:00"],
        "q3h": ["06:00", "09:00", "12:00", "15:00", "18:00", "21:00", "00:00", "03:00"],
        "q6h": ["06:00", "12:00", "18:00", "00:00"],
        "q8h": ["06:00", "14:00", "22:00"],
        "q12h": ["08:00", "20:00"],
    }

    KA_KE_TOLERANCE = 0.001

    @dataclass
    class Prescription:
        name: str
        dose: float
        half_life: float
        uptake: float
        peak: float
        frequency: str = "qd"
        times: List[str] = field(default_factory=lambda: ["09:00"])
        metabolite_life: Optional[float] = None
        relative_metabolite_level: Optional[float] = None
        metabolite_name: Optional[str] = None
        duration: Optional[float] = None
        duration_unit: Optional[str] = None

        def __post_init__(self):
            if self.times is None:
                self.times = DEFAULT_TIMES.get(self.frequency, ["09:00"])

    return DEFAULT_TIMES, FREQUENCY_MAP, KA_KE_TOLERANCE, Prescription


@app.cell
def _(mo):
    mo.md(r"""### Core PK Equation — Single Dose""")
    return


@app.cell
def _(KA_KE_TOLERANCE, LN2, np):
    def calculate_concentration(t, dose, half_life, uptake):
        """One-compartment first-order absorption. Returns raw (unnormalized) concentration."""
        t = np.asarray(t, dtype=float)

        if dose <= 0 or half_life <= 0 or uptake <= 0:
            return np.zeros_like(t)

        ke = LN2 / half_life
        ka = LN2 / uptake

        result = np.zeros_like(t)
        mask = t > 0

        if abs(ka - ke) < KA_KE_TOLERANCE:
            result[mask] = dose * ka * t[mask] * np.exp(-ke * t[mask])
        else:
            result[mask] = dose * (ka / (ka - ke)) * (
                np.exp(-ke * t[mask]) - np.exp(-ka * t[mask])
            )

        return np.maximum(result, 0)

    return (calculate_concentration,)


@app.cell
def _(Prescription, calculate_concentration, np, plt):
    # Example: Ibuprofen 400mg
    ibuprofen = Prescription(
        name="Ibuprofen",
        dose=400,
        half_life=2.0,
        uptake=0.5,
        peak=1.5,
        frequency="tid",
        times=["08:00", "14:00", "20:00"],
    )

    _t = np.linspace(0, 12, 500)
    _c = calculate_concentration(_t, ibuprofen.dose, ibuprofen.half_life, ibuprofen.uptake)
    _c_normalized = _c / _c.max() if _c.max() > 0 else _c

    _fig, _ax = plt.subplots()
    _ax.plot(_t, _c_normalized, linewidth=2)
    _ax.set_xlabel("Time (hours)")
    _ax.set_ylabel("Relative Concentration (peak = 1.0)")
    _ax.set_title(f"{ibuprofen.name} — Single Dose ({ibuprofen.dose}mg)")
    _ax.set_ylim(0, 1.05)
    _ax.grid(True, alpha=0.3)
    plt.tight_layout()
    _fig
    return (ibuprofen,)


@app.cell
def _(mo):
    mo.md(
        r"""
        ---
        ## Phase 2: Core Functionality — Multi-Dose Accumulation

        ### Dose Expansion & Accumulation
        """
    )
    return


@app.cell
def _(calculate_concentration, np):
    def parse_time(time_str):
        """Convert HH:MM string to hours."""
        h, m = time_str.split(":")
        return int(h) + int(m) / 60

    def expand_dose_times(times, num_days):
        """Generate all dose administration times (in hours) across num_days."""
        dose_times = []
        for day in range(num_days):
            for t_str in times:
                dose_times.append(day * 24 + parse_time(t_str))
        return sorted(dose_times)

    def _dosing_end_hours(rx, fallback_end):
        """Compute the hour at which dosing stops (duration limit or fallback)."""
        if rx.duration is not None:
            unit = getattr(rx, "duration_unit", None) or "days"
            return rx.duration * 24 if unit == "days" else rx.duration
        return fallback_end

    def accumulate_doses(rx, start_hours=0, end_hours=None, interval_minutes=15):
        """Multi-dose accumulation. Returns (time_array, normalized_concentration)."""
        if end_hours is None:
            end_hours = max(rx.half_life * 10, 48)

        dosing_end = _dosing_end_hours(rx, end_hours)

        num_days = int(np.ceil(dosing_end / 24)) + 1
        dose_times = expand_dose_times(rx.times, num_days)

        dose_times = [dt for dt in dose_times if dt < dosing_end]

        t = np.arange(start_hours, end_hours, interval_minutes / 60)
        total = np.zeros_like(t)

        for dose_time in dose_times:
            elapsed = t - dose_time
            contribution = calculate_concentration(elapsed, rx.dose, rx.half_life, rx.uptake)
            total += contribution

        max_conc = total.max()
        if max_conc > 0:
            total /= max_conc

        return t, total

    return accumulate_doses, expand_dose_times, parse_time, _dosing_end_hours


@app.cell
def _(mo):
    mo.md(r"""### Metabolite Calculation""")
    return


@app.cell
def _(KA_KE_TOLERANCE, LN2, _dosing_end_hours, expand_dose_times, np):
    def calculate_metabolite_concentration(t, dose, parent_half_life, metabolite_half_life, fm=1.0):
        """Sequential metabolism model. Returns raw concentration."""
        t = np.asarray(t, dtype=float)

        if dose <= 0 or parent_half_life <= 0 or metabolite_half_life <= 0:
            return np.zeros_like(t)

        ke_parent = LN2 / parent_half_life
        ke_metabolite = LN2 / metabolite_half_life

        result = np.zeros_like(t)
        mask = t > 0

        if abs(ke_metabolite - ke_parent) < KA_KE_TOLERANCE:
            result[mask] = dose * fm * ke_parent * t[mask] * np.exp(-ke_parent * t[mask])
        else:
            result[mask] = dose * fm * ke_parent / (ke_metabolite - ke_parent) * (
                np.exp(-ke_parent * t[mask]) - np.exp(-ke_metabolite * t[mask])
            )

        return np.maximum(result, 0)

    def accumulate_metabolite_doses(rx, start_hours=0, end_hours=None, interval_minutes=15):
        """Multi-dose metabolite accumulation. Returns (time_array, normalized_concentration) or None."""
        if rx.metabolite_life is None or rx.relative_metabolite_level is None:
            return None

        if end_hours is None:
            end_hours = max(rx.half_life * 10, rx.metabolite_life * 10, 48)

        dosing_end = _dosing_end_hours(rx, end_hours)

        num_days = int(np.ceil(dosing_end / 24)) + 1
        dose_times = expand_dose_times(rx.times, num_days)

        dose_times = [dt for dt in dose_times if dt < dosing_end]

        t = np.arange(start_hours, end_hours, interval_minutes / 60)
        total = np.zeros_like(t)

        for dose_time in dose_times:
            elapsed = t - dose_time
            contribution = calculate_metabolite_concentration(
                elapsed, rx.dose, rx.half_life, rx.metabolite_life
            )
            total += contribution

        max_conc = total.max()
        if max_conc > 0:
            total = total / max_conc * rx.relative_metabolite_level

        return t, total

    return accumulate_metabolite_doses, calculate_metabolite_concentration


@app.cell
def _(accumulate_doses, ibuprofen, plt):
    _t, _c = accumulate_doses(ibuprofen, start_hours=0, end_hours=48)

    _fig, _ax = plt.subplots()
    _ax.plot(_t, _c, linewidth=2, label=f"{ibuprofen.name} {ibuprofen.dose}mg ({ibuprofen.frequency})")
    _ax.set_xlabel("Time (hours)")
    _ax.set_ylabel("Relative Concentration (peak = 1.0)")
    _ax.set_title("Multi-Dose Accumulation")
    _ax.set_ylim(0, 1.05)
    _ax.legend()
    _ax.grid(True, alpha=0.3)
    plt.tight_layout()
    _fig
    return


@app.cell
def _(mo):
    mo.md(r"""### Multi-Drug Comparison""")
    return


@app.cell
def _(accumulate_doses, accumulate_metabolite_doses, plt):
    def plot_prescriptions(prescriptions, end_hours=48, title="PK Comparison"):
        """Overlay multiple drug curves on one plot."""
        fig, ax = plt.subplots()
        colors = plt.cm.tab10.colors

        for i, rx in enumerate(prescriptions):
            color = colors[i % len(colors)]

            t, c = accumulate_doses(rx, end_hours=end_hours)
            label = f"{rx.name} {rx.dose}mg ({rx.frequency})"
            ax.plot(t, c, linewidth=2, color=color, label=label)

            met = accumulate_metabolite_doses(rx, end_hours=end_hours)
            if met is not None:
                t_m, c_m = met
                met_label = f"{rx.name} — Metabolite"
                ax.plot(t_m, c_m, linewidth=1.5, color=color, linestyle="--", label=met_label)

        ax.set_xlabel("Time (hours)")
        ax.set_ylabel("Relative Concentration (peak = 1.0)")
        ax.set_title(title)
        ax.set_ylim(0)
        ax.legend(loc="upper right")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    return (plot_prescriptions,)


@app.cell
def _(Prescription, ibuprofen, plot_prescriptions):
    acetaminophen = Prescription(
        name="Acetaminophen",
        dose=500,
        half_life=3.0,
        uptake=0.75,
        peak=1.0,
        frequency="q6h",
        times=["06:00", "12:00", "18:00", "00:00"],
    )

    _fig = plot_prescriptions(
        [ibuprofen, acetaminophen], end_hours=48, title="Ibuprofen vs Acetaminophen"
    )
    _fig
    return (acetaminophen,)


@app.cell
def _(mo):
    mo.md(r"""### Prescription JSON I/O""")
    return


@app.cell
def _(Prescription, json):
    def prescription_to_dict(rx):
        """Convert Prescription to dict matching web app JSON format."""
        d = {
            "name": rx.name,
            "dose": rx.dose,
            "halfLife": rx.half_life,
            "uptake": rx.uptake,
            "peak": rx.peak,
            "frequency": rx.frequency,
            "times": rx.times,
        }
        if rx.metabolite_life is not None:
            d["metaboliteLife"] = rx.metabolite_life
        if rx.relative_metabolite_level is not None:
            d["relativeMetaboliteLevel"] = rx.relative_metabolite_level
        if rx.metabolite_name is not None:
            d["metaboliteName"] = rx.metabolite_name
        if rx.duration is not None:
            d["duration"] = rx.duration
        if rx.duration_unit is not None:
            d["durationUnit"] = rx.duration_unit
        return d

    def prescription_from_dict(d):
        """Create Prescription from web app JSON format (handles legacy fields)."""
        rel_level = d.get("relativeMetaboliteLevel")
        if rel_level is None and "metaboliteConversionFraction" in d:
            rel_level = d["metaboliteConversionFraction"]

        met_life = d.get("metaboliteLife")
        met_name = d.get("metaboliteName")
        if met_life is None and isinstance(d.get("metaboliteHalfLife"), dict):
            met_life = d["metaboliteHalfLife"].get("halfLife")
            met_name = met_name or d["metaboliteHalfLife"].get("name")

        return Prescription(
            name=d["name"],
            dose=float(d["dose"]),
            half_life=float(d["halfLife"]),
            uptake=float(d["uptake"]),
            peak=float(d["peak"]),
            frequency=d.get("frequency", "qd"),
            times=d.get("times", ["09:00"]),
            metabolite_life=float(met_life) if met_life is not None else None,
            relative_metabolite_level=float(rel_level) if rel_level is not None else None,
            metabolite_name=met_name,
            duration=d.get("duration"),
            duration_unit=d.get("durationUnit"),
        )

    def save_prescriptions(prescriptions, filepath):
        """Export prescriptions to JSON file."""
        data = [prescription_to_dict(rx) for rx in prescriptions]
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        return f"Saved {len(data)} prescription(s) to {filepath}"

    def load_prescriptions(filepath):
        """Import prescriptions from JSON file."""
        with open(filepath) as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
        return [prescription_from_dict(d) for d in data]

    return load_prescriptions, prescription_from_dict, prescription_to_dict, save_prescriptions


@app.cell
def _(mo):
    mo.md(r"""### PK Milestone Timeline""")
    return


@app.cell
def _(KA_KE_TOLERANCE, LN2, _dosing_end_hours, expand_dose_times, mo, np):
    def calculate_milestones(rx, start_hours=0, end_hours=None):
        """Calculate PK milestone events for a prescription."""
        if end_hours is None:
            end_hours = max(rx.half_life * 10, 48)

        dosing_end = _dosing_end_hours(rx, end_hours)

        num_days = int(np.ceil(dosing_end / 24)) + 1
        dose_times = expand_dose_times(rx.times, num_days)
        dose_times = [dt for dt in dose_times if dt < dosing_end]

        events = []
        ke = LN2 / rx.half_life
        ka = LN2 / rx.uptake

        for i, dt in enumerate(dose_times):
            events.append({
                "time_hours": dt,
                "event": "Dose",
                "description": f"{rx.dose}mg administered",
                "level": None,
            })

            if abs(ka - ke) < KA_KE_TOLERANCE:
                t_peak = 1.0 / ke
            else:
                t_peak = np.log(ka / ke) / (ka - ke)

            peak_time = dt + t_peak
            next_dose = dose_times[i + 1] if i + 1 < len(dose_times) else end_hours

            if peak_time < next_dose and peak_time <= end_hours:
                events.append({
                    "time_hours": peak_time,
                    "event": "Peak",
                    "description": "Peak concentration (Cmax)",
                    "level": 100.0,
                })

            remaining = 100.0
            for hl in range(1, 11):
                remaining *= 0.5
                hl_time = dt + t_peak + hl * rx.half_life
                if remaining < 5 or hl_time >= next_dose or hl_time > end_hours:
                    break
                events.append({
                    "time_hours": hl_time,
                    "event": "Half-life",
                    "description": f"{hl}x half-life ({remaining:.1f}% remaining)",
                    "level": remaining,
                })

        events.sort(key=lambda e: e["time_hours"])
        return events

    def format_milestones_md(rx, end_hours=None):
        """Format milestone timeline as markdown table."""
        events = calculate_milestones(rx, end_hours=end_hours)

        lines = [
            f"**PK Timeline: {rx.name} {rx.dose}mg ({rx.frequency})**\n",
            "| Time (h) | Event | Level | Description |",
            "|----------|-------|-------|-------------|",
        ]

        for e in events:
            time_str = f'{e["time_hours"]:.1f}'
            level_str = f'{e["level"]:.1f}%' if e["level"] is not None else "—"
            lines.append(f'| {time_str} | {e["event"]} | {level_str} | {e["description"]} |')

        return mo.md("\n".join(lines))

    return calculate_milestones, format_milestones_md


@app.cell
def _(format_milestones_md, ibuprofen):
    format_milestones_md(ibuprofen, end_hours=24)
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ---
        ## Phase 3: Analysis

        ### Steady-State Analysis
        """
    )
    return


@app.cell
def _(LN2, accumulate_doses, mo, np, parse_time):
    def steady_state_analysis(rx):
        """Compute steady-state metrics for a prescription."""
        ke = LN2 / rx.half_life

        times_h = sorted([parse_time(t) for t in rx.times])
        if len(times_h) > 1:
            intervals = [times_h[i + 1] - times_h[i] for i in range(len(times_h) - 1)]
            intervals.append(24 - times_h[-1] + times_h[0])
            tau = np.mean(intervals)
        else:
            tau = 24.0

        accum_factor = 1 / (1 - np.exp(-ke * tau))
        t_ss = 5 * rx.half_life

        sim_end = t_ss + tau * 2
        t, c = accumulate_doses(rx, end_hours=sim_end)

        last_interval = t >= (sim_end - tau)
        if last_interval.any():
            ss_peak = c[last_interval].max()
            ss_trough = c[last_interval].min()
            swing = ss_peak - ss_trough
        else:
            ss_peak = ss_trough = swing = 0

        metrics = {
            "tau": tau, "accum_factor": accum_factor, "t_ss": t_ss,
            "ss_peak": ss_peak, "ss_trough": ss_trough, "swing": swing,
        }

        result = mo.md(f"""
**Steady-State Analysis: {rx.name}**

| Metric | Value |
|--------|-------|
| Dosing interval (tau) | {tau:.1f} hours |
| Elimination half-life | {rx.half_life:.1f} hours |
| Accumulation factor | {accum_factor:.2f}x |
| Time to steady-state | ~{t_ss:.0f} hours ({t_ss / 24:.1f} days) |
| SS peak (normalized) | {ss_peak:.3f} |
| SS trough (normalized) | {ss_trough:.3f} |
| Peak-trough swing | {swing:.3f} |
""")
        return result, metrics

    return (steady_state_analysis,)


@app.cell
def _(ibuprofen, steady_state_analysis):
    _result, _metrics = steady_state_analysis(ibuprofen)
    _result
    return


@app.cell
def _(mo):
    mo.md(r"""### Parameter Sensitivity""")
    return


@app.cell
def _(Prescription, accumulate_doses, plt):
    def sensitivity_plot(rx, param_name, values, end_hours=48):
        """Plot family of curves varying one parameter."""
        fig, ax = plt.subplots()
        cmap = plt.cm.viridis

        for i, val in enumerate(values):
            modified = Prescription(
                name=rx.name, dose=rx.dose, half_life=rx.half_life,
                uptake=rx.uptake, peak=rx.peak, frequency=rx.frequency,
                times=list(rx.times),
            )
            setattr(modified, param_name, val)

            t, c = accumulate_doses(modified, end_hours=end_hours)
            color = cmap(i / max(len(values) - 1, 1))
            ax.plot(t, c, linewidth=1.5, color=color, label=f"{param_name}={val}")

        ax.set_xlabel("Time (hours)")
        ax.set_ylabel("Relative Concentration")
        ax.set_title(f"Sensitivity: {rx.name} — varying {param_name}")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    return (sensitivity_plot,)


@app.cell
def _(ibuprofen, sensitivity_plot):
    _fig = sensitivity_plot(ibuprofen, "half_life", [1.0, 1.5, 2.0, 3.0, 4.0], end_hours=48)
    _fig
    return


@app.cell
def _(mo):
    mo.md(r"""### Dosing Frequency Comparison""")
    return


@app.cell
def _(DEFAULT_TIMES, FREQUENCY_MAP, Prescription, plot_prescriptions):
    def compare_frequencies(base_rx, frequencies, end_hours=48):
        """Compare same drug at different dosing frequencies (adjusting dose to match daily total)."""
        base_n = FREQUENCY_MAP.get(base_rx.frequency)
        if base_n is None:
            base_n = len(base_rx.times) or 1
        base_daily = base_rx.dose * base_n

        variants = []
        for freq in frequencies:
            n_doses = FREQUENCY_MAP.get(freq)
            if n_doses is None:
                continue
            dose_per = base_daily / n_doses
            rx = Prescription(
                name=base_rx.name, dose=dose_per, half_life=base_rx.half_life,
                uptake=base_rx.uptake, peak=base_rx.peak, frequency=freq,
                times=DEFAULT_TIMES.get(freq, ["09:00"]),
            )
            variants.append(rx)

        fig = plot_prescriptions(
            variants, end_hours=end_hours,
            title=f"{base_rx.name} — Same Daily Dose, Different Frequencies",
        )
        return fig

    return (compare_frequencies,)


@app.cell
def _(compare_frequencies, ibuprofen):
    _fig = compare_frequencies(ibuprofen, ["bid", "tid", "qid", "q6h"])
    _fig
    return


@app.cell
def _(mo):
    mo.md(r"""### Titration / Taper Schedule""")
    return


@app.cell
def _(calculate_concentration, dataclass, np, parse_time, plt):
    @dataclass
    class DoseStep:
        dose: float
        duration_days: int

    def accumulate_schedule(rx, steps, interval_minutes=15):
        """Accumulate doses across a titration/taper schedule with variable doses."""
        total_days = sum(s.duration_days for s in steps)
        end_hours = total_days * 24 + rx.half_life * 5

        dose_events = []
        day_offset = 0
        for step in steps:
            for day in range(step.duration_days):
                for t_str in rx.times:
                    dose_events.append(((day_offset + day) * 24 + parse_time(t_str), step.dose))
            day_offset += step.duration_days

        t = np.arange(0, end_hours, interval_minutes / 60)
        total = np.zeros_like(t)

        for dose_time, dose_mg in dose_events:
            elapsed = t - dose_time
            contribution = calculate_concentration(elapsed, dose_mg, rx.half_life, rx.uptake)
            total += contribution

        max_conc = total.max()
        if max_conc > 0:
            total /= max_conc

        return t, total

    def plot_schedule(rx, steps, title=None):
        """Plot a titration/taper schedule with dose step annotations."""
        t, c = accumulate_schedule(rx, steps)

        fig, ax = plt.subplots(figsize=(14, 5))
        ax.plot(t, c, linewidth=2)
        ax.set_xlabel("Time (hours)")
        ax.set_ylabel("Relative Concentration")
        ax.set_title(title or f"{rx.name} Schedule")

        day_offset = 0
        for step in steps:
            ax.axvline(x=day_offset * 24, color="gray", linestyle=":", alpha=0.5)
            ax.text(
                day_offset * 24 + 12, 0.95, f"{step.dose}mg",
                ha="center", fontsize=8, color="gray",
            )
            day_offset += step.duration_days

        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    return DoseStep, accumulate_schedule, plot_schedule


@app.cell
def _(DoseStep, Prescription, plot_schedule):
    prednisone = Prescription(
        name="Prednisone", dose=40, half_life=3.5, uptake=1.0, peak=2.0,
        frequency="qd", times=["08:00"],
    )

    taper_steps = [
        DoseStep(dose=40, duration_days=5),
        DoseStep(dose=30, duration_days=5),
        DoseStep(dose=20, duration_days=5),
        DoseStep(dose=10, duration_days=5),
        DoseStep(dose=5, duration_days=5),
    ]

    _fig = plot_schedule(prednisone, taper_steps, title="Prednisone Taper Schedule")
    _fig
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ---
        ## Your Prescriptions

        Edit the cell below to define your own prescriptions, then the plots will update automatically.
        """
    )
    return


@app.cell
def _(Prescription, format_milestones_md, mo, plot_prescriptions, steady_state_analysis):
    my_prescriptions = [
        Prescription(
            name="Drug A",
            dose=500,
            half_life=6.0,
            uptake=1.5,
            peak=2.0,
            frequency="bid",
            times=["09:00", "21:00"],
        ),
        # Add more prescriptions as needed:
        # Prescription(name="Drug B", dose=..., half_life=..., uptake=..., peak=...),
    ]

    _fig = plot_prescriptions(my_prescriptions, end_hours=72)

    _milestones = mo.vstack([format_milestones_md(rx, end_hours=48) for rx in my_prescriptions])
    _analyses = mo.vstack([steady_state_analysis(rx)[0] for rx in my_prescriptions])

    mo.vstack([_fig, _milestones, _analyses])
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ---
        ## Load from Web App Export

        Import prescriptions exported from the Pharmacokinetics Grapher web application.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ```python
        # Uncomment and edit the path to load from a JSON export:
        # imported = load_prescriptions('my_export.json')
        # plot_prescriptions(imported, end_hours=72)
        ```
        """
    )
    return


if __name__ == "__main__":
    app.run()

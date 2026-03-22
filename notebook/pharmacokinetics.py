# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo",
#     "numpy",
#     "matplotlib",
# ]
# ///

import marimo

__generated_with = "0.21.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(r"""
    # Pharmacokinetics Grapher

    Visualize medication concentration curves using one-compartment pharmacokinetic modeling.

    > **Educational use only.** Approximate relative concentration curves based on simplified PK models. Not for medical dosing decisions.
    """)
    return


@app.cell
def _():
    import numpy as np
    import matplotlib.pyplot as plt

    from pk_core import (
        Prescription, DoseStep, FREQUENCY_MAP, DEFAULT_TIMES,
        calculate_concentration, accumulate_doses, accumulate_metabolite_doses,
        accumulate_schedule, calculate_milestones, compute_steady_state_metrics,
        save_prescriptions, load_prescriptions, generate_frequency_variants,
    )

    plt.rcParams["figure.figsize"] = (12, 5)
    plt.rcParams["figure.dpi"] = 100
    return (
        DoseStep,
        Prescription,
        accumulate_doses,
        accumulate_metabolite_doses,
        accumulate_schedule,
        calculate_concentration,
        calculate_milestones,
        compute_steady_state_metrics,
        generate_frequency_variants,
        np,
        plt,
    )


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## Phase 1: Single-Dose Visualization
    """)
    return


@app.cell
def _(Prescription, calculate_concentration, np, plt):
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
    mo.md(r"""
    ---
    ## Phase 2: Multi-Dose Accumulation
    """)
    return


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
    mo.md(r"""
    ### Multi-Drug Comparison
    """)
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
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### PK Milestone Timeline
    """)
    return


@app.cell
def _(calculate_milestones, mo):
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

    return (format_milestones_md,)


@app.cell
def _(format_milestones_md, ibuprofen):
    format_milestones_md(ibuprofen, end_hours=24)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## Phase 3: Analysis

    ### Steady-State Analysis
    """)
    return


@app.cell
def _(compute_steady_state_metrics, mo):
    def display_steady_state(rx):
        """Compute and display steady-state metrics as markdown."""
        m = compute_steady_state_metrics(rx)
        return mo.md(f"""
    **Steady-State Analysis: {rx.name}**

    | Metric | Value |
    |--------|-------|
    | Dosing interval (tau) | {m["tau"]:.1f} hours |
    | Elimination half-life | {rx.half_life:.1f} hours |
    | Accumulation factor | {m["accum_factor"]:.2f}x |
    | Time to steady-state | ~{m["t_ss"]:.0f} hours ({m["t_ss"] / 24:.1f} days) |
    | SS peak (normalized) | {m["ss_peak"]:.3f} |
    | SS trough (normalized) | {m["ss_trough"]:.3f} |
    | Peak-trough swing | {m["swing"]:.3f} |
    """), m

    return (display_steady_state,)


@app.cell
def _(display_steady_state, ibuprofen):
    _result, _metrics = display_steady_state(ibuprofen)
    _result
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Parameter Sensitivity
    """)
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
    mo.md(r"""
    ### Dosing Frequency Comparison
    """)
    return


@app.cell
def _(generate_frequency_variants, ibuprofen, plot_prescriptions):
    _variants = generate_frequency_variants(ibuprofen, ["bid", "tid", "qid", "q6h"])
    _fig = plot_prescriptions(
        _variants, end_hours=48,
        title=f"{ibuprofen.name} — Same Daily Dose, Different Frequencies",
    )
    _fig
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Titration / Taper Schedule
    """)
    return


@app.cell
def _(DoseStep, Prescription, accumulate_schedule, plt):
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

    _t, _c = accumulate_schedule(prednisone, taper_steps)

    _fig, _ax = plt.subplots(figsize=(14, 5))
    _ax.plot(_t, _c, linewidth=2)
    _ax.set_xlabel("Time (hours)")
    _ax.set_ylabel("Relative Concentration")
    _ax.set_title("Prednisone Taper Schedule")

    _day_offset = 0
    for _step in taper_steps:
        _ax.axvline(x=_day_offset * 24, color="gray", linestyle=":", alpha=0.5)
        _ax.text(
            _day_offset * 24 + 12, 0.95, f"{_step.dose}mg",
            ha="center", fontsize=8, color="gray",
        )
        _day_offset += _step.duration_days

    _ax.grid(True, alpha=0.3)
    plt.tight_layout()
    _fig
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## Your Prescriptions

    Edit the cell below to define your own prescriptions, then the plots will update automatically.
    """)
    return


@app.cell
def _(
    Prescription,
    display_steady_state,
    format_milestones_md,
    mo,
    plot_prescriptions,
):
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
    ]

    _fig = plot_prescriptions(my_prescriptions, end_hours=72)
    _milestones = mo.vstack([format_milestones_md(rx, end_hours=48) for rx in my_prescriptions])
    _analyses = mo.vstack([display_steady_state(rx)[0] for rx in my_prescriptions])

    mo.vstack([_fig, _milestones, _analyses])
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## Load from Web App Export

    Import prescriptions exported from the Pharmacokinetics Grapher web application.

    ```python
    imported = load_prescriptions('my_export.json')
    plot_prescriptions(imported, end_hours=72)
    ```
    """)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()

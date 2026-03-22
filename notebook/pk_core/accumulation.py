"""Multi-dose accumulation and schedule calculations."""

import numpy as np

from .calculator import calculate_concentration, calculate_metabolite_concentration
from .models import DEFAULT_TIMES, FREQUENCY_MAP, Prescription


def parse_time(time_str):
    """Convert HH:MM string to hours from midnight."""
    h, m = time_str.split(":")
    return int(h) + int(m) / 60


def expand_dose_times(times, num_days):
    """Generate all dose administration times (in hours) across num_days."""
    dose_times = []
    for day in range(num_days):
        for t_str in times:
            dose_times.append(day * 24 + parse_time(t_str))
    return sorted(dose_times)


def dosing_end_hours(rx, fallback_end):
    """Compute the hour at which dosing stops (duration limit or fallback)."""
    if rx.duration is not None:
        unit = getattr(rx, "duration_unit", None) or "days"
        return rx.duration * 24 if unit == "days" else rx.duration
    return fallback_end


def accumulate_doses(rx, start_hours=0, end_hours=None, interval_minutes=15):
    """Multi-dose accumulation. Returns (time_array, normalized_concentration)."""
    if end_hours is None:
        end_hours = max(rx.half_life * 10, 48)

    d_end = dosing_end_hours(rx, end_hours)

    num_days = int(np.ceil(d_end / 24)) + 1
    dose_times = expand_dose_times(rx.times, num_days)
    dose_times = [dt for dt in dose_times if dt < d_end]

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


def accumulate_metabolite_doses(rx, start_hours=0, end_hours=None, interval_minutes=15):
    """Multi-dose metabolite accumulation. Returns (time_array, normalized_concentration) or None."""
    if rx.metabolite_life is None or rx.relative_metabolite_level is None:
        return None

    if end_hours is None:
        end_hours = max(rx.half_life * 10, rx.metabolite_life * 10, 48)

    d_end = dosing_end_hours(rx, end_hours)

    num_days = int(np.ceil(d_end / 24)) + 1
    dose_times = expand_dose_times(rx.times, num_days)
    dose_times = [dt for dt in dose_times if dt < d_end]

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


def accumulate_schedule(rx, steps, interval_minutes=15):
    """Accumulate doses across a titration/taper schedule with variable doses.

    Returns (time_array, normalized_concentration).
    """
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


def generate_frequency_variants(base_rx, frequencies):
    """Generate prescription variants with adjusted doses to match the same daily total.

    Returns list of Prescription objects. Skips 'custom' frequencies.
    """
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

    return variants

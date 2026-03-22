"""PK milestone event calculation."""

import numpy as np

from .accumulation import dosing_end_hours, expand_dose_times
from .models import KA_KE_TOLERANCE, LN2


def calculate_milestones(rx, start_hours=0, end_hours=None):
    """Calculate PK milestone events for a prescription.

    Returns list of dicts with keys: time_hours, event, description, level.
    """
    if end_hours is None:
        end_hours = max(rx.half_life * 10, 48)

    d_end = dosing_end_hours(rx, end_hours)

    num_days = int(np.ceil(d_end / 24)) + 1
    dose_times = expand_dose_times(rx.times, num_days)
    dose_times = [dt for dt in dose_times if dt < d_end]

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

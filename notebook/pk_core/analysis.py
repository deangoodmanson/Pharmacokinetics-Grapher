"""Steady-state and pharmacokinetic analysis computations."""

import numpy as np

from .accumulation import accumulate_doses, parse_time
from .models import LN2


def compute_steady_state_metrics(rx):
    """Compute steady-state metrics for a prescription.

    Returns dict with keys: tau, accum_factor, t_ss, ss_peak, ss_trough, swing.
    """
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
        ss_peak = float(c[last_interval].max())
        ss_trough = float(c[last_interval].min())
        swing = ss_peak - ss_trough
    else:
        ss_peak = ss_trough = swing = 0.0

    return {
        "tau": float(tau),
        "accum_factor": float(accum_factor),
        "t_ss": float(t_ss),
        "ss_peak": ss_peak,
        "ss_trough": ss_trough,
        "swing": swing,
    }

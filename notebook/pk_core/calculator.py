"""Single-dose pharmacokinetic concentration equations.

One-compartment first-order absorption model.
"""

import numpy as np

from .models import KA_KE_TOLERANCE, LN2


def calculate_concentration(t, dose, half_life, uptake):
    """One-compartment first-order absorption. Returns raw (unnormalized) concentration.

    Standard formula: C(t) = dose * [ka/(ka-ke)] * (exp(-ke*t) - exp(-ka*t))
    Fallback (|ka-ke| < tolerance): C(t) = dose * ka * t * exp(-ke*t)
    """
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


def calculate_metabolite_concentration(t, dose, parent_half_life, metabolite_half_life, fm=1.0):
    """Sequential metabolism model. Returns raw (unnormalized) metabolite concentration.

    Standard formula: C_met(t) = dose * fm * ke_p / (ke_m - ke_p) * (exp(-ke_p*t) - exp(-ke_m*t))
    Fallback (|ke_m - ke_p| < tolerance): C_met(t) = dose * fm * ke_p * t * exp(-ke_p*t)
    """
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

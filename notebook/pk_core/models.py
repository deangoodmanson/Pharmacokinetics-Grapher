"""Data models and constants for pharmacokinetic calculations."""

import math
from dataclasses import dataclass, field

LN2 = math.log(2)  # 0.6931471805599453

KA_KE_TOLERANCE = 0.001

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


@dataclass
class Prescription:
    name: str
    dose: float              # mg
    half_life: float         # hours
    uptake: float            # hours (absorption time)
    peak: float              # hours (Tmax, stored for reference)
    frequency: str = "qd"
    times: list[str] = field(default_factory=lambda: ["09:00"])
    metabolite_life: float | None = None
    relative_metabolite_level: float | None = None
    metabolite_name: str | None = None
    duration: float | None = None
    duration_unit: str | None = None  # 'days' or 'hours'

    def __post_init__(self):
        if self.times is None:
            self.times = DEFAULT_TIMES.get(self.frequency, ["09:00"])


@dataclass
class DoseStep:
    dose: float          # mg per dose for this step
    duration_days: int   # how long this step lasts

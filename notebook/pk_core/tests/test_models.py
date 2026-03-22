"""Tests for pk_core.models."""

import math

from pk_core.models import (
    DEFAULT_TIMES,
    FREQUENCY_MAP,
    KA_KE_TOLERANCE,
    LN2,
    DoseStep,
    Prescription,
)


class TestConstants:
    def test_ln2_matches_math(self):
        assert LN2 == math.log(2)

    def test_ka_ke_tolerance_positive(self):
        assert KA_KE_TOLERANCE > 0

    def test_frequency_map_keys(self):
        expected = {"once", "qd", "bid", "tid", "qid", "q3h", "q6h", "q8h", "q12h", "custom"}
        assert set(FREQUENCY_MAP.keys()) == expected

    def test_frequency_map_custom_is_none(self):
        assert FREQUENCY_MAP["custom"] is None

    def test_default_times_match_frequency_counts(self):
        for freq, count in FREQUENCY_MAP.items():
            if freq == "custom" or freq not in DEFAULT_TIMES:
                continue
            assert len(DEFAULT_TIMES[freq]) == count, f"{freq}: expected {count} times"


class TestPrescription:
    def test_basic_creation(self):
        rx = Prescription(name="Test", dose=500, half_life=6.0, uptake=1.5, peak=2.0)
        assert rx.name == "Test"
        assert rx.dose == 500
        assert rx.frequency == "qd"
        assert rx.times == ["09:00"]

    def test_none_times_defaults_from_frequency(self):
        rx = Prescription(
            name="Test", dose=500, half_life=6.0, uptake=1.5, peak=2.0,
            frequency="bid", times=None,
        )
        assert rx.times == ["09:00", "21:00"]

    def test_optional_fields_default_none(self):
        rx = Prescription(name="Test", dose=500, half_life=6.0, uptake=1.5, peak=2.0)
        assert rx.metabolite_life is None
        assert rx.relative_metabolite_level is None
        assert rx.duration is None
        assert rx.duration_unit is None


class TestDoseStep:
    def test_creation(self):
        step = DoseStep(dose=40, duration_days=5)
        assert step.dose == 40
        assert step.duration_days == 5

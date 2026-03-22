"""Tests for pk_core.accumulation."""

import numpy as np
import pytest

from pk_core.accumulation import (
    accumulate_doses,
    accumulate_metabolite_doses,
    accumulate_schedule,
    dosing_end_hours,
    expand_dose_times,
    generate_frequency_variants,
    parse_time,
)
from pk_core.models import DoseStep, FREQUENCY_MAP, Prescription


class TestParseTime:
    def test_midnight(self):
        assert parse_time("00:00") == 0.0

    def test_noon(self):
        assert parse_time("12:00") == 12.0

    def test_with_minutes(self):
        assert parse_time("09:30") == 9.5

    def test_evening(self):
        assert parse_time("21:00") == 21.0

    def test_end_of_day(self):
        assert parse_time("23:59") == pytest.approx(23 + 59 / 60)


class TestExpandDoseTimes:
    def test_single_dose_one_day(self):
        times = expand_dose_times(["09:00"], 1)
        assert times == [9.0]

    def test_bid_two_days(self):
        times = expand_dose_times(["09:00", "21:00"], 2)
        assert times == [9.0, 21.0, 33.0, 45.0]

    def test_sorted_output(self):
        times = expand_dose_times(["21:00", "09:00"], 2)
        assert times == sorted(times)

    def test_zero_days(self):
        times = expand_dose_times(["09:00"], 0)
        assert times == []


class TestDosingEndHours:
    def test_no_duration_returns_fallback(self):
        rx = Prescription(name="T", dose=500, half_life=6, uptake=1.5, peak=2)
        assert dosing_end_hours(rx, 48) == 48

    def test_duration_days(self):
        rx = Prescription(name="T", dose=500, half_life=6, uptake=1.5, peak=2,
                          duration=7, duration_unit="days")
        assert dosing_end_hours(rx, 48) == 168  # 7 * 24

    def test_duration_hours(self):
        rx = Prescription(name="T", dose=500, half_life=6, uptake=1.5, peak=2,
                          duration=36, duration_unit="hours")
        assert dosing_end_hours(rx, 48) == 36

    def test_duration_no_unit_defaults_days(self):
        rx = Prescription(name="T", dose=500, half_life=6, uptake=1.5, peak=2,
                          duration=3)
        assert dosing_end_hours(rx, 48) == 72  # 3 * 24


class TestAccumulateDoses:
    @pytest.fixture
    def bid_rx(self):
        return Prescription(
            name="Test", dose=500, half_life=6.0, uptake=1.5, peak=2.0,
            frequency="bid", times=["09:00", "21:00"],
        )

    def test_returns_tuple(self, bid_rx):
        result = accumulate_doses(bid_rx, end_hours=48)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_normalized_peak_is_one(self, bid_rx):
        t, c = accumulate_doses(bid_rx, end_hours=48)
        assert pytest.approx(c.max(), abs=1e-6) == 1.0

    def test_non_negative(self, bid_rx):
        t, c = accumulate_doses(bid_rx, end_hours=48)
        assert np.all(c >= 0)

    def test_time_array_spacing(self, bid_rx):
        t, c = accumulate_doses(bid_rx, end_hours=48, interval_minutes=15)
        dt = np.diff(t)
        np.testing.assert_allclose(dt, 0.25, atol=1e-10)

    def test_accumulation_increases_trough(self, bid_rx):
        """Later troughs should be higher than early troughs due to accumulation."""
        t, c = accumulate_doses(bid_rx, end_hours=72)
        # Compare trough at ~hour 15 vs ~hour 63
        early_mask = (t >= 14) & (t <= 16)
        late_mask = (t >= 62) & (t <= 64)
        if early_mask.any() and late_mask.any():
            assert c[late_mask].min() >= c[early_mask].min()

    def test_duration_limits_dosing(self):
        rx = Prescription(
            name="Test", dose=500, half_life=6.0, uptake=1.5, peak=2.0,
            frequency="qd", times=["09:00"], duration=1, duration_unit="days",
        )
        t, c = accumulate_doses(rx, end_hours=72)
        # After day 1, concentration should only decay
        late = c[t >= 48]
        assert late.max() < 0.1  # should be near zero after many half-lives


class TestAccumulateMetaboliteDoses:
    def test_returns_none_without_metabolite_data(self):
        rx = Prescription(name="T", dose=500, half_life=6, uptake=1.5, peak=2)
        assert accumulate_metabolite_doses(rx) is None

    def test_returns_none_with_partial_data(self):
        rx = Prescription(name="T", dose=500, half_life=6, uptake=1.5, peak=2,
                          metabolite_life=12)
        assert accumulate_metabolite_doses(rx) is None

    def test_returns_data_with_full_metabolite(self):
        rx = Prescription(name="T", dose=500, half_life=6, uptake=1.5, peak=2,
                          metabolite_life=12, relative_metabolite_level=1.0,
                          frequency="bid", times=["09:00", "21:00"])
        result = accumulate_metabolite_doses(rx, end_hours=48)
        assert result is not None
        t, c = result
        assert len(t) > 0
        assert np.all(c >= 0)

    def test_peak_scales_to_relative_level(self):
        rx = Prescription(name="T", dose=500, half_life=6, uptake=1.5, peak=2,
                          metabolite_life=12, relative_metabolite_level=0.5,
                          frequency="bid", times=["09:00", "21:00"])
        t, c = accumulate_metabolite_doses(rx, end_hours=48)
        assert pytest.approx(c.max(), abs=0.01) == 0.5


class TestAccumulateSchedule:
    def test_basic_schedule(self):
        rx = Prescription(name="T", dose=40, half_life=3.5, uptake=1.0, peak=2.0,
                          frequency="qd", times=["08:00"])
        steps = [DoseStep(dose=40, duration_days=3), DoseStep(dose=20, duration_days=3)]
        t, c = accumulate_schedule(rx, steps)
        assert pytest.approx(c.max(), abs=1e-6) == 1.0
        assert np.all(c >= 0)

    def test_schedule_length(self):
        rx = Prescription(name="T", dose=40, half_life=3.5, uptake=1.0, peak=2.0,
                          frequency="qd", times=["08:00"])
        steps = [DoseStep(dose=40, duration_days=5)]
        t, c = accumulate_schedule(rx, steps)
        expected_end = 5 * 24 + 3.5 * 5
        assert t[-1] < expected_end
        assert t[-1] > expected_end - 1


class TestGenerateFrequencyVariants:
    def test_preserves_daily_dose(self):
        rx = Prescription(name="T", dose=400, half_life=2, uptake=0.5, peak=1.5,
                          frequency="tid", times=["08:00", "14:00", "20:00"])
        daily = 400 * 3  # 1200mg

        variants = generate_frequency_variants(rx, ["bid", "qid"])
        assert len(variants) == 2

        for v in variants:
            n = FREQUENCY_MAP[v.frequency]
            assert pytest.approx(v.dose * n) == daily

    def test_skips_custom(self):
        rx = Prescription(name="T", dose=400, half_life=2, uptake=0.5, peak=1.5,
                          frequency="tid", times=["08:00", "14:00", "20:00"])
        variants = generate_frequency_variants(rx, ["bid", "custom", "qid"])
        freqs = [v.frequency for v in variants]
        assert "custom" not in freqs
        assert len(variants) == 2

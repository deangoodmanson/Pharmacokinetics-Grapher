"""Tests for pk_core.analysis."""

import numpy as np
import pytest

from pk_core.analysis import compute_steady_state_metrics
from pk_core.models import LN2, Prescription


class TestComputeSteadyStateMetrics:
    def setup_method(self):
        self.rx = Prescription(
            name="Test", dose=500, half_life=6.0, uptake=1.5, peak=2.0,
            frequency="bid", times=["09:00", "21:00"],
        )

    def test_returns_dict_with_expected_keys(self):
        metrics = compute_steady_state_metrics(self.rx)
        expected_keys = {"tau", "accum_factor", "t_ss", "ss_peak", "ss_trough", "swing"}
        assert set(metrics.keys()) == expected_keys

    def test_tau_for_bid(self):
        metrics = compute_steady_state_metrics(self.rx)
        assert pytest.approx(metrics["tau"], abs=0.1) == 12.0

    def test_tau_for_qd(self):
        rx = Prescription(name="T", dose=500, half_life=6, uptake=1.5, peak=2,
                          frequency="qd", times=["09:00"])
        metrics = compute_steady_state_metrics(rx)
        assert pytest.approx(metrics["tau"]) == 24.0

    def test_accumulation_factor_formula(self):
        """Accumulation factor should match 1 / (1 - exp(-ke * tau))."""
        metrics = compute_steady_state_metrics(self.rx)
        ke = LN2 / self.rx.half_life
        expected = 1 / (1 - np.exp(-ke * metrics["tau"]))
        assert pytest.approx(metrics["accum_factor"], rel=1e-6) == expected

    def test_time_to_steady_state(self):
        metrics = compute_steady_state_metrics(self.rx)
        assert pytest.approx(metrics["t_ss"]) == 5 * self.rx.half_life

    def test_peak_ge_trough(self):
        metrics = compute_steady_state_metrics(self.rx)
        assert metrics["ss_peak"] >= metrics["ss_trough"]

    def test_swing_is_peak_minus_trough(self):
        metrics = compute_steady_state_metrics(self.rx)
        assert pytest.approx(metrics["swing"]) == metrics["ss_peak"] - metrics["ss_trough"]

    def test_ss_peak_near_one(self):
        """At steady state the peak should be near 1.0 (since curve is normalized)."""
        metrics = compute_steady_state_metrics(self.rx)
        assert metrics["ss_peak"] > 0.9

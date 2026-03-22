"""Tests for pk_core.calculator."""

import numpy as np
import pytest

from pk_core.calculator import calculate_concentration, calculate_metabolite_concentration
from pk_core.models import LN2


class TestCalculateConcentration:
    def test_positive_values_after_dose(self):
        t = np.linspace(0.1, 12, 100)
        c = calculate_concentration(t, dose=500, half_life=6.0, uptake=1.5)
        assert np.all(c >= 0)
        assert np.max(c) > 0

    def test_zero_dose_returns_zeros(self):
        t = np.linspace(0, 12, 50)
        c = calculate_concentration(t, dose=0, half_life=6.0, uptake=1.5)
        assert np.all(c == 0)

    def test_negative_dose_returns_zeros(self):
        t = np.linspace(0, 12, 50)
        c = calculate_concentration(t, dose=-100, half_life=6.0, uptake=1.5)
        assert np.all(c == 0)

    def test_negative_time_returns_zero(self):
        c = calculate_concentration(np.array([-1.0, -0.5]), dose=500, half_life=6.0, uptake=1.5)
        assert np.all(c == 0)

    def test_zero_time_returns_zero(self):
        c = calculate_concentration(np.array([0.0]), dose=500, half_life=6.0, uptake=1.5)
        assert c[0] == 0.0

    def test_zero_half_life_returns_zeros(self):
        t = np.linspace(0, 12, 50)
        c = calculate_concentration(t, dose=500, half_life=0, uptake=1.5)
        assert np.all(c == 0)

    def test_zero_uptake_returns_zeros(self):
        t = np.linspace(0, 12, 50)
        c = calculate_concentration(t, dose=500, half_life=6.0, uptake=0)
        assert np.all(c == 0)

    def test_curve_rises_then_falls(self):
        t = np.linspace(0.01, 24, 500)
        c = calculate_concentration(t, dose=500, half_life=6.0, uptake=1.5)
        peak_idx = np.argmax(c)
        assert peak_idx > 0
        assert peak_idx < len(c) - 1

    def test_decays_to_near_zero(self):
        """After many half-lives, concentration should be negligible."""
        t = np.array([100.0])  # ~16 half-lives for hl=6
        c = calculate_concentration(t, dose=500, half_life=6.0, uptake=1.5)
        assert c[0] < 0.01  # raw (unnormalized) value is small but not zero

    def test_ka_approx_ke_fallback(self):
        """When uptake ≈ half_life, fallback formula should produce smooth curve."""
        t = np.linspace(0.01, 24, 200)
        c = calculate_concentration(t, dose=500, half_life=4.0, uptake=4.0)
        assert np.all(c >= 0)
        assert np.max(c) > 0
        # Should still rise then fall
        peak_idx = np.argmax(c)
        assert peak_idx > 0

    def test_scalar_input(self):
        c = calculate_concentration(2.0, dose=500, half_life=6.0, uptake=1.5)
        assert float(c) > 0

    def test_known_peak_time(self):
        """Peak should occur at t_max = ln(ka/ke) / (ka - ke)."""
        half_life = 6.0
        uptake = 1.5
        ka = LN2 / uptake
        ke = LN2 / half_life
        expected_tmax = np.log(ka / ke) / (ka - ke)

        t = np.linspace(0.01, 24, 2000)
        c = calculate_concentration(t, dose=500, half_life=half_life, uptake=uptake)
        measured_tmax = t[np.argmax(c)]

        assert abs(measured_tmax - expected_tmax) < 0.02  # within one time step


class TestCalculateMetaboliteConcentration:
    def test_positive_values(self):
        t = np.linspace(0.1, 24, 100)
        c = calculate_metabolite_concentration(t, dose=500, parent_half_life=6.0, metabolite_half_life=12.0)
        assert np.all(c >= 0)
        assert np.max(c) > 0

    def test_zero_dose_returns_zeros(self):
        t = np.linspace(0, 12, 50)
        c = calculate_metabolite_concentration(t, dose=0, parent_half_life=6.0, metabolite_half_life=12.0)
        assert np.all(c == 0)

    def test_negative_time_returns_zero(self):
        c = calculate_metabolite_concentration(np.array([-1.0]), dose=500, parent_half_life=6.0, metabolite_half_life=12.0)
        assert c[0] == 0.0

    def test_ke_approx_fallback(self):
        """When parent and metabolite half-lives are equal, fallback should work."""
        t = np.linspace(0.01, 24, 200)
        c = calculate_metabolite_concentration(t, dose=500, parent_half_life=6.0, metabolite_half_life=6.0)
        assert np.all(c >= 0)
        assert np.max(c) > 0

    def test_fm_scaling(self):
        t = np.linspace(0.1, 24, 100)
        c1 = calculate_metabolite_concentration(t, dose=500, parent_half_life=6.0, metabolite_half_life=12.0, fm=1.0)
        c2 = calculate_metabolite_concentration(t, dose=500, parent_half_life=6.0, metabolite_half_life=12.0, fm=0.5)
        np.testing.assert_allclose(c2, c1 * 0.5, rtol=1e-10)

    def test_zero_parent_half_life_returns_zeros(self):
        t = np.linspace(0, 12, 50)
        c = calculate_metabolite_concentration(t, dose=500, parent_half_life=0, metabolite_half_life=12.0)
        assert np.all(c == 0)

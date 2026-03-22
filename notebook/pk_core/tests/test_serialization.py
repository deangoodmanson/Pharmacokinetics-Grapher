"""Tests for pk_core.serialization."""

import json
import os
import tempfile

import pytest

from pk_core.models import Prescription
from pk_core.serialization import (
    load_prescriptions,
    prescription_from_dict,
    prescription_to_dict,
    save_prescriptions,
)


class TestPrescriptionToDict:
    def test_basic_fields(self):
        rx = Prescription(name="Ibu", dose=400, half_life=2.0, uptake=0.5, peak=1.5,
                          frequency="tid", times=["08:00", "14:00", "20:00"])
        d = prescription_to_dict(rx)
        assert d["name"] == "Ibu"
        assert d["dose"] == 400
        assert d["halfLife"] == 2.0
        assert d["uptake"] == 0.5
        assert d["peak"] == 1.5
        assert d["frequency"] == "tid"
        assert d["times"] == ["08:00", "14:00", "20:00"]

    def test_omits_none_optional_fields(self):
        rx = Prescription(name="T", dose=500, half_life=6, uptake=1.5, peak=2)
        d = prescription_to_dict(rx)
        assert "metaboliteLife" not in d
        assert "relativeMetaboliteLevel" not in d
        assert "duration" not in d

    def test_includes_metabolite_fields(self):
        rx = Prescription(name="T", dose=500, half_life=6, uptake=1.5, peak=2,
                          metabolite_life=12, relative_metabolite_level=0.5,
                          metabolite_name="Met")
        d = prescription_to_dict(rx)
        assert d["metaboliteLife"] == 12
        assert d["relativeMetaboliteLevel"] == 0.5
        assert d["metaboliteName"] == "Met"

    def test_includes_duration(self):
        rx = Prescription(name="T", dose=500, half_life=6, uptake=1.5, peak=2,
                          duration=7, duration_unit="days")
        d = prescription_to_dict(rx)
        assert d["duration"] == 7
        assert d["durationUnit"] == "days"


class TestPrescriptionFromDict:
    def test_basic_round_trip(self):
        rx = Prescription(name="Ibu", dose=400, half_life=2.0, uptake=0.5, peak=1.5,
                          frequency="tid", times=["08:00", "14:00", "20:00"])
        d = prescription_to_dict(rx)
        rx2 = prescription_from_dict(d)
        assert rx2.name == rx.name
        assert rx2.dose == rx.dose
        assert rx2.half_life == rx.half_life
        assert rx2.uptake == rx.uptake
        assert rx2.peak == rx.peak
        assert rx2.frequency == rx.frequency
        assert rx2.times == rx.times

    def test_metabolite_round_trip(self):
        rx = Prescription(name="T", dose=500, half_life=6, uptake=1.5, peak=2,
                          metabolite_life=12, relative_metabolite_level=0.5)
        d = prescription_to_dict(rx)
        rx2 = prescription_from_dict(d)
        assert rx2.metabolite_life == 12
        assert rx2.relative_metabolite_level == 0.5

    def test_legacy_metabolite_conversion_fraction(self):
        d = {
            "name": "T", "dose": 500, "halfLife": 6, "uptake": 1.5, "peak": 2,
            "metaboliteConversionFraction": 0.3,
        }
        rx = prescription_from_dict(d)
        assert rx.relative_metabolite_level == 0.3

    def test_legacy_nested_metabolite_half_life(self):
        d = {
            "name": "T", "dose": 500, "halfLife": 6, "uptake": 1.5, "peak": 2,
            "metaboliteHalfLife": {"halfLife": 12, "name": "ActiveMet"},
        }
        rx = prescription_from_dict(d)
        assert rx.metabolite_life == 12
        assert rx.metabolite_name == "ActiveMet"

    def test_string_numbers_coerced(self):
        d = {
            "name": "T", "dose": "500", "halfLife": "6", "uptake": "1.5", "peak": "2",
        }
        rx = prescription_from_dict(d)
        assert rx.dose == 500.0
        assert isinstance(rx.dose, float)

    def test_defaults_for_missing_optional(self):
        d = {"name": "T", "dose": 500, "halfLife": 6, "uptake": 1.5, "peak": 2}
        rx = prescription_from_dict(d)
        assert rx.frequency == "qd"
        assert rx.times == ["09:00"]


class TestFileIO:
    def test_save_and_load_round_trip(self):
        rxs = [
            Prescription(name="A", dose=500, half_life=6, uptake=1.5, peak=2),
            Prescription(name="B", dose=400, half_life=2, uptake=0.5, peak=1.5,
                         frequency="tid", times=["08:00", "14:00", "20:00"]),
        ]
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            filepath = f.name

        try:
            save_prescriptions(rxs, filepath)
            loaded = load_prescriptions(filepath)
            assert len(loaded) == 2
            assert loaded[0].name == "A"
            assert loaded[1].name == "B"
            assert loaded[1].frequency == "tid"
        finally:
            os.unlink(filepath)

    def test_load_single_dict(self):
        """load_prescriptions should handle a single dict (not wrapped in array)."""
        d = {"name": "T", "dose": 500, "halfLife": 6, "uptake": 1.5, "peak": 2}
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump(d, f)
            filepath = f.name

        try:
            loaded = load_prescriptions(filepath)
            assert len(loaded) == 1
            assert loaded[0].name == "T"
        finally:
            os.unlink(filepath)

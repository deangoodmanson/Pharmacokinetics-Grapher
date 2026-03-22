"""Tests for pk_core.milestones."""

from pk_core.milestones import calculate_milestones
from pk_core.models import Prescription


class TestCalculateMilestones:
    def setup_method(self):
        self.rx = Prescription(
            name="Test", dose=500, half_life=6.0, uptake=1.5, peak=2.0,
            frequency="bid", times=["09:00", "21:00"],
        )

    def test_returns_list(self):
        events = calculate_milestones(self.rx, end_hours=24)
        assert isinstance(events, list)
        assert len(events) > 0

    def test_first_event_is_dose(self):
        events = calculate_milestones(self.rx, end_hours=24)
        assert events[0]["event"] == "Dose"

    def test_contains_peak_event(self):
        events = calculate_milestones(self.rx, end_hours=24)
        peak_events = [e for e in events if e["event"] == "Peak"]
        assert len(peak_events) > 0

    def test_contains_half_life_events(self):
        events = calculate_milestones(self.rx, end_hours=48)
        hl_events = [e for e in events if e["event"] == "Half-life"]
        assert len(hl_events) > 0

    def test_events_sorted_by_time(self):
        events = calculate_milestones(self.rx, end_hours=48)
        times = [e["time_hours"] for e in events]
        assert times == sorted(times)

    def test_peak_level_is_100(self):
        events = calculate_milestones(self.rx, end_hours=24)
        peak = next(e for e in events if e["event"] == "Peak")
        assert peak["level"] == 100.0

    def test_dose_level_is_none(self):
        events = calculate_milestones(self.rx, end_hours=24)
        dose = next(e for e in events if e["event"] == "Dose")
        assert dose["level"] is None

    def test_half_life_levels_decrease(self):
        # Use once-daily to get more half-life events between doses
        rx = Prescription(
            name="Test", dose=500, half_life=2.0, uptake=0.5, peak=1.0,
            frequency="qd", times=["09:00"],
        )
        events = calculate_milestones(rx, end_hours=24)
        hl_events = [e for e in events if e["event"] == "Half-life"]
        if len(hl_events) >= 2:
            levels = [e["level"] for e in hl_events]
            assert levels == sorted(levels, reverse=True)

    def test_ka_approx_ke_produces_peak(self):
        """When uptake ≈ half_life, milestone calculation should still produce a peak."""
        rx = Prescription(
            name="Test", dose=500, half_life=4.0, uptake=4.0, peak=4.0,
            frequency="qd", times=["09:00"],
        )
        events = calculate_milestones(rx, end_hours=48)
        peak_events = [e for e in events if e["event"] == "Peak"]
        assert len(peak_events) > 0

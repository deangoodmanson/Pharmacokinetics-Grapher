"""JSON serialization and file I/O for prescriptions."""

import json

from .models import Prescription


def prescription_to_dict(rx):
    """Convert Prescription to dict matching web app JSON format."""
    d = {
        "name": rx.name,
        "dose": rx.dose,
        "halfLife": rx.half_life,
        "uptake": rx.uptake,
        "peak": rx.peak,
        "frequency": rx.frequency,
        "times": rx.times,
    }
    if rx.metabolite_life is not None:
        d["metaboliteLife"] = rx.metabolite_life
    if rx.relative_metabolite_level is not None:
        d["relativeMetaboliteLevel"] = rx.relative_metabolite_level
    if rx.metabolite_name is not None:
        d["metaboliteName"] = rx.metabolite_name
    if rx.duration is not None:
        d["duration"] = rx.duration
    if rx.duration_unit is not None:
        d["durationUnit"] = rx.duration_unit
    return d


def prescription_from_dict(d):
    """Create Prescription from web app JSON format (handles legacy fields)."""
    rel_level = d.get("relativeMetaboliteLevel")
    if rel_level is None and "metaboliteConversionFraction" in d:
        rel_level = d["metaboliteConversionFraction"]

    met_life = d.get("metaboliteLife")
    met_name = d.get("metaboliteName")
    if met_life is None and isinstance(d.get("metaboliteHalfLife"), dict):
        met_life = d["metaboliteHalfLife"].get("halfLife")
        met_name = met_name or d["metaboliteHalfLife"].get("name")

    return Prescription(
        name=d["name"],
        dose=float(d["dose"]),
        half_life=float(d["halfLife"]),
        uptake=float(d["uptake"]),
        peak=float(d["peak"]),
        frequency=d.get("frequency", "qd"),
        times=d.get("times", ["09:00"]),
        metabolite_life=float(met_life) if met_life is not None else None,
        relative_metabolite_level=float(rel_level) if rel_level is not None else None,
        metabolite_name=met_name,
        duration=d.get("duration"),
        duration_unit=d.get("durationUnit"),
    )


def save_prescriptions(prescriptions, filepath):
    """Export prescriptions to JSON file."""
    data = [prescription_to_dict(rx) for rx in prescriptions]
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    return f"Saved {len(data)} prescription(s) to {filepath}"


def load_prescriptions(filepath):
    """Import prescriptions from JSON file."""
    with open(filepath) as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = [data]
    return [prescription_from_dict(d) for d in data]

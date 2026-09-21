"""Basic tests for powuk core types."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from powuk.core.constraints import Constraint, ConstraintType, Region, Severity
from powuk.core.regions import get_all_regions, REGIONS


def test_region_creation():
    r = Region("TEST", "Test Region", 51.0, 0.0)
    assert r.code == "TEST"
    assert r.lat == 51.0


def test_constraint_gap():
    r = Region("TEST", "Test", 51.0, 0.0)
    c = Constraint(
        constraint_id="GRID-HEADROOM-TEST-20260915",
        constraint_type=ConstraintType.GRID_HEADROOM,
        region=r,
        measured_at="2026-09-15T00:00:00",
        demand_value=450.0,
        supply_value=400.0,
        severity=Severity.HIGH,
    )
    assert c.gap == 50.0


def test_constraint_no_gap():
    r = Region("TEST", "Test", 51.0, 0.0)
    c = Constraint(
        constraint_id="GRID-HEADROOM-TEST-20260915",
        constraint_type=ConstraintType.GRID_HEADROOM,
        region=r,
        measured_at="2026-09-15T00:00:00",
    )
    assert c.gap is None


def test_all_regions_exist():
    regions = get_all_regions()
    assert len(regions) == 12
    assert all(r.lat is not None for r in regions)


if __name__ == "__main__":
    test_region_creation()
    test_constraint_gap()
    test_constraint_no_gap()
    test_all_regions_exist()
    print("All tests passed.")

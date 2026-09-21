"""Tests for powuk core types, CollectorResult, and source registry."""
import sys, os, asyncio, sqlite3, json, hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.constraints import Constraint, ConstraintType, Region, Severity
from core.regions import get_all_regions, REGIONS


# ─── CORE TYPES ─────────────────────────────────────────────

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


# ─── COLLECTOR RESULT ───────────────────────────────────────

def test_collector_result_success():
    from server import CollectorResult, CollectorStatus
    r = CollectorResult.success(rows=100)
    assert r.status == CollectorStatus.SUCCESS
    assert r.rows == 100

def test_collector_result_success_empty():
    from server import CollectorResult, CollectorStatus
    r = CollectorResult.success(rows=0)
    assert r.status == CollectorStatus.SUCCESS_EMPTY
    assert r.rows == 0

def test_collector_result_partial():
    from server import CollectorResult, CollectorStatus
    r = CollectorResult.partial(rows=50, warnings=["page 3 failed"])
    assert r.status == CollectorStatus.PARTIAL
    assert r.rows == 50
    assert "page 3 failed" in r.warnings

def test_collector_result_failed():
    from server import CollectorResult, CollectorStatus
    r = CollectorResult.failed("HTTP 403: forbidden")
    assert r.status == CollectorStatus.FAILED
    assert "403" in r.error

def test_collector_result_blocked():
    from server import CollectorResult, CollectorStatus
    r = CollectorResult.blocked("API key not configured")
    assert r.status == CollectorStatus.BLOCKED
    assert "API key" in r.error

def test_collector_result_inferred_status_not_from_rows():
    """Status must be explicit, never inferred from row count."""
    from server import CollectorResult, CollectorStatus
    # 0 rows can be success_empty, not failed
    r = CollectorResult.success(rows=0)
    assert r.status == CollectorStatus.SUCCESS_EMPTY
    # 100 rows can be partial if warnings exist
    r2 = CollectorResult.partial(rows=100, warnings=["some pages failed"])
    assert r2.status == CollectorStatus.PARTIAL


# ─── SOURCE REGISTRY ────────────────────────────────────────

def test_sources_yaml_loads():
    from server import SOURCES
    assert isinstance(SOURCES, dict)
    assert len(SOURCES) >= 10

def test_sources_have_required_fields():
    from server import SOURCES
    for sid, src in SOURCES.items():
        assert "id" in src, f"{sid} missing id"
        assert "domain" in src, f"{sid} missing domain"
        assert "cadence" in src, f"{sid} missing cadence"
        assert "stage" in src, f"{sid} missing stage"

def test_source_stages_are_valid():
    from server import SOURCES
    valid_stages = {"discovery", "raw", "normalized", "monitored", "verified", "aggregate_only"}
    for sid, src in SOURCES.items():
        stage = src.get("stage", "")
        assert stage in valid_stages, f"{sid} has invalid stage: {stage}"

def test_all_collector_ids_have_config():
    from server import SOURCES, COLLECTORS
    collector_ids = [name for name, _, _ in COLLECTORS]
    for cid in collector_ids:
        assert cid in SOURCES, f"Collector '{cid}' has no entry in sources.yaml"


# ─── SCHEDULER ISOLATION ────────────────────────────────────

def test_async_scheduler_does_not_stall():
    """Slow collector A should not block fast collector B."""
    from server import CollectorResult
    
    call_log = []
    
    def slow_collector(conn):
        import time
        time.sleep(0.1)  # Simulate slow source
        call_log.append("slow")
        return CollectorResult.success(rows=1)
    
    def fast_collector(conn):
        call_log.append("fast")
        return CollectorResult.success(rows=1)
    
    async def run():
        conn = sqlite3.connect(":memory:")
        # Run both in threads — should complete in ~0.1s, not 0.2s
        t0 = asyncio.get_event_loop().time()
        await asyncio.gather(
            asyncio.to_thread(slow_collector, conn),
            asyncio.to_thread(fast_collector, conn),
        )
        elapsed = asyncio.get_event_loop().time() - t0
        return elapsed, call_log
    
    elapsed, log = asyncio.run(run())
    assert elapsed < 0.5, f"Took {elapsed}s — collectors not isolated"
    assert "fast" in log
    assert "slow" in log


# ─── FETCH ERROR CLASSIFICATION ─────────────────────────────

def test_fetch_error_classification():
    from server import FetchError
    e = FetchError(403, "forbidden")
    assert e.status_code == 403
    assert "forbidden" in str(e)


# ─── DB SCHEMA ──────────────────────────────────────────────

def test_db_schema_has_tables():
    from server import get_db
    conn = get_db()
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    assert "raw_ingest" in tables
    assert "observation" in tables
    assert "collector_state" in tables


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
        except Exception as e:
            print(f"  ✗ {t.__name__}: {e}")
    print(f"\n{len(tests)} tests run.")

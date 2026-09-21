"""Tests for Layer 1 — manifest, health, collector interface."""
import sys, json, tempfile, sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from layer1.manifest import SourceManifest, load_all_manifests
from layer1.health import CollectorHealth, HealthRegistry
from layer1.collector import CollectorResult, CollectorStatus, store_raw, get_db


# ─── MANIFEST ────────────────────────────────────────────────

def test_manifest_loads():
    """All source manifests load without error."""
    manifests = load_all_manifests()
    assert len(manifests) >= 10
    for mid, m in manifests.items():
        assert m.id == mid
        assert m.garden == "powuk"
        assert m.authority.name
        assert m.collection.cadence
        assert m.health.max_staleness_hours > 0

def test_manifest_yaml_roundtrip():
    """Manifest survives YAML serialize/deserialize."""
    manifests = load_all_manifests()
    for mid, m in manifests.items():
        yaml_str = m.to_yaml()
        assert "id:" in yaml_str
        assert "cadence:" in yaml_str

def test_manifest_has_required_fields():
    """Every manifest has the required structure."""
    manifests = load_all_manifests()
    for mid, m in manifests.items():
        assert m.id, f"{mid}: missing id"
        assert m.authority.name, f"{mid}: missing authority.name"
        assert m.collection.cadence, f"{mid}: missing cadence"
        assert m.health.max_staleness_hours > 0, f"{mid}: invalid staleness"

def test_manifest_specific_sources():
    """Check specific source manifests exist."""
    manifests = load_all_manifests()
    expected = ["neso_demand", "neso_generation", "pvlive", "apar", "ons_labour", "refcom"]
    for eid in expected:
        assert eid in manifests, f"Missing manifest: {eid}"


# ─── HEALTH ──────────────────────────────────────────────────

def test_health_defaults():
    """Health state defaults to never_run."""
    h = CollectorHealth(source_id="test")
    assert h.status == "never_run"
    assert h.runs == 0
    assert h.health_label() == "NOT_RUN"

def test_health_ok():
    """Health state after successful run."""
    h = CollectorHealth(source_id="test", status="ok", last_success="2026-09-21T12:00:00+00:00")
    assert not h.is_stale(max_staleness_hours=48)
    assert "OK" in h.health_label()

def test_health_stale():
    """Health state when source is stale."""
    h = CollectorHealth(source_id="test", status="ok", last_success="2026-09-10T12:00:00+00:00")
    assert h.is_stale(max_staleness_hours=48)
    assert h.health_label() == "STALE"

def test_health_failed():
    """Health state on failure."""
    h = CollectorHealth(source_id="test", status="failed", error="HTTP 403")
    assert "FAILED" in h.health_label()

def test_health_registry():
    """Health registry tracks multiple sources."""
    reg = HealthRegistry()
    reg.record_success("neso_demand", records_new=100, bytes=5000)
    reg.record_failure("ch_capacity", error="API key missing")
    
    summary = reg.summary()
    assert "neso_demand" in summary
    assert "ch_capacity" in summary
    assert "OK" in summary["neso_demand"]
    assert "FAILED" in summary["ch_capacity"]

def test_health_json_roundtrip():
    """Health state survives JSON serialization."""
    reg = HealthRegistry()
    reg.record_success("test_source", records_new=50)
    
    json_str = reg.to_json()
    data = json.loads(json_str)
    assert "test_source" in data
    assert data["test_source"]["status"] == "ok"

def test_health_record_blocked():
    """Blocked status for missing API key."""
    reg = HealthRegistry()
    reg.record_blocked("ch_capacity", "COMPANIES_HOUSE_API_KEY not set")
    assert "FAILED:COMPANIES_HOUSE_API_KEY" in reg.summary()["ch_capacity"]


# ─── COLLECTOR ───────────────────────────────────────────────

def test_collector_result_types():
    """Collector result has correct status types."""
    r1 = CollectorResult(status=CollectorStatus.SUCCESS, rows=100)
    assert r1.status == "ok"
    
    r2 = CollectorResult(status=CollectorStatus.FAILED, error="timeout")
    assert r2.status == "failed"

def test_store_raw():
    """Raw storage writes content-hashed files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = get_db(str(db_path))
        
        result = store_raw(conn, "test_source", b'{"test": "data"}')
        assert result["hash"]
        assert result["bytes"] == 16
        assert Path(result["path"]).exists()
        
        conn.close()

def test_get_db_creates_schema():
    """Database schema is created on first access."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = get_db(str(db_path))
        
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        assert "raw_blob" in tables
        assert "raw_ingest" in tables
        assert "observation" in tables
        
        conn.close()


# ─── INTEGRATION ─────────────────────────────────────────────

def test_manifest_drives_collector():
    """Manifest config can drive collector behavior."""
    manifests = load_all_manifests()
    m = manifests["neso_demand"]
    
    assert m.collection.cadence == "hourly"
    assert m.storage.raw is True
    assert m.storage.append_only is True
    assert m.health.expected_min_rows == 100
    assert m.health.max_staleness_hours == 2

def test_all_sources_have_manifests():
    """Every collector in server.py has a manifest."""
    manifests = load_all_manifests()
    manifest_ids = set(manifests.keys())
    
    # These should all exist
    expected = {
        "neso_demand", "neso_generation", "pvlive", "evspark_trades",
        "planning_apps", "contracts_finder", "find_tender", "ch_capacity",
        "apar", "ofqual", "ons_labour", "refcom", "ashe_wages", "ukpn_flex",
    }
    missing = expected - manifest_ids
    assert not missing, f"Missing manifests: {missing}"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
        except Exception as e:
            print(f"  ✗ {t.__name__}: {e}")
    print(f"\n{len(tests)} tests run.")

"""Level 1 ingestion tests.

Proves: If collector says N normalized records, I can query N normalized records.
"""
import sys, json, tempfile, sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from layer1.collector import (
    store_raw, store_normalized, record_coverage, get_coverage, get_db
)


# ─── RAW STORE INVARIANTS ────────────────────────────────────

def test_raw_store_immutable():
    """Same content stored twice produces same hash and file path."""
    data = b'{"test": "data"}'
    r1 = store_raw("test_source", data)
    r2 = store_raw("test_source", data)
    
    # Same content = same hash
    assert r1["hash"] == r2["hash"]
    
    # Same hash = same file path (deduplication)
    assert r1["path"] == r2["path"]
    
    # File exists
    assert Path(r1["path"]).exists()

def test_raw_store_different_content():
    """Different content produces different hashes."""
    r1 = store_raw("test_source", b'content_a')
    r2 = store_raw("test_source", b'content_b')
    assert r1["hash"] != r2["hash"]


# ─── NORMALIZED STORE INVARIANTS ─────────────────────────────

def test_normalized_store_jsonl():
    """Normalized records persist to data/normalized/ as JSONL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        records = [{"id": 1, "name": "test"}, {"id": 2, "name": "test2"}]
        # Temporarily override the path
        import layer1.collector as lc
        old_norm = lc.NORM_DIR
        lc.NORM_DIR = Path(tmpdir) / "normalized"
        
        result = store_normalized("test_source", records)
        
        lc.NORM_DIR = old_norm
        
        assert result["records"] == 2
        assert Path(result["path"]).exists()
        
        # Read back and verify
        with open(result["path"]) as f:
            lines = f.readlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["id"] == 1


# ─── COVERAGE INVARIANTS ─────────────────────────────────────

def test_coverage_complete():
    """Coverage with 100% collection is marked complete."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = get_db(str(db_path))
        
        record_coverage(conn, "test_source", expected=100, collected=100)
        cov = get_coverage(conn, "test_source")
        
        assert len(cov) == 1
        assert cov[0]["coverage_ratio"] == 1.0
        assert cov[0]["complete"] in (True, 1)
        
        conn.close()

def test_coverage_partial():
    """Coverage with <99% collection is marked partial."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = get_db(str(db_path))
        
        record_coverage(conn, "test_source", expected=1000, collected=500)
        cov = get_coverage(conn, "test_source")
        
        assert len(cov) == 1
        assert cov[0]["coverage_ratio"] == 0.5
        assert cov[0]["complete"] in (False, 0)
        
        conn.close()

def test_coverage_overwrite():
    """Second coverage check overwrites first (latest wins)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = get_db(str(db_path))
        
        record_coverage(conn, "test_source", expected=100, collected=50)
        record_coverage(conn, "test_source", expected=100, collected=99)
        
        cov = get_coverage(conn, "test_source")
        assert len(cov) == 1
        assert cov[0]["collected_count"] == 99
        
        conn.close()


# ─── THE CRITICAL LEVEL 1 TEST ───────────────────────────────

def test_parsed_equals_persisted():
    """If we parsed N records, we persisted N records.
    
    This is THE Level 1 invariant.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Simulate: parse 1000 records, persist all
        records = [{"id": i, "value": f"record_{i}"} for i in range(1000)]
        
        import layer1.collector as lc
        old_norm = lc.NORM_DIR
        lc.NORM_DIR = Path(tmpdir) / "normalized"
        
        result = store_normalized("test_source", records)
        
        lc.NORM_DIR = old_norm
        
        # Count persisted records
        with open(result["path"]) as f:
            persisted = sum(1 for _ in f)
        
        assert persisted == 1000, f"Expected 1000 persisted, got {persisted}"
        assert result["records"] == 1000

def test_no_sampling_in_production():
    """Production collectors must not use [:N] slicing on normalized data.
    
    Sampling belongs only in tests/fixtures/debug.
    """
    server_path = Path(__file__).parent.parent / "server.py"
    content = server_path.read_text()
    
    # Check that store() is not called with sliced data for normalized output
    # Pattern: store(conn, ..., json.dumps(records[:...]))
    import re
    bad_patterns = re.findall(r'store\(conn.*json\.dumps\(records\[:\d+\]\)', content)
    assert len(bad_patterns) == 0, f"Found sampling in store() calls: {bad_patterns}"


# ─── SCHEMA DRIFT DETECTION ──────────────────────────────────

def test_normalized_records_preserve_all_fields():
    """Normalized records preserve all source fields."""
    records = [
        {"ukprn": "12345", "name": "Test Provider", "status": "Active", "extra_field": "value"},
        {"ukprn": "67890", "name": "Test Provider 2", "status": "Inactive"},
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        import layer1.collector as lc
        old_norm = lc.NORM_DIR
        lc.NORM_DIR = Path(tmpdir) / "normalized"
        
        result = store_normalized("test_source", records)
        
        lc.NORM_DIR = old_norm
        
        with open(result["path"]) as f:
            persisted = [json.loads(line) for line in f]
        
        # First record should have extra_field
        assert persisted[0].get("extra_field") == "value"
        # Second record should have all fields even without extra_field
        assert persisted[1]["name"] == "Test Provider 2"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
        except Exception as e:
            print(f"  ✗ {t.__name__}: {e}")
    print(f"\n{len(tests)} tests run.")

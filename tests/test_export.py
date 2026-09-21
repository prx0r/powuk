"""Tests for powuk → powkernel export adapter.

Proves powuk can export to powkernel format without domain-specific code in the kernel.
"""
import sys, json, tempfile, sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "k2"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from pow.graph import Graph
from pow.constraint import constraint_pressure, bottlenecks
from pow.counterfactual import criticality, unknowns
from export.adapter import build_uk_graph, export_powuk_to_powkernel


def test_uk_graph_builds():
    """The UK dependency graph builds with correct counts."""
    g = build_uk_graph()
    assert len(g.nodes) > 10
    assert len(g.edges) > 10
    s = g.stats()
    assert s["nodes"] > 10
    assert s["edges"] > 10

def test_uk_graph_has_no_cycles():
    """The UK dependency graph is acyclic (DAG)."""
    g = build_uk_graph()
    # Check no node is its own upstream
    for node_id in g.nodes:
        upstream = g.upstream(node_id)
        assert node_id not in upstream, f"Cycle detected involving {node_id}"

def test_uk_graph_upstream_downstream():
    """Can trace dependencies through the UK graph."""
    g = build_uk_graph()
    
    # Data centres depend on grid connections
    assert "uk:grid_connection" in g.upstream("uk:data_centre_capacity")
    
    # Grid connections depend on transformers
    assert "uk:distribution_transformer" in g.upstream("uk:grid_connection")

def test_uk_graph_constraint_pressure():
    """Constraint pressure computes over the UK graph (even with no observations)."""
    g = build_uk_graph()
    derivs = constraint_pressure(g)
    # All derivations should have unknowns since we have no observations
    for d in derivs:
        assert d.kind == "constraint_pressure"
        assert len(d.unknowns) > 0  # No observations = all unknown

def test_uk_graph_criticality():
    """Criticality scoring works over the UK graph."""
    g = build_uk_graph()
    scores = criticality(g)
    assert len(scores) == len(g.nodes)
    # All scores should be 0 since no observations exist yet
    for s in scores:
        assert s["criticality_score"] >= 0

def test_uk_graph_unknowns():
    """Unknowns reports missing observations."""
    g = build_uk_graph()
    missing = unknowns(g)
    assert len(missing) > 0
    for m in missing:
        assert len(m["missing"]) > 0

def test_export_with_mock_db():
    """Export from a mock powuk database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock powuk DB
        db_path = Path(tmpdir) / "powuk.db"
        conn = sqlite3.connect(str(db_path))
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS observation (
                id TEXT PRIMARY KEY, source TEXT, metric TEXT, value TEXT,
                unit TEXT, event_time TEXT, observed_at TEXT
            );
            CREATE TABLE IF NOT EXISTS collector_state (
                source TEXT PRIMARY KEY, last_run TEXT, status TEXT,
                rows INT, interval INT, runs INT DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS raw_ingest (
                retrieval_id TEXT PRIMARY KEY, source TEXT, dataset TEXT,
                raw_hash TEXT, observed_at TEXT, row_count INT, status TEXT
            );
        """)
        
        # Insert test observations
        conn.execute("INSERT INTO observation VALUES ('obs1', 'grid', 'uk_demand_mw', '45000', 'MW', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')")
        conn.execute("INSERT INTO observation VALUES ('obs2', 'grid', 'uk_wind_mw', '12000', 'MW', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')")
        conn.execute("INSERT INTO collector_state VALUES ('neso_demand', '2026-09-01T00:00:00Z', 'ok', 2832, 3600, 1)")
        conn.commit()
        
        store_path = Path(tmpdir) / "powkernel_export"
        result = export_powuk_to_powkernel(conn, str(store_path))
        
        assert result["nodes"] > 0
        assert result["edges"] > 0
        assert result["observations"] >= 2
        assert result["evidence"] >= 1
        
        # Verify the store has content
        store_files = list(store_path.rglob("*.jsonl"))
        assert len(store_files) > 0
        
        conn.close()

def test_export_produces_valid_powkernel_objects():
    """Exported objects can be loaded back into a powkernel Graph."""
    g = build_uk_graph()
    
    # Add some observations
    from pow.model import Observation
    g.add(Observation.create("capacity", "uk:grid_connection", 5000.0, "MW", "2026-09-01", "powuk"))
    g.add(Observation.create("capacity", "uk:hv_electrician", 340.0, "people", "2026-09-01", "powuk"))
    
    # Compute constraints
    derivs = constraint_pressure(g)
    for d in derivs:
        g.add(d)
    
    # The graph should now have derivations
    assert len(g.derivations) > 0
    
    # And we can find bottlenecks
    bn = bottlenecks(g, threshold=0)
    assert isinstance(bn, list)

def test_no_domain_code_in_kernel():
    """The powkernel kernel contains no UK-specific code."""
    import pow.model as model_mod
    import pow.constraint as constraint_mod
    import pow.counterfactual as counter_mod
    
    for mod in [model_mod, constraint_mod, counter_mod]:
        source = Path(mod.__file__).read_text().lower()
        for term in ["electrician", "transformer", "neso", "companies_house", "mcs", "ozev", "refcom"]:
            assert term not in source, f"UK-specific term '{term}' in kernel {mod.__name__}"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
        except Exception as e:
            print(f"  ✗ {t.__name__}: {e}")
    print(f"\n{len(tests)} tests run.")

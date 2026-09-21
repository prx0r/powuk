"""POWUK → POWKernel export adapter.

This is the ONLY place powuk touches powkernel.

Powuk stays domain-specific internally.
This adapter converts to the interchange format.
"""
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# Import powkernel
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "k2"))
from pow.canonical import make_id
from pow.model import Node, Edge, Observation, Evidence, Derivation
from pow.graph import Graph
from pow.store import Store


# ─── UK DEPENDENCY GRAPH ─────────────────────────────────────

# The REQUIRES relationships that define UK physical constraints.
# This is the domain knowledge that powuk encodes.

UK_EDGES = [
    # Grid chain
    ("uk:data_centre_capacity", "uk:grid_connection", "Data centres require grid connections"),
    ("uk:grid_connection", "uk:distribution_transformer", "Grid connections require transformers"),
    ("uk:distribution_transformer", "uk:electrical_steel", "Transformers require electrical steel"),
    ("uk:grid_connection", "uk:hv_electrician", "Grid work requires HV electricians"),
    
    # Trade chain
    ("uk:ev_charger_demand", "uk:electrician_capacity", "EV charger installation requires electricians"),
    ("uk:heat_pump_demand", "uk:hvac_engineer_capacity", "Heat pump installation requires HVAC engineers"),
    ("uk:solar_demand", "uk:solar_installer_capacity", "Solar installation requires MCS installers"),
    ("uk:retrofit_demand", "uk:retrofit_coordinator_capacity", "Retrofit requires coordinators"),
    
    # Training pipeline
    ("uk:apprenticeship_start", "uk:qualified_electrician", "Apprenticeships produce qualified electricians"),
    ("uk:apprenticeship_start", "uk:qualified_hvac", "Apprenticeships produce qualified HVAC engineers"),
    
    # Certification dependencies
    ("uk:ev_charger_install", "uk:okev_certification", "EV charger install requires OZEV certification"),
    ("uk:heat_pump_install", "uk:mcs_certification", "Heat pump install requires MCS certification"),
    ("uk:f_gas_work", "uk:refcom_certification", "F-gas work requires REFCOM certification"),
]

UK_NODES = [
    ("uk:data_centre_capacity", "capacity", "UK data centre capacity"),
    ("uk:grid_connection", "capacity", "Grid connection capacity"),
    ("uk:distribution_transformer", "equipment", "Distribution transformer supply"),
    ("uk:electrical_steel", "resource", "Electrical steel supply"),
    ("uk:hv_electrician", "capability", "HV qualified electricians"),
    ("uk:ev_charger_demand", "demand", "EV charger installation demand"),
    ("uk:electrician_capacity", "capability", "Qualified electricians"),
    ("uk:heat_pump_demand", "demand", "Heat pump installation demand"),
    ("uk:hvac_engineer_capacity", "capability", "Qualified HVAC engineers"),
    ("uk:solar_demand", "demand", "Solar panel installation demand"),
    ("uk:solar_installer_capacity", "capability", "MCS solar installers"),
    ("uk:retrofit_demand", "demand", "Retrofit/insulation demand"),
    ("uk:retrofit_coordinator_capacity", "capability", "Retrofit coordinators"),
    ("uk:apprenticeship_start", "capacity", "Apprenticeship starts per year"),
    ("uk:qualified_electrician", "capacity", "Newly qualified electricians per year"),
    ("uk:qualified_hvac", "capacity", "Newly qualified HVAC engineers per year"),
    ("uk:ev_charger_install", "capability", "EV charger installation"),
    ("uk:okev_certification", "capability", "OZEV authorised installer"),
    ("uk:heat_pump_install", "capability", "Heat pump installation"),
    ("uk:mcs_certification", "capability", "MCS certified installer"),
    ("uk:f_gas_work", "capability", "F-gas handling work"),
    ("uk:refcom_certification", "capability", "REFCOM F-gas certified"),
]


def build_uk_graph() -> Graph:
    """Build the UK dependency graph as powkernel objects."""
    g = Graph()
    
    for node_id, kind, label in UK_NODES:
        g.add(Node(id=node_id, kind=kind, label=label))
    
    for source, target, _label in UK_EDGES:
        g.add(Edge.create(source, target))
    
    return g


# ─── ADAPTER: powuk observation → powkernel observation ──────

def observation_to_powkernel(obs_row: dict) -> Observation:
    """Convert a powuk SQLite observation row to a powkernel Observation.
    
    obs_row keys: id, source, metric, value, unit, event_time, observed_at
    """
    return Observation(
        id=f"obs:{obs_row['id'][:16]}",
        metric=obs_row["metric"],
        subject=f"uk:{obs_row['source']}:{obs_row['metric']}",
        value=float(obs_row["value"]) if obs_row["value"] else None,
        unit=obs_row.get("unit"),
        as_of=obs_row.get("event_time") or obs_row.get("observed_at", ""),
        source=obs_row.get("source", "powuk"),
    )


def constraint_to_derivation(constraint_row: dict) -> Derivation:
    """Convert a powuk constraint to a powkernel Derivation."""
    return Derivation.create(
        kind=f"constraint_{constraint_row.get('type', 'unknown')}",
        subject=f"uk:{constraint_row.get('region', 'unknown')}",
        value=constraint_row.get("severity"),
        as_of=constraint_row.get("measured_at", ""),
        model="powuk_constraint_pressure/v1",
        inputs=[f"obs:{constraint_row.get('source', 'unknown')}"],
        unknowns=constraint_row.get("unknowns", []),
    )


def provider_to_node(provider: dict) -> Node:
    """Convert a powuk capability_provider to a powkernel Node."""
    return Node(
        id=f"uk:provider:{provider.get('provider_id', 'unknown')}",
        kind="capability",
        label=provider.get("name", "Unknown provider"),
    )


def capability_to_observation(cap: dict, provider: dict) -> Observation:
    """Convert a powuk provider_capability to a powkernel Observation."""
    return Observation.create(
        metric=f"certification:{cap.get('certification_scheme', 'unknown')}",
        subject=f"uk:provider:{cap.get('provider_id', 'unknown')}",
        value=1.0 if cap.get("status") == "active" else 0.0,
        unit="active",
        as_of=cap.get("observed_at", ""),
        source="powuk",
    )


# ─── FULL EXPORT ─────────────────────────────────────────────

def export_powuk_to_powkernel(conn, store_path: str = None) -> dict:
    """Export all powuk data to powkernel format.
    
    Args:
        conn: SQLite connection to powuk.db
        store_path: optional path for JSONL store
    
    Returns:
        Summary of exported objects
    """
    store = Store(store_path) if store_path else None
    g = build_uk_graph()
    
    exported = {"nodes": 0, "edges": 0, "observations": 0, "evidence": 0, "derivations": 0}
    
    # 1. Export the UK dependency graph
    for node in g.nodes.values():
        if store:
            store.append(node)
        exported["nodes"] += 1
    
    for edge in g.edges.values():
        if store:
            store.append(edge)
        exported["edges"] += 1
    
    # 2. Export observations from powuk DB
    try:
        rows = conn.execute(
            "SELECT id, source, metric, value, unit, event_time, observed_at FROM observation ORDER BY observed_at DESC LIMIT 10000"
        ).fetchall()
        
        for row in rows:
            obs_dict = {
                "id": row[0], "source": row[1], "metric": row[2],
                "value": row[3], "unit": row[4], "event_time": row[5], "observed_at": row[6]
            }
            pk_obs = observation_to_powkernel(obs_dict)
            if store:
                store.append(pk_obs)
            exported["observations"] += 1
    except Exception:
        pass
    
    # 3. Export collector state as evidence
    try:
        rows = conn.execute(
            "SELECT source, status, rows, runs, last_run FROM collector_state"
        ).fetchall()
        
        for row in rows:
            ev = Evidence.create(
                claim=f"Collector {row[0]} ran {row[3]} times, last status: {row[1]}",
                target=f"uk:collector:{row[0]}",
                direction="SUPPORTS",
                publisher="powuk",
                observed_at=row[4] or "",
            )
            if store:
                store.append(ev)
            exported["evidence"] += 1
    except Exception:
        pass
    
    # 4. Export capability providers as nodes + observations
    try:
        providers = conn.execute(
            "SELECT provider_id, name, region, source FROM capability_provider LIMIT 5000"
        ).fetchall()
        
        for p in providers:
            p_dict = {"provider_id": p[0], "name": p[1], "region": p[2]}
            node = provider_to_node(p_dict)
            if store:
                store.append(node)
            exported["nodes"] += 1
            
            caps = conn.execute(
                "SELECT certification_scheme, status, observed_at FROM provider_capability WHERE provider_id=?",
                (p[0],)
            ).fetchall()
            
            for cap in caps:
                cap_dict = {
                    "provider_id": p[0],
                    "certification_scheme": cap[0],
                    "status": cap[1],
                    "observed_at": cap[2],
                }
                obs = capability_to_observation(cap_dict, p_dict)
                if store:
                    store.append(obs)
                exported["observations"] += 1
    except Exception:
        pass
    
    return exported

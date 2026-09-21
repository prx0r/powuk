# REPO_MAP.md — powuk Handover

> UK Physical Constraint Graph. Where is physical demand appearing faster than physical capacity?
> Last updated: 2026-09-21

---

## Directory Structure

```
powuk/
├── server.py                  # MAIN — 16 async collectors, CLI entry point
├── config/sources.yaml        # SINGLE SOURCE OF TRUTH — all source config
├── data/powuk.db              # SQLite — observations, raw blobs, collector state, coverage
├── data/raw/                  # Immutable raw evidence (content-hashed)
├── data/normalized/           # Parsed JSONL records (append-only)
├── data/derived/              # Server logs, cached outputs
│
├── core/                      # CANONICAL TYPES (active)
│   ├── constraints.py         # ConstraintType, Severity, Region, Constraint, TradeProfile, Opportunity
│   ├── regions.py             # 12 UK GSP/DNO regions with lat/lon
│   └── capability_provider.py # STALE — Level 2 entity module, not imported anywhere
│
├── layer1/                    # LAYER 1 — Observatory
│   ├── collector.py           # CollectorResult, CollectorStatus, store_raw, store_normalized, record_coverage
│   ├── manifest.py            # SourceManifest YAML schema
│   ├── health.py              # CollectorHealth, HealthRegistry
│   └── sources/*.yaml         # 16 source manifests (one per collector)
│
├── layer2/                    # LAYER 2 — Constraint Model (hollow)
│   ├── __init__.py            # Imports core types
│   └── scarcity.py            # STALE — re-exports from compiler/scarcity.py, never imported
│
├── compiler/                  # SCARCITY COMPILER (active)
│   └── scarcity.py            # compute_severity, compile_grid_constraint, compile_scarsity_view
│
├── export/                    # POWKERNEL EXPORT (active)
│   └── adapter.py             # powuk → powkernel format (depends on /root/k2/)
│
├── collectors/                # PLACEHOLDER — empty, all collectors in server.py
│
├── models/                    # STALE — 9 Level 3 analytical models, none wired in
│   ├── diffusion.py           # Richards curve S-curve fitting
│   ├── hazard.py              # Weibull hazard + cohort convolution
│   ├── lagscan.py             # Cross-correlation + Granger causality
│   ├── network.py             # Leontief inverse (input-output)
│   ├── reconstruct.py         # Gradient boosting link reconstruction
│   ├── scenario.py            # Technology-shock scenario engine
│   ├── shadow.py              # LP shadow prices via scipy linprog
│   ├── skills.py              # Skill bottleneck + mobility matrix
│   └── synergy.py             # Complementarity screening (interaction uplift)
│
├── sdk/                       # STALE — Full Companies House SDK (not used by server.py)
│   └── companies_house.py     # REST, Document, Streaming APIs + trade filters
│
├── schemas/                   # DESIGN DOCS — JSON schemas, taxonomies, contracts
│   ├── contracts.py           # STALE — canonical dataclasses, never imported
│   ├── *.schema.json          # JSON Schema definitions
│   ├── *.yaml                 # Taxonomies and source definitions
│   ├── *.sql                  # Shared SQL schemas
│   ├── *.md                   # Design documents
│   └── systems/               # pow-frontier system specs (separate system)
│
├── tests/                     # TEST SUITE — 42 tests
│   ├── test_core.py           # Core types, CollectorResult, source registry, DB schema
│   ├── test_export.py         # powkernel export, UK graph, DAG check
│   ├── test_layer1.py         # Manifest, health, collector interface, raw storage
│   └── test_ingestion.py      # Level 1 invariants: raw store, normalized, coverage
│
├── *.md                       # Documentation
│   ├── AGENTS.md              # Operations manual (authoritative)
│   ├── README.md              # Project overview
│   ├── THESIS.md              # Core question
│   ├── DEVPLAN.md             # Architecture vision
│   ├── COMPANIES_HOUSE_REF.md # CH API reference
│   ├── COMPANIES_HOUSE_SPEC.md# CH collector spec
│   ├── ZIP_REGISTRY.md        # Email zip extraction log
│   ├── cool.md                # Visionary ideas
│   ├── review[2-6].md         # HISTORICAL checkpoint reviews
│   └── REPO_MAP.md            # THIS FILE
│
└── .env                       # LIVE API KEYS (Companies House) — do not commit
```

---

## What Works (Level 1)

| Collector | Status | Rows | Notes |
|-----------|--------|------|-------|
| neso_demand | Working | 2,832 | UK electricity demand, hourly |
| neso_generation | Working | 310,691 | Generation mix, hourly |
| pvlive | Working | 1 | Solar output snapshot |
| evspark_trades | Working | 55,925 | Electrical businesses (legacy local file) |
| planning_apps | Working | 5,000 | Planning applications, paginated |
| contracts_finder | Working | 1,000 | Public procurement, paginated |
| find_tender | Working | 50+ | Higher-value procurement, paginated |
| apar | Working | 1,432 | Training providers |
| ofqual | Working | 10,000 | UK qualifications |
| ons_labour | Working | 175,181 | Labour demand by SOC |
| ashe_wages | Working | 3,906 | Wage data by region × SOC |
| ons_skills | Working | ~varies | Skills from job adverts |
| ons_salaries | Working | ~varies | Salaries from job adverts |
| refcom | Working | 11,295 | F-gas certified companies |
| ch_capacity | Working | 7 clusters | Companies House SIC search |
| ukpn_flex | Stub | 1 | Catalogue metadata only |

---

## What's Broken / Stubbed

| Issue | Where | Fix Needed |
|-------|-------|------------|
| evspark uses legacy local path | server.py:349 | Replace with proper API source |
| CH SIC search may return wrong counts | server.py:479-528 | Verify API behavior |
| REFCOM entity enumeration unreliable | server.py:690-713 | Error handling breaks early |
| Ofqual active count returns 0 | sources.yaml:190 | Status field filter investigation |
| No tests for models/ | models/*.py | Add tests when Level 3 is activated |
| SDK not used by collector | sdk/companies_house.py | Refactor CH collector to use SDK |

---

## Architecture Levels

```
LEVEL 0 — Source Discovery (DONE for all 16 sources)
LEVEL 1 — Physical Observatory (CURRENT)
  Raw acquisition, historical backfill, continuous snapshots
  Source-faithful normalization, provenance, coverage
  "Don't ask what the data means yet. Make sure we own the data correctly."
LEVEL 2 — Entity Resolution (NOT STARTED)
  Canonical entity resolution, geography harmonisation
  Occupation/SIC/capability mappings, cross-source joins
  core/capability_provider.py is a building block for this level.
LEVEL 3 — Constraint Economics (NOT STARTED)
  Scarcity, shadow prices, entry/exit, Seesaw, lag models
  models/*.py are the analytical tools for this level.
```

---

## Key Invariants

1. **If collector says N normalized records, I can query N normalized records.**
2. **Raw means bytes retrieved from source, period. Nothing derived enters data/raw/.**
3. **config/sources.yaml is the single source of truth.**
4. **Every collector returns explicit CollectorResult status, never inferred from row count.**
5. **Each collector runs in its own thread via asyncio.to_thread. One slow source never blocks others.**

---

## How to Run

```bash
cd /root/powuk

# Run once (test)
python3 server.py once

# Run forever (daemon)
nohup python3 -u server.py > data/derived/server.log 2>&1 &

# Check status
python3 server.py status

# Run tests
python3 tests/test_core.py
python3 tests/test_layer1.py
python3 tests/test_export.py
python3 tests/test_ingestion.py
```

---

## Dependencies

- Python 3.10+
- sqlite3 (stdlib)
- openpyxl (XLSX parsing)
- pyyaml (sources.yaml loading)
- scipy, numpy, sklearn (models/ — Level 3 only)
- External: /root/k2/pow/ (powkernel — for export/adapter.py only)

---

## Open Threads for Next Sprint

1. **Refactor server.py monolith** → move collectors to `collectors/{domain}/{source}.py`
2. **Wire SDK** → refactor CH collector to use `sdk/companies_house.py`
3. **Add ASHE historical releases** → backfill 2021-2024 editions
4. **Test coverage** → add tests for models/ when activating Level 3
5. **Schema drift detection** → quarantine when source columns change
6. **Incremental fetch** → verify planning/contracts watermarks work with real APIs
7. **Parquet normalization** → migrate from JSONL to typed Parquet datasets
8. **REFCOM entity resolution** → debug GetByIndex or find alternative

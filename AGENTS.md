# AGENTS.md — powuk operations

> UK physical constraint graph. Where is physical demand appearing faster than physical capacity?

---

## What this is

powuk is a **POW** (Physical Operating Workspace) for the UK.

It has two clean layers:

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 2 — UK Constraint Model                          │
│                                                         │
│  Takes Layer 1 observations and computes:                │
│  - What is constrained?                                 │
│  - How strongly?                                        │
│  - Where are the bottlenecks?                           │
│  - What happens if something changes?                   │
│                                                         │
│  layer2/compiler/scarcity.py  — severity scoring        │
│  layer2/core/constraints.py   — UK constraint types     │
│  layer2/core/regions.py       — GSP/DNO regions         │
│  layer2/models/               — analytical models       │
├─────────────────────────────────────────────────────────┤
│  LAYER 1 — UK Physical Observatory                      │
│                                                         │
│  Continuously preserve the observable state of UK       │
│  physical economic capacity and demand.                 │
│                                                         │
│  layer1/sources/*.yaml  — one manifest per source       │
│  layer1/manifest.py     — source manifest schema        │
│  layer1/health.py       — collector health state        │
│  layer1/collector.py    — base collector interface      │
│  server.py              — collector runner              │
│  data/raw/              — immutable raw evidence        │
├─────────────────────────────────────────────────────────┤
│  EXPORT — POWKernel interchange                         │
│                                                         │
│  export/adapter.py — converts powuk → powkernel format  │
│  (NODE, EDGE, OBSERVATION, EVIDENCE, DERIVATION)       │
└─────────────────────────────────────────────────────────┘
```

### Layer 1: The Observatory

**Mission:** Continuously preserve the observable state of UK physical economic capacity and demand.

No need to decide what constitutes a binding constraint. Just observe.

Every source has:
- A manifest (`layer1/sources/*.yaml`) — the contract
- A health state (last_attempt, last_success, records, staleness)
- Immutable raw storage (content-hashed, append-only)

### Layer 2: The Constraint Model

**Mission:** Given Layer 1 observations, compute what is constrained, why, and how strongly.

Consumes observations. Produces derivations. Never overwrites evidence.

### Export: POWKernel

**Mission:** Convert powuk data to the generic interchange format.

The ONLY place powuk touches powkernel. All other code is UK-specific.

---

## Level Definitions

```text
LEVEL 0 — Source Discovery
  API exploration, documentation, fixtures
  Status: done for all 14 sources

LEVEL 1 — Physical Observatory (CURRENT)
  Raw acquisition, historical backfill, continuous snapshots
  Source-faithful normalization, provenance, coverage
  Monitoring, schema-drift detection
  "Don't ask what the data means yet. Make sure we own the data correctly."

LEVEL 2 — Entity Resolution
  Canonical entity resolution, geography harmonisation
  Occupation/SIC/capability mappings, cross-source joins
  Consistent time series

LEVEL 3 — Constraint Economics
  Scarcity, shadow prices, entry/exit
  Seesaw, lag models, AGI impact, opportunities
```

### Level 1 Invariant

```text
If collector says N normalized records,
I can query N normalized records.
Not "we parsed N in RAM once."
```

### Level 1 Source Coverage

Every bounded source tracks:

```text
expected_count | collected_count | coverage_ratio | complete
```

If coverage < 0.99, source is PARTIAL, never VERIFIED.

---

## How to operate

### Start the server
```bash
cd /root/powuk
nohup python3 -u server.py > data/derived/server.log 2>&1 &
```

### Check status
```bash
pgrep -f "powuk.*server" && echo "Running"
python3 server.py status
```

### Run once (test)
```bash
python3 server.py once
```

### View logs
```bash
tail -f data/derived/server.log
```

### Run tests
```bash
python3 tests/test_core.py       # core types + collector tests
python3 tests/test_export.py     # powkernel export tests
python3 tests/test_layer1.py     # manifest + health + collector interface
```

### Query the database
```python
import sqlite3
conn = sqlite3.connect('data/powuk.db')
conn.execute('SELECT source, metric, value FROM observation ORDER BY observed_at DESC LIMIT 10')
```

---

## Architecture

### CollectorResult (status semantics)

Every collector returns a `CollectorResult` with explicit status:

```python
CollectorStatus.SUCCESS       # data collected, rows > 0
CollectorStatus.SUCCESS_EMPTY # source responded, no data (legitimate)
CollectorStatus.PARTIAL       # some pages/records succeeded, some failed
CollectorStatus.FAILED        # exception or non-retryable HTTP error
CollectorStatus.BLOCKED       # missing API key or config, no retry possible
```

**Never infer status from row count.** Zero rows can be `SUCCESS_EMPTY`.

### Implementation stages (from sources.yaml)

```
discovery  → endpoint identified, may not work yet
raw        → raw data collected, not normalized
normalized → parsed into queryable records
monitored  → health/staleness checks passing
verified   → tests prove traceability, re-runnability, completeness
```

### Async isolation

Each collector runs in its own thread via `asyncio.to_thread`. One slow/broken
source never blocks others. This is a hard requirement.

### Source registry

`config/sources.yaml` is the **single source of truth**. All collector config
(cadence, URLs, auth, stage) lives there. Generate docs from it, never hand-edit.

---

## Collectors (14 active)

| Collector | Interval | Stage | What it measures |
|-----------|----------|-------|-----------------|
| neso_demand | hourly | normalized | UK electricity demand |
| neso_generation | hourly | normalized | Generation mix (wind/solar/gas) |
| pvlive | hourly | raw | Actual solar output |
| ukpn_flex | 12h | discovery | DNO flexibility catalog (not actual data yet) |
| evspark_trades | daily | raw | Electrical businesses by area (legacy local file) |
| planning_apps | 2h | raw | Where development is happening |
| contracts_finder | 2h | raw | Public procurement |
| find_tender | 2h | raw | Higher-value procurement |
| ch_capacity | 12h | discovery | Companies House SIC search (broken, returns 1) |
| apar | daily | normalized | Training providers (1,432) |
| ofqual | daily | raw | UK qualifications (10,000) |
| ons_labour | daily | raw | ONS labour data (175K rows) |
| refcom | daily | aggregate_only | F-gas certified companies (11,295 count, no entities) |
| ashe_wages | daily | normalized | ASHE wage data (3,906 records) |

### Adding a collector

1. Add entry to `config/sources.yaml` with stage
2. Add collector function in `server.py` returning `CollectorResult`
3. Add test in `tests/test_core.py`

---

## Data sources

| Source | Auth | Stage |
|--------|------|-------|
| NESO Open Data | none | normalized |
| PV Live API | none | raw |
| Planning Data API | none | raw |
| Contracts Finder | none | raw |
| Find a Tender | none | raw |
| Companies House REST | API key | discovery (SIC search broken) |
| Ofqual Register | none | raw |
| REFCOM API | none | aggregate_only (entity fetch fails) |
| ONS Labour | none | raw |
| APAR | none | normalized |
| ASHE Wages | none | normalized |

### API Keys
- Companies House REST: `COMPANIES_HOUSE_API_KEY` env var
- Companies House Streaming: `COMPANIES_HOUSE_STREAM_KEY` env var

---

## Key files

| File | Purpose |
|------|---------|
| server.py | Main collector server with CollectorResult |
| config/sources.yaml | Source registry (single source of truth) |
| THESIS.md | The one question we answer |
| DEVPLAN.md | Architecture vision |
| DATA_SOURCES.md | Generated from sources.yaml |
| COMPANIES_HOUSE_REF.md | Full CH API reference |
| COMPANIES_HOUSE_SPEC.md | Narrow CH collector spec |
| sdk/companies_house.py | Python SDK for CH API |
| core/constraints.py | Canonical constraint types |
| core/regions.py | UK GSP/DNO regions |
| compiler/scarcity.py | Demand/supply → severity scoring |

---

## Git

```bash
cd /root/powuk
git add -A
git commit -m "description"
git push
```

Remote: `https://github.com/prx0r/powuk`

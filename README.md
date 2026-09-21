# powuk — UK Physical Constraint Graph

> Where is physical demand appearing faster than physical capacity can respond?

## The Question

```
demand for EV charger installation
vs
qualified EV charger installers in the area
= CONSTRAINT (opportunity exists)
```

## Core Primitive

```
thing → failure → part → intervention → outcome
demand → supply → gap → constraint → opportunity
```

## Constraints We Track

| Type | Source | What it measures |
|------|--------|-----------------|
| `grid_headroom` | National Grid ESO | GSP demand vs capacity |
| `grid_queue` | GSO/DNO | Connection queue length |
| `trade_capacity` | Checkatrade/MCS/ONS | Installers per region vs job demand |
| `parts_availability` | eBay/Jawa/Keepa | Component availability for repair |
| `planning_backlog` | Local authorities | Planning application timelines |
| `infrastructure` | DNO/NGESO | Cable, transformer, substation constraints |

## Architecture

```
collectors/          raw data ingestion
  grid.py            GSP demand, connection queues, flexibility
  trades.py          Checkatrade, MCS, ONS, job postings
  ev_solar_heatpump.py  OZEV, MCS, DNO embedded generation

compiler/            raw → derived constraint state
  scarcity.py        demand vs supply → severity → opportunities

core/                canonical types
  constraints.py     Constraint, Region, TradeProfile, Opportunity
  regions.py         UK GSP/DNO regions

schemas/             JSON Schema validation
data/raw/            append-only raw evidence
data/derived/        compiled scarcity views
tests/               tests
```

## Data Flow

```
Raw Sources → Collectors → Raw Store → Compiler → Scarcity View → Opportunities
                                                                     ↓
                                                              Seesaw reads
                                                              Action taken
                                                              Outcomes verified
```

## Regions

12 GSP-level regions mapped to DNOs:
- UK Power Networks (London, East, South East)
- Western Power Distribution (South West, West Midlands, East Midlands)
- Electricity North West (North West, North East)
- SP Energy Networks (Central Scotland, North Scotland)
- NIE Networks (Northern Ireland)

## Scoring

Each constraint gets a severity:
- 0 = NONE (demand ≤ supply)
- 1 = LOW (demand 1-1.5x supply)
- 2 = MEDIUM (demand 1.5-2x supply)
- 3 = HIGH (demand 2-3x supply)
- 4 = CRITICAL (demand > 3x supply or supply = 0)

Composite regional scarcity = max severity across all constraints in that region.

## Usage

```python
from powuk.core.regions import get_all_regions
from powuk.compiler.scarcity import compile_grid_constraint

regions = get_all_regions()
constraint = compile_grid_constraint(
    region=regions[0],
    demand_mw=450,
    capacity_mw=500,
    queue_count=23,
)
# severity = HIGH (queue backlog)
```

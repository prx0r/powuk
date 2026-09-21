# powuk thesis

> **Where is physical demand appearing faster than physical capacity can respond?**

That's the only question. Every collector, every table, every model must answer it.

## The primitive

```
demand_signal → supply_signal → gap → constraint → opportunity
```

If we can't measure both sides of the gap for a specific thing in a specific place, we don't collect it.

## The five constraint types we track

1. **Grid** — Can the network handle new connections? (headroom, queue length)
2. **Trades** — Are there enough qualified people to do the work? (electricians, solar installers, heat pump engineers)
3. **Parts** — Can you get the components needed? (PCBs, inverters, chargers)
4. **Planning** — How long does approval take? (backlog, consent timelines)
5. **Infrastructure** — Is the physical stuff there? (substation capacity, cable routes)

## What we collect (and nothing else)

### Grid demand/supply
- NESO demand data (half-hourly UK demand) — **when demand spikes, constraints appear**
- NESO generation mix (wind/solar/gas output) — **renewable intermittency creates grid pressure**
- PV Live (actual solar generation) — **embedded generation affects local headroom**
- UKPN/NGED/ENW capacity data — **DNO-level constraints are where opportunities live**

### Trade capacity
- Electrical businesses by postcode area (EvSpark evidence) — **supply side**
- Job posting volume by trade × region — **demand side**
- MCS certified installer counts — **qualified supply**
- ONS labour data — **workforce trends**

### Planning/procurement
- Planning applications — **where development is happening**
- Contracts Finder — **what's being procured, by whom**
- Find a Tender — **public sector demand signals**

### Physical constraints
- Constraint surface candidates (from UKGraph) — **already identified constraints**
- Open Repair Alliance — **repair economics data**

## What we do NOT collect (yet)

- Generic UK business data (cgraphuk verticals are useful but not core)
- Consumer intent signals (wantgraph — interesting but not grid/trades/planning)
- Market friction (frictiongraph — too abstract right now)
- Research papers (openalex — interesting but not actionable yet)
- Energy pricing (octopus — pricing is outcome, not constraint)

## The scoring formula

For each region × constraint type:

```
severity = demand / supply
```

- demand > 3× supply = CRITICAL (4)
- demand > 2× supply = HIGH (3)
- demand > 1.5× supply = MEDIUM (2)
- demand > 1× supply = LOW (1)
- demand ≤ supply = NONE (0)

Composite regional scarcity = max severity across all constraints in that region.

## The output

A table: `region × constraint_type → severity → opportunity`

That's what Seesaw reads. That's what decides where to allocate capital.

## What we need to build

1. **Collectors that measure both sides of the gap** — not just data, but matched demand/supply pairs
2. **A compiler that computes severity** — the scoring formula above
3. **A daily scarcity view** — region × constraint → severity score
4. **Nothing else**

---

*Strip everything that doesn't directly answer: "Where is physical demand appearing faster than physical capacity can respond?"*

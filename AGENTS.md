# AGENTS.md — powuk operations

> UK physical constraint graph. Where is physical demand appearing faster than physical capacity?

---

## What this is

powuk measures scarcity across four layers:
1. **Installed capacity** — who can legally do the work now
2. **Incoming capacity** — who is being produced
3. **Demand** — what work is arriving
4. **Capacity friction** — why supply isn't responding

```
POW_Scarcity(s,g,t) = Demand / (Capacity + Expected Incoming Capacity)
```

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

### Query the database
```python
import sqlite3
conn = sqlite3.connect('data/powuk.db')
conn.execute('SELECT source, metric, value FROM observation ORDER BY observed_at DESC LIMIT 10')
```

---

## Collectors (13 active)

| Collector | Interval | What it measures |
|-----------|----------|-----------------|
| neso_demand | hourly | UK electricity demand |
| neso_generation | hourly | Generation mix (wind/solar/gas) |
| pvlive | hourly | Actual solar output |
| ukpn_flex | 12h | DNO flexibility capacity |
| evspark_trades | daily | Electrical businesses by area |
| planning_apps | 2h | Where development is happening |
| contracts_finder | 2h | Public procurement |
| find_tender | 2h | Higher-value procurement |
| ch_capacity | 12h | Companies House trade businesses |
| apar | daily | Training providers (1,263) |
| ofqual | daily | UK qualifications (10,000) |
| ons_labour | daily | ONS labour data |
| refcom | daily | F-gas certified companies (11,298) |

### Adding a collector
Add to server.py:
```python
@c("my_collector", interval_seconds)
def my_collector(conn):
    """What it measures."""
    # fetch data
    d = fetch_json("https://...")
    # store raw
    store(conn, "source", "dataset", json.dumps(d).encode())
    # store observation
    obs(conn, "source", "metric_name", value)
    return value
```

---

## Data sources

| Source | Auth | Status |
|--------|------|--------|
| NESO Open Data | none | ✓ Live |
| PV Live API | none | ✓ Live |
| Planning Data API | none | ✓ Live |
| Contracts Finder | none | ✓ Live |
| Find a Tender | none | ✓ Live |
| Companies House REST | API key | ✓ Active |
| Companies House Streaming | separate key | ✓ Active |
| Ofqual Register | none | ✓ Live |
| REFCOM API | none | ✓ Live |
| ONS | none | ✓ Live |
| APAR | none | ✓ Downloaded |

### API Keys
- Companies House REST: `YOUR_API_KEY`
- Companies House Streaming: `YOUR_STREAM_KEY`

---

## Key files

| File | Purpose |
|------|---------|
| server.py | Main collector server |
| THESIS.md | The one question we answer |
| DEVPLAN.md | Architecture vision |
| SOURCES.md | Registry of all data sources |
| COMPANIES_HOUSE_REF.md | Full CH API reference |
| COMPANIES_HOUSE_SPEC.md | Narrow CH collector spec |
| sdk/companies_house.py | Python SDK for CH API |

---

## Git

```bash
cd /root/powuk
git add -A
git commit -m "description"
git push
```

Remote: `https://github.com/prx0r/powuk`

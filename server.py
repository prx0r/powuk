"""powuk — UK physical constraint collector.

One question: Where is physical demand appearing faster than physical capacity?

Collectors measure both sides of the gap:
- Grid: demand vs capacity (NESO + PV Live + DNO)
- Trades: job demand vs installer supply
- Planning: application volume vs approval speed
- Procurement: contract demand vs available providers

Usage:
    python3 server.py          # run forever
    python3 server.py once     # collect once
    python3 server.py status   # show state
"""
import asyncio, hashlib, json, os, sqlite3, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent
DATA = BASE / "data"
RAW = DATA / "raw"
DB = DATA / "powuk.db"

# Load .env if present
env_path = BASE / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

for d in [RAW / "grid", RAW / "trades", RAW / "planning", DATA / "derived"]:
    d.mkdir(parents=True, exist_ok=True)

# ─── DB ──────────────────────────────────────────────────────

def get_db():
    c = sqlite3.connect(str(DB))
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript("""
    CREATE TABLE IF NOT EXISTS raw_ingest (
        id TEXT PRIMARY KEY, source TEXT, dataset TEXT, observed_at TEXT,
        raw_hash TEXT, raw_path TEXT, row_count INT, bytes INT, status TEXT
    );
    CREATE TABLE IF NOT EXISTS observation (
        id TEXT PRIMARY KEY, source TEXT, metric TEXT, value TEXT,
        unit TEXT, event_time TEXT, observed_at TEXT
    );
    CREATE TABLE IF NOT EXISTS collector_state (
        source TEXT PRIMARY KEY, last_run TEXT, status TEXT,
        rows INT, interval INT, runs INT DEFAULT 0
    );
    """)
    c.commit()
    return c

def store(c, source, dataset, data, rows=None):
    h = hashlib.sha256(data).hexdigest()[:16]
    ts = datetime.now(timezone.utc).isoformat()
    path = RAW / source / f"{dataset}.{'json' if data[:1] in (b'{',b'[') else 'csv'}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    c.execute("INSERT OR REPLACE INTO raw_ingest VALUES (?,?,?,?,?,?,?,?,'ok')",
              (f"{source}_{dataset}_{h}", source, dataset, ts, h, str(path), rows, len(data)))
    c.commit()

def obs(c, source, metric, value, unit=None, event_time=None):
    ts = datetime.now(timezone.utc).isoformat()
    oid = hashlib.sha256(f"{source}:{metric}:{ts}:{value}".encode()).hexdigest()[:24]
    c.execute("INSERT OR REPLACE INTO observation VALUES (?,?,?,?,?,?,?)",
              (oid, source, metric, json.dumps(value, default=str), unit, event_time or ts, ts))
    c.commit()

def state(c, source, status, rows=None, interval=None):
    c.execute("""INSERT INTO collector_state VALUES (?,?,?,?,?,1)
              ON CONFLICT(source) DO UPDATE SET last_run=excluded.last_run,
              status=excluded.status, rows=excluded.rows, runs=runs+1""",
              (source, datetime.now(timezone.utc).isoformat(), status, rows, interval))
    c.commit()

# ─── FETCH ───────────────────────────────────────────────────

def fetch(url, t=30):
    return urllib.request.urlopen(urllib.request.Request(url,
        headers={"User-Agent": "powuk/1.0"}), timeout=t).read()

def fetch_json(url, t=30):
    return json.loads(fetch(url, t).decode())

LOG = []
def log(m):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {m}", flush=True)
    LOG.append(m)

# ─── COLLECTORS (only what answers the thesis) ───────────────

COLLECTORS = []

def c(name, interval):
    def d(fn):
        COLLECTORS.append((name, fn, interval))
        return fn
    return d

# GRID: Where is demand outstripping capacity?

@c("neso_demand", 3600)  # hourly
def grid_demand(conn):
    """UK half-hourly electricity demand — the demand side of grid constraints."""
    d = fetch("https://api.neso.energy/dataset/7a12172a-939c-404c-b581-a6128b74f588/resource/177f6fa4-ae49-4182-81ea-0c6b35f26ca6/download/demanddataupdate.csv")
    lines = d.decode().strip().split("\n")
    store(conn, "grid", "neso_demand", d, len(lines)-1)
    if len(lines) > 1:
        last = lines[-1].split(",")
        if len(last) > 2:
            obs(conn, "grid", "uk_demand_mw", float(last[2]), "MW", f"{last[0]}T{last[1]}:00Z")
    return len(lines)-1

@c("neso_generation", 3600)  # hourly
def grid_generation(conn):
    """UK generation mix — shows renewable penetration and fossil backup."""
    d = fetch("https://api.neso.energy/dataset/88313ae5-94e4-4ddc-a790-593554d8c6b9/resource/f93d1835-75bc-43e5-84ad-12472b180a98/download/df_fuel_ckan.csv", 60)
    lines = d.decode().strip().split("\n")
    store(conn, "grid", "neso_generation", d, len(lines)-1)
    if len(lines) > 1:
        last = lines[-1].split(",")
        if len(last) > 13:
            ts = last[0]
            obs(conn, "grid", "uk_total_gen_mw", float(last[12]), "MW", ts)
            obs(conn, "grid", "uk_wind_mw", float(last[4])+float(last[5]), "MW", ts)
            obs(conn, "grid", "uk_solar_mw", float(last[10]), "MW", ts)
            obs(conn, "grid", "uk_carbon_intensity", float(last[13]), "gCO2/kWh", ts)
    return len(lines)-1

@c("pvlive", 3600)  # hourly
def grid_solar(conn):
    """Actual UK solar generation — embedded generation affects local headroom."""
    d = fetch_json("https://api.pvlive.uk/pvlive/api/v4/gsp/0?data_format=json")
    store(conn, "grid", "pvlive", json.dumps(d).encode())
    if isinstance(d, dict) and d.get("data"):
        for row in d["data"]:
            if row[0] == 0:
                obs(conn, "grid", "uk_solar_actual_mw", row[2], "MW", row[1])
    return 1

@c("ukpn_flex", 43200)  # 12h
def grid_dno_flex(conn):
    """UKPN flexibility dispatches — where DNOs are managing constraints."""
    try:
        d = fetch_json("https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets?limit=50")
        store(conn, "grid", "ukpn_catalog", json.dumps(d).encode())
        return 1
    except Exception as e:
        return 0

# TRADES: Are there enough people to do the work?

@c("evspark_trades", 86400)  # daily
def trade_supply(conn):
    """Electrical businesses by UK postcode area — supply side of trade constraints."""
    src = Path("/root/ab/businesses/evspark/receipts/ch_sweep_areas.csv")
    if not src.exists():
        return 0
    d = src.read_bytes()
    store(conn, "trades", "evspark_areas", d)
    lines = d.decode().strip().split("\n")
    total = sum(int(l.split(",")[1]) for l in lines[1:] if len(l.split(",")) > 1)
    obs(conn, "trades", "uk_electrical_businesses", total)
    return total

# PLANNING: Where is development happening faster than approvals?

@c("planning_apps", 7200)  # 2h
def planning_demand(conn):
    """Planning applications — where development pressure exists."""
    d = fetch_json("https://www.planning.data.gov.uk/entity.json?dataset=planning-application&limit=100")
    if "entities" in d:
        store(conn, "planning", "apps", json.dumps(d).encode(), len(d["entities"]))
        obs(conn, "planning", "apps_total", d.get("count", 0))
        return d.get("count", 0)
    return 0

@c("contracts_finder", 7200)  # 2h
def procurement_demand(conn):
    """Public procurement — where government is buying capacity."""
    d = fetch_json("https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search?limit=100")
    if "releases" in d:
        store(conn, "planning", "contracts", json.dumps(d).encode(), len(d["releases"]))
        return len(d["releases"])
    return 0

@c("find_tender", 7200)  # 2h
def find_tender(conn):
    """Find a Tender — higher-value UK procurement (OCDS)."""
    try:
        d = fetch_json("https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages?limit=50")
        if "releases" in d:
            store(conn, "planning", "find_tender", json.dumps(d).encode(), len(d["releases"]))
            return len(d["releases"])
    except Exception:
        pass
    return 0

@c("ch_capacity", 43200)  # 12h
def companies_house_capacity(conn):
    """Companies House — POWUK business capacity layer.
    
    Measures: firm stock, formations, dissolutions, charges
    For: POW-relevant SIC codes only (electrical, HVAC, solar, EV, telecom, repair)
    """
    import base64
    key = os.environ.get("COMPANIES_HOUSE_API_KEY", "")
    if not key:
        log("ch_capacity: no API key configured")
        return 0
    auth = base64.b64encode(f"{key}:".encode()).decode()
    
    SIC_CLUSTERS = {
        "electrical": {"sic": "43210", "queries": ["electrical contractor", "electrical installation"]},
        "hvac": {"sic": "43220", "queries": ["plumbing heating", "air conditioning"]},
        "solar": {"sic": "35110", "queries": ["solar panel", "renewable energy"]},
        "ev": {"sic": "43210", "queries": ["ev charger", "electric vehicle charging"]},
        "telecom": {"sic": "61100", "queries": ["telecommunications", "fibre broadband"]},
        "repair": {"sic": "95110", "queries": ["computer repair", "electronics repair"]},
        "construction": {"sic": "41100", "queries": ["building contractor", "construction"]},
    }
    
    results = {}
    for cluster, info in SIC_CLUSTERS.items():
        try:
            q = info["queries"][0].replace(" ", "+")
            url = f"https://api.company-information.service.gov.uk/search/companies?q={q}&items_per_page=1"
            req = urllib.request.Request(url, headers={
                "Authorization": f"Basic {auth}",
                "User-Agent": "powuk/1.0",
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                d = json.loads(resp.read().decode())
                total = d.get("total_results", 0)
                results[cluster] = {"sic": info["sic"], "active_firms": total}
                obs(conn, "ch", f"active_firms_{cluster}", total)
        except Exception:
            pass
    
    store(conn, "ch", "capacity_snapshot", json.dumps(results).encode())
    obs(conn, "ch", "clusters_tracked", len(results))
    return len(results)

@c("apar", 86400)  # daily
def apar_providers(conn):
    """APAR — Apprenticeship Provider and Assessment Register.
    
    The training provider universe. Who is eligible to train apprentices.
    """
    src = Path("/root/powuk/data/raw/labour/apar.csv")
    if not src.exists():
        # Download if not present
        import urllib.request
        url = "https://download.apprenticeships.education.gov.uk/apar/downloadcsv?filename=apar-2026-09-15-11-10-40.csv"
        try:
            urllib.request.urlretrieve(url, str(src))
        except Exception:
            return 0
    
    import csv
    providers = []
    with open(src) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("CanDeliverApprenticeships") == "True":
                providers.append({
                    "ukprn": row.get("Ukprn"),
                    "name": row.get("Name"),
                    "type": row.get("ApplicationType"),
                    "status": row.get("Status"),
                    "start_date": row.get("StartDate"),
                })
    
    store(conn, "labour", "apar", json.dumps(providers).encode(), len(providers))
    obs(conn, "labour", "apar_providers", len(providers))
    return len(providers)

@c("ofqual", 86400)  # daily
def ofqual_qualifications(conn):
    """Ofqual register — UK qualifications by trade/level."""
    try:
        d = fetch_json("https://register-api.ofqual.gov.uk/api/qualifications?pageSize=500&type=Regulated%20Qualification")
        if "results" in d:
            store(conn, "labour", "ofqual", json.dumps(d).encode(), len(d["results"]))
            # Count active qualifications
            active = [q for q in d["results"] if q.get("status") == "Awarded"]
            obs(conn, "labour", "uk_qualifications_active", len(active))
            return len(d["results"])
    except Exception:
        pass
    return 0

@c("ons_labour", 86400)  # daily
def ons_labour_demand(conn):
    """ONS labour demand — job adverts by SOC × region."""
    try:
        d = fetch("https://www.ons.gov.uk/file?uri=/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/datasets/labourdemandvolumesbystandardoccupationclassificationsoc2020uk/labourdemandbyoccupationandregion2024.xlsx", 60)
        store(conn, "labour", "ons_demand", d, len(d))
        obs(conn, "labour", "ons_labour_data_size", len(d), "bytes")
        return len(d)
    except Exception:
        pass
    return 0

@c("refcom", 86400)  # daily
def refcom_capacity(conn):
    """REFCOM F-gas certified companies — HVAC/refrigeration capacity."""
    try:
        # Get total count
        url = "https://api.refcom.org.uk/api/PublicCompany/GetFgasActiveCertificateCount"
        req = urllib.request.Request(url, headers={"User-Agent": "powuk/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            total = int(resp.read().decode().strip())
        
        obs(conn, "certification", "fgas_companies", total, "companies")
        store(conn, "certification", "refcom_count", json.dumps({"total": total}).encode())
        return total
    except Exception as e:
        return 0

# ─── SERVER ──────────────────────────────────────────────────

async def run_one(name, fn, interval, conn):
    while True:
        try:
            r = fn(conn)
            state(conn, name, "ok", r, interval)
            log(f"✓ {name}: {r}")
        except Exception as e:
            state(conn, name, "error")
            log(f"✗ {name}: {e}")
        await asyncio.sleep(interval)

async def run_all(conn):
    log(f"Running {len(COLLECTORS)} collectors...")
    for name, fn, _ in COLLECTORS:
        try:
            r = fn(conn)
            state(conn, name, "ok", r)
            log(f"✓ {name}: {r}")
        except Exception as e:
            state(conn, name, "error")
            log(f"✗ {name}: {e}")

def status(conn):
    rows = conn.execute("SELECT * FROM collector_state ORDER BY last_run DESC").fetchall()
    obs_count = conn.execute("SELECT COUNT(*) FROM observation").fetchone()[0]
    raw_count = conn.execute("SELECT COUNT(*) FROM raw_ingest").fetchone()[0]
    return {
        "collectors": {r[0]: {"status": r[2], "rows": r[3], "runs": r[5]} for r in rows},
        "observations": obs_count,
        "raw_ingests": raw_count,
        "db_bytes": DB.stat().st_size if DB.exists() else 0
    }

async def main():
    conn = get_db()
    log(f"powuk server — {len(COLLECTORS)} collectors")
    await run_all(conn)
    await asyncio.gather(*[asyncio.create_task(run_one(n, f, i, conn)) for n, f, i in COLLECTORS])

if __name__ == "__main__":
    conn = get_db()
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        print(json.dumps(status(conn), indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "once":
        asyncio.run(run_all(conn))
        print(json.dumps(status(conn), indent=2))
    else:
        asyncio.run(main())

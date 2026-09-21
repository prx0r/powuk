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
import asyncio, hashlib, json, os, sqlite3, sys, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Import collector types from layer1 (single source of truth)
sys.path.insert(0, str(Path(__file__).parent))
from layer1.collector import CollectorResult, CollectorStatus, record_coverage, store_raw, store_normalized

BASE = Path(__file__).parent
DATA = BASE / "data"
RAW = DATA / "raw"
DB = DATA / "powuk.db"


# ─── SOURCE REGISTRY ──────────────────────────────────────────

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
    c = sqlite3.connect(str(DB), check_same_thread=False)
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript("""
    CREATE TABLE IF NOT EXISTS raw_blob (
        raw_hash TEXT PRIMARY KEY,
        storage_path TEXT NOT NULL,
        bytes INT NOT NULL,
        first_seen TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS raw_ingest (
        retrieval_id TEXT PRIMARY KEY,
        source TEXT NOT NULL,
        dataset TEXT NOT NULL,
        raw_hash TEXT NOT NULL,
        observed_at TEXT NOT NULL,
        row_count INT,
        status TEXT
    );
    CREATE TABLE IF NOT EXISTS observation (
        id TEXT PRIMARY KEY, source TEXT, metric TEXT, value TEXT,
        unit TEXT, event_time TEXT, observed_at TEXT
    );
    CREATE TABLE IF NOT EXISTS collector_state (
        source TEXT PRIMARY KEY, last_run TEXT, status TEXT,
        rows INT, interval INT, runs INT DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS source_coverage (
        source_id TEXT NOT NULL,
        partition TEXT NOT NULL DEFAULT 'default',
        expected_count INT NOT NULL,
        collected_count INT NOT NULL,
        unique_count INT,
        coverage_ratio REAL NOT NULL,
        complete BOOLEAN NOT NULL,
        checked_at TEXT NOT NULL,
        PRIMARY KEY (source_id, partition)
    );
    """)
    c.commit()
    return c

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

def get_last_success(conn, source):
    """Get last successful run time for a source (watermark for incremental fetch)."""
    row = conn.execute("SELECT last_run FROM collector_state WHERE source=?", (source,)).fetchone()
    return row[0] if row else None

# ─── FETCH (with retry) ──────────────────────────────────────

# Transient HTTP codes worth retrying
RETRYABLE_CODES = {408, 425, 429, 500, 502, 503, 504}
# Permanent codes — fail immediately, no retry
PERMANENT_CODES = {400, 401, 403, 404, 405, 410}


class FetchError(Exception):
    """Non-retryable fetch failure."""
    def __init__(self, status_code, message):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")


def fetch(url, t=30, max_retries=3):
    """Fetch URL with Retry-After header support, exponential backoff, jitter."""
    import random
    last_err = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "powuk/1.0"})
            with urllib.request.urlopen(req, timeout=t) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code in PERMANENT_CODES:
                raise FetchError(e.code, e.read().decode()[:200]) from e
            if e.code == 429:
                retry_after = e.headers.get("Retry-After") if hasattr(e, 'headers') else None
                if retry_after:
                    try:
                        delay = float(retry_after)
                    except (ValueError, TypeError):
                        delay = min(60.0, 2 ** (attempt + 1))
                else:
                    delay = min(60.0, 2 ** (attempt + 1))
                delay += random.uniform(0, 0.5)  # jitter
                time.sleep(delay)
                last_err = e
                continue
            if e.code in RETRYABLE_CODES and attempt < max_retries - 1:
                delay = min(30.0, 2 ** (attempt + 1)) + random.uniform(0, 0.5)
                time.sleep(delay)
                last_err = e
                continue
            raise FetchError(e.code, e.read().decode()[:200]) from e
        except FetchError:
            raise
        except Exception as e:
            if attempt >= max_retries - 1:
                raise
            delay = min(30.0, 2 ** (attempt + 1)) + random.uniform(0, 0.5)
            time.sleep(delay)
            last_err = e
    raise last_err or RuntimeError("fetch failed after retries")


def fetch_json(url, t=30, max_retries=3):
    """Fetch URL, return parsed JSON."""
    return json.loads(fetch(url, t, max_retries).decode())

# ─── SOURCE REGISTRY ──────────────────────────────────────────

def load_sources():
    """Load source registry from config/sources.yaml. Returns dict keyed by source ID."""
    try:
        import yaml
        config_path = BASE / "config" / "sources.yaml"
        with open(config_path) as f:
            data = yaml.safe_load(f)
        sources = data.get("sources", [])
        return {s["id"]: s for s in sources if "id" in s}
    except Exception as e:
        log(f"Warning: could not load sources.yaml: {e}")
        return {}

SOURCES = load_sources()

def cadence_to_seconds(cadence):
    """Convert cadence string from sources.yaml to seconds."""
    if not cadence:
        return 3600
    cadence = cadence.strip().lower()
    mapping = {
        "hourly": 3600, "1h": 3600,
        "2h": 7200, "3h": 10800, "6h": 21600,
        "12h": 43200, "daily": 86400, "24h": 86400,
    }
    return mapping.get(cadence, 3600)

def get_source_config(source_id):
    """Get config for a source, with cadence fallback to COLLECTORS list."""
    return SOURCES.get(source_id, {})

LOG = []
def log(m):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {m}", flush=True)
    LOG.append(m)

# ─── COLLECTORS (only what answers the thesis) ───────────────

COLLECTORS = []

def c(name, default_interval=None):
    """Register a collector. Reads cadence from sources.yaml if available."""
    def d(fn):
        src = SOURCES.get(name, {})
        cadence = src.get("cadence")
        interval = cadence_to_seconds(cadence) if cadence else (default_interval or 3600)
        COLLECTORS.append((name, fn, interval))
        return fn
    return d

# GRID: Where is demand outstripping capacity?

@c("neso_demand")  # cadence from sources.yaml (hourly)
def grid_demand(conn):
    """UK half-hourly electricity demand — the demand side of grid constraints.
    
    Stores raw CSV + last 24h of observations (48 half-hourly periods).
    """
    d = fetch("https://api.neso.energy/dataset/7a12172a-939c-404c-b581-a6128b74f588/resource/177f6fa4-ae49-4182-81ea-0c6b35f26ca6/download/demanddataupdate.csv")
    lines = d.decode().strip().split("\n")
    store_raw("neso_demand", d, "csv")
    
    # Store last 48 observations (24h of half-hourly data)
    count = 0
    if len(lines) > 1:
        for line in lines[-49:-1]:  # last 48 data rows
            parts = line.split(",")
            if len(parts) > 2 and parts[2]:
                try:
                    ts = f"{parts[0]}T{parts[1]}:00Z"
                    obs(conn, "grid", "uk_demand_mw", float(parts[2]), "MW", ts)
                    count += 1
                except (ValueError, IndexError):
                    pass
    return CollectorResult.success(rows=len(lines)-1, warnings=[f"Stored {count} observations (last 24h)"] if count else [])

@c("neso_generation")  # cadence from sources.yaml (hourly)
def grid_generation(conn):
    """UK generation mix — shows renewable penetration and fossil backup.
    
    Stores raw CSV + last 24h of observations.
    """
    d = fetch("https://api.neso.energy/dataset/88313ae5-94e4-4ddc-a790-593554d8c6b9/resource/f93d1835-75bc-43e5-84ad-12472b180a98/download/df_fuel_ckan.csv", 60)
    lines = d.decode().strip().split("\n")
    store_raw("neso_generation", d, "csv")
    
    # Store last 48 observations (24h of half-hourly data)
    count = 0
    if len(lines) > 1:
        for line in lines[-49:-1]:
            parts = line.split(",")
            if len(parts) > 13 and parts[12]:
                try:
                    ts = parts[0]
                    obs(conn, "grid", "uk_total_gen_mw", float(parts[12]), "MW", ts)
                    obs(conn, "grid", "uk_wind_mw", float(parts[4])+float(parts[5]), "MW", ts)
                    obs(conn, "grid", "uk_solar_mw", float(parts[10]), "MW", ts)
                    obs(conn, "grid", "uk_carbon_intensity", float(parts[13]), "gCO2/kWh", ts)
                    count += 1
                except (ValueError, IndexError):
                    pass
    return CollectorResult.success(rows=len(lines)-1, warnings=[f"Stored {count} observation sets (last 24h)"] if count else [])

@c("pvlive")  # cadence from sources.yaml (hourly)
def grid_solar(conn):
    """Actual UK solar generation — embedded generation affects local headroom."""
    d = fetch_json("https://api.pvlive.uk/pvlive/api/v4/gsp/0?data_format=json")
    store_raw("pvlive", json.dumps(d).encode(), "json")
    if isinstance(d, dict) and d.get("data"):
        for row in d["data"]:
            if row[0] == 0:
                obs(conn, "grid", "uk_solar_actual_mw", row[2], "MW", row[1])
    return CollectorResult.success(rows=1)

@c("ukpn_flex")  # cadence from sources.yaml (12h)
def grid_dno_flex(conn):
    """UKPN flexibility dispatches — where DNOs are managing constraints.
    
    Stage: discovery — currently fetches dataset catalogue, not actual flexibility data.
    """
    d = fetch_json("https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets?limit=50")
    store_raw("ukpn_flex", json.dumps(d).encode(), "json")
    return CollectorResult.success(rows=1, warnings=["Stage discovery: fetched catalogue metadata only, not flexibility data"])

# TRADES: Are there enough people to do the work?

@c("evspark_trades")  # cadence from sources.yaml (daily)
def trade_supply(conn):
    """Electrical businesses by UK postcode area — supply side of trade constraints.
    
    Stage: raw — uses legacy local file. Not portable.
    """
    src = Path("/root/ab/businesses/evspark/receipts/ch_sweep_areas.csv")
    if not src.exists():
        return CollectorResult.blocked("Legacy source file not found: /root/ab/...")
    d = src.read_bytes()
    store_raw("evspark_trades", d, "csv")
    lines = d.decode().strip().split("\n")
    total = sum(int(l.split(",")[1]) for l in lines[1:] if len(l.split(",")) > 1)
    obs(conn, "trades", "uk_electrical_businesses", total)
    return CollectorResult.success(rows=total, warnings=["Stage raw: legacy local file, not portable"])

# PLANNING: Where is development happening faster than approvals?

@c("planning_apps")  # cadence from sources.yaml (2h)
def planning_demand(conn):
    """Planning applications — where development pressure exists.
    
    Uses modified_since watermark for incremental fetch.
    Stage: raw
    """
    all_entities = []
    start_index = 0
    page_size = 100
    
    # Use watermark for incremental fetch
    last_success = get_last_success(conn, "planning_apps")
    max_pages = 50  # from sources.yaml
    
    while start_index < max_pages * page_size:
        url = f"https://www.planning.data.gov.uk/entity.json?dataset=planning-application&limit={page_size}&start={start_index}"
        if last_success:
            url += f"&modified_since={last_success[:10]}"
        d = fetch_json(url)
        if "entities" not in d or len(d["entities"]) == 0:
            break
        all_entities.extend(d["entities"])
        start_index += page_size
        if start_index >= d.get("count", 0):
            break
    
    if all_entities:
        store_normalized("planning_apps", all_entities)
    
    return CollectorResult.success(rows=len(all_entities))

@c("contracts_finder")  # cadence from sources.yaml (2h)
def procurement_demand(conn):
    """Public procurement — where government is buying capacity.
    
    Uses modified_since watermark for incremental fetch.
    Stage: raw
    """
    all_releases = []
    start_index = 0
    page_size = 100
    max_pages = 50  # from sources.yaml
    
    last_success = get_last_success(conn, "contracts_finder")
    
    while start_index < max_pages * page_size:
        url = f"https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search?limit={page_size}&start={start_index}"
        if last_success:
            url += f"&modifiedSince={last_success[:10]}"
        d = fetch_json(url, t=15)
        if "releases" not in d or len(d["releases"]) == 0:
            break
        all_releases.extend(d["releases"])
        start_index += page_size
    
    if all_releases:
        store_normalized("contracts_finder", all_releases)
    
    return CollectorResult.success(rows=len(all_releases))

@c("find_tender")  # cadence from sources.yaml (2h)
def find_tender(conn):
    """Find a Tender — higher-value UK procurement (OCDS).
    
    Paginates through available releases with watermark.
    Stage: raw
    """
    all_releases = []
    start_index = 0
    page_size = 50
    max_pages = 50  # from sources.yaml
    
    last_success = get_last_success(conn, "find_tender")
    
    while start_index < max_pages * page_size:
        url = f"https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages?limit={page_size}&start={start_index}"
        if last_success:
            url += f"&modifiedSince={last_success[:10]}"
        d = fetch_json(url, t=15)
        releases = d.get("releases", [])
        if not releases:
            break
        all_releases.extend(releases)
        start_index += page_size
    
    if all_releases:
        store_normalized("find_tender", all_releases)
    
    return CollectorResult.success(rows=len(all_releases))

@c("ch_capacity")  # cadence from sources.yaml (12h)
def companies_house_capacity(conn):
    """Companies House — POWUK business capacity layer.
    
    SIC clusters driven from sources.yaml config.
    Paginates all companies per SIC code.
    """
    import base64
    key = os.environ.get("COMPANIES_HOUSE_API_KEY", "")
    if not key:
        return CollectorResult.blocked("COMPANIES_HOUSE_API_KEY not configured")
    
    auth = base64.b64encode(f"{key}:".encode()).decode()
    
    # Load SIC clusters from sources.yaml
    try:
        import yaml
        with open(BASE / "config" / "sources.yaml") as f:
            config = yaml.safe_load(f)
        ch_config = next(s for s in config["sources"] if s["id"] == "ch_capacity")
        sic_clusters = ch_config.get("sic_clusters", {})
    except Exception:
        # Fallback if config unreadable
        sic_clusters = {
            "electrical": ["43210"],
            "hvac": ["43220"],
            "solar": ["35110"],
            "telecom": ["61100"],
            "repair": ["95110"],
            "construction": ["41100"],
        }
    
    warnings = []
    all_entities = []
    results = {}
    for cluster, sic_codes in sic_clusters.items():
        try:
            all_items = []
            for sic in sic_codes:
                start_index = 0
                while start_index < 10000:  # Safety cap
                    url = f"https://api.company-information.service.gov.uk/advanced-search/companies?sic_codes={sic}&company_status=active&size=5000&start_index={start_index}"
                    req = urllib.request.Request(url, headers={
                        "Authorization": f"Basic {auth}",
                        "User-Agent": "powuk/1.0",
                    })
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        d = json.loads(resp.read().decode())
                        items = d.get("items", [])
                        all_items.extend(items)
                        if len(items) < 5000:
                            break
                        start_index += len(items)
            
            # Dedupe by company_number
            seen = set()
            unique = []
            for item in all_items:
                cn = item.get("company_number")
                if cn and cn not in seen:
                    seen.add(cn)
                    entity = {
                        "company_number": cn,
                        "name": item.get("company_name"),
                        "status": item.get("company_status"),
                        "sic_codes": item.get("sic_codes", []),
                        "incorporation_date": item.get("incorporation_date"),
                        "postcode": item.get("registered_office_address", {}).get("postal_code"),
                        "cluster": cluster,
                    }
                    unique.append(entity)
                    all_entities.append(entity)
            
            results[cluster] = {"sic_codes": sic_codes, "active_firms": len(unique)}
            obs(conn, "ch", f"active_firms_{cluster}", float(len(unique)), "firms")
        except Exception as e:
            warnings.append(f"{cluster}: {str(e)[:80]}")
    
    # Store entity-level records (not just counts)
    if all_entities:
        store_normalized("ch_capacity", all_entities)
    
    # Also store cluster summary
    cluster_records = [{"cluster": cluster, **info} for cluster, info in results.items()]
    store_normalized("ch_capacity_summary", cluster_records)
    
    obs(conn, "ch", "clusters_tracked", float(len(results)))
    return CollectorResult.success(rows=len(results), warnings=warnings)

@c("apar")  # cadence from sources.yaml (daily)
def apar_providers(conn):
    """APAR — Apprenticeship Provider and Assessment Register.
    
    Stage: normalized — all fields preserved.
    """
    import csv
    import urllib.request
    
    url = "https://download.apprenticeships.education.gov.uk/apar/downloadcsv?filename=apar.csv"
    req = urllib.request.Request(url, headers={"User-Agent": "powuk/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    
    # Store raw via store_raw (dedup, content-hashed)
    raw_info = store_raw("apar", data, "csv")
    
    # Parse CSV and normalize ALL fields
    lines = data.decode().strip().split("\n")
    reader = csv.DictReader(lines)
    
    providers = []
    for row in reader:
        provider = {k: row.get(k) for k in row.keys()}
        providers.append(provider)
    
    # Store normalized via store_normalized
    store_normalized("apar", providers)
    
    active = sum(1 for p in providers if p.get("CanDeliverApprenticeships") == "True")
    obs(conn, "labour", "apar_providers_total", float(len(providers)), "providers")
    obs(conn, "labour", "apar_providers_active", float(active), "providers")
    record_coverage(conn, "apar", expected=len(providers), collected=len(providers))
    
    return CollectorResult.success(rows=len(providers))

@c("ofqual")  # cadence from sources.yaml (daily)
def ofqual_qualifications(conn):
    """Ofqual register — UK qualifications by trade/level.
    
    Paginates through all records (52K+ total).
    """
    all_results = []
    page_size = 500
    start_index = 0
    max_records = 60000  # Safety cap
    
    while start_index < max_records:
        url = f"https://register-api.ofqual.gov.uk/api/qualifications?pageSize={page_size}&start={start_index}&type=Regulated%20Qualification"
        d = fetch_json(url)
        results = d.get("results", [])
        if not results:
            break
        all_results.extend(results)
        start_index += page_size
        if len(results) < page_size:
            break
    
    if all_results:
        # Store normalized via store_normalized
        store_normalized("ofqual", all_results)
        
        # Count by status for observability
        status_counts = {}
        for q in all_results:
            s = q.get("status", "unknown")
            status_counts[s] = status_counts.get(s, 0) + 1
        
        obs(conn, "labour", "uk_qualifications_total", float(len(all_results)))
        for s, count in status_counts.items():
            obs(conn, "labour", f"uk_qualifications_{s.lower()}", float(count))
        
        # Coverage: Ofqual has ~52,887 total qualifications
        record_coverage(conn, "ofqual", expected=52887, collected=len(all_results))
    
    return CollectorResult.success(rows=len(all_results))

@c("ons_labour")  # cadence from sources.yaml (daily)
def ons_labour_demand(conn):
    """ONS labour demand — job adverts by SOC x region.
    
    Normalizes ALL rows into queryable records.
    """
    url = "https://www.ons.gov.uk/file?uri=/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/datasets/labourdemandvolumesbystandardoccupationclassificationsoc2020uk/january2017tojuly2026/labourdemandbyoccupation.xlsx"
    d = fetch(url, 60)
    
    # Store raw via store_raw (dedup, content-hashed)
    raw_info = store_raw("ons_labour", d, "xlsx")
    
    # Parse XLSX and normalize ALL rows
    import io
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(d), read_only=True)
    
    records = []
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) < 2:
            continue
        
        headers = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(rows[0])]
        
        period_col = next((i for i, h in enumerate(headers) if 'period' in h.lower() or 'date' in h.lower()), None)
        soc_col = next((i for i, h in enumerate(headers) if 'soc' in h.lower() or 'occupation' in h.lower()), None)
        geo_col = next((i for i, h in enumerate(headers) if 'region' in h.lower() or 'area' in h.lower()), None)
        
        for row in rows[1:]:
            if row is None or all(v is None for v in row):
                continue
            record = {
                "sheet": sheet_name,
                "period": str(row[period_col]) if period_col is not None and row[period_col] else None,
                "soc_code": str(row[soc_col]) if soc_col is not None and row[soc_col] else None,
                "geography": str(row[geo_col]) if geo_col is not None and row[geo_col] else None,
                "raw_row": [str(v) if v is not None else None for v in row[:10]],
            }
            records.append(record)
    
    wb.close()
    
    # Store normalized via store_normalized
    store_normalized("ons_labour", records)
    
    obs(conn, "labour", "ons_labour_records", float(len(records)), "records")
    obs(conn, "labour", "ons_labour_sheets", float(len(wb.sheetnames)), "sheets")
    record_coverage(conn, "ons_labour", expected=len(records), collected=len(records))
    
    return CollectorResult.success(rows=len(records))

@c("refcom")  # cadence from sources.yaml (daily)
def refcom_capacity(conn):
    """REFCOM F-gas certified companies — HVAC/refrigeration capacity.
    
    Full enumeration: iterates 0 to total-1, deduplicates by companyId.
    """
    base_url = "https://api.refcom.org.uk/api/PublicCompany"
    
    # Get total count
    count_url = f"{base_url}/GetFgasActiveCertificateCount"
    count_data = fetch_json(count_url)
    total = int(count_data) if isinstance(count_data, (int, float)) else int(str(count_data).strip())
    
    # Store raw count response
    store_raw("refcom", json.dumps({"total_count": total}).encode(), "json")
    
    # Enumerate ALL companies (0 to total-1)
    companies = {}
    errors = 0
    for idx in range(total):
        url = f"{base_url}/GetByIndex?scheme=fgas&index={idx}"
        req = urllib.request.Request(url, headers={"User-Agent": "powuk/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                items = data if isinstance(data, list) else [data] if data else []
                for item in items:
                    if item and isinstance(item, dict) and item.get("companyId"):
                        cid = item["companyId"]
                        if cid not in companies:
                            companies[cid] = {
                                "company_id": cid,
                                "name": item.get("companyName"),
                                "postcode": item.get("postcode"),
                                "fgas_code": item.get("fGasCode"),
                                "phone": item.get("telephoneNo"),
                            }
        except Exception:
            errors += 1
            if errors > 100:
                break
    
    company_list = list(companies.values())
    
    # Store normalized via store_normalized
    store_normalized("refcom", company_list)
    
    obs(conn, "certification", "fgas_companies", float(total), "companies")
    obs(conn, "certification", "fgas_collected", float(len(company_list)), "companies")
    
    coverage = len(company_list) / total if total > 0 else 0
    warnings = []
    if coverage < 0.99:
        warnings.append(f"Coverage {coverage:.1%} ({len(company_list)}/{total})")
    
    record_coverage(conn, "refcom", expected=total, collected=len(company_list))
    
    return CollectorResult.success(rows=len(company_list), warnings=warnings)

@c("ashe_wages")  # cadence from sources.yaml (daily)
def ashe_wages(conn):
    """ASHE — Annual Survey of Hours and Earnings.
    
    Wage/shadow-price proxy for skilled labour.
    Table 3: Region × SOC2 × earnings
    """
    import zipfile
    import io
    
    # Download ASHE Table 3
    url = "https://www.ons.gov.uk/file?uri=/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/regionbyoccupation2digitsocashetable3/2025provisional/ashetable32025provisional.zip"
    d = fetch(url, 60)
    
    # Store raw via store_raw (dedup, content-hashed)
    raw_info = store_raw("ashe_wages", d, "zip")
    
    # Extract and parse XLSX
    import openpyxl
    with zipfile.ZipFile(io.BytesIO(d)) as zf:
        xlsx_files = [f for f in zf.namelist() if f.endswith('.xlsx')]
        if not xlsx_files:
            return CollectorResult.failed("No XLSX found in ASHE zip")
        with zf.open(xlsx_files[0]) as xlsx_file:
            wb = openpyxl.load_workbook(io.BytesIO(xlsx_file.read()), read_only=True)
            
            records = []
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                rows = list(ws.iter_rows(values_only=True))
                if len(rows) < 3:
                    continue
                
                for row in rows[2:]:
                    if row and row[0]:
                        record = {
                            "region": str(row[0]) if row[0] else None,
                            "soc_code": str(row[1]) if len(row) > 1 and row[1] else None,
                            "occupation": str(row[2]) if len(row) > 2 and row[2] else None,
                            "hourly_pay": float(row[3]) if len(row) > 3 and row[3] and isinstance(row[3], (int, float)) else None,
                            "annual_pay": float(row[4]) if len(row) > 4 and row[4] and isinstance(row[4], (int, float)) else None,
                        }
                        if record["region"] and record["soc_code"]:
                            records.append(record)
            
            wb.close()
    
    # Store normalized via store_normalized
    store_normalized("ashe_wages", records)
    
    obs(conn, "labour", "ashe_wage_records", float(len(records)), "records")
    record_coverage(conn, "ashe_wages", expected=len(records), collected=len(records))
    
    return CollectorResult.success(rows=len(records))

@c("ons_skills")  # cadence from sources.yaml (daily)
def ons_job_skills(conn):
    """ONS job-ad skills/competencies from online job adverts.
    
    Skills, competencies and other job requirements from online job adverts, UK.
    """
    url = "https://www.ons.gov.uk/file?uri=/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/datasets/skillscompetenciesandotherjobrequirementsfromonlinejobadvertsuk/january2017toseptember2025/skillscompetenciesandotherjobrequirementsfromonlinejobadvertsuk.xlsx"
    d = fetch(url, 60)
    
    # Store raw via store_raw (dedup, content-hashed)
    raw_info = store_raw("ons_skills", d, "xlsx")
    
    # Parse XLSX
    import io
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(d), read_only=True)
    
    records = []
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) < 2:
            continue
        headers = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(rows[0])]
        for row in rows[1:]:
            if row is None or all(v is None for v in row):
                continue
            record = {"sheet": sheet_name}
            for i, h in enumerate(headers):
                if i < len(row) and row[i] is not None:
                    record[h] = str(row[i])
            records.append(record)
    wb.close()
    
    # Store normalized via store_normalized
    store_normalized("ons_skills", records)
    
    obs(conn, "labour", "ons_skills_records", float(len(records)), "records")
    record_coverage(conn, "ons_skills", expected=len(records), collected=len(records))
    
    return CollectorResult.success(rows=len(records))

@c("ons_salaries")  # cadence from sources.yaml (daily)
def ons_job_salaries(conn):
    """ONS online job adverts salaries, UK.
    
    Salary data from online job adverts.
    """
    url = "https://www.ons.gov.uk/file?uri=/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/onlinejobadvertssalariesuk/january2017tomay2025/onlinejobadvertssalariesuk.xlsx"
    d = fetch(url, 60)
    
    # Store raw via store_raw (dedup, content-hashed)
    raw_info = store_raw("ons_salaries", d, "xlsx")
    
    # Parse XLSX
    import io
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(d), read_only=True)
    
    records = []
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) < 2:
            continue
        headers = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(rows[0])]
        for row in rows[1:]:
            if row is None or all(v is None for v in row):
                continue
            record = {"sheet": sheet_name}
            for i, h in enumerate(headers):
                if i < len(row) and row[i] is not None:
                    record[h] = str(row[i])
            records.append(record)
    wb.close()
    
    # Store normalized via store_normalized
    store_normalized("ons_salaries", records)
    
    obs(conn, "labour", "ons_salaries_records", float(len(records)), "records")
    record_coverage(conn, "ons_salaries", expected=len(records), collected=len(records))
    
    return CollectorResult.success(rows=len(records))

# ─── SERVER ──────────────────────────────────────────────────

async def run_one(name, fn, interval, conn):
    """Run a single collector in a loop. Each iteration gets its own DB connection."""
    while True:
        try:
            thread_conn = get_db()
            result = await asyncio.to_thread(fn, thread_conn)
            thread_conn.close()
            if not isinstance(result, CollectorResult):
                result = CollectorResult.success(rows=int(result) if result else 0)
            
            state(conn, name, result.status.value, result.rows, interval)
            icon = {"success": "✓", "success_empty": "○", "partial": "△", "failed": "✗", "blocked": "■"}
            log(f"{icon.get(result.status.value, '?')} {name}: {result.status.value} rows={result.rows}")
            if result.warnings:
                for w in result.warnings:
                    log(f"  ⚠ {name}: {w}")
        except Exception as e:
            state(conn, name, "failed", 0, interval)
            log(f"✗ {name}: {e}")
        await asyncio.sleep(interval)

async def run_all(conn):
    """Run all collectors once, each in its own thread with its own DB connection."""
    log(f"Running {len(COLLECTORS)} collectors...")
    db_path = str(DB)
    tasks = []
    for name, fn, _ in COLLECTORS:
        async def _run(n=name, f=fn):
            try:
                thread_conn = get_db()
                result = await asyncio.to_thread(f, thread_conn)
                thread_conn.close()
                if not isinstance(result, CollectorResult):
                    result = CollectorResult.success(rows=int(result) if result else 0)
                state(conn, n, result.status.value, result.rows)
                icon = {"success": "✓", "success_empty": "○", "partial": "△", "failed": "✗", "blocked": "■"}
                log(f"{icon.get(result.status.value, '?')} {n}: {result.status.value} rows={result.rows}")
                if result.warnings:
                    for w in result.warnings:
                        log(f"  ⚠ {n}: {w}")
            except Exception as e:
                state(conn, n, "failed", 0)
                log(f"✗ {n}: {e}")
        tasks.append(_run())
    await asyncio.gather(*tasks)

def status(conn):
    rows = conn.execute("SELECT * FROM collector_state ORDER BY last_run DESC").fetchall()
    obs_count = conn.execute("SELECT COUNT(*) FROM observation").fetchone()[0]
    raw_count = conn.execute("SELECT COUNT(*) FROM raw_ingest").fetchone()[0]
    
    # Get coverage data
    try:
        coverage_rows = conn.execute(
            "SELECT source_id, expected_count, collected_count, coverage_ratio, complete FROM source_coverage"
        ).fetchall()
        coverage = {r[0]: {"expected": r[1], "collected": r[2], "ratio": r[3], "complete": r[4]} for r in coverage_rows}
    except Exception:
        coverage = {}
    
    health = {}
    for row in rows:
        source = row[0]
        last_status = row[2]
        run_count = row[5]
        
        # Check implementation stage from sources.yaml
        stage = SOURCES.get(source, {}).get("stage", "unknown")
        
        cov = coverage.get(source)
        cov_str = ""
        if cov:
            cov_str = f" [{cov['collected']}/{cov['expected']}={cov['ratio']:.0%}]"
        
        if last_status in ("failed", "blocked"):
            health[source] = f"FAILED ({stage}){cov_str}"
        elif run_count == 0:
            health[source] = f"NOT_RUN ({stage}){cov_str}"
        else:
            health[source] = f"OK ({stage}){cov_str}"
    
    return {
        "collectors": {r[0]: {"status": r[2], "rows": r[3], "runs": r[5]} for r in rows},
        "health": health,
        "coverage": coverage,
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

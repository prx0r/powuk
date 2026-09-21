"""
powuk capability_provider entity.

Who can legally or credibly do the work now.
Built from certification registers, Companies House, and training data.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import hashlib
import json
import sqlite3


# ─── SCHEMA ───────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS capability_provider (
    provider_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    company_number TEXT,
    is_sole_trader BOOLEAN DEFAULT 0,
    postcode TEXT,
    lat REAL,
    lon REAL,
    region TEXT,
    source TEXT NOT NULL,
    observed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS provider_capability (
    id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL,
    capability TEXT NOT NULL,  -- electrical, ev_charger, solar_pv, heat_pump, hvac, f_gas, retrofit, etc.
    certification_scheme TEXT,  -- MCS, OZEV, F-Gas, TrustMark, Competent Person, etc.
    certification_start TEXT,
    certification_expiry TEXT,
    status TEXT DEFAULT 'active',
    source TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    FOREIGN KEY (provider_id) REFERENCES capability_provider(provider_id)
);

CREATE INDEX IF NOT EXISTS idx_provider_capability ON provider_capability(provider_id, capability);
CREATE INDEX IF NOT EXISTS idx_provider_region ON capability_provider(region, postcode);
CREATE INDEX IF NOT EXISTS idx_capability_scheme ON provider_capability(capability, certification_scheme);
"""


# ─── ENTITY ───────────────────────────────────────────────────

@dataclass
class CapabilityProvider:
    name: str
    source: str
    company_number: Optional[str] = None
    is_sole_trader: bool = False
    postcode: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    region: Optional[str] = None
    provider_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.provider_id:
            raw = f"{self.name}:{self.company_number or 'sole'}:{self.source}"
            self.provider_id = hashlib.sha256(raw.encode()).hexdigest()[:24]


@dataclass
class ProviderCapability:
    provider_id: str
    capability: str
    source: str
    certification_scheme: Optional[str] = None
    certification_start: Optional[str] = None
    certification_expiry: Optional[str] = None
    status: str = "active"
    cap_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.cap_id:
            raw = f"{self.provider_id}:{self.capability}:{self.certification_scheme}"
            self.cap_id = hashlib.sha256(raw.encode()).hexdigest()[:24]


# ─── STORAGE ──────────────────────────────────────────────────

def init_provider_db(conn: sqlite3.Connection):
    conn.executescript(SCHEMA)
    conn.commit()


def upsert_provider(conn: sqlite3.Connection, provider: CapabilityProvider):
    ts = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT OR REPLACE INTO capability_provider
        (provider_id, name, company_number, is_sole_trader, postcode, lat, lon, region, source, observed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (provider.provider_id, provider.name, provider.company_number,
          provider.is_sole_trader, provider.postcode, provider.lat, provider.lon,
          provider.region, provider.source, ts))
    conn.commit()


def upsert_capability(conn: sqlite3.Connection, cap: ProviderCapability):
    ts = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT OR REPLACE INTO provider_capability
        (id, provider_id, capability, certification_scheme, certification_start, certification_expiry, status, source, observed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (cap.cap_id, cap.provider_id, cap.capability, cap.certification_scheme,
          cap.certification_start, cap.certification_expiry, cap.status, cap.source, ts))
    conn.commit()


# ─── QUERIES ──────────────────────────────────────────────────

def count_by_capability(conn: sqlite3.Connection, capability: str, region: Optional[str] = None) -> int:
    """Count active providers with a given capability."""
    if region:
        return conn.execute("""
            SELECT COUNT(DISTINCT pc.provider_id)
            FROM provider_capability pc
            JOIN capability_provider p ON pc.provider_id = p.provider_id
            WHERE pc.capability = ? AND pc.status = 'active' AND p.region = ?
        """, (capability, region)).fetchone()[0]
    else:
        return conn.execute("""
            SELECT COUNT(DISTINCT provider_id)
            FROM provider_capability
            WHERE capability = ? AND status = 'active'
        """, (capability,)).fetchone()[0]


def count_by_region(conn: sqlite3.Connection, region: str) -> dict:
    """Count providers by capability in a region."""
    rows = conn.execute("""
        SELECT pc.capability, COUNT(DISTINCT pc.provider_id)
        FROM provider_capability pc
        JOIN capability_provider p ON pc.provider_id = p.provider_id
        WHERE p.region = ? AND pc.status = 'active'
        GROUP BY pc.capability
    """, (region,)).fetchall()
    return {row[0]: row[1] for row in rows}


def get_provider_capabilities(conn: sqlite3.Connection, provider_id: str) -> list:
    """Get all capabilities for a provider."""
    rows = conn.execute("""
        SELECT capability, certification_scheme, status
        FROM provider_capability
        WHERE provider_id = ?
    """, (provider_id,)).fetchall()
    return [{"capability": r[0], "scheme": r[1], "status": r[2]} for r in rows]

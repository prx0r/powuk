"""Base collector interface.

Every collector follows the same contract:
1. Fetch data from source
2. Store raw data (immutable, append-only)
3. Record health state
4. Return result

No domain logic. No constraint modeling. Just data acquisition.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class CollectorStatus(str, Enum):
    SUCCESS = "ok"
    SUCCESS_EMPTY = "ok_empty"
    PARTIAL = "partial"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class CollectorResult:
    """Standardized collector outcome."""
    status: CollectorStatus
    rows: int = 0
    bytes: int = 0
    source_timestamp: Optional[str] = None
    schema_hash: Optional[str] = None
    error: Optional[str] = None
    warnings: list = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


# ─── RAW STORAGE ─────────────────────────────────────────────

def store_raw(conn: sqlite3.Connection, source_id: str, data: bytes,
              ext: str = "json") -> dict:
    """Store raw data with content-hashed path. Append-only.
    
    Returns dict with storage metadata.
    """
    h = hashlib.sha256(data).hexdigest()[:16]
    now = datetime.now(timezone.utc)
    path_partition = now.strftime("%Y/%m/%d")
    
    # Auto-detect extension
    if ext == "auto":
        if data[:1] in (b"{", b"["):
            ext = "json"
        elif data[:2] == b"PK":
            ext = "xlsx"
        elif b"," in data[:100]:
            ext = "csv"
        else:
            ext = "bin"
    
    filename = f"{now.strftime('%H%M%S')}_{h}.{ext}"
    base = Path(__file__).parent.parent / "data" / "raw" / source_id / path_partition
    base.mkdir(parents=True, exist_ok=True)
    path = base / filename
    path.write_bytes(data)
    
    # Record in DB
    retrieval_id = f"{source_id}_{h}_{now.strftime('%H%M%S%f')}"
    conn.execute("""
        INSERT OR IGNORE INTO raw_blob (raw_hash, storage_path, bytes, first_seen)
        VALUES (?, ?, ?, ?)
    """, (h, str(path), len(data), now.isoformat()))
    conn.execute("""
        INSERT INTO raw_ingest (retrieval_id, source, dataset, raw_hash, observed_at, row_count, status)
        VALUES (?, ?, ?, ?, ?, ?, 'ok')
    """, (retrieval_id, source_id, source_id, h, now.isoformat(), None))
    conn.commit()
    
    return {
        "path": str(path),
        "hash": h,
        "bytes": len(data),
        "observed_at": now.isoformat(),
    }


def get_db(db_path: str = None) -> sqlite3.Connection:
    """Get database connection with Layer 1 schema."""
    if db_path is None:
        db_path = str(Path(__file__).parent.parent / "data" / "powuk.db")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
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
    """)
    conn.commit()
    return conn

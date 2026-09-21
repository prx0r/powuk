"""Base collector interface.

Every collector follows the same contract:
1. Fetch data from source
2. Store raw bytes (immutable, data/raw/)
3. Parse and store normalized records (data/normalized/)
4. Record coverage (expected vs collected)
5. Return result

No domain logic. No constraint modeling. Just data acquisition.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class CollectorStatus(str, Enum):
    SUCCESS = "success"
    SUCCESS_EMPTY = "success_empty"
    PARTIAL = "partial"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class CollectorResult:
    """Standardized collector outcome. Never infer status from row count."""
    status: CollectorStatus
    rows: int = 0
    artifacts: list = field(default_factory=list)
    cursor: Optional[str] = None
    warnings: list = field(default_factory=list)
    error: Optional[str] = None

    @staticmethod
    def success(rows=0, **kw):
        s = CollectorStatus.SUCCESS_EMPTY if rows == 0 else CollectorStatus.SUCCESS
        return CollectorResult(status=s, rows=rows, **kw)

    @staticmethod
    def partial(rows=0, **kw):
        return CollectorResult(status=CollectorStatus.PARTIAL, rows=rows, **kw)

    @staticmethod
    def failed(error, **kw):
        return CollectorResult(status=CollectorStatus.FAILED, error=str(error), **kw)

    @staticmethod
    def blocked(reason, **kw):
        return CollectorResult(status=CollectorStatus.BLOCKED, error=reason, **kw)


# ─── PATHS ───────────────────────────────────────────────────

BASE = Path(__file__).parent.parent
RAW_DIR = BASE / "data" / "raw"
NORM_DIR = BASE / "data" / "normalized"


# ─── RAW STORAGE ─────────────────────────────────────────────

def store_raw(source_id: str, data: bytes, ext: str = "auto") -> dict:
    """Store raw bytes from source. Immutable, content-hashed.
    
    Raw = bytes retrieved from source, period.
    Nothing derived enters data/raw/.
    """
    h = hashlib.sha256(data).hexdigest()[:16]
    now = datetime.now(timezone.utc)
    path_partition = now.strftime("%Y/%m/%d")
    
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
    base = RAW_DIR / source_id / path_partition
    base.mkdir(parents=True, exist_ok=True)
    path = base / filename
    path.write_bytes(data)
    
    return {
        "path": str(path),
        "hash": h,
        "bytes": len(data),
        "observed_at": now.isoformat(),
    }


# ─── NORMALIZED STORAGE ──────────────────────────────────────

def store_normalized(source_id: str, records: list[dict], fmt: str = "jsonl") -> dict:
    """Store normalized records. Append-only, source-faithful.
    
    Normalized = parsed, structured, queryable.
    Stored under data/normalized/, never data/raw/.
    """
    now = datetime.now(timezone.utc)
    path_partition = now.strftime("%Y/%m/%d")
    
    base = NORM_DIR / source_id / path_partition
    base.mkdir(parents=True, exist_ok=True)
    
    if fmt == "jsonl":
        filename = f"{now.strftime('%H%M%S')}.jsonl"
        path = base / filename
        with open(path, "w") as f:
            for record in records:
                f.write(json.dumps(record, default=str) + "\n")
        bytes_written = path.stat().st_size
    elif fmt == "json":
        filename = f"{now.strftime('%H%M%S')}.json"
        path = base / filename
        content = json.dumps(records, default=str).encode()
        path.write_bytes(content)
        bytes_written = len(content)
    else:
        raise ValueError(f"Unknown format: {fmt}")
    
    return {
        "path": str(path),
        "records": len(records),
        "bytes": bytes_written,
        "observed_at": now.isoformat(),
    }


# ─── COVERAGE ────────────────────────────────────────────────

def record_coverage(conn: sqlite3.Connection, source_id: str,
                    expected: int, collected: int, unique: int = None,
                    partition: str = "default"):
    """Record source coverage. The honesty metric.
    
    coverage_ratio = collected / expected
    If < 0.99, source is PARTIAL.
    """
    if unique is None:
        unique = collected
    ratio = collected / expected if expected > 0 else 0
    complete = ratio >= 0.99
    
    conn.execute("""
        INSERT OR REPLACE INTO source_coverage
        (source_id, partition, expected_count, collected_count, unique_count,
         coverage_ratio, complete, checked_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (source_id, partition, expected, collected, unique, ratio,
          complete, datetime.now(timezone.utc).isoformat()))
    conn.commit()


def get_coverage(conn: sqlite3.Connection, source_id: str = None) -> list[dict]:
    """Get coverage for one or all sources."""
    if source_id:
        rows = conn.execute(
            "SELECT * FROM source_coverage WHERE source_id=?", (source_id,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM source_coverage ORDER BY source_id").fetchall()
    
    cols = ["source_id", "partition", "expected_count", "collected_count",
            "unique_count", "coverage_ratio", "complete", "checked_at"]
    return [dict(zip(cols, r)) for r in rows]


# ─── OBSERVATIONS ────────────────────────────────────────────

def store_observation(conn: sqlite3.Connection, source: str, metric: str,
                      value, unit: str = None, event_time: str = None):
    """Store a single observation (monitoring metric, not economic data)."""
    ts = datetime.now(timezone.utc).isoformat()
    oid = hashlib.sha256(f"{source}:{metric}:{ts}:{value}".encode()).hexdigest()[:24]
    conn.execute("INSERT OR REPLACE INTO observation VALUES (?,?,?,?,?,?,?)",
                 (oid, source, metric, json.dumps(value, default=str), unit, event_time or ts, ts))
    conn.commit()


# ─── DB SCHEMA ───────────────────────────────────────────────

def get_db(db_path: str = None) -> sqlite3.Connection:
    """Get database connection with full Layer 1 schema."""
    if db_path is None:
        db_path = str(BASE / "data" / "powuk.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
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
    conn.commit()
    return conn

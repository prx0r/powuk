"""Database, observations, collector state, and watermarks.

Single implementation for all infrastructure. server.py and collectors
import from here, not from their own duplicates.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def get_db(db_path: str = None) -> sqlite3.Connection:
    """Get database connection with full schema."""
    if db_path is None:
        db_path = str(Path(__file__).parent.parent / "data" / "powuk.db")
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
        CREATE TABLE IF NOT EXISTS coverage_check (
            check_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            partition TEXT NOT NULL DEFAULT 'default',
            expected_count INT NOT NULL,
            collected_count INT NOT NULL,
            unique_count INT,
            coverage_ratio REAL NOT NULL,
            checked_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS normalized_partition (
            partition_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            record_count INT NOT NULL,
            storage_uri TEXT NOT NULL,
            content_hash TEXT,
            raw_retrieval_ids TEXT,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    return conn


def obs(conn: sqlite3.Connection, source: str, metric: str, value,
        unit: str = None, event_time: str = None):
    """Store a single observation."""
    ts = datetime.now(timezone.utc).isoformat()
    oid = hashlib.sha256(f"{source}:{metric}:{ts}:{value}".encode()).hexdigest()[:24]
    conn.execute("INSERT OR REPLACE INTO observation VALUES (?,?,?,?,?,?,?)",
                 (oid, source, metric, json.dumps(value, default=str), unit, event_time or ts, ts))
    conn.commit()


def state(conn: sqlite3.Connection, source: str, status: str,
          rows: int = None, interval: int = None):
    """Update collector state (last run, status, row count, run count)."""
    conn.execute("""INSERT INTO collector_state VALUES (?,?,?,?,?,1)
              ON CONFLICT(source) DO UPDATE SET last_run=excluded.last_run,
              status=excluded.status, rows=excluded.rows, runs=runs+1""",
              (source, datetime.now(timezone.utc).isoformat(), status, rows, interval))
    conn.commit()


def get_last_success(conn: sqlite3.Connection, source: str) -> Optional[str]:
    """Get last successful run time for a source (watermark for incremental fetch)."""
    row = conn.execute("SELECT last_run FROM collector_state WHERE source=?", (source,)).fetchone()
    return row[0] if row else None

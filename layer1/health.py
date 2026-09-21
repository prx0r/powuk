"""Standardized collector health state.

Every collector exposes the same health interface.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import json


@dataclass
class CollectorHealth:
    """Standardized health state for a collector.
    
    Every source exposes exactly these fields.
    """
    source_id: str
    last_attempt: Optional[str] = None
    last_success: Optional[str] = None
    records_seen: int = 0
    records_new: int = 0
    bytes: int = 0
    source_timestamp: Optional[str] = None  # freshest timestamp from source
    schema_hash: Optional[str] = None       # hash of the data schema
    error: Optional[str] = None
    status: str = "never_run"  # never_run, ok, ok_empty, partial, failed, blocked
    runs: int = 0

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "last_attempt": self.last_attempt,
            "last_success": self.last_success,
            "records_seen": self.records_seen,
            "records_new": self.records_new,
            "bytes": self.bytes,
            "source_timestamp": self.source_timestamp,
            "schema_hash": self.schema_hash,
            "error": self.error,
            "status": self.status,
            "runs": self.runs,
        }

    @staticmethod
    def from_dict(d: dict) -> CollectorHealth:
        return CollectorHealth(**{k: v for k, v in d.items() if k in CollectorHealth.__dataclass_fields__})

    def is_stale(self, max_staleness_hours: int = 48) -> bool:
        """Check if the source is stale."""
        if self.last_success is None:
            return True
        try:
            last = datetime.fromisoformat(self.last_success.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            hours = (now - last).total_seconds() / 3600
            return hours > max_staleness_hours
        except Exception:
            return True

    def health_label(self, max_staleness_hours: int = 48) -> str:
        """Human-readable health label."""
        if self.status == "never_run":
            return "NOT_RUN"
        if self.status in ("failed", "blocked"):
            return f"FAILED:{self.error}" if self.error else "FAILED"
        if self.is_stale(max_staleness_hours):
            return "STALE"
        return f"OK({self.status})"


class HealthRegistry:
    """Registry of health states for all collectors."""
    
    def __init__(self):
        self._health: dict[str, CollectorHealth] = {}
    
    def get(self, source_id: str) -> CollectorHealth:
        if source_id not in self._health:
            self._health[source_id] = CollectorHealth(source_id=source_id)
        return self._health[source_id]
    
    def update(self, source_id: str, **kw):
        """Update health state for a source."""
        h = self.get(source_id)
        for k, v in kw.items():
            if hasattr(h, k):
                setattr(h, k, v)
        h.last_attempt = datetime.now(timezone.utc).isoformat()
        h.runs += 1
    
    def record_success(self, source_id: str, records_new: int = 0,
                       records_seen: int = 0, bytes: int = 0,
                       source_timestamp: str = None, schema_hash: str = None):
        self.update(source_id,
                    status="ok" if records_new > 0 else "ok_empty",
                    last_success=datetime.now(timezone.utc).isoformat(),
                    records_new=records_new,
                    records_seen=records_seen,
                    bytes=bytes,
                    source_timestamp=source_timestamp,
                    schema_hash=schema_hash,
                    error=None)
    
    def record_failure(self, source_id: str, error: str):
        self.update(source_id, status="failed", error=error)
    
    def record_blocked(self, source_id: str, reason: str):
        self.update(source_id, status="blocked", error=reason)
    
    def record_partial(self, source_id: str, records_new: int = 0, error: str = None):
        self.update(source_id, status="partial", records_new=records_new, error=error)
    
    def summary(self, staleness_hours: int = 48) -> dict[str, str]:
        """Summary of all source health."""
        return {sid: h.health_label(staleness_hours) for sid, h in self._health.items()}
    
    def to_json(self) -> str:
        return json.dumps({sid: h.to_dict() for sid, h in self._health.items()}, indent=2)

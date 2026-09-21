"""Standardized source manifest.

Every source has a manifest. The manifest is the contract.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import yaml
from pathlib import Path


@dataclass
class SourceAuthority:
    """Who owns the data."""
    name: str            # e.g. "NESO", "ONS", "Companies House"
    url: str             # official homepage
    license: str = "ogl" # ogl, crown_copyright, local, etc.
    redistribution: str = "allowed"


@dataclass
class CollectionConfig:
    """How we collect."""
    cadence: str           # hourly, daily, 12h, 2h
    backfill_from: str = None  # earliest date, e.g. "2018-01-01"
    mode: str = "snapshot"     # snapshot, paginated, backfill, stream
    page_size: int = 100
    max_pages: int = 50


@dataclass
class StorageConfig:
    """How we store."""
    raw: bool = True
    append_only: bool = True
    format: str = "json"  # json, csv, xlsx, parquet


@dataclass
class TimeConfig:
    """Time semantics."""
    source_timestamp: bool = True  # does the data include its own timestamp?
    observed_at: bool = True       # do we record when we fetched it?


@dataclass
class HealthConfig:
    """Health thresholds."""
    expected_min_rows: int = 0
    max_staleness_hours: int = 48


@dataclass
class SourceManifest:
    """Complete manifest for a data source."""
    id: str
    garden: str  # "powuk"
    authority: SourceAuthority
    collection: CollectionConfig
    storage: StorageConfig
    time: TimeConfig
    health: HealthConfig
    url: str = None       # direct download/API URL
    format: str = "json"  # data format
    auth: str = "none"    # none, api_key, oauth
    notes: str = ""

    @staticmethod
    def from_yaml(path: str) -> SourceManifest:
        """Load manifest from YAML file."""
        data = yaml.safe_load(Path(path).read_text())
        return SourceManifest(
            id=data["id"],
            garden=data.get("garden", "powuk"),
            authority=SourceAuthority(**data["authority"]),
            collection=CollectionConfig(**data["collection"]),
            storage=StorageConfig(**data.get("storage", {})),
            time=TimeConfig(**data.get("time", {})),
            health=HealthConfig(**data.get("health", {})),
            url=data.get("url"),
            format=data.get("format", "json"),
            auth=data.get("auth", "none"),
            notes=data.get("notes", ""),
        )

    def to_yaml(self) -> str:
        """Serialize manifest to YAML."""
        data = {
            "id": self.id,
            "garden": self.garden,
            "authority": {
                "name": self.authority.name,
                "url": self.authority.url,
                "license": self.authority.license,
                "redistribution": self.authority.redistribution,
            },
            "collection": {
                "cadence": self.collection.cadence,
                "mode": self.collection.mode,
            },
            "storage": {
                "raw": self.storage.raw,
                "append_only": self.storage.append_only,
                "format": self.storage.format,
            },
            "time": {
                "source_timestamp": self.time.source_timestamp,
                "observed_at": self.time.observed_at,
            },
            "health": {
                "expected_min_rows": self.health.expected_min_rows,
                "max_staleness_hours": self.health.max_staleness_hours,
            },
        }
        if self.url:
            data["url"] = self.url
        if self.collection.backfill_from:
            data["collection"]["backfill_from"] = self.collection.backfill_from
        if self.auth != "none":
            data["auth"] = self.auth
        if self.notes:
            data["notes"] = self.notes
        return yaml.dump(data, default_flow_style=False, sort_keys=False)


def load_all_manifests(sources_dir: str = None) -> dict[str, SourceManifest]:
    """Load all source manifests from a directory."""
    if sources_dir is None:
        sources_dir = str(Path(__file__).parent / "sources")
    manifests = {}
    for path in Path(sources_dir).glob("*.yaml"):
        m = SourceManifest.from_yaml(str(path))
        manifests[m.id] = m
    return manifests

"""Standardized source manifest.

Every source has a manifest. The manifest is the contract.
This is the SINGLE SOURCE OF TRUTH for all source configuration.
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
class HistoryConfig:
    """History/backfill semantics."""
    type: str = "current_state_only"  # embedded_full_history, paginated_api, current_state_only
    earliest: str = None              # earliest available period, e.g. "2009", "2017-01"
    partition: str = "release"        # release, month, day
    snapshot_now: bool = False


@dataclass
class CoverageConfig:
    """Coverage tracking."""
    strategy: str = "auto"            # auto, manual, api_total
    expected_count: int = None        # known total from source (e.g. Ofqual 52887)
    minimum_ratio: float = 0.99       # below this → PARTIAL


@dataclass
class AuthConfig:
    """Authentication."""
    type: str = "none"        # none, api_key, basic, oauth
    env_var: str = None       # environment variable name for the key


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

    # Extended fields (from config/sources.yaml)
    domain: str = ""           # grid, trades, planning, procurement, business, training, labour, certification
    priority: str = "P0"       # P0, P1, P2
    stage: str = "discovery"   # discovery, raw, normalized, monitored, verified, aggregate_only
    recoverability: str = "snapshot"  # canonical, snapshot, aggregate_only
    rights: str = "ogl"        # ogl, crown_copyright, local
    source_file: str = None    # legacy local file path (if applicable)
    sic_clusters: dict = None  # SIC code clusters (for Companies House)
    history: HistoryConfig = None
    coverage: CoverageConfig = None
    auth_config: AuthConfig = None

    def __post_init__(self):
        if self.history is None:
            self.history = HistoryConfig()
        if self.coverage is None:
            self.coverage = CoverageConfig()
        if self.auth_config is None:
            self.auth_config = AuthConfig(type=self.auth)

    @staticmethod
    def from_yaml(path: str) -> SourceManifest:
        """Load manifest from YAML file."""
        data = yaml.safe_load(Path(path).read_text())

        history_data = data.get("history", {})
        history = HistoryConfig(**history_data) if history_data else HistoryConfig()

        coverage_data = data.get("coverage", {})
        coverage = CoverageConfig(**coverage_data) if coverage_data else CoverageConfig()

        auth_data = data.get("auth_config", {})
        auth_config = AuthConfig(**auth_data) if auth_data else AuthConfig(type=data.get("auth", "none"))

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
            domain=data.get("domain", ""),
            priority=data.get("priority", "P0"),
            stage=data.get("stage", "discovery"),
            recoverability=data.get("recoverability", "snapshot"),
            rights=data.get("rights", "ogl"),
            source_file=data.get("source_file"),
            sic_clusters=data.get("sic_clusters"),
            history=history,
            coverage=coverage,
            auth_config=auth_config,
        )

    def to_yaml(self) -> str:
        """Serialize manifest to YAML."""
        data = {
            "id": self.id,
            "garden": self.garden,
            "domain": self.domain,
            "priority": self.priority,
            "stage": self.stage,
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
            "recoverability": self.recoverability,
            "rights": self.rights,
        }
        if self.url:
            data["url"] = self.url
        if self.collection.backfill_from:
            data["collection"]["backfill_from"] = self.collection.backfill_from
        if self.collection.page_size != 100:
            data["collection"]["page_size"] = self.collection.page_size
        if self.collection.max_pages != 50:
            data["collection"]["max_pages"] = self.collection.max_pages
        if self.auth != "none":
            data["auth"] = self.auth
        if self.source_file:
            data["source_file"] = self.source_file
        if self.sic_clusters:
            data["sic_clusters"] = self.sic_clusters
        if self.history.type != "current_state_only":
            data["history"] = {
                "type": self.history.type,
            }
            if self.history.earliest:
                data["history"]["earliest"] = self.history.earliest
            if self.history.partition:
                data["history"]["partition"] = self.history.partition
        if self.coverage.expected_count:
            data["coverage"] = {
                "strategy": self.coverage.strategy,
                "expected_count": self.coverage.expected_count,
                "minimum_ratio": self.coverage.minimum_ratio,
            }
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

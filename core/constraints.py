"""Canonical constraint types for powuk."""
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class ConstraintType(Enum):
    GRID_HEADROOM = "grid_headroom"
    GRID_QUEUE = "grid_queue"
    TRADE_CAPACITY = "trade_capacity"
    PARTS_AVAILABILITY = "parts_availability"
    PLANNING_BACKLOG = "planning_backlog"
    INFRASTRUCTURE = "infrastructure"


class Severity(Enum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass(frozen=True)
class Region:
    """UK region with GSP/DNO identity."""
    code: str          # e.g. "GSP-10", "DNO-London"
    name: str
    lat: float
    lon: float


@dataclass(frozen=True)
class Constraint:
    """A measured physical constraint at a point in time."""
    constraint_id: str
    constraint_type: ConstraintType
    region: Region
    measured_at: datetime
    demand_value: Optional[float] = None
    supply_value: Optional[float] = None
    severity: Severity = Severity.NONE
    source: str = ""
    evidence_url: str = ""
    notes: str = ""

    @property
    def gap(self) -> Optional[float]:
        if self.demand_value is not None and self.supply_value is not None:
            return self.demand_value - self.supply_value
        return None


@dataclass(frozen=True)
class TradeProfile:
    """Installer/repairer capacity in a region."""
    trade: str              # electrician, solar_installer, heat_pump, etc.
    region: Region
    active_count: int       # known active tradespeople
    demand_signal: float    # job postings, enquiries, etc.
    qualification_rate: float  # fraction with required certs
    measured_at: datetime


@dataclass(frozen=True)
class Opportunity:
    """Where demand exceeds supply."""
    opportunity_id: str
    constraint: Constraint
    trade_profile: Optional[TradeProfile]
    gap_magnitude: float
    urgency: Severity
    detected_at: datetime
    description: str
    action: str  # what could be done

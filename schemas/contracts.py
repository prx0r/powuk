"""Reference-only shared POW contracts.

Keep this package tiny. Domain tables belong to each garden.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

class TruthClass(str, Enum):
    VERIFIED = "verified"
    DERIVED = "derived"
    ESTIMATED = "estimated"
    HEURISTIC = "heuristic"
    CONCEPTUAL = "conceptual"
    UNAVAILABLE = "unavailable"

class Recoverability(str, Enum):
    CANONICAL = "canonical"
    THIRD_PARTY = "third_party"
    PARTIAL = "partial"
    EPHEMERAL = "ephemeral"

class DataRights(str, Enum):
    OPEN_REPUBLISH = "open_republish"
    ATTRIBUTION = "attribution"
    INTERNAL_ONLY = "internal_only"
    DERIVED_INTERNAL_ONLY = "derived_internal_only"
    DERIVED_PUBLISHABLE = "derived_publishable"
    LICENSE_REQUIRED = "license_required"
    UNKNOWN = "unknown"

@dataclass
class Observation:
    observation_id: str
    garden: str
    entity_id: str
    metric: str
    value: Any
    event_time: str
    observed_at: str
    source_id: str
    unit: str = ""
    truth_class: str = TruthClass.VERIFIED.value
    recoverability: str = Recoverability.THIRD_PARTY.value
    rights: str = DataRights.UNKNOWN.value
    source_version: str = ""
    raw_payload_hash: str = ""
    parent_observation_ids: list[str] = field(default_factory=list)
    method_id: str = ""
    method_version: str = ""
    tags: dict = field(default_factory=dict)

@dataclass
class DerivedFact:
    derived_id: str
    garden: str
    entity_id: str
    metric: str
    value: Any
    computed_at: str
    method_id: str
    method_version: str
    input_observation_ids: list[str]
    unit: str = ""
    confidence: float = 0.0
    truth_class: str = TruthClass.DERIVED.value
    rights: str = DataRights.UNKNOWN.value
    valid_from: str = ""
    valid_to: str = ""
    limitations: list[str] = field(default_factory=list)

@dataclass
class EconomicEvent:
    event_id: str
    garden: str
    event_type: str
    observed_at: str
    entity_ids: list[str]
    effective_at: str = ""
    direction: Optional[str] = None
    magnitude: Optional[float] = None
    confidence: float = 1.0
    source_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    rights: str = DataRights.UNKNOWN.value
    tags: dict = field(default_factory=dict)

@dataclass
class Relationship:
    relationship_id: str
    subject_entity_id: str
    predicate: str
    object_entity_id: str
    observed_at: str
    source_ids: list[str]
    valid_from: str = ""
    valid_to: str = ""
    confidence: float = 1.0
    rights: str = DataRights.UNKNOWN.value
    attributes: dict = field(default_factory=dict)

@dataclass
class DecisionSpec:
    id: str
    version: str
    primitive: str  # noul | choice | score
    question: str
    allowed_outputs: list[str] = field(default_factory=list)
    confidence_threshold: float = 0.5
    fallback: str = "UNKNOWN"
    consequence: str = "LOW"
    eval_set: str = ""

"""Layer 2 — UK Constraint Model.

Imports UK types from core/ and computes constraint severity.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.constraints import (
    Constraint, ConstraintType, Severity, Region, TradeProfile
)
from core.regions import get_all_regions, REGIONS

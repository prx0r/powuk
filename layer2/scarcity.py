"""UK scarcity compiler.

Takes Layer 1 observations → produces Layer 2 constraint derivations.
"""
from datetime import datetime
from typing import Optional
from core.constraints import (
    Constraint, ConstraintType, Severity, Region, TradeProfile
)


def compute_severity(demand: Optional[float], supply: Optional[float]) -> Severity:
    """Map demand/supply gap to severity."""
    if demand is None or supply is None:
        return Severity.NONE
    if supply <= 0:
        return Severity.CRITICAL
    ratio = demand / supply
    if ratio > 3.0:
        return Severity.CRITICAL
    elif ratio > 2.0:
        return Severity.HIGH
    elif ratio > 1.5:
        return Severity.MEDIUM
    elif ratio > 1.0:
        return Severity.LOW
    return Severity.NONE


def compile_grid_constraint(
    region: Region,
    demand_mw: Optional[float],
    capacity_mw: Optional[float],
    queue_count: Optional[int],
    ts: Optional[datetime] = None,
) -> list[Constraint]:
    """Compile grid constraints for a region."""
    ts = ts or datetime.utcnow()
    constraints = []

    if demand_mw is not None and capacity_mw is not None:
        severity = compute_severity(demand_mw, capacity_mw)
        constraints.append(Constraint(
            constraint_id=f"GRID-HEADROOM-{region.code}-{ts.strftime('%Y%m%d')}",
            constraint_type=ConstraintType.GRID_HEADROOM,
            region=region,
            measured_at=ts,
            demand_value=demand_mw,
            supply_value=capacity_mw,
            severity=severity,
            source="national_grid_eso",
        ))

    if queue_count is not None:
        severity = compute_severity(float(queue_count), 10.0)
        constraints.append(Constraint(
            constraint_id=f"GRID-QUEUE-{region.code}-{ts.strftime('%Y%m%d')}",
            constraint_type=ConstraintType.GRID_QUEUE,
            region=region,
            measured_at=ts,
            demand_value=float(queue_count),
            supply_value=10.0,
            severity=severity,
            source="gso_queue",
        ))

    return constraints


def compile_trade_constraint(
    region: Region,
    trade: str,
    active_count: int,
    job_postings: Optional[float],
    ts: Optional[datetime] = None,
) -> Optional[Constraint]:
    """Compile trade capacity constraint for a region."""
    ts = ts or datetime.utcnow()
    severity = compute_severity(job_postings, float(active_count) if active_count else None)

    return Constraint(
        constraint_id=f"TRADE-{trade.upper()}-{region.code}-{ts.strftime('%Y%m%d')}",
        constraint_type=ConstraintType.TRADE_CAPACITY,
        region=region,
        measured_at=ts,
        demand_value=job_postings,
        supply_value=float(active_count),
        severity=severity,
        source="checkatrade+indeed",
        notes=f"{trade} in {region.name}",
    )


def compile_scarcity_view(
    regions: list[Region],
    grid_data: dict,
    trade_data: dict,
) -> dict:
    """Produce the full scarcity view."""
    view = {}
    ts = datetime.utcnow()

    for region in regions:
        region_constraints = []

        gsp = grid_data.get(region.code, {})
        if gsp:
            region_constraints.extend(compile_grid_constraint(
                region=region,
                demand_mw=gsp.get("demand_mw"),
                capacity_mw=gsp.get("capacity_mw"),
                queue_count=gsp.get("queue_count"),
                ts=ts,
            ))

        trades = trade_data.get(region.code, {})
        for trade_name, trade_info in trades.items():
            tc = compile_trade_constraint(
                region=region,
                trade=trade_name,
                active_count=trade_info.get("active_count", 0),
                job_postings=trade_info.get("job_postings"),
                ts=ts,
            )
            if tc:
                region_constraints.append(tc)

        if region_constraints:
            max_severity = max(c.severity.value for c in region_constraints)
            avg_severity = sum(c.severity.value for c in region_constraints) / len(region_constraints)
        else:
            max_severity = 0
            avg_severity = 0

        view[region.code] = {
            "region": region,
            "constraints": region_constraints,
            "constraint_count": len(region_constraints),
            "max_severity": Severity(max_severity),
            "avg_severity": round(avg_severity, 2),
            "compiled_at": ts,
        }

    return view

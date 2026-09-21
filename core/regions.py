"""UK regions with GSP/DNO identity."""
from .constraints import Region

# GSP (Grid Supply Point) regions — these are the real constraint boundaries
# Each GSP serves a geographic area with measurable demand/capacity
REGIONS = {
    # Distribution Network Operator areas (approximate centroids)
    "UKPN-London": Region("UKPN-London", "London (UK Power Networks)", 51.5074, -0.1278),
    "UKPN-East": Region("UKPN-East", "East of England (UKPN)", 52.2053, 1.0300),
    "UKPN-SouthEast": Region("UKPN-SouthEast", "South East (UKPN)", 51.2694, -0.6386),
    "WPD-SouthWest": Region("WPD-SouthWest", "South West (Western Power)", 50.7184, -3.5339),
    "WPD-Midlands": Region("WPD-Midlands", "West Midlands (Western Power)", 52.4862, -1.8904),
    "WPD-EastMidlands": Region("WPD-EastMidlands", "East Midlands (Western Power)", 52.8300, -1.1500),
    "ENW-NorthWest": Region("ENW-NorthWest", "North West (Electricity North West)", 53.4808, -2.2426),
    "ENW-NorthEast": Region("ENW-NorthEast", "North East (Electricity North West)", 54.9783, -1.6178),
    "SPEN-South": Region("SPEN-South", "Central & Southern Scotland (SP Energy)", 55.8642, -4.2518),
    "SPEN-North": Region("SPEN-North", "North Scotland (SP Energy)", 57.4778, -4.2247),
    "NIE-Northern": Region("NIE-Northern", "Northern Ireland (NIE Networks)", 54.5973, -5.9301),
    "ERDF-France": Region("ERDF-France", "Cross-channel (IFA)", 51.0833, 1.5667),  # interconnector
}

# Quick access by DNO group
DNO_GROUPS = {
    "UKPN": ["UKPN-London", "UKPN-East", "UKPN-SouthEast"],
    "WPD": ["WPD-SouthWest", "WPD-Midlands", "WPD-EastMidlands"],
    "ENW": ["ENW-NorthWest", "ENW-NorthEast"],
    "SPEN": ["SPEN-South", "SPEN-North"],
    "NIE": ["NIE-Northern"],
}


def get_regions_by_dno(dno: str) -> list[Region]:
    """Get all regions for a DNO."""
    codes = DNO_GROUPS.get(dno, [])
    return [REGIONS[c] for c in codes if c in REGIONS]


def get_all_regions() -> list[Region]:
    """Get all UK regions."""
    return list(REGIONS.values())

# Canonical cross-system edges

Recommended predicates:

## Physical ↔ UK
- `repair_task REQUIRES_OCCUPATION occupation`
- `repair_task REQUIRES_SKILL skill`
- `component INSTALLED_BY occupation`
- `device SERVICED_BY occupation`

## Physical ↔ Grid
- `device CONSUMES_ELECTRICITY`
- `component USED_IN grid_asset`
- `component REQUIRED_FOR reinforcement_project`

## Physical ↔ Capital
- `company MANUFACTURES component`
- `company DISTRIBUTES component`
- `company CONSUMES component`
- `company SELLS device`
- `company OPERATES facility`

## UK ↔ Grid
- `grid_project REQUIRES_OCCUPATION occupation`
- `grid_asset LOCATED_IN place`

## Capital ↔ everything
- `company EXPOSED_TO resource`
- `company OPERATES_IN place`
- `security REPRESENTS company`

## Frontier
- `hypothesis PREDICTS_PRESSURE_ON resource`
- `hypothesis PREDICTS_DEMAND_FOR component`
- `hypothesis PREDICTS_CAPACITY_RESPONSE_IN domain`

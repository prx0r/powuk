# Companies House — POWUK source spec

> Measure the formation, destruction and financing of UK physical-service capacity relevant to POW.

Not "collect UK companies."

---

## SIC CLUSTERS (50-100 codes)

### Electrical
- 43210 — Electrical installation
- 43290 — Other construction installation
- 33140 — Repair of electrical equipment
- 27110 — Manufacture of electric motors, generators
- 27200 — Manufacture of batteries
- 27900 — Manufacture of other electrical equipment
- 46520 — Wholesale of electronic/electrical parts

### HVAC / Plumbing / Heating
- 43220 — Plumbing, heat and air-conditioning installation
- 43290 — Other construction installation
- 43910 — Roofing activities (solar mounting)

### Solar / Renewables / Energy
- 35110 — Production of electricity
- 35140 — Trade of electricity
- 43910 — Roofing (solar panel mounting)
- 43210 — Electrical (solar wiring)
- 28110 — Manufacture of engines/turbines (wind)

### EV Charging / Transport
- 43210 — Electrical (charger installation)
- 45200 — Maintenance/repair of motor vehicles
- 49320 — Taxi operation (EV transition)

### Telecommunications / Data Infrastructure
- 61100 — Wired telecommunications
- 61200 — Wireless telecommunications
- 61900 — Other telecommunications
- 62011 — Software development
- 62090 — Other IT services
- 63110 — Data processing, hosting

### Electronics / Computer Repair
- 95110 — Repair/maintenance of computers
- 95210 — Repair/maintenance of consumer electronics
- 95290 — Repair of other electrical equipment

### Industrial / Machinery
- 33120 — Repair of machinery
- 33200 — Installation of industrial machinery
- 43999 — Other construction installation

### Construction (physical infrastructure)
- 41100 — Development of building projects
- 41202 — Construction of domestic buildings
- 42990 — Other civil engineering
- 43999 — Other construction installation

---

## THE FIVE MEASUREMENTS

### 1. FIRM STOCK
How many relevant incorporated firms exist?
```
active_firms = count(companies WHERE sic IN pow_sics AND status = 'active')
```

### 2. CAPACITY FORMATION
How many are being created?
```
new_firms_1d = formations in last 24h
new_firms_30d = formations in last 30 days
new_firms_365d = formations in last 365 days
```

### 3. CAPACITY DESTRUCTION
How many dissolve / enter insolvency?
```
dissolved_1d = dissolutions in last 24h
dissolved_30d = dissolutions in last 30 days
insolvencies_30d = insolvency events in last 30 days
```

### 4. CAPITAL RESPONSE
Are these firms taking secured finance?
```
new_charges_30d = new charges registered in last 30 days
charge_value_30d = total value of new charges
```

### 5. CAPACITY MIGRATION
Are companies changing SIC/location into these sectors?
```
sic_changes_30d = companies switching TO pow_sics
region_migrations_30d = companies moving INTO region
```

---

## OUTPUT TABLE

```
powuk_company_capacity_daily
├── date
├── sic_cluster (electrical, hvac, solar, ev, telecom, repair, industrial, construction)
├── postcode_area (B, BT, C, CM, etc.)
├── active_firms
├── new_firms_1d
├── new_firms_30d
├── new_firms_365d
├── dissolved_1d
├── dissolved_30d
├── insolvencies_30d
├── new_charges_30d
├── net_firm_growth_30d (= new_firms_30d - dissolved_30d)
├── formation_acceleration (= new_firms_30d / new_firms_365d_per_month)
├── failure_acceleration (= dissolved_30d / dissolved_365d_per_month)
├── capital_acceleration (= new_charges_30d / charges_365d_per_month)
```

---

## CAPACITY-RESPONSE RATIO

```
capacity_response = growth_in_firms / growth_in_demand_signals
```

Where demand signals come from:
- Job postings (ONS/Indeed)
- Planning applications
- Procurement contracts
- Search activity

Interpretation:
- demand ↑↑↑ / firms ↑ = CONSTRAINT TIGHTENING
- demand ↑ / firms ↑↑↑ = supply responding, opportunity narrowing
- demand ↓ / firms ↑↑ = overcapacity forming

---

## LEGISLATION RESPONSE TRACKING

When legislation changes, watch the chain:
```
t0 legislation introduced
t1 job postings change
t2 procurement appears
t3 company formations change
t4 secured financing changes
t5 capacity catches demand
```

After accumulating data:
```
median UK electrician supply response = X months
median HVAC business formation response = Y months
solar installation capacity responds in Z months
```

This historical response function becomes impossible to recreate later.

---

## WHAT WE COLLECT (brutally narrow)

### Daily (from streaming API)
- Company formations (SIC in pow_sics)
- Company dissolutions (SIC in pow_sics)
- Insolvency events (SIC in pow_sics)
- New charges (SIC in pow_sics)

### Monthly (from bulk CSV)
- Full firm stock by SIC × postcode area
- Net growth calculation
- Acceleration metrics

### NOT COLLECTED (yet)
- Director networks
- PSC graphs
- Virtual office detection
- Acquisition detection
- Generic company data

---

*This spec should be the source of truth for the Companies House collector.*

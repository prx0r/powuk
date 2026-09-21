# powuk source registry

> Every data source we collect from, what it is, and why it matters.
> Sources mined from powpowpow email zips are marked with [ZIP].

---

## GRID — Where is demand outstripping capacity?

### NESO Demand (live) ✓ collecting
- **Source:** National Grid ESO Open Data Portal
- **URL:** `https://api.neso.energy/dataset/7a12172a-939c-404c-b581-a6128b74f588/resource/177f6fa4-ae49-4182-81ea-0c6b35f26ca6/download/demanddataupdate.csv`
- **Format:** CSV, half-hourly
- **Auth:** None
- **Cadence:** Daily (updates by 08:30 UTC)
- **What it is:** UK system demand (ND), total system demand (TSD), England/Wales demand, embedded wind/solar generation, interconnector flows (IFA, IFA2, BritNed, Moyle, NEMO, Viking, Greenlink)
- **Columns:** SETTLEMENT_DATE, SETTLEMENT_PERIOD, ND, FORECAST_ACTUAL_INDICATOR, TSD, ENGLAND_WALES_DEMAND, EMBEDDED_WIND_GENERATION, EMBEDDED_WIND_CAPACITY, EMBEDDED_SOLAR_GENERATION, EMBEDDED_SOLAR_CAPACITY, NON_BM_STOR, PUMP_STORAGE_PUMPING, SCOTTISH_TRANSFER, IFA_FLOW, IFA2_FLOW, BRITNED_FLOW, MOYLE_FLOW, EAST_WEST_FLOW, NEMO_FLOW, NSL_FLOW, ELECLINK_FLOW, VIKING_FLOW, GREENLINK_FLOW
- **Why it matters:** High demand + low generation = grid stress. Embedded solar/wind reducing TSD means less headroom for new connections.
- **Constraint signal:** ND > 50GW or TSD approaching capacity limits

### NESO Generation Mix (live)
- **Source:** National Grid ESO Open Data Portal
- **URL:** `https://api.neso.energy/dataset/88313ae5-94e4-4ddc-a790-593554d8c6b9/resource/f93d1835-75bc-43e5-84ad-12472b180a98/download/df_fuel_ckan.csv`
- **Format:** CSV, half-hourly
- **Auth:** None
- **Cadence:** Daily
- **What it is:** UK generation by fuel type from 2009 to present. Gas, coal, nuclear, wind (onshore+offshore), embedded wind, hydro, imports, biomass, solar, storage.
- **Columns:** DATETIME, GAS, COAL, NUCLEAR, WIND, WIND_EMB, HYDRO, IMPORTS, BIOMASS, OTHER, SOLAR, STORAGE, GENERATION, CARBON_INTENSITY, LOW_CARBON, ZERO_CARBON, RENEWABLE, FOSSIL, plus percentage columns
- **Why it matters:** Renewable intermittency creates grid constraints. When wind drops, gas fills the gap, constraints appear. Solar peak creates export constraints at local level.
- **Constraint signal:** High renewable % = more grid flexibility needed. Low wind + high demand = constraint cost spike.

### PV Live (live)
- **Source:** Sheffield Solar / PV Live API
- **URL:** `https://api.pvlive.uk/pvlive/api/v4/gsp/0?data_format=json`
- **Format:** JSON
- **Auth:** None
- **Cadence:** Near real-time (hourly)
- **What it is:** Actual UK solar PV generation at GSP (Grid Supply Point) level. GSP 0 = whole UK.
- **Why it matters:** Embedded solar reduces network demand during day but creates export constraints at local level. When solar output is high, local DNO headroom shrinks.
- **Constraint signal:** Solar output approaching installed capacity = local export constraint

### UKPN Open Data (daily)
- **Source:** UK Power Networks Open Data Portal
- **URL:** `https://ukpowernetworks.opendatasoft.com/`
- **Format:** JSON (CKAN API)
- **Auth:** Portal registration for some datasets
- **Cadence:** Daily
- **What it is:** DNO flexibility dispatches, embedded capacity register, network headroom, future constraint forecasts. UKPN covers London, South East, East of England.
- **Why it matters:** UKPN is the largest DNO by customers. Their flexibility dispatch data shows where constraints are actively being managed. Embedded capacity shows how much generation/storage is connected locally.
- **Constraint signal:** High flexibility dispatch volume = active constraints. Low headroom = connection queue bottleneck.

### NESO TEC Register (12h)
- **Source:** National Grid ESO
- **URL:** `https://api.neso.energy/api/3/action/datapackage_show?id=transmission-entry-capacity-tec-register`
- **Format:** CSV via CKAN
- **Auth:** None
- **Cadence:** Twice weekly
- **What it is:** Forward contracted transmission entry capacity. Who has booked connection capacity, how much, where.
- **Why it matters:** Shows where future capacity is already committed. If TEC is high but actual connections are low, there's a queue. If TEC is low but applications are high, there's a bottleneck.
- **Constraint signal:** TEC > actual connections = queue backlog

---

## TRADES — Are there enough people?

### EvSpark Business Evidence (daily)
- **Source:** Local file from `/root/ab/businesses/evspark/receipts/ch_sweep_areas.csv`
- **Format:** CSV
- **Auth:** N/A (local)
- **Cadence:** Daily
- **What it is:** Electrical, plumbing/heating, and landlord business counts by UK postcode area. 127 areas. Includes new businesses (2024-26) and dissolved businesses (2023+).
- **Columns:** area, electrical, elec_new_24_26, elec_dissolved_23plus, plumbing_heat, landlords
- **Why it matters:** Supply side of trade constraints. Areas with few electricians but high housing/EV growth = trade shortage.
- **Constraint signal:** Low electrical count + high landlord count = EV charger installation bottleneck

---

## PLANNING — Where is demand appearing?

### Planning Applications (2h)
- **Source:** Planning Data API
- **URL:** `https://www.planning.data.gov.uk/entity.json?dataset=planning-application&limit=100`
- **Format:** JSON
- **Auth:** None
- **Cadence:** Near real-time
- **What it is:** England planning applications. Reference, status, description, location, decision date.
- **Why it matters:** Planning applications signal where development is happening. High application volume in an area = future infrastructure demand (grid connections, EV chargers, solar installs).
- **Constraint signal:** High applications + low grid capacity = connection bottleneck

### Contracts Finder (2h)
- **Source:** Contracts Finder
- **URL:** `https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search?limit=100`
- **Format:** JSON (OCDS)
- **Auth:** None
- **Cadence:** Near real-time
- **What it is:** UK public procurement notices in Open Contracting Data Standard. Tender notices, contract awards, modifications.
- **Why it matters:** Public procurement signals where government is buying capacity. Energy infrastructure contracts, EV charger installations, building retrofits = future demand for trades and parts.
- **Constraint signal:** High procurement value + low trade supply = capacity gap

---

## PENDING SOURCES (need auth/setup)

### Companies House API
- **URL:** `https://api.company-information.service.gov.uk/`
- **Auth:** API key (free)
- **What:** UK company registrations, SIC codes, officers
- **Use:** Count businesses by trade × region

### ELEXON BMRS
- **URL:** `https://data.elexon.co.uk/bmrs/api/v1`
- **Auth:** None (but new API)
- **What:** Balancing mechanism, system prices, frequency
- **Use:** Real-time grid stress indicators

### Skills England
- **URL:** `https://occupational-maps-api.skillsengland.education.gov.uk/api/v1/`
- **Auth:** Unknown (403 currently)
- **What:** Occupational maps, skills, qualifications
- **Use:** Map trades to skills to training capacity

### ONS Labour Demand
- **URL:** `https://www.ons.gov.uk/employmentandlabourmarket/.../labourdemandvolumesby...`
- **Auth:** None
- **What:** Online job advert volumes by SOC2020 × local authority
- **Use:** Demand side of trade constraints

### Find a Tender
- **URL:** `https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages`
- **Auth:** None
- **What:** Higher-value UK procurement notices
- **Use:** Infrastructure procurement signals

---

## EXTRACTED DATA (from emails, already on disk)

### Constraint Surface
- **Source:** `/root/powpowpow/extracted/zip_1_constraint_surface/`
- **What:** UK constraint candidates — EV PDR reform, water abstraction, regulatory changes
- **Format:** JSONL candidates + source ledger + state

### Market Graph
- **Source:** `/root/powpowpow/extracted/zip_1_marketgraph/`
- **What:** UK market signals — business activity, pricing, availability
- **Format:** JSONL candidates + source ledger

### Want Graph
- **Source:** `/root/powpowpow/extracted/zip_1_WantGraph/`
- **What:** Consumer intent from Reddit — what people want to buy/do
- **Format:** JSONL candidates + source ledger

### Friction Graph
- **Source:** `/root/powpowpow/extracted/zip_1_frictiongraph_all_reports/`
- **What:** Market friction/entropy signals — where things are hard to get/do
- **Format:** JSONL candidates + source ledger

---

## HOW WE USE IT

```
Grid demand (neso_demand)
    + Grid supply (neso_generation + pvlive)
    = Grid constraint severity

Trade supply (evspark_trades)
    + Trade demand (planning_apps + contracts_finder)
    = Trade constraint severity

Each region × constraint type → severity score → opportunity
```

The severity formula:
```
demand / supply ratio:
  > 3.0 = CRITICAL (4)
  > 2.0 = HIGH (3)
  > 1.5 = MEDIUM (2)
  > 1.0 = LOW (1)
  ≤ 1.0 = NONE (0)
```

---

## NEW SOURCES (mined from powpowpow zips)

### Labour / Skills (P0 — from pow-scarcity-lab SOURCE_MATRIX)

#### ONS Labour Demand by SOC × LAD
- **URL:** `https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/datasets/labourdemandvolumesbystandardoccupationclassificationsoc2020uk`
- **Format:** XLSX (historical files)
- **Auth:** None
- **Cadence:** Monthly
- **What:** Online job advert volumes by SOC2020 occupation × local authority district
- **Why:** Demand side of trade constraints — where are electricians/solar installers being hired?

#### Skills England Occupational Maps API
- **URL:** `https://occupational-maps-api.skillsengland.education.gov.uk/api/v1/`
- **Format:** JSON API
- **Auth:** None (currently 403 — may need registration)
- **What:** Occupation → SOC code → duties → knowledge/skills/behaviours → training products
- **Why:** Maps trades to required skills and training capacity

#### Apprenticeship Display Advert API
- **URL:** `https://api.apprenticeships.education.gov.uk/vacancies`
- **Format:** JSON API (v2)
- **Auth:** API key required
- **What:** Live apprenticeship vacancies by trade, location, level
- **Why:** Training pipeline — how many new electricians/solar installers are being trained?

#### DfE Apprenticeships Statistics
- **URL:** `https://explore-education-statistics.service.gov.uk/find-statistics/apprenticeships/2025-26/explore`
- **Format:** CSV/XLSX
- **Auth:** None
- **What:** Starts, achievements, participation by geography, level, subject
- **Why:** Historical training output — how many qualified people enter the workforce each year?

#### Ofqual Register
- **URL:** `https://register-api.ofqual.gov.uk`
- **Format:** JSON API
- **Auth:** None
- **What:** Qualification number, title, level, awarding org, operational dates
- **Why:** What qualifications exist for each trade, which are active?

### Component Supply (P0 — from pow-scarcity-lab + POW_SYSTEMS)

#### Nexar / Octopart
- **URL:** `https://api.nexar.com/graphql`
- **Format:** GraphQL
- **Auth:** OAuth
- **What:** Component supply chain — stock, price, lead time, lifecycle, sellers
- **Why:** Multi-distributor divergence = physical constraint signal

#### DigiKey Product Information API
- **URL:** `https://developer.digikey.com/products/product-information-v4`
- **Format:** JSON API
- **Auth:** OAuth
- **What:** Stock/availability, price, substitutions, product change notifications
- **Why:** Real-time component availability

#### Mouser Search API
- **URL:** `https://www.mouser.com/api/v2/search/partnumber`
- **Format:** JSON API
- **Auth:** API key
- **What:** Availability, lead time, lifecycle, price breaks
- **Why:** Cross-reference with DigiKey for constraint detection

#### Farnell / element14
- **URL:** `https://partner.element14.com/Search_API`
- **Format:** JSON API
- **Auth:** API key
- **What:** UK store stock/pricing
- **Why:** UK-specific component availability

### Physical Repair (P1 — from POW_SYSTEMS pow_physical)

#### OPSS Product Recalls
- **URL:** `https://www.gov.uk/product-safety-alerts-reports-recalls`
- **Format:** Web/feed
- **Auth:** None
- **What:** Product safety alerts, recalls by category/brand/model
- **Why:** Failure frequency data — which products break and why?

#### France Durability Index
- **URL:** `https://schema.data.gouv.fr/etalab/schema-indice-durabilite/`
- **Format:** Open data
- **Auth:** None
- **What:** Repairability score, reliability, spare-part classes, disassembly info
- **Why:** European repairability benchmark — what's fixable?

#### EPREL (EU Energy Products)
- **URL:** `https://energy-efficient-products.ec.europa.eu/eprel_en`
- **Format:** Public search/export
- **Auth:** None
- **What:** Registration, supplier/manufacturer, model, energy parameters, repairability
- **Why:** EU product database with repair/spare-part data

### EV Charger Product Data (from marketgraph zip)

#### Electric Point
- **URL:** `https://www.electricpoint.com/`
- **What:** EV charging cables, connectors, accessories
- **Why:** UK EV charger product availability and pricing

#### EV-Cables UK
- **URL:** `https://ev-cables.co.uk/`
- **What:** EV charging cables by type/phase/length
- **Why:** UK EV cable supply chain

#### Arnold Clark Autoparts
- **URL:** `https://www.arnoldclarkautoparts.com/`
- **What:** EV charging cables, automotive parts
- **Why:** UK automotive parts availability

### Research / Innovation (P0 — from pow-scarcity-lab)

#### EPO Open Patent Services
- **URL:** `https://ops.epo.org/3.2/rest-services`
- **Format:** REST API
- **Auth:** OAuth
- **What:** Bibliographic, legal-event, full-text patent data
- **Why:** Innovation signals — where is effort moving after scarcity shocks?

#### Crossref
- **URL:** `https://api.crossref.org/`
- **Format:** REST API
- **Auth:** None (polite pool recommended)
- **What:** DOI, title, author, publisher, relations
- **Why:** Academic research graph

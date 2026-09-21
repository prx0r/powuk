# powuk data sources

> Every source we collect, why we collect it, and what we do with it.

---

## GRID — Where is demand outstripping capacity?

### NESO Demand (hourly)
- **What:** UK half-hourly electricity demand (system demand, interconnector flows, embedded generation)
- **Why:** High demand + low generation = grid stress. This is the demand side of grid constraints.
- **URL:** `https://api.neso.energy/dataset/7a12172a-939c-404c-b581-a6128b74f588/resource/177f6fa4-ae49-4182-81ea-0c6b35f26ca6/download/demanddataupdate.csv`
- **Format:** CSV, half-hourly
- **Auth:** None
- **Cadence:** Hourly
- **What we store:** Raw CSV + observation (uk_demand_mw)
- **Data since:** Aug 2026 (live)

### NESO Generation Mix (hourly)
- **What:** UK generation by fuel type (gas, coal, nuclear, wind, solar, imports)
- **Why:** Renewable intermittency creates grid constraints. When wind drops, gas fills the gap, constraints appear.
- **URL:** `https://api.neso.energy/dataset/88313ae5-94e4-4ddc-a790-593554d8c6b9/resource/f93d1835-75bc-43e5-84ad-12472b180a98/download/df_fuel_ckan.csv`
- **Format:** CSV, half-hourly
- **Auth:** None
- **Cadence:** Hourly
- **What we store:** Raw CSV + observations (total_gen_mw, wind_mw, solar_mw, carbon_intensity)
- **Data since:** 2009 (310K rows)

### PV Live (hourly)
- **What:** Actual UK solar PV generation at GSP level
- **Why:** Embedded solar reduces network demand during day but creates export constraints at local level.
- **URL:** `https://api.pvlive.uk/pvlive/api/v4/gsp/0?data_format=json`
- **Format:** JSON
- **Auth:** None
- **Cadence:** Hourly
- **What we store:** Raw JSON + observation (uk_solar_actual_mw)
- **Data since:** Live (near real-time)

### UKPN Open Data (12h)
- **What:** UK Power Networks flexibility dispatches, embedded capacity, network headroom
- **Why:** UKPN is the largest DNO. Their flexibility data shows where constraints are actively being managed.
- **URL:** `https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets?limit=50`
- **Format:** JSON (CKAN API)
- **Auth:** None (some datasets need portal registration)
- **Cadence:** 12h
- **What we store:** Raw JSON + observation (dataset count)
- **Data since:** Live

---

## TRADES — Are there enough people?

### EvSpark Business Evidence (daily)
- **What:** Electrical, plumbing/heating, and landlord business counts by UK postcode area (127 areas)
- **Why:** Supply side of trade constraints. Areas with few electricians but high housing/EV growth = trade shortage.
- **Source:** Local file `/root/ab/businesses/evspark/receipts/ch_sweep_areas.csv`
- **Format:** CSV
- **Auth:** N/A (local)
- **Cadence:** Daily
- **What we store:** Raw CSV + observation (total electrical businesses)
- **Data since:** Local copy, 127 areas

---

## PLANNING — Where is demand appearing?

### Planning Applications (2h, paginated)
- **What:** England planning applications (reference, status, description, location)
- **Why:** Planning applications signal where development is happening. High application volume = future infrastructure demand.
- **URL:** `https://www.planning.data.gov.uk/entity.json?dataset=planning-application`
- **Format:** JSON
- **Auth:** None
- **Cadence:** 2h (paginated, up to 1000)
- **What we store:** Raw JSON + observation (total apps)
- **Data since:** Live (incomplete coverage)

---

## PROCUREMENT — What's being bought?

### Contracts Finder (2h, paginated)
- **What:** UK public procurement notices in OCDS format
- **Why:** Public procurement signals where government is buying capacity. Energy infrastructure contracts = future demand for trades.
- **URL:** `https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search`
- **Format:** JSON (OCDS)
- **Auth:** None
- **Cadence:** 2h (paginated, up to 1000)
- **What we store:** Raw JSON + observation (total releases)
- **Data since:** Live

### Find a Tender (2h, paginated)
- **What:** Higher-value UK procurement notices (OCDS)
- **Why:** Same as above but for larger contracts.
- **URL:** `https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages`
- **Format:** JSON (OCDS)
- **Auth:** None
- **Cadence:** 2h (paginated, up to 50)
- **What we store:** Raw JSON + observation (total releases)
- **Data since:** Live

---

## BUSINESS CAPACITY — Who's forming, who's failing?

### Companies House (12h)
- **What:** UK companies by SIC code (electrical, HVAC, solar, EV, telecom, repair, construction)
- **Why:** Business formation/dissolution signals trade capacity. New companies = supply entering. Dissolutions = capacity leaving.
- **URL:** `https://api.company-information.service.gov.uk/search/companies`
- **Format:** JSON (REST API)
- **Auth:** API key (env var)
- **Cadence:** 12h
- **What we store:** Raw JSON + observations (active firms per SIC cluster)
- **Data since:** Live (search API)

---

## TRAINING — Who is being produced?

### APAR — Training Providers (daily)
- **What:** Apprenticeship Provider and Assessment Register (1,263 eligible providers)
- **Why:** The training provider universe. Who can train apprentices? Where are they located?
- **URL:** `https://download.apprenticeships.education.gov.uk/apar/downloadcsv?filename=apar.csv`
- **Format:** CSV
- **Auth:** None
- **Cadence:** Daily
- **What we store:** Raw CSV + observation (total providers)
- **Data since:** 2018 (provider list)

### Ofqual — Qualifications (daily)
- **What:** UK regulated qualifications (10,000+ including trade qualifications)
- **Why:** What qualifications exist for each trade? Which are active? What levels?
- **URL:** `https://register-api.ofqual.gov.uk/api/qualifications?pageSize=500`
- **Format:** JSON
- **Auth:** None
- **Cadence:** Daily
- **What we store:** Raw JSON + observation (total qualifications)
- **Data since:** Live (52,887 total in register)

---

## LABOUR — Who can do the work?

### ONS Labour Demand (daily)
- **What:** Online job advert volumes by SOC2020 occupation × region (Jan 2017 - Jul 2026)
- **Why:** Demand side of trade constraints. Where are electricians/solar installers being hired?
- **URL:** `https://www.ons.gov.uk/.../labourdemandbyoccupation.xlsx`
- **Format:** XLSX
- **Auth:** None
- **Cadence:** Daily
- **What we store:** Raw XLSX + observation (total rows)
- **Data since:** Jan 2017 (175K rows, 9 years of history)

---

## CERTIFICATION — Who can legally do the work?

### REFCOM — F-gas Certified Companies (daily)
- **What:** F-gas certified companies (11,298 companies)
- **Why:** HVAC/refrigeration capacity. F-gas certification is required to work with refrigerants. Critical for heat pump installation.
- **URL:** `https://api.refcom.org.uk/api/PublicCompany/GetFgasActiveCertificateCount`
- **Format:** JSON (REST API)
- **Auth:** None
- **Cadence:** Daily
- **What we store:** Raw JSON + observation (total companies)
- **Data since:** Live (11,298 active)

---

## SOURCES NOT YET COLLECTED (but in spec)

| Source | Priority | Why | Status |
|--------|----------|-----|--------|
| Skills England Occupational Maps | P0 | Occupation → skills → training | API returns 403 |
| Nomis/APS Labour Supply | P0 | Employment by occupation × region | Need to find URL |
| DfE Apprenticeships Historical | P0 | Training pipeline history | URL issues |
| ONS Job-ad Skills | P0 | What skills are being demanded | Need to find URL |
| ONS Job-ad Salaries | P1 | Wage signals by occupation | Need to find URL |
| Apprenticeship Display Advert API | P0 | Real-time labour demand | Needs API key |
| TrustMark | P0 | Retrofit capacity | Needs API key (free) |
| MCS Installers | P0 | Heat-pump/solar capacity | No public API (scrape) |
| OZEV Installers | P0 | EV charger capacity | No public API (scrape) |
| Competent Person Electrical | P0 | Electrician capacity | No public API (scrape) |

---

## COLLECTION PHILOSOPHY

1. **Immutable raw** — every fetch stored with content-hashed path, never overwritten
2. **Full history** — download all available historical data, not just latest
3. **Provenance** — every observation has source, timestamp, raw reference
4. **Health monitoring** — every collector reports status, failures logged
5. **Easy addition** — new source = one collector function, register in sources.yaml

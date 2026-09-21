# POW data gardens — collection priorities

## P0: start the clock now

These states are difficult or impossible to reconstruct exactly after the fact.

### Electronic component availability

Track a selected “boring indispensable” basket across multiple distributors: stock, price breaks, lead time, lifecycle status, suggested substitutes, MOQ and region.

Primary sources:
- Nexar / Octopart API — component supply-chain data: https://nexar.com/api
- DigiKey Product Information API: https://developer.digikey.com/products/product-information-v4
- Mouser Search API — availability, lead time, lifecycle, pricing: https://www.mouser.com/en/api-search/
- Farnell / element14 Product Search API — stock/pricing/product detail: https://partner.element14.com/Search_API

Why: multi-distributor divergence is itself information. A single distributor stockout can be noise; synchronized depletion is a potential physical constraint.

### Forward physical capacity

- NESO TEC Register, machine-readable, updated twice weekly: https://www.neso.energy/data-portal/transmission-entry-capacity-tec-register
- England Planning Data API, including monitoring new planning applications: https://www.planning.data.gov.uk/docs
- Contracts Finder / Find a Tender OCDS: https://www.gov.uk/government/publications/open-contracting

Why: future capacity often becomes observable as planning, procurement or grid-connection commitments **before** production exists.

### Labour / skill pressure

- ONS occupation-level online job-ad volumes, monthly, Jan 2017 onward: https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/datasets/labourdemandvolumesbystandardoccupationclassificationsoc2020uk
- ONS job-ad skills/competencies: https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/datasets/skillscompetenciesandotherjobrequirementsfromonlinejobadvertsuk
- ONS online job-ad salaries: https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/onlinejobadvertssalariesuk
- Skills England Occupational Maps API — occupation, duties, KSBs and training products: https://occupational-maps.skillsengland.education.gov.uk/public-api/
- Apprenticeship Display Advert API: https://developer.apprenticeships.education.gov.uk/

Why: this lets POW distinguish “hardware shortage” from “qualified-human bottleneck” and measure training response.

### Technology frontier

- OpenAlex API, connected graph of works/topics/institutions: https://help.openalex.org/api/
- GitHub releases/commits REST API: https://docs.github.com/en/rest/releases/releases
- EPO Open Patent Services: https://www.epo.org/en/searching-for-patents/data/web-services/ops

Why: directed-technical-change models need to know where effort is moving after a relative-price shock.

### Trade / physical flows

- HMRC UK Trade Info OData API, commodity/country/month: https://www.uktradeinfo.com/api-documentation
- BGS World Mineral Statistics API, long-run commodity production/trade: https://www.bgs.ac.uk/mineralsuk/statistics/world-mineral-statistics/world-mineral-statistics-data-download/
- USGS Mineral Commodity Summaries data, >90 nonfuel commodities: https://www.usgs.gov/data/mineral-commodity-summaries-2026-data-release

Why: a domestic distributor shortage can be checked against import quantities, global production and mineral bottlenecks.

### Used / secondary market

- eBay Browse API: https://developer.ebay.com/api-docs/buy/api-browse.html

Snapshot active inventory, price, condition, parts-only ratio and listing disappearance. Treat asking prices as asking prices; do not relabel them as realized transaction prices.

### Public-company assimilation

- SEC EDGAR submissions + XBRL APIs, real-time and keyless: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- IBKR L2, where licensed/subscribed, via `reqMktDepth`: https://ibkrcampus.com/docs/tws-api/doc/market-data-live/market-depth-l-2/request-market-depth

Why: physical state can lead company narrative and market pricing. This is the assimilation-latency layer.

## P1: backfillable structural graph

These can be added later because historical data already exists.

- ONS UK supply/use and input-output tables, 1997–2023: https://www.ons.gov.uk/economy/nationalaccounts/supplyandusetables/datasets/inputoutputsupplyandusetables
- ONS UK input-output analytical tables: https://www.ons.gov.uk/economy/nationalaccounts/supplyandusetables/datasets/ukinputoutputanalyticaltablesindustrybyindustry
- Eurostat FIGARO 2026 edition, 64 industries/products, 2010–2024: https://ec.europa.eu/eurostat/en/web/esa-supply-use-input-tables/database
- OECD ICIO 2025 edition: https://www.oecd.org/en/data/datasets/inter-country-input-output-tables.html
- US BEA detailed input-output tables: https://www.bea.gov/resources/guide-interactive-industry-input-output-accounts-tables
- Companies House API for UK firm identity/SIC/location/filings: https://developer.company-information.service.gov.uk/

Use these as priors / coarse topology, not as sufficient evidence for a component-level dependency.

## P1: failure / maintenance history

- Open Repair Alliance data: https://openrepair.org/open-data/downloads/
- iFixit repair guides/API: https://www.ifixit.com/News/3981/the-worlds-first-repair-api
- NHTSA datasets/APIs: https://www.nhtsa.gov/nhtsa-datasets-and-apis
- UK OPSS recalls/alerts: https://www.gov.uk/guidance/product-recalls-and-alerts

This is the Greer term: inherited installed capital creates a future maintenance demand wave.

## Proprietary probes worth planting

Public data can seed the graph; proprietary longitudinal outcomes create the moat.

1. **3D-printer probe** — OctoPrint/Moonraker job/failure/maintenance outcomes.
2. **repair outcome probe** — symptom -> attempted intervention -> part -> time -> success/failure.
3. **component basket** — exact same MPNs across distributors hourly/daily.
4. **used equipment cohort** — listing-level state transitions for selected machines/components.
5. **physical project cohort** — planning/procurement/connection record -> actual completion/cancellation.

## The anti-hoarding rule

A source belongs in POW only if it enables at least one of:

- adoption forecast
- dependency edge
- buffer/capacity estimate
- maintenance hazard
- skill scarcity
- innovation response
- assimilation latency
- outcome validation

Otherwise it is interesting data, not POW data.

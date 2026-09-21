# Companies House API — full reference

> Source of truth for all Companies House data we can access.

**Base URL:** `https://api.company-information.service.gov.uk`
**Auth:** HTTP Basic — key as username, empty password
**Key:** `d284d51e-b98b-4517-861d-0f8b2273ceeb`
**Rate limit:** 600 requests per 5 minutes per key (172,800/day)

---

## ALL APIS

| API | Purpose | Auth | Status |
|-----|---------|------|--------|
| Public Data API | Search, profiles, officers, filings | REST key ✓ | Active |
| Document API | Fetch filed documents (PDFs) | REST key ✓ | Active |
| Streaming API | Real-time change events | Streaming key needed | Register |
| Manipulate API | File company changes | OAuth needed | Not for us |
| Bulk Data | Monthly CSV snapshot | None | Active (part1 downloaded) |

---

## AUTH

```bash
# curl
curl -u "d284d51e-b98b-4517-861d-0f8b2273ceeb:" https://api.company-information.service.gov.uk/...

# Python
import base64, requests
auth = base64.b64encode(b"d284d51e-b98b-4517-861d-0f8b2273ceeb:").decode()
requests.get(url, headers={"Authorization": f"Basic {auth}"})
```

---

## SEARCH ENDPOINTS

### Search companies
```
GET /search/companies?q={term}&items_per_page={n}&start_index={n}
```
- Free-text search across company names
- Returns: company_number, title, company_status, address_snippet, kind
- Use for: finding trade businesses by name/description

### Advanced company search
```
GET /advanced-search/companies?
  company_name_includes={string}&
  company_name_excludes={string}&
  sic_codes={code}&
  company_status={active|dissolved}&
  registered_office_address_region={region}&
  registered_office_address_locality={town}&
  registered_office_address_postal_code={postcode}&
  incorporation_from={YYYY-MM-DD}&
  incorporation_to={YYYY-MM-DD}&
  dissolved_from={YYYY-MM-DD}&
  dissolved_to={YYYY-MM-DD}&
  size={1-5000}&
  start_index={n}
```
- Filter by SIC code, status, location, date range
- Use for: count active electrical companies in a region

### Search officers
```
GET /search/officers?q={term}&items_per_page={n}&start_index={n}
```
- Search for people (directors, secretaries)
- Returns: name, officer_role, address, snippet
- Use for: finding electricians who run multiple companies

### Search all
```
GET /search?q={term}&items_per_page={n}
```
- Searches companies AND officers in one call
- Use for: broad discovery

### Alphabetical search
```
GET /alphabetical-search/companies?q={letter}&size={n}
```
- Browse companies alphabetically
- Use for: systematic enumeration

### Dissolved company search
```
GET /dissolved-search/companies?q={term}&items_per_page={n}
```
- Search only dissolved companies
- Use for: tracking companies that left the market

---

## COMPANY ENDPOINTS

### Company profile
```
GET /company/{company_number}
```
Returns:
```json
{
  "company_number": "00445790",
  "company_name": "...",
  "company_status": "active",
  "company_type": "ltd",
  "incorporation_date": "1987-04-22",
  "registered_office_address": {
    "address_line_1": "...",
    "address_line_2": "...",
    "care_of": "...",
    "country": "United Kingdom",
    "locality": "London",
    "postal_code": "SW1A 1AA",
    "po_box": "...",
    "region": "..."
  },
  "sic_codes": ["43210", "43220"],
  "accounts": {
    "account_ref_day": 31,
    "account_ref_month": 3,
    "next_accounts": {
      "due_on": "2026-12-31",
      "overdue": false
    },
    "last_accounts": {
      "made_up_to": "2025-12-31",
      "type": "full"
    }
  },
  "confirmation_statement": {
    "next_due": "2027-04-15",
    "overdue": false
  },
  "charges": {
    "charges_count": 2,
    "satisfied_count": 1
  },
  "previous_company_names": [...],
  "etag": "..."
}
```

### Registered office address
```
GET /company/{company_number}/registered-office-address
```

### Company officers
```
GET /company/{company_number}/officers?items_per_page={n}&start_index={n}
```
Returns:
```json
{
  "items": [{
    "name": "SMITH, John",
    "officer_role": "director",
    "appointed_on": "2020-01-15",
    "resigned_on": null,
    "date_of_birth": {"month": 6, "year": 1985},
    "nationality": "British",
    "occupation": "Electrician",
    "address": {...},
    "links": {...}
  }],
  "total_results": 12
}
```

### Officer appointment (single)
```
GET /company/{company_number}/appointments/{appointment_id}
```

### Filing history
```
GET /company/{company_number}/filing-history?items_per_page={n}
```
Returns:
```json
{
  "items": [{
    "transaction_id": "...",
    "date": "2026-09-16",
    "type": "AA",
    "description": "accounts-with-accounts-type-full",
    "category": "accounts",
    "status": "filed",
    "links": {...}
  }],
  "total_results": 45
}
```
Filing types:
- `AA` = Annual accounts
- `AD01` = Change of registered office
- `AP01` = Appointment of director
- `TM01` = Termination of director
- `SH01` = Statement of capital
- `AR01` = Annual return
- `MR01` = Registration of charge
- `DS01` = Application to strike off

### Charges
```
GET /company/{company_number}/charges
GET /company/{company_number}/charges/{charge_id}
```
Returns: charge details, amount, status (satisfied/outstanding)

### Insolvency
```
GET /company/{company_number}/insolvency
```

### Exemptions
```
GET /company/{company_number}/exemptions
```

### UK Establishments
```
GET /company/{company_number}/uk-establishments
```

### Registers
```
GET /company/{company_number}/registers
```

---

## PERSONS WITH SIGNIFICANT CONTROL (PSC)

### List PSCs
```
GET /company/{company_number}/persons-with-significant-control
```
Returns: individuals, corporate entities, legal persons with significant control

### Get individual PSC
```
GET /company/{company_number}/persons-with-significant-control/individual/{notification_id}
```

### Get corporate PSC
```
GET /company/{company_number}/persons-with-significant-control/corporate-entity/{notification_id}
```

### PSC statements
```
GET /company/{company_number}/persons-with-significant-control-statements
```

### PSC notifications (cross-company)
```
GET /persons-with-significant-control/{psc_id}/notifications
```
- Find all companies a person controls

---

## OFFICER ENDPOINTS

### Officer appointments (cross-company)
```
GET /officers/{officer_id}/appointments
```
- Find all companies a director serves on
- Use for: detecting capacity concentration (one person running 5 electrical companies)

### Officer disqualifications
```
GET /disqualified-officers/natural/{officer_id}
GET /disqualified-officers/corporate/{officer_id}
```

---

## DOCUMENT API

Fetch actual filed documents (PDFs, accounts, certificates).

### Get document metadata
```
GET https://document-api.company-information.service.gov.uk/document/{document_id}
```
Returns:
```json
{
  "company_number": "07621999",
  "barcode": "YEHHQ5PE",
  "category": "liquidations",
  "pages": 12,
  "created_at": "2025-12-19T23:59:54Z",
  "resources": {
    "application/pdf": {"content_length": 459050}
  }
}
```

### Get document content (PDF)
```
GET https://document-api.company-information.service.gov.uk/document/{document_id}/content
```
Returns: PDF binary

### Document categories
| Category | What it is | Powuk use |
|----------|-----------|-----------|
| accounts | Annual accounts | Company health, revenue signals |
| certificates | Incorporation, name change | Company lifecycle |
| liquidations | Voluntary/statutory liquidation | Trade capacity exiting |
| insolvency | Administration, CVA | Business distress |
| charges | Mortgages, charges | Financial stress |
| offcers | Director appointments | Network mapping |
| returns | Annual returns | Compliance status |

### How to get document IDs
From filing history:
```
GET /company/{number}/filing-history
→ items[].links.document_metadata → document URL
```

---

## STREAMING API

Real-time event streams for all company changes. Requires separate streaming key.

**Base URL:** `https://stream.companieshouse.gov.uk`
**Auth:** HTTP Basic (streaming key, not REST key)
**Format:** Server-Sent Events (SSE)

### Available streams

| Stream | URL | What it gives |
|--------|-----|---------------|
| Companies | `/companies` | Company creation, name changes, status changes |
| Filings | `/filings` | Every filing as it happens |
| Officers | `/officers` | Director appointments, resignations |
| PSC | `/persons-with-significant-control` | Ownership changes |
| Charges | `/charges` | New/satisfied charges |
| Insolvency | `/insolvency-cases` | Insolvency events |
| Disqualified | `/disqualified-officers` | Disqualification orders |
| Exemptions | `/company-exemptions` | Exemption changes |

### Usage
```
GET /companies?timepoint={timestamp}
```
Returns SSE stream of company change events.

### Why this is powerful for powuk
- **Real-time trade capacity signal** — When an electrical contractor files DS01 (strike-off), you know immediately
- **Director network changes** — When someone resigns from 5 companies at once, capacity is shifting
- **Liquidation cascade** — Multiple electrical companies entering liquidation in same region = market stress
- **New company formation** — New "EV charger" company appearing = demand signal

### Registration
Need to register a separate Streaming API key at:
`https://developer.company-information.service.gov.uk/manage-applications`

---

## BULK DATA

### Free monthly snapshot
```
http://download.companieshouse.gov.uk/BasicCompanyDataAsOneFile-YYYY-MM-01.zip
```
- ~469MB zipped, ~2GB unzipped
- ~5 million active companies
- Columns: CompanyName, CompanyNumber, RegAddress.*, CompanyCategory, CompanyStatus, CountryOfOrigin, DissolutionDate, IncorporationDate, Accounts.*, Returns.*, Mortgages.*, SICCode.SicText_1-4, PreviousName_1-10.*, ConfStmt.*
- Updated monthly, available by 5th of month
- **We have part1 (70MB) already filtered to 130,839 trade businesses**

---

## SIC CODES (relevant to powuk)

### Primary trade SICs
| Code | Description | Powuk relevance |
|------|-------------|-----------------|
| 43210 | Electrical installation | Electricians, EV charger installers |
| 43220 | Plumbing, heat and air-conditioning installation | Heat pump installers, boiler engineers |
| 43290 | Other construction installation | General trade installers |
| 43910 | Roofing activities | Solar panel installers |
| 43999 | Other construction installation nec | Miscellaneous trade |
| 41100 | Development of building projects | Property developers |
| 41202 | Construction of domestic buildings | House builders |

### Energy/renewable SICs
| Code | Description | Powuk relevance |
|------|-------------|-----------------|
| 35110 | Production of electricity | Solar/wind farm operators |
| 35140 | Trade of electricity | Energy traders |
| 35110 | Electricity generation | Renewable generators |

### Parts/supply SICs
| Code | Description | Powuk relevance |
|------|-------------|-----------------|
| 46520 | Wholesale of electronic and electrical parts | Component distributors |
| 47540 | Retail sale of electrical household appliances | Retail |
| 33140 | Repair of electrical equipment | Repair businesses |

### Tech/repair SICs
| Code | Description | Powuk relevance |
|------|-------------|-----------------|
| 95110 | Repair and maintenance of computers | IT repair |
| 95210 | Repair and maintenance of consumer electronics | Electronics repair |
| 62011 | Software development | Tech companies |

---

## WHAT WE CAN BUILD

### 1. Trade supply mapper
Search by SIC code × region → count active companies per area
```
GET /advanced-search/companies?sic_codes=43210&registered_office_address_region=London&company_status=active&size=5000
```
Output: `region × trade → company count → supply signal`

### 2. Business health tracker
Track company status changes over time
```
GET /company/{number} → check company_status, accounts.overdue, confirmation_statement.overdue
```
Output: `companies with overdue accounts = struggling = potential exit`

### 3. Officer network mapper
Find people running multiple trade companies
```
GET /officers/{officer_id}/appointments → all companies they serve on
```
Output: `person → [company1, company2, ...] → capacity concentration`

### 4. Dissolution monitor
Track companies leaving the market
```
GET /dissolved-search/companies?q=electrical&dissolved_from=2025-01-01
```
Output: `monthly dissolutions by trade = capacity drain signal`

### 5. Filing pattern detector
Watch for accounts overdue, strike-off actions
```
GET /company/{number}/filing-history → AA (accounts), DS01 (strike-off)
```
Output: `companies about to close = capacity leaving`

### 6. PSC ownership graph
Who owns what in the trade sector
```
GET /company/{number}/persons-with-significant-control
```
Output: `owner → [companies] → market concentration`

---

## RATE LIMIT STRATEGY

600 requests per 5 minutes = 120 requests per minute

**Batch by region:**
- 12 UK regions × 5 trade SICs = 60 searches per cycle
- Each search returns up to 5000 results
- Full UK trade map in ~1 cycle (5 minutes)

**Batch by company:**
- To profile 1000 companies: 1000 requests
- Takes ~8 minutes at rate limit
- Do overnight or in background

**Bulk approach:**
- Download monthly CSV (469MB)
- Filter by SIC code locally
- Use API only for freshness updates

---

## DATA WE ALREADY HAVE

| Source | Records | Location |
|--------|---------|----------|
| Bulk CSV (part1) | 849,999 companies | `/root/ographuk/data/bulk/part1.db` |
| Filtered trade businesses | 130,839 | `/root/powuk/data/raw/trades/companies_house_trade.csv` |
| Electrical installers (43210) | 7,868 | in above |
| Plumbing/HVAC (43220) | 7,025 | in above |
| Electricity producers (35110) | 1,566 | in above |

---

---

## COOL STUFF TO BUILD

### 1. Trade capacity real-time monitor
Combine Streaming API (filing events) + REST API (company profiles)
- Every DS01 (strike-off) for SIC 43210 → "electrical company closing"
- Every AP01 (new director) for SIC 43210 → "new capacity entering"
- Every AA (accounts) showing losses → "company struggling"
- Stream these events into powuk DB → live trade supply signal

### 2. Document intelligence
Fetch actual filed accounts PDFs → extract:
- Revenue figures
- Employee counts
- Profit/loss
- Director names
Build: "How big is each electrical contractor?" from their actual accounts

### 3. Insolvency early warning
- Charges increasing + accounts overdue + director resignations = company about to fail
- Cross-reference with trade type → "electrical contractors failing in Midlands"
- This is the signal DNOs and trade bodies would pay for

### 4. Officer network graph
- Every director → all their companies
- Detect: one person running 10 electrical companies = capacity concentration
- Detect: same director across electrical + solar = vertically integrated
- Detect: director resigning from all companies = exiting the trade

### 5. Geographic supply/demand heat map
- SIC 43210 companies × postcode → supply density
- Planning apps × postcode → demand density
- Grid queue × postcode → connection pressure
- Overlay: where is supply < demand < grid capacity?

### 6. Company lifecycle tracker
Track a single company through:
```
Incorporation → Director appointments → Accounts filed → 
Charges registered → Accounts overdue → Director resignations → 
Strike-off application → Dissolution
```
This is the "company health trajectory" that predicts trade capacity changes.

---

---

## SDK

Quick Python import:
```python
from sdk.companies_house import CH

# or import specific functions
from sdk.companies_house import search_companies, get_company, stream_officers
```

### Available functions

**Search:**
- `search_companies(query, items_per_page)` — free text
- `search_officers(query, items_per_page)` — find people
- `search_all(query, items_per_page)` — companies + officers
- `advanced_search(sic_codes, company_status, region, ...)` — filtered

**Company:**
- `get_company(number)` — full profile
- `get_officers(number)` — directors, secretaries
- `get_filings(number)` — filing history
- `get_charges(number)` — mortgages
- `get_psc(number)` — ownership
- `get_insolvency(number)` — insolvency info
- `get_officer_appointments(officer_id)` — all their companies

**Documents:**
- `get_document_metadata(document_id)` — category, pages, size
- `get_document_content(document_id, out_path)` — download PDF

**Streaming:**
- `stream_companies(timepoint)` — company changes
- `stream_filings(timepoint)` — filing events
- `stream_officers(timepoint)` — officer changes
- `stream_insolvency(timepoint)` — insolvency events
- `stream_charges(timepoint)` — charge events
- `stream_psc(timepoint)` — ownership changes

---

## LIMITATIONS

### REST API
- **Rate limit:** 600 requests per 5 minutes (172,800/day)
- **429 response:** You've hit the limit. Wait for the 5-minute window to reset.
- **Advanced search total_results:** May show 0 even with results (known bug). Use items count instead.

### Document API
- **Same key as REST API**
- **Rate limit:** Same 600/5min bucket
- **Content types:** PDF, some HTML
- **Availability:** Most filings have documents. Very old ones may not.

### Streaming API
- **Separate key** (not interchangeable with REST)
- **Max 2 concurrent connections per account**
- **If you read too slowly, connection drops** — must process events in real-time
- **Reconnect with last timepoint** for continuity
- **429 = rate limited** — wait 1 minute before reconnect
- **Heartbeat:** Empty lines sent periodically to keep connection alive
- **Queue backlog:** Can request historical timepoint, but queue has limits (416 if too old)

### Bulk Data
- **Monthly snapshot** — updated by 5th of month
- **~469MB zipped** — ~5M companies
- **Free, no auth required**
- **No support provided**

---

*Last updated: 2026-09-21*
*REST API key: active*
*Streaming API key: active*
*Document API: active (same as REST)*
*Bulk data: part1 downloaded (849K companies)*
*SDK: /root/powuk/sdk/companies_house.py*

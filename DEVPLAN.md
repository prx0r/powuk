# powuk devplan

> Where is physical skilled capacity scarce, how quickly is Britain producing more of it, what new demand is arriving, and where is the gap getting worse?

---

## FOUR CANONICAL QUANTITIES (per skill × geography × time)

### 1. INSTALLED CAPACITY — who can legally do the work now
- Registered Competent Person Electrical
- MCS installers (heat pumps, solar)
- F-gas/REFCOM (HVAC, refrigeration)
- OZEV EV chargepoint installers
- TrustMark / PAS 2030 (retrofit)
- EPC/DEC assessors
- Companies House filtered firms
- Estimated sole traders (ONS)

### 2. INCOMING CAPACITY — who is being produced
- Apprenticeship starts/completions (by standard, provider, geography)
- APAR (training provider universe)
- UKRLP (provider locations)
- Skills Bootcamps
- New certifications
- New Companies House formations

### 3. DEMAND — what work is arriving
- Job vacancies (Indeed/Reed/ONS)
- Apprenticeship vacancies (Find an Apprenticeship API)
- Government procurement (Contracts Finder / Find a Tender)
- Planning applications
- Legislation/regulation changes
- Subsidies/grants (BUS, ECO, etc.)
- Infrastructure announcements

### 4. CAPACITY FRICTION — why supply isn't responding
- Wages
- Vacancy duration
- Training completion rates
- Business failure rates
- Geographic distance/travel constraints
- Qualification requirements
- Certification bottlenecks

---

## SCARCITY FORMULA

```
POW_Scarcity(s,g,t) = D(s,g,t) / (C(s,g,t) + E[ΔC(s,g,t)])

D = work demand
C = currently qualified local capacity
E[ΔC] = expected incoming capacity from training/new entrants
```

---

## PRIORITY COLLECTORS

| Priority | Source | Data | API/URL |
|----------|--------|------|---------|
| A+ | Apprenticeship datasets | skill pipeline + history | explore-education-statistics.service.gov.uk |
| A+ | APAR | training-provider universe | download.apprenticeships.education.gov.uk/apar |
| A+ | Registered Competent Person Electrical | electrician capacity | electricalcompetentperson.co.uk |
| A+ | MCS | heat-pump/solar capacity | mcs-certified.com |
| A+ | F-gas/REFCOM | HVAC capacity | refcom.co.uk |
| A+ | OZEV | EV installer capacity | gov.uk/electric-vehicle-chargepoint-installers |
| A | TrustMark | retrofit capacity | trustmark.org.uk/business/data-warehouse |
| A | UKRLP | provider locations | ukrlp.education.gov.uk |
| A | Find an Apprenticeship API | real-time labour demand | api.manage-apprenticeships.service.gov.uk |
| A | Companies House filtered | business formation/failure | api.company-information.service.gov.uk |
| A | Job vacancies | current demand | indeed/reed APIs |
| A | Legislation | future demand shock | gov.uk |
| A | Procurement | funded work arriving | contractsfinder/find-tender |
| B+ | EPC assessors | upstream retrofit capacity | gov.uk/get-new-energy-certificate |
| B+ | CITB | construction workforce | citb.co.uk |
| B+ | Skills Bootcamps | fast policy response | gov.uk |
| B | EA waste registers | construction/repair activity | data.gov.uk |
| B | DVSA MOT | Repair ↔ POW bridge | gov.uk |
| WATCH | Ofgem heat-network register | brand-new regulatory dataset | ofgem.gov.uk |

---

## DATA FLOW

```
CERTIFICATION REGISTERS → powuk_capability_provider
TRAINING DATA → powuk_training_pipeline
DEMAND SIGNALS → powuk_demand_signals
COMPANIES HOUSE → powuk_company_capacity (enrichment layer)
         ↓
    SCARCITY COMPILER
         ↓
    powuk_scarcity_daily(skill, geography, date)
         ↓
    SEESAW reads
```

---

## OUTPUT TABLE

```
powuk_scarcity_daily
├── date
├── skill_cluster (electrical, hvac, solar, ev, telecom, repair, construction)
├── geography (postcode_area / local_authority / region)
├── installed_capacity (registered providers)
├── incoming_capacity (training pipeline)
├── demand_signal (vacancies + procurement + planning)
├── capacity_friction (wages, failures, bottlenecks)
├── pow_scarcity_score (0-4)
├── capacity_response_ratio
└── trend (tightening / loosening / stable)
```

---

## IMPLEMENTATION ORDER

1. Test all certification register APIs
2. Download APAR + apprenticeship datasets
3. Build capability_provider entity
4. Build training_pipeline entity
5. Wire up demand signal collectors
6. Build scarcity compiler
7. Create output table
8. Backfill historical data
9. Set up monitoring
10. Deploy always-on collection

---

*This is the source of truth for powuk development.*

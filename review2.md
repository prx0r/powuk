# powuk review2.md

<!-- HISTORICAL REVIEW — 2026-09-21, commit ~41dadf4. First major code review.
     Issues identified: secrets committed, monolith server.py, no collector
     contracts, raw storage overwrites, no manifest/provenance, APAR hardcoded,
     CH keyword search, planning/contracts capped at 100, no monitoring, no tests.
     Many of these have been fixed in subsequent commits. See review6.md for
     the latest review state. -->

> Checkpoint 1 is not a scarcity engine. It is a trustworthy historical data acquisition machine.

---

## Key issues

1. Secrets committed (Companies House keys in server.py and sdk/)
2. server.py is everything in one file — needs proper architecture
3. Collectors don't have consistent contracts
4. Raw storage overwrites (not immutable)
5. No manifest/provenance tracking
6. APAR is hardcoded dated CSV, not a pipeline
7. Companies House collector uses search text, not SIC filters
8. Planning/contracts just grab first 100, not full pagination
9. No monitoring/health checks
10. No tests that matter

## Target architecture

```
powuk/
├── config/sources.yaml
├── ingestion/
│   ├── base.py
│   ├── raw_store.py
│   ├── manifest.py
│   ├── http.py
│   ├── cursor.py
│   └── runner.py
├── collectors/
│   ├── capability/
│   ├── training/
│   ├── labour/
│   ├── business/
│   ├── procurement/
│   ├── planning/
│   └── policy/
├── normalizers/
├── schemas/
├── storage/
├── monitoring/
├── cli/
└── tests/
```

## Implementation order

### Phase A — Foundation
- Rotate keys
- Remove contamination
- Source registry
- RawStore (immutable)
- Manifest DB
- Canonical Parquet writer
- CLI
- Monitoring state
- Common collector interface

### Phase B — Easiest historical sources
- APAR (proper pipeline)
- DfE apprenticeships
- ONS job ads
- ONS job skills
- Nomis labour supply
- UKRLP

### Phase C — Ephemeral capability registers
- Competent Person Electrical
- MCS
- OZEV
- REFCOM/F-gas
- TrustMark

### Phase D — Transactional demand
- Contracts Finder (full pagination)
- Find a Tender (full pagination)
- Planning (full pagination)
- Apprenticeship vacancies

### Phase E — Companies House
- Relevant company baseline (SIC filters)
- Companies stream
- Insolvency stream
- Charges stream

### Phase F — Policy
- Official publications
- Legislation/regulation metadata
- Grants/subsidies

## Definition of done

Checkpoint 1 is finished when:
- All P0 source collectors operational
- All available historical data backfilled
- Ephemeral sources snapshot continuously
- Streams resumable
- Raw immutable
- Normalized canonical data queryable
- Stable entity IDs
- Source → raw → normalized provenance intact
- Source revisions preserved
- Collector health visible
- Failures alertable
- Tests prove no silent gaps/duplication
- New source can be added using one standard interface

Then begin: scarcity indexes, capacity-response lag, constraint inference, opportunity discovery.

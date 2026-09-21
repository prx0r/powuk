# powuk review7.md

The latest push is a real architectural improvement. `4be92da` fixes most of the mechanical flaws that previously prevented POWUK from being a trustworthy garden: explicit collector results, raw/normalized separation, coverage, config-driven cadence, watermarking, and tests.

For a **final Layer-1 push**, I would now stop touching Layer 2 entirely and close three things: **one canonical ingestion architecture, complete source coverage, and an acceptance command that can prove the garden is complete.**

The remaining structural issues are not large conceptual problems; they are consolidation/completeness problems:

* `config/sources.yaml` and `layer1/sources/*.yaml` are two competing source registries.
* `server.py` still owns its own DB/storage/state logic alongside `layer1/collector.py`.
* collectors are still largely embedded in `server.py`.
* `store_raw()` currently deduplicates files, but doesn't itself persist the retrieval/provenance ledger; the older `server.store()` does.
* some config stages are already stale: e.g. Companies House is still marked `discovery`; REFCOM metadata describes the previous aggregate-only implementation.
* `ons_skills` and `ons_salaries` exist in central config/code but have no corresponding `layer1/sources/*.yaml` manifest.
* the current tests verify infrastructure primitives much better than before, but don't yet prove every actual collector against a golden fixture.
* the source universe is still short of what we identified as necessary for full POWUK Layer 1.

I would send the coding agent this as the **final Layer-1 brief**:

# POWUK — Final Layer 1 Completion Push

## Mission

This is the last architectural/content push for Layer 1.

Do not implement scarcity, Seesaw, opportunity ranking, cross-source entity resolution, capability inference, AGI modelling, or economic scoring.

Layer 1 has one job:

> Own the relevant UK physical-economy source data correctly, historically, continuously and reproducibly.

After this push, Layer 1 should be boring.

New sources should be mechanically addable without changing architecture.

The finished pipeline is:

```text
SOURCE MANIFEST
      ↓
COLLECTOR
      ↓
FETCH RECEIPT
      ↓
IMMUTABLE RAW BLOB
      ↓
RETRIEVAL EVENT
      ↓
SOURCE-FAITHFUL NORMALIZATION
      ↓
NORMALIZED PARTITION
      ↓
COVERAGE / COMPLETENESS
      ↓
HEALTH / SCHEMA DRIFT
      ↓
WATERMARK
```

No modelling is required.

---

# 1. Freeze the Layer boundaries

Canonical definitions:

```text
LEVEL 0
source discovery
endpoint investigation
fixtures
licence/terms research

LEVEL 1 — THIS REPO WORK
raw acquisition
historical backfill
continuous snapshots/events
source-faithful normalization
release-vintage preservation
provenance
coverage/completeness
schema drift
monitoring
watermarks
source health

LEVEL 2
entity resolution
postcode/LAD/geography harmonisation
SOC/SIC/occupation/capability mapping
cross-source joins
canonical time series

LEVEL 3
scarcity
shadow prices
entry/exit
capacity response
Seesaw
AGI effects
opportunities
```

No Layer-2/3 dependency may be required to operate Layer 1.

Existing research/model code can remain, but Layer-1 acceptance must succeed with it ignored.

---

# 2. Eliminate the dual source registry

There are currently two source systems:

```text
config/sources.yaml

layer1/sources/*.yaml
```

Do not maintain both manually.

Use:

```text
layer1/sources/*.yaml
```

as the sole source of truth.

Reason:

The per-source manifests already support:

```text
authority
licence
collection
storage
time
health
URL
auth
notes
```

Extend `SourceManifest` with:

```text
domain
priority
stage
recoverability

history:
    type
    earliest
    partition
    revisioned

coverage:
    strategy
    expected_count_field
    minimum_ratio

schema:
    version
    required_fields

auth:
    type
    env_var
```

Then:

```text
load_all_manifests()
        ↓
collector registry
scheduler
health
docs
status
checkpoint report
```

Delete `config/sources.yaml`, or generate it automatically if another consumer truly needs it.

Never manually edit both.

Add:

```bash
python -m layer1.cli manifests check
```

which fails on:

```text
duplicate IDs
missing collector
collector without manifest
invalid cadence
unknown mode
missing licence
missing history semantics
missing health SLA
```

---

# 3. Make `layer1/collector.py` the only infrastructure implementation

`server.py` still duplicates:

```text
get_db()
raw_blob schema
raw_ingest schema
observation schema
collector_state schema
source_coverage schema
store()
obs()
state()
```

Delete that duplication.

There must be exactly one implementation of:

```text
DB schema
raw storage
normalized storage
retrieval ledger
coverage
collector result
watermarks
health
```

under:

```text
layer1/
```

Suggested structure:

```text
layer1/
    collector.py
    storage.py
    state.py
    health.py
    manifest.py
    fetch.py
    runner.py
    cli.py

    collectors/
        grid/
        labour/
        training/
        certification/
        business/
        planning/
        procurement/
        policy/
        property/
```

`server.py` should eventually become either:

```text
python -m layer1.runner
```

or a tiny compatibility wrapper.

No collector-specific logic should live in `server.py`.

---

# 4. Fix the raw storage/provenance contract completely

`store_raw()` currently writes the content-addressed blob, but the provenance ledger is separate.

Unify the operation.

Every acquisition should return:

```text
RawReceipt
---------
retrieval_id
source_id
dataset_id
requested_at
received_at
request_url
request_params
http_status
media_type
content_encoding
raw_sha256
bytes
storage_uri
source_etag
source_last_modified
collector_version
```

Storage model:

```text
raw_blob
    sha256 PRIMARY KEY
    storage_uri
    bytes
    first_seen

retrieval
    retrieval_id PRIMARY KEY
    source_id
    dataset_id
    raw_sha256
    requested_at
    received_at
    request metadata...
```

Same bytes retrieved on 30 consecutive days:

```text
1 raw_blob
30 retrieval records
```

That is correct.

The retrieval itself is part of the historical evidence.

Every normalized partition must reference one or more retrieval IDs.

---

# 5. Use full SHA-256 internally

The current storage layer truncates hashes:

```python
sha256(...).hexdigest()[:16]
```

Do not use truncated hashes as canonical blob IDs.

Use the full 64-character SHA-256 digest.

A short prefix may be used in filenames/UI, but database identity must remain:

```text
full_sha256
```

Tests:

```text
len(raw_hash) == 64
rehash(file) == raw_hash
```

---

# 6. Atomic writes

All raw and normalized writes should be crash-safe.

Pattern:

```text
write tempfile
fsync
atomic rename
record manifest transaction
```

Never expose half-written JSONL/Parquet files.

Test:

Simulate exception halfway through write.

Expected:

```text
no final artifact
no successful retrieval/partition record
```

---

# 7. Normalized storage: move from JSONL blobs toward Parquet

JSONL is acceptable for streams/small fixtures.

For historical analytical datasets use Parquet.

Examples:

```text
normalized/
  ons_labour/
    release=2026-07/
      part-000.parquet

  ashe/
    reference_year=2025/
    release=provisional/
      part-000.parquet

  apprenticeships/
    academic_year=2025-26/
      part-000.parquet

  companies_house/
    snapshot_date=2026-09-22/
      part-*.parquet
```

Use explicit source-native schemas.

Do not prematurely force all datasets into one table.

Layer 1 is:

```text
source-faithful
```

Layer 2 is:

```text
cross-source canonical
```

Add DuckDB as the verification/query layer.

Example:

```bash
powuk query "select count(*) from read_parquet('data/normalized/ons_labour/**/*.parquet')"
```

---

# 8. Add a normalized-partition ledger

Create:

```text
normalized_partition
--------------------
partition_id
source_id
source_release
period_start
period_end
schema_version
normalizer_version
record_count
unique_record_count
storage_uri
content_hash
raw_retrieval_ids
created_at
```

This solves:

```text
Where are the 175,193 ONS records?
Which raw workbook produced them?
Which parser version created them?
```

The critical invariant becomes enforceable:

```text
CollectorResult.rows
==
SUM(normalized_partition.record_count for run)
```

---

# 9. Coverage needs history, not latest-only overwrite

Current:

```text
PRIMARY KEY(source_id, partition)
INSERT OR REPLACE
```

keeps only latest coverage measurement.

Keep a current view, but preserve the history.

Use:

```text
coverage_check
--------------
check_id
source_id
partition
expected_count
collected_count
unique_count
coverage_ratio
checked_at
```

Then:

```text
current_source_coverage
```

can be a latest-row view.

This lets us detect source regressions:

```text
REFCOM
99.8%
99.9%
99.9%
62.1%  ← collector broke
```

---

# 10. Coverage must affect CollectorStatus

Currently a collector can return `SUCCESS` with a warning even when coverage is below 99%.

Enforce:

```text
coverage >= threshold
    → SUCCESS

0 < coverage < threshold
    → PARTIAL

coverage == 0 and source validly empty
    → SUCCESS_EMPTY

failed acquisition
    → FAILED
```

Do not let warnings carry semantic state.

For bounded sources:

```python
if coverage < manifest.coverage.minimum_ratio:
    return CollectorResult.partial(...)
```

---

# 11. Preserve schema hashes and schema evolution

Every structured acquisition should compute a source schema fingerprint.

Examples:

CSV:

```text
column names
column order
```

JSON:

```text
top-level shape
stable object keys
```

XLSX:

```text
sheet names
expected header cells
```

Persist:

```text
source_schema
-------------
source_id
schema_hash
first_seen
last_seen
example_retrieval_id
```

On unexpected schema:

```text
new hash
+
required fields missing
→ QUARANTINE_SCHEMA_CHANGE
```

Do not silently guess column meanings.

---

# 12. Replace heuristic ONS parsers with explicit source schemas

Current ONS skills/salaries normalizers still essentially save:

```text
sheet
raw_row[0:15]
```

That is structured archiving, not useful normalization.

Finish each official source properly.

For every ONS workbook:

```text
known sheets
known header rows
known dimensions
known measure columns
known period semantics
```

Implement versioned normalizers:

```text
ons_labour_v1
ons_job_skills_v1
ons_job_salaries_v1
ashe_table3_v1
```

Unknown workbook shape:

```text
PARTIAL / FAILED_SCHEMA
```

not heuristic substitution.

Preserve source row as optional JSON for replay, but expose typed fields.

---

# 13. ASHE must become historical, not only 2025 provisional

Discover and ingest all practical historical releases.

Preserve separately:

```text
reference_year
release_date
release_type
provisional/final/revised
SOC version
```

Do not overwrite:

```text
2024 provisional
```

with:

```text
2024 revised
```

Both are source vintages.

Acceptance:

```text
multiple years queryable
release lineage visible
known manually checked wage cells exactly match source
```

---

# 14. Finish Companies House as an entity baseline

Do not stop at counts.

Layer 1 should possess the relevant business universe.

Read SIC clusters from the canonical manifest.

For each SIC:

```text
paginate all relevant companies
persist raw responses
normalize companies
dedupe by company_number
retain all SIC codes
retain registered postcode
status
incorporation date
dissolution date where applicable
company type
```

Then run relevant streams continuously:

```text
companies
insolvency-cases
charges
```

Stream requirements:

```text
raw-first
durable cursor
crash replay
separate STREAM_KEY
cursor only advances after durable write
```

Baseline + stream gives the actual business-capacity garden.

Counts become QA metrics only.

---

# 15. REFCOM: resolve the enumeration correctly or remain explicitly aggregate

The newest code tries:

```text
0 ... total-1
```

Good direction.

But completion must be proven.

At end of run:

```text
published_total
unique_entities
failed_indexes
coverage_ratio
```

If:

```text
coverage < 99%
```

return `PARTIAL`.

Persist failed indexes for retry.

Do not restart 11k calls from zero every day.

After baseline:

```text
snapshot current register
diff against previous snapshot
```

If API does not permit reliable full enumeration:

```text
stage = aggregate_only
```

and use the national count only as an explicit aggregate series.

Do not fake entity completeness.

---

# 16. Finish Ofqual pagination

Current source historically exposed tens of thousands of qualifications.

A 500-row page is not Layer-1 completion.

Retrieve all pages.

Normalize qualification records with stable identifiers.

Preserve:

```text
qualification_number
title
organisation
level
status
operational dates
sector subject area
```

where source provides them.

Coverage must compare:

```text
API total
vs
unique normalized qualification IDs
```

---

# 17. Kill `evspark_trades` as a production dependency

It depends on:

```text
/root/ab/businesses/evspark/...
```

That violates clean-machine reproducibility.

Keep it only as:

```text
legacy/calibration fixture
```

Remove it from P0 production status.

Its replacement is:

```text
Companies House baseline
+
official labour statistics
+
registered trade/certification directories
```

Checkpoint must pass on a machine with no `/root/ab`.

---

# 18. Finish planning acquisition properly

Watermarking is an improvement, but verify that the upstream query really uses a changing temporal parameter rather than repeatedly paging from record zero.

Need:

```text
historical backfill
partitioned by source-supported date/change field

then

incremental:
last source watermark - overlap
→ now
```

Keep:

```text
source entity ID
source modified date
first_seen
last_seen
raw release versions
```

Also preserve **coverage of contributing authorities**.

Planning Data is not uniformly complete.

Create:

```text
planning_source_coverage
------------------------
authority
period
records
first_seen
last_seen
```

Never interpret expansion of dataset coverage as expansion of planning demand.

---

# 19. Finish procurement lifecycle acquisition

Both Contracts Finder and Find a Tender should retain OCDS releases, not merely current objects.

Store:

```text
ocid
release_id
release_date
tag/type
buyer
tender
award
supplier
value
CPV
location
modifications
```

Preserve each release version.

Historical backfill should proceed by source-supported date windows.

Incremental collection should overlap the last window.

Do not overwrite previous releases.

This gives Layer 2 access later to:

```text
published → tender → award → modification
```

without Layer 1 interpreting it.

---

# 20. Complete the missing core P0 source set

Layer 1 is not "full" with the current 16 sources.

Add the following before declaring completion.

## Labour / workforce

```text
Nomis / official labour supply
- employment
- self-employment
- occupation/geography where statistically valid

Claimant Count
- local monthly series

ONS Workforce Jobs / vacancies where relevant
```

Do not invent unavailable occupation×small-area precision.

Preserve published uncertainty/reliability flags.

## Business calibration

```text
ONS Business Demography
ONS UK Business: Activity, Size and Location
```

These calibrate Companies House against official economic business stock.

## Training pipeline

```text
DfE apprenticeship historical datasets
- starts
- participation
- achievements
- completion/achievement rates
- standards/frameworks
- provider
- geography where supplied

UKRLP
- UKPRN
- provider identity
- addresses/status
```

Backfill every accessible official release.

## Occupational structure

```text
Skills England Occupational Maps
```

If API key is pending:

```text
stage = blocked_auth
```

but request/use the official key.

Collect source data only; crosswalks belong in Layer 2.

## Qualified physical capacity

Start current snapshots now:

```text
MCS
OZEV authorised installers
Registered Competent Person Electrical
TrustMark
REFCOM
```

Use official downloadable/API/backend data where permitted before HTML scraping.

If only current state exists, today's snapshot is the beginning of history.

## Physical demand denominator

```text
EPC/open building-energy stock
```

Backfill available official data.

No modelling yet.

## Policy / mandatory demand

Create official-document collectors for:

```text
legislation
regulatory guidance
consultations
grants/subsidy programmes
```

Layer 1 stores documents and explicit metadata:

```text
publication date
effective date if explicitly supplied
deadline if explicitly supplied
department
document type
URL
raw document/text
```

Do not infer economic impact yet.

## Technology diffusion

Add relevant official ONS/BICS technology/AI-adoption releases where available.

This is raw explanatory context for later POW analysis.

---

# 21. Add source-discovery fallback rules for blockers

For every blocked source, follow:

```text
1. official bulk download
2. documented API
3. official service backend endpoint
4. official static CSV/XLSX/JSON
5. regulator/data.gov.uk mirror
6. permitted automated browser/search acquisition
7. manual periodic snapshot
8. aggregate proxy
9. explicitly blocked
```

Never write:

```text
"No API → scrape"
```

without exhausting higher-quality routes.

Every blocker must have:

```text
blocker_reason
attempted_routes
fallback
owner/action
next_check_date
```

---

# 22. Every source gets a fixture

No source can be `verified` without:

```text
tests/fixtures/{source_id}/
```

containing a small representative source payload.

Each source must have tests for:

```text
raw parsing
record count
stable source IDs
required fields
null handling
schema drift
idempotent normalization
coverage
provenance
```

For complicated spreadsheets, include manually verified golden cells.

---

# 23. Add live smoke tests separately

Use:

```text
@pytest.mark.live
```

for network tests.

They should verify:

```text
endpoint reachable
auth works
response schema recognizable
one tiny page/download works
```

Do not run full backfills in CI.

Offline fixture tests must remain deterministic.

---

# 24. Add replay testing

Critical Layer-1 capability:

```bash
powuk replay RAW_HASH
```

It should:

```text
locate raw artifact
choose correct parser version
normalize again
produce same normalized content hash
```

This proves raw retention is actually useful.

Acceptance:

```text
same raw
same normalizer version
=
same normalized result
```

---

# 25. Add idempotency tests across real collectors

For each fixture:

```text
normalize once
normalize again
```

Expected:

```text
same logical record IDs
same row counts
same content hash
```

Incremental rerun with no upstream changes:

```text
0 new logical records
```

but a new retrieval observation may legitimately exist.

---

# 26. Add crash/recovery tests

For paginated/stream sources simulate failure:

```text
after raw download
after page 4
after normalized write
before watermark update
after watermark update
```

Recovery must create:

```text
no missing records
no duplicate logical records
no cursor advancing past durable data
```

This is essential for unattended gardening.

---

# 27. Add staleness from manifest SLAs

`HealthRegistry` already supports staleness.

Wire manifest-specific:

```text
max_staleness_hours
```

into runtime health.

Examples:

```text
hourly source → stale after ~3h
daily register → stale after ~36–48h
annual release → stale semantics based on release cadence, not 48h
```

Do not use one global staleness threshold.

---

# 28. Distinguish source freshness from collector freshness

Track both:

```text
last_successful_fetch
source_latest_timestamp
```

A collector can be working perfectly while upstream hasn't published new data.

That should not show as collector failure.

Expose:

```text
collector_lag
source_lag
```

separately.

---

# 29. Make status machine-actionable

Create:

```bash
powuk status --json
powuk status
```

Fields per source:

```text
source_id
stage
priority

last_attempt
last_success
last_source_timestamp

collector_status
schema_status

raw_artifacts
raw_bytes
normalized_records

historical_start
historical_end

expected_count
unique_count
coverage_ratio

backfill_partitions_total
backfill_partitions_done

watermark
staleness

blocker
```

No prose parsing required.

---

# 30. Implement `powuk verify`

This is the final checkpoint gate.

Output:

```text
SOURCE             RAW   NORMALIZED  HISTORY     COVERAGE  LIVE   SCHEMA  PROVENANCE
ons_labour         PASS  PASS        PASS        100%      PASS   PASS    PASS
ashe_wages         PASS  PASS        PASS        100%      PASS   PASS    PASS
apar               PASS  PASS        N/A         100%      PASS   PASS    PASS
refcom             PASS  PASS        FROM-2026   99.9%     PASS   PASS    PASS
...
```

Exit non-zero when any required P0 source fails.

Statuses:

```text
PASS
PARTIAL
BLOCKED_AUTH
BLOCKED_SOURCE
NOT_IMPLEMENTED
```

Blocked external sources do not have to magically pass, but must be explicit.

---

# 31. Define Layer-1 completion numerically

A P0 source is `VERIFIED` only when:

```text
manifest valid
collector fixture tests pass
raw retrieval persisted
normalized output persisted
normalized count truthful
provenance link intact
schema fingerprint recorded
coverage threshold satisfied
historical backfill exhausted where available
incremental/snapshot mode operational
watermark/cursor durable where applicable
health SLA configured
live smoke test succeeds or explicit external blocker recorded
```

A source cannot become verified because:

```text
"collector returned rows"
```

---

# 32. Add a global Layer-1 completeness report

Create:

```text
data/state/layer1_checkpoint.json
```

Example:

```json
{
  "checkpoint": 1,
  "generated_at": "...",
  "p0_sources": 24,
  "verified": 21,
  "partial": 1,
  "blocked_external": 2,
  "historical_backfill_complete": 19,
  "snapshot_sources_active": 5,
  "streams_active": 3,
  "tests_passed": 0,
  "tests_failed": 0
}
```

The exact counts depend on final source selection.

This becomes the handoff to Layer 2.

---

# 33. Clean repository before declaring Layer 1 complete

Archive/remove:

```text
review2.md
review3.md
review4.md
review5.md
review6.md
```

They were useful working notes, but should not become architecture.

Likewise remove/archive duplicated old:

```text
SOURCE_MATRIX.csv
source_priority_matrix.csv
obsolete source docs
```

Generate source documentation from manifests.

Keep canonical docs:

```text
README.md
THESIS.md
AGENTS.md
LAYER1.md
COMPANIES_HOUSE_REF.md
```

Move non-Layer-1 model code to a clearly separate location if necessary, but do not spend time refactoring it beyond preventing dependency contamination.

---

# 34. Final repository shape

Target:

```text
powuk/
  layer1/
    collectors/
      business/
      certification/
      grid/
      labour/
      planning/
      policy/
      procurement/
      property/
      training/

    sources/
      *.yaml

    collector.py
    fetch.py
    storage.py
    state.py
    health.py
    manifest.py
    runner.py
    cli.py

  data/
    raw/
    normalized/
    quarantine/
    state/

  tests/
    fixtures/
    test_storage.py
    test_manifests.py
    test_coverage.py
    test_replay.py
    test_incremental.py
    test_schema_drift.py
    collectors/

  layer2/
  research/

  README.md
  THESIS.md
  AGENTS.md
  LAYER1.md
```

---

# 35. Final source set

The minimum POWUK Layer-1 garden should cover these source families:

```text
GRID / POWER
NESO demand
NESO generation
PV Live
actual DNO constraint/headroom datasets where obtainable

LABOUR DEMAND
ONS online job demand
ONS job skills
ONS job salaries
official vacancies/workforce series

LABOUR SUPPLY
Nomis / ONS workforce
self-employment
claimant count

WAGES
ASHE historical
relevant earnings releases

BUSINESS CAPACITY
Companies House entity baseline
Companies House company stream
insolvency stream
charges stream
ONS business stock/demography

TRAINING
APAR
UKRLP
DfE apprenticeship starts
DfE achievements/completions
DfE vacancies/history
Ofqual
Skills England

CERTIFIED CAPACITY
REFCOM
MCS
OZEV
Competent Person Electrical
TrustMark

PHYSICAL DEMAND
planning
Contracts Finder
Find a Tender
EPC/building stock

POLICY
legislation
regulatory publications
grants/subsidies

TECHNOLOGY
relevant official AI/technology-adoption series
```

Anything outside those families can wait unless it is exceptionally cheap and obviously relevant.

---

# 36. Final acceptance tests

Before calling Layer 1 complete, perform these end-to-end checks.

### Random provenance audit

Pick 100 random normalized rows across multiple sources.

For every row prove:

```text
normalized row
→ normalized partition
→ retrieval ID
→ raw hash
→ raw artifact exists
→ hash verifies
```

Expected:

```text
100/100
```

### Completeness audit

For every bounded source with a published count:

```text
unique collected / expected
```

must satisfy its threshold.

### Historical audit

For every backfillable source:

```text
earliest available period
→ latest available period
```

must have no unexplained holes.

### Replay audit

Pick 20 raw artifacts.

Replay normalization.

Expected:

```text
identical normalized content hashes
```

### Freshness audit

Stop one collector artificially.

After its SLA:

```text
status → STALE
```

Restart it:

```text
status → HEALTHY
```

### Crash audit

Crash a paginated source mid-run.

Restart.

Expected:

```text
no hole
no duplicate logical rows
correct watermark
```

### Clean-machine audit

On a fresh machine/VPS:

```text
git clone
install requirements
set env keys
powuk manifests check
powuk collect --smoke
pytest
```

No dependency on:

```text
/root/ab
manual files
untracked local state
old databases
```

---

# Definition of done

Layer 1 is complete when the following statement is true:

> POWUK continuously preserves the best available official and legitimate source data describing UK physical capacity, labour, training, firms, wages, certifications, infrastructure demand and policy; backfills all reconstructable history; begins accumulating irrecoverable current-state history where backfill is impossible; preserves raw evidence and release vintages; normalizes every source faithfully; measures its own completeness; detects schema/source failures; and can reproduce every normalized record from raw evidence.

At that point:

```text
FREEZE LAYER 1 ARCHITECTURE.
```

New sources may continue to be added, but only through the same manifest/collector/test contract.

Then begin Layer 2:

```text
source-specific observations
        ↓
entity resolution
geography
occupation
capability
company/provider joins
        ↓
Capability × Geography × Time
```

Do not start Layer 2 until:

```bash
powuk verify
```

passes all non-externally-blocked P0 sources.

The latest architecture is close enough that I would treat this as the **last refactor**. The most important final changes are: collapse the two manifest systems, remove the remaining infrastructure duplication from `server.py`, turn raw/retrieval/normalized provenance into one coherent contract, finish the missing core P0 sources, and make `powuk verify` the hard Layer-1 gate.

After that, don't keep "improving" Layer 1. Keep the collectors running and accumulating time. That is when the garden actually starts becoming valuable.

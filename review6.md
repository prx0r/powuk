# powuk review6.md

This is the first push where I'd say POWUK is **starting to become Level 1 rather than merely describing Level 1**. `bda2693` adds several real improvements, and `69276da` adds the correct missing wage dimension.

But there is a critical pattern in the latest code: **several collectors report the size of the full dataset while only persisting a sample of it.** For a data garden, that is worse than an obvious stub because status says "3,906 records" while only 500 records have actually been retained in the normalized artifact.

For Level 1, the invariant needs to be:

```text
If collector says N normalized records,
I can query N normalized records.
```

Not "we parsed N in RAM once."

## The most important current bugs

### 1. ONS says ~175k normalized, but stores only 1,000

Current code:

```python
records = [...]
...
store(
    conn,
    "labour",
    "ons_demand",
    json.dumps(records[:1000]).encode(),
    len(records)
)
```

This is a severe Level-1 failure.

The manifest says:

```text
row_count = 175,193
```

while the stored normalized payload contains:

```text
1,000
```

Everything after row 1,000 disappears when the process exits.

Remove **all sampling from production ingestion**.

Sampling belongs only in:

```text
tests/fixtures/
debug/
preview()
```

Never the garden.

### Test

For every normalized artifact:

```python
assert actual_record_count(artifact) == manifest.row_count
```

That one test would catch this class of problem everywhere.

---

### 2. ASHE has exactly the same problem

Commit advertises:

> 3,906 wage records

but:

```python
json.dumps(records[:500])
```

stores 500.

So right now the actual garden contains at most 500 wage records from that run.

Fix immediately.

And don't store thousands/millions of rows as giant JSON arrays long term. This is where Parquet starts making sense:

```text
normalized/
  ashe/
    release=2025-provisional/
      table=3/
        part-000.parquet
```

Then DuckDB can query it directly.

---

## 3. REFCOM still isn't entity-level ingestion

This one is especially important.

The commit says:

> entity-level REFCOM

but code does:

```python
for idx in range(0, min(500, total), 10):
```

So with 11,298 companies it tests indices:

```text
0
10
20
30
...
490
```

That's at most **50 companies**.

Then it stores:

```json
{
  "total_count": 11298,
  "sample": [...]
}
```

That's not an entity collector. It's a sample probe.

For Level 1, choose one of two honest states:

```text
REFCOM_COUNT
status = VERIFIED_AGGREGATE
```

or actually enumerate:

```text
REFCOM_ENTITIES
expected ≈ 11,298
collected ≈ 11,298
```

If `GetByIndex` genuinely supports sequential enumeration, iterate every index, rate-limited and resumable:

```text
0 → total-1
```

Checkpoint progress:

```text
0/11,298
1,000/11,298
...
11,298/11,298
```

If that's not possible, mark the entity dataset `BLOCKED/PARTIAL`; don't call it complete.

### Excellent completeness test

Because REFCOM conveniently exposes a total:

```python
coverage = collected_unique_entities / published_total

assert coverage >= 0.99
```

If 50 / 11,298:

```text
coverage = 0.44%
```

That should scream `PARTIAL`.

---

# 4. APAR says "ALL fields", but doesn't preserve all fields

The comment says:

```text
Normalizes ALL fields from the CSV
```

but code explicitly selects about eight fields:

```python
ukprn
name
application_type
start_date
status
application_determined_date
can_deliver_apprenticeships
can_deliver_apprenticeship_units
```

That's not necessarily bad—those may be the useful columns—but don't claim all fields.

For Level 1, I'd do:

```python
source_record = dict(row)
```

and separately canonical fields:

```text
ukprn
provider_name
status
...
```

Best pattern:

```text
source payload
+
canonical projection
```

So new source columns aren't silently lost.

---

# 5. Companies House has moved from wrong → useful proxy, but isn't yet the company garden

Using:

```text
advanced-search + sic_codes
```

is much better.

But it still only asks for:

```text
size=1
```

and stores a **count**.

So it currently answers:

```text
How many active firms match SIC X?
```

It does not yet give us:

```text
which firms
where they are
when incorporated
whether they're entering/leaving
their complete SIC combinations
```

For Level 1, we absolutely need the entity baseline.

The real Companies House build should now be:

```text
SIC 43210
   ↓
paginate ALL companies
   ↓
company_number
name
status
incorporation_date
postcode
SIC[]
   ↓
normalize
   ↓
repeat relevant SICs
   ↓
dedupe by company_number
```

Then stream forward from the baseline.

Otherwise you can never calculate properly:

```text
firm formation
firm exit
firm migration
regional company stock
provider ↔ Companies House resolution
```

Counts alone won't get POWUK there.

---

# 6. Your configured SIC universe and implemented SIC universe disagree

`sources.yaml` has richer clusters:

```yaml
electrical: ["43210", "33140", "46520"]
hvac: ["43220", "43290"]
...
```

But `server.py` uses only:

```python
"electrical": "43210",
"hvac": "43220",
...
```

So even after introducing the registry, the collector ignores it.

This proves `sources.yaml` is still not truly driving ingestion.

For Level 1:

```python
config = source("ch_capacity")
for cluster, sic_codes in config["sic_clusters"].items():
    ...
```

There must be **one source of truth**.

### Test

Change a SIC in YAML in a fixture.

Assert collector request changes.

If it doesn't, config isn't executable.

---

# 7. Planning "bounded windows" are not windows

Current code:

```python
start=0
...
start=4900
```

every run.

That's just:

> fetch the first 5,000 records repeatedly.

It isn't an incremental bounded window.

Likewise Contracts Finder repeatedly grabs the first 1,000.

A real window needs a temporal/watermark constraint:

```text
modified_since = last_success - overlap
modified_before = now
```

or historical partitions:

```text
2018-01
2018-02
...
2026-09
```

If the upstream API doesn't support a clean cursor, maintain stable IDs and crawl until reaching already-seen records—but the collector must actually progress through history.

Right now you can run it for a year and still have broadly the same initial slice.

That defeats the garden.

---

# 8. Find a Tender is still only 50 records

The comment now honestly says:

```text
Single fetch
```

Good—at least it isn't pretending pagination works.

But Level 1 cannot stop there.

If that endpoint genuinely has awkward pagination, find another official access pattern:

```text
date ranges
release packages
bulk files
OCDS download
search query windows
```

If none exists, implement historical discovery through published releases.

The requirement is not:

> use pagination.

The requirement is:

> eventually acquire the complete relevant history.

Those are different things.

---

# 9. Ofqual is capped at 500

Current:

```text
?pageSize=500
```

Yet docs say:

```text
52,887 total
```

So this is another hidden 1% collector.

Same lesson as REFCOM.

Level 1 source status needs:

```text
expected_records
collected_records
coverage_ratio
```

Across **every bounded source**.

Then these problems become impossible to hide.

I'd add this immediately:

```text
source_coverage
---------------
source_id
partition
expected_count
collected_count
unique_count
coverage_ratio
complete
checked_at
```

That may be the single best structural addition now.

---

# 10. ASHE is the right data, but only one release

Adding wages is exactly correct.

But Level 1 philosophy is:

```text
ingest as much historical data as possible
```

Currently the URL is hardcoded:

```text
2025 provisional
```

We want the historical editions too.

For ASHE:

```text
release discovery
↓
2021
2022
2023
2024
2025
...
```

and ideally earlier where harmonizable.

Preserve:

```text
reference_year
release_type = provisional/final/revised
release_date
SOC version
```

Don't overwrite a provisional figure when final/revised appears.

This becomes an excellent temporal garden.

---

# 11. Be careful: the ASHE parser may be extracting the wrong cells

The code assumes:

```python
row[0] = region
row[1] = SOC
row[2] = occupation
row[3] = hourly_pay
row[4] = annual_pay
```

ASHE workbooks are usually much more structurally complex than that: multiple sheets, measures, percentiles, sex/work patterns, metadata/header rows, suppression markers, etc.

The fact it produced 3,906 rows does not establish that those rows mean what the schema says.

This needs a **golden semantic test**, not merely "parser returned rows".

Take 5–10 manually verified cells from the workbook:

```text
known region
known occupation
known measure
known value
```

and assert normalized output matches exactly.

If one fails, parser is wrong.

This is important for all spreadsheets with complex headers.

---

# 12. ONS labour parser is also too heuristic

It guesses:

```python
period_col = first header containing "period" or "date"
soc_col = first containing "soc" or "occupation"
geo_col = first containing "region" or "area"
```

Then only preserves:

```text
first 10 raw columns
```

This is useful exploration code, not a trustworthy normalizer.

For official datasets, use **dataset-specific explicit mappings**.

Example:

```python
ONS_JOB_ADS_SCHEMA_V1 = {
   ...
}
```

Fail loudly when expected headers disappear.

Do not dynamically guess a different interpretation when ONS changes the workbook.

That's how silent historical corruption happens.

### Desired behavior

```text
known schema → normalize
unknown schema → QUARANTINE_SCHEMA_CHANGE
```

not:

```text
"eh, this column contains 'area', good enough"
```

---

# 13. We still have double raw writes

ONS:

```python
raw_path.write_bytes(d)
```

then:

```python
store(... d ...)
```

So the same payload is written twice.

APAR does similar.

ASHE writes ZIP manually and then writes normalized data via `store()`.

This is a symptom that:

```text
raw
normalized
```

still aren't first-class separate APIs.

Level 1 should settle this now:

```python
raw = raw_store.put(...)
normalized = normalized_store.write(...)
```

Do not call both of them `store()`.

---

# 14. `store()` is still being used for raw and normalized data

This is increasingly dangerous.

For example:

```python
store(conn, "labour", "ashe_wages", json.dumps(records...))
```

puts normalized data under:

```text
data/raw/labour/
```

So your "raw" tree now contains derived JSON.

That destroys the conceptual separation.

I'd require:

```text
data/raw/
data/normalized/
data/state/
data/quarantine/
```

or R2 prefixes equivalent.

Nothing derived may enter `/raw`.

Raw means bytes retrieved from source, period.

---

# 15. Normalized data needs typed tables/Parquet now

We're at the point where giant JSON blobs stop being appropriate.

For Level 1 I'd create straightforward normalized datasets:

```text
providers
certifications
companies
job_demand
wages
qualifications
training_providers
planning_applications
procurement_releases
```

Each one Parquet.

Don't prematurely force every source into one universal economic table.

Level 1 should preserve source fidelity.

Example:

```text
normalized/ons_job_demand/
normalized/ashe_wages/
normalized/apar/
normalized/refcom/
```

Layer 2 can unify them onto:

```text
Capability × Geography × Time
```

That's an important distinction.

**Level 1 should be source-clean, not theory-clean.**

---

# 16. That's how I'd define your levels now

This is worth freezing.

```text
LEVEL 0
source discovery
API exploration
documentation
fixtures

LEVEL 1  ← YOU ARE HERE
raw acquisition
historical backfill
continuous snapshots/streams
source-faithful normalization
provenance
coverage/completeness
monitoring
schema-drift detection

LEVEL 2
canonical entity resolution
geography harmonisation
occupation/SIC/capability mappings
cross-source joins
consistent time series

LEVEL 3
POW economics
scarcity
shadow prices
entry/exit
Seesaw
lag models
AGI impact
opportunities
```

That helps enormously because it stops the coding agents from trying to solve everything simultaneously.

At Level 1:

> **Don't ask what the data means yet. Make sure we own the data correctly.**

---

# 17. The existing tests are now the largest process failure

Despite all these ingestion changes, `tests/test_core.py` is **completely unchanged**.

It still tests:

```text
Region
Constraint.gap
12 regions
```

Those are basically Level 3 concepts.

Ironically, the tests currently validate the least important part of the repo.

For Level 1, I would delete/deprioritize those tests and immediately add:

* `test_raw_store.py`: same bytes, different retrievals; hash correctness; no overwrite.
* `test_ons_job_demand.py`: fixture → exact expected rows; **175,193 parsed means 175,193 persisted**.
* `test_ashe.py`: golden verified workbook cells; full persisted count; provisional/final vintages stay separate.
* `test_apar.py`: all source rows retained; UKPRN stable; source column changes trigger schema check.
* `test_refcom.py`: enumerate mocked 23 records and get 23 unique entities; no every-10th sampling.
* `test_companies_house.py`: mocked SIC has 251 companies over pages → exactly 251 persisted and deduped.
* `test_coverage.py`: source claiming 10,000 with only 500 persisted is `PARTIAL`, never `VERIFIED`.
* `test_incremental.py`: second run fetches only new/overlap partition, not page zero forever.
* `test_provenance.py`: random normalized record can resolve source raw hash/artifact.
* `test_schema_drift.py`: renamed required source column → quarantine/failure, not guessed normalization.

I'd make these tests the immediate next task before adding more sources.

---

# 18. What I would build next at Level 1

The new ASHE collector is directionally correct, but I would **pause new source additions for one iteration** and make the storage contract solid.

Then start the next source wave:

```text
P0 BACKFILL
------------
DfE apprenticeship history
Nomis labour/self-employed
ASHE historical releases
ONS job skills
ONS job salaries
ONS business demography
UK Business Activity/Size/Location
UKRLP
EPC

P0 SNAPSHOT FROM NOW
--------------------
REFCOM full entities
MCS installers
OZEV installers
Competent Person Electrical
TrustMark

P0 EVENT/CHANGE
---------------
Companies House relevant-company stream
procurement
planning
apprenticeship vacancies
policy/regulatory documents
```

The distinction matters:

**Backfillable source?** Exhaust history now.

**Current-state register?** Start snapshotting today.

**Event stream?** Get reliable cursoring running today.

---

## Overall assessment

There is a real jump from the previous state.

Before:

```text
download source
count it
claim collector works
```

Now you have the beginnings of:

```text
download source
retain raw
parse entities/records
retain history
```

But the current code has a dangerous **sampling illusion**:

```text
parsed 175,193 → saved 1,000
parsed 3,906 → saved 500
REFCOM total 11,298 → sampled ~50
Ofqual total 52k → fetched 500
```

That is the main thing I'd attack next.

The Level-1 northstar should be incredibly boring:

> **For every source we claim to possess, prove completeness, preserve the exact raw evidence, persist every normalized record, preserve every historical vintage, and know exactly where collection is partial.**

Once that is true for 20–30 core sources, POWUK has a genuinely valuable Level-1 garden. Then Level 2 can turn those clean source-specific datasets into the unified UK physical-capacity graph.

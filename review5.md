# powuk review5.md

Latest push `89236c3` is mostly a **hardening/documentation patch**, not a structural checkpoint leap. The useful change is retry handling plus explicit `ok/empty/error`; the bigger value is actually in `DATA_SOURCES.md` because it exposes exactly where the blockers are.

I would not repeat the prior review. The new issues I see are these.

## 1. The health-state change is still semantically broken

The new runner does:

```python
if r == 0 and "error" not in str(r).lower():
    state(..., "ok")
```

That condition is effectively meaningless because `r` is numeric.

More importantly, collectors still catch exceptions internally and return `0`.

So:

```text
REFCOM HTTP 500
→ collector catches exception
→ returns 0
→ runner marks OK/EMPTY
```

The runner cannot infer collector health from row count.

### Fix

Every collector should return:

```python
CollectorResult(
    status="success" | "success_empty" | "partial" | "failed" | "blocked",
    rows=...,
    artifacts=[...],
    cursor=...,
    warnings=[...],
    error=None,
)
```

This is exactly one of the stronger ideas already implemented conceptually in `ographuk`: distinguish `SUCCESS_EMPTY`, `FAILED`, and `PARTIAL`.

### Test

Mock:

```text
200 + 0 records
500
429 then 200
malformed JSON
page 3 fails after pages 1-2
```

Expected:

```text
SUCCESS_EMPTY
FAILED
SUCCESS
FAILED
PARTIAL
```

Never infer any of these from `rows`.

---

## 2. Retry handling can stall the entire collector system

`server.py` uses async orchestration, but all the actual collectors are synchronous blocking functions.

Now `fetch()` can do:

```text
sleep(60)
sleep(...)
network timeout
```

inside the event loop.

Because all collector functions execute synchronously in the same event loop, one 429 can block **every other collector**.

That's a new structural problem introduced by adding retries.

### Better options

Simplest:

```text
one normal synchronous scheduler process
```

No pretend async.

Or execute collector bodies with:

```python
await asyncio.to_thread(fn, conn)
```

but SQLite connection handling then needs to be per worker/thread.

Better longer-term:

```text
runner
→ launches isolated collector process/job
→ collector opens own DB/state connection
```

A broken source should never stall Companies House, ONS, APAR, etc.

### Test

Create:

```text
collector A sleeps 10 seconds
collector B returns immediately
```

Assert B completes immediately rather than after A.

This should be a mandatory scheduler test.

---

# 3. `DATA_SOURCES.md` confirms several "live" collectors are still metadata probes

Most obvious:

### UKPN

Document says:

> "flexibility dispatches, embedded capacity, network headroom"

but actual endpoint is the **dataset catalogue**.

So the asserted dataset and collected dataset don't match.

This should become a machine-checkable invariant:

```text
source_claim
dataset_schema
```

For UKPN, either find actual dataset IDs and ingest them or mark:

```text
status: discovery_only
```

Do not list it as a completed collector.

### Test

For every source, define expected fields.

Example:

```yaml
ukpn_flex:
  required_any:
    - constraint
    - capacity
    - flexibility
    - location
```

A catalogue response containing only metadata must fail semantic validation.

---

# 4. Do not let blockers become "scrape it"

The new source document says:

```text
MCS: no public API (scrape)
OZEV: no public API (scrape)
Competent Person: no public API (scrape)
```

That's too quick.

Use a source-resolution ladder:

```text
1 official downloadable dataset
2 official API
3 official search/backend endpoint
4 official static file/document
5 data.gov.uk / regulator mirror
6 permitted browser acquisition
7 manual snapshot
8 abandon / aggregate proxy
```

Do not start HTML scraping until 1–5 are exhausted.

For example, OZEV has an official postcode-based installer finder and authorised-installer list maintained by government. ([GOV.UK][1])

Even if there is no documented API, inspect the official service's network interface and downloadable assets first.

Same principle for MCS and Competent Person.

---

# 5. Skills England is not actually blocked

`DATA_SOURCES.md` says:

```text
Skills England Occupational Maps
API returns 403
```

The official documentation explains exactly what that means: **the API requires an API key passed in the `X-API-KEY` header**, and there's a form to request one. A 403 generally indicates an issue with the key or how it is supplied. ([Occupational Maps][2])

So this is not a technical blocker.

### Route

Request key, then ingest:

```text
occupations
SOC mappings
typical job titles
duties/KSBs
progression relationships
technical education products
green themes
```

This endpoint is particularly valuable because `occupation.dutiesKSB` and progression are directly exposed. ([Occupational Maps][2])

### Test

Use one known occupation ID fixture:

```text
OCC0135
```

Assert:

```text
occupation exists
SOC exists when expanded
KSB expansion parses
products parse
same payload normalizes deterministically
```

Also live test:

```text
missing key → BLOCKED_AUTH
invalid key → BLOCKED_AUTH
valid key → SUCCESS
```

Not generic FAILED.

---

# 6. DfE apprenticeship history is not blocked either

The repo says:

```text
DfE Apprenticeships Historical — URL issues
```

The official Explore Education Statistics release exposes **downloadable underlying datasets**, including:

* starts
* achievements
* enrolments
* participation
* monthly starts
* vacancies

with large CSV/ZIP files. ([Explore Education Statistics][3])

There is also a 649,920-row subject time-series dataset covering starts/enrolments/achievements. ([Explore Education Statistics][4])

This is exactly what Checkpoint 1 needs.

### Alternative to fragile URLs

Do not hardcode the current ZIP URL.

Build a release-discovery collector:

```text
release landing page
→ discover dataset links
→ persist release manifest
→ download each underlying file
```

Then every future release gets discovered automatically.

### Test

Fixture one archived release HTML/API response.

Assert:

```text
all expected dataset families discovered
duplicate links deduped
release date captured
ZIP hash persisted
re-run does not duplicate logical data
```

This should be a priority before adding another niche collector.

---

# 7. ONS skills and salary sources are also not blocked

The source document says:

```text
ONS Job-ad Skills — need URL
ONS Job-ad Salaries — need URL
```

The official datasets exist directly:

**Skills/competencies:** January 2017–September 2025, downloadable XLSX. ([Office for National Statistics][5])

**Online job advert salaries:** January 2017–May 2025, downloadable XLSX. ([Office for National Statistics][6])

So these should move immediately from:

```text
BLOCKED
```

to:

```text
BACKFILL_READY
```

There's also a current monthly **Textkernel new online job adverts** ONS series with previous version files exposed, which is particularly useful because the page preserves superseded releases. ([Office for National Statistics][7])

That means you can test revision preservation properly.

### Test

For ONS source discovery:

```text
latest edition
previous editions
download href
release date
superseded date/reason
```

Then assert historical releases remain distinct artifacts.

This is a perfect test case for:

```text
same economic period
different release vintage
```

---

# 8. The ONS collector still measures row count rather than data

This is still a structural issue, but the new push makes it more obvious because `DATA_SOURCES.md` says:

> "What we store: Raw XLSX + observation (total rows)"

For Checkpoint 1, that's insufficient.

The row count is monitoring metadata.

It is not an economic observation.

Don't put:

```text
ons_labour_rows = 175193
```

into the same observation abstraction as:

```text
electrician vacancies in Oldham = 342
```

Those are different domains.

Create:

```text
ingestion_metric
```

versus:

```text
economic_observation
```

### Test

Schema test should reject:

```text
metric = source_rows
```

from the economic observation table.

Operational metrics belong in collector/run tables.

---

# 9. The repo now has four sources of source truth

There are now:

```text
SOURCES.md
DATA_SOURCES.md
config/sources.yaml
data/SOURCE_MATRIX.csv
schemas/source_priority_matrix.csv
```

This is already drifting.

That's a structural problem.

One machine source of truth:

```text
config/sources.yaml
```

Then generate:

```text
DATA_SOURCES.md
```

from it.

Delete or archive the others.

Otherwise you'll eventually have:

```text
MCS = P0 in one file
MCS = A+ in another
MCS absent in YAML
```

### Test

CI test:

```text
generate DATA_SOURCES.md
git diff --exit-code
```

If hand-edited docs differ from config, CI fails.

---

# 10. The registry still isn't executable

Related point: `sources.yaml` is not driving `server.py`.

If changing:

```yaml
cadence: daily
```

doesn't change scheduling, then the registry isn't configuration—it's another document.

Checkpoint architecture should be:

```text
sources.yaml
→ SourceConfig
→ collector registry
→ scheduler
```

Collector code provides transformation logic, not cadence/auth/URL duplication.

### Test

Set test source cadence to `17`.

Instantiate runner.

Assert runner schedules interval 17 without editing Python.

Also assert all collector IDs have exactly one config entry.

---

# 11. Nomis is a research blocker, not an engineering blocker

The agent says:

```text
Need to find URL
```

Don't let coding agent burn time guessing endpoint strings.

Split roles:

```text
source discovery
vs
collector implementation
```

For Nomis, use its API/database metadata to identify datasets and construct queries for occupation/geography/employment/self-employment.

If detailed occupation × local geography isn't available at desired granularity in one dataset, fallback cleanly:

```text
APS occupation estimates at broader geography
+
BRES industry employment at finer geography
+
Companies House/provider counts
```

Do not fabricate local occupational precision by joining incompatible denominators.

### Test

For any labour series store:

```text
geography_level
SOC_level
estimate
sample/error/reliability marker where provided
```

Then test aggregation only across compatible geography/SOC definitions.

---

# 12. Apprenticeship advert API key is not a blocker to history

The document says:

```text
Apprenticeship Display Advert API — needs API key
```

Fine for live acquisition.

But the DfE underlying apprenticeship statistics already include an **underlying apprenticeship vacancies dataset**. ([Explore Education Statistics][3])

So do both:

```text
historical:
DfE vacancies dataset

forward:
live advert API once key arrives
```

That's an important general pattern:

> API auth unavailable should not block historical backfill if an official statistical archive exists.

### Test

When live API becomes available, overlap both sources for one period.

Compare:

```text
counts
dates
standard IDs
geography
```

Document expected differences.

This is a source-calibration test.

---

# 13. Do not store "current directory count" when entity-level acquisition is possible

REFCOM is the clearest case.

The current collector stores only:

```text
11,298
```

A count is useful for completeness verification, not as the primary garden.

If entity extraction is blocked, use two modes:

```text
aggregate_probe
entity_collector
```

and mark:

```text
completeness_class: aggregate_only
```

rather than pretending the source is done.

Alternative if individual records cannot legally/reliably be harvested:

```text
regional aggregate queries
```

if search interface permits postcode/area counts.

Even geography-conditioned aggregate history is much better than national total.

### Test

If entity collector expected count is 11,298:

```text
abs(entity_count - official_count) / official_count < threshold
```

If >2–5%, flag `PARTIAL`.

This is exactly how the official count becomes useful.

---

# 14. Preserve source coverage, not just source values

Planning Data is explicitly incomplete.

Right now POWUK can accumulate planning applications but may interpret changes as economic changes when they are actually **coverage changes**.

Need:

```text
coverage_observation
```

Examples:

```text
which LPAs represented
records per LPA
earliest/latest period
dataset coverage metadata
schema version
```

Then:

```text
planning applications +40%
```

isn't interpreted as demand +40% if 30 new councils entered the feed.

This applies to every evolving government dataset.

### Test

Simulate:

```text
period A = 50 councils
period B = 75 councils
```

Assert naive national growth series is marked incomparable unless coverage-adjusted.

---

# 15. Retry policy needs `Retry-After`, jitter, and classification

Current:

```python
429 → sleep(60)
```

is crude.

Use:

```text
Retry-After header if present
exponential backoff
small jitter
retry only transient codes
```

Rough categories:

```text
408 / 425 / 429 / 500 / 502 / 503 / 504 → retry
400 / 401 / 403 / 404 → normally don't retry
```

A 403 should become:

```text
BLOCKED_AUTH
```

not three wasted attempts.

### Test

Mock status sequence:

```text
429 Retry-After: 2
200
```

Assert exactly one retry and delay honors header.

Also:

```text
403
```

assert no retry.

---

# 16. Documentation contains assertions that aren't proven by code

Examples:

```text
"Companies House by SIC code"
```

implementation still uses textual company search.

```text
"Find a Tender paginated"
```

current implementation still appears to make one request.

```text
"UKPN flexibility dispatches"
```

implementation retrieves dataset catalogue.

This is more dangerous than missing documentation because it makes humans think Checkpoint 1 is healthier than it is.

Introduce a generated status field:

```yaml
implementation:
  stage: discovery | raw | normalized | monitored | verified
```

Example:

```yaml
ukpn_flex:
  stage: discovery
```

Only tests can promote to `verified`.

---

## What I would tell the coding agent to do next

Not another "hardened infrastructure" commit.

Make the next push a **truthfulness + blocker-resolution commit**:

1. Introduce `CollectorResult` with explicit status semantics.
2. Remove internal exception swallowing.
3. Prevent synchronous retry sleeps from blocking other collectors.
4. Make `sources.yaml` executable and generate docs from it.
5. Add implementation stages (`discovery/raw/normalized/verified`).
6. Resolve the fake blockers:

   * Skills England → request/use API key and `X-API-KEY`. ([Occupational Maps][2])
   * DfE history → release-discovery over downloadable underlying files. ([Explore Education Statistics][3])
   * ONS skills → direct official dataset. ([Office for National Statistics][5])
   * ONS salaries → direct official dataset. ([Office for National Statistics][6])
   * apprenticeship vacancy history → DfE underlying vacancy dataset while live API waits. ([Explore Education Statistics][3])
7. Change UKPN status to `discovery` until actual data tables are collected.
8. Change REFCOM to `aggregate_only` until individual/location records are acquired.
9. Normalize one big historical source fully—I'd choose **ONS labour demand**—rather than adding another raw file.
10. Add failure-mode tests before claiming "tested and working."

The most useful acceptance test now is brutally simple:

```text
For each source marked VERIFIED:

Can I pick 10 random normalized economic records,
trace every one to a raw artifact,
re-run normalization and get identical output,
prove the collector covered its claimed range,
and distinguish source-empty from source-broken?
```

If any answer is no, it isn't `VERIFIED`.

The coding agent is making real progress, but the next phase should make the repo **honest about what it knows**. That will solve more problems than adding another ten sources.

[1]: https://www.gov.uk/guidance/residential-and-commercial-chargepoints-become-an-authorised-installer?utm_source=chatgpt.com "Residential and commercial chargepoints: become an authorised installer - GOV.UK"
[2]: https://occupational-maps.skillsengland.education.gov.uk/public-api/?utm_source=chatgpt.com "Occupational Maps: Public API"
[3]: https://explore-education-statistics.service.gov.uk/find-statistics/apprenticeships/2025-26/explore?utm_source=chatgpt.com "Explore and download data - Apprenticeships - Explore education statistics - GOV.UK"
[4]: https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/57a21bd2-ac04-4ecb-9a10-54ad5687df75?utm_source=chatgpt.com "Subjects - Starts, Achievements, Enrolments by Detailed level, Degree flag, Std-fwk flag, STEM, SSA T1 and 2, Route, Data set from Apprenticeships - Explore education statistics - GOV.UK"
[5]: https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/datasets/skillscompetenciesandotherjobrequirementsfromonlinejobadvertsuk?utm_source=chatgpt.com "Skills, competencies and other job requirements from online job adverts, UK - Office for National Statistics"
[6]: https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/onlinejobadvertssalariesuk?utm_source=chatgpt.com "Online job adverts salaries, UK - Office for National Statistics"
[7]: https://cy.ons.gov.uk/economy/economicoutputandproductivity/output/datasets/textkernelnewonlinejobadverts/current?utm_source=chatgpt.com "Textkernel new online job adverts - Office for National Statistics"

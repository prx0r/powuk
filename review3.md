# powuk review3.md

> Latest push: **good infrastructure progress, but the repo is still at "collector demo" stage rather than Checkpoint 1**.

The important change is that the agent is now fixing the right category of problems instead of building more modelling. Commit `41dadf4e` genuinely improves raw retention, secret handling, source configuration and basic monitoring. But several claims in the commit message are stronger than what the code actually does.

## What genuinely improved

The credential cleanup is real. Keys are now environment-driven and `.env.example` exists. That was necessary.

The change from overwrite paths such as:

```text
data/raw/grid/neso_demand.csv
```

to timestamp/hash paths is also a real improvement. It moves toward the actual garden principle:

```text
source
→ successive observations
→ historical state
```

rather than "latest file only".

Getting ONS job-ad history to load **175,193 rows** is useful. That is exactly the type of historical material we should ingest before doing modelling.

REFCOM discovery is also promising because the source is highly relevant to POWUK.

And introducing `config/sources.yaml` is directionally correct: source behavior needs eventually to be configuration-driven rather than scattered through prose and `server.py`.

So this push is materially better.

---

# But there are still several serious problems

## 1. `sources.yaml` appears invalid YAML

At the top:

```yaml
# powuk source registry

> Machine-readable configuration for all data sources.

sources:
```

That `>` line is not attached to a key.

Unless some permissive parser happens to tolerate it, this is not a valid top-level YAML document.

It should simply be:

```yaml
# powuk source registry
# Machine-readable configuration for all data sources.

sources:
```

or:

```yaml
description: >
  Machine-readable configuration for all data sources.

sources:
```

More importantly, I don't see the application actually **loading this registry at all**.

So presently the "machine-readable registry" is mostly documentation.

Checkpoint 1 needs:

```text
sources.yaml
     ↓
runner
     ↓
collector configuration
```

not:

```text
sources.yaml

and separately

server.py hardcoded everything again
```

That duplication will immediately drift.

---

# 2. "All 13 collectors working" is misleading

Several collectors return *something*, but aren't collecting the dataset their names imply.

That distinction is fundamental.

### UKPN

`ukpn_flex` currently fetches:

```text
/catalog/datasets?limit=50
```

That's a **catalogue of datasets**.

It does not collect flexibility dispatches, headroom, constraints, or anything resembling the intended economic signal.

So:

```text
UKPN collector runs
```

is true.

But:

```text
UKPN data garden is collecting
```

is false.

This is exactly the theatre distinction we need the agent to internalize.

---

# 3. REFCOM currently collects only one number

The new collector calls:

```text
GetFgasActiveCertificateCount
```

and stores:

```text
11,298
```

That's useful as a sanity metric, but it throws away the thing we actually wanted:

```text
company
certificate
postcode/location
status
possibly sole-trader/company identity
```

Our moat isn't:

```text
UK has 11,298 F-gas companies today
```

It's:

```text
entity A appeared
entity B disappeared
entity C moved
entity D gained/lost certification
regional capacity changed
```

If the public REFCOM API exposes company search/listing endpoints—and the previous research suggests useful public register data exists—the agent should ingest the **entity-level register**, not just its count.

Keep count as monitoring:

```text
expected_total ≈ 11,298
```

and assert normalized records roughly match it.

That's an excellent completeness test.

---

# 4. Companies House is still wrong

This is probably the biggest source-specific issue.

The new specification correctly says:

```text
POW-relevant SIC codes
```

But `server.py` still queries:

```text
?q=electrical+contractor
?q=plumbing+heating
?q=solar+panel
```

and uses:

```python
total_results
```

as `active_firms`.

That is not a SIC count.

In fact it could be badly biased by:

* company name,
* description/search indexing,
* dissolved firms,
* irrelevant matches,
* companies that perform the work but don't contain those words.

And the code creates:

```python
"electrical": {"sic": "43210", ...}
```

but never actually sends the SIC code to Companies House.

So `COMPANIES_HOUSE_SPEC.md` and implementation currently contradict each other.

This needs to be fixed before trusting any CH number.

Checkpoint 1 CH should be:

```text
relevant SIC universe
       ↓
all matching companies
       ↓
company_number as stable key
       ↓
status/incorporation/dissolution/postcode/SIC
       ↓
historical baseline
       ↓
stream deltas from now
```

Not keyword counts.

---

# 5. Companies House stream still uses the wrong credential

`collectors/ptech/companies_house_stream.py` has:

```python
key=os.environ['COMPANIES_HOUSE_API_KEY']
```

but the stream has its own credential.

It should be:

```python
COMPANIES_HOUSE_STREAM_KEY
```

You already added the proper variable to `.env.example`, so this looks like an implementation miss.

Also this collector isn't integrated with the 13-collector `server.py` runner anyway.

So AGENTS says:

> Companies House Streaming ✓ Active

while the main server neither runs it nor appears to monitor it.

That's another example where operational docs overstate reality.

---

# 6. The raw-storage fix is only half-correct

The new `store()` is much better, but there is a subtle important bug.

Raw artifact ID:

```python
f"{source}_{dataset}_{h}"
```

depends only on:

```text
source + dataset + content hash
```

Then:

```sql
INSERT OR REPLACE
```

means if the exact same bytes are retrieved tomorrow, yesterday's **retrieval event is overwritten in the manifest DB**.

You may have two filesystem files:

```text
2026/09/21/..._abc.csv
2026/09/22/..._abc.csv
```

but only one manifest record.

That's wrong.

You need separate concepts:

```text
raw_blob
---------
sha256
storage_uri
bytes

retrieval
---------
retrieval_id
raw_blob_hash
source_id
retrieved_at
request...
```

Same bytes can legitimately be fetched 100 times.

You dedupe storage if you want.

But you preserve all 100 observations that:

> this was the source state at these observation times.

That is particularly important for current-state registers where "no change today" is meaningful evidence.

---

# 7. Timestamp semantics regressed

`store()` now uses:

```python
strftime("%Y/%m/%d/%H%M%S")
```

both to construct the path **and** as `observed_at`.

So your DB stores:

```text
2026/09/21/155730
```

rather than a real timestamp.

Paths can use this.

Database fields should remain ISO UTC:

```text
2026-09-21T15:57:30.123456+00:00
```

Have:

```python
now = datetime.now(timezone.utc)

observed_at = now.isoformat()
path_partition = now.strftime("%Y/%m/%d")
filename = ...
```

Don't conflate storage partition with time semantics.

---

# 8. File type detection is wrong

`store()` says:

```python
ext = "json" if body starts {/[ else "csv"
```

Therefore an XLSX file becomes:

```text
....csv
```

The ONS collector actually:

1. manually writes an `.xlsx`,
2. then passes the exact bytes to `store()`,
3. which stores the XLSX bytes again under `.csv`.

So ONS is duplicating raw bytes and one copy has the wrong extension.

APAR similarly manually writes one raw file and then calls `store()` on transformed JSON, mixing the raw and normalized concepts.

This tells me the common ingestion contract still isn't real.

`store()` should accept explicit metadata:

```python
store_raw(
    body,
    source_id="ons_labour",
    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    extension="xlsx",
)
```

No magic extension guessing.

---

# 9. APAR is still not normalized

The collector now downloads the current CSV each run—good.

But then it takes the raw register and reduces it to:

```text
ukprn
name
type
status
start_date
```

only for providers where:

```text
CanDeliverApprenticeships == True
```

This means we throw away information before building our historical canonical layer.

For checkpoint 1, preserve **every source field** in a typed normalized table if feasible, or at minimum preserve the full raw row plus selected canonical columns.

Do not decide in 2026 which APAR fields will matter in 2029.

Raw protects us somewhat, but normalized history should be rich enough to query without repeatedly reparsing old CSVs.

---

# 10. There is almost no normalization yet

This is the largest architectural gap.

Current core pipeline is still basically:

```text
download a large file
↓
save raw
↓
calculate ONE count
↓
observation table
```

Example:

ONS:

```text
175,193 rows downloaded
```

but normalized output is effectively:

```text
ons_labour_rows = 175193
```

That isn't a data garden.

We need those 175,193 rows represented as queryable records like:

```text
period
SOC2020
occupation
geography
demand_measure
value
source_release
```

Likewise APAR needs provider rows.

REFCOM needs company rows.

Procurement needs release rows.

Planning needs application rows.

Until that exists, we are primarily **archiving sources**, not yet building the clean historical garden.

Archiving is good and necessary, but it's only layer 1.

---

# 11. Planning "pagination" is not complete pagination

The code has:

```python
if start_index >= 1000:
    break
```

So it intentionally collects at most 1,000 records.

Likewise configuration has:

```yaml
max_pages: 10
```

That is a smoke-test safety cap, not ingestion.

If there are 1 million records:

```text
collected = 1,000
```

should never be called "paginated collection complete."

Same issue in Contracts Finder:

```python
if start_index >= 1000:
    break
```

That must become one of:

```text
full historical pagination
```

or:

```text
incremental query by date/cursor
```

with bounded windows.

Do not blindly fetch the entire database every 2h either.

Correct pattern:

### Initial backfill

```text
earliest_date → today
partition by month/week/day
paginate completely
```

### Incremental

```text
last_watermark - overlap
→ now
```

Overlap guards against delayed updates.

---

# 12. Find a Tender isn't paginated at all

Despite `sources.yaml` saying:

```yaml
mode: paginated
max_pages: 10
```

the implementation still:

```python
...ocdsReleasePackages?limit=50
```

once.

So configuration and implementation have already diverged in the first commit.

This is exactly why the registry must drive the runner.

---

# 13. Current health monitoring is mostly cosmetic

Current rule:

```python
if last_status == "error":
    FAILED
elif run_count == 0:
    NOT_RUN
else:
    HEALTHY
```

But collectors frequently catch errors internally and return `0`.

Example REFCOM:

```python
except Exception:
    return 0
```

Then runner does:

```python
state(..., "ok", 0)
```

Therefore:

```text
REFCOM API completely broken
→ returns 0
→ status = ok
→ health = HEALTHY
```

This is dangerous.

Same issue with:

```text
UKPN
Find a Tender
Ofqual
Companies House per-cluster failures
```

A collector must either:

```text
raise CollectorError
```

or return an explicit result:

```python
CollectorResult(
    status="failed",
    rows=0,
    ...
)
```

Zero rows can be legitimate data.

Therefore row count cannot encode execution status.

---

# 14. Health ignores staleness

A collector could have succeeded once six months ago and still display:

```text
HEALTHY
```

Need source-specific SLA:

```yaml
max_staleness: 3h
```

Then:

```text
last success < SLA        HEALTHY
over SLA                  STALE
auth failure              BLOCKED_AUTH
HTTP failure              FAILED
never run                  NOT_RUN
```

This is essential for unattended garden operation.

---

# 15. Tests haven't changed

This is the clearest sign checkpoint work hasn't reached validation yet.

`tests/test_core.py` still tests:

```text
Region constructs
Constraint.gap works
there are 12 regions
```

None of the new functionality is tested.

No tests for:

```text
immutable raw storage
hash correctness
same-content retrieval
APAR parsing
ONS parsing
pagination
Companies House filtering
health semantics
error propagation
stream resume
secret absence
normalization
idempotency
```

So currently the most important changes are unverified.

I would make **tests the next commit**, before another data source.

---

# 16. Source registry is missing the sources we actually prioritized

Current registry has:

```text
REFCOM
APAR
Ofqual
ONS
```

but still does not include the highest-value capacity registers we discussed:

```text
Registered Competent Person Electrical
MCS
OZEV
TrustMark
UKRLP
DfE apprenticeship starts/achievements
Apprenticeship vacancies
Nomis occupation/self-employed supply
Skills Bootcamps
policy/legislation
```

Meanwhile it still contains four grid collectors.

Grid data is useful, but for the **POWUK garden we're actually defining**, I would now bias effort toward:

```text
people
qualifications
providers
firms
demand
```

instead of further grid work.

---

# 17. The REFCOM result changes the priority

The fact that the agent found an accessible REFCOM API is exactly what we want it doing.

Now go one level deeper.

Find all public endpoints behind that register.

Don't stop at:

```text
GetFgasActiveCertificateCount
```

Explore legitimate public API calls used by its own public search UI and determine whether we can retrieve:

```text
certificate holders
company names
locations
registration/certificate IDs
status
```

If yes, that becomes an excellent permanent panel from today onward.

This same approach should be applied to:

```text
MCS
OZEV
Competent Person
TrustMark
```

Public directory UI → inspect official/public data access → capture current entity universe → snapshot.

---

# 18. `evspark_trades` should become temporary

This line is still embedded:

```text
/root/ab/businesses/evspark/receipts/ch_sweep_areas.csv
```

That is not portable and isn't a canonical upstream source.

Fine as an interim calibration dataset.

But flag it:

```yaml
status: legacy_seed
```

and remove it from P0 once proper sources exist.

Checkpoint 1 should be reproducible on a clean machine.

Anything depending on random `/root/ab/...` state violates that.

---

# 19. AGENTS.md is encouraging the wrong extension pattern

It says:

> Adding a collector: add to `server.py`

That's exactly what we said not to do.

The coding agent is now being taught to make the monolith bigger.

Change immediately to:

```text
collectors/{domain}/{source}.py
```

using a shared collector contract.

`server.py` should eventually shrink toward orchestration only.

---

# 20. P0 source definitions need explicit backfill semantics

Right now:

```yaml
mode: backfill
```

doesn't tell us anything actionable.

A source should say something like:

```yaml
history:
  type: embedded_full_history
  earliest: 2017-01
  partition: release
  revisions: true
```

or:

```yaml
history:
  type: current_state_only
  snapshot_now: true
```

or:

```yaml
history:
  type: paginated_api
  earliest: 2015-01-01
  partition: month
```

That determines collection behavior.

---

# The next commit should be much less glamorous

I would tell the agent:

> **Do not add another source in the next commit. Make the 13 claimed collectors honest.**

Specifically:

```text
1. Fix sources.yaml syntax and make code load it.
2. Fix CH stream to use STREAM_KEY.
3. Replace CH keyword search with actual SIC-based collection.
4. Convert REFCOM from count-only to entity-level if public API permits.
5. Remove pagination hard caps and implement bounded historical windows.
6. Paginate Find a Tender.
7. Stop swallowing exceptions.
8. Make health detect failure + staleness.
9. Split raw blob from retrieval event.
10. Fix MIME/extension handling.
11. Normalize APAR provider rows.
12. Normalize ONS 175k rows.
13. Add actual tests for all of the above.
```

Then I would accept the next checkpoint when this command can exist:

```text
powuk verify
```

and output something like:

```text
SOURCE               RAW   NORM     HISTORY       CURRENT    HEALTH
ONS jobs             PASS  175193   2017→2026     current    PASS
APAR                  PASS  1263     current-only  snapshot   PASS
REFCOM                PASS  11298    from-2026     snapshot   PASS
Companies House      PASS  132xxx   baseline       stream     PASS
Contracts Finder     PASS  2.1m     full           current    PASS
Find a Tender        PASS  xxxk     full           current    PASS
```

with every number traceable back to immutable raw artifacts.

## Current checkpoint assessment

I'd describe `41dadf4e` like this:

```text
Secrets                  █████████░  strong
Raw retention            ███████░░░  improved, manifest semantics wrong
Source registry          ████░░░░░░  exists but not yet executable
Historical backfill      ████░░░░░░  ONS good start
Pagination               ███░░░░░░░  partial/capped
Normalization            ██░░░░░░░░  mostly absent
Entity-level capacity    ██░░░░░░░░  REFCOM currently count only
Companies House          ██░░░░░░░░  implementation contradicts spec
Monitoring               ███░░░░░░░  cosmetic health
Resumability             ██░░░░░░░░  CH prototype only
Tests                    █░░░░░░░░░  essentially unchanged
```

So: **good push, correct direction, but still around one-third of the way to a real Checkpoint 1.**

The biggest win now would not be finding the 14th source. It would be converting **ONS + APAR + REFCOM + Companies House + procurement** into five unquestionably correct end-to-end pipelines. Once those are boring and reliable, adding MCS/OZEV/etc. becomes mechanical.
